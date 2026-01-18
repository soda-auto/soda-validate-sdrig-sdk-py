# IfMux Device Guide

Complete guide for Interface Multiplexer (IfMux) module in SDRIG SDK.

**Quick Navigation:**
- [Quick Start](#-quick-start) - Get started in 3 steps
- [Overview](#-overview) - IfMux device capabilities
- [CAN Channels](#-can-channels) - CAN FD configuration and control
- [LIN Interface](#-lin-interface) - LIN communication
- [Relay Control](#-relay-control) - Internal and external relays
- [Examples](#-practical-examples) - Real-world usage examples
- [Troubleshooting](#-troubleshooting) - Common issues

---

## 🚀 Quick Start

### 1. Connect to IfMux Device

```python
from sdrig import SDRIG

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    # Connect to IfMux device
    ifmux = sdk.connect_ifmux(
        "66:6A:DB:B3:06:27",  # IfMux MAC address
        auto_start=True,       # Start heartbeat automatically
        lin_enabled=True       # Enable LIN support (optional)
    )
```

### 2. Configure CAN Channel

```python
from sdrig.types.enums import CANSpeed

# Set CAN channel speed
ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)  # 500 kbps
```

### 3. Send CAN Message

```python
# Send raw CAN message
ifmux.send_raw_can(
    channel_id=0,
    can_id=0x123,
    data=b'\x01\x02\x03\x04\x05\x06\x07\x08'
)
```

### Complete Minimal Example

```python
from sdrig import SDRIG
from sdrig.types.enums import CANSpeed
import time

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    # Connect to IfMux
    ifmux = sdk.connect_ifmux("66:6A:DB:B3:06:27", auto_start=True)
    time.sleep(2)  # Wait for device initialization

    # Configure CAN channel 0
    ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)
    print("CAN channel 0 configured to 500 kbps")

    # Send CAN message
    ifmux.send_raw_can(
        channel_id=0,
        can_id=0x123,
        data=b'\x01\x02\x03\x04'
    )
    print("CAN message sent")
```

---

## 📖 Overview

### What is IfMux?

IfMux (Interface Multiplexer) is a powerful module providing **8 CAN FD channels** and optional **LIN interface** for comprehensive vehicle network simulation and testing.

### Key Features

| Feature | Specification |
|---------|--------------|
| **CAN Channels** | 8 independent channels (0-7) |
| **CAN FD** | Up to 5 Mbps (8 Mbps capable) |
| **CAN Classic** | 125 kbps, 250 kbps, 500 kbps, 1 Mbps |
| **LIN** | LIN 2.0 support (optional) |
| **Internal Relays** | 8 relays (one per channel) |
| **External Relays** | 8×8 matrix (64 connections) |
| **Backplane** | 16 additional CAN channels via backplane |
| **State Monitoring** | TX/RX counters, error tracking |

### When to Use IfMux

**Use IfMux for:**
- Multi-ECU CAN network simulation
- CAN bus testing and validation
- Network topology testing
- Gateway and router testing
- LIN bus communication
- Relay matrix routing

**Examples:**
- Simulating complete vehicle CAN network
- Testing CAN gateway with multiple buses
- Body electronics testing (CAN + LIN)
- Network load testing
- ECU-to-ECU communication testing

---

## 🔧 API Reference

### Connecting to IfMux

```python
ifmux = sdk.connect_ifmux(
    mac="66:6A:DB:B3:06:27",  # IfMux MAC address
    auto_start=True,           # Start heartbeat automatically
    lin_enabled=False          # Enable LIN support
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `mac` | str | - | Device MAC address |
| `auto_start` | bool | False | Auto-start heartbeat |
| `lin_enabled` | bool | False | Enable LIN interface |

**Returns:** `DeviceIfMux` object

---

### Accessing CAN Channels

```python
channel = ifmux.channel(channel_id)  # channel_id: 0-7
```

Each channel object provides full CAN control.

---

## 📡 CAN Channels

### 1. Configure CAN Speed

```python
from sdrig.types.enums import CANSpeed

ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)
```

**Available Speeds:**

| Speed | Value | Type | Common Use |
|-------|-------|------|------------|
| `SPEED_125K` | 125000 | Classic | Low-speed networks |
| `SPEED_250K` | 250000 | Classic | Body electronics |
| `SPEED_500K` | 500000 | Classic | Powertrain (most common) |
| `SPEED_1M` | 1000000 | Classic/FD | High-speed networks |
| `SPEED_2M` | 2000000 | FD | CAN FD data phase |
| `SPEED_5M` | 5000000 | FD | High-performance CAN FD |
| `SPEED_8M` | 8000000 | FD | Maximum CAN FD speed |

**Example - Multiple Channels:**
```python
# Configure multiple CAN networks
ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)  # Powertrain CAN
ifmux.channel(1).set_speed(CANSpeed.SPEED_250K)  # Body CAN
ifmux.channel(2).set_speed(CANSpeed.SPEED_1M)    # Diagnostic CAN
```

---

### 2. Send Raw CAN Message

```python
ifmux.send_raw_can(
    channel_id=0,
    can_id=0x123,
    data=b'\x01\x02\x03\x04\x05\x06\x07\x08',
    extended=True,  # Use 29-bit extended ID
    fd=True         # Use CAN-FD
)
```

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `channel_id` | int | - | CAN channel (0-7) |
| `can_id` | int | - | CAN message ID |
| `data` | bytes | - | Message payload (up to 64 bytes for FD) |
| `extended` | bool | True | Use 29-bit ID (vs 11-bit) |
| `fd` | bool | True | Use CAN-FD |

**CAN Message ID Formats:**
- **Standard (11-bit)**: 0x000 - 0x7FF (2048 IDs)
- **Extended (29-bit)**: 0x00000000 - 0x1FFFFFFF (~536M IDs)

**CAN Data Length:**
- **Classic CAN**: Up to 8 bytes
- **CAN FD**: Up to 64 bytes

**Example - Engine RPM Message:**
```python
# Send engine RPM (J1939 format)
# PGN: 0x0F004 (Engine Speed)
can_id = 0x0CF00400  # J1939 ID with priority 3
rpm = 2500

# Encode RPM (0.125 rpm/bit)
rpm_raw = int(rpm / 0.125)
data = bytes([
    rpm_raw & 0xFF,
    (rpm_raw >> 8) & 0xFF,
    0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF
])

ifmux.send_raw_can(channel_id=0, can_id=can_id, data=data)
```

---

### 3. Register CAN Receive Callback

```python
def on_can_received(channel_id, can_id, data):
    """Callback for received CAN messages"""
    print(f"Channel {channel_id}: ID=0x{can_id:03X}, Data={data.hex()}")

# Register callback
ifmux.register_raw_can_callback(on_can_received)
```

**Callback Parameters:**
- `channel_id` (int): CAN channel that received the message
- `can_id` (int): CAN message ID
- `data` (bytes): Message payload

**Example - Monitor Specific Message:**
```python
def monitor_speed_sensor(channel_id, can_id, data):
    """Monitor wheel speed sensor messages"""
    if can_id == 0x1A0:  # Wheel speed CAN ID
        # Parse wheel speeds (example format)
        fl_speed = int.from_bytes(data[0:2], 'little')
        fr_speed = int.from_bytes(data[2:4], 'little')
        print(f"Wheel speeds: FL={fl_speed}, FR={fr_speed} km/h")

ifmux.register_raw_can_callback(monitor_speed_sensor)
```

---

### 4. Get Channel State

```python
from sdrig.types.enums import CANState

# Get CAN controller state
state = ifmux.channel(0).get_state()

if state == CANState.ERROR_ACTIVE:
    print("Channel OK")
elif state == CANState.ERROR_PASSIVE:
    print("Channel in error passive mode")
elif state == CANState.BUS_OFF:
    print("Channel bus-off (disconnected)")
```

**CAN States:**
- `ERROR_ACTIVE` - Normal operation
- `ERROR_PASSIVE` - High error count, limited transmission
- `BUS_OFF` - Too many errors, disconnected from bus

---

### 5. Get Channel Statistics

```python
stats = ifmux.channel(0).get_stats()

print(f"TX count: {stats['tx_count']}")
print(f"RX count: {stats['rx_count']}")
print(f"Errors: {stats['error_count']}")
print(f"State: {stats['state']}")
print(f"Last error: {stats['lec']}")
```

**Statistics Fields:**
- `tx_count` - Transmitted message count
- `rx_count` - Received message count
- `error_count` - Error counter
- `state` - Current CAN state
- `lec` - Last error code (STUFF, FORM, ACK, BIT, CRC, etc.)

---

## 🔌 LIN Interface

For complete LIN documentation, see **[LIN Interface Guide](lin-interface.md)**.

### Quick LIN Usage

#### Enable LIN

```python
# IMPORTANT: Enable LIN when connecting
ifmux = sdk.connect_ifmux("MAC", auto_start=True, lin_enabled=True)
```

#### Configure LIN Frame

```python
ifmux.configure_lin_frame(
    frame_id=0x3C,      # Frame ID (0-63)
    data_length=8,      # Data length (1-8 bytes)
    checksum_type=1     # Enhanced checksum
)
```

#### Send LIN Frame

```python
data = bytes([0x3C, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07])
ifmux.send_lin_frame(frame_id=0x3C, data=data)
```

**See Also:** [LIN Interface Guide](lin-interface.md) for detailed LIN documentation with examples.

---

## 🔀 Relay Control

IfMux provides two relay systems for flexible signal routing:

### 1. Internal Relays (8 relays)

Each CAN channel has an internal relay for connecting to backplane or external circuits.

```python
# Close internal relay (connect to backplane)
ifmux.channel(0).set_internal_relay(closed=True)

# Open internal relay (disconnect)
ifmux.channel(0).set_internal_relay(closed=False)
```

**Use Cases:**
- Connect CAN channel to backplane
- Isolate CAN channel
- Create network topology

---

### 2. External Relay Matrix (8×8 = 64 connections)

8 inputs × 8 outputs relay matrix for flexible signal routing.

```python
# Connect channel 0 to external output 2
ifmux.channel(0).set_external_relay(output=2, closed=True)

# Disconnect
ifmux.channel(0).set_external_relay(output=2, closed=False)
```

**Parameters:**
- `output` (int): External output number (0-7)
- `closed` (bool): True to connect, False to disconnect

**Example - Route One Channel to Multiple Outputs:**
```python
# Route CAN channel 0 to multiple external outputs
for output in [0, 2, 5]:
    ifmux.channel(0).set_external_relay(output, closed=True)
print("Channel 0 routed to outputs 0, 2, 5")
```

---

## 🎯 Practical Examples

### Example 1: Multi-Network CAN Gateway Test

```python
from sdrig import SDRIG
from sdrig.types.enums import CANSpeed
import time

def setup_can_gateway_test(ifmux):
    """
    Simulate 3-network CAN gateway:
    - Channel 0: Powertrain CAN (500k)
    - Channel 1: Body CAN (250k)
    - Channel 2: Infotainment CAN (500k)
    """
    # Configure networks
    ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)  # Powertrain
    ifmux.channel(1).set_speed(CANSpeed.SPEED_250K)  # Body
    ifmux.channel(2).set_speed(CANSpeed.SPEED_500K)  # Infotainment

    print("CAN gateway test network configured")

    # Send test messages on each network
    # Powertrain: Engine RPM
    ifmux.send_raw_can(0, 0x0CF00400, b'\x10\x27\xFF\xFF\xFF\xFF\xFF\xFF')

    # Body: Door status
    ifmux.send_raw_can(1, 0x220, b'\x01\x00\x00\x00')

    # Infotainment: Media status
    ifmux.send_raw_can(2, 0x3A0, b'\x05\x02\x01')

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    ifmux = sdk.connect_ifmux("66:6A:DB:B3:06:27", auto_start=True)
    time.sleep(2)

    setup_can_gateway_test(ifmux)
```

---

### Example 2: CAN Bus Load Testing

```python
from sdrig import SDRIG
from sdrig.types.enums import CANSpeed
import time
import random

def can_bus_load_test(ifmux, channel_id, duration_sec=10, load_percent=50):
    """
    Generate CAN bus load

    Args:
        ifmux: IfMux device
        channel_id: CAN channel
        duration_sec: Test duration in seconds
        load_percent: Target bus load (0-100%)
    """
    # Configure channel
    ifmux.channel(channel_id).set_speed(CANSpeed.SPEED_500K)

    # Calculate message rate
    # At 500kbps with 8-byte messages: ~8000 msgs/sec = 100% load
    max_msgs_per_sec = 8000
    target_msgs_per_sec = int(max_msgs_per_sec * load_percent / 100)
    interval = 1.0 / target_msgs_per_sec if target_msgs_per_sec > 0 else 1.0

    print(f"Generating {load_percent}% load on channel {channel_id}")
    print(f"Sending ~{target_msgs_per_sec} msgs/sec")

    start_time = time.time()
    msg_count = 0

    while time.time() - start_time < duration_sec:
        # Generate random CAN message
        can_id = random.randint(0x100, 0x7FF)
        data = bytes([random.randint(0, 255) for _ in range(8)])

        ifmux.send_raw_can(channel_id, can_id, data)
        msg_count += 1

        time.sleep(interval)

    print(f"Sent {msg_count} messages in {duration_sec}s")

    # Get statistics
    stats = ifmux.channel(channel_id).get_stats()
    print(f"Channel stats: {stats}")

# Usage
with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    ifmux = sdk.connect_ifmux("66:6A:DB:B3:06:27", auto_start=True)
    time.sleep(2)

    # Test 50% bus load for 10 seconds
    can_bus_load_test(ifmux, channel_id=0, duration_sec=10, load_percent=50)
```

---

### Example 3: CAN Message Monitoring

```python
from sdrig import SDRIG
from sdrig.types.enums import CANSpeed
import time
from collections import defaultdict

class CANMonitor:
    """Monitor and log CAN messages"""

    def __init__(self, ifmux):
        self.ifmux = ifmux
        self.message_counts = defaultdict(int)
        self.start_time = time.time()

    def on_can_message(self, channel_id, can_id, data):
        """Handle received CAN message"""
        self.message_counts[(channel_id, can_id)] += 1

        # Log message
        elapsed = time.time() - self.start_time
        print(f"[{elapsed:.3f}s] CH{channel_id} ID=0x{can_id:03X} "
              f"Data={data.hex()}")

    def print_statistics(self):
        """Print monitoring statistics"""
        print("\n=== CAN Monitor Statistics ===")
        for (ch, can_id), count in sorted(self.message_counts.items()):
            print(f"Channel {ch}, ID 0x{can_id:03X}: {count} messages")

# Usage
with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    ifmux = sdk.connect_ifmux("66:6A:DB:B3:06:27", auto_start=True)
    time.sleep(2)

    # Configure channel
    ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)

    # Create monitor
    monitor = CANMonitor(ifmux)
    ifmux.register_raw_can_callback(monitor.on_can_message)

    # Monitor for 30 seconds
    print("Monitoring CAN bus for 30 seconds...")
    time.sleep(30)

    # Print statistics
    monitor.print_statistics()
```

---

### Example 4: Relay Matrix Routing

```python
from sdrig import SDRIG
from sdrig.types.enums import CANSpeed
import time

def configure_relay_matrix(ifmux):
    """
    Configure relay matrix for ECU testing:
    - Channel 0 → Outputs 0, 1, 2 (3 ECUs)
    - Channel 1 → Output 3 (Gateway)
    - Channel 2 → Outputs 4, 5 (Test equipment)
    """
    print("Configuring relay matrix...")

    # Channel 0 to multiple ECUs
    ifmux.channel(0).set_external_relay(0, closed=True)
    ifmux.channel(0).set_external_relay(1, closed=True)
    ifmux.channel(0).set_external_relay(2, closed=True)

    # Channel 1 to gateway
    ifmux.channel(1).set_external_relay(3, closed=True)

    # Channel 2 to test equipment
    ifmux.channel(2).set_external_relay(4, closed=True)
    ifmux.channel(2).set_external_relay(5, closed=True)

    # Enable internal relays for backplane connection
    ifmux.channel(0).set_internal_relay(closed=True)
    ifmux.channel(1).set_internal_relay(closed=True)
    ifmux.channel(2).set_internal_relay(closed=True)

    print("Relay matrix configured")

# Usage
with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    ifmux = sdk.connect_ifmux("66:6A:DB:B3:06:27", auto_start=True)
    time.sleep(2)

    # Configure CAN speeds
    ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)
    ifmux.channel(1).set_speed(CANSpeed.SPEED_500K)
    ifmux.channel(2).set_speed(CANSpeed.SPEED_250K)

    # Configure relay routing
    configure_relay_matrix(ifmux)

    # Send test messages
    ifmux.send_raw_can(0, 0x123, b'\x01\x02\x03\x04')
    print("Test messages sent through relay matrix")
```

---

### Example 5: CAN FD High-Speed Testing

```python
from sdrig import SDRIG
from sdrig.types.enums import CANSpeed
import time

def can_fd_test(ifmux, channel_id):
    """Test CAN FD with high-speed data phase"""

    # Configure for CAN FD (5 Mbps data phase)
    ifmux.channel(channel_id).set_speed(CANSpeed.SPEED_5M)
    print(f"Channel {channel_id} configured for CAN FD @ 5 Mbps")

    # CAN FD allows up to 64 bytes
    large_payload = bytes(range(64))  # 0-63

    # Send CAN FD message
    ifmux.send_raw_can(
        channel_id=channel_id,
        can_id=0x123,
        data=large_payload,
        extended=True,
        fd=True
    )
    print(f"Sent CAN FD message with 64 bytes")

    # Send burst of CAN FD messages
    for i in range(100):
        data = bytes([i % 256] * 32)  # 32-byte payload
        ifmux.send_raw_can(channel_id, 0x100 + i, data, fd=True)

    # Check statistics
    stats = ifmux.channel(channel_id).get_stats()
    print(f"TX count: {stats['tx_count']}")

# Usage
with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    ifmux = sdk.connect_ifmux("66:6A:DB:B3:06:27", auto_start=True)
    time.sleep(2)

    can_fd_test(ifmux, channel_id=0)
```

---

## 🎓 Best Practices

### 1. Configure Speed Before Sending

```python
# ✗ Wrong: send without configuration
ifmux.send_raw_can(0, 0x123, b'\x01\x02')

# ✓ Correct: configure first
ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)
time.sleep(0.5)  # Allow configuration to apply
ifmux.send_raw_can(0, 0x123, b'\x01\x02')
```

### 2. Add Delays After Connection

```python
# Always wait after connecting
ifmux = sdk.connect_ifmux("MAC", auto_start=True)
time.sleep(2)  # Critical: allow device initialization

# Then proceed
ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)
```

**Recommended delays:**
- After connection: **2 seconds**
- After speed configuration: **500ms**
- Between relay changes: **100ms**

### 3. Monitor Channel State

```python
from sdrig.types.enums import CANState

