# -*- coding: utf-8 -*-


class DeviceBusyError(Exception):
    pass

class BlockedByRfKillError(Exception):
    pass

class IncorrectInterfaceError(Exception):
    pass

class IncorrectInterfaceStateError(Exception):
    pass

class IncorrectInterfaceNameError(Exception):
    pass
