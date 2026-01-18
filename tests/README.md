# SDRIG SDK Testing

Complete testing guide for the SDRIG Python SDK.

**Quick Navigation:**
- [Quick Start](#-quick-start) - Run tests immediately
- [Test Types](#-test-types) - Unit, Integration, Compliance
- [Requirements](#-requirements) - Hardware and software needs
- [Documentation](#-documentation) - Detailed guides

---

## 🚀 Quick Start

### Run Unit Tests (No Hardware)

```bash
# Fast tests, no hardware required
pytest tests/unit/

# With coverage report
pytest tests/unit/ --cov=sdrig --cov-report=html
```

**Result**: 82 tests, ~0.5 seconds, 100% pass rate ✅

---

### Run Integration Tests (Hardware Required)

```bash
# All CAN message types
python tests/test_integration_all_messages.py

# Or detailed version
python tests/test_all_messages_detailed.py
```

**Requirements**: UIO, ELoad, IfMux devices connected to network

---

## 📊 Test Types

### 1. Unit Tests ⚡

**Speed**: Very fast (< 1 second)
**Hardware**: ❌ Not required
**Count**: 82 tests
**Coverage**: 42% overall, 100% for enums

Tests individual components in isolation using mocks:

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_enums.py` | 17 | Enum values and PGN verification |
| `test_can_protocol.py` | 15 | J1939 ID format, PGN extraction |
| `test_device_uio.py` | 34 | UIO pin operations |
| `test_device_eload.py` | 16 | ELoad channel control |

**Run:**
```bash
pytest tests/unit/                      # All unit tests
pytest tests/unit/test_enums.py         # Specific file
pytest tests/unit/ -v                   # Verbose output
pytest tests/unit/ --cov=sdrig          # With coverage
```

**Documentation**: [`tests/unit/README.md`](unit/README.md)

---

### 2. Integration Tests 🔧

**Speed**: Slow (2-5 minutes)
**Hardware**: ✅ Required (UIO, ELoad, IfMux)
**Count**: 27-33 message types

Tests complete message flow with real hardware:

**What's Tested:**
- **Device Discovery**: MODULE_INFO, MODULE_INFO_EX, PIN_INFO
- **UIO Messages** (16): Voltage, current, PWM, relay control
- **ELoad Messages** (3): Current sink, temperature monitoring
- **IfMux CAN** (5): Speed config, state monitoring, relays
- **IfMux LIN** (3): Frame configuration, send/receive

**Run:**
```bash
# Standard integration test
python tests/test_integration_all_messages.py

# Detailed with packet inspection
python tests/test_all_messages_detailed.py
```

**Hardware Setup:**
- Network interface: `enp0s31f6` (configurable in code)
- Stream ID: `1`
- All three device types must be on network

**Documentation**: [`tests/README_TESTS.md`](README_TESTS.md)

---

### 3. Compliance Tests 📋

**Speed**: Slow (3-10 minutes)
**Hardware**: ✅ Required (UIO, ELoad)
**Count**: 12 test areas

Verifies compliance with official SDRIG hardware manuals:

| # | Test Area | Description |
|---|-----------|-------------|
| 1 | MODULE_INFO heartbeat | 9s periodic requirement |
| 2 | Timing requirements | Message intervals |
| 3 | Message sequence | Correct order |
| 4 | ELoad voltage source | Output mode |
| 5 | ELoad voltage measurement | Input mode |
| 6 | ELoad mutually exclusive | Mode conflicts |
| 7 | ICU relay control | PWM input switching |
| 8 | 4-20mA standard | Industrial current loop |
| 9 | ELoad PGN values | Message IDs |
| 10 | Device info PGNs | Discovery messages |
| 11 | LIN PGN values | LIN protocol IDs |
| 12 | ELoad relay control | Relay switching |

**Run:**
```bash
python tests/test_official_manual_compliance.py
```

**Documentation**: [`docs/OFFICIAL_MANUAL_COMPLIANCE.md`](../docs/OFFICIAL_MANUAL_COMPLIANCE.md)

---

## 📦 Requirements

### Software Requirements

**Essential:**
```bash
pytest>=7.0.0
pytest-cov>=4.0.0
```

**Install:**
```bash
pip install -e ".[dev]"
```

### Hardware Requirements

**For Integration & Compliance Tests:**

| Device | Model | Required For |
|--------|-------|--------------|
| **UIO** | Universal I/O | Integration, Compliance |
| **ELoad** | Electronic Load | Integration, Compliance |
| **IfMux** | Interface Multiplexer | Integration only |

**Network Setup:**
- Ethernet interface (e.g., `enp0s31f6`)
- AVTP Stream ID: 1
- All devices on same network

**Check Device Availability:**
```bash
python examples/01_device_discovery.py
```

---

## 📖 Documentation

### Detailed Test Documentation

| Document | Description | Type |
|----------|-------------|------|
| [`unit/README.md`](unit/README.md) | Unit test guide | No hardware |
| [`README_TESTS.md`](README_TESTS.md) | Integration test guide | Hardware required |
| [`../TESTING.md`](../TESTING.md) | Complete testing guide | All types |
| [`../docs/OFFICIAL_MANUAL_COMPLIANCE.md`](../docs/OFFICIAL_MANUAL_COMPLIANCE.md) | Compliance verification | Hardware required |

### Related Documentation

- **Main Documentation**: [`docs/README.md`](../docs/README.md)
- **Device Guides**: [`docs/guides/`](../docs/guides/)
- **API Reference**: [`docs/api/`](../docs/api/)
- **Examples**: [`examples/`](../examples/)

---

## 🎯 Testing Pyramid

```
              /\
             /  \       Manual Testing
            /____\
           /      \     Compliance Tests (12 areas)
          /   12   \    ✅ Hardware required
         /  tests   \   🐌 Slow (3-10 min)
        /____________\
       /              \ Integration Tests (27-33)
      /   27 tests     \ ✅ Hardware required
     /   Hardware       \ 🐌 Slow (2-5 min)
    /     Required       \
   /______________________\
  /                        \ Unit Tests (82)
 /      82 tests            \ ❌ No hardware
/        No Hardware         \ ⚡ Fast (< 1s)
/____________________________\
```

**Testing Strategy:**
1. **Unit tests** - Run frequently during development (fast feedback)
2. **Integration tests** - Run before commits (verify hardware interaction)
3. **Compliance tests** - Run before releases (validate specifications)

---

## 🔬 Test Coverage

### Current Coverage (v0.2.0)

```
Module                     Statements  Coverage
-----------------------------------------------
sdrig/__init__.py                  12    100%
sdrig/types/enums.py              156    100%  ✓ Complete
sdrig/types/structs.py             45     67%
sdrig/protocol/can_protocol.py    87     45%
sdrig/devices/device_uio.py       245     38%
sdrig/devices/device_eload.py     178     40%
sdrig/devices/device_ifmux.py     156     32%
-----------------------------------------------
TOTAL                            1234     42%
```

**Target**: 70%+ coverage by v1.0.0

---

## ⚙️ Running Tests

### Quick Commands

```bash
# Unit tests only (fast)
pytest tests/unit/

# Unit tests with coverage
pytest tests/unit/ --cov=sdrig --cov-report=html
open htmlcov/index.html  # View coverage report

# Integration tests (requires hardware)
python tests/test_integration_all_messages.py

# Compliance tests (requires hardware)
python tests/test_official_manual_compliance.py

# Specific test file
pytest tests/unit/test_enums.py

# Specific test class
pytest tests/unit/test_enums.py::TestPGNEnum

# Verbose output
pytest tests/unit/ -v

# Stop on first failure
pytest tests/unit/ -x

# Show print statements
pytest tests/unit/ -s
```

---

## 🐛 Troubleshooting

### Unit Tests Failing

**Issue**: Import errors or module not found

**Solution**:
```bash
# Install in development mode
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

---

### Integration Tests Failing

**Issue**: "No devices found"

**Solution**:
```bash
# Check devices are on network
python examples/01_device_discovery.py

# Verify network interface
ip link show

# Check interface name in test code
# Edit IFACE variable in test files
```

---

**Issue**: "Permission denied" on network interface

**Solution**:
```bash
# Add user to dialout group
sudo usermod -aG dialout $USER

# Or run with sudo
sudo python tests/test_integration_all_messages.py
```

---

**Issue**: Timeouts or incomplete responses

**Solution**:
- Increase timeout values in test code
- Check network connection stability
- Verify device firmware versions
- Restart devices

---

### Compliance Tests Failing

**Issue**: Timing requirements not met

**Solution**:
- Check system load (high CPU can affect timing)
- Verify heartbeat messages are sent every 9 seconds
- Review `OFFICIAL_MANUAL_COMPLIANCE.md` for specifications

---

## 🎓 Best Practices

### 1. Run Unit Tests Frequently

```bash
# Before every commit
pytest tests/unit/

# During development (watch mode)
pytest-watch tests/unit/
```

### 2. Test Hardware Setup Separately

```bash
# Verify devices before running tests
python examples/01_device_discovery.py
```

### 3. Use Coverage to Find Gaps

```bash
# Generate coverage report
pytest tests/unit/ --cov=sdrig --cov-report=html

# Open report
open htmlcov/index.html
```

### 4. Isolate Failing Tests

```bash
# Run only failed tests from last run
pytest --lf

# Run specific failing test
pytest tests/unit/test_device_uio.py::TestUIOPinVoltage::test_set_voltage
```

### 5. Enable Debug Mode

```python
# In test code, enable debug logging
with SDRIG(iface="enp0s31f6", stream_id=1, debug=True) as sdk:
    # All CAN messages will be logged
    pass
```

---

## 📈 Test Statistics

### Version 0.2.0 (Current)

| Metric | Value |
|--------|-------|
| **Total Tests** | 82 unit + 27 integration + 12 compliance = 121 |
| **Unit Test Pass Rate** | 100% (82/82) ✅ |
| **Unit Test Speed** | < 0.5 seconds ⚡ |
| **Code Coverage** | 42% overall, 100% for enums |
| **Last Updated** | 2026-01-17 |

### Test Execution Time

| Test Type | Count | Time | Hardware |
|-----------|-------|------|----------|
| Unit | 82 | < 1s | ❌ No |
| Integration | 27 | 2-5 min | ✅ Yes |
| Compliance | 12 | 3-10 min | ✅ Yes |
| **Total** | **121** | **5-16 min** | - |

---

## 🔗 Additional Resources

### Testing Tools
- **pytest**: https://docs.pytest.org/
- **pytest-cov**: https://pytest-cov.readthedocs.io/
- **coverage.py**: https://coverage.readthedocs.io/

### SDRIG Resources
- **Main Documentation**: [`docs/README.md`](../docs/README.md)
- **CHANGELOG**: [`CHANGELOG.md`](../CHANGELOG.md)
- **Examples**: [`examples/`](../examples/)
- **Official SDRIG Docs**: https://docs.soda.auto/projects/soda-validate/en/latest/software-defined-rig.html

---

## 📝 Contributing Tests

### Adding Unit Tests

1. Create test file in `tests/unit/`
2. Use fixtures from `conftest.py`
3. Mock hardware dependencies
4. Follow naming convention: `test_*.py`

**Example:**
```python
def test_new_feature(uio_device_mocks):
    """Test new feature"""
    uio = DeviceUIO("MAC", "iface", 1, "dbc_path")

    # Test code here
    assert uio.some_method() == expected_value
```

### Adding Integration Tests

1. Add test to `test_integration_all_messages.py`
2. Ensure hardware is available
3. Add timeout handling
4. Document hardware requirements

### Running CI/CD

```bash
# Run all tests suitable for CI (unit tests only)
pytest tests/unit/ --cov=sdrig --cov-report=xml

# Generate coverage badge
coverage-badge -o coverage.svg
```

---

## 📞 Support

**Issues and Questions:**
- GitHub Issues: https://github.com/soda-auto/soda-validate-sdrig-sdk-py/issues
- Email: chubuchnyi@soda.auto

**Before Reporting Issues:**
1. Run `pytest tests/unit/` to verify basic functionality
2. Check device availability with `examples/01_device_discovery.py`
3. Review troubleshooting section above
4. Include test output and error messages

---

© 2026 SODA Validate. All rights reserved.
