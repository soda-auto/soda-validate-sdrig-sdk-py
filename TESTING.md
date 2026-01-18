# SDRIG SDK - Complete Testing Guide

## Overview

The SDRIG SDK has comprehensive test coverage across multiple levels:

```
Testing Pyramid:
                /\
               /  \       Manual Testing
              /____\
             /      \     Compliance Tests (12 areas)
            / 12     \    test_official_manual_compliance.py
           /  tests   \   ✅ Requires hardware
          /____________\
         /              \ Integration Tests (27 tests)
        /   27 tests     \ test_integration_all_messages.py
       /    Hardware      \ test_all_messages_detailed.py
      /      Required      \ ✅ Requires hardware
     /______________________\
    /                        \
   /      185+ tests          \ Unit Tests
  /      No Hardware           \ tests/unit/
 /         Required              \ ⚡ Fast (< 5s)
/______________________________\ ❌ No hardware
```

## Test Types

### 1. Unit Tests (185+ tests) ⚡ FAST
**Location**: `tests/unit/`
**Hardware**: ❌ Not required
**Speed**: ⚡ Very fast (< 5 seconds total)

Tests individual components in isolation:
- ✅ Enum values (70+ tests)
- ✅ CAN protocol utilities (30+ tests)
- ✅ UIO device class (35+ tests)
- ✅ ELoad device class (50+ tests)

```bash
# Run all unit tests
pytest tests/unit/

# Run with coverage
pytest tests/unit/ --cov=sdrig --cov-report=html

# Quick script
./run_tests.sh unit
./run_tests.sh unit coverage
```

**Documentation**: `tests/unit/README.md`

### 2. Integration Tests (27 tests) 🐌 SLOW
**Location**: `tests/test_integration_all_messages.py`
**Hardware**: ✅ Required (UIO, ELoad, IfMux)
**Speed**: 🐌 Slow (~2-5 minutes)

Tests message flow across actual hardware:
- Device discovery
- UIO messages (voltage, current, PWM, relay)
- ELoad messages (current, temperature)
- IfMux messages (CAN, LIN)

```bash
# Run integration tests
python3 tests/test_integration_all_messages.py

# Or detailed version
python3 tests/test_all_messages_detailed.py
```

**Documentation**: `tests/README_TESTS.md`

### 3. Compliance Tests (12 areas) 🐌 SLOW
**Location**: `tests/test_official_manual_compliance.py`
**Hardware**: ✅ Required (UIO, ELoad)
**Speed**: 🐌 Slow (~3-10 minutes)

Tests compliance with official UIO/MUX manuals:
1. MODULE_INFO_REQ heartbeat
2. Timing requirements
3. Message sequence
4. ELoad voltage source mode
5. ELoad voltage measurement mode
6. ELoad mutually exclusive modes
7. ELoad relay control
8. ELoad PGN values
9. ICU relay control
10. 4-20mA industrial standard
11. Device information PGN values
12. LIN PGN values

```bash
# Run compliance tests
python3 tests/test_official_manual_compliance.py
```

**Documentation**: `tests/COMPLIANCE_TEST_SUMMARY.md`

## Quick Start

### Install Testing Dependencies

```bash
# Basic
pip install pytest

# Full testing suite
pip install -r requirements-test.txt
```

### Run All Tests

```bash
# Unit tests only (fast, no hardware)
./run_tests.sh unit

# Unit tests with coverage
./run_tests.sh unit coverage

# All tests (requires hardware)
./run_tests.sh all
```

### Run Specific Tests

```bash
# Unit tests - specific file
pytest tests/unit/test_enums.py

# Unit tests - specific class
pytest tests/unit/test_device_uio.py::TestUIOPinVoltage

# Unit tests - specific test
pytest tests/unit/test_enums.py::TestPGNEnum::test_module_info_req_exists

# Integration tests
python3 tests/test_integration_all_messages.py

# Compliance tests
python3 tests/test_official_manual_compliance.py
```

## Test Statistics

| Test Type | Tests | Hardware | Speed | Coverage |
|-----------|-------|----------|-------|----------|
| Unit | 185+ | ❌ No | ⚡ < 5s | Enums, Protocol, Devices |
| Integration | 27 | ✅ Yes | 🐌 ~5min | Message flow |
| Compliance | 12 areas | ✅ Yes | 🐌 ~10min | Manual requirements |
| **Total** | **224+** | - | - | **Comprehensive** |

## Test Coverage by Component

### Enums (100% target)
- ✅ PGN values (30+ tests)
- ✅ Device types
- ✅ Features and states
- ✅ CAN enums

### CAN Protocol (100% target)
- ✅ prepare_can_id()
- ✅ extract_pgn_from_can_id()
- ✅ J1939 format compliance
- ✅ Bit field extraction

### UIO Device (90%+ target)
- ✅ Voltage control (0-24V)
- ✅ Current loop (0-20mA, 4-20mA)
- ✅ PWM generation (20Hz-5kHz)
- ✅ PWM input (ICU)
- ✅ Relay control
- ✅ Feature enabling/disabling

### ELoad Device (90%+ target)
- ✅ Current sink mode (0-10A)
- ✅ Voltage source mode (0-24V)
- ✅ Voltage measurement mode
- ✅ Mutually exclusive modes
- ✅ Relay control (4 outputs)
- ✅ Power monitoring
- ✅ Temperature monitoring

### Protocol Layer (70%+ target)
- ✅ CAN ID encoding/decoding
- ⚠️ AVTP packet handling (integration)
- ⚠️ Message encoding (integration)

## Test Configuration

