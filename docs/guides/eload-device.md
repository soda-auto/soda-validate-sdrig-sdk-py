# Electronic Load Module (ELM) - Complete Guide

## Overview

The Electronic Load Module (ELM) is a versatile hardware component with 8 channels that supports three operational modes:

1. **Current Sink Mode (Electronic Load)**: 0-10A per channel
2. **Voltage Source Mode (Power Supply)**: 0-24V output
3. **Voltage Measurement Mode**: Measure voltage when disabled

## Hardware Specifications

- **Channels**: 8 independent channels
- **Current Range**: 0-10A per channel (sink mode)
- **Voltage Range**: 0-24V (source/measurement mode)
- **Power Limits**:
  - Per channel: 200W max
  - Total: 600W max
- **Digital Outputs**: 4 relay outputs (dout_1 to dout_4)
- **Temperature Monitoring**: Per-channel temperature sensors

## Communication Protocol

### Timing Requirements

Per ELoad documentation, messages must be sent at specific intervals:

- **MODULE_INFO_req**: Every 9 seconds (max 10s)
  - If not received for 10s, module goes to IDLE mode
- **Other messages**: Every 3 seconds (max 4s)
  - If not received for 4s, module disables corresponding function

The SDK handles this automatically via periodic tasks.

### CAN Messages

| PGN | Name | Direction | Description |
|-----|------|-----------|-------------|
| 0x121FF | OP_MODE_req | TX | Request operational modes (voltage/current input/output) |
| 0x120FF | OP_MODE_ans | RX | Operational mode response |
| 0x116FF | VOLTAGE_ELM_OUT_VAL_REQ | TX | Set voltage output (8 channels) |
| 0x117FF | VOLTAGE_ELM_OUT_VAL_ANS | RX | Voltage output confirmation |
| 0x114FF | VOLTAGE_ELM_IN_ANS | RX | Voltage input measurement (8 channels) |
| 0x129FF | CUR_ELM_OUT_VAL_REQ | TX | Set current output (8 channels) |
| 0x12BFF | CUR_ELM_OUT_VAL_ANS | RX | Current output confirmation |
| 0x12AFF | CUR_ELM_IN_VAL_ANS | RX | Current input measurement (8 channels) |
| 0x12EFF | TEMP_ELM_IN_ANS | RX | Temperature measurement (8 channels) |
| 0x12CFF | SWITCH_ELM_DOUT_REQ | TX | Digital output relay control (4 relays) |
| 0x12DFF | SWITCH_ELM_DOUT_ANS | RX | Digital output relay status |

## Operating Modes

### Mode 1: Current Sink (Electronic Load)

Use ELoad as an electronic load to sink current from a power source.

```python
from sdrig import SDRIG

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    eload = sdk.connect_eload("86:12:35:9B:FD:45", auto_start=True)

    # Set current sink value
    eload.channel(0).set_current(2.5)  # Sink 2.5A

    # Monitor measurements
    voltage = eload.channel(0).get_voltage()  # Input voltage
    current = eload.channel(0).get_current()  # Measured current
    power = eload.channel(0).get_power()      # Power dissipation (V*I)
    temp = eload.channel(0).get_temperature() # Channel temperature

    print(f"Load: {voltage:.2f}V, {current:.3f}A, {power:.2f}W, {temp:.1f}°C")
```

**Features:**
- Range: 0-10A per channel
- Automatic voltage measurement while sinking current
- Power and temperature monitoring
- Disables voltage source mode automatically

### Mode 2: Voltage Source (Power Supply)

Use ELoad as a voltage source (power supply mode).

```python
from sdrig import SDRIG

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    eload = sdk.connect_eload("86:12:35:9B:FD:45", auto_start=True)

    # Set voltage output
    eload.channel(0).set_voltage(12.0)  # Output 12V

    # Monitor measurements
    voltage = eload.channel(0).get_voltage()  # Output voltage
    current = eload.channel(0).get_current()  # Load current
    power = eload.channel(0).get_power()      # Power delivered
    temp = eload.channel(0).get_temperature() # Channel temperature

    print(f"Supply: {voltage:.2f}V, {current:.3f}A, {power:.2f}W, {temp:.1f}°C")
```

**Features:**
- Range: 0-24V output
- Current measurement of connected load
- Power and temperature monitoring
- Disables current sink mode automatically

