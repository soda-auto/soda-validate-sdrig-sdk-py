# SDRIG CAN Messages Reference

Complete reference for all CAN messages in the SDRIG protocol.

## Message Format

All messages use the J1939 CAN ID format:
- Priority (3 bits): message priority
- PGN (18 bits): Parameter Group Number
- Source Address (8 bits): sender address

## Timing Requirements (ELoad)

### Heartbeat Messages

**MODULE_INFO_req (0x000FE):**
- Must be sent every 9 seconds (maximum 10 seconds)
- If the module doesn't receive a message for 10 seconds, it enters IDLE mode
- In IDLE mode, the module does not send data over Ethernet
- SDK automatically sends heartbeat every 9 seconds

### Periodic Messages

**All other messages:**
- Must be sent every 3 seconds (maximum 4 seconds)
- If the module doesn't receive a message for 4 seconds, it:
  - Disables the corresponding function
  - Clears the data
- SDK automatically sends OP_MODE_req, VOLTAGE_OUT, CURRENT_OUT every 3 seconds

**Note:** SDK fully automates the sending of heartbeat and periodic messages.
Users don't need to manually manage timing.

## List of All Messages (38 types)

### Device Information (3 messages)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 1 | 0x001FE | MODULE_INFO | RX | Basic module information (name, version, build date) |
| 2 | 0x008FE | MODULE_INFO_EX | RX | Extended information (IP address, MAC, Chip UID) |
| 3 | 0x002FE | MODULE_INFO_BOOT | RX | Bootloader information |

### Pin Configuration (1 message)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 4 | 0x010FE | PIN_INFO | RX | Configuration and capabilities of all pins (64 pins) |

### UIO - Operation Modes (2 messages)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 5 | 0x121FE | OP_MODE_REQ | TX | Request pin operation modes (enable/disable functions) |
| 6 | 0x120FE | OP_MODE_ANS | RX | Response with current pin operation modes |

### UIO - Voltage Input (1 message)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 7 | 0x114FE | VOLTAGE_IN_ANS | RX | Measured input voltage (mV) |

### UIO - Voltage Output (2 messages)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 8 | 0x116FE | VOLTAGE_OUT_VAL_REQ | TX | Set output voltage (mV) |
| 9 | 0x117FE | VOLTAGE_OUT_VAL_ANS | RX | Confirmation of set voltage |

### UIO - Current Input (1 message)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 10 | 0x128FE | CUR_LOOP_IN_VAL_ANS | RX | Measured input current (µA, 4-20mA current loop) |

### UIO - Current Output (2 messages)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 11 | 0x126FE | CUR_LOOP_OUT_VAL_REQ | TX | Set output current (µA, 4-20mA) |
| 12 | 0x127FE | CUR_LOOP_OUT_VAL_ANS | RX | Confirmation of set current |

### UIO - PWM Input (1 message)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 13 | 0x122FE | PWM_IN_ANS | RX | Measured PWM signal via ICU (frequency, duty cycle) |

### UIO - PWM Output (2 messages)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 14 | 0x112FE | PWM_OUT_VAL_REQ | TX | Set PWM signal (frequency, duty cycle, voltage) |
| 15 | 0x113FE | PWM_OUT_VAL_ANS | RX | Confirmation of set PWM |

### ELoad - Switch/Relay (2 messages)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 16 | 0x123FE | SWITCH_OUTPUT_REQ | TX | Control relay/switch (open/closed) |
| 17 | 0x124FE | SWITCH_OUTPUT_ANS | RX | Confirmation of relay state |

### ELoad - Voltage Control (3 messages)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 18 | 0x116FE | VOLTAGE_ELM_OUT_VAL_REQ | TX | Set output voltage (V, 0-24V, 8 channels) |
| 19 | 0x117FE | VOLTAGE_ELM_OUT_VAL_ANS | RX | Confirmation of output voltage (8 channels) |
| 20 | 0x114FE | VOLTAGE_ELM_IN_ANS | RX | Measured input voltage (V, 0-24V, 8 channels) |

### ELoad - Current Control (3 messages)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 21 | 0x129FE | CUR_ELM_OUT_VAL_REQ | TX | Set load current (A, 0-10A, 8 channels) |
| 22 | 0x12BFE | CUR_ELM_OUT_VAL_ANS | RX | Confirmation of load current (8 channels) |
| 23 | 0x12AFE | CUR_ELM_IN_VAL_ANS | RX | Measured current (A, 0-11A, 8 channels) |

