# -*- coding: utf-8 -*-

from enum import Enum, auto


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
    DOWN = auto()
    UP = auto()


class InterfaceState(Enum):
    DOWN = auto()
    UP = auto()
