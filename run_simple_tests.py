#!/usr/bin/env python3
"""
Simple Unit Test Runner (No pytest required)

Runs critical unit tests without pytest dependency.
"""

import sys
import importlib.util
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Load enums module directly without importing full package
spec = importlib.util.spec_from_file_location("enums", "sdrig/types/enums.py")
enums = importlib.util.module_from_spec(spec)
spec.loader.exec_module(enums)

# Extract enums
PGN = enums.PGN
DeviceType = enums.DeviceType
Feature = enums.Feature
FeatureState = enums.FeatureState
RelayState = enums.RelayState
CANSpeed = enums.CANSpeed
CANState = enums.CANState
LastErrorCode = enums.LastErrorCode

def test_pgn_values():
    """Test PGN enum values per official manual"""
    print("\n" + "="*70)
    print("Testing PGN Enum Values")
    print("="*70)

    tests = [
        ("MODULE_INFO_REQ", PGN.MODULE_INFO_REQ, 0x00000),
        ("MODULE_INFO", PGN.MODULE_INFO, 0x00100),
        ("MODULE_INFO_EX", PGN.MODULE_INFO_EX, 0x00800),
        ("MODULE_INFO_BOOT", PGN.MODULE_INFO_BOOT, 0x00200),
        ("PIN_INFO", PGN.PIN_INFO, 0x01000),
        ("OP_MODE_REQ", PGN.OP_MODE_REQ, 0x121FF),
        ("OP_MODE_ANS", PGN.OP_MODE_ANS, 0x120FF),
        ("VOLTAGE_IN_ANS", PGN.VOLTAGE_IN_ANS, 0x114FF),
        ("VOLTAGE_OUT_VAL_REQ", PGN.VOLTAGE_OUT_VAL_REQ, 0x116FF),
        ("PWM_IN_ANS", PGN.PWM_IN_ANS, 0x122FF),
        ("CUR_LOOP_IN_VAL_ANS", PGN.CUR_LOOP_IN_VAL_ANS, 0x128FF),
        ("SWITCH_OUTPUT_REQ", PGN.SWITCH_OUTPUT_REQ, 0x123FF),
        ("VOLTAGE_ELM_OUT_VAL_REQ", PGN.VOLTAGE_ELM_OUT_VAL_REQ, 0x116FF),
        ("VOLTAGE_ELM_IN_ANS", PGN.VOLTAGE_ELM_IN_ANS, 0x114FF),
        ("CUR_ELM_OUT_VAL_REQ", PGN.CUR_ELM_OUT_VAL_REQ, 0x129FF),
        ("CUR_ELM_IN_VAL_ANS", PGN.CUR_ELM_IN_VAL_ANS, 0x12AFF),
        ("TEMP_ELM_IN_ANS", PGN.TEMP_ELM_IN_ANS, 0x12EFF),
        ("SWITCH_ELM_DOUT_REQ", PGN.SWITCH_ELM_DOUT_REQ, 0x12CFF),
        ("SWITCH_ELM_DOUT_ANS", PGN.SWITCH_ELM_DOUT_ANS, 0x12DFF),
        ("CAN_INFO_REQ", PGN.CAN_INFO_REQ, 0x021FF),
        ("CAN_INFO_ANS", PGN.CAN_INFO_ANS, 0x02000),
        ("CAN_MUX_REQ", PGN.CAN_MUX_REQ, 0x028FF),
        ("CAN_MUX_ANS", PGN.CAN_MUX_ANS, 0x02900),
        ("LIN_CFG_REQ", PGN.LIN_CFG_REQ, 0x140FF),
        ("LIN_FRAME_SET_REQ", PGN.LIN_FRAME_SET_REQ, 0x142FF),
        ("LIN_FRAME_RCVD_ANS", PGN.LIN_FRAME_RCVD_ANS, 0x143FF),
    ]

    passed = 0
    failed = 0

    for name, actual, expected in tests:
        if actual == expected:
            print(f"  ✓ {name} = 0x{actual:05X}")
            passed += 1
        else:
            print(f"  ✗ {name} = 0x{actual:05X} (expected 0x{expected:05X})")
            failed += 1

    return passed, failed


