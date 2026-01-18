# SDRIG Python SDK Documentation

Complete documentation for the SDRIG (Software-Defined Remote Interface Gateway) Python SDK.

**Official Documentation**: [SODA Validate - Software-Defined RIG](https://docs.soda.auto/projects/soda-validate/en/latest/software-defined-rig.html)

---

## 📚 Quick Navigation

| Section | Description | Status |
|---------|-------------|--------|
| [Getting Started](#-getting-started) | Installation and first steps | ✅ Complete |
| [Device Guides](#-device-guides) | Hardware module documentation | ✅ Complete |
| [API Reference](#-api-reference) | Protocol and SDK API | ✅ Complete |
| [Testing](#-testing) | Test documentation | ✅ Complete |
| [Development](#-development) | Contributing and architecture | 🟡 In Progress |
| [Examples](#-examples) | Code examples | ✅ Complete |

---

## 🚀 Getting Started

### Installation

```bash
# Install from source
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
```

### Quick Start

```python
from sdrig import SDRIG

# Create SDK instance with context manager
with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    # Discover devices
    devices = sdk.discover_devices()

    # Connect to UIO device
    uio = sdk.connect_uio("82:7B:C4:B1:92:F2", auto_start=True)

    # Control pin
    uio.pin(0).set_voltage(12.0)
    current = uio.pin(1).get_current()

    # Generate PWM
    uio.pin(2).set_pwm(frequency=1000, duty_cycle=50.0)
```

**See also:**
- [Main README](../README.md) - Project overview and examples
- [Examples Directory](../examples/) - Complete working examples

---

## 📖 Device Guides

### Universal Input/Output (UIO)
**8× universal channels with voltage, current, PWM, and relay control**

- **Features:**
  - Voltage I/O: 0-24V
  - Current I/O: 0-20mA (4-20mA industrial standard)
  - PWM I/O: 20Hz - 5kHz
  - Relay control

- **Documentation:**
  - 📄 [UIO Device Guide](guides/uio-device.md) ✅

**Quick Example:**
```python
uio = sdk.connect_uio("MAC", auto_start=True)
uio.pin(0).set_voltage(12.0)          # Set voltage
uio.pin(1).set_current(10.0)          # Set current (4-20mA)
uio.pin(2).set_pwm(1000, 50, 12)      # PWM: freq, duty, voltage
uio.pin(3).set_relay(RelayState.CLOSED)  # Control relay
```

---

### Electronic Load (ELoad)
**8× current sink channels (0-10A @ 0-24V)**

- **Features:**
  - Current sinking: 0-10A per channel
  - Voltage monitoring: 0-24V
  - Power limits: 200W/channel, 600W total
  - Temperature monitoring

- **Documentation:**
  - 📄 [ELoad Device Guide](guides/eload-device.md) ✅

**Quick Example:**
```python
eload = sdk.connect_eload("MAC", auto_start=True)
eload.channel(0).set_current(2.5)     # Sink 2.5A
voltage = eload.channel(0).get_voltage()
power = eload.get_total_power()
temp = eload.channel(0).get_temperature()
```

---

### Interface Multiplexer (IfMux)
**8× CAN FD channels + LIN interface**

- **Features:**
  - CAN FD: 125kbps - 5Mbps
  - LIN 2.0 support
  - Internal/external relays
  - State monitoring

- **Documentation:**
  - 📄 [IfMux Device Guide](guides/ifmux-device.md) ✅
  - 📄 [LIN Interface Guide](guides/lin-interface.md) ✅

**Quick Example:**
```python
# CAN
ifmux = sdk.connect_ifmux("MAC", auto_start=True)
ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)
ifmux.send_raw_can(channel=0, can_id=0x123, data=b'\x01\x02\x03')

# LIN
ifmux = sdk.connect_ifmux("MAC", auto_start=True, lin_enabled=True)
ifmux.configure_lin_frame(frame_id=0x3C, data_length=8)
ifmux.send_lin_frame(0x3C, data)
```

---

## 🔧 API Reference

### CAN Protocol
**Complete reference for all CAN messages in the SDRIG protocol**

- 📄 [CAN Messages Reference](api/can-protocol.md) ✅
  - 38 CAN message types
  - J1939 format (PDU1/PDU2, PGN addressing)
  - Timing requirements (heartbeat, periodic messages)
  - Field descriptions and data types
  - Message sequence diagrams

**Message Categories:**
- **Device Information** (3 messages): MODULE_INFO, MODULE_INFO_EX, PIN_INFO
- **UIO Messages** (16 messages): Voltage, current, PWM, relay control
- **ELoad Messages** (3 messages): Load control, measurements
- **IfMux CAN** (5 messages): CAN configuration, state, relays
- **IfMux LIN** (3 messages): LIN frame configuration and transfer

---

### SDK API
**High-level SDK classes and methods**

#### Main Classes

**SDRIG** - Main SDK Class
```python
from sdrig import SDRIG

sdk = SDRIG(iface="enp0s31f6", stream_id=1, debug=False)
```
- `discover_devices(timeout=3.0)` - Discover all devices on network
- `connect_uio(mac, auto_start=False)` - Connect to UIO device
- `connect_eload(mac, auto_start=False)` - Connect to ELoad device
- `connect_ifmux(mac, auto_start=False, lin_enabled=False)` - Connect to IfMux

**DeviceUIO** - Universal Input/Output
- `pin(index)` - Access pin by index (0-7)
- `set_voltage(pin, voltage)` - Set output voltage (0-24V)
- `set_current(pin, current)` - Set output current (0-20mA)
- `set_pwm(pin, freq, duty, voltage)` - Generate PWM signal
- `set_relay(pin, state)` - Control relay (OPEN/CLOSED)
- `get_voltage(pin)` - Read input voltage
- `get_current(pin)` - Read input current

**DeviceELoad** - Electronic Load
- `channel(index)` - Access channel by index (0-7)
- `set_current(channel, current)` - Sink current (0-10A)
- `get_voltage(channel)` - Measure voltage
- `get_current(channel)` - Measure current
- `get_power(channel)` - Calculate power
- `get_total_power()` - Total power across all channels
- `get_temperature(channel)` - Read temperature sensor

**DeviceIfMux** - CAN/LIN Multiplexer
- `channel(index)` - Access CAN channel (0-7)
- `set_speed(channel, speed)` - Configure CAN speed (125K-5M)
- `send_raw_can(channel, can_id, data)` - Send raw CAN message
- `configure_lin_frame(frame_id, length)` - Configure LIN frame
- `send_lin_frame(frame_id, data)` - Send LIN frame
- `set_relay(channel, internal, external)` - Control CAN relays

---

### Type Definitions

**Enumerations:**
```python
from sdrig import (
    DeviceType,      # UIO, ELOAD, IFMUX
    Feature,         # GET_VOLTAGE, SET_VOLTAGE, GET_CURRENT, ...
    FeatureState,    # IDLE, OPERATE, ERROR, DISABLED
    RelayState,      # OPEN, CLOSED
    CANSpeed,        # SPEED_125K, SPEED_250K, SPEED_500K, SPEED_1M, SPEED_2M, SPEED_5M
    CANState,        # ERROR_ACTIVE, ERROR_PASSIVE, BUS_OFF
    LastErrorCode,   # NONE, STUFF, FORM, ACK, BIT1, BIT0, CRC
    PGN              # All Parameter Group Numbers (0x000FF - 0x143FF)
)
```

**Data Classes:**
```python
from sdrig import (
    PinState,           # UIO pin state (voltage, current, PWM, relay)
    ValuePair,          # Get/Set value pair
    PWMConfig,          # PWM configuration (freq, duty, voltage)
    ModuleInfo,         # Module information (MAC, type, version, serial)
    CANChannelState,    # CAN channel state (speed, tx/rx counters, errors)
    ELoadChannelState   # ELoad channel state (voltage, current, power, temp)
)
```

---

## 🧪 Testing

### Unit Tests
- 📄 [Unit Test Documentation](../tests/unit/README.md) ✅
- **Coverage:** 82 tests, 100% pass rate
- **Areas:** Enums, CAN protocol, UIO device, ELoad device
- **Run:** `pytest tests/unit/`

### Integration Tests
- 📄 [Testing Guide](../tests/README.md) ✅
- **Hardware Requirements:** UIO, ELoad, IfMux connected to network
- **Tests:** All 38 CAN message types
- **Run:** `python tests/test_all_messages_detailed.py`

**See also:**
- 📄 [Testing Guide](../tests/README.md) - Complete testing documentation
- 📄 [TESTING.md](../TESTING.md) - Detailed testing guide

---

## 🛠️ Development

**Current Structure:**
```
sdrig/
├── devices/          # Device implementations (UIO, ELoad, IfMux)
├── protocol/         # AVTP, CAN/J1939, message encoding
├── utils/            # Logger, TaskMonitor, DeviceManager
├── types/            # Enums and dataclasses
└── sdk.py            # High-level SDK API
```
---

## 💻 Examples

All examples are in the [`examples/`](../examples/) directory:

1. **[01_device_discovery.py](../examples/01_device_discovery.py)** - Device discovery on network
2. **[02_uio_voltage_control.py](../examples/02_uio_voltage_control.py)** - Voltage input/output
3. **[03_uio_pwm_control.py](../examples/03_uio_pwm_control.py)** - PWM generation
4. **[04_eload_control.py](../examples/04_eload_control.py)** - Electronic load control
5. **[05_can_communication.py](../examples/05_can_communication.py)** - CAN message handling
6. **[06_lin_communication.py](../examples/06_lin_communication.py)** - LIN communication

---

## 🔍 Protocols

### AVTP (Audio Video Transport Protocol)
- **Standard:** IEEE 1722 Non-Time-Synchronous Control Format
- **Encapsulation:** ACF-CAN (AVTP Control Format for CAN)
- **EtherType:** 0x22F0
- **Transport:** Raw Ethernet Layer 2

### CAN / J1939
- **ID Format:** 29-bit Extended ID (J1939)
- **Addressing:** PGN-based (Parameter Group Number)
- **CAN FD:** Supported
- **Database:** DBC format with cantools integration

### LIN (Local Interconnect Network)
- **Version:** LIN 2.0
- **Frame ID:** 0-63
- **Data Length:** 1-8 bytes
- **Checksum:** Classic / Enhanced
- **Topology:** Master-Slave

---

## 🐛 Debugging

### Enable Debug Mode
```python
# Global debug mode
with SDRIG(iface="enp0s31f6", stream_id=1, debug=True) as sdk:
    # All messages logged to console
    pass

# Enable packet dumps
from sdrig import SDRIGLogger
SDRIGLogger.enable_debug_mode()
SDRIGLogger.enable_packet_dumps()
```

### Device Health Monitoring
```python
# Check device status
device.is_running()  # True/False
device.is_alive()    # True/False

# Health information
health = device.health
print(f"Last seen: {health.last_seen}")
print(f"Message count: {health.message_count}")
print(f"Error count: {health.error_count}")
```

---

## 📦 Utilities

### DeviceManager
```python
from sdrig.utils.device_manager import DeviceManager

manager = DeviceManager(iface="enp0s31f6", stream_id=1, dbc_path="soda_xil_fd.dbc")
devices = manager.discover_devices(timeout=3.0)
manager.print_devices()
```

### TaskMonitor
```python
from sdrig.utils.task_monitor import TaskMonitor

monitor = TaskMonitor()
monitor.add_task_sec("heartbeat", send_heartbeat, period_sec=1.0)
monitor.start()
```

### Logger
```python
from sdrig.utils.logger import SDRIGLogger

logger = SDRIGLogger.get_logger("my_module")
logger.info("Message")
logger.debug("Debug info")
```

---

## ⚠️ Troubleshooting

### Permission Denied (Network Interface)
```bash
# Add user to dialout group
sudo usermod -aG dialout $USER

# Or run with sudo
sudo python your_script.py
```

### Network Interface Not Found
```bash
# List all network interfaces
ip link show

# Check interface name (common: enp0s31f6, eth0, ens33)
```

### No Response from Device
1. Check device power and network connection
2. Verify MAC address is correct
3. Enable debug mode to see raw packets
4. Check that Stream ID matches device configuration

### LIN Not Working
1. Ensure `lin_enabled=True` when connecting to IfMux
2. Check physical LIN bus connection and termination
3. Verify Frame ID is in valid range (0-63)
4. Configure frame before attempting to send

### Test Failures
1. Check that all devices are powered and connected
2. Verify network interface name in test configuration
3. Run device discovery to confirm devices are visible
4. Check that no other process is using the network interface

---

## 🔗 Additional Resources

### Official Links
- **SODA Validate Docs:** https://docs.soda.auto/projects/soda-validate/en/latest/
- **SDRig Hardware Manual:** https://docs.soda.auto/projects/soda-validate/en/latest/software-defined-rig.html
- **GitHub Repository:** https://github.com/soda-auto/soda-validate-sdrig-sdk-py
- **Issue Tracker:** https://github.com/soda-auto/soda-validate-sdrig-sdk-py/issues

### Standards
- **IEEE 1722:** AVTP (Audio Video Transport Protocol)
- **ISO 11898:** CAN Specification
- **SAE J1939:** Commercial Vehicle Network Protocol
- **ISO 17987:** LIN Specification

---

## 📧 Support

**Questions and Issues:**
- GitHub Issues: https://github.com/soda-auto/soda-validate-sdrig-sdk-py/issues
- Email: chubuchnyi@soda.auto

**Contributing:**
- Pull requests welcome
- Follow existing code style
- Add unit tests for new features
- Update documentation

---

© 2026 SODA Validate. All rights reserved.