# Check state before sending
state = ifmux.channel(0).get_state()
if state == CANState.BUS_OFF:
    print("ERROR: Channel is bus-off!")
    # Reset or reconfigure channel
elif state == CANState.ERROR_PASSIVE:
    print("WARNING: High error count")
else:
    # OK to send
    ifmux.send_raw_can(0, 0x123, data)
```

### 4. Use Correct CAN ID Format

```python
# Standard ID (11-bit): 0x000 - 0x7FF
ifmux.send_raw_can(0, 0x123, data, extended=False)

# Extended ID (29-bit): Use full 29 bits
# J1939 format example
ifmux.send_raw_can(0, 0x0CF00400, data, extended=True)
```

### 5. Validate Data Length

```python
def send_can_safe(ifmux, channel_id, can_id, data, fd=False):
    """Send CAN message with validation"""
    max_length = 64 if fd else 8

    if len(data) > max_length:
        raise ValueError(f"Data too long: {len(data)} (max {max_length})")

    ifmux.send_raw_can(channel_id, can_id, data, fd=fd)
```

### 6. Handle LIN Correctly

```python
# ✗ Wrong: LIN not enabled
ifmux = sdk.connect_ifmux("MAC", auto_start=True)
ifmux.configure_lin_frame(0x3C, 8)  # Will fail!

