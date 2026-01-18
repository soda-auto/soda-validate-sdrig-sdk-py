"""
Unit tests for device_eload.py

Tests ELoad device functionality including:
- Current sink mode (electronic load)
- Voltage source mode (power supply)
- Voltage measurement mode
- Mutually exclusive modes
- Relay control
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sdrig.devices.device_eload import DeviceELoad, ELoadChannel
from sdrig.types.enums import PGN, Feature, FeatureState


class TestELoadCurrentSink:
    """Test ELoad current sink mode (electronic load)"""

    def test_set_current_valid_range(self, eload_device_mocks):
        """Test setting current in valid range (0-10A)"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Test valid currents
        for current in [0.0, 2.5, 5.0, 10.0]:
            eload.channel(0).set_current(current)
            assert eload._currents_out[0] == current

    def test_set_current_invalid_range(self, eload_device_mocks):
        """Test setting current outside valid range raises error"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Test invalid currents
        with pytest.raises(ValueError):
            eload.channel(0).set_current(-1.0)

        with pytest.raises(ValueError):
            eload.channel(0).set_current(11.0)

    def test_set_current_disables_voltage(self, eload_device_mocks):
        """Test set_current disables voltage source"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Enable current sink
        eload.channel(0).set_current(5.0)

        # Check voltage disabled
        assert eload._voltages_out[0] == 0.0

    def test_get_current(self, eload_device_mocks):
        """Test getting current measurement"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Simulate current measurement
        eload.channels[0].state.current_measured = 5.5

        current = eload.channel(0).get_current()
        assert current == 5.5


class TestELoadVoltageSource:
    """Test ELoad voltage source mode (power supply)"""

    def test_set_voltage_valid_range(self, eload_device_mocks):
        """Test setting voltage in valid range (0-24V)"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Test valid voltages
        for voltage in [0.0, 5.0, 12.0, 24.0]:
            eload.channel(0).set_voltage(voltage)
            assert eload._voltages_out[0] == voltage

    def test_set_voltage_invalid_range(self, eload_device_mocks):
        """Test setting voltage outside valid range raises error"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Test invalid voltages
        with pytest.raises(ValueError):
            eload.channel(0).set_voltage(-1.0)

        with pytest.raises(ValueError):
            eload.channel(0).set_voltage(25.0)

    def test_set_voltage_disables_current(self, eload_device_mocks):
        """Test set_voltage disables current sink"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Enable voltage source
        eload.channel(0).set_voltage(12.0)

        # Check current disabled
        assert eload._currents_out[0] == 0.0

    def test_get_voltage(self, eload_device_mocks):
        """Test getting voltage measurement"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Simulate voltage measurement
        eload.channels[0].state.voltage = 12.5

        voltage = eload.channel(0).get_voltage()
        assert voltage == 12.5


class TestELoadMutuallyExclusiveModes:
    """Test mutually exclusive modes (current sink vs voltage source)"""

    def test_current_then_voltage(self, eload_device_mocks):
        """Test switching from current sink to voltage source"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Enable current sink
        eload.channel(0).set_current(5.0)
        assert eload._currents_out[0] == 5.0
        assert eload._voltages_out[0] == 0.0

        # Switch to voltage source
        eload.channel(0).set_voltage(12.0)
        assert eload._voltages_out[0] == 12.0
        assert eload._currents_out[0] == 0.0  # Auto-disabled

    def test_voltage_then_current(self, eload_device_mocks):
        """Test switching from voltage source to current sink"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Enable voltage source
        eload.channel(0).set_voltage(12.0)
        assert eload._voltages_out[0] == 12.0
        assert eload._currents_out[0] == 0.0

        # Switch to current sink
        eload.channel(0).set_current(5.0)
        assert eload._currents_out[0] == 5.0
        assert eload._voltages_out[0] == 0.0  # Auto-disabled

    def test_voltage_measurement_mode(self, eload_device_mocks):
        """Test voltage measurement mode (both disabled)"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Disable both modes
        eload.channel(0).set_current(0.0)
        eload.channel(0).set_voltage(0.0)

        # Both should be disabled
        assert eload._currents_out[0] == 0.0
        assert eload._voltages_out[0] == 0.0

        # Can still measure voltage
        eload.channels[0].state.voltage = 13.8
        voltage = eload.channel(0).get_voltage()
        assert voltage == 13.8


