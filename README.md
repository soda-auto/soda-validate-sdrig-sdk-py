# SDRIG Python SDK

## ABOUT
Professional Python SDK for controlling SDRIG (Software-Defined Remote Interface Gateway) hardware modules via **AVTP ACF-CAN** protocol.

Supports:
- **UIO** (Universal Input/Output) - 8 pins with voltage, current, and PWM I/O
- **ELoad** (Electronic Load) - 8 channels, 0-10A current sinking
- **IfMux** (Interface Multiplexer) - 8 CAN FD channels + optional LIN

## INSTALLATION

### From Source
```bash
pip install -e .
```

### Development Installation
```bash
pip install -e ".[dev]"
```

## PROJECT STRUCTURE
```
soda-validate-sdrig-sdk-py/
├── sdrig/                          # Main SDK package
│   ├── devices/                    # Device classes
│   │   ├── device_sdr.py          # Base device class
│   │   ├── device_uio.py          # UIO device
│   │   ├── device_eload.py        # ELoad device
│   │   └── device_ifmux.py        # IfMux device
│   ├── protocol/                   # Protocol implementation
│   │   ├── avtp.py                # AVTP packet handling
│   │   ├── avtp_manager.py        # AVTP communication manager
│   │   ├── can_protocol.py        # CAN/J1939 utilities
│   │   └── can_messages.py        # CAN message encoding/decoding
│   ├── utils/                      # Utilities
│   │   ├── logger.py              # Logging utilities
│   │   ├── task_monitor.py        # Periodic task scheduler
│   │   └── device_manager.py      # Device discovery
│   ├── types/                      # Type definitions
│   │   ├── enums.py               # Enumerations
│   │   └── structs.py             # Data structures
│   └── sdk.py                      # High-level SDK API
├── scripts/                        # Legacy standalone scripts
├── examples/                       # Usage examples
├── tests/                          # Unit and integration tests
└── soda_xil_fd.dbc                # CAN database file
```

## QUICK START

### SDK Usage (Recommended)

```python
from sdrig import SDRIG

# Create SDK instance with context manager
with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    # Discover devices
    devices = sdk.discover_devices()

    # Connect to UIO device
    uio = sdk.connect_uio("82:7B:C4:B1:92:F2", auto_start=True)

    # Set voltage on pin 0
    uio.pin(0).set_voltage(12.0)

    # Read current on pin 1
    current = uio.pin(1).get_current()
    print(f"Current: {current}mA")

    # Generate PWM on pin 2 (current HW outputs at fixed 5V)
    uio.pin(2).set_pwm(frequency=1000, duty_cycle=50.0)
```

### Legacy CLI Scripts

#### 1. Device Discovery
```bash
python scripts/devices_list.py --iface enp0s31f6
```

#### 2. Control UIO Pins
```bash
# Set voltage
python scripts/pins_write.py --dst UIO1 --pin 0 --voltage 12.0

# Set current
python scripts/pins_write.py --dst UIO1 --pin 1 --current 10.0

# Set PWM
python scripts/pins_write.py --dst UIO1 --pin 2 \
    --pwm --pwm-freq 1000 --pwm-duty 50 --pwm-voltage 12
```

## DEVICE ALIASES

Pre-configured device aliases in scripts:
- `UIO1`: 82:7B:C4:B1:92:F2
- `UIO2`: EA:42:53:AA:03:A3
- `UIO3`: AE:FF:85:97:E1:95
- `ELM1`: 86:12:35:9B:FD:45
- `ELM2`: 22:5D:94:7E:49:46
- `IFMUX`: 66:6A:DB:B3:06:27

You can also use MAC addresses directly:
```bash
python scripts/pins_write.py --dst 82:7B:C4:B1:92:F2 --pin 0 --voltage 12.0
```

## DOCKER USAGE

### Build
```bash
sudo docker build -t sdr-py-avtp .
```

### Run
```bash
sudo docker run --rm -it --network host \
    --cap-add NET_ADMIN --cap-add NET_RAW \
    --env-file .env \
    -v "$PWD/":/app \
    --entrypoint /bin/bash \
    sdr-py-avtp
```

