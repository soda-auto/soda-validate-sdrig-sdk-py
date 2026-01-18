#!/usr/bin/env python3
"""
Manual Unit Test Runner (No pytest required)

Runs unit tests without pytest dependency for environments where pytest is not available.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import test modules
from tests.unit import test_enums

def run_test_class(test_class, class_name):
    """Run all test methods in a test class"""
    print(f"\n{'='*70}")
    print(f"Running {class_name}")
    print(f"{'='*70}")

    test_instance = test_class()
    test_methods = [m for m in dir(test_instance) if m.startswith('test_')]

    passed = 0
    failed = 0

    for method_name in test_methods:
        try:
            method = getattr(test_instance, method_name)
            method()
            print(f"  ✓ {method_name}")
            passed += 1
        except AssertionError as e:
            print(f"  ✗ {method_name}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ✗ {method_name}: ERROR - {e}")
            failed += 1

    return passed, failed


def main():
    """Run all unit tests"""
    print("="*70)
    print("SDRIG SDK - Manual Unit Test Runner")
    print("="*70)

    total_passed = 0
    total_failed = 0

    # Test enums
    test_classes = [
        (test_enums.TestPGNEnum, "TestPGNEnum"),
        (test_enums.TestDeviceType, "TestDeviceType"),
        (test_enums.TestFeature, "TestFeature"),
        (test_enums.TestFeatureState, "TestFeatureState"),
        (test_enums.TestRelayState, "TestRelayState"),
        (test_enums.TestCANSpeed, "TestCANSpeed"),
        (test_enums.TestCANState, "TestCANState"),
        (test_enums.TestLastErrorCode, "TestLastErrorCode"),
    ]

    for test_class, class_name in test_classes:
        passed, failed = run_test_class(test_class, class_name)
        total_passed += passed
        total_failed += failed

    # Print summary
    print(f"\n{'='*70}")
    print(f"TEST SUMMARY")
    print(f"{'='*70}")
    print(f"Total tests run: {total_passed + total_failed}")
    print(f"Passed:          {total_passed} ({'✓' if total_failed == 0 else ''})")
    print(f"Failed:          {total_failed}")
    print(f"{'='*70}")

    if total_failed == 0:
        print("✓ ALL TESTS PASSED!")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())
