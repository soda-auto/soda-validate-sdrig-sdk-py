"""
SDRIG SDK - Software-Defined Remote Interface Gateway SDK

Python SDK for controlling SDRIG hardware modules including UIO (Universal I/O),
ELoad (Electronic Load), and IfMux (Interface Multiplexer) devices.
"""

__version__ = "0.1.0"
__author__ = "SODA Validate"
__license__ = "MIT"

# Main SDK interface
from .sdk import SDRIG, discover

# Device classes
from .devices.device_uio import DeviceUIO, Pin
from .devices.device_eload import DeviceELoad, ELoadChannel
from .devices.device_ifmux import DeviceIfMux, CANChannel

# Enums and types
from .types.enums import (
    DeviceType,
    Feature,
    FeatureState,
    RelayState,
    CANSpeed,
    CANState,
    PGN
)

# Data structures
from .types.structs import (
    PinState,
    ValuePair,
    PWMConfig,
    ModuleInfo,
    CANChannelState,
    ELoadChannelState
)

# Utilities
from .utils.logger import get_logger, SDRIGLogger
from .utils.device_manager import DeviceManager

__all__ = [
    # Main API
    'SDRIG',
    'discover',

    # Devices
    'DeviceUIO',
    'Pin',
    'DeviceELoad',
    'ELoadChannel',
    'DeviceIfMux',
    'CANChannel',

    # Enums
    'DeviceType',
    'Feature',
    'FeatureState',
    'RelayState',
    'CANSpeed',
    'CANState',
    'PGN',

    # Structures
    'PinState',
    'ValuePair',
    'PWMConfig',
    'ModuleInfo',
    'CANChannelState',
    'ELoadChannelState',

    # Utilities
    'get_logger',
    'SDRIGLogger',
    'DeviceManager',
]
