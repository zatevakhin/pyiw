# -*- coding: utf-8 -*-

import os
import re
import subprocess
from enum import Enum, auto
from collections import namedtuple


class WirelessInterfaceInfo:
    def __init__(self, data):
        self.interface = data.get("interface")
        self.addr = data.get("addr")
        self.type = data.get("type")
        self.ifindex = int(data.get("ifindex"))
        self.wdev = int(data.get("wdev"), 16)
        self.wiphy = int(data.get("wiphy"))
        self.txpower = float(data.get("txpower"))

    def __repr__(self):
        return f"<Interface ({self.interface} - {self.type})>"


class InterfaceFlags(Enum):
    NO_CARRIER = auto()
    BROADCAST = auto()
    MULTICAST = auto()
    LOOPBACK = auto()
    LOWER_UP = auto()
    UP = auto()


class InterfaceState(Enum):
    DOWN = auto()
    UP = auto()


class Tools:
    IW = "/usr/sbin/iw"
    IP = "/usr/bin/ip"


class BlockedByRfKillError(Exception):
    pass

class IncorrectInterfaceError(Exception):
    pass

class IncorrectInterfaceStateError(Exception):
    pass

class IncorrectInterfaceNameError(Exception):
    pass


class WirelessInterface:

    @staticmethod
    def list():
        return list(filter(lambda ifc: os.path.exists(f"/sys/class/net/{ifc}/wireless"), os.listdir("/sys/class/net")))

    @staticmethod
    def list_monitor():
        return list(filter(WirelessInterface.is_monitor, WirelessInterface.list()))

    @staticmethod
    def is_wireless(interface):
        return interface in WirelessInterface.list()

    @staticmethod
    def is_monitor(interface):
        info = WirelessInterface.get_info(interface)
        return info.type == "monitor"

    @staticmethod
    def get_flags(interface):
        if not WirelessInterface.is_wireless(interface):
            raise IncorrectInterfaceError(f"Incorrect interface ... ({interface}). Use wireless interface.")

        try:
            output = subprocess.check_output([Tools.IP, 'link', 'show', interface], stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            raise Exception(e.output.strip())

        status = []

        if match := re.search(r"<(.+)>", output.decode('utf-8'), re.I):
            status = str(match.groups()[0]).replace("-", "_").split(",")
            status = list(filter(lambda st: st.name in status, list(InterfaceFlags)))

        return status
    
    @staticmethod
    def set_state(interface, state: InterfaceState):
        if not WirelessInterface.is_wireless(interface):
            raise IncorrectInterfaceError(f"Incorrect interface ... ({interface}). Use wireless interface.")

        if not isinstance(state, InterfaceState):
            raise IncorrectInterfaceStateError(f"State have incorrect type ... ({state})")

        flags = WirelessInterface.get_flags(interface)
        
        if [InterfaceFlags.UP not in flags, InterfaceFlags.UP in flags][InterfaceState.UP == state]:
            return True

        try:
            process = subprocess.run([Tools.IP, 'link', 'set', interface, str(state.name).lower()], capture_output=True)
            process.check_returncode()

        except subprocess.CalledProcessError as e:
            if e.returncode == 2 and is_blocked_by_rf_kill(e.stderr):
                raise BlockedByRfKillError(e)
            elif e.returncode == 2:
                raise PermissionError(e)
            else:
                raise e

        return True
    
    @staticmethod
    def get_info(interface):
        if not WirelessInterface.is_wireless(interface):
            raise IncorrectInterfaceError(f"Incorrect interface ... ({interface}). Use wireless interface.")

        try:
            output = subprocess.check_output([Tools.IW, 'dev', interface, 'info'], stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
                raise e

        if match := re.findall(r"([^\s]+)\s([^\s]+)", output.decode('utf-8'), re.M | re.I):
            return WirelessInterfaceInfo(dict((k.lower(), v) for k,v in dict(match).items()))

        return True

    @staticmethod
    def add_monitor(interface, monitor):
        if not WirelessInterface.is_wireless(interface):
            raise IncorrectInterfaceError(f"Incorrect interface ... ({interface}). Use wireless interface.")

        monitors = WirelessInterface.list_monitor()

        if monitor in monitors:
            raise IncorrectInterfaceNameError(f"This interface {monitor} name already in use.")

        try:
            subprocess.run([Tools.IW, 'dev', interface, 'interface', 'add', monitor, 'type', 'monitor'], check=True, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            if e.returncode == 255:
                raise PermissionError(e)
            else:
                raise e

        return True

    @staticmethod
    def set_channel(interface, channel):
        if not WirelessInterface.is_wireless(interface):
            raise IncorrectInterfaceError(f"Incorrect interface ... ({interface}). Use wireless interface.")

        try:
            subprocess.run([Tools.IW, 'dev', interface, 'set', 'channel', str(channel)], check=True, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            if e.returncode == 255:
                raise PermissionError(e)
            else:
                raise e

        return True


def is_blocked_by_rf_kill(output):
    output = output.decode().lower()
    MSG_PATTERN = "Operation not possible due to RF-kill".lower()
    return MSG_PATTERN in output
