"""
DeviceUIO - Universal Input/Output Device

This module provides the DeviceUIO class for controlling UIO modules with
8 configurable pins supporting voltage I/O, current loop I/O, and PWM I/O.
"""

from typing import List, Optional, Dict
from ..devices.device_sdr import DeviceSDR
from ..types.enums import DeviceType, Feature, FeatureState, RelayState, PGN
from ..types.structs import PinState, ValuePair
from ..utils.logger import get_logger

logger = get_logger('device_uio')


class Pin:
    """
    Represents a single UIO pin with all features

    Each pin supports:
    - Voltage Input (0-24V)
    - Voltage Output (0-24V)
    - Current Loop Input (0-20mA)
    - Current Loop Output (0-20mA)
    - PWM Input Measurement (20Hz-5kHz)
    - PWM Output Generation (20Hz-5kHz)
    """

    def __init__(self, device: 'DeviceUIO', pin_number: int):
        """
        Initialize pin

        Args:
            device: Parent UIO device
            pin_number: Pin number (0-7)
        """
        self.device = device
        self.pin_number = pin_number
        self.state = PinState(pin_number=pin_number)

    def set_voltage(self, voltage: float):
        """
        Set voltage output on this pin

        Args:
            voltage: Voltage in volts (0-24V)
        """
        if not 0 <= voltage <= 24:
            raise ValueError(f"Voltage must be 0-24V, got {voltage}")
        self.disable_all_features()
        # Enable both SET_VOLTAGE (output) and GET_VOLTAGE (input/readback) in OP_MODE
        # Both are needed to set voltage and monitor actual output
        self.device._set_op_mode(self.pin_number, Feature.SET_VOLTAGE, FeatureState.OPERATE)
        self.device._set_op_mode(self.pin_number, Feature.GET_VOLTAGE, FeatureState.OPERATE)

        # Enable voltage output switch
        self.device._switch_states['vlt_o'][self.pin_number] = True

        # Update voltage value in device state
        self.device._voltages_out[self.pin_number] = voltage
        self.state.voltage.set_value = voltage
        logger.debug(f"Pin {self.pin_number}: Set voltage to {voltage}V")

        # Send immediately if value changed (Performance optimization 2.1 - change detection)
        if self.device._voltages_out != self.device._voltages_out_last:
            self.device._send_voltage_out_req()

    def get_voltage(self) -> float:
        """
        Get last measured voltage input

        Returns:
            Voltage in volts
        """
        self.device._set_op_mode(self.pin_number, Feature.GET_VOLTAGE, FeatureState.OPERATE)
        
        return self.state.voltage.get_value

    def set_tx_current(self, current: float):
        """
        Set current loop output on this pin

        Args:
            current: Current in milliamps (0-20mA)
        """
        if not 0 <= current <= 20:
            raise ValueError(f"Current must be 0-20mA, got {current}")

        self.disable_all_features()
        self.device._set_op_mode(self.pin_number, Feature.SET_CURRENT, FeatureState.OPERATE)
        self.device._switch_states['cur_o'][self.pin_number] = True
    

        # Update current value in device state
        self.device._currents_out[self.pin_number] = current
        self.state.current.set_value = 0.0
        logger.debug(f"Pin {self.pin_number}: Set current to {current}mA")

        # Send immediately if value changed (Performance optimization 2.1 - change detection)
        if self.device._currents_out != self.device._currents_out_last:
            self.device._send_current_out_req()

    def get_tx_current(self) -> float:
        """
        Get last measured current loop input

        Returns:
            Current in milliamps
        """
        return self.state.current.set_value

    def get_rx_current(self) -> float:
        """
        Get last measured current loop input

        Returns:
            Current in milliamps
        """
        self.disable_all_features()
        self.device._set_op_mode(self.pin_number, Feature.GET_CURRENT, FeatureState.OPERATE)
        self.device._switch_states['cur_i'][self.pin_number] = True

        return self.state.current.get_value

    def set_pwm(self, frequency: float, duty_cycle: float, voltage: float = 5.0):
        """
        Set PWM output on this pin

        Args:
            frequency: PWM frequency in Hz (0-5000)
            duty_cycle: Duty cycle in percent (0-100)
            voltage: PWM voltage level in volts (default: 5.0)

        Note:
            Current hardware revision supports only 5V PWM output.
            The voltage parameter is accepted for future compatibility
            but is internally clamped to 5.0V.
        """
        # Validate frequency range
        if not 0 <= frequency <= 5000:
            raise ValueError(f"Frequency must be 0-5000 Hz, got {frequency}")

        # Validate duty cycle range
        if not 0 <= duty_cycle <= 100:
            raise ValueError(f"Duty cycle must be 0-100%, got {duty_cycle}")

        # HARDWARE LIMITATION: Current revision supports only 5V PWM
        # Future revisions may support variable voltage (5-30.5V per DBC)
        voltage = 5.0  # Fixed at 5V for current hardware
        self.disable_all_features()
        # Enable both SET_PWM (output) and GET_PWM (input/readback) in OP_MODE
        # Both are needed to set PWM and monitor actual output
        self.device._set_op_mode(self.pin_number, Feature.SET_PWM, FeatureState.OPERATE)
        self.device._set_op_mode(self.pin_number, Feature.GET_PWM, FeatureState.OPERATE)

        # Enable PWM switch for output and ICU switch for input/readback
        self.device._switch_states['pwm'][self.pin_number] = True
        self.device._switch_states['icu'][self.pin_number] = True

        # Update PWM values in device state
        self.device._pwm_out[self.pin_number] = (frequency, duty_cycle, voltage)

        self.state.pwm_frequency.set_value = frequency
        self.state.pwm_duty_cycle.set_value = duty_cycle
        self.state.pwm_voltage.set_value = voltage

        logger.debug(
            f"Pin {self.pin_number}: Set PWM to {frequency}Hz, "
            f"{duty_cycle}%, {voltage}V"
        )

        # Send immediately if value changed (Performance optimization 2.1 - change detection)
        if self.device._pwm_out != self.device._pwm_out_last:
            self.device._send_pwm_out_req()

    def get_pwm(self) -> tuple[float, float, float]:
        """
        Get last measured PWM input (via ICU - Input Capture Unit)

        Note: ICU measures only frequency and duty cycle.
        Voltage measurement is not available via ICU (always returns 0.0).

        Returns:
            Tuple of (frequency, duty_cycle, voltage)
            - frequency: Measured frequency in Hz
            - duty_cycle: Measured duty cycle in %
            - voltage: Always 0.0 (ICU cannot measure voltage)
        """
        return (
            self.state.pwm_frequency.get_value,
            self.state.pwm_duty_cycle.get_value,
            self.state.pwm_voltage.get_value  # Always 0.0 for ICU measurements
        )

    def enable_pwm_input(self):
        """
        Enable PWM input measurement (ICU) without enabling PWM output.

        Use this when you want to measure an external PWM signal without
        generating PWM output on the same pin.

        Note: ICU measures only frequency and duty cycle (no voltage).
        """
        self.disable_all_features()
        # Enable GET_PWM (ICU input) in OP_MODE
        self.device._set_op_mode(self.pin_number, Feature.GET_PWM, FeatureState.OPERATE)
        # Enable ICU switch for input measurement
        self.device._switch_states['icu'][self.pin_number] = True
        

        logger.debug(f"Pin {self.pin_number}: Enabled PWM input (ICU)")

    def enable_feature(self, feature: Feature):
        """
        Enable a feature on this pin

        Args:
            feature: Feature to enable
        """
        self.device._set_op_mode(self.pin_number, feature, FeatureState.OPERATE)
        logger.debug(f"Pin {self.pin_number}: Enabled {feature.name}")

    def disable_feature(self, feature: Feature):
        """
        Disable a feature on this pin

        Args:
            feature: Feature to disable
        """
        # Disable in OP_MODE
        self.device._set_op_mode(self.pin_number, feature, FeatureState.DISABLED)

        # Disable corresponding switch
        feature_to_switch = {
            Feature.SET_VOLTAGE: 'vlt_o',
            Feature.SET_CURRENT: 'cur_o',
            Feature.SET_PWM: 'pwm',
            Feature.GET_CURRENT: 'cur_i',
            Feature.GET_PWM: 'icu',  # ICU switch for PWM input measurement
        }
        if feature in feature_to_switch:
            switch_key = feature_to_switch[feature]
            self.device._switch_states[switch_key][self.pin_number] = False

        logger.debug(f"Pin {self.pin_number}: Disabled {feature.name}")

    def disable_all_features(self):
        """Disable all features on this pin"""
        # Disable main features
        features_to_disable = [
            Feature.GET_VOLTAGE,
            Feature.SET_VOLTAGE,
            Feature.GET_CURRENT,
            Feature.SET_CURRENT,
            Feature.GET_PWM,
            Feature.SET_PWM
        ]
        for feature in features_to_disable:
            try:
                self.disable_feature(feature)
            except Exception as e:
                logger.debug(f"Failed to disable {feature.name}: {e}")

    def get_feature_state(self, feature: Feature) -> FeatureState:
        """
        Get current state of a feature

        Args:
            feature: Feature to query

        Returns:
            Feature state
        """
        return self.state.features.get(feature, FeatureState.UNKNOWN)

    def set_relay(self, state: RelayState):
        """
        Set relay state for this pin

        This controls the physical relay that connects/disconnects the pin
        to voltage output circuitry. When CLOSED, voltage output is enabled.

        Args:
            state: Relay state (OPEN/CLOSED)
        """
        # Update internal state
        self.state.relay_state = state

        # Relay controls voltage output switch
        # When relay is CLOSED, enable voltage output switch
        # When relay is OPEN, disable voltage output switch
        if state == RelayState.CLOSED:
            self.device._switch_states['vlt_o'][self.pin_number] = True
        else:
            self.device._switch_states['vlt_o'][self.pin_number] = False

        # Send SWITCH_OUTPUT_REQ with updated states for all pins
        self.device._send_switch_output_req()

        logger.debug(f"Pin {self.pin_number}: Set relay to {state.name}")

    def has_capability(self, feature: Feature) -> bool:
        """
        Check if pin supports a feature

        Args:
            feature: Feature to check

        Returns:
            True if supported
        """
        return self.state.has_capability(feature)

    def __repr__(self) -> str:
        return f"Pin({self.pin_number})"