# ✓ Correct: enable LIN
ifmux = sdk.connect_ifmux("MAC", auto_start=True, lin_enabled=True)
time.sleep(2)
ifmux.configure_lin_frame(0x3C, 8)  # OK
```

### 7. Clean Up Relays

```python
# Open all relays when done
for ch in range(8):
    ifmux.channel(ch).set_internal_relay(closed=False)
    for out in range(8):
        ifmux.channel(ch).set_external_relay(out, closed=False)
```

### 8. Enable Debug During Development

```python
# See all CAN traffic
with SDRIG(iface="enp0s31f6", stream_id=1, debug=True) as sdk:
    ifmux = sdk.connect_ifmux("MAC", auto_start=True)
    # All CAN messages logged to console
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
if ifmux.is_running():
    print("✓ Device is running")
else:
    print("✗ Device is not running")
    ifmux.start()  # Start manually

# Check if device is alive
if ifmux.is_alive():
    print("✓ Device responding")
else:
    print("✗ Device not responding")
```

### Monitor Channel Statistics

```python
# Get detailed channel stats
for ch_id in range(8):
    stats = ifmux.channel(ch_id).get_stats()
    print(f"Channel {ch_id}:")
    print(f"  State: {stats['state']}")
    print(f"  TX: {stats['tx_count']}, RX: {stats['rx_count']}")
    print(f"  Errors: {stats['error_count']}, LEC: {stats['lec']}")
