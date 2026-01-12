# SDR Py Project

## ABOUT
Python SDK for SDRIG control via **AVTP ACF-CAN** frames

## INSTALLATION
```bash
pip install -r requirements.txt --user
```

## PROJECT STRUCTURE
```
soda-validate-sdrig-sdk-py/
├── scripts/
│   ├── AVTP.py                    # AVTP packet structures (Scapy)
│   ├── AvtpCanManager.py          # AVTP CAN message manager
│   ├── devices_list.py            # Device discovery and info parsing
│   ├── can_send.py                # Send raw CAN messages
│   ├── can_sniff.py               # Sniff CAN messages
│   ├── pins_read.py               # Read UIO pin information
│   └── pins_write.py              # Write/control UIO pins ⭐ NEW
├── examples/
│   └── uio_pin_control_example.py # Example usage
├── soda_xil_fd.dbc                # CAN database file
└── requirements.txt
```

## QUICK START

### 1. Device Discovery
Find all SDRIG devices on the network:
```bash
python scripts/devices_list.py --iface enp2s0.3900
```

### 2. Read Pin Information
Get pin capabilities and current state:
```bash
python scripts/pins_read.py --dst UIO1 --iface enp2s0.3900
```

### 3. Control Pins

#### Set Voltage Output (0-24V)
```bash
python scripts/pins_write.py --dst UIO1 --pin 0 --voltage 12.0
```

#### Set Current Loop Output (0-20mA)
```bash
python scripts/pins_write.py --dst UIO1 --pin 1 --current 10.0
```

#### Set PWM Output (20Hz-5kHz)
```bash
python scripts/pins_write.py --dst UIO1 --pin 2 \
    --pwm --pwm-freq 1000 --pwm-duty 50 --pwm-voltage 12
```

#### Disable All Features on a Pin
```bash
python scripts/pins_write.py --dst UIO1 --pin 0 --disable
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
export SDRIG_IFACE=enp2s0.3900
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
    iface="enp2s0.3900",
    stream_id=1,
    dbc_path="soda_xil_fd.dbc"
)

# Resolve device MAC
dst = resolve_dst("UIO1")

# Set voltage on pin 0
controller.set_voltage(pin=0, voltage=12.0, dst_mac=dst)

# Set current on pin 1
controller.set_current(pin=1, current=10.0, dst_mac=dst)

# Set PWM on pin 2
controller.set_pwm(
    pin=2,
    frequency=1000,  # Hz
    duty=50.0,       # %
    voltage=12.0,    # V
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
- **Current Loop Input**: Measure 0-20mA
- **Current Loop Output**: Generate 0-20mA
- **PWM Input**: Measure frequency (20Hz-5kHz) and duty cycle
- **PWM Output**: Generate PWM (20Hz-5kHz, 0-100% duty)

### Feature States
- `DISABLED` (2): Feature is off
- `OPERATE` (3): Feature is active and working
- Other states: UNKNOWN, IDLE, WARNING, ERROR

### Relay Management
The SDK automatically manages relay states when switching between features.
Only one output feature can be active per pin at a time.

## EXAMPLES

See `examples/uio_pin_control_example.py` for comprehensive examples:
```bash
cd examples
python uio_pin_control_example.py
```

## PROTOCOL DETAILS

The SDK uses AVTP (Audio Video Transport Protocol) with ACF-CAN encapsulation:
1. **OP_MODE_req**: Enable/disable pin features
2. **SWITCH_OUTPUT_req**: Control relay states
3. **VOLTAGE/CURRENT/PWM_req**: Set output values

All messages use:
- Extended CAN IDs (29-bit)
- CAN FD format
- J1939 PGN addressing

## DEVELOPMENT PLAN

See [PYTHON_SDK_DEVELOPMENT_PLAN.md](../PYTHON_SDK_DEVELOPMENT_PLAN.md) for:
- Full SDK architecture plan
- Object-oriented device classes
- Advanced features roadmap
- Testing strategy

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

## LICENSE

See LICENSE file for details.

## SUPPORT

For issues and questions:
- GitHub Issues: https://github.com/soda-auto/soda-validate-sdrig-sdk-py/issues
- Documentation: https://docs.soda.auto/
