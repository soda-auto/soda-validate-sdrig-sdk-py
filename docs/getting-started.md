# Getting Started with SDRIG SDK

Welcome to the SDRIG Python SDK! This guide will help you get started with controlling SDRIG hardware modules.

**What You'll Learn:**
- [Installation](#-installation) - Install the SDK
- [Basic Concepts](#-basic-concepts) - Understand SDRIG components
- [First Steps](#-first-steps) - Your first program
- [Common Tasks](#-common-tasks) - Practical examples
- [Next Steps](#-next-steps) - Where to go from here

---

## 📦 Installation

### Prerequisites

**Python Version:**
- Python 3.8 or higher

**Operating System:**
- Linux (recommended)
- Windows (with WSL)

**Network:**
- Ethernet interface
- Access to SDRIG devices on network

---

### Install from Source

```bash
# Clone repository (if not already done)
git clone https://github.com/soda-auto/soda-validate-sdrig-sdk-py.git
cd soda-validate-sdrig-sdk-py

# Install in development mode
pip install -e .

# Verify installation
python -c "import sdrig; print(sdrig.__version__)"
```

---

### Install Development Dependencies (Optional)

```bash
# Install with testing and documentation tools
pip install -e ".[dev]"
```

This includes:
- `pytest` - Unit testing
- `pytest-cov` - Coverage reporting
- Additional development tools

---

## 🧩 Basic Concepts

### What is SDRIG?

**SDRIG** (Software-Defined Remote Interface Gateway) is a modular hardware platform for automotive testing and simulation.

### Hardware Components

The SDRIG system consists of three main device types:

#### 1. UIO - Universal Input/Output
**Purpose**: Simulate and measure analog signals

**Capabilities:**
- 8 configurable pins
- Voltage I/O: 0-24V
- Current I/O: 0-20mA (4-20mA industrial standard)
- PWM I/O: 20Hz-5kHz

**Use Cases:**
- Temperature sensor simulation
- Pressure sensor testing
- Throttle position emulation
- Actuator control

---

#### 2. ELoad - Electronic Load
**Purpose**: Current sinking and power measurement

**Capabilities:**
- 8 channels
- Current sink: 0-10A per channel
- Voltage measurement: 0-24V
- Power limits: 200W/channel, 600W total
- Temperature monitoring
- Relay control

**Use Cases:**
- Battery discharge testing
- Power supply testing
- Load simulation
- Power consumption analysis

---

#### 3. IfMux - Interface Multiplexer
**Purpose**: CAN and LIN network communication

**Capabilities:**
- 8 CAN FD channels (up to 5 Mbps)
- LIN 2.0 interface
- Internal/external relay matrix
- State monitoring

**Use Cases:**
- Multi-network CAN simulation
- ECU communication testing
- Gateway testing
- LIN bus communication

---

### Communication Protocol

**AVTP (Audio Video Transport Protocol)**
- Layer 2 Ethernet protocol
- IEEE 1722 standard
- ACF-CAN encapsulation for CAN messages
- Raw socket communication

---

## 🎯 First Steps

### Step 1: Check Network Connection

```bash
# List network interfaces
ip link show

# Note your interface name (e.g., enp0s31f6, eth0, ens33)
```

---

### Step 2: Discover Devices

Create a file `discover.py`:

```python
from sdrig import SDRIG

# Replace with your network interface
IFACE = "enp0s31f6"
STREAM_ID = 1

with SDRIG(iface=IFACE, stream_id=STREAM_ID) as sdk:
    print("Discovering SDRIG devices...")
    devices = sdk.discover_devices(timeout=3.0)

    if not devices:
        print("No devices found!")
        print("- Check network connection")
        print("- Verify devices are powered on")
        print("- Check interface name")
    else:
        print(f"\nFound {len(devices)} device(s):\n")
        for dev in devices:
            print(f"Type: {dev.type.name}")
            print(f"MAC: {dev.mac}")
            print(f"Version: {dev.hardware_version}.{dev.software_version}")
            print(f"Serial: {dev.serial_number}")
            print("-" * 40)
```

**Run:**
```bash
python discover.py
```

**Expected Output:**
```
Discovering SDRIG devices...

Found 3 device(s):

Type: UIO
MAC: 82:7B:C4:B1:92:F2
Version: 1.0
Serial: UIO001
----------------------------------------
Type: ELOAD
MAC: 76:4D:28:9A:3E:C1
Version: 1.0
Serial: ELOAD001
----------------------------------------
Type: IFMUX
MAC: 66:6A:DB:B3:06:27
Version: 1.0
Serial: IFMUX001
----------------------------------------
```

---

### Step 3: Your First Program

Let's control a UIO device to set a voltage output.

Create `first_program.py`:

```python
from sdrig import SDRIG
import time

# Configuration
IFACE = "enp0s31f6"
STREAM_ID = 1
UIO_MAC = "82:7B:C4:B1:92:F2"  # Replace with your UIO MAC

with SDRIG(iface=IFACE, stream_id=STREAM_ID) as sdk:
    print("Connecting to UIO device...")

    # Connect to UIO device
    uio = sdk.connect_uio(UIO_MAC, auto_start=True)
    time.sleep(2)  # Wait for device to initialize

    print("UIO device connected!")

    # Set voltage on pin 0
    voltage = 12.0
    print(f"Setting pin 0 to {voltage}V...")
    uio.pin(0).set_voltage(voltage)

    print("Success! Voltage is now set.")
    print("Press Ctrl+C to exit...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")
```

**Run:**
```bash
python first_program.py
```

**Expected Output:**
```
Connecting to UIO device...
UIO device connected!
Setting pin 0 to 12.0V...
Success! Voltage is now set.
Press Ctrl+C to exit...
```

**🎉 Congratulations!** You've just controlled your first SDRIG device!

---

## 🔧 Common Tasks

### Task 1: Read Sensor Input

**Scenario**: Read voltage from a sensor connected to UIO pin 1.

```python
from sdrig import SDRIG
import time

IFACE = "enp0s31f6"
UIO_MAC = "82:7B:C4:B1:92:F2"

with SDRIG(iface=IFACE, stream_id=1) as sdk:
    uio = sdk.connect_uio(UIO_MAC, auto_start=True)
    time.sleep(2)

    # Enable voltage input on pin 1
    from sdrig.types.enums import Feature
    uio.pin(1).enable_feature(Feature.GET_VOLTAGE)
    time.sleep(1)  # Wait for measurement

    # Read voltage
    voltage = uio.pin(1).get_voltage()
    print(f"Sensor voltage: {voltage:.2f}V")
```

---

### Task 2: Generate PWM Signal

**Scenario**: Control a servo motor with PWM.

```python
from sdrig import SDRIG
import time

IFACE = "enp0s31f6"
UIO_MAC = "82:7B:C4:B1:92:F2"

with SDRIG(iface=IFACE, stream_id=1) as sdk:
    uio = sdk.connect_uio(UIO_MAC, auto_start=True)
    time.sleep(2)

    # Generate 50Hz PWM with 7.5% duty cycle (servo center position)
    frequency = 50    # 50Hz for servo
    duty_cycle = 7.5  # 7.5% = center position

    print("Controlling servo to center position...")
    uio.pin(2).set_pwm(frequency, duty_cycle, 5.0)

    time.sleep(2)

    # Move to 90 degrees (10% duty)
    print("Moving servo to 90 degrees...")
    uio.pin(2).set_pwm(frequency, 10.0, 5.0)

    time.sleep(2)
    print("Done!")
```

---

### Task 3: Simulate 4-20mA Sensor

**Scenario**: Simulate an industrial pressure sensor.

```python
from sdrig import SDRIG
import time

IFACE = "enp0s31f6"
UIO_MAC = "82:7B:C4:B1:92:F2"

def pressure_to_current(pressure_bar):
    """Convert pressure (0-100 bar) to 4-20mA"""
    if not 0 <= pressure_bar <= 100:
        raise ValueError("Pressure must be 0-100 bar")
    return 4.0 + (pressure_bar / 100.0) * 16.0

with SDRIG(iface=IFACE, stream_id=1) as sdk:
    uio = sdk.connect_uio(UIO_MAC, auto_start=True)
    time.sleep(2)

    # Simulate pressure ramp: 0 → 50 → 100 bar
    for pressure in [0, 25, 50, 75, 100]:
        current = pressure_to_current(pressure)
        print(f"Pressure: {pressure} bar → {current:.2f}mA")
        uio.pin(0).set_tx_current(current)
        time.sleep(1)
```

---

### Task 4: Test Electronic Load

**Scenario**: Sink current to test a power supply.

```python
from sdrig import SDRIG
import time

IFACE = "enp0s31f6"
ELOAD_MAC = "76:4D:28:9A:3E:C1"

with SDRIG(iface=IFACE, stream_id=1) as sdk:
    eload = sdk.connect_eload(ELOAD_MAC, auto_start=True)
    time.sleep(2)

    print("Testing power supply with 2.5A load...")

    # Sink 2.5A on channel 0
    eload.channel(0).set_tx_current(2.5)
    time.sleep(2)

    # Measure voltage and power
    voltage = eload.channel(0).get_voltage()
    power = eload.channel(0).get_power()

    print(f"Voltage: {voltage:.2f}V")
    print(f"Power: {power:.2f}W")

    # Check if voltage is within acceptable range
    if 11.5 <= voltage <= 12.5:
        print("✓ Power supply OK")
    else:
        print("✗ Power supply voltage out of range!")
```

---

### Task 5: Send CAN Message

**Scenario**: Send engine RPM message on CAN bus.

```python
from sdrig import SDRIG
from sdrig.types.enums import CANSpeed
import time

IFACE = "enp0s31f6"
IFMUX_MAC = "66:6A:DB:B3:06:27"

with SDRIG(iface=IFACE, stream_id=1) as sdk:
    ifmux = sdk.connect_ifmux(IFMUX_MAC, auto_start=True)
    time.sleep(2)

    # Configure CAN channel 0 to 500 kbps
    print("Configuring CAN channel to 500 kbps...")
    ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)
    time.sleep(0.5)

    # Send engine RPM message (2500 RPM)
    rpm = 2500
    rpm_raw = int(rpm / 0.125)  # 0.125 rpm/bit scaling

    data = bytes([
        rpm_raw & 0xFF,
        (rpm_raw >> 8) & 0xFF,
        0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF
    ])

    print(f"Sending engine RPM: {rpm} RPM")
    ifmux.send_raw_can(
        channel_id=0,
        can_id=0x0CF00400,  # J1939 Engine Speed PGN
        data=data
    )
    print("Message sent!")
```

---

### Task 6: Use LIN Interface

**Scenario**: Send LIN diagnostic message.

```python
from sdrig import SDRIG
import time

IFACE = "enp0s31f6"
IFMUX_MAC = "66:6A:DB:B3:06:27"

with SDRIG(iface=IFACE, stream_id=1, debug=True) as sdk:
    # IMPORTANT: Enable LIN support
    ifmux = sdk.connect_ifmux(IFMUX_MAC, auto_start=True, lin_enabled=True)
    time.sleep(2)

    # Configure LIN diagnostic frame
    frame_id = 0x3C  # Standard diagnostic request
    print(f"Configuring LIN frame ID {frame_id}...")
    ifmux.configure_lin_frame(frame_id, data_length=8)
    time.sleep(0.5)

    # Send diagnostic request
    data = bytes([0x3C, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07])
    print("Sending LIN frame...")
    ifmux.send_lin_frame(frame_id, data)

    print("LIN message sent! (Check debug output for response)")
    time.sleep(2)
```

---

## 🎓 Understanding the Code

### SDK Context Manager

```python
with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    # Your code here
    pass
# Automatic cleanup when exiting
```

**Why use `with`?**
- Automatic resource cleanup
- Proper shutdown of connections
- Exception handling

---

### Device Connection

```python
uio = sdk.connect_uio(
    "82:7B:C4:B1:92:F2",  # MAC address from discovery
    auto_start=True        # Start heartbeat automatically
)
time.sleep(2)  # IMPORTANT: Wait for initialization
```

**Key points:**
- Use MAC address from device discovery
- `auto_start=True` starts heartbeat (recommended)
- Always wait 2 seconds after connection

---

### Pin Access

```python
uio.pin(0)  # Access pin by index (0-7)
uio.pin(0).set_voltage(12.0)  # Set voltage on pin 0
voltage = uio.pin(1).get_voltage()  # Read voltage from pin 1
```

**Pin numbering:** 0-7 (total 8 pins)

---

## ⚠️ Common Mistakes

### 1. Forgetting to Wait After Connection

```python
# ✗ Wrong: No delay
uio = sdk.connect_uio("MAC", auto_start=True)
uio.pin(0).set_voltage(12.0)  # May fail!

# ✓ Correct: Add delay
uio = sdk.connect_uio("MAC", auto_start=True)
time.sleep(2)  # Wait for initialization
uio.pin(0).set_voltage(12.0)  # OK
```

---

### 2. Using Wrong Interface Name

```python
# ✗ Wrong: Hardcoded interface may not exist
IFACE = "eth0"  # May not exist on your system

# ✓ Correct: Check available interfaces first
# Run: ip link show
# Then use the actual interface name
IFACE = "enp0s31f6"  # Your actual interface
```

---

### 3. Not Enabling LIN

```python
# ✗ Wrong: LIN not enabled
ifmux = sdk.connect_ifmux("MAC", auto_start=True)
ifmux.configure_lin_frame(0x3C, 8)  # Will fail!

# ✓ Correct: Enable LIN
ifmux = sdk.connect_ifmux("MAC", auto_start=True, lin_enabled=True)
time.sleep(2)
ifmux.configure_lin_frame(0x3C, 8)  # OK
```

---

### 4. Invalid Parameter Values

```python
# ✗ Wrong: Values out of range
uio.pin(0).set_voltage(30.0)  # Max is 24V
uio.pin(0).set_tx_current(25.0)  # Max is 20mA

# ✓ Correct: Stay within limits
uio.pin(0).set_voltage(24.0)  # OK: 0-24V
uio.pin(0).set_tx_current(20.0)  # OK: 0-20mA
```

**Valid Ranges:**
- Voltage: 0-24V
- Current: 0-20mA
- PWM frequency: 20-5000Hz
- PWM duty cycle: 0-100%

---

## 🐛 Troubleshooting

### "No devices found"

**Cause:** Devices not visible on network

**Solutions:**
```bash
# 1. Check network interface
ip link show

# 2. Check if interface is up
sudo ip link set enp0s31f6 up

# 3. Verify device power

# 4. Try discovery example
python examples/01_device_discovery.py
```

---

### "Permission denied" on network interface

**Cause:** Insufficient permissions for raw sockets

**Solutions:**
```bash
# Option 1: Run with sudo
sudo python your_script.py

# Option 2: Add user to dialout group
sudo usermod -aG dialout $USER
# Then logout and login again

# Option 3: Set capabilities (persistent)
sudo setcap cap_net_raw+ep $(which python3)
```

---

### "Device not responding"

**Cause:** Device not initialized or wrong MAC address

**Solutions:**
```python
# 1. Verify MAC address
with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    devices = sdk.discover_devices()
    for dev in devices:
        print(f"{dev.type.name}: {dev.mac}")

# 2. Increase wait time
uio = sdk.connect_uio("MAC", auto_start=True)
time.sleep(5)  # Longer wait

# 3. Check device status
if uio.is_alive():
    print("Device OK")
else:
    print("Device not responding")
```

---

### Import errors

**Cause:** SDK not properly installed

**Solutions:**
```bash
# Reinstall SDK
pip uninstall sdrig -y
pip install -e .

# Verify installation
python -c "import sdrig; print(sdrig.__version__)"
```

---

## 📚 Next Steps

### Learn More

**Device-Specific Guides:**
- [UIO Device Guide](guides/uio-device.md) - Complete UIO reference
- [ELoad Device Guide](guides/eload-device.md) - Electronic load guide
- [IfMux Device Guide](guides/ifmux-device.md) - CAN/LIN interface
- [LIN Interface Guide](guides/lin-interface.md) - LIN protocol

**API Documentation:**
- [CAN Protocol Reference](api/can-protocol.md) - All CAN messages
- [Main Documentation](README.md) - Complete SDK reference

**Testing:**
- [Testing Guide](../tests/README.md) - How to run tests

---

### Try Examples

Explore the `examples/` directory:

```bash
# Device discovery
python examples/01_device_discovery.py

# UIO voltage control
python examples/02_uio_voltage_control.py

# UIO PWM generation
python examples/03_uio_pwm_control.py

# Electronic load testing
python examples/04_eload_control.py

# CAN communication
python examples/05_can_communication.py

# LIN communication
python examples/06_lin_communication.py
```

---

### Build Your First Project

**Project Ideas for Beginners:**

1. **Temperature Monitor**
   - Read voltage from temperature sensor
   - Convert to temperature
   - Log values to file

2. **LED Controller**
   - Generate PWM signals
   - Control LED brightness
   - Create patterns

3. **Power Supply Tester**
   - Use ELoad to sink current
   - Measure voltage stability
   - Calculate efficiency

4. **CAN Logger**
   - Monitor CAN bus
   - Log messages to CSV
   - Filter specific message IDs

---

## 🎯 Quick Reference

### Essential Imports

```python
from sdrig import SDRIG
from sdrig.types.enums import (
    CANSpeed,      # CAN bus speeds
    Feature,       # UIO features
    FeatureState,  # Feature states
    RelayState     # Relay states
)
import time
```

---

### Basic Template

```python
from sdrig import SDRIG
import time

# Configuration
IFACE = "enp0s31f6"
STREAM_ID = 1
DEVICE_MAC = "XX:XX:XX:XX:XX:XX"

with SDRIG(iface=IFACE, stream_id=STREAM_ID) as sdk:
    # Connect to device
    device = sdk.connect_uio(DEVICE_MAC, auto_start=True)
    # or: sdk.connect_eload(...)
    # or: sdk.connect_ifmux(...)

    time.sleep(2)  # Wait for initialization

    # Your code here

    print("Done!")
```

---

### Parameter Ranges

| Parameter | Minimum | Maximum | Unit |
|-----------|---------|---------|------|
| Voltage | 0 | 24 | V |
| Current | 0 | 20 | mA |
| PWM Frequency | 20 | 5000 | Hz |
| PWM Duty Cycle | 0 | 100 | % |
| Pin Number | 0 | 7 | - |
| Channel Number | 0 | 7 | - |

---

## 💡 Tips for Success

1. **Always discover devices first** - Use `examples/01_device_discovery.py`
2. **Wait after connections** - 2 seconds minimum
3. **Enable debug mode during development** - `debug=True`
4. **Check parameter ranges** - Validate before sending
5. **Use context manager** - `with SDRIG(...) as sdk:`
6. **Read examples** - Learn from working code
7. **Check documentation** - Device guides have detailed info

---

## 📞 Getting Help

**Documentation:**
- Main: [`docs/README.md`](README.md)
- Troubleshooting: Each device guide has troubleshooting section

**Support:**
- GitHub Issues: https://github.com/soda-auto/soda-validate-sdrig-sdk-py/issues
- Email: chubuchnyi@soda.auto

**Before Asking:**
1. Try device discovery
2. Check parameter ranges
3. Review troubleshooting sections
4. Run with `debug=True`

---

## 🎉 You're Ready!

You now have everything you need to start working with SDRIG hardware.

**Happy testing!** 🚀

---

© 2026 SODA Validate. All rights reserved.
