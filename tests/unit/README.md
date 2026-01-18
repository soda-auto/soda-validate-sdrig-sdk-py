# SDRIG SDK - Unit Tests

## Overview

Unit tests for the SDRIG SDK. These tests run in isolation without requiring actual hardware.

## Test Structure

```
tests/unit/
├── __init__.py                  # Unit test package
├── conftest.py                  # Pytest fixtures and mocks
├── test_enums.py                # Test enum values (12 test classes, 70+ tests)
├── test_can_protocol.py         # Test CAN protocol utilities (5 test classes, 30+ tests)
├── test_device_uio.py           # Test UIO device class (6 test classes, 35+ tests)
└── test_device_eload.py         # Test ELoad device class (9 test classes, 50+ tests)
```

## Running Tests

### All Unit Tests
```bash
cd ./soda-validate-sdrig-sdk-py
pytest tests/unit/
```

### Specific Test File
```bash
pytest tests/unit/test_enums.py
pytest tests/unit/test_device_uio.py
pytest tests/unit/test_device_eload.py
```

### Specific Test Class
```bash
pytest tests/unit/test_enums.py::TestPGNEnum
pytest tests/unit/test_device_uio.py::TestUIOPinVoltage
```

### Specific Test Method
```bash
pytest tests/unit/test_enums.py::TestPGNEnum::test_module_info_req_exists
```

### With Coverage
```bash
pytest tests/unit/ --cov=sdrig --cov-report=html
```

### Verbose Output
```bash
pytest tests/unit/ -v
```

### Show Print Statements
```bash
pytest tests/unit/ -s
```

## Test Categories

### 1. Enum Tests (`test_enums.py`)

Tests all enum values for correctness per official manual:

- **TestPGNEnum**: All PGN values (30+ tests)
  - Device information PGNs
  - UIO PGNs
  - ELoad PGNs
  - CAN interface PGNs
  - LIN interface PGNs

- **TestDeviceType**: Device type enum
- **TestFeature**: Pin feature enum
- **TestFeatureState**: Feature state enum
- **TestRelayState**: Relay state enum
- **TestCANSpeed**: CAN bus speed enum
- **TestCANState**: CAN controller state enum
- **TestLastErrorCode**: CAN error code enum

### 2. Protocol Tests (`test_can_protocol.py`)

Tests CAN protocol utilities and J1939 compliance:

- **TestPrepareCANID**: CAN ID preparation
  - Basic CAN ID format
  - MODULE_INFO_REQ format
  - Priority handling
  - Source address handling

- **TestExtractPGNFromCANID**: PGN extraction
  - PGN extraction from CAN ID
  - Roundtrip testing

- **TestJ1939Format**: J1939 compliance
  - 29-bit extended ID
  - PDU1 format (PF < 240)
  - PDU2 format (PF >= 240)

- **TestCANIDComponents**: Bit field tests
  - Priority bits (26-28)
  - Source address bits (0-7)
  - PGN bits (8-25)

### 3. UIO Device Tests (`test_device_uio.py`)

Tests UIO device functionality with mocked hardware:

- **TestUIOPinVoltage**: Voltage control (6 tests)
  - Valid/invalid ranges (0-24V)
  - OP_MODE enabling
  - Relay control
  - Voltage measurement

- **TestUIOPinCurrent**: Current loop control (4 tests)
  - Valid/invalid ranges (0-20mA)
  - 4-20mA conversion
  - Current measurement

- **TestUIOPinPWM**: PWM control (7 tests)
  - Valid/invalid ranges (20Hz-5kHz, 0-100%)
  - ICU relay enabling
  - enable_pwm_input() method
  - PWM measurement

- **TestUIOPinControl**: Pin control (4 tests)
  - Pin number validation
  - disable_all_features()
  - disable_feature()

- **TestUIODevice**: Device class (3 tests)
  - Device creation
  - Device type
  - Start/stop

### 4. ELoad Device Tests (`test_device_eload.py`)

Tests ELoad device functionality including new features:

