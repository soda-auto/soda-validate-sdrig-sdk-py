"""
Data structures for SDRIG SDK

This module contains dataclasses and structured types used throughout the SDK.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from .enums import Feature, FeatureState, RelayState, CANState, LastErrorCode


@dataclass
class ValuePair:
    """Pair of get/set values for a feature"""
    get_value: float = 0.0
    set_value: float = 0.0

    def __repr__(self) -> str:
        return f"ValuePair(get={self.get_value:.3f}, set={self.set_value:.3f})"


@dataclass
class PinState:
    """Complete state of a UIO pin"""
    pin_number: int
    features: Dict[Feature, FeatureState] = field(default_factory=dict)
    relay_state: RelayState = RelayState.UNKNOWN
    voltage: ValuePair = field(default_factory=ValuePair)
    current: ValuePair = field(default_factory=ValuePair)
    pwm_frequency: ValuePair = field(default_factory=ValuePair)
    pwm_duty_cycle: ValuePair = field(default_factory=ValuePair)
    pwm_voltage: ValuePair = field(default_factory=ValuePair)
    capabilities: int = 0  # Bitmask of supported features

    def __post_init__(self):
        """Initialize features dict if empty"""
        if not self.features:
            self.features = {
                Feature.GET_VOLTAGE: FeatureState.UNKNOWN,
                Feature.SET_VOLTAGE: FeatureState.UNKNOWN,
                Feature.GET_CURRENT: FeatureState.UNKNOWN,
                Feature.SET_CURRENT: FeatureState.UNKNOWN,
                Feature.GET_PWM: FeatureState.UNKNOWN,
                Feature.SET_PWM: FeatureState.UNKNOWN,
            }

    def has_capability(self, feature: Feature) -> bool:
        """Check if pin supports a feature"""
        return bool(self.capabilities & (1 << feature.value))


@dataclass
class ModuleInfo:
    """Device module information"""
    mac_address: str
    app_name: str = ""
    hw_name: str = ""
    version: str = ""
    build_date: str = ""
    crc: str = ""
    ip_address: Optional[str] = None
    chip_uid: Optional[str] = None
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CANChannelState:
    """State of a CAN channel"""
    channel_id: int
    state: CANState = CANState.UNKNOWN
    lec: LastErrorCode = LastErrorCode.NO_CHANGE
    speed: int = 0
    tx_count: int = 0
    rx_count: int = 0
    error_count: int = 0


@dataclass
class ELoadChannelState:
    """State of an Electronic Load channel"""
    channel_id: int
    enabled: bool = False
    voltage: float = 0.0  # Measured voltage (V)
    current_set: float = 0.0  # Set current (A)
    current_measured: float = 0.0  # Measured current (A)
    temperature: float = 0.0  # Temperature (°C)
    power: float = 0.0  # Calculated power (W)


@dataclass
class PWMConfig:
    """PWM configuration"""
    frequency: float  # Hz
    duty_cycle: float  # Percentage (0-100)
    voltage: float  # Voltage level (V)

    def __post_init__(self):
        """Validate PWM parameters"""
        if not 20 <= self.frequency <= 5000:
            raise ValueError(f"PWM frequency must be 20-5000 Hz, got {self.frequency}")
        if not 0 <= self.duty_cycle <= 100:
            raise ValueError(f"Duty cycle must be 0-100%, got {self.duty_cycle}")
        # DBC signal has offset=5V, so physical range is 5-30.5V
        if not 5.0 <= self.voltage <= 30.5:
            raise ValueError(f"PWM voltage must be 5-30.5V (per DBC offset), got {self.voltage}")


@dataclass
class DeviceHealth:
    """Device health and activity information"""
    mac_address: str
    last_seen: float = 0.0  # Timestamp
    message_count: int = 0
    error_count: int = 0
    is_active: bool = False
    timeout_threshold: float = 5.0  # seconds

    def is_alive(self, current_time: float) -> bool:
        """Check if device is still alive"""
        return self.is_active and (current_time - self.last_seen) < self.timeout_threshold