### ELoad - Temperature (1 message)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 24 | 0x12EFE | TEMP_ELM_IN_ANS | RX | Load channel temperature (°C, 8 channels) |

### ELoad - Digital Output (2 messages)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 25 | 0x12CFE | SWITCH_ELM_DOUT_REQ | TX | Control digital outputs (4 relays) |
| 26 | 0x12DFE | SWITCH_ELM_DOUT_ANS | RX | State of digital outputs (4 relays) |

### IfMux - CAN Configuration (2 messages)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 21 | 0x021FE | CAN_INFO_REQ | TX | Set CAN speed (classic and FD) for 8 channels |
| 22 | 0x020FE | CAN_INFO_ANS | RX | Confirmation of CAN configuration |

### IfMux - CAN State (1 message)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 23 | 0x022FE | CAN_STATE_ANS | RX | CAN bus state and last error code (LEC) |

### IfMux - CAN Multiplexer (2 messages)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 24 | 0x028FE | CAN_MUX_REQ | TX | Control CAN relay (internal/external bus) |
| 25 | 0x029FE | CAN_MUX_ANS | RX | Confirmation of CAN relay configuration |

### IfMux - LIN Configuration (1 message)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 26 | 0x040FE | LIN_CFG_REQ | TX | Configuration of LIN frames (ID, direction, checksum) for 62 frames |

### IfMux - LIN Data (2 messages)

| # | PGN | Name | Direction | Description |
|---|-----|------|-----------|-------------|
| 27 | 0x042FE | LIN_FRAME_SET_REQ | TX | Send LIN frame data (up to 8 bytes) |
| 28 | 0x043FE | LIN_FRAME_RCVD_ANS | RX | Receive LIN frame data |

## Detailed Descriptions

### MODULE_INFO (0x001FE)
**Size:** 64 bytes
**Period:** On request + keepalive every 5 sec
**Fields:**
- `sys_runtime_s`: System uptime (seconds)
- `module_status`: Module status
- `module_app_fw_name_1/2/3`: Firmware name (24 bytes ASCII)
- `module_app_ver_*`: Version (gen.major.minor.fix.build)
- `module_app_build_*`: Build date and time
- `module_app_hw_name_1/2`: Hardware name (16 bytes ASCII)
- `module_app_crc`: Firmware CRC32

### MODULE_INFO_EX (0x008FE)
**Size:** 32 bytes
**Period:** On request
**Fields:**
- `module_mac_addr`: MAC address (6 bytes)
- `module_ip_addr`: IP address (4 bytes)
- `module_chip_uid_1/2`: Unique chip ID (16 bytes)

### PIN_INFO (0x010FE)
**Size:** 64 bytes
**Period:** On request
**Fields:**
- `pin_info_pin_1_capabilities` ... `pin_info_pin_64_capabilities`: Bitmask of capabilities for each pin

### OP_MODE_REQ/ANS (0x121FE / 0x120FE)
**Size:** 48 bytes
**Period:** On command / immediate response
**Fields (for each function and pin 1-8):**
- `pwm_1_op_mode` ... `pwm_8_op_mode`: PWM generator mode (for PWM output)
- `icu_1_op_mode` ... `icu_8_op_mode`: ICU mode (Input Capture Unit, for PWM measurement)
- `vlt_i_1_op_mode` ... `vlt_i_8_op_mode`: Input voltage mode
- `cur_i_1_op_mode` ... `cur_i_8_op_mode`: Input current mode
- `vlt_o_1_op_mode` ... `vlt_o_8_op_mode`: Output voltage mode
- `cur_o_1_op_mode` ... `cur_o_8_op_mode`: Output current mode

**Mode values:**
- 0: DISABLED
- 1: ENABLED
- 2: ENABLED_CONTINUOUS
- 3: ENABLED_READ_ONLY

**Note:**
- For PWM generation (output), use `pwm_X_op_mode`
- For PWM measurement (input), use `icu_X_op_mode`

### VOLTAGE_OUT_VAL_REQ/ANS (0x116FE / 0x117FE)
**Size:** 64 bytes
**Period:** On command / immediate response
**Fields:**
- `vlt_o_1_value` ... `vlt_o_8_value`: Voltage in mV (0-240FE)

### VOLTAGE_IN_ANS (0x114FE)
**Size:** 64 bytes
**Period:** Periodically every 100ms
**Fields:**
- `vlt_i_1_value` ... `vlt_i_8_value`: Measured voltage in mV

### CUR_LOOP_OUT_VAL_REQ/ANS (0x126FE / 0x127FE)
**Size:** 64 bytes
**Period:** On command / immediate response
**Fields:**
- `cur_ma_o_1_value` ... `cur_ma_o_8_value`: Current in µA (4000-20000 for 4-20mA)