class DeviceUIO(DeviceSDR):
    """
    Universal Input/Output Device

    Provides control for 8 configurable pins with multiple I/O capabilities.
    """

    # Pre-computed signal names for OP_MODE (Performance optimization 2.3)
    _OP_MODE_SIGNALS = [
        f"{prefix}_{i}_op_mode"
        for prefix in ["pwm", "icu", "vlt_i", "cur_i", "vlt_o", "cur_o"]
        for i in range(1, 9)
    ]

    def __init__(self, mac_address: str, iface: str, stream_id: int, dbc_path: str):
        """
        Initialize UIO device

        Args:
            mac_address: Device MAC address
            iface: Network interface name
            stream_id: AVTP stream ID
            dbc_path: Path to DBC file
        """
        super().__init__(mac_address, iface, stream_id, dbc_path)

        # Create 8 pins
        self.pins: List[Pin] = [Pin(self, i) for i in range(8)]

        # State storage for periodic transmission
        # Operation modes: dict[pin_number][feature] = state
        self._op_modes = {i: {} for i in range(8)}

        # Output values for each pin
        self._voltages_out = [0.0] * 8  # Voltage output values (V)
        self._currents_out = [0.0] * 8  # Current output values (mA)
        # PWM output (freq, duty, voltage)
        # Note: DBC signal has offset=5V, so minimum voltage is 5V, maximum 30.5V
        # Default: 0Hz (disabled), 0% duty cycle, 5V (minimum allowed)
        # Use list comprehension to create independent tuples
        self._pwm_out = [(0.0, 0.0, 5.0) for _ in range(8)]

        # Last sent values for change detection (Performance optimization 2.1)
        self._voltages_out_last = [0.0] * 8
        self._currents_out_last = [0.0] * 8
        self._pwm_out_last = [(0.0, 0.0, 5.0) for _ in range(8)]

        # Switch/relay states for SWITCH_OUTPUT_req
        # Each feature has 8 pins, True = switch closed (feature enabled)
        self._switch_states = {
            'icu': [False] * 8,      # ICU (input capture unit)
            'pwm': [False] * 8,      # PWM
            'vlt_o': [False] * 8,    # Voltage output
            'cur_o': [False] * 8,    # Current output
            'cur_i': [False] * 8,    # Current input
        }

        logger.info(f"UIO device initialized: {mac_address}")

    def device_type(self) -> DeviceType:
        """Get device type"""
        return DeviceType.UIO

    def pin(self, pin_number: int) -> Pin:
        """
        Get pin by number

        Args:
            pin_number: Pin number (0-7)

        Returns:
            Pin object

        Raises:
            ValueError: If pin number invalid
        """
        if not 0 <= pin_number <= 7:
            raise ValueError(f"Pin number must be 0-7, got {pin_number}")
        return self.pins[pin_number]

    def _setup_periodic_tasks(self):
        """Setup periodic tasks for UIO device"""
        # Request MODULE_INFO every 4 seconds as keepalive
        self.request_module_info()
        self.task_monitor.add_task_sec(
            "module_info",
            self.request_module_info,
            4.0
        )

        # Combined periodic task for all parameters (Performance optimization 2.1)
        # Sends op_mode_req, voltage_out_req, current_out_req, pwm_out_req, switch_output_req
        # every 100ms. voltage/current/pwm also sent immediately on change via change detection.
        self.task_monitor.add_task_sec(
            "all_parameters",
            self._send_all_parameters,
            0.1
        )

    def _send_all_parameters(self):
        """
        Send all parameter updates in single periodic task (Performance optimization 2.1)
        This replaces 5 separate periodic tasks with one combined task at 100ms interval.
        """
        self._send_op_mode_req()
        self._send_voltage_out_req()
        self._send_current_out_req()
        self._send_pwm_out_req()
        self._send_switch_output_req()

    def _set_op_mode(self, pin_number: int, feature: Feature, state: FeatureState):
        """
        Set operation mode for a pin feature

        Args:
            pin_number: Pin number (0-7)
            feature: Feature type
            state: Feature state
        """
        if pin_number not in self._op_modes:
            self._op_modes[pin_number] = {}
        self._op_modes[pin_number][feature] = state

    def _send_op_mode_req(self):
        """Send OP_MODE_REQ with current state of all pins"""
        # Start with defaults using pre-computed signal names (Performance optimization 2.3)
        data = {sig: 2 for sig in self._OP_MODE_SIGNALS}  # Default: 2 = FEATURE_STATUS_DISABLED

        # Apply current operation modes from state (single pass)
        feature_map = {
            Feature.GET_VOLTAGE: "vlt_i",
            Feature.SET_VOLTAGE: "vlt_o",
            Feature.GET_CURRENT: "cur_i",
            Feature.SET_CURRENT: "cur_o",
            Feature.GET_PWM: "icu",    # Input Capture Unit for PWM measurement
            Feature.SET_PWM: "pwm",    # PWM generator for PWM output
        }

        for pin_num, modes in self._op_modes.items():
            for feature, state in modes.items():
                if feature in feature_map:
                    prefix = feature_map[feature]
                    signal_name = f"{prefix}_{pin_num + 1}_op_mode"
                    if signal_name in data:
                        data[signal_name] = state.value

        try:
            # Debug: log data before encoding
            logger.debug(f"OP_MODE_REQ data: {data}")
            self.send_can_message(PGN.OP_MODE_REQ, data)
        except Exception as e:
            logger.debug(f"Failed to send OP_MODE_REQ: {e}")

    def _send_voltage_out_req(self):
        """Send VOLTAGE_OUT_VAL_REQ with current voltage values for all pins"""
        data = {}
        for i in range(1, 9):
            signal_name = f"vlt_o_{i}_value"
            data[signal_name] = self._voltages_out[i - 1]

        try:
            self.send_can_message(PGN.VOLTAGE_OUT_VAL_REQ, data)
            # Update last sent values for change detection (Performance optimization 2.1)
            self._voltages_out_last = self._voltages_out.copy()
        except Exception as e:
            logger.debug(f"Failed to send VOLTAGE_OUT_VAL_REQ: {e}")

    def _send_current_out_req(self):
        """Send CUR_LOOP_OUT_VAL_REQ with current values for all pins"""
        data = {}
        for i in range(1, 9):
            signal_name = f"cur_ma_o_{i}_value"
            data[signal_name] = self._currents_out[i - 1]

        try:
            self.send_can_message(PGN.CUR_LOOP_OUT_VAL_REQ, data)
            # Update last sent values for change detection (Performance optimization 2.1)
            self._currents_out_last = self._currents_out.copy()
        except Exception as e:
            logger.debug(f"Failed to send CUR_LOOP_OUT_VAL_REQ: {e}")

    def _send_pwm_out_req(self):
        """Send PWM_OUT_VAL_REQ with current PWM values for all pins"""
        data = {}
        for i in range(1, 9):
            freq, duty, volt = self._pwm_out[i - 1]
            data[f"pwm_{i}_frequency"] = freq
            data[f"pwm_{i}_duty"] = duty
            data[f"pwm_{i}_voltage"] = volt

        try:
            self.send_can_message(PGN.PWM_OUT_VAL_REQ, data)
            # Update last sent values for change detection (Performance optimization 2.1)
            self._pwm_out_last = [pwm for pwm in self._pwm_out]
        except Exception as e:
            logger.debug(f"Failed to send PWM_OUT_VAL_REQ: {e}")

    def _send_switch_output_req(self):
        """Send SWITCH_OUTPUT_req with current switch states for all pins"""
        data = {}

        # Build switch data for all features and pins
        # SWITCH_OUTPUT_req has 40 bit flags (5 bytes)
        for feature_key, signal_prefix in [
            ('icu', 'sel_icu'),
            ('pwm', 'sel_pwm'),
            ('vlt_o', 'sel_vlt_o'),
            ('cur_o', 'sel_cur_o'),
            ('cur_i', 'sel_cur_i'),
        ]:
            for i in range(1, 9):
                signal_name = f"{signal_prefix}_{i}"
                # 1 if switch closed (feature enabled), 0 if open
                data[signal_name] = 1 if self._switch_states[feature_key][i - 1] else 0

        try:
            self.send_can_message(PGN.SWITCH_OUTPUT_REQ, data)
        except Exception as e:
            logger.debug(f"Failed to send SWITCH_OUTPUT_REQ: {e}")

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
            elif pgn == PGN.PIN_INFO.value:
                self._handle_pin_info(decoded)
            elif pgn == PGN.OP_MODE_ANS.value:
                self._handle_op_mode_ans(decoded)
            elif pgn == PGN.VOLTAGE_IN_ANS.value:
                self._handle_voltage_in(decoded)
            elif pgn == PGN.VOLTAGE_OUT_VAL_ANS.value:
                self._handle_voltage_out(decoded)
            elif pgn == PGN.CUR_LOOP_IN_VAL_ANS.value:
                self._handle_current_in(decoded)
            elif pgn == PGN.CUR_LOOP_OUT_VAL_ANS.value:
                self._handle_current_out(decoded)
            elif pgn == PGN.PWM_IN_ANS.value:
                self._handle_pwm_in(decoded)
            elif pgn == PGN.PWM_OUT_VAL_ANS.value:
                self._handle_pwm_out(decoded)
            elif pgn == PGN.SWITCH_OUTPUT_ANS.value:
                self._handle_switch_output(decoded)

        except Exception as e:
            logger.debug(f"Error processing UIO message PGN 0x{pgn:04X}: {e}")

    def _handle_module_info(self, decoded: Dict):
        """Handle MODULE_INFO message"""
        from ..protocol.can_messages import ModuleInfoMessage
        self.module_info = ModuleInfoMessage.from_decoded(decoded, self.mac_address)
        logger.info(f"UIO Module: {self.module_info.app_name} {self.module_info.version}")

    def _handle_module_info_ex(self, decoded: Dict):
        """Handle MODULE_INFO_EX message"""
        from ..protocol.can_messages import ModuleInfoExMessage
        info_ex = ModuleInfoExMessage.from_decoded(decoded, self.mac_address)
        if self.module_info:
            self.module_info.ip_address = info_ex.ip_address
            self.module_info.chip_uid = info_ex.chip_uid
        logger.info(f"UIO IP: {info_ex.ip_address}")

    def _handle_pin_info(self, decoded: Dict):
        """Handle PIN_INFO message"""
        pin_num = decoded.get("pin_number", 0)
        if 0 <= pin_num <= 7:
            self.pins[pin_num].state.capabilities = decoded.get("capabilities", 0)
            logger.debug(f"Pin {pin_num} capabilities: 0x{self.pins[pin_num].state.capabilities:02X}")

    def _handle_op_mode_ans(self, decoded: Dict):
        """Handle OP_MODE_ANS message"""
        pin_num = decoded.get("pin_number", 0)
        feature = decoded.get("feature", 0)
        state = decoded.get("state", 0)

        if 0 <= pin_num <= 7:
            try:
                feat_enum = Feature(feature)
                state_enum = FeatureState(state)
                self.pins[pin_num].state.features[feat_enum] = state_enum
            except ValueError:
                pass

    def _handle_voltage_in(self, decoded: Dict):
        """Handle VOLTAGE_IN_ANS message"""
        logger.debug(f"Received VOLTAGE_IN_ANS: {decoded}")
        # VOLTAGE_IN_ANS contains values for all 8 pins
        for i in range(1, 9):
            signal_name = f"vlt_i_{i}_value"
            if signal_name in decoded:
                pin_idx = i - 1  # Convert to 0-based
                self.pins[pin_idx].state.voltage.get_value = decoded[signal_name]
                logger.debug(f"Pin {pin_idx} voltage IN: {decoded[signal_name]}V")

    def _handle_voltage_out(self, decoded: Dict):
        """Handle VOLTAGE_OUT_VAL_ANS message"""
        logger.debug(f"Received VOLTAGE_OUT_VAL_ANS: {decoded}")
        # VOLTAGE_OUT_VAL_ANS contains values for all 8 pins
        for i in range(1, 9):
            signal_name = f"vlt_o_{i}_value"
            if signal_name in decoded:
                pin_idx = i - 1  # Convert to 0-based
                # Update the set_value to reflect what device acknowledged
                self.pins[pin_idx].state.voltage.set_value = decoded[signal_name]
                # Also update get_value for output monitoring
                self.pins[pin_idx].state.voltage.get_value = decoded[signal_name]
                logger.debug(f"Pin {pin_idx} voltage OUT: {decoded[signal_name]}V")

    def _handle_current_in(self, decoded: Dict):
        """Handle CUR_LOOP_IN_VAL_ANS message"""
        # CUR_LOOP_IN_VAL_ANS contains values for all 8 pins
        for i in range(1, 9):
            signal_name = f"cur_ma_i_{i}_value"
            if signal_name in decoded:
                pin_idx = i - 1
                self.pins[pin_idx].state.current.get_value = decoded[signal_name]

    def _handle_current_out(self, decoded: Dict):
        """Handle CUR_LOOP_OUT_VAL_ANS message"""
        # CUR_LOOP_OUT_VAL_ANS contains values for all 8 pins
        for i in range(1, 9):
            signal_name = f"cur_ma_o_{i}_value"
            if signal_name in decoded:
                pin_idx = i - 1
                self.pins[pin_idx].state.current.set_value = decoded[signal_name]
                #self.pins[pin_idx].state.current.get_value = decoded[signal_name]

    def _handle_pwm_in(self, decoded: Dict):
        """Handle PWM_IN_ANS message (ICU - Input Capture Unit)"""
        # PWM_IN_ANS contains ICU measurements for all 8 pins
        # ICU measures frequency and duty cycle only (no voltage measurement)
        for i in range(1, 9):
            freq_signal = f"icu_{i}_frequency"
            duty_signal = f"icu_{i}_duty"

            pin_idx = i - 1
            if freq_signal in decoded:
                self.pins[pin_idx].state.pwm_frequency.get_value = decoded[freq_signal]
            if duty_signal in decoded:
                self.pins[pin_idx].state.pwm_duty_cycle.get_value = decoded[duty_signal]
            # Note: ICU does not measure voltage, only frequency and duty cycle

    def _handle_pwm_out(self, decoded: Dict):
        """Handle PWM_OUT_VAL_ANS message"""
        # PWM_OUT_VAL_ANS contains values for all 8 pins
        for i in range(1, 9):
            freq_signal = f"pwm_{i}_frequency"
            duty_signal = f"pwm_{i}_duty"
            volt_signal = f"pwm_{i}_voltage"

            pin_idx = i - 1
            if freq_signal in decoded:
                self.pins[pin_idx].state.pwm_frequency.set_value = decoded[freq_signal]
                self.pins[pin_idx].state.pwm_frequency.get_value = decoded[freq_signal]
            if duty_signal in decoded:
                self.pins[pin_idx].state.pwm_duty_cycle.set_value = decoded[duty_signal]
                self.pins[pin_idx].state.pwm_duty_cycle.get_value = decoded[duty_signal]
            if volt_signal in decoded:
                self.pins[pin_idx].state.pwm_voltage.set_value = decoded[volt_signal]
                self.pins[pin_idx].state.pwm_voltage.get_value = decoded[volt_signal]

    def _handle_switch_output(self, decoded: Dict):
        """Handle SWITCH_OUTPUT_ANS message"""
        # SWITCH_OUTPUT_ANS contains sel_* signals for all pins/features
        # Update internal switch states based on response
        for feature_key, signal_prefix in [
            ('icu', 'sel_icu'),
            ('pwm', 'sel_pwm'),
            ('vlt_o', 'sel_vlt_o'),
            ('cur_o', 'sel_cur_o'),
            ('cur_i', 'sel_cur_i'),
        ]:
            for i in range(1, 9):
                signal_name = f"{signal_prefix}_{i}"
                if signal_name in decoded:
                    pin_idx = i - 1
                    self._switch_states[feature_key][pin_idx] = bool(decoded[signal_name])

                    # Update relay state for voltage output switch
                    if feature_key == 'vlt_o':
                        self.pins[pin_idx].state.relay_state = (
                            RelayState.CLOSED if decoded[signal_name] else RelayState.OPEN
                        )

    def disable_all_pins(self):
        """Disable all features on all pins"""
        for pin in self.pins:
            pin.disable_all_features()

    def __repr__(self) -> str:
        return f"DeviceUIO(mac={self.mac_address}, pins=8, running={self._running})"
