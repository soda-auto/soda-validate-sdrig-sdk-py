"""
Unit tests for device_uio.py

Tests UIO device functionality with mocked hardware.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sdrig.devices.device_uio import DeviceUIO, Pin
from sdrig.types.enums import PGN, Feature, FeatureState


class TestUIOPinVoltage:
    """Test UIO pin voltage control"""

    def test_set_voltage_valid_range(self, uio_device_mocks):
        """Test setting voltage in valid range (0-24V)"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Test valid voltages
        for voltage in [0.0, 5.0, 12.0, 24.0]:
            uio.pin(0).set_voltage(voltage)
            assert uio._voltages_out[0] == voltage

    def test_set_voltage_invalid_range(self, uio_device_mocks):
        """Test setting voltage outside valid range raises error"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Test invalid voltages
        with pytest.raises(ValueError):
            uio.pin(0).set_voltage(-1.0)

        with pytest.raises(ValueError):
            uio.pin(0).set_voltage(25.0)

    def test_set_voltage_enables_op_mode(self, uio_device_mocks):
        """Test set_voltage enables correct OP_MODE"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        uio.pin(0).set_voltage(12.0)

        # Check OP_MODE was set
        assert Feature.SET_VOLTAGE in uio._op_modes[0]
        assert uio._op_modes[0][Feature.SET_VOLTAGE] == FeatureState.OPERATE

    def test_set_voltage_enables_relay(self, uio_device_mocks):
        """Test set_voltage enables voltage output relay"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        uio.pin(0).set_voltage(12.0)

        # Check relay was enabled
        assert uio._switch_states['vlt_o'][0] == True

    def test_get_voltage(self, uio_device_mocks):
        """Test getting voltage measurement"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Simulate voltage measurement
        uio.pins[0].state.voltage.get_value = 12.5

        voltage = uio.pin(0).get_voltage()
        assert voltage == 12.5