### Inside Container
```bash
export SDRIG_IFACE=enp0s31f6
export SDRIG_STREAM_ID=1
export SDRIG_DBC=/app/soda_xil_fd.dbc
export PYTHONPATH=/app

# Discovery
python scripts/devices_list.py

# Control pins
python scripts/pins_write.py --dst UIO1 --pin 0 --voltage 12.0
```

## PROGRAMMATIC USAGE

```python
from pins_write import UIOPinController, resolve_dst

# Create controller
controller = UIOPinController(
    iface="enp0s31f6",
    stream_id=1,
    dbc_path="soda_xil_fd.dbc"
)

# Resolve device MAC
dst = resolve_dst("UIO1")

# Set voltage on pin 0
controller.set_voltage(pin=0, voltage=12.0, dst_mac=dst)

# Set current on pin 1
controller.set_current(pin=1, current=10.0, dst_mac=dst)

# Set PWM on pin 2 (current HW: fixed 5V output)
controller.set_pwm(
    pin=2,
    frequency=1000,  # Hz
    duty=50.0,       # %
    voltage=5.0,     # V (fixed in current HW)
    dst_mac=dst
)

# Disable all features on pin 0
controller.disable_all_features(pin=0, dst_mac=dst)
```

## PIN FEATURES

### UIO Module (8 pins)
Each pin supports (mutually exclusive):
- **Voltage Input**: Measure 0-24V
- **Voltage Output**: Generate 0-24V
- **Current Loop Input**: Measure 0-20mA (supports 4-20mA industrial standard)
- **Current Loop Output**: Generate 0-20mA (supports 4-20mA industrial standard)
- **PWM Input**: Measure frequency (20Hz-5kHz) and duty cycle (via ICU)
- **PWM Output**: Generate PWM (20Hz-5kHz, 0-100% duty, fixed 5V level)

**Current Loop Standards:**
- **0-20mA**: Full range, 0mA = 0%, 20mA = 100%
- **4-20mA**: Industrial standard with "live zero" (4mA = 0%, 20mA = 100%, <4mA = fault)

### Feature States
- `DISABLED` (2): Feature is off
- `OPERATE` (3): Feature is active and working
- Other states: UNKNOWN, IDLE, WARNING, ERROR

### Relay Management
The SDK automatically manages relay states when switching between features.
Only one output feature can be active per pin at a time.

## EXAMPLES

The `examples/` directory contains comprehensive examples:

```bash
# Device discovery
python examples/01_device_discovery.py

# UIO voltage control
python examples/02_uio_voltage_control.py

# UIO current loop control
python examples/02b_uio_current_control.py

# UIO PWM generation
python examples/03_uio_pwm_control.py

# UIO PWM input measurement
python examples/03b_uio_pwm_input.py

# Electronic load control
python examples/04_eload_control.py

# CAN communication via IfMux
python examples/05_can_communication.py

# LIN communication via IfMux
python examples/06_lin_communication.py
```

### Device-Specific Examples

#### UIO (Universal Input/Output)
```python
from sdrig import SDRIG

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    uio = sdk.connect_uio("82:7B:C4:B1:92:F2", auto_start=True)

    # Voltage I/O
    uio.pin(0).set_voltage(12.0)
    voltage = uio.pin(0).get_voltage()

    # Current Loop I/O (0-20mA)
    uio.pin(1).set_current(10.0)  # mA
    current = uio.pin(1).get_current()

    # 4-20mA Industrial Standard (4mA=0%, 20mA=100%)
    def percent_to_4_20ma(percent):
        return 4.0 + (percent / 100.0) * 16.0

    uio.pin(1).set_current(percent_to_4_20ma(50))  # 50% = 12mA

    # PWM Generation (current HW: fixed 5V output)
    uio.pin(2).set_pwm(frequency=1000, duty_cycle=50.0)  # voltage defaults to 5.0V
    freq, duty, volt = uio.pin(2).get_pwm()  # volt always 0.0 (ICU cannot measure voltage)

    # PWM Input Measurement (measure external PWM without generating output)
    uio.pin(3).enable_pwm_input()  # Enable ICU for PWM measurement
    freq, duty, volt = uio.pin(3).get_pwm()  # Read measured values
```