### Mode 3: Voltage Measurement (Disabled)

Measure external voltage when both current sink and voltage source are disabled.

```python
from sdrig import SDRIG

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    eload = sdk.connect_eload("86:12:35:9B:FD:45", auto_start=True)

    # Disable all modes
    eload.channel(0).set_current(0.0)  # Disable current sink
    eload.channel(0).set_voltage(0.0)  # Disable voltage source

    # Measure external voltage
    voltage = eload.channel(0).get_voltage()
    print(f"Measured voltage: {voltage:.2f}V")
```

**Features:**
- High-impedance voltage measurement
- No power consumption
- Useful for monitoring without loading

## Multiple Channels

All channels are independent and can operate in different modes simultaneously.

```python
from sdrig import SDRIG

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    eload = sdk.connect_eload("86:12:35:9B:FD:45", auto_start=True)

    # Channel 0: Current sink (load testing)
    eload.channel(0).set_current(5.0)  # 5A load

    # Channel 1: Voltage source (power supply)
    eload.channel(1).set_voltage(12.0)  # 12V output

    # Channel 2: Voltage measurement only
    eload.channel(2).set_current(0.0)
    eload.channel(2).set_voltage(0.0)

    # Monitor all channels
    for i in range(3):
        v = eload.channel(i).get_voltage()
        c = eload.channel(i).get_current()
        p = eload.channel(i).get_power()
        print(f"Ch{i}: {v:.2f}V, {c:.3f}A, {p:.2f}W")

    # Total power across all channels
    total = eload.get_total_power()
    print(f"Total: {total:.2f}W (max 600W)")
```

## Digital Output Relays

ELoad provides 4 digital output relays (open collector outputs).

```python
from sdrig import SDRIG

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    eload = sdk.connect_eload("86:12:35:9B:FD:45", auto_start=True)

    # Control relays (0-3 = dout_1 to dout_4)
    eload.set_relay(0, closed=True)   # Close relay 0 (dout_1)
    eload.set_relay(1, closed=False)  # Open relay 1 (dout_2)

    # Read relay states
    for relay_id in range(4):
        state = eload.get_relay(relay_id)
        print(f"Relay {relay_id+1}: {'CLOSED' if state else 'OPEN'}")
```

**Use Cases:**
- External device control
- Interlock signals
- Status indicators
- Test sequencing

## Power Management

### Per-Channel Power Limit

Each channel has a maximum power dissipation of 200W.

```python
# Calculate safe current for given voltage
max_channel_power = 200.0  # W
input_voltage = 12.0       # V

safe_current = max_channel_power / input_voltage
print(f"Safe current at {input_voltage}V: {safe_current:.2f}A")

# Set current with safety check
if input_voltage * target_current <= max_channel_power:
    eload.channel(0).set_current(target_current)
else:
    print("Warning: Exceeds 200W channel limit")
```

### Total Power Limit

Total power across all channels is limited to 600W.

```python
# Monitor total power
total_power = eload.get_total_power()
if total_power > 600.0:
    print("Warning: Exceeds 600W total limit")
    eload.disable_all_channels()
```

## Temperature Monitoring

Each channel includes temperature monitoring.

```python
from sdrig import SDRIG
import time

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    eload = sdk.connect_eload("86:12:35:9B:FD:45", auto_start=True)

    # Set high current load
    eload.channel(0).set_current(8.0)

    # Monitor temperature
    for _ in range(10):
        temp = eload.channel(0).get_temperature()
        print(f"Temperature: {temp:.1f}°C")

        # Safety check
        if temp > 80.0:
            print("Warning: High temperature!")
            eload.channel(0).set_current(0.0)
            break

        time.sleep(1)
```

## Best Practices

### 1. Gradual Current Ramping

Avoid sudden current changes to prevent voltage spikes.

```python
def ramp_current(channel, target_current, step=1.0, delay=0.5):
    """Gradually ramp current to target"""
    current = 0.0
    while current < target_current:
        current = min(current + step, target_current)
        channel.set_current(current)
        time.sleep(delay)
```

### 2. Power Monitoring

Always monitor power to stay within limits.

