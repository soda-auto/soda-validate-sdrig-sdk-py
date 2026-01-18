"""
DeviceELoad - Electronic Load Device

This module provides the DeviceELoad class for controlling electronic load modules
with 8 channels supporting:
- Current sink mode: 0-10A @ 0-24V (electronic load)
- Voltage source mode: 0-24V output (power supply)
- Voltage measurement when disabled
"""

from typing import List, Dict
from ..devices.device_sdr import DeviceSDR
from ..types.enums import DeviceType, PGN, Feature, FeatureState
from ..types.structs import ELoadChannelState
from ..utils.logger import get_logger

logger = get_logger('device_eload')


class ELoadChannel:
    """
    Represents a single Electronic Load channel

    Each channel supports:
    - Current sink mode: 0-10A (electronic load)
    - Voltage source mode: 0-24V output (power supply)
    - Voltage measurement: 0-24V (when disabled or in any mode)
    - Current measurement: 0-11A
    - Temperature monitoring
    - Power limiting: 200W per channel, 600W total

    Note: Current sink and voltage source modes are mutually exclusive.
    """

    def __init__(self, device: 'DeviceELoad', channel_id: int):
        """
        Initialize ELoad channel

        Args:
            device: Parent ELoad device
            channel_id: Channel number (0-7)
        """
        self.device = device
        self.channel_id = channel_id
        self.state = ELoadChannelState(channel_id=channel_id)

    def set_current(self, current: float):
        """
        Set current sink value (electronic load mode)

        Args:
            current: Current in amps (0-10A)

        Raises:
            ValueError: If current out of range

        Note:
            - Enables current sink mode and disables voltage source mode
            - Channel becomes an electronic load (sinks current)
            - Mutually exclusive with voltage source mode
        """
        if not 0 <= current <= 10:
            raise ValueError(f"Current must be 0-10A, got {current}")

        # Enable current output and disable voltage output
        self.device._set_op_mode(self.channel_id, Feature.SET_CURRENT, FeatureState.OPERATE)
        self.device._set_op_mode(self.channel_id, Feature.GET_CURRENT, FeatureState.OPERATE)
        self.device._set_op_mode(self.channel_id, Feature.SET_VOLTAGE, FeatureState.DISABLED)
        self.device._set_op_mode(self.channel_id, Feature.GET_VOLTAGE, FeatureState.OPERATE)

        # Update current value in device state
        self.device._currents_out[self.channel_id] = current
        self.state.current_set = current
        self.state.enabled = current > 0
        logger.debug(f"Channel {self.channel_id}: Set current to {current}A")

        # Disable voltage when enabling current
        self.device._voltages_out[self.channel_id] = 0.0

        # Send immediately if value changed (Performance optimization - change detection)
        if self.device._currents_out != self.device._currents_out_last:
            self.device._send_current_out_req()

    def get_current(self) -> float:
        """
        Get last measured current

        Returns:
            Current in amps
        """
        return self.state.current_measured

    def set_voltage(self, voltage: float):
        """
        Set voltage source output (power supply mode)

        Args:
            voltage: Voltage in volts (0-24V)

        Raises:
            ValueError: If voltage out of range

        Note:
            - Enables voltage source mode and disables current sink mode
            - Channel becomes a power supply (0-24V output)
            - Mutually exclusive with current sink mode
        """
        if not 0 <= voltage <= 24:
            raise ValueError(f"Voltage must be 0-24V, got {voltage}")

        # Enable voltage output and disable current output
        self.device._set_op_mode(self.channel_id, Feature.SET_VOLTAGE, FeatureState.OPERATE)
        self.device._set_op_mode(self.channel_id, Feature.GET_VOLTAGE, FeatureState.OPERATE)
        self.device._set_op_mode(self.channel_id, Feature.SET_CURRENT, FeatureState.DISABLED)
        self.device._set_op_mode(self.channel_id, Feature.GET_CURRENT, FeatureState.DISABLED)

        # Update voltage value in device state
        self.device._voltages_out[self.channel_id] = voltage
        self.state.voltage = voltage
        logger.debug(f"Channel {self.channel_id}: Set voltage to {voltage}V")

        # Disable current when enabling voltage
        self.device._currents_out[self.channel_id] = 0.0
        self.state.current_set = 0.0

        # Send immediately if value changed
        if self.device._voltages_out != self.device._voltages_out_last:
            self.device._send_voltage_out_req()

    def get_voltage(self) -> float:
        """
        Get last measured voltage (works in all modes)

        Returns:
            Voltage in volts

        Note:
            - In current sink mode: measures input voltage
            - In voltage source mode: measures output voltage
            - When disabled: measures connected voltage
        """
        return self.state.voltage

    def get_temperature(self) -> float:
        """
        Get last measured temperature

        Returns:
            Temperature in Celsius
        """
        return self.state.temperature

    def get_power(self) -> float:
        """
        Get calculated power

        Returns:
            Power in watts
        """
        return self.state.power

    def disable(self):
        """Disable current sinking on this channel"""
        self.set_current(0.0)

    def __repr__(self) -> str:
        return (
            f"ELoadChannel({self.channel_id}, "
            f"I={self.state.current_measured:.2f}A, "
            f"V={self.state.voltage:.2f}V, "
            f"P={self.state.power:.2f}W)"
        )


