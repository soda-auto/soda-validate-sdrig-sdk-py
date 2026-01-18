"""
Enumerations for SDRIG SDK

This module contains all enum types used throughout the SDK.
"""

from enum import IntEnum, Enum


class DeviceType(Enum):
    """Device types in SDRIG system"""
    UNKNOWN = "Unknown"
    UIO = "UIO"  # Universal Input/Output
    ELOAD = "ELoad"  # Electronic Load
    IFMUX = "IfMux"  # Interface Multiplexer


class Feature(IntEnum):
    """UIO Pin features"""
    UNKNOWN = 0
    GET_VOLTAGE = 1  # Voltage Input (0-24V)
    SET_VOLTAGE = 2  # Voltage Output (0-24V)
    GET_CURRENT = 3  # Current Loop Input (0-20mA)
    SET_CURRENT = 4  # Current Loop Output (0-20mA)
    GET_PWM = 5  # PWM Input Measurement (20Hz-5kHz)
    SET_PWM = 6  # PWM Output Generation (20Hz-5kHz)


class FeatureState(IntEnum):
    """State of a feature on a pin"""
    UNKNOWN = 0
    IDLE = 1  # Feature not active
    DISABLED = 2  # Feature explicitly disabled
    OPERATE = 3  # Feature operating normally
    WARNING = 4  # Feature has warnings
    ERROR = 5  # Feature has errors


class RelayState(IntEnum):
    """Relay state for pin switching"""
    OPEN = 0
    CLOSED = 1
    UNKNOWN = 2


class CANSpeed(IntEnum):
    """CAN bus speed configuration"""
    SPEED_125K = 125000
    SPEED_250K = 250000
    SPEED_500K = 500000
    SPEED_1M = 1000000
    SPEED_2M = 2000000
    SPEED_4M = 4000000
    SPEED_5M = 5000000


class CANState(IntEnum):
    """CAN controller state"""
    ERROR_ACTIVE = 0
    ERROR_PASSIVE = 1
    BUS_OFF = 2
    UNKNOWN = 3


class LastErrorCode(IntEnum):
    """CAN Last Error Code (LEC)"""
    NO_ERROR = 0
    STUFF_ERROR = 1
    FORM_ERROR = 2
    ACK_ERROR = 3
    BIT1_ERROR = 4
    BIT0_ERROR = 5
    CRC_ERROR = 6
    NO_CHANGE = 7


class J1939Address(IntEnum):
    """J1939 Address constants"""
    NULL_SA = 0x00      # NULL source address (default for outgoing messages)
    WILDCARD_SA = 0xFE  # Wildcard SA (used in DBC templates)
    BROADCAST_DA = 0xFF # Global/Broadcast destination address


class PGN(IntEnum):
    """
    Parameter Group Numbers for CAN messages

    NOTE: PGN values include wildcard Source Address (0xFE) in lowest byte.
    This matches the DBC file format where all CAN IDs use SA=0xFE as template.

    When building CAN ID: build_j1939_id() shifts PGN left by 8 bits,
    then replaces bits [7:0] with actual Source Address.

    Per official UIO/MUX Module Control Manual:
    - MODULE_INFO_REQ must be sent every 9 seconds (max 10s) or module goes IDLE
    - Other messages must be sent every 3 seconds (max 4s) or functions disabled
    """
    # Device Information (per official manual)
    MODULE_INFO_REQ = 0x000FE   # Request for module information (heartbeat)
    MODULE_INFO = 0x001FE       # Module information response
    MODULE_INFO_EX = 0x008FE    # Extended module information (MAC, IP, UID)
    MODULE_INFO_BOOT = 0x002FE  # Bootloader information

    # Pin Information
    PIN_INFO = 0x010FE          # Pin capabilities (64 pins)

    # UIO Operation Modes
    OP_MODE_REQ = 0x121FE       # Request operational modes (voltage, current, PWM, ICU)
    OP_MODE_ANS = 0x120FE       # Operational modes response

    # Voltage
    VOLTAGE_IN_ANS = 0x114FE            # Voltage input measurement (8 channels)
    VOLTAGE_OUT_VAL_REQ = 0x116FE       # Voltage output request (8 channels)
    VOLTAGE_OUT_VAL_ANS = 0x117FE       # Voltage output response

    # Current Loop
    CUR_LOOP_IN_VAL_ANS = 0x128FE       # Current loop input measurement (8 channels)
    CUR_LOOP_OUT_VAL_REQ = 0x126FE      # Current loop output request (8 channels)
    CUR_LOOP_OUT_VAL_ANS = 0x127FE      # Current loop output response

    # PWM
    PWM_IN_ANS = 0x122FE                # PWM input (ICU) measurement (8 channels)
    PWM_OUT_VAL_REQ = 0x112FE           # PWM output request (8 channels)
    PWM_OUT_VAL_ANS = 0x113FE           # PWM output response

    # Switch/Relay
    SWITCH_OUTPUT_REQ = 0x123FE         # Switch relay control (voltage, current, PWM, ICU)
    SWITCH_OUTPUT_ANS = 0x124FE         # Switch relay status

    # Electronic Load
    VOLTAGE_ELM_OUT_VAL_REQ = 0x116FE   # ELoad voltage output request (8 channels)
    VOLTAGE_ELM_OUT_VAL_ANS = 0x117FE   # ELoad voltage output response
    VOLTAGE_ELM_IN_ANS = 0x114FE        # ELoad voltage input measurement (8 channels)
    CUR_ELM_IN_VAL_ANS = 0x12AFE        # ELoad current input measurement (8 channels)
    CUR_ELM_OUT_VAL_REQ = 0x129FE       # ELoad current output request (8 channels)
    CUR_ELM_OUT_VAL_ANS = 0x12BFE       # ELoad current output response
    TEMP_ELM_IN_ANS = 0x12EFE           # ELoad temperature measurement (8 channels)
    SWITCH_ELM_DOUT_REQ = 0x12CFE       # ELoad digital output relay control (4 relays)
    SWITCH_ELM_DOUT_ANS = 0x12DFE       # ELoad digital output relay status

    # CAN Interface (per official manual)
    CAN_INFO_REQ = 0x021FE              # CAN speed configuration request
    CAN_INFO_ANS = 0x020FE              # CAN speed configuration response
    CAN_STATE_ANS = 0x022FE             # CAN controller state
    CAN_MUX_REQ = 0x028FE               # CAN MUX relay configuration request
    CAN_MUX_ANS = 0x029FE               # CAN MUX relay configuration response

    # LIN Interface (corrected to match DBC file)
    LIN_CFG_REQ = 0x040FE               # LIN configuration request (0-61 frames)
    LIN_FRAME_SET_REQ = 0x042FE         # LIN frame data set request
    LIN_FRAME_RCVD_ANS = 0x043FE        # LIN frame received response