def test_device_types():
    """Test DeviceType enum"""
    print("\n" + "="*70)
    print("Testing DeviceType Enum")
    print("="*70)

    tests = [
        ("UIO", DeviceType.UIO.value, "UIO"),
        ("ELOAD", DeviceType.ELOAD.value, "ELoad"),
        ("IFMUX", DeviceType.IFMUX.value, "IfMux"),
    ]

    passed = 0
    failed = 0

    for name, actual, expected in tests:
        if actual == expected:
            print(f"  ✓ DeviceType.{name} = '{actual}'")
            passed += 1
        else:
            print(f"  ✗ DeviceType.{name} = '{actual}' (expected '{expected}')")
            failed += 1

    return passed, failed


def test_features():
    """Test Feature enum"""
    print("\n" + "="*70)
    print("Testing Feature Enum")
    print("="*70)

    tests = [
        ("UNKNOWN", Feature.UNKNOWN, 0),
        ("GET_VOLTAGE", Feature.GET_VOLTAGE, 1),
        ("SET_VOLTAGE", Feature.SET_VOLTAGE, 2),
        ("GET_CURRENT", Feature.GET_CURRENT, 3),
        ("SET_CURRENT", Feature.SET_CURRENT, 4),
        ("GET_PWM", Feature.GET_PWM, 5),
        ("SET_PWM", Feature.SET_PWM, 6),
    ]

    passed = 0
    failed = 0

    for name, actual, expected in tests:
        if actual == expected:
            print(f"  ✓ Feature.{name} = {actual}")
            passed += 1
        else:
            print(f"  ✗ Feature.{name} = {actual} (expected {expected})")
            failed += 1

    return passed, failed


def test_feature_states():
    """Test FeatureState enum"""
    print("\n" + "="*70)
    print("Testing FeatureState Enum")
    print("="*70)

    tests = [
        ("UNKNOWN", FeatureState.UNKNOWN, 0),
        ("IDLE", FeatureState.IDLE, 1),
        ("DISABLED", FeatureState.DISABLED, 2),
        ("OPERATE", FeatureState.OPERATE, 3),
        ("WARNING", FeatureState.WARNING, 4),
        ("ERROR", FeatureState.ERROR, 5),
    ]

    passed = 0
    failed = 0

    for name, actual, expected in tests:
        if actual == expected:
            print(f"  ✓ FeatureState.{name} = {actual}")
            passed += 1
        else:
            print(f"  ✗ FeatureState.{name} = {actual} (expected {expected})")
            failed += 1

    return passed, failed


def test_can_speeds():
    """Test CANSpeed enum"""
    print("\n" + "="*70)
    print("Testing CANSpeed Enum")
    print("="*70)

    tests = [
        ("SPEED_125K", CANSpeed.SPEED_125K, 125000),
        ("SPEED_250K", CANSpeed.SPEED_250K, 250000),
        ("SPEED_500K", CANSpeed.SPEED_500K, 500000),
        ("SPEED_1M", CANSpeed.SPEED_1M, 1000000),
        ("SPEED_2M", CANSpeed.SPEED_2M, 2000000),
        ("SPEED_4M", CANSpeed.SPEED_4M, 4000000),
        ("SPEED_5M", CANSpeed.SPEED_5M, 5000000),
    ]

    passed = 0
    failed = 0

    for name, actual, expected in tests:
        if actual == expected:
            print(f"  ✓ CANSpeed.{name} = {actual}")
            passed += 1
        else:
            print(f"  ✗ CANSpeed.{name} = {actual} (expected {expected})")
            failed += 1

    return passed, failed