### CUR_LOOP_IN_VAL_ANS (0x128FE)
**Size:** 64 bytes
**Period:** Periodically every 100ms
**Fields:**
- `cur_ma_i_1_value` ... `cur_ma_i_8_value`: Measured current in µA

### PWM_OUT_VAL_REQ/ANS (0x112FE / 0x113FE)
**Size:** 64 bytes
**Period:** On command / immediate response
**Fields (for each pin 1-8):**
- `pwm_1_frequency` ... `pwm_8_frequency`: Frequency in Hz (20-5000 Hz)
- `pwm_1_duty` ... `pwm_8_duty`: Duty cycle in % (0-1FE)
- `pwm_1_voltage` ... `pwm_8_voltage`: Voltage in mV (field present but ignored)

**Note:**
Current hardware revision generates PWM only at **5V (fixed value)**.
The `voltage` field is present in the protocol for compatibility with future versions,
but in the current version it is always ignored and a fixed value of 5000 mV is used.

### PWM_IN_ANS (0x122FE)
**Size:** 32 bytes
**Period:** Periodically every 100ms
**Measurement method:** ICU (Input Capture Unit)
**Fields (for each pin 1-8):**
- `icu_1_frequency` ... `icu_8_frequency`: Measured frequency in Hz
- `icu_1_duty` ... `icu_8_duty`: Measured duty cycle in % (0-1FE)

**Note:** ICU does not measure voltage, only timing parameters of the signal (frequency and duty cycle)

### SWITCH_OUTPUT_REQ/ANS (0x123FE / 0x124FE)
**Size:** 8 bytes
**Period:** On command / immediate response
**Fields (for each pin 1-8):**
- `sel_icu_1` ... `sel_icu_8`: ICU relay (Input Capture Unit for PWM measurement)
- `sel_pwm_1` ... `sel_pwm_8`: PWM generator relay (for PWM generation)
- `sel_vlt_o_1` ... `sel_vlt_o_8`: Output voltage relay
- `sel_cur_o_1` ... `sel_cur_o_8`: Output current relay
- `sel_cur_i_1` ... `sel_cur_i_8`: Input current relay

**Values:** 0 = relay open (disabled), 1 = relay closed (enabled)

**Important:**
- For PWM generation, the `sel_pwm` relay must be enabled
- For PWM measurement (via ICU), the `sel_icu` relay must be enabled
- SDK automatically controls relays when using `set_pwm()` and `enable_pwm_input()` methods

### VOLTAGE_ELM_OUT_VAL_REQ/ANS (0x116FE / 0x117FE)
**Size:** 16 bytes
**Period:** Every 3 seconds (max 4s) / immediate response
**Fields (for each channel 1-8):**
- `vlt_o_1_value` ... `vlt_o_8_value`: Output voltage in V (0-24.0)

**Description:**
Sets ELoad to voltage source mode (power supply mode).
Channel generates the specified voltage at the output (0-24V).

**Note:**
- Voltage source mode is mutually exclusive with current sink mode
- SDK automatically disables current sink when enabling voltage source
- Requires enabling OP_MODE for vlt_o (voltage output)

### VOLTAGE_ELM_IN_ANS (0x114FE)
**Size:** 16 bytes
**Period:** Periodically every second
**Fields (for each channel 1-8):**
- `vlt_i_1_value` ... `vlt_i_8_value`: Measured voltage in V (0-24.0)

**Description:**
Measures input voltage on the channel. Works in all modes:
- In current sink mode: measures input voltage from source
- In voltage source mode: measures output voltage
- In disabled mode: measures external voltage (high impedance)

### CUR_ELM_OUT_VAL_REQ/ANS (0x129FE / 0x12BFE)
**Size:** 16 bytes
**Period:** Every 3 seconds (max 4s) / immediate response
**Fields (for each channel 1-8):**
- `cur_o_1_value` ... `cur_o_8_value`: Load current in A (0-10.0)

**Description:**
Sets ELoad to electronic load mode (current sink mode).
Channel sinks the specified current from the power source (0-10A).

**Note:**
- Current sink mode is mutually exclusive with voltage source mode
- SDK automatically disables voltage source when enabling current sink
- Requires enabling OP_MODE for cur_o (current output)
- Maximum power: 200W per channel, 600W total

### CUR_ELM_IN_VAL_ANS (0x12AFE)
**Size:** 16 bytes
**Period:** Periodically every second
**Fields (for each channel 1-8):**
- `cur_i_1_value` ... `cur_i_8_value`: Measured current in A (0-11.0)

