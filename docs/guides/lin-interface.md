# LIN Interface Guide

Complete guide for LIN (Local Interconnect Network) communication with SDRIG SDK.

**Quick Navigation:**
- [Quick Start](#-quick-start-3-steps) - Get started in 3 steps
- [Overview](#-overview) - LIN protocol basics
- [API Reference](#-api-reference) - Complete API documentation
- [Examples](#-practical-examples) - Real-world usage examples
- [Troubleshooting](#-troubleshooting) - Common issues and solutions

---

## 🚀 Quick Start (3 Steps)

### 1. Connect with LIN Enabled

```python
from sdrig import SDRIG

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    # IMPORTANT: set lin_enabled=True
    ifmux = sdk.connect_ifmux(
        "66:6A:DB:B3:06:27",  # IfMux MAC address
        auto_start=True,
        lin_enabled=True      # Enable LIN support
    )
```

### 2. Configure Frame

```python
ifmux.configure_lin_frame(
    frame_id=0x3C,          # Frame ID (0-63)
    data_length=8,          # Data length (1-8 bytes)
    checksum_type=1         # Enhanced checksum (recommended)
)
```

### 3. Send Frame

```python
data = bytes([0x3C, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07])
ifmux.send_lin_frame(0x3C, data)
```

### Complete Minimal Example

```python
from sdrig import SDRIG
import time

with SDRIG(iface="enp0s31f6", stream_id=1, debug=True) as sdk:
    # Connect with LIN enabled
    ifmux = sdk.connect_ifmux("66:6A:DB:B3:06:27", auto_start=True, lin_enabled=True)
    time.sleep(2)

    # Configure frame
    ifmux.configure_lin_frame(frame_id=0x3C, data_length=8)
    time.sleep(0.5)

    # Send data
    data = bytes([0x3C, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77])
    ifmux.send_lin_frame(0x3C, data)

    # Wait for response
    time.sleep(2)
```

---

## 📖 Overview

LIN (Local Interconnect Network) is a single-wire serial communication protocol used in the automotive industry for low-cost communication between sensors and actuators.

SDRIG SDK supports LIN through the **IfMux** (Interface Multiplexer) module.

### LIN Key Features

- **Speed**: Up to 20 kbit/s
- **Topology**: Master-Slave (one Master, up to 15 Slaves)
- **Frame ID**: 0-63 (6 bits)
- **Data Length**: 1-8 bytes
- **Checksum**: Classic or Enhanced
- **Standard**: LIN 2.0 (ISO 17987)

### When to Use LIN

**Use LIN for:**
- Low-speed sensor networks (temperature, pressure)
- Simple actuator control (motors, valves)
- Cost-sensitive applications
- Automotive body electronics

**Use CAN for:**
- High-speed communication (>20 kbit/s)
- Safety-critical systems
- Complex data exchange

---

## 🔧 API Reference

### 1. Configure LIN Frame

Before sending any frame, it must be configured with its parameters.

```python
ifmux.configure_lin_frame(
    frame_id=0x3C,          # Frame ID (0-63)
    data_length=8,          # Data length (1-8 bytes)
    checksum_type=1         # 0=classic, 1=enhanced
)
```

**Parameters:**

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `frame_id` | int | 0-63 | Frame identifier (6-bit) |
| `data_length` | int | 1-8 | Number of data bytes |
| `checksum_type` | int | 0-1 | Checksum algorithm |

**Checksum Types:**
- `0` - **Classic**: Checksums data only (LIN 1.x compatibility)
- `1` - **Enhanced**: Checksums PID + data (LIN 2.x standard, **recommended**)

**Example:**
```python
# Configure diagnostic frame
ifmux.configure_lin_frame(
    frame_id=0x3C,      # Standard diagnostic request
    data_length=8,      # Full 8 bytes
    checksum_type=1     # Enhanced checksum
)
time.sleep(0.1)  # Allow time to process
```

---

### 2. Send LIN Frame

Send data on a previously configured frame.

```python
ifmux.send_lin_frame(frame_id=0x3C, data=data)
```

**Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `frame_id` | int | Frame ID (0-63), must be configured |
| `data` | bytes | Data payload (1-8 bytes) |

**Important:**
- Frame must be configured before sending
- Data length must match configured length
- Data is a `bytes` object

**Example:**
```python
# Send sensor request
frame_id = 0x27
data = bytes([0x27, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
ifmux.send_lin_frame(frame_id, data)
```

---

### 3. Receive LIN Frames

Frames are received automatically and processed by the SDK.

#### Enable Debug Mode

```python
# See all received frames in console
with SDRIG(iface="enp0s31f6", stream_id=1, debug=True) as sdk:
    ifmux = sdk.connect_ifmux("MAC", auto_start=True, lin_enabled=True)
    # Received frames will be logged
```

#### Register Custom Callback

```python
from sdrig.types.enums import PGN

def on_lin_frame_received(pgn, data, src_mac):
    """Callback for processing received LIN frames"""
    decoded = ifmux.can_db.decode_message(pgn, data)
    frame_id = decoded.get('frame_id', 0)
    frame_data = decoded.get('data', b'')

    print(f"Received LIN Frame ID: 0x{frame_id:02X}")
    print(f"Data: {frame_data.hex()}")

# Register callback for LIN_FRAME_RCVD_ANS messages
ifmux.register_message_callback(
    PGN.LIN_FRAME_RCVD_ANS.value,
    on_lin_frame_received
)
```

---

## 🎯 Practical Examples

### Example 1: Basic Send and Receive

```python
from sdrig import SDRIG
import time

with SDRIG(iface="enp0s31f6", stream_id=1, debug=True) as sdk:
    ifmux = sdk.connect_ifmux("66:6A:DB:B3:06:27", auto_start=True, lin_enabled=True)
    time.sleep(2)

    # Configure frame
    ifmux.configure_lin_frame(frame_id=0x3C, data_length=8)
    time.sleep(0.5)

    # Send data
    data = bytes([0x3C, 0x11, 0x22, 0x33, 0x44, 0x55, 0x66, 0x77])
    ifmux.send_lin_frame(0x3C, data)

    # Wait for response
    time.sleep(2)
```

---

### Example 2: Reading Temperature Sensor

```python
from sdrig import SDRIG
import time

def read_temperature_sensor(ifmux, sensor_frame_id=0x27):
    """Read temperature sensor via LIN"""

    # Configure sensor frame (2 bytes: temperature)
    ifmux.configure_lin_frame(
        frame_id=sensor_frame_id,
        data_length=2,
        checksum_type=1
    )
    time.sleep(0.2)

    # Request data (Master sends header)
    request = bytes([sensor_frame_id, 0x00])
    ifmux.send_lin_frame(sensor_frame_id, request)

    # Slave will respond automatically (data in logs or callback)
    time.sleep(0.5)

with SDRIG(iface="enp0s31f6", stream_id=1, debug=True) as sdk:
    ifmux = sdk.connect_ifmux("MAC", auto_start=True, lin_enabled=True)
    time.sleep(2)

    # Periodic sensor reading
    for i in range(10):
        print(f"Reading {i+1}/10")
        read_temperature_sensor(ifmux)
        time.sleep(1)
```

---

### Example 3: Controlling Mirror Motor

```python
from sdrig import SDRIG
import time

class MirrorController:
    """Rear-view mirror controller via LIN"""

    FRAME_ID = 0x30

    CMD_STOP = 0x00
    CMD_LEFT = 0x01
    CMD_RIGHT = 0x02
    CMD_UP = 0x03
    CMD_DOWN = 0x04

    def __init__(self, ifmux):
        self.ifmux = ifmux

        # Configure mirror control frame
        self.ifmux.configure_lin_frame(
            frame_id=self.FRAME_ID,
            data_length=3,  # Command + speed + reserve
            checksum_type=1
        )
        time.sleep(0.2)

    def move(self, command, speed=100):
        """Move mirror in specified direction"""
        data = bytes([self.FRAME_ID, command, speed])
        self.ifmux.send_lin_frame(self.FRAME_ID, data)

    def stop(self):
        """Stop mirror movement"""
        self.move(self.CMD_STOP, 0)

# Usage
with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    ifmux = sdk.connect_ifmux("MAC", auto_start=True, lin_enabled=True)
    time.sleep(2)

    mirror = MirrorController(ifmux)

    # Move left
    print("Moving left...")
    mirror.move(MirrorController.CMD_LEFT, speed=80)
    time.sleep(2)

    # Stop
    print("Stopping...")
    mirror.stop()
```

---

### Example 4: LIN Diagnostics

```python
from sdrig import SDRIG
import time

def lin_diagnostic_session(ifmux):
    """Perform LIN diagnostic session"""

    # Diagnostic frames (LIN standard)
    DIAG_REQUEST_ID = 0x3C   # Master request
    DIAG_RESPONSE_ID = 0x3D  # Slave response

    # Configure both frames
    ifmux.configure_lin_frame(DIAG_REQUEST_ID, data_length=8)
    ifmux.configure_lin_frame(DIAG_RESPONSE_ID, data_length=8)
    time.sleep(0.5)

    # Read by Identifier request
    nad = 0x01              # Node Address
    pci = 0x06              # Protocol Control Information (length)
    sid = 0xB0              # Service ID: Read by Identifier
    supplier_id = 0x0001    # Supplier ID
    function_id = 0x0002    # Function ID

    request = bytes([
        nad,
        pci,
        sid,
        (supplier_id >> 8) & 0xFF,  # Supplier ID high
        supplier_id & 0xFF,          # Supplier ID low
        (function_id >> 8) & 0xFF,  # Function ID high
        function_id & 0xFF,          # Function ID low
        0xFF                         # Fill byte
    ])

    print(f"Sending diagnostic request: {request.hex()}")
    ifmux.send_lin_frame(DIAG_REQUEST_ID, request)

    # Wait for response on DIAG_RESPONSE_ID
    time.sleep(1)
    print("Check logs for diagnostic response on frame 0x3D")

with SDRIG(iface="enp0s31f6", stream_id=1, debug=True) as sdk:
    ifmux = sdk.connect_ifmux("MAC", auto_start=True, lin_enabled=True)
    time.sleep(2)

    lin_diagnostic_session(ifmux)
```

---

### Example 5: Periodic Polling

```python
from sdrig import SDRIG
import time

def periodic_sensor_poll(ifmux, frame_ids, interval=1.0):
    """Poll multiple sensors periodically"""

    # Configure all sensors
    for fid in frame_ids:
        ifmux.configure_lin_frame(frame_id=fid, data_length=2)
        time.sleep(0.1)

    print("Starting periodic polling...")
    try:
        while True:
            for fid in frame_ids:
                # Send request
                request = bytes([fid, 0x00])
                ifmux.send_lin_frame(fid, request)
                time.sleep(0.1)

            time.sleep(interval)

    except KeyboardInterrupt:
        print("\nPolling stopped")

# Usage
with SDRIG(iface="enp0s31f6", stream_id=1, debug=True) as sdk:
    ifmux = sdk.connect_ifmux("MAC", auto_start=True, lin_enabled=True)
    time.sleep(2)

    # Poll temperature (0x27) and pressure (0x28) sensors
    periodic_sensor_poll(ifmux, frame_ids=[0x27, 0x28], interval=2.0)
```

---

## 📋 LIN Frame ID Reference

### Standard Frame IDs

| Range | Usage | Description |
|-------|-------|-------------|
| `0x00-0x3B` | Normal frames | Sensors, actuators, switches |
| `0x3C` | Diagnostic request | Master → Slave diagnostic commands |
| `0x3D` | Diagnostic response | Slave → Master diagnostic data |
| `0x3E` | Reserved | User-defined |
| `0x3F` | Reserved | User-defined |

### Typical Device Assignments

| Frame IDs | Device Type | Examples |
|-----------|-------------|----------|
| `0x20-0x25` | Sensors | Temperature, pressure, level |
| `0x26-0x2F` | Actuators | Motors, valves, heaters |
| `0x30-0x35` | Switches | Buttons, position sensors |
| `0x36-0x3B` | Indicators | LEDs, displays |

---

## ⚙️ Checksum Types

### Classic Checksum (0)

- **Usage**: LIN 1.x compatibility
- **Algorithm**: Checksums data bytes only
- **Formula**: `~(sum(data_bytes)) & 0xFF`

**When to use:**
- Communicating with old LIN 1.x devices
- Explicitly required by device specification

### Enhanced Checksum (1) - Recommended

- **Usage**: LIN 2.x standard
- **Algorithm**: Checksums Protected ID + data bytes
- **Formula**: `~(PID + sum(data_bytes)) & 0xFF`

**When to use:**
- All new projects (default and recommended)
- LIN 2.0+ compliant devices
- Better error detection

**Best Practice:** Always use Enhanced checksum (1) unless device specifically requires Classic.

---

## 🎓 Best Practices

### 1. Always Add Delays

LIN communication requires time for hardware processing.

```python
# Configure frame
ifmux.configure_lin_frame(frame_id=0x3C, data_length=8)
time.sleep(0.1)  # Minimum 100ms after configuration

# Send frame
ifmux.send_lin_frame(0x3C, data)
time.sleep(0.5)  # Allow time for slave response
```

**Recommended delays:**
- After configuration: **100ms minimum**
- Between frames: **50ms minimum**
- Waiting for response: **500ms-1s**

---

### 2. Use Enhanced Checksum

```python
# Always use Enhanced checksum for new projects
ifmux.configure_lin_frame(
    frame_id=0x3C,
    data_length=8,
    checksum_type=1  # Enhanced (recommended)
)
```

---

### 3. Enable Debug During Development

```python
# See all LIN traffic in console
with SDRIG(iface="enp0s31f6", stream_id=1, debug=True) as sdk:
    ifmux = sdk.connect_ifmux("MAC", auto_start=True, lin_enabled=True)
    # All LIN frames logged
```

---

### 4. Handle Exceptions

```python
try:
    ifmux.configure_lin_frame(frame_id=0x3C, data_length=8)
    ifmux.send_lin_frame(0x3C, data)
except RuntimeError as e:
    print(f"LIN Error: {e}")  # e.g., "LIN not enabled"
except ValueError as e:
    print(f"Invalid parameter: {e}")  # e.g., "Frame ID out of range"
```

---

### 5. Validate Parameters

```python
def send_lin_safely(ifmux, frame_id, data):
    """Send LIN frame with validation"""

    # Validate Frame ID
    if not 0 <= frame_id <= 63:
        raise ValueError(f"LIN frame ID must be 0-63, got {frame_id}")

    # Validate data length
    if not 1 <= len(data) <= 8:
        raise ValueError(f"LIN data must be 1-8 bytes, got {len(data)}")

    # Send
    try:
        ifmux.send_lin_frame(frame_id, data)
    except RuntimeError:
        print("LIN not enabled. Use lin_enabled=True")
        raise
```

---

### 6. Configure Once, Send Multiple

```python
# Efficient: configure once
ifmux.configure_lin_frame(frame_id=0x27, data_length=2)
time.sleep(0.2)

# Send multiple times
for i in range(100):
    ifmux.send_lin_frame(0x27, bytes([0x27, 0x00]))
    time.sleep(0.1)
```

---

## 🐛 Debugging and Diagnostics

### Enable Debug Logging

```python
from sdrig import SDRIGLogger

# Global debug mode
SDRIGLogger.enable_debug_mode()

# Or when creating SDK
with SDRIG(iface="enp0s31f6", stream_id=1, debug=True) as sdk:
    # All LIN frames logged to console
    pass
```

---

### Check LIN Status

```python
# Verify LIN is enabled
if ifmux.lin_enabled:
    print("✓ LIN support is active")
else:
    print("✗ LIN support is disabled")
    print("  Use lin_enabled=True when connecting")
```

---

### Monitor Frame Traffic

```python
from sdrig.types.enums import PGN

frame_count = 0

def count_frames(pgn, data, src_mac):
    global frame_count
    frame_count += 1
    print(f"Frame {frame_count}: PGN=0x{pgn:05X}, Data={data.hex()}")

# Register callback
ifmux.register_message_callback(
    PGN.LIN_FRAME_RCVD_ANS.value,
    count_frames
)
```

---

## ⚠️ Troubleshooting

### Issue: RuntimeError "LIN not enabled for this device"

**Cause:** LIN support not enabled when connecting to IfMux.

**Solution:**
```python
# ✗ Wrong
ifmux = sdk.connect_ifmux("MAC", auto_start=True)

# ✓ Correct
ifmux = sdk.connect_ifmux("MAC", auto_start=True, lin_enabled=True)
```

---

### Issue: No Response from Slave Devices

**Possible causes and solutions:**

1. **Physical connection issue**
   - Check LIN bus wiring
   - Verify termination resistor (1kΩ)
   - Check ground connection

2. **Wrong Frame ID**
   - Verify Frame ID matches slave device
   - Check device documentation

3. **Not in Master mode**
   - SDK operates as Master only
   - Ensure device is configured as Slave

4. **Timing issue**
   - Increase delays between operations
   - Some slaves need more time to respond

---

### Issue: ValueError when Sending Frame

**Cause:** Invalid parameters.

**Common errors:**

```python
# Frame ID out of range
ifmux.send_lin_frame(64, data)  # ✗ Max is 63

# Data too long
ifmux.send_lin_frame(0x3C, bytes([0]*9))  # ✗ Max 8 bytes

# Frame not configured
ifmux.send_lin_frame(0x3C, data)  # ✗ Must configure first
```

**Solution:**
```python
# Validate before sending
if 0 <= frame_id <= 63 and 1 <= len(data) <= 8:
    ifmux.configure_lin_frame(frame_id, len(data))
    time.sleep(0.1)
    ifmux.send_lin_frame(frame_id, data)
```

---

### Issue: Received Frames Not Visible

**Solution:**

1. **Enable debug mode**
   ```python
   with SDRIG(iface="...", stream_id=1, debug=True) as sdk:
       # Frames now visible in console
   ```

2. **Register callback**
   ```python
   ifmux.register_message_callback(
       PGN.LIN_FRAME_RCVD_ANS.value,
       my_callback
   )
   ```

3. **Check application logs**
   ```python
   from sdrig import SDRIGLogger
   logger = SDRIGLogger.get_logger("my_app")
   logger.info("Checking for LIN frames...")
   ```

---

### Issue: Checksum Errors

**Cause:** Mismatch between configured and actual checksum type.

**Solution:**
- Most devices use Enhanced (1)
- Check device specification
- Try both checksum types if unsure:

```python
# Try Enhanced first
ifmux.configure_lin_frame(frame_id=0x3C, data_length=8, checksum_type=1)
time.sleep(0.2)
ifmux.send_lin_frame(0x3C, data)
time.sleep(1)

# If no response, try Classic
ifmux.configure_lin_frame(frame_id=0x3C, data_length=8, checksum_type=0)
time.sleep(0.2)
ifmux.send_lin_frame(0x3C, data)
```

---

## 🔗 Additional Resources

### Documentation
- **LIN Specification**: ISO 17987
- **Example Script**: [`examples/06_lin_communication.py`](../../examples/06_lin_communication.py)
- **API Reference**: `sdrig.devices.device_ifmux.DeviceIfMux`
- **Main Documentation**: [`docs/README.md`](../README.md)

### Related Guides
- **IfMux Device Guide**: Complete IfMux documentation (CAN + LIN)
- **CAN Protocol Reference**: [`docs/api/can-protocol.md`](../api/can-protocol.md)
- **Testing Guide**: [`tests/README_TESTS.md`](../../tests/README_TESTS.md)

### Standards
- **ISO 17987**: LIN specification
- **IEEE 1722**: AVTP protocol (transport layer)

---

## 📊 Quick Reference

### Parameters Summary

| Parameter | Range | Default | Description |
|-----------|-------|---------|-------------|
| `frame_id` | 0-63 | - | Frame identifier |
| `data_length` | 1-8 | - | Payload size |
| `checksum_type` | 0-1 | 1 | Checksum algorithm |
| `lin_enabled` | bool | False | Enable LIN support |

### Error Codes

| Error | Cause | Solution |
|-------|-------|----------|
| `RuntimeError` | LIN not enabled | Use `lin_enabled=True` |
| `ValueError` | Invalid parameters | Check ranges |
| `TimeoutError` | No response | Check physical connection |

### Timing Guidelines

| Operation | Minimum Delay |
|-----------|--------------|
| After configure | 100ms |
| Between frames | 50ms |
| Wait for response | 500ms |
| After connection | 2s |

---

© 2026 SODA Validate. All rights reserved.
