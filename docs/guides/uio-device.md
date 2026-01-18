# UIO Device Guide

Complete guide for Universal Input/Output (UIO) module in SDRIG SDK.

**Quick Navigation:**
- [Quick Start](#-quick-start) - Get started in 3 steps
- [Overview](#-overview) - UIO device capabilities
- [API Reference](#-api-reference) - Complete API documentation
- [Pin Features](#-pin-features) - Voltage, Current, PWM, Relay
- [Examples](#-practical-examples) - Real-world usage examples
- [Best Practices](#-best-practices) - Recommendations
- [Troubleshooting](#-troubleshooting) - Common issues

---

## 🚀 Quick Start

### 1. Connect to UIO Device

```python
from sdrig import SDRIG

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    # Connect to UIO device
    uio = sdk.connect_uio(
        "82:7B:C4:B1:92:F2",  # UIO MAC address
        auto_start=True        # Start heartbeat automatically
    )
```

### 2. Control a Pin

```python
# Set voltage output
uio.pin(0).set_voltage(12.0)  # 12V output

# Read voltage input
voltage = uio.pin(1).get_voltage()
print(f"Voltage: {voltage}V")
```

### 3. Complete Minimal Example

```python
from sdrig import SDRIG
import time

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    # Connect to UIO
    uio = sdk.connect_uio("82:7B:C4:B1:92:F2", auto_start=True)
    time.sleep(2)  # Wait for device initialization

    # Set voltage on pin 0
    uio.pin(0).set_voltage(12.0)
    print("Set 12V on pin 0")

    # Read voltage from pin 1
    time.sleep(1)
    voltage = uio.pin(1).get_voltage()
    print(f"Pin 1 voltage: {voltage}V")
```

---

## 📖 Overview

### What is UIO?

UIO (Universal Input/Output) is a versatile module with **8 configurable pins**, each supporting multiple I/O modes:

- **Voltage I/O**: 0-24V input/output
- **Current I/O**: 0-20mA input/output (4-20mA industrial standard)
- **PWM I/O**: 20Hz-5kHz input/output
- **Relay Control**: Switch relays on/off

### Key Features

| Feature | Specification |
|---------|--------------|
| **Pins** | 8 universal channels (0-7) |
| **Voltage** | 0-24V input/output |
| **Current** | 0-20mA (supports 4-20mA standard) |
| **PWM Frequency** | 20Hz - 5kHz |
| **PWM Duty Cycle** | 0-100% |
| **PWM Voltage** | 5V (current hardware) |
| **Relay** | OPEN/CLOSED control |
| **Resolution** | 12-bit ADC/DAC |

### When to Use UIO

**Use UIO for:**
- Simulating sensor signals (voltage, current)
- Testing ECU analog inputs
- Generating PWM signals for actuator control
- Reading sensor outputs
- Relay switching for power control
- 4-20mA industrial current loop

**Examples:**
- Temperature sensor simulation (voltage output)
- Pressure sensor testing (4-20mA current)
- Throttle position emulation (PWM output)
- Reading speedometer signal (PWM input)
- Controlling power relays

---

## 🔧 API Reference

### Connecting to UIO

```python
uio = sdk.connect_uio(
    mac="82:7B:C4:B1:92:F2",  # UIO MAC address
    auto_start=True           # Start heartbeat automatically
)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `mac` | str | Device MAC address |
| `auto_start` | bool | Auto-start heartbeat (default: False) |

**Returns:** `DeviceUIO` object

---

### Accessing Pins

```python
pin = uio.pin(index)  # index: 0-7
```

Each pin object provides access to all I/O features.

---

## 📍 Pin Features

### 1. Voltage I/O

#### Set Voltage Output (0-24V)

```python
uio.pin(0).set_voltage(12.0)  # Set 12V output
```

**Parameters:**
- `voltage` (float): Voltage in volts, range 0-24V

**Behavior:**
- Enables `SET_VOLTAGE` and `GET_VOLTAGE` features
- Enables voltage output switch
- Sends voltage command to device

**Example:**
```python
# Simulate temperature sensor (0-5V)
temp_celsius = 25.0
voltage = temp_celsius * 5.0 / 100.0  # 25°C → 1.25V
uio.pin(0).set_voltage(voltage)
```

#### Get Voltage Input (0-24V)

```python
voltage = uio.pin(1).get_voltage()  # Read voltage
```

**Returns:** `float` - Voltage in volts

**Example:**
```python
# Read throttle position sensor (0-5V)
voltage = uio.pin(1).get_voltage()
position_percent = (voltage / 5.0) * 100.0
print(f"Throttle: {position_percent:.1f}%")
```

---

### 2. Current I/O (4-20mA)

#### Set Current Output (0-20mA)

```python
uio.pin(2).set_tx_current(10.0)  # Set 10mA output
```

**Parameters:**
- `current` (float): Current in milliamps, range 0-20mA

**Behavior:**
- Enables `SET_CURRENT` and `GET_CURRENT` features
- Enables current output and input switches
- Sends current command to device

**Example - 4-20mA Standard:**
```python
# Simulate pressure sensor (4-20mA, 0-100 bar)
pressure_bar = 50.0  # 50 bar
current_ma = 4.0 + (pressure_bar / 100.0) * 16.0  # 12mA
uio.pin(2).set_tx_current(current_ma)
```

#### Get Current Input (0-20mA)

```python
current = uio.pin(3).get_tx_current()  # Read current
```

**Returns:** `float` - Current in milliamps

**Example - Reading 4-20mA Sensor:**
```python
# Read industrial current loop sensor
current = uio.pin(3).get_rx_current()

# Convert 4-20mA to 0-100%
if 4.0 <= current <= 20.0:
    value_percent = ((current - 4.0) / 16.0) * 100.0
    print(f"Sensor value: {value_percent:.1f}%")
elif current < 4.0:
    print("Sensor error: current below 4mA")
elif current > 20.0:
    print("Sensor error: current above 20mA")
```

---

### 3. PWM I/O

#### Set PWM Output (20Hz-5kHz)

```python
uio.pin(4).set_pwm(
    frequency=1000,   # 1kHz
    duty_cycle=50.0,  # 50%
    voltage=5.0       # 5V (current hardware)
)
```

**Parameters:**

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `frequency` | float | 20-5000 | Frequency in Hz |
| `duty_cycle` | float | 0-100 | Duty cycle in percent |
| `voltage` | float | 5.0 (fixed) | PWM voltage level |

**Note:** Current hardware supports only **5V PWM output**. The voltage parameter is accepted for future compatibility but is internally fixed to 5.0V.

**Example - Throttle Control:**
```python
# Control servo motor with PWM
frequency = 50  # 50Hz (standard servo frequency)
position_percent = 75  # 75% position

# Map 0-100% to 5-10% duty cycle (typical servo range)
duty_cycle = 5.0 + (position_percent / 100.0) * 5.0

uio.pin(4).set_pwm(frequency, duty_cycle, 5.0)
```

#### Get PWM Input (20Hz-5kHz)

```python
freq, duty, voltage = uio.pin(5).get_pwm()
```

**Returns:** `tuple[float, float, float]`
- `freq`: Frequency in Hz
- `duty`: Duty cycle in percent
- `voltage`: Always 0.0 (ICU cannot measure voltage)

**Note:** PWM input uses ICU (Input Capture Unit) which measures only frequency and duty cycle.

**Example - Reading Wheel Speed Sensor:**
```python
# Read PWM wheel speed sensor
freq, duty, _ = uio.pin(5).get_pwm()

# Calculate RPM (assuming 60 pulses per revolution)
rpm = freq * 60 / 60  # freq to RPM
print(f"Wheel speed: {rpm:.0f} RPM")
```

#### Enable PWM Input Only

```python
uio.pin(5).enable_pwm_input()
```

Use this when you want to measure an external PWM signal **without** generating PWM output on the same pin.

---

### 4. Feature Management

#### Enable Feature

```python
from sdrig.types.enums import Feature

uio.pin(0).enable_feature(Feature.GET_VOLTAGE)
```

**Available Features:**
- `Feature.GET_VOLTAGE` - Voltage input
- `Feature.SET_VOLTAGE` - Voltage output
- `Feature.GET_CURRENT` - Current input
- `Feature.SET_CURRENT` - Current output
- `Feature.GET_PWM` - PWM input (ICU)
- `Feature.SET_PWM` - PWM output

#### Disable Feature

```python
uio.pin(0).disable_feature(Feature.SET_VOLTAGE)
```

#### Disable All Features

```python
uio.pin(0).disable_all_features()
```

Disables all features on the pin and resets to idle state.

#### Check Feature State

```python
from sdrig.types.enums import FeatureState

state = uio.pin(0).get_feature_state(Feature.SET_VOLTAGE)
if state == FeatureState.OPERATE:
    print("Voltage output is active")
```

**Feature States:**
- `FeatureState.IDLE` - Feature inactive
- `FeatureState.OPERATE` - Feature active
- `FeatureState.ERROR` - Feature error
- `FeatureState.DISABLED` - Feature disabled

---

## 🎯 Practical Examples

### Example 1: Temperature Sensor Simulation

```python
from sdrig import SDRIG
import time

def simulate_temperature_sensor(uio, pin_num, temp_celsius):
    """
    Simulate temperature sensor (0-100°C → 0-5V)
    """
    voltage = (temp_celsius / 100.0) * 5.0  # Scale to 0-5V
    uio.pin(pin_num).set_voltage(voltage)
    print(f"Temperature: {temp_celsius}°C → {voltage:.2f}V")

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    uio = sdk.connect_uio("82:7B:C4:B1:92:F2", auto_start=True)
    time.sleep(2)

    # Simulate temperature ramp
    for temp in range(20, 101, 10):
        simulate_temperature_sensor(uio, pin_num=0, temp_celsius=temp)
        time.sleep(1)
```

---

### Example 2: Industrial 4-20mA Sensor

```python
from sdrig import SDRIG
import time

class PressureSensor:
    """4-20mA pressure sensor (0-100 bar)"""

    def __init__(self, uio, pin_num):
        self.uio = uio
        self.pin = pin_num

    def set_pressure(self, pressure_bar):
        """Set pressure (0-100 bar) as 4-20mA output"""
        if not 0 <= pressure_bar <= 100:
            raise ValueError("Pressure must be 0-100 bar")

        # 4-20mA standard: 4mA = 0 bar, 20mA = 100 bar
        current_ma = 4.0 + (pressure_bar / 100.0) * 16.0
        self.uio.pin(self.pin).set_tx_current(current_ma)
        print(f"Pressure: {pressure_bar:.1f} bar → {current_ma:.2f}mA")

    def read_pressure(self):
        """Read pressure from 4-20mA input"""
        current_ma = self.uio.pin(self.pin).get_rx_current()

        if current_ma < 4.0:
            raise RuntimeError("Sensor error: current below 4mA")
        elif current_ma > 20.0:
            raise RuntimeError("Sensor error: current above 20mA")

        # Convert 4-20mA to 0-100 bar
        pressure_bar = ((current_ma - 4.0) / 16.0) * 100.0
        return pressure_bar

# Usage
with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    uio = sdk.connect_uio("82:7B:C4:B1:92:F2", auto_start=True)
    time.sleep(2)

    sensor = PressureSensor(uio, pin_num=2)

    # Simulate pressure test
    for pressure in [0, 25, 50, 75, 100]:
        sensor.set_pressure(pressure)
        time.sleep(1)
```

---

### Example 3: PWM Throttle Control

```python
from sdrig import SDRIG
import time

class ThrottleController:
    """PWM throttle actuator control"""

    def __init__(self, uio, pin_num):
        self.uio = uio
        self.pin = pin_num
        self.frequency = 50  # 50Hz standard for servo motors

    def set_position(self, percent):
        """Set throttle position (0-100%)"""
        if not 0 <= percent <= 100:
            raise ValueError("Position must be 0-100%")

        # Map 0-100% to 5-10% duty cycle (typical servo range)
        duty_cycle = 5.0 + (percent / 100.0) * 5.0

        self.uio.pin(self.pin).set_pwm(
            frequency=self.frequency,
            duty_cycle=duty_cycle,
            voltage=5.0
        )
        print(f"Throttle: {percent}% (duty: {duty_cycle:.1f}%)")

    def close(self):
        """Close throttle (0%)"""
        self.set_position(0)

    def open(self):
        """Open throttle (100%)"""
        self.set_position(100)

# Usage
with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    uio = sdk.connect_uio("82:7B:C4:B1:92:F2", auto_start=True)
    time.sleep(2)

    throttle = ThrottleController(uio, pin_num=4)

    # Smooth throttle ramp
    print("Opening throttle...")
    for pos in range(0, 101, 10):
        throttle.set_position(pos)
        time.sleep(0.5)

    print("Closing throttle...")
    for pos in range(100, -1, -10):
        throttle.set_position(pos)
        time.sleep(0.5)
```

---

### Example 4: Reading PWM Wheel Speed

```python
from sdrig import SDRIG
import time

def read_wheel_speed(uio, pin_num, pulses_per_rev=60):
    """
    Read wheel speed from PWM sensor

    Args:
        uio: UIO device
        pin_num: Pin connected to sensor
        pulses_per_rev: Sensor pulses per revolution
    """
    # Enable PWM input
    uio.pin(pin_num).enable_pwm_input()
    time.sleep(0.5)

    # Read PWM frequency
    freq, duty, _ = uio.pin(pin_num).get_pwm()

    if freq > 0:
        # Calculate RPM
        rpm = (freq * 60) / pulses_per_rev

        # Calculate speed (assuming wheel diameter 0.65m)
        wheel_circumference = 0.65 * 3.14159  # meters
        speed_kmh = (rpm * wheel_circumference * 60) / 1000

        print(f"Frequency: {freq:.1f}Hz")
        print(f"RPM: {rpm:.0f}")
        print(f"Speed: {speed_kmh:.1f} km/h")
    else:
        print("No signal detected")

# Usage
with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    uio = sdk.connect_uio("82:7B:C4:B1:92:F2", auto_start=True)
    time.sleep(2)

    # Read wheel speed every second
    for _ in range(10):
        read_wheel_speed(uio, pin_num=5, pulses_per_rev=60)
        time.sleep(1)
```

---

### Example 5: Multi-Pin Test Sequence

```python
from sdrig import SDRIG
from sdrig.types.enums import RelayState
import time

def run_pin_test_sequence(uio):
    """Test all pin features in sequence"""

    print("=== UIO Pin Test Sequence ===\n")

    # Test 1: Voltage output
    print("Test 1: Voltage Output (Pin 0)")
    for voltage in [5.0, 12.0, 24.0]:
        uio.pin(0).set_voltage(voltage)
        print(f"  Set: {voltage}V")
        time.sleep(1)
    uio.pin(0).disable_all_features()

    # Test 2: Current output (4-20mA)
    print("\nTest 2: Current Output (Pin 1)")
    for current in [4.0, 12.0, 20.0]:
        uio.pin(1).set_tx_current(current)
        print(f"  Set: {current}mA")
        time.sleep(1)
    uio.pin(1).disable_all_features()

    # Test 3: PWM output
    print("\nTest 3: PWM Output (Pin 2)")
    frequencies = [100, 1000, 5000]
    for freq in frequencies:
        uio.pin(2).set_pwm(frequency=freq, duty_cycle=50.0)
        print(f"  Set: {freq}Hz @ 50% duty")
        time.sleep(1)
    uio.pin(2).disable_all_features()

    # Test 4: Relay control
    print("\nTest 4: Relay Control (Pin 3)")
    uio.pin(3).set_relay(RelayState.CLOSED)
    print("  Relay: CLOSED")
    time.sleep(1)
    uio.pin(3).set_relay(RelayState.OPEN)
    print("  Relay: OPEN")
    time.sleep(1)

    print("\n=== Test Complete ===")

# Usage
with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    uio = sdk.connect_uio("82:7B:C4:B1:92:F2", auto_start=True)
    time.sleep(2)

    run_pin_test_sequence(uio)
```

---

## 🎓 Best Practices

### 1. Always Validate Parameters

```python
def set_voltage_safe(uio, pin_num, voltage):
    """Set voltage with validation"""
    if not 0 <= pin_num <= 7:
        raise ValueError(f"Pin number must be 0-7, got {pin_num}")
    if not 0 <= voltage <= 24:
        raise ValueError(f"Voltage must be 0-24V, got {voltage}")

    uio.pin(pin_num).set_voltage(voltage)
```

### 2. Add Delays After Connection

```python
# Always wait after connecting
uio = sdk.connect_uio("MAC", auto_start=True)
time.sleep(2)  # Allow device to initialize

# Then proceed with commands
uio.pin(0).set_voltage(12.0)
```

**Recommended delays:**
- After connection: **2 seconds**
- Between commands: **100ms minimum**
- After feature changes: **500ms**

### 3. Disable Features When Done

```python
# Set voltage
uio.pin(0).set_voltage(12.0)
# ... use output ...

# Clean up when done
uio.pin(0).disable_all_features()
```

### 4. Use Context Manager

```python
# Automatic cleanup
with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    uio = sdk.connect_uio("MAC", auto_start=True)
    # ... work with UIO ...
# Device automatically stopped and cleaned up
```

### 5. Handle 4-20mA Standard Correctly

```python
# Always check for error conditions
current = uio.pin(0).get_rx_current()

if current < 4.0:
    print("ERROR: Sensor disconnected or short circuit")
elif 4.0 <= current <= 20.0:
    # Valid range
    value = ((current - 4.0) / 16.0) * 100.0
    print(f"Sensor value: {value:.1f}%")
else:
    print("ERROR: Current overload")
```

### 6. Scale PWM for Servo Control

```python
def servo_angle_to_pwm(angle_deg):
    """
    Convert servo angle to PWM duty cycle
    Typical servo: 0° = 5% duty, 180° = 10% duty
    """
    if not 0 <= angle_deg <= 180:
        raise ValueError("Angle must be 0-180°")

    duty_cycle = 5.0 + (angle_deg / 180.0) * 5.0
    return duty_cycle

# Usage
angle = 90  # 90 degrees
duty = servo_angle_to_pwm(angle)
uio.pin(0).set_pwm(frequency=50, duty_cycle=duty, voltage=5.0)
```

### 7. Enable Debug During Development

```python
# See all messages in console
with SDRIG(iface="enp0s31f6", stream_id=1, debug=True) as sdk:
    uio = sdk.connect_uio("MAC", auto_start=True)
    # All CAN messages will be logged
```

### 8. Check Feature State Before Use

```python
from sdrig.types.enums import Feature, FeatureState

# Check if feature is active
state = uio.pin(0).get_feature_state(Feature.SET_VOLTAGE)
if state != FeatureState.OPERATE:
    uio.pin(0).enable_feature(Feature.SET_VOLTAGE)
```

---

## 🐛 Debugging

### Enable Debug Logging

```python
from sdrig import SDRIGLogger

# Global debug mode
SDRIGLogger.enable_debug_mode()

# Or when creating SDK
with SDRIG(iface="enp0s31f6", stream_id=1, debug=True) as sdk:
    # All messages logged
    pass
```

### Check Device Status

```python
# Verify device is running
if uio.is_running():
    print("✓ Device is running")
else:
    print("✗ Device is not running")

# Check if device is alive
if uio.is_alive():
    print("✓ Device responding")
else:
    print("✗ Device not responding")
```

### Monitor Pin State

```python
# Get complete pin state
pin_state = uio.pin(0).state

print(f"Voltage: set={pin_state.voltage.set_value}V, "
      f"get={pin_state.voltage.get_value}V")
print(f"Current: set={pin_state.current.set_value}mA, "
      f"get={pin_state.current.get_value}mA")
print(f"PWM: {pin_state.pwm_frequency.get_value}Hz @ "
      f"{pin_state.pwm_duty_cycle.get_value}%")
```

---

## ⚠️ Troubleshooting

### Issue: ValueError - Parameter Out of Range

**Cause:** Invalid parameter value.

**Common errors:**
```python
uio.pin(0).set_voltage(30.0)      # ✗ Max is 24V
uio.pin(0).set_tx_current(25.0)      # ✗ Max is 20mA
uio.pin(0).set_pwm(10, 50, 5.0)   # ✗ Min frequency is 20Hz
```

**Solution:** Check valid ranges:
- Voltage: 0-24V
- Current: 0-20mA
- PWM frequency: 20-5000Hz
- PWM duty cycle: 0-100%
- Pin number: 0-7

---

### Issue: No Output on Pin

**Possible causes:**

1. **Feature not enabled**
   ```python
   # Enable feature explicitly
   from sdrig.types.enums import Feature
   uio.pin(0).enable_feature(Feature.SET_VOLTAGE)
   ```

2. **Insufficient delay after connection**
   ```python
   uio = sdk.connect_uio("MAC", auto_start=True)
   time.sleep(2)  # CRITICAL: wait for initialization
   ```

3. **Device not started**
   ```python
   # Check auto_start flag
   uio = sdk.connect_uio("MAC", auto_start=True)  # ✓ Correct
   ```

---

### Issue: Voltage/Current Reading Always Zero

**Causes:**

1. **Input feature not enabled**
   ```python
   # Enable GET_VOLTAGE for input
   from sdrig.types.enums import Feature
   uio.pin(0).enable_feature(Feature.GET_VOLTAGE)
   time.sleep(0.5)
   voltage = uio.pin(0).get_voltage()
   ```

2. **No signal connected**
   - Check physical connections
   - Verify signal source is active

3. **Reading too quickly**
   ```python
   # Add delay after enabling
   uio.pin(0).enable_feature(Feature.GET_VOLTAGE)
   time.sleep(1)  # Wait for measurement
   voltage = uio.pin(0).get_voltage()
   ```

---

### Issue: PWM Input Not Working

**Causes:**

1. **PWM output and input conflict**
   ```python
   # ✗ Wrong: enabling both
   uio.pin(0).set_pwm(1000, 50, 5.0)
   freq, duty, _ = uio.pin(0).get_pwm()  # Won't work

   # ✓ Correct: use separate pins
   uio.pin(0).set_pwm(1000, 50, 5.0)     # Output on pin 0
   freq, duty, _ = uio.pin(1).get_pwm()   # Input on pin 1
   ```

2. **ICU not enabled**
   ```python
   # Enable PWM input explicitly
   uio.pin(0).enable_pwm_input()
   time.sleep(0.5)
   freq, duty, _ = uio.pin(0).get_pwm()
   ```

3. **Frequency out of range**
   - ICU measures 20Hz - 5kHz
   - Signal below 20Hz may not be detected

---

### Issue: Device Not Responding

**Solutions:**

1. **Check network connection**
   ```bash
   # Verify device is on network
   python examples/01_device_discovery.py
   ```

2. **Verify MAC address**
   ```python
   # Use discovery to find correct MAC
   devices = sdk.discover_devices()
   for dev in devices:
       if dev.type == DeviceType.UIO:
           print(f"UIO MAC: {dev.mac}")
   ```

3. **Check heartbeat**
   ```python
   # Ensure auto_start=True or start manually
   uio = sdk.connect_uio("MAC", auto_start=True)

   # Or start manually
   uio.start()
   ```

---

### Issue: 4-20mA Current Loop Errors

**Diagnosis:**

```python
current = uio.pin(0).get_rx_current()

if current < 4.0:
    print("ERROR: Wire break or sensor disconnected")
    print("  - Check physical connections")
    print("  - Verify sensor power supply")
elif current > 20.0:
    print("ERROR: Short circuit or sensor overload")
    print("  - Check for short circuits")
    print("  - Verify sensor specifications")
else:
    # Normal operation (4-20mA)
    value = ((current - 4.0) / 16.0) * 100.0
    print(f"Sensor OK: {value:.1f}%")
```

---

## 📊 Technical Specifications

### Electrical Characteristics

| Parameter | Min | Typ | Max | Unit |
|-----------|-----|-----|-----|------|
| Voltage Input Range | 0 | - | 24 | V |
| Voltage Output Range | 0 | - | 24 | V |
| Voltage Accuracy | - | ±0.1 | - | V |
| Current Input Range | 0 | - | 20 | mA |
| Current Output Range | 0 | - | 20 | mA |
| Current Accuracy | - | ±0.1 | - | mA |
| PWM Frequency Range | 20 | - | 5000 | Hz |
| PWM Voltage (Output) | - | 5.0 | - | V |
| PWM Duty Cycle | 0 | - | 100 | % |
| ADC/DAC Resolution | - | 12 | - | bit |

### Pin Configuration

- **Total Pins**: 8 (numbered 0-7)
- **Simultaneous Operations**: All pins can operate independently
- **Switching Speed**: < 100ms
- **Update Rate**: 100Hz (10ms period)

---

## 🔗 Additional Resources

### Documentation
- **Main Documentation**: [`docs/README.md`](../README.md)
- **CAN Protocol Reference**: [`docs/api/can-protocol.md`](../api/can-protocol.md)
- **ELoad Device Guide**: [`docs/guides/eload-device.md`](../guides/eload-device.md)

### Examples
- **Voltage Control**: [`examples/02_uio_voltage_control.py`](../../examples/02_uio_voltage_control.py)
- **Current Control**: [`examples/02b_uio_current_control.py`](../../examples/02b_uio_current_control.py)
- **PWM Control**: [`examples/03_uio_pwm_control.py`](../../examples/03_uio_pwm_control.py)
- **PWM Input**: [`examples/03b_uio_pwm_input.py`](../../examples/03b_uio_pwm_input.py)

### API Reference
- **API Class**: `sdrig.devices.device_uio.DeviceUIO`
- **Pin Class**: `sdrig.devices.device_uio.Pin`
- **Enums**: `sdrig.types.enums.Feature`, `FeatureState`, `RelayState`

### Official Resources
- **SODA Validate**: https://docs.soda.auto/projects/soda-validate/en/latest/
- **SDRig Hardware Manual**: https://docs.soda.auto/projects/soda-validate/en/latest/software-defined-rig.html

---

## 📝 Quick Reference

### Pin Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `set_voltage(v)` | `v: 0-24V` | Set voltage output |
| `get_voltage()` | - | Get voltage input |
| `set_tx_current(i)` | `i: 0-20mA` | Set current output |
| `get_tx_current(i)` | `i: 0-20mA` | Get current output |
| `get_rx_current()` | `i: 4-20mA` | Get current input |
| `set_pwm(f, d, v)` | `f: 20-5000Hz, d: 0-100%, v: 5V` | Set PWM output |
| `get_pwm()` | - | Get PWM input (freq, duty, voltage) |
| `enable_pwm_input()` | - | Enable PWM input only |
| `set_relay(state)` | `OPEN/CLOSED` | Control relay |
| `enable_feature(f)` | `Feature` | Enable feature |
| `disable_feature(f)` | `Feature` | Disable feature |
| `disable_all_features()` | - | Disable all features |

### Common Patterns

**Set voltage:**
```python
uio.pin(0).set_voltage(12.0)
```

**Read voltage:**
```python
v = uio.pin(0).get_voltage()
```

**4-20mA output:**
```python
i = 4.0 + (value/100.0) * 16.0
uio.pin(0).set_tx_current(i)
```

**PWM output:**
```python
uio.pin(0).set_pwm(1000, 50, 5.0)
```

**Relay control:**
```python
uio.pin(0).set_relay(RelayState.CLOSED)
```

---

© 2026 SODA Validate. All rights reserved.
