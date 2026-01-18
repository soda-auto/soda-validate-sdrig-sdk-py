"""
CAN Message encoder/decoder with DBC support

This module provides wrapper classes for all SDRIG CAN messages
using cantools for DBC-based encoding/decoding.
"""

import cantools
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from ..utils.logger import get_logger
from ..types.enums import PGN
from .can_protocol import prepare_can_id, extract_pgn, normalize_can_id_for_dbc

logger = get_logger('can_messages')


def build_voltage_out_data(pin_number: int, voltage: float) -> Dict[str, Any]:
    """
    Build VOLTAGE_OUT_VAL_req message data for all 8 pins

    Args:
        pin_number: Pin number (0-7)
        voltage: Voltage value for the specified pin

    Returns:
        Dictionary with all voltage signals
    """
    data = {}
    for i in range(1, 9):  # Pins 1-8
        signal_name = f"vlt_o_{i}_value"
        # Set the voltage for the specified pin, 0 for others
        data[signal_name] = voltage if (i - 1) == pin_number else 0.0
    return data


def build_current_out_data(pin_number: int, current: float) -> Dict[str, Any]:
    """
    Build CUR_LOOP_OUT_VAL_req message data for all 8 pins

    Args:
        pin_number: Pin number (0-7)
        current: Current value for the specified pin (mA)

    Returns:
        Dictionary with all current signals
    """
    data = {}
    for i in range(1, 9):  # Pins 1-8
        signal_name = f"cur_ma_o_{i}_value"
        data[signal_name] = current if (i - 1) == pin_number else 0.0
    return data


def build_pwm_out_data(pin_number: int, frequency: float, duty_cycle: float, voltage: float) -> Dict[str, Any]:
    """
    Build PWM_OUT_VAL_req message data for all 8 pins

    Args:
        pin_number: Pin number (0-7)
        frequency: PWM frequency (Hz)
        duty_cycle: Duty cycle (%)
        voltage: PWM voltage (V)

    Returns:
        Dictionary with all PWM signals
    """
    data = {}
    for i in range(1, 9):  # Pins 1-8
        # Each PWM has frequency, duty cycle, and voltage signals
        freq_signal = f"pwm_{i}_frequency"
        duty_signal = f"pwm_{i}_duty"
        volt_signal = f"pwm_{i}_voltage"

        if (i - 1) == pin_number:
            data[freq_signal] = frequency
            data[duty_signal] = duty_cycle
            data[volt_signal] = voltage
        else:
            data[freq_signal] = 0.0
            data[duty_signal] = 0.0
            data[volt_signal] = 0.0
    return data


def build_op_mode_data(pin_number: int, feature: int, state: int) -> Dict[str, Any]:
    """
    Build OP_MODE_req message data for all signals

    Args:
        pin_number: Pin number (0-7)
        feature: Feature type (1=GET_VOLTAGE, 2=SET_VOLTAGE, etc.)
        state: Operation state

    Returns:
        Dictionary with all op_mode signals
    """
    # Map feature to signal prefix
    # Feature values from enums.py:
    # GET_VOLTAGE = 1, SET_VOLTAGE = 2, GET_CURRENT = 3, SET_CURRENT = 4
    # GET_PWM = 5, SET_PWM = 6

    feature_map = {
        1: "vlt_i",  # GET_VOLTAGE -> voltage input
        2: "vlt_o",  # SET_VOLTAGE -> voltage output
        3: "cur_i",  # GET_CURRENT -> current input
        4: "cur_o",  # SET_CURRENT -> current output
        5: "icu",    # GET_PWM -> icu (Input Capture Unit for PWM measurement)
        6: "pwm",    # SET_PWM -> pwm (PWM generator for PWM output)
    }

    data = {}

    # Initialize all signals to 2 (FEATURE_STATUS_DISABLED)
    signal_prefixes = ["pwm", "icu", "vlt_i", "cur_i", "vlt_o", "cur_o"]
    for prefix in signal_prefixes:
        for i in range(1, 9):
            signal_name = f"{prefix}_{i}_op_mode"
            # if signal_prefixes is vlt_i set it to 3
            if prefix == "vlt_i":
                data[signal_name] = 3  # 3 = FEATURE_STATUS_ENABLED_READ_ONLY
            else:
                data[signal_name] = 0  # 2 = FEATURE_STATUS_DISABLED

    # Set the specific signal for the requested pin and feature
    if feature in feature_map:
        prefix = feature_map[feature]
        pin_num = pin_number + 1  # Convert 0-based to 1-based
        signal_name = f"{prefix}_{pin_num}_op_mode"
        if signal_name in data:
            data[signal_name] = state

    return data