class DeviceELoad(DeviceSDR):
    """
    Electronic Load Device

    Provides control for 8 electronic load channels with current sinking,
    voltage monitoring, and temperature monitoring.
    """

    def __init__(self, mac_address: str, iface: str, stream_id: int, dbc_path: str):
        """
        Initialize ELoad device

        Args:
            mac_address: Device MAC address
            iface: Network interface name
            stream_id: AVTP stream ID
            dbc_path: Path to DBC file
        """
        super().__init__(mac_address, iface, stream_id, dbc_path)

        # Create 8 channels
        self.channels: List[ELoadChannel] = [ELoadChannel(self, i) for i in range(8)]

        # Operation modes: dict[channel_id][feature] = state
        self._op_modes = {i: {} for i in range(8)}

        # Output values for each channel
        self._voltages_out = [0.0] * 8  # Voltage output values (V)
        self._currents_out = [0.0] * 8  # Current sink values (A)

        # Last sent values for change detection (Performance optimization)
        self._voltages_out_last = [0.0] * 8
        self._currents_out_last = [0.0] * 8

        # Digital output relay states (4 relays: dout_1, dout_2, dout_3, dout_4)
        self._relay_states = [False] * 4  # False = open, True = closed

        # Total power limit
        self.max_total_power = 600.0  # Watts
        self.max_channel_power = 200.0  # Watts per channel

        logger.info(f"ELoad device initialized: {mac_address}")

    def device_type(self) -> DeviceType:
        """Get device type"""
        return DeviceType.ELOAD

    def channel(self, channel_id: int) -> ELoadChannel:
        """
        Get channel by ID

        Args:
            channel_id: Channel ID (0-7)

        Returns:
            ELoadChannel object

        Raises:
            ValueError: If channel ID invalid
        """
        if not 0 <= channel_id <= 7:
            raise ValueError(f"Channel ID must be 0-7, got {channel_id}")
        return self.channels[channel_id]

    def get_total_power(self) -> float:
        """
        Get total power consumption across all channels

        Returns:
            Total power in watts
        """
        return sum(ch.state.power for ch in self.channels)

    def disable_all_channels(self):
        """Disable all channels"""
        for channel in self.channels:
            channel.disable()

    def set_relay(self, relay_id: int, closed: bool):
        """
        Set digital output relay state

        Args:
            relay_id: Relay ID (0-3 for dout_1 to dout_4)
            closed: True to close relay, False to open

        Raises:
            ValueError: If relay_id out of range
        """
        if not 0 <= relay_id <= 3:
            raise ValueError(f"Relay ID must be 0-3, got {relay_id}")

        self._relay_states[relay_id] = closed
        logger.debug(f"Relay {relay_id+1}: {'closed' if closed else 'open'}")

        # Send immediately
        self._send_switch_relay_req()

    def get_relay(self, relay_id: int) -> bool:
        """
        Get digital output relay state

        Args:
            relay_id: Relay ID (0-3 for dout_1 to dout_4)

        Returns:
            True if relay closed, False if open

        Raises:
            ValueError: If relay_id out of range
        """
        if not 0 <= relay_id <= 3:
            raise ValueError(f"Relay ID must be 0-3, got {relay_id}")

        return self._relay_states[relay_id]

    def _set_op_mode(self, channel_id: int, feature: Feature, state: FeatureState):
        """
        Set operation mode for a channel feature

        Args:
            channel_id: Channel number (0-7)
            feature: Feature type
            state: Feature state
        """
        if channel_id not in self._op_modes:
            self._op_modes[channel_id] = {}
        self._op_modes[channel_id][feature] = state

    def _send_op_mode_req(self):
        """Send OP_MODE_REQ with current state of all channels"""
        # Build data for all op_mode signals
        data = {}

        feature_map = {
            Feature.GET_VOLTAGE: "vlt_i",
            Feature.SET_VOLTAGE: "vlt_o",
            Feature.GET_CURRENT: "cur_i",
            Feature.SET_CURRENT: "cur_o",
            Feature.GET_PWM: "icu",
            Feature.SET_PWM: "pwm",
        }

        # Set all to DISABLED by default
        for prefix in ["pwm", "icu", "vlt_i", "vlt_o", "cur_i", "cur_o"]:
            for i in range(1, 9):
                signal_name = f"{prefix}_{i}_op_mode"
                data[signal_name] = 2  # FEATURE_STATUS_DISABLED

        # Apply current operation modes from state
        for channel_id, modes in self._op_modes.items():
            for feature, state in modes.items():
                if feature in feature_map:
                    prefix = feature_map[feature]
                    signal_name = f"{prefix}_{channel_id + 1}_op_mode"
                    if signal_name in data:
                        data[signal_name] = state.value

        try:
            self.send_can_message(PGN.OP_MODE_REQ, data)
        except Exception as e:
            logger.debug(f"Failed to send OP_MODE_REQ: {e}")

    def _send_voltage_out_req(self):
        """Send VOLTAGE_ELM_OUT_VAL_REQ with voltage values for all channels"""
        data = {}
        for i in range(1, 9):
            signal_name = f"vlt_o_{i}_value"
            data[signal_name] = self._voltages_out[i - 1]

        try:
            self.send_can_message(PGN.VOLTAGE_ELM_OUT_VAL_REQ, data)
            # Update last sent values for change detection
            self._voltages_out_last = self._voltages_out.copy()
        except Exception as e:
            logger.debug(f"Failed to send VOLTAGE_ELM_OUT_VAL_REQ: {e}")

    def _send_current_out_req(self):
        """Send CUR_ELM_OUT_VAL_REQ with current values for all channels"""
        data = {}
        for i in range(1, 9):
            signal_name = f"cur_o_{i}_value"
            data[signal_name] = self._currents_out[i - 1]

        try:
            self.send_can_message(PGN.CUR_ELM_OUT_VAL_REQ, data)
            # Update last sent values for change detection (Performance optimization)
            self._currents_out_last = self._currents_out.copy()
        except Exception as e:
            logger.debug(f"Failed to send CUR_ELM_OUT_VAL_REQ: {e}")

    def _send_switch_relay_req(self):
        """Send SWITCH_ELM_DOUT_req with relay states"""
        data = {}
        for i in range(1, 5):  # 4 relays (dout_1 to dout_4)
            signal_name = f"dout_{i}_en"
            # 1 if relay closed, 0 if open
            data[signal_name] = 1 if self._relay_states[i - 1] else 0

        try:
            self.send_can_message(PGN.SWITCH_ELM_DOUT_REQ, data)
        except Exception as e:
            logger.debug(f"Failed to send SWITCH_ELM_DOUT_REQ: {e}")

    def _setup_periodic_tasks(self):
        """Setup periodic tasks for ELoad device"""
        # Request MODULE_INFO every 9 seconds (max 10s, per documentation)
        self.request_module_info()
        self.task_monitor.add_task_sec(
            "module_info",
            self.request_module_info,
            9.0
        )

        # Send all parameters every 3 seconds (max 4s, per documentation)
        # This includes OP_MODE, VOLTAGE_OUT, CURRENT_OUT
        self.task_monitor.add_task_sec(
            "all_parameters",
            self._send_all_parameters,
            0.1
        )

    def _send_all_parameters(self):
        """
        Send all parameter updates in single periodic task

        Per ELoad documentation:
        - MODULE_INFO_req must be sent every 9 seconds (max 10s)
        - Other messages must be sent every 3 seconds (max 4s)
        """
        self._send_op_mode_req()
        self._send_voltage_out_req()
        self._send_current_out_req()

    def _process_can_message(self, pgn: int, data: bytes, src_mac: str):
        """
        Process received CAN message

        Args:
            pgn: Parameter Group Number
            data: Message data
            src_mac: Source MAC address
        """
        try:
            # Build 29-bit CAN ID with priority=3 and SA=0x00 for DBC lookup
            # Extended bit handled by DBC layer
            can_id = (3 << 26) | (pgn << 8) | 0x00
            decoded = self.can_db.decode_message(can_id, data)

            # Handle different message types
            if pgn == PGN.MODULE_INFO.value:
                self._handle_module_info(decoded)
            elif pgn == PGN.MODULE_INFO_EX.value:
                self._handle_module_info_ex(decoded)
            elif pgn == PGN.VOLTAGE_ELM_IN_ANS.value:
                self._handle_voltage_in(decoded)
            elif pgn == PGN.VOLTAGE_ELM_OUT_VAL_ANS.value:
                self._handle_voltage_out(decoded)
            elif pgn == PGN.CUR_ELM_IN_VAL_ANS.value:
                self._handle_current_in(decoded)
            elif pgn == PGN.CUR_ELM_OUT_VAL_ANS.value:
                self._handle_current_out(decoded)
            elif pgn == PGN.TEMP_ELM_IN_ANS.value:
                self._handle_temperature(decoded)
            elif pgn == PGN.SWITCH_ELM_DOUT_ANS.value:
                self._handle_relay_response(decoded)

        except Exception as e:
            logger.debug(f"Error processing ELoad message PGN 0x{pgn:04X}: {e}")

    def _handle_module_info(self, decoded: Dict):
        """Handle MODULE_INFO message"""
        from ..protocol.can_messages import ModuleInfoMessage
        self.module_info = ModuleInfoMessage.from_decoded(decoded, self.mac_address)
        logger.info(f"ELoad Module: {self.module_info.app_name} {self.module_info.version}")

    def _handle_module_info_ex(self, decoded: Dict):
        """Handle MODULE_INFO_EX message"""
        from ..protocol.can_messages import ModuleInfoExMessage
        info_ex = ModuleInfoExMessage.from_decoded(decoded, self.mac_address)
        if self.module_info:
            self.module_info.ip_address = info_ex.ip_address
            self.module_info.chip_uid = info_ex.chip_uid
        logger.info(f"ELoad IP: {info_ex.ip_address}")

    def _handle_voltage_in(self, decoded: Dict):
        """Handle VOLTAGE_ELM_IN_ANS message - voltage input measurement"""
        # Message contains voltage measurements for all 8 channels
        for i in range(1, 9):
            signal_name = f"vlt_i_{i}_value"
            if signal_name in decoded:
                channel_idx = i - 1
                voltage = decoded[signal_name]
                self.channels[channel_idx].state.voltage = voltage
                logger.debug(f"Channel {channel_idx} voltage IN: {voltage:.2f}V")

    def _handle_voltage_out(self, decoded: Dict):
        """Handle VOLTAGE_ELM_OUT_VAL_ANS message - voltage output confirmation"""
        # Message contains voltage output values for all 8 channels
        for i in range(1, 9):
            signal_name = f"vlt_o_{i}_value"
            if signal_name in decoded:
                channel_idx = i - 1
                voltage = decoded[signal_name]
                # Update state with confirmed output voltage
                self.channels[channel_idx].state.voltage = voltage
                logger.debug(f"Channel {channel_idx} voltage OUT: {voltage:.2f}V")

    def _handle_current_in(self, decoded: Dict):
        """Handle CUR_ELM_IN_VAL_ANS message - current input measurement"""
        # Message contains current measurements for all 8 channels
        for i in range(1, 9):
            signal_name = f"cur_i_{i}_value"
            if signal_name in decoded:
                channel_idx = i - 1
                current = decoded[signal_name]
                channel = self.channels[channel_idx]
                channel.state.current_measured = current
                # Update power calculation
                channel.state.power = current * channel.state.voltage
                logger.debug(f"Channel {channel_idx} current IN: {current:.3f}A")

    def _handle_current_out(self, decoded: Dict):
        """Handle CUR_ELM_OUT_VAL_ANS message - current output confirmation"""
        # Message contains current output values for all 8 channels
        for i in range(1, 9):
            signal_name = f"cur_o_{i}_value"
            if signal_name in decoded:
                channel_idx = i - 1
                current = decoded[signal_name]
                # Update state with confirmed output current
                self.channels[channel_idx].state.current_set = current
                logger.debug(f"Channel {channel_idx} current OUT: {current:.3f}A")

    def _handle_temperature(self, decoded: Dict):
        """Handle TEMP_ELM_IN_ANS message"""
        channel_id = decoded.get("pin_number", 0)
        if 0 <= channel_id <= 7:
            temperature = decoded.get("temperature", 0.0)
            self.channels[channel_id].state.temperature = temperature

    def _handle_relay_response(self, decoded: Dict):
        """Handle SWITCH_ELM_DOUT_ANS message"""
        # Update relay states from response
        for i in range(1, 5):  # 4 relays (dout_1 to dout_4)
            signal_name = f"dout_{i}_en"
            if signal_name in decoded:
                self._relay_states[i - 1] = bool(decoded[signal_name])
                logger.debug(f"Relay {i}: {'closed' if self._relay_states[i-1] else 'open'}")

    def __repr__(self) -> str:
        total_power = self.get_total_power()
        return (
            f"DeviceELoad(mac={self.mac_address}, "
            f"channels=8, power={total_power:.1f}W, "
            f"running={self._running})"
        )