- **TestELoadCurrentSink**: Current sink mode (4 tests)
  - Valid/invalid ranges (0-10A)
  - Voltage source disabling
  - Current measurement

- **TestELoadVoltageSource**: Voltage source mode (4 tests)
  - Valid/invalid ranges (0-24V)
  - Current sink disabling
  - Voltage measurement

- **TestELoadMutuallyExclusiveModes**: Mode switching (3 tests)
  - Current → Voltage switching
  - Voltage → Current switching
  - Measurement mode (both disabled)

- **TestELoadRelayControl**: Relay control (3 tests)
  - Valid/invalid relay IDs (0-3)
  - Set/get relay state

- **TestELoadPowerManagement**: Power monitoring (4 tests)
  - Power calculation (V * I)
  - Total power
  - Power limits
  - Temperature monitoring

- **TestELoadChannelControl**: Channel control (4 tests)
  - Channel number validation
  - disable_channel()
  - disable_all_channels()

- **TestELoadDevice**: Device class (3 tests)
  - Device creation
  - Device type
  - Initial state

- **TestELoadOPMode**: OP_MODE management (3 tests)
  - OP_MODE setting
  - Voltage source OP_MODE
  - Current sink OP_MODE

## Mocking Strategy

### Fixtures (conftest.py)

1. **mock_can_db**: Mocks cantools.database.Database
   - encode_message()
   - decode_message()

2. **mock_avtp_manager**: Mocks AVTP communication
   - send_can_message()
   - start_listening()
   - stop_listening()

3. **mock_task_monitor**: Mocks periodic task scheduler
   - add_task_sec()
   - add_task_ms()
   - start()
   - stop()

4. **uio_device_mocks**: Combined mocks for UIO device
5. **eload_device_mocks**: Combined mocks for ELoad device

6. **Sample Data Fixtures**:
   - sample_module_info
   - sample_voltage_data
   - sample_current_data
   - sample_pwm_data

## What's NOT Tested

Unit tests do NOT test:
- Actual hardware communication
- AVTP packet transmission
- Network layer
- Real CAN bus communication
- DBC file parsing
- Timing requirements (tested in integration/compliance tests)

These are covered by integration tests and compliance tests.

## Test Coverage Goals

Target coverage:
- ✅ Enums: 100%
- ✅ CAN protocol utilities: 100%
- ✅ Device classes (public API): 90%+
- ⚠️ Internal methods: 70%+
- ⚠️ Error handling: 80%+

## Adding New Tests

### Test Template

```python
class TestNewFeature:
    """Test new feature"""

    def test_basic_functionality(self, uio_device_mocks):
        """Test basic functionality"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        # Test code here
        assert result == expected

    def test_error_case(self, uio_device_mocks):
        """Test error handling"""
        uio = DeviceUIO(
            mac_address="00:11:22:33:44:55",
            iface="eth0",
            stream_id=1,
            dbc_path="test.dbc"
        )

        with pytest.raises(ValueError):
            uio.some_method(invalid_value)
```

## Dependencies

Required packages:
- pytest (>=7.0.0)
- pytest-mock (optional, for advanced mocking)
- pytest-cov (optional, for coverage reports)

Install:
```bash
pip install pytest pytest-mock pytest-cov
```

## CI/CD Integration

These tests can be run in CI/CD without hardware:

```yaml
# Example GitHub Actions
- name: Run unit tests
  run: pytest tests/unit/ --cov=sdrig --cov-report=xml

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

## Tips

1. **Fast Tests**: Unit tests should run in < 1 second each
2. **Isolation**: Each test should be independent
3. **Clear Names**: Test names should describe what they test
4. **Arrange-Act-Assert**: Use AAA pattern
5. **One Assert**: Prefer one assertion per test (or related assertions)

## See Also

- `tests/test_integration_all_messages.py` - Integration tests (requires hardware)
- `tests/test_official_manual_compliance.py` - Compliance tests (requires hardware)
- `tests/README_TESTS.md` - General test documentation

---

**Total Unit Tests**: 185+
**Test Files**: 4
**Test Classes**: 32
**Coverage**: Enums, Protocol, UIO, ELoad
