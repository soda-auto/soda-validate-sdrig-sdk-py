"""
Unit tests for enums.py

Tests all enum values for correctness per official manual.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sdrig.types.enums import (
    PGN, DeviceType, Feature, FeatureState,
    RelayState, CANSpeed, CANState, LastErrorCode
)


class TestPGNEnum:
    """Test PGN enum values"""

    def test_module_info_req_exists(self):
        """Test MODULE_INFO_REQ exists and has correct value"""
        assert hasattr(PGN, 'MODULE_INFO_REQ')
        assert PGN.MODULE_INFO_REQ == 0x000FE

    def test_device_info_pgns(self):
        """Test device information PGN values per official manual"""
        assert PGN.MODULE_INFO == 0x001FE
        assert PGN.MODULE_INFO_EX == 0x008FE
        assert PGN.MODULE_INFO_BOOT == 0x002FE
        assert PGN.PIN_INFO == 0x010FE

    def test_uio_pgns(self):
        """Test UIO PGN values"""
        assert PGN.OP_MODE_REQ == 0x121FE
        assert PGN.OP_MODE_ANS == 0x120FE
        assert PGN.VOLTAGE_IN_ANS == 0x114FE
        assert PGN.VOLTAGE_OUT_VAL_REQ == 0x116FE
        assert PGN.VOLTAGE_OUT_VAL_ANS == 0x117FE
        assert PGN.PWM_IN_ANS == 0x122FE
        assert PGN.PWM_OUT_VAL_REQ == 0x112FE
        assert PGN.PWM_OUT_VAL_ANS == 0x113FE
        assert PGN.CUR_LOOP_IN_VAL_ANS == 0x128FE
        assert PGN.CUR_LOOP_OUT_VAL_REQ == 0x126FE
        assert PGN.CUR_LOOP_OUT_VAL_ANS == 0x127FE
        assert PGN.SWITCH_OUTPUT_REQ == 0x123FE
        assert PGN.SWITCH_OUTPUT_ANS == 0x124FE

    def test_eload_pgns(self):
        """Test ELoad PGN values per official manual"""
        assert PGN.VOLTAGE_ELM_OUT_VAL_REQ == 0x116FE
        assert PGN.VOLTAGE_ELM_OUT_VAL_ANS == 0x117FE
        assert PGN.VOLTAGE_ELM_IN_ANS == 0x114FE
        assert PGN.CUR_ELM_IN_VAL_ANS == 0x12AFE
        assert PGN.CUR_ELM_OUT_VAL_REQ == 0x129FE
        assert PGN.CUR_ELM_OUT_VAL_ANS == 0x12BFE
        assert PGN.TEMP_ELM_IN_ANS == 0x12EFE
        assert PGN.SWITCH_ELM_DOUT_REQ == 0x12CFE
        assert PGN.SWITCH_ELM_DOUT_ANS == 0x12DFE

    def test_can_pgns(self):
        """Test CAN interface PGN values per official manual"""
        assert PGN.CAN_INFO_REQ == 0x021FE
        assert PGN.CAN_INFO_ANS == 0x020FE
        assert PGN.CAN_STATE_ANS == 0x022FE
        assert PGN.CAN_MUX_REQ == 0x028FE
        assert PGN.CAN_MUX_ANS == 0x029FE

    def test_lin_pgns(self):
        """Test LIN interface PGN values per official manual"""
        assert PGN.LIN_CFG_REQ == 0x040FE
        assert PGN.LIN_FRAME_SET_REQ == 0x042FE
        assert PGN.LIN_FRAME_RCVD_ANS == 0x043FE

    def test_pgn_values_are_integers(self):
        """Test all PGN values are integers"""
        for name, value in PGN.__members__.items():
            assert isinstance(value, int)
            assert value >= 0


class TestDeviceType:
    """Test DeviceType enum"""

    def test_device_types_exist(self):
        """Test all device types exist"""
        assert DeviceType.UNKNOWN
        assert DeviceType.UIO
        assert DeviceType.ELOAD
        assert DeviceType.IFMUX

    def test_device_type_values(self):
        """Test device type string values"""
        assert DeviceType.UIO.value == "UIO"
        assert DeviceType.ELOAD.value == "ELoad"
        assert DeviceType.IFMUX.value == "IfMux"


class TestFeature:
    """Test Feature enum"""

    def test_all_features_exist(self):
        """Test all features exist"""
        assert Feature.UNKNOWN == 0
        assert Feature.GET_VOLTAGE == 1
        assert Feature.SET_VOLTAGE == 2
        assert Feature.GET_CURRENT == 3
        assert Feature.SET_CURRENT == 4
        assert Feature.GET_PWM == 5
        assert Feature.SET_PWM == 6

    def test_feature_values_sequential(self):
        """Test feature values are sequential"""
        features = [
            Feature.UNKNOWN,
            Feature.GET_VOLTAGE,
            Feature.SET_VOLTAGE,
            Feature.GET_CURRENT,
            Feature.SET_CURRENT,
            Feature.GET_PWM,
            Feature.SET_PWM
        ]
        for i, feature in enumerate(features):
            assert feature == i


class TestFeatureState:
    """Test FeatureState enum"""

    def test_all_states_exist(self):
        """Test all feature states exist"""
        assert FeatureState.UNKNOWN == 0
        assert FeatureState.IDLE == 1
        assert FeatureState.DISABLED == 2
        assert FeatureState.OPERATE == 3
        assert FeatureState.WARNING == 4
        assert FeatureState.ERROR == 5

    def test_disabled_vs_operate(self):
        """Test critical states have correct values"""
        assert FeatureState.DISABLED == 2
        assert FeatureState.OPERATE == 3


class TestRelayState:
    """Test RelayState enum"""

    def test_relay_states(self):
        """Test relay state values"""
        assert RelayState.OPEN == 0
        assert RelayState.CLOSED == 1
        assert RelayState.UNKNOWN == 2


class TestCANSpeed:
    """Test CANSpeed enum"""

    def test_can_speeds(self):
        """Test CAN speed values"""
        assert CANSpeed.SPEED_125K == 125000
        assert CANSpeed.SPEED_250K == 250000
        assert CANSpeed.SPEED_500K == 500000
        assert CANSpeed.SPEED_1M == 1000000
        assert CANSpeed.SPEED_2M == 2000000
        assert CANSpeed.SPEED_4M == 4000000
        assert CANSpeed.SPEED_5M == 5000000


class TestCANState:
    """Test CANState enum"""

    def test_can_states(self):
        """Test CAN controller state values"""
        assert CANState.ERROR_ACTIVE == 0
        assert CANState.ERROR_PASSIVE == 1
        assert CANState.BUS_OFF == 2
        assert CANState.UNKNOWN == 3


class TestLastErrorCode:
    """Test LastErrorCode enum"""

    def test_error_codes(self):
        """Test CAN last error code values"""
        assert LastErrorCode.NO_ERROR == 0
        assert LastErrorCode.STUFF_ERROR == 1
        assert LastErrorCode.FORM_ERROR == 2
        assert LastErrorCode.ACK_ERROR == 3
        assert LastErrorCode.BIT1_ERROR == 4
        assert LastErrorCode.BIT0_ERROR == 5
        assert LastErrorCode.CRC_ERROR == 6
        assert LastErrorCode.NO_CHANGE == 7