#### ELoad (Electronic Load)
```python
from sdrig import SDRIG

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    eload = sdk.connect_eload("AA:BB:CC:DD:EE:FF", auto_start=True)

    # Mode 1: Current Sink (Electronic Load, 0-10A per channel)
    eload.channel(0).set_current(2.5)  # Sink 2.5A

    # Mode 2: Voltage Source (Power Supply, 0-24V)
    eload.channel(1).set_voltage(12.0)  # Output 12V

    # Mode 3: Voltage Measurement (Disabled mode)
    eload.channel(2).set_current(0.0)  # Disable current sink
    eload.channel(2).set_voltage(0.0)  # Disable voltage source
    voltage = eload.channel(2).get_voltage()  # Measure external voltage

    # Monitor voltage, current, power, temperature (works in all modes)
    voltage = eload.channel(0).get_voltage()  # 0-24V
    current = eload.channel(0).get_current()  # Measured current
    power = eload.channel(0).get_power()      # V * I in watts
    temp = eload.channel(0).get_temperature() # Channel temperature

    # Total power across all channels
    total = eload.get_total_power()  # Max 600W total

    # Digital output relay control (4 relays: dout_1 to dout_4)
    eload.set_relay(0, closed=True)   # Close relay 0 (dout_1)
    state = eload.get_relay(0)        # Get relay state
    eload.set_relay(0, closed=False)  # Open relay 0

    # Note: Current sink and voltage source modes are mutually exclusive per channel
```

#### IfMux (CAN/LIN Interface Multiplexer)
```python
from sdrig import SDRIG, CANSpeed

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    ifmux = sdk.connect_ifmux("11:22:33:44:55:66", auto_start=True)

    # Configure CAN channel
    ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)
    ifmux.channel(0).set_internal_relay(True)

    # Send raw CAN message
    ifmux.send_raw_can(
        channel_id=0,
        can_id=0x123,
        data=b'\x01\x02\x03\x04',
        extended=False
    )

    # Check status
    stats = ifmux.channel(0).get_stats()
```

#### LIN Communication
```python
from sdrig import SDRIG

with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
    # Enable LIN support
    ifmux = sdk.connect_ifmux("11:22:33:44:55:66", auto_start=True, lin_enabled=True)

    # Configure LIN frame
    ifmux.configure_lin_frame(frame_id=0x3C, data_length=8, checksum_type=1)

    # Send LIN frame
    data = bytes([0x3C, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07])
    ifmux.send_lin_frame(0x3C, data)
```

**See full guide:** [`docs/guides/lin-interface.md`](docs/guides/lin-interface.md)

## DETAILED GUIDES

- **ELoad Complete Guide**: [`docs/guides/eload-device.md`](docs/guides/eload-device.md) - Electronic load with voltage source/sink modes
- **LIN Interface Guide**: [`docs/guides/lin-interface.md`](docs/guides/lin-interface.md) - Complete LIN communication guide
- **CAN Messages Reference**: [`docs/api/can-protocol.md`](docs/api/can-protocol.md) - Complete CAN message documentation

## PROTOCOL DETAILS

The SDK uses AVTP (Audio Video Transport Protocol) with ACF-CAN encapsulation:
1. **OP_MODE_req**: Enable/disable pin features
2. **SWITCH_OUTPUT_req**: Control relay states
3. **VOLTAGE/CURRENT/PWM_req**: Set output values

All messages use:
- Extended CAN IDs (29-bit)
- CAN FD format
- J1939 PGN addressing


## TROUBLESHOOTING

### Permission Denied
Run with sudo or add user to appropriate groups:
```bash
sudo usermod -aG dialout $USER
```

### Network Interface Not Found
Check interface name:
```bash
ip link show
```

### No Response from Device
1. Check device power
2. Verify MAC address
3. Check network connectivity
4. Use `can_sniff.py` to monitor traffic


## SUPPORT

For issues and questions:
- GitHub Issues: https://github.com/soda-auto/soda-validate-sdrig-sdk-py/issues
- Documentation: https://docs.soda.auto/