```

---

## ⚠️ Troubleshooting

### Issue: No CAN Messages Sent/Received

**Possible causes:**

1. **Speed not configured**
   ```python
   # Configure speed first
   ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)
   time.sleep(0.5)
   ```

2. **Channel in BUS_OFF state**
   ```python
   # Check state
   state = ifmux.channel(0).get_state()
   if state == CANState.BUS_OFF:
       # Reconfigure or reset
       ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)
   ```

3. **No termination resistor**
   - CAN bus requires 120Ω termination at each end
   - Check physical connections

---

### Issue: LIN Not Working

**Cause:** LIN not enabled when connecting.

**Solution:**
```python
# ✓ Correct
ifmux = sdk.connect_ifmux("MAC", auto_start=True, lin_enabled=True)
```

See [LIN Interface Guide](lin-interface.md) for detailed LIN troubleshooting.

---

### Issue: High Error Count

**Diagnosis:**
```python
stats = ifmux.channel(0).get_stats()
lec = ifmux.channel(0).get_lec()

print(f"Error count: {stats['error_count']}")
print(f"Last error: {lec.name}")
```

**Common errors:**
- `ACK` - No other node on bus
- `STUFF` - Bit stuffing violation
- `FORM` - Frame format error
- `CRC` - CRC check failed
- `BIT` - Bit error

**Solutions:**
- Check termination (120Ω)
- Verify bus speed matches other nodes
- Check wiring quality
- Reduce bus load

---

### Issue: Device Not Responding

**Solutions:**

1. **Check network connection**
   ```bash
   python examples/01_device_discovery.py
   ```

2. **Verify MAC address**
   ```python
   devices = sdk.discover_devices()
   for dev in devices:
       if dev.type == DeviceType.IFMUX:
           print(f"IfMux MAC: {dev.mac}")
   ```

3. **Check heartbeat**
   ```python
   # Ensure auto_start=True or start manually
   ifmux = sdk.connect_ifmux("MAC", auto_start=True)
   ```

---

### Issue: Relay Matrix Not Working

**Diagnosis:**
```python
# Set relay and verify
ifmux.channel(0).set_external_relay(2, closed=True)
time.sleep(0.1)