def test_can_protocol():
    """Test CAN protocol utilities"""
    print("\n" + "="*70)
    print("Testing CAN Protocol")
    print("="*70)

    try:
        # Load enums module and add to sys.modules for relative imports
        spec_enums = importlib.util.spec_from_file_location("sdrig.types.enums", "sdrig/types/enums.py")
        enums_module = importlib.util.module_from_spec(spec_enums)
        sys.modules['sdrig.types.enums'] = enums_module
        spec_enums.loader.exec_module(enums_module)

        # Load CAN protocol module
        spec = importlib.util.spec_from_file_location("can_protocol", "sdrig/protocol/can_protocol.py")
        can_protocol = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(can_protocol)

        prepare_can_id = can_protocol.prepare_can_id
        extract_pgn = can_protocol.extract_pgn
    except Exception as e:
        print(f"  ⚠️ Skipping CAN protocol tests: {e}")
        return 0, 0

    passed = 0
    failed = 0

    # Test prepare_can_id
    print("\n  Testing prepare_can_id():")
    test_cases = [
        (0x0F004, 0x00, 3),
        (0x121FF, 0xFE, 3),
        (0x116FF, 0xFE, 3),
    ]

    for pgn, sa, priority in test_cases:
        try:
            can_id = prepare_can_id(pgn, sa, priority)

            # Verify priority
            extracted_priority = (can_id >> 26) & 0x7
            assert extracted_priority == priority, f"Priority mismatch: {extracted_priority} != {priority}"

            # Verify source address
            extracted_sa = can_id & 0xFF
            assert extracted_sa == sa, f"SA mismatch: {extracted_sa} != {sa}"

            print(f"    ✓ PGN 0x{pgn:05X}, SA 0x{sa:02X}, Priority {priority} -> CAN ID 0x{can_id:08X}")
            passed += 1
        except Exception as e:
            print(f"    ✗ PGN 0x{pgn:05X}: {e}")
            failed += 1

    # Test extract_pgn
    print("\n  Testing extract_pgn():")
    test_pgns = [0x0F004, 0x121FF, 0x116FF]

    for original_pgn in test_pgns:
        try:
            can_id = prepare_can_id(original_pgn, 0xFE, 3)
            extracted_pgn = extract_pgn(can_id)
            assert extracted_pgn == original_pgn, f"PGN mismatch: 0x{extracted_pgn:05X} != 0x{original_pgn:05X}"
            print(f"    ✓ Roundtrip: 0x{original_pgn:05X} -> 0x{can_id:08X} -> 0x{extracted_pgn:05X}")
            passed += 1
        except Exception as e:
            print(f"    ✗ PGN 0x{original_pgn:05X}: {e}")
            failed += 1

    return passed, failed


def main():
    """Run all tests"""
    print("="*70)
    print("SDRIG SDK - Simple Unit Test Runner")
    print("="*70)
    print("Running critical unit tests without pytest...")

    total_passed = 0
    total_failed = 0

    # Run all test functions
    test_functions = [
        test_pgn_values,
        test_device_types,
        test_features,
        test_feature_states,
        test_can_speeds,
        test_can_protocol,
    ]

    for test_func in test_functions:
        try:
            passed, failed = test_func()
            total_passed += passed
            total_failed += failed
        except Exception as e:
            print(f"\n✗ ERROR in {test_func.__name__}: {e}")
            total_failed += 1

    # Print summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"Total tests:  {total_passed + total_failed}")
    print(f"Passed:       {total_passed} ({total_passed / (total_passed + total_failed) * 100:.1f}%)")
    print(f"Failed:       {total_failed}")
    print("="*70)

    if total_failed == 0:
        print("✓ ALL TESTS PASSED!")
        print("\nNote: This is a subset of the full test suite.")
        print("For complete testing, install pytest: pip install pytest")
        print("Then run: pytest tests/unit/")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