```python
def safe_set_current(eload, channel_id, current):
    """Set current with power limit check"""
    # Set current
    eload.channel(channel_id).set_current(current)
    time.sleep(0.5)

    # Check power
    power = eload.channel(channel_id).get_power()
    if power > 200.0:
        print(f"Warning: Channel power {power:.1f}W exceeds 200W limit")
        eload.channel(channel_id).set_current(0.0)
        return False

    # Check total power
    total = eload.get_total_power()
    if total > 600.0:
        print(f"Warning: Total power {total:.1f}W exceeds 600W limit")
        eload.disable_all_channels()
        return False

    return True
```

### 3. Temperature Protection

Implement thermal protection for high-power tests.

```python
def temperature_protected_test(channel, current, max_temp=75.0):
    """Run test with temperature protection"""
    channel.set_current(current)

    while True:
        temp = channel.get_temperature()
        if temp > max_temp:
            print(f"Temperature limit reached: {temp:.1f}°C")
            channel.set_current(0.0)
            break

        time.sleep(1)
```

### 4. Mode Switching

Always disable conflicting modes explicitly.

```python
# Switch from current sink to voltage source
eload.channel(0).set_current(0.0)  # Disable current sink first
time.sleep(0.5)
eload.channel(0).set_voltage(12.0)  # Enable voltage source

# Switch from voltage source to current sink
eload.channel(0).set_voltage(0.0)  # Disable voltage source first
time.sleep(0.5)
eload.channel(0).set_current(5.0)  # Enable current sink
```

## Common Use Cases

### Battery Discharge Testing

```python
def battery_discharge_test(eload, channel_id, discharge_current, cutoff_voltage):
    """Test battery discharge capacity"""
    eload.channel(channel_id).set_current(discharge_current)

    capacity_ah = 0.0
    start_time = time.time()

    while True:
        voltage = eload.channel(channel_id).get_voltage()
        current = eload.channel(channel_id).get_current()

        if voltage < cutoff_voltage:
            break

        elapsed_hours = (time.time() - start_time) / 3600
        capacity_ah = discharge_current * elapsed_hours

        print(f"{voltage:.2f}V, {current:.3f}A, {capacity_ah:.3f}Ah")
        time.sleep(10)

    eload.channel(channel_id).set_current(0.0)
    return capacity_ah
```

### Power Supply Testing

```python
def power_supply_load_test(eload, channel_id, test_currents):
    """Test power supply under various loads"""
    for current in test_currents:
        eload.channel(channel_id).set_current(current)
        time.sleep(2)

        voltage = eload.channel(channel_id).get_voltage()
        actual_current = eload.channel(channel_id).get_current()

        # Check voltage regulation
        regulation_error = abs(voltage - 12.0) / 12.0 * 100
        print(f"{actual_current:.3f}A: {voltage:.3f}V (error: {regulation_error:.2f}%)")
```

## Troubleshooting

### Issue: Voltage measurement reads 0V

**Solution:**
- Ensure OP_MODE is enabled for voltage input
- Check connection to voltage source
- Verify heartbeat messages are being sent

### Issue: Current not sinking as expected

**Solution:**
- Check power limit (200W per channel, 600W total)
- Verify input voltage is sufficient
- Monitor temperature (thermal throttling may occur)

### Issue: Relay not switching

**Solution:**
- Verify correct relay ID (0-3 for dout_1 to dout_4)
- Check SWITCH_ELM_DOUT messages are being sent
- Ensure heartbeat is active

## API Reference

### ELoadChannel Methods

- `set_current(current: float)` - Set current sink (0-10A)
- `set_voltage(voltage: float)` - Set voltage source (0-24V)
- `get_current() -> float` - Get measured current
- `get_voltage() -> float` - Get measured voltage
- `get_power() -> float` - Get calculated power (V*I)
- `get_temperature() -> float` - Get channel temperature
- `disable()` - Disable channel (set current to 0)

### DeviceELoad Methods

- `channel(channel_id: int) -> ELoadChannel` - Get channel object (0-7)
- `set_relay(relay_id: int, closed: bool)` - Control relay (0-3)
- `get_relay(relay_id: int) -> bool` - Get relay state
- `get_total_power() -> float` - Get total power across all channels
- `disable_all_channels()` - Disable all channels

## See Also

- [Main README](../README.md)
- [CAN Messages Reference](api/can-protocol.md)
- [Example: ELoad Control](../examples/04_eload_control.py)