# Check with multimeter if connection is made
```

**Common issues:**
- Insufficient delay after relay command
- Relay already in use by another channel
- Hardware limitation (check manual)

---

## 📊 Technical Specifications

### CAN Specifications

| Parameter | Value |
|-----------|-------|
| **Channels** | 8 (0-7) |
| **CAN Classic Speeds** | 125K, 250K, 500K, 1M bps |
| **CAN FD Speeds** | 1M, 2M, 4M, 5M, 8M bps |
| **CAN ID** | 11-bit standard, 29-bit extended |
| **Data Length (Classic)** | Up to 8 bytes |
| **Data Length (FD)** | Up to 64 bytes |
| **Backplane Channels** | 16 additional channels |

### Relay Specifications

| Type | Count | Description |
|------|-------|-------------|
| **Internal Relays** | 8 | One per CAN channel |
| **External Matrix** | 8×8 (64) | Flexible routing |
| **Switching Time** | < 10ms | Typical |

### LIN Specifications

| Parameter | Value |
|-----------|-------|
| **Standard** | LIN 2.0 |
| **Speed** | Up to 20 kbit/s |
| **Frame ID** | 0-63 |
| **Data Length** | 1-8 bytes |
| **Checksum** | Classic / Enhanced |

---

## 🔗 Additional Resources

### Documentation
- **Main Documentation**: [`docs/README.md`](../README.md)
- **LIN Interface Guide**: [`docs/guides/lin-interface.md`](lin-interface.md)
- **CAN Protocol Reference**: [`docs/api/can-protocol.md`](../api/can-protocol.md)
- **UIO Device Guide**: [`docs/guides/uio-device.md`](uio-device.md)

### Examples
- **CAN Communication**: [`examples/05_can_communication.py`](../../examples/05_can_communication.py)
- **LIN Communication**: [`examples/06_lin_communication.py`](../../examples/06_lin_communication.py)

### API Reference
- **API Class**: `sdrig.devices.device_ifmux.DeviceIfMux`
- **Channel Class**: `sdrig.devices.device_ifmux.CANChannel`
- **Enums**: `sdrig.types.enums.CANSpeed`, `CANState`, `LastErrorCode`

### Standards
- **ISO 11898**: CAN specification
- **ISO 11898-1**: CAN FD specification
- **SAE J1939**: Commercial vehicle CAN protocol
- **ISO 17987**: LIN specification

### Official Resources
- **SODA Validate**: https://docs.soda.auto/projects/soda-validate/en/latest/
- **SDRig Hardware Manual**: https://docs.soda.auto/projects/soda-validate/en/latest/software-defined-rig.html

---

## 📝 Quick Reference

### CAN Channel Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `set_speed(speed)` | `CANSpeed` | Configure CAN speed |
| `get_state()` | - | Get CAN controller state |
| `get_lec()` | - | Get last error code |
| `get_stats()` | - | Get TX/RX/error statistics |
| `set_internal_relay(closed)` | `bool` | Control internal relay |
| `set_external_relay(out, closed)` | `int, bool` | Control external relay |

### IfMux Methods

| Method | Parameters | Description |
|--------|------------|-------------|
| `channel(id)` | `0-7` | Get CAN channel object |
| `send_raw_can(...)` | See API | Send raw CAN message |
| `register_raw_can_callback(cb)` | `function` | Register receive callback |
| `configure_lin_frame(...)` | See LIN | Configure LIN frame |
| `send_lin_frame(...)` | See LIN | Send LIN frame |

### Common Patterns

**Configure CAN:**
```python
ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)
```

**Send CAN:**
```python
ifmux.send_raw_can(0, 0x123, b'\x01\x02\x03')
```

**Monitor CAN:**
```python
ifmux.register_raw_can_callback(my_callback)
```

**Control relay:**
```python
ifmux.channel(0).set_internal_relay(closed=True)
```

**LIN (see LIN guide):**
```python
ifmux.configure_lin_frame(0x3C, 8)
ifmux.send_lin_frame(0x3C, data)
```

---

© 2026 SODA Validate. All rights reserved.