class CANMessageDatabase:
    """Manager for CAN message database (DBC)"""

    def __init__(self, dbc_path: str):
        """
        Initialize CAN message database

        Args:
            dbc_path: Path to DBC file
        """
        self.dbc_path = Path(dbc_path)
        if not self.dbc_path.exists():
            raise FileNotFoundError(f"DBC file not found: {dbc_path}")

        self.db = cantools.database.load_file(str(self.dbc_path))
        # Cache: normalized_id -> message (Performance optimization 2.2)
        self._message_cache: Dict[int, cantools.database.Message] = {}
        logger.info(f"Loaded DBC file: {dbc_path}")
        logger.info(f"Messages in database: {len(self.db.messages)}")

    def encode_message(self, can_id: int, data: Dict[str, Any]) -> bytes:
        """
        Encode CAN message using DBC

        Args:
            can_id: CAN message ID
            data: Dictionary of signal names and values

        Returns:
            Encoded message bytes
        """
        # Normalize ID for DBC lookup (PDU1/PDU2 aware for J1939)
        normalized_id = normalize_can_id_for_dbc(can_id)

        # Check cache first (Performance optimization 2.2)
        message = self._message_cache.get(normalized_id)
        if not message:
            try:
                message = self.db.get_message_by_frame_id(normalized_id)
                self._message_cache[normalized_id] = message
            except KeyError:
                logger.error(f"Message with ID 0x{can_id:08X} not found in DBC")
                raise

        # Encode with strict=False to allow partial signal data
        encoded = message.encode(data, strict=False)
        logger.debug(f"Encoded {message.name}: data={data} -> bytes={encoded.hex()}")
        return encoded

    def decode_message(self, can_id: int, data: bytes) -> Optional[Dict[str, Any]]:
        """
        Decode CAN message using DBC

        Args:
            can_id: CAN message ID (should already have extended bit set)
            data: Message data bytes

        Returns:
            Dictionary of decoded signals, or None if message not found
        """
        # Normalize ID for DBC lookup (PDU1/PDU2 aware for J1939)
        normalized_id = normalize_can_id_for_dbc(can_id)

        # Check cache first (Performance optimization 2.2)
        message = self._message_cache.get(normalized_id)
        if not message:
            try:
                message = self.db.get_message_by_frame_id(normalized_id)
                self._message_cache[normalized_id] = message
            except KeyError:
                logger.debug(f"Message with ID 0x{can_id:08X} not found in DBC")
                return None

        return message.decode(data)

    def get_message_name(self, can_id: int) -> Optional[str]:
        """
        Get message name from CAN ID

        Args:
            can_id: CAN message ID

        Returns:
            Message name or None
        """
        try:
            message = self.db.get_message_by_frame_id(can_id | 0x80000000)
            return message.name
        except KeyError:
            # Normalize ID for DBC lookup (PDU1/PDU2 aware for J1939)
            normalized_id = normalize_can_id_for_dbc(can_id)
            try:
                message = self.db.get_message_by_frame_id(normalized_id)
                return message.name
            except KeyError:
                return None


@dataclass
class ModuleInfoMessage:
    """MODULE_INFO message data"""
    mac_address: str = ""
    app_name: str = ""
    hw_name: str = ""
    version: str = ""
    build_date: str = ""
    crc: int = 0
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_decoded(cls, decoded: Dict[str, Any], mac_address: str) -> 'ModuleInfoMessage':
        """Create from decoded CAN message"""
        msg = cls(mac_address=mac_address, raw_data=decoded)

        # Extract firmware name (3 x 8-byte fields)
        if "module_app_fw_name_1" in decoded:
            try:
                fw_name_1 = decoded['module_app_fw_name_1'].to_bytes(8, 'little').decode('utf-8')
                fw_name_2 = decoded['module_app_fw_name_2'].to_bytes(8, 'little').decode('utf-8')
                fw_name_3 = decoded['module_app_fw_name_3'].to_bytes(8, 'little').decode('utf-8')
                msg.app_name = (fw_name_1 + fw_name_2 + fw_name_3).rstrip("\x00")
            except Exception as e:
                logger.warning(f"Failed to decode app name: {e}")

        # Extract version
        if "module_app_ver_gen" in decoded:
            msg.version = (
                f"{decoded['module_app_ver_gen']}."
                f"{decoded['module_app_ver_major']}."
                f"{decoded['module_app_ver_minor']}."
                f"{decoded['module_app_ver_fix']}."
                f"{decoded['module_app_ver_build']}"
            )
            if "module_app_target" in decoded:
                msg.version += f" {decoded['module_app_target']}"

        # Extract build date
        if "module_app_build_day" in decoded:
            msg.build_date = (
                f"{decoded['module_app_build_day']:02d}/"
                f"{decoded['module_app_build_month']:02d}/"
                f"{decoded['module_app_build_year']:04d} "
                f"{decoded['module_app_build_hour']:02d}:"
                f"{decoded['module_app_build_min']:02d}"
            )

        # Extract hardware name
        if "module_app_hw_name_1" in decoded:
            try:
                hw_name_1 = decoded['module_app_hw_name_1'].to_bytes(8, 'little').decode('utf-8')
                hw_name_2 = decoded['module_app_hw_name_2'].to_bytes(8, 'little').decode('utf-8')
                msg.hw_name = (hw_name_1 + hw_name_2).rstrip("\x00")
            except Exception as e:
                logger.warning(f"Failed to decode hw name: {e}")

        # Extract CRC
        if "module_app_crc" in decoded:
            msg.crc = decoded['module_app_crc']

        return msg


