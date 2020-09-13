# -*- coding: utf-8 -*-

import os
import re
import subprocess
from collections import namedtuple

from .exceptions import *
from .types import *


class Tools:
    IW = "/usr/sbin/iw"
    IP = "/usr/bin/ip"


def all_wireless():
    return list(filter(lambda ifc: os.path.exists(f"/sys/class/net/{ifc}/wireless"), os.listdir("/sys/class/net")))

def all_monitor():
    return list(filter(is_monitor, all_wireless()))


def is_monitor(interface):
    info = get_info(interface)
    return info.type == "monitor"


def is_wireless(interface):
    return interface in all_wireless()


def get_info(interface):
    if not is_wireless(interface):
        raise IncorrectInterfaceError(f"Incorrect interface ... ({interface}). Use wireless interface.")

    try:
        output = subprocess.check_output([Tools.IW, 'dev', interface, 'info'], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
            raise e

    if match := re.findall(r"([^\s]+)\s([^\s]+)", output.decode('utf-8'), re.M | re.I):
        return WirelessInterfaceInfo(dict((k.lower(), v) for k,v in dict(match).items()))

    return True


def get_flags(interface):
    if not is_wireless(interface):
        raise IncorrectInterfaceError(f"Incorrect interface ... ({interface}). Use wireless interface.")

    try:
        output = subprocess.check_output([Tools.IP, 'link', 'show', interface], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        raise Exception(e.output.strip())

    status = []

    if match := re.search(r"<(.+)>", output.decode('utf-8'), re.I):
        status = str(match.groups()[0]).replace("-", "_").split(",")
        status = list(filter(lambda st: st.name in status, list(InterfaceFlags)))
        if InterfaceFlags.UP not in status:
            status.append(InterfaceFlags.DOWN)

    return status


def set_state(interface, state: InterfaceState):
    if not is_wireless(interface):
        raise IncorrectInterfaceError(f"Incorrect interface ... ({interface}). Use wireless interface.")

    if not isinstance(state, InterfaceState):
        raise IncorrectInterfaceStateError(f"State have incorrect type ... ({state})")

    flags = get_flags(interface)
    
    if [InterfaceFlags.UP not in flags, InterfaceFlags.UP in flags][InterfaceState.UP == state]:
        return True

    try:
        process = subprocess.run([Tools.IP, 'link', 'set', interface, str(state.name).lower()], capture_output=True)
        process.check_returncode()

    except subprocess.CalledProcessError as e:
        if e.returncode == 2 and __is_blocked_by_rf_kill(e.stderr):
            raise BlockedByRfKillError(e)
        elif e.returncode == 2:
            raise PermissionError(e)
        else:
            raise e

    return True


def add_monitor(interface, monitor):
    if not is_wireless(interface):
        raise IncorrectInterfaceError(f"Incorrect interface ... ({interface}). Use wireless interface.")

    if monitor in all_monitor():
        raise IncorrectInterfaceNameError(f"This interface {monitor} name already in use.")

    try:
        subprocess.run([Tools.IW, 'dev', interface, 'interface', 'add', monitor, 'type', 'monitor'], check=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        if e.returncode == 255:
            raise PermissionError(e)
        else:
            raise e

    return True


def set_channel(interface, channel):
    if not is_wireless(interface):
        raise IncorrectInterfaceError(f"Incorrect interface ... ({interface}). Use wireless interface.")

    try:
        subprocess.run([Tools.IW, 'dev', interface, 'set', 'channel', str(channel)], check=True, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        if e.returncode == 255:
            raise PermissionError(e)
        elif e.returncode == 240:
            raise DeviceBusyError(e)
        else:
            raise e

    return True


def __is_blocked_by_rf_kill(output):
    output = output.decode().lower()
    MSG_PATTERN = "Operation not possible due to RF-kill".lower()
    return MSG_PATTERN in output