class TestELoadRelayControl:
    """Test ELoad digital output relay control"""

    def test_set_relay_valid_range(self, eload_device_mocks):
        """Test setting relay in valid range (0-3)"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Test all 4 relays
        for relay_id in range(4):
            eload.set_relay(relay_id, closed=True)
            assert eload._relay_states[relay_id] == True

            eload.set_relay(relay_id, closed=False)
            assert eload._relay_states[relay_id] == False

    def test_set_relay_invalid_range(self, eload_device_mocks):
        """Test setting relay outside valid range raises error"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        with pytest.raises(ValueError):
            eload.set_relay(-1, closed=True)

        with pytest.raises(ValueError):
            eload.set_relay(4, closed=True)

    def test_get_relay(self, eload_device_mocks):
        """Test getting relay state"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Set and verify
        eload.set_relay(0, closed=True)
        assert eload.get_relay(0) == True

        eload.set_relay(0, closed=False)
        assert eload.get_relay(0) == False


class TestELoadPowerManagement:
    """Test ELoad power management"""

    def test_get_power(self, eload_device_mocks):
        """Test power calculation (V * I)"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Set voltage and current
        eload.channels[0].state.voltage = 12.0
        eload.channels[0].state.current_measured = 5.0

        # Calculate power
        eload.channels[0].state.power = 12.0 * 5.0

        power = eload.channel(0).get_power()
        assert power == 60.0

    def test_get_total_power(self, eload_device_mocks):
        """Test total power across all channels"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Set power on multiple channels
        eload.channels[0].state.power = 100.0
        eload.channels[1].state.power = 150.0
        eload.channels[2].state.power = 200.0

        total = eload.get_total_power()
        assert total == 450.0

    def test_max_power_limits(self, eload_device_mocks):
        """Test power limit constants"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        assert eload.max_channel_power == 200.0  # 200W per channel
        assert eload.max_total_power == 600.0    # 600W total

    def test_get_temperature(self, eload_device_mocks):
        """Test temperature monitoring"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Simulate temperature
        eload.channels[0].state.temperature = 45.5

        temp = eload.channel(0).get_temperature()
        assert temp == 45.5


class TestELoadChannelControl:
    """Test ELoad channel control"""

    def test_channel_valid_range(self, eload_device_mocks):
        """Test valid channel numbers (0-7)"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        for channel_id in range(8):
            channel = eload.channel(channel_id)
            assert isinstance(channel, ELoadChannel)
            assert channel.channel_id == channel_id

    def test_channel_invalid_range(self, eload_device_mocks):
        """Test invalid channel numbers raise error"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        with pytest.raises(ValueError):
            eload.channel(-1)

        with pytest.raises(ValueError):
            eload.channel(8)

    def test_disable_channel(self, eload_device_mocks):
        """Test disabling a channel"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Enable channel
        eload.channel(0).set_current(5.0)

        # Disable
        eload.channel(0).disable()

        assert eload._currents_out[0] == 0.0

    def test_disable_all_channels(self, eload_device_mocks):
        """Test disabling all channels"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Enable multiple channels
        eload.channel(0).set_current(2.0)
        eload.channel(1).set_current(3.0)
        eload.channel(2).set_voltage(12.0)

        # Disable all
        eload.disable_all_channels()

        # Verify all disabled
        for i in range(8):
            assert eload._currents_out[i] == 0.0


class TestELoadDevice:
    """Test ELoad device class"""

    def test_device_creation(self, eload_device_mocks):
        """Test creating ELoad device"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        assert eload.mac_address == "00:11:22:33:44:55"
        assert len(eload.channels) == 8

    def test_device_type(self, eload_device_mocks):
        """Test device type is ELOAD"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        from sdrig.types.enums import DeviceType
        assert eload.device_type() == DeviceType.ELOAD

    def test_initial_state(self, eload_device_mocks):
        """Test initial state of ELoad device"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # All channels should be disabled initially
        for i in range(8):
            assert eload._voltages_out[i] == 0.0
            assert eload._currents_out[i] == 0.0

        # All relays should be open initially
        for i in range(4):
            assert eload._relay_states[i] == False


class TestELoadOPMode:
    """Test ELoad OP_MODE management"""

    def test_set_op_mode(self, eload_device_mocks):
        """Test setting OP_MODE for channel"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Set OP_MODE
        eload._set_op_mode(0, Feature.SET_VOLTAGE, FeatureState.OPERATE)

        # Verify
        assert 0 in eload._op_modes
        assert Feature.SET_VOLTAGE in eload._op_modes[0]
        assert eload._op_modes[0][Feature.SET_VOLTAGE] == FeatureState.OPERATE

    def test_op_mode_for_voltage_source(self, eload_device_mocks):
        """Test OP_MODE when enabling voltage source"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Enable voltage source
        eload.channel(0).set_voltage(12.0)

        # Check OP_MODE
        assert eload._op_modes[0][Feature.SET_VOLTAGE] == FeatureState.OPERATE
        assert eload._op_modes[0][Feature.GET_VOLTAGE] == FeatureState.OPERATE
        assert eload._op_modes[0][Feature.SET_CURRENT] == FeatureState.DISABLED

    def test_op_mode_for_current_sink(self, eload_device_mocks):
        """Test OP_MODE when enabling current sink"""
        eload = DeviceELoad(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Enable current sink
        eload.channel(0).set_current(5.0)

        # Check OP_MODE
        assert eload._op_modes[0][Feature.SET_CURRENT] == FeatureState.OPERATE
        assert eload._op_modes[0][Feature.GET_CURRENT] == FeatureState.OPERATE
        assert eload._op_modes[0][Feature.SET_VOLTAGE] == FeatureState.DISABLED