class TestUIOPinCurrent:
    """Test UIO pin current loop control"""

    def test_set_current_valid_range(self, uio_device_mocks):
        """Test setting current in valid range (0-20mA)"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Test valid currents
        for current in [0.0, 4.0, 12.0, 20.0]:
            uio.pin(0).set_tx_current(current)
            assert uio._currents_out[0] == current

    def test_set_current_invalid_range(self, uio_device_mocks):
        """Test setting current outside valid range raises error"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Test invalid currents
        with pytest.raises(ValueError):
            uio.pin(0).set_tx_current(-1.0)

        with pytest.raises(ValueError):
            uio.pin(0).set_tx_current(21.0)

    def test_4_20ma_conversion(self, uio_device_mocks):
        """Test 4-20mA industrial standard conversion"""
        def percent_to_4_20ma(percent):
            return 4.0 + (percent / 100.0) * 16.0

        # Test conversion
        assert percent_to_4_20ma(0) == 4.0    # 0% = 4mA
        assert percent_to_4_20ma(50) == 12.0  # 50% = 12mA
        assert percent_to_4_20ma(100) == 20.0 # 100% = 20mA

    def test_get_current(self, uio_device_mocks):
        """Test getting current measurement"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Simulate current measurement
        uio.pins[0].state.current.get_value = 10.5

        current = uio.pin(0).get_rx_current()
        assert current == 10.5


class TestUIOPinPWM:
    """Test UIO pin PWM control"""

    def test_set_pwm_valid_range(self, uio_device_mocks):
        """Test setting PWM in valid range"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Test valid PWM
        uio.pin(0).set_pwm(frequency=1000, duty_cycle=50.0)

        freq, duty, volt = uio._pwm_out[0]
        assert freq == 1000
        assert duty == 50.0
        assert volt == 5.0  # Hardware limitation: fixed 5V

    def test_set_pwm_invalid_frequency(self, uio_device_mocks):
        """Test setting PWM with invalid frequency"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Test invalid frequencies
        with pytest.raises(ValueError):
            uio.pin(0).set_pwm(frequency=10, duty_cycle=50.0)  # < 20Hz

        with pytest.raises(ValueError):
            uio.pin(0).set_pwm(frequency=6000, duty_cycle=50.0)  # > 5000Hz

    def test_set_pwm_invalid_duty(self, uio_device_mocks):
        """Test setting PWM with invalid duty cycle"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Test invalid duty cycles
        with pytest.raises(ValueError):
            uio.pin(0).set_pwm(frequency=1000, duty_cycle=-1.0)

        with pytest.raises(ValueError):
            uio.pin(0).set_pwm(frequency=1000, duty_cycle=101.0)

    def test_set_pwm_enables_icu(self, uio_device_mocks):
        """Test set_pwm enables ICU relay for readback"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        uio.pin(0).set_pwm(frequency=1000, duty_cycle=50.0)

        # Check ICU relay enabled
        assert uio._switch_states['icu'][0] == True
        assert uio._switch_states['pwm'][0] == True

    def test_enable_pwm_input(self, uio_device_mocks):
        """Test enable_pwm_input enables ICU without PWM output"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        uio.pin(0).enable_pwm_input()

        # Check ICU enabled, PWM not enabled
        assert uio._switch_states['icu'][0] == True
        assert uio._switch_states['pwm'][0] == False

    def test_get_pwm(self, uio_device_mocks):
        """Test getting PWM measurement"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Simulate PWM measurement
        uio.pins[0].state.pwm_frequency.get_value = 1000.0
        uio.pins[0].state.pwm_duty_cycle.get_value = 50.0
        uio.pins[0].state.pwm_voltage.get_value = 0.0  # ICU can't measure voltage

        freq, duty, volt = uio.pin(0).get_pwm()
        assert freq == 1000.0
        assert duty == 50.0
        assert volt == 0.0  # ICU limitation


class TestUIOPinControl:
    """Test UIO pin control methods"""

    def test_pin_number_valid_range(self, uio_device_mocks):
        """Test valid pin numbers (0-7)"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        for pin_num in range(8):
            pin = uio.pin(pin_num)
            assert isinstance(pin, Pin)
            assert pin.pin_number == pin_num

    def test_pin_number_invalid_range(self, uio_device_mocks):
        """Test invalid pin numbers raise error"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        with pytest.raises(ValueError):
            uio.pin(-1)

        with pytest.raises(ValueError):
            uio.pin(8)

    def test_disable_all_features(self, uio_device_mocks):
        """Test disabling all features on a pin"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Enable some features
        uio.pin(0).set_voltage(12.0)
        uio.pin(0).set_tx_current(10.0)

        # Disable all
        uio.pin(0).disable_all_features()

        # Check features are disabled (OP_MODE set to DISABLED)
        # Note: Values are not reset to 0, only the features are disabled
        from sdrig.types.enums import Feature, FeatureState
        assert uio._op_modes[0].get(Feature.SET_VOLTAGE) == FeatureState.DISABLED
        assert uio._op_modes[0].get(Feature.SET_CURRENT) == FeatureState.DISABLED

    def test_disable_feature(self, uio_device_mocks):
        """Test disabling specific feature"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Enable voltage
        uio.pin(0).set_voltage(12.0)

        # Disable voltage feature
        uio.pin(0).disable_feature(Feature.SET_VOLTAGE)

        # Check OP_MODE was set to DISABLED
        assert uio._op_modes[0][Feature.SET_VOLTAGE] == FeatureState.DISABLED
        assert uio._switch_states['vlt_o'][0] == False


class TestUIODevice:
    """Test UIO device class"""

    def test_device_creation(self, uio_device_mocks):
        """Test creating UIO device"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        assert uio.mac_address == "00:11:22:33:44:55"
        assert len(uio.pins) == 8

    def test_device_type(self, uio_device_mocks):
        """Test device type is UIO"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        from sdrig.types.enums import DeviceType
        assert uio.device_type() == DeviceType.UIO

    def test_start_stop(self, uio_device_mocks):
        """Test starting and stopping device"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Start
        uio.start()
        assert uio._running == True

        # Stop
        uio.stop()
        assert uio._running == False