@dataclass
class ModuleInfoExMessage:
    """MODULE_INFO_EX message data"""
    mac_address: str = ""
    ip_address: str = ""
    chip_uid: str = ""
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_decoded(cls, decoded: Dict[str, Any], mac_address: str) -> 'ModuleInfoExMessage':
        """Create from decoded CAN message"""
        import socket

        msg = cls(mac_address=mac_address, raw_data=decoded)

        # Extract IP address
        if "module_ip_addr" in decoded:
            try:
                ip_bytes = decoded['module_ip_addr'].to_bytes(4, 'big')
                msg.ip_address = socket.inet_ntoa(ip_bytes)
            except Exception as e:
                logger.warning(f"Failed to decode IP address: {e}")

        # Extract chip UID
        if "module_chip_uid_1" in decoded and "module_chip_uid_2" in decoded:
            msg.chip_uid = f"{decoded['module_chip_uid_1']:016X}{decoded['module_chip_uid_2']:016X}"

        return msg


@dataclass
class PinInfoMessage:
    """PIN_INFO message data"""
    pin_number: int = 0
    capabilities: int = 0
    raw_data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_decoded(cls, decoded: Dict[str, Any]) -> 'PinInfoMessage':
        """Create from decoded CAN message"""
        msg = cls(raw_data=decoded)

        if "pin_number" in decoded:
            msg.pin_number = decoded["pin_number"]
        if "capabilities" in decoded:
            msg.capabilities = decoded["capabilities"]

        return msg


@dataclass
class OpModeMessage:
    """OP_MODE operation mode message"""
    pin_number: int = 0
    feature: int = 0
    state: int = 0
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for encoding"""
        return {
            "pin_number": self.pin_number,
            "feature": self.feature,
            "state": self.state
        }

    @classmethod
    def from_decoded(cls, decoded: Dict[str, Any]) -> 'OpModeMessage':
        """Create from decoded CAN message"""
        return cls(
            pin_number=decoded.get("pin_number", 0),
            feature=decoded.get("feature", 0),
            state=decoded.get("state", 0),
            raw_data=decoded
        )


@dataclass
class VoltageMessage:
    """Voltage input/output message"""
    pin_number: int = 0
    voltage: float = 0.0
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for encoding"""
        return {
            "pin_number": self.pin_number,
            "voltage": self.voltage
        }

    @classmethod
    def from_decoded(cls, decoded: Dict[str, Any]) -> 'VoltageMessage':
        """Create from decoded CAN message"""
        return cls(
            pin_number=decoded.get("pin_number", 0),
            voltage=decoded.get("voltage", 0.0),
            raw_data=decoded
        )


@dataclass
class CurrentMessage:
    """Current loop input/output message"""
    pin_number: int = 0
    current: float = 0.0
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for encoding"""
        return {
            "pin_number": self.pin_number,
            "current": self.current
        }

    @classmethod
    def from_decoded(cls, decoded: Dict[str, Any]) -> 'CurrentMessage':
        """Create from decoded CAN message"""
        return cls(
            pin_number=decoded.get("pin_number", 0),
            current=decoded.get("current", 0.0),
            raw_data=decoded
        )


@dataclass
class PWMMessage:
    """PWM input/output message"""
    pin_number: int = 0
    frequency: float = 0.0
    duty_cycle: float = 0.0
    voltage: float = 0.0
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for encoding"""
        return {
            "pin_number": self.pin_number,
            "frequency": self.frequency,
            "duty_cycle": self.duty_cycle,
            "voltage": self.voltage
        }

    @classmethod
    def from_decoded(cls, decoded: Dict[str, Any]) -> 'PWMMessage':
        """Create from decoded CAN message"""
        return cls(
            pin_number=decoded.get("pin_number", 0),
            frequency=decoded.get("frequency", 0.0),
            duty_cycle=decoded.get("duty_cycle", 0.0),
            voltage=decoded.get("voltage", 0.0),
            raw_data=decoded
        )


@dataclass
class SwitchOutputMessage:
    """Switch/relay output message"""
    pin_number: int = 0
    state: int = 0
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for encoding"""
        return {
            "pin_number": self.pin_number,
            "state": self.state
        }

    @classmethod
    def from_decoded(cls, decoded: Dict[str, Any]) -> 'SwitchOutputMessage':
        """Create from decoded CAN message"""
        return cls(
            pin_number=decoded.get("pin_number", 0),
            state=decoded.get("state", 0),
            raw_data=decoded
        )