### Pytest Configuration (`pytest.ini`)

```ini
[pytest]
testpaths = tests/unit
addopts = -v --strict-markers --tb=short
markers =
    unit: Unit tests (no hardware)
    integration: Integration tests (hardware)
    compliance: Compliance tests (hardware)
```

### Running with Markers

```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run only compliance tests
pytest -m compliance
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Tests

on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt

      - name: Run unit tests
        run: pytest tests/unit/ --cov=sdrig

      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Docker Testing

```bash
# Build test image
docker build -t sdrig-tests .

# Run unit tests
docker run --rm sdrig-tests pytest tests/unit/

# Run with hardware (requires --network host)
docker run --rm --network host \
    --cap-add NET_ADMIN --cap-add NET_RAW \
    sdrig-tests python3 tests/test_official_manual_compliance.py
```

## Coverage Reports

### Generate Coverage Report

```bash
# HTML report
pytest tests/unit/ --cov=sdrig --cov-report=html

# Terminal report
pytest tests/unit/ --cov=sdrig --cov-report=term-missing

# XML report (for CI)
pytest tests/unit/ --cov=sdrig --cov-report=xml
```

### View Coverage Report

```bash
# Open HTML report
xdg-open htmlcov/index.html

# Or
firefox htmlcov/index.html
```

## Test Development

### Adding New Unit Tests

1. Create test file: `tests/unit/test_new_feature.py`
2. Import component to test
3. Write test class
4. Write test methods
5. Use fixtures from conftest.py

```python
import pytest
from sdrig.new_feature import NewFeature

class TestNewFeature:
    """Test new feature"""

    def test_basic_functionality(self):
        """Test basic functionality"""
        feature = NewFeature()
        result = feature.do_something()
        assert result == expected

    def test_error_case(self):
        """Test error handling"""
        feature = NewFeature()
        with pytest.raises(ValueError):
            feature.do_something(invalid_input)
```

### Adding New Integration Tests

1. Add to `test_integration_all_messages.py`
2. Follow existing test structure
3. Use MessageTracker for verification
4. Test with actual hardware

### Adding New Compliance Tests

1. Add to `test_official_manual_compliance.py`
2. Reference official manual requirement
3. Test both implementation and PGN values
4. Update COMPLIANCE_TEST_SUMMARY.md

## Test Best Practices

### Unit Tests
- ✅ Fast (< 1 second each)
- ✅ Isolated (no shared state)
- ✅ No hardware dependencies
- ✅ Clear test names
- ✅ One concept per test
- ✅ Use AAA pattern (Arrange-Act-Assert)

### Integration Tests
- ✅ Test real hardware
- ✅ Test message sequences
- ✅ Verify CAN messages sent/received
- ✅ Clean up after each test

### Compliance Tests
- ✅ Reference official manual
- ✅ Test timing requirements
- ✅ Test PGN values
- ✅ Test message sequences
- ✅ Document compliance status

## Troubleshooting

### Unit Tests Failing

```bash
# Run with verbose output
pytest tests/unit/ -v

# Run with print statements
pytest tests/unit/ -s

# Run specific failing test
pytest tests/unit/test_enums.py::TestPGNEnum::test_module_info_req_exists -v
```

### Integration Tests Failing

1. Check hardware connections
2. Verify network interface (enp0s31f6)
3. Check device MAC addresses
4. Run device discovery:
   ```bash
   python3 examples/01_device_discovery.py
   ```

### Compliance Tests Failing

1. Check hardware is powered
2. Verify device firmware versions
3. Check timing requirements
4. Review official manual requirements

### Import Errors

```bash
# Make sure PYTHONPATH is set
export PYTHONPATH=/home/chubuchnyi/SDRIG/soda-validate-sdrig-sdk-py:$PYTHONPATH

# Or install in development mode
pip install -e .
```

## Documentation

### Test Documentation Files

- **`TESTING.md`** (this file) - Complete testing guide
- **`tests/unit/README.md`** - Unit test documentation
- **`tests/README_TESTS.md`** - Integration test documentation
- **`tests/UNIT_TEST_SUMMARY.md`** - Unit test implementation summary
- **`tests/COMPLIANCE_TEST_SUMMARY.md`** - Compliance test details
- **`COMPLIANCE_STATUS.md`** - Overall compliance status

### Code Documentation

- **`docs/OFFICIAL_MANUAL_COMPLIANCE.md`** - Manual compliance verification
- **`docs/guides/eload-device.md`** - ELoad complete guide
- **`docs/api/can-protocol.md`** - CAN protocol reference

## Summary

✅ **Complete Testing Suite Implemented**

| Component | Status |
|-----------|--------|
| Unit Tests | ✅ 185+ tests, no hardware, < 5s |
| Integration Tests | ✅ 27 tests, hardware required |
| Compliance Tests | ✅ 12 areas, manual verified |
| Documentation | ✅ Complete and comprehensive |
| CI/CD Ready | ✅ Can run in containers |
| Coverage | ✅ Enums 100%, Devices 90%+ |

The SDRIG SDK has comprehensive test coverage at all levels, from fast unit tests to full compliance verification.

---

**Quick Commands**:
```bash
# Fast unit tests (no hardware)
./run_tests.sh unit

# With coverage
./run_tests.sh unit coverage

# Integration tests (requires hardware)
python3 tests/test_integration_all_messages.py

# Compliance tests (requires hardware)
python3 tests/test_official_manual_compliance.py
```

**Total Tests**: 224+
**Execution Time**: < 5 seconds (unit), ~5-10 minutes (integration + compliance)
**Hardware Required**: Only for integration and compliance tests