**Description:**
Measures current through the channel. Works in different modes:
- In current sink mode: measures sinking current
- In voltage source mode: measures load current

### TEMP_ELM_IN_ANS (0x12EFE)
**Size:** 8 bytes
**Period:** Periodically every second
**Fields (for each channel 1-8):**
- `temp_i_1_value` ... `temp_i_8_value`: Temperature in °C (0-150)

**Description:**
Temperature monitoring of each channel. Used for overheat protection.

**Note:**
It is recommended to limit current/power when temperature >80°C.

### SWITCH_ELM_DOUT_REQ/ANS (0x12CFE / 0x12DFE)
**Size:** 8 bytes
**Period:** On command / immediate response
**Fields (for each relay 1-4):**
- `dout_1_en` ... `dout_4_en`: Relay state (0=open, 1=closed)

**Description:**
Control of 4 digital outputs (open collector). Used for:
- Controlling external devices
- Interlock signals
- Status indication
- Test sequences

**Electrical characteristics:**
- Type: Open collector
- Maximum current: according to module specification
- Levels: TTL/CMOS compatible

### CAN_INFO_REQ/ANS (0x021FE / 0x020FE)
**Size:** 64 bytes
**Period:** On command / immediate response
**Fields (for each channel 1-8):**
- `can1_speed` ... `can8_speed`: Classic CAN speed (kbit/s)
- `can1_speed_fd` ... `can8_speed_fd`: CAN-FD speed (kbit/s)

**Standard speeds:**
- Classic: 125, 250, 500, 1000 kbit/s
- CAN-FD: 2000, 4000, 8000 kbit/s

### CAN_STATE_ANS (0x022FE)
**Size:** 16 bytes
**Period:** Periodically every second
**Fields (for each channel 1-8):**
- `can_state_1` ... `can_state_8`: State (0=disabled, 1=running, 2=error)
- `can_lec_1` ... `can_lec_8`: Last Error Code (LEC)

### CAN_MUX_REQ/ANS (0x028FE / 0x029FE)
**Size:** 16 bytes
**Period:** On command / immediate response
**Fields (for each channel 1-8):**
- `can_mux_int_can1_en` ... `can_mux_int_can8_en`: Connection to internal bus
- `can_mux_ext_can1_out` ... `can_mux_ext_can8_out`: Connection to external bus

### LIN_CFG_REQ (0x040FE)
**Size:** 64 bytes (configuration for 62 frames)
**Period:** On command
**Fields (for each frame 1-62):**
- `lin_cfg_frm1_enable` ... `lin_cfg_frm62_enable`: Whether frame is enabled
- `lin_cfg_frm1_direction` ... : Direction (0=RX, 1=TX)
- `lin_cfg_frm1_checksum_type` ... : Checksum type (0=classic, 1=enhanced)

### LIN_FRAME_SET_REQ (0x042FE)
**Size:** Variable (up to 16 bytes)
**Period:** On command
**Fields:**
- `lin_frame_id`: Frame ID (0-0x3F)
- `lin_frame_data_1` ... `lin_frame_data_8`: Frame data (up to 8 bytes)

### LIN_FRAME_RCVD_ANS (0x043FE)
**Size:** Variable (up to 16 bytes)
**Period:** When frame is received
**Fields:**
- `lin_frame_id`: Received frame ID
- `lin_frame_data_1` ... `lin_frame_data_8`: Frame data

## Notes

### PGN Format (J1939)
- **PDU1 Format** (PF < 0xF0): PGN = (Priority << 18) | (PF << 8) | PS
  - PS = Destination Address (0x00 for specific device, 0xFF for broadcast)
  - Examples: MODULE_INFO (0x001FE), CAN_INFO_ANS (0x020FE)

- **PDU2 Format** (PF >= 0xF0): PGN = (Priority << 18) | (PF << 8) | (PGN Extension)
  - Always broadcast
  - Examples: OP_MODE_ANS (0x120FE), VOLTAGE_IN_ANS (0x114FE)

### Extended Frame Format
All messages use 29-bit Extended CAN ID (EFF flag set).

### CAN-FD Support
UIO, ELoad, IfMux support CAN-FD format for extended data (up to 64 bytes).

### Source Address
By default, SDK uses:
- 0xFE for sending commands (wildcard)
- Devices respond with their real address

---

**Last Updated**: 2026-01-17
**Protocol Version**: 1.0
**SDK Version**: 0.1.0
