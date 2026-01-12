#!/usr/bin/env python3
"""
Example: UIO Pin Control

This example demonstrates how to control UIO module pins programmatically.
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from pins_write import UIOPinController, resolve_dst


def example_voltage_control():
    """Example: Control voltage output"""
    print("=" * 60)
    print("Example 1: Voltage Output Control")
    print("=" * 60)

    controller = UIOPinController(
        iface="enp2s0.3900",
        stream_id=1,
        dbc_path="../soda_xil_fd.dbc"
    )

    dst = resolve_dst("UIO1")

    # Set different voltages on different pins
    voltages = [5.0, 12.0, 24.0]
    for pin, voltage in enumerate(voltages):
        print(f"\nSetting pin {pin} to {voltage}V")
        controller.set_voltage(pin, voltage, dst)

    print("\nVoltage control example completed")


def example_current_control():
    """Example: Control current loop output"""
    print("\n" + "=" * 60)
    print("Example 2: Current Loop Output Control")
    print("=" * 60)

    controller = UIOPinController(
        iface="enp2s0.3900",
        stream_id=1,
        dbc_path="../soda_xil_fd.dbc"
    )

    dst = resolve_dst("UIO1")

    # Set current outputs
    currents = [4.0, 12.0, 20.0]  # mA
    for i, current in enumerate(currents):
        pin = i + 3  # Use pins 3, 4, 5
        print(f"\nSetting pin {pin} to {current}mA")
        controller.set_current(pin, current, dst)

    print("\nCurrent control example completed")


def example_pwm_control():
    """Example: Control PWM output"""
    print("\n" + "=" * 60)
    print("Example 3: PWM Output Control")
    print("=" * 60)

    controller = UIOPinController(
        iface="enp2s0.3900",
        stream_id=1,
        dbc_path="../soda_xil_fd.dbc"
    )

    dst = resolve_dst("UIO1")

    # Set PWM outputs with different frequencies and duty cycles
    pwm_configs = [
        (100, 25.0, 12.0),   # 100Hz, 25%, 12V
        (1000, 50.0, 12.0),  # 1kHz, 50%, 12V
        (5000, 75.0, 12.0),  # 5kHz, 75%, 12V
    ]

    for i, (freq, duty, voltage) in enumerate(pwm_configs):
        pin = i + 5  # Use pins 5, 6, 7
        print(f"\nSetting pin {pin} to PWM: {freq}Hz, {duty}%, {voltage}V")
        controller.set_pwm(pin, freq, duty, voltage, dst)

    print("\nPWM control example completed")


def example_disable_all():
    """Example: Disable all pin features"""
    print("\n" + "=" * 60)
    print("Example 4: Disable All Pin Features")
    print("=" * 60)

    controller = UIOPinController(
        iface="enp2s0.3900",
        stream_id=1,
        dbc_path="../soda_xil_fd.dbc"
    )

    dst = resolve_dst("UIO1")

    # Disable all features on all pins
    for pin in range(8):
        print(f"\nDisabling all features on pin {pin}")
        controller.disable_all_features(pin, dst)

    print("\nDisable example completed")


def main():
    print("UIO Pin Control Examples")
    print("=" * 60)
    print("\nNote: Make sure you have:")
    print("1. Network interface configured (enp2s0.3900)")
    print("2. UIO device connected and powered")
    print("3. Proper permissions to access network interface")
    print("4. DBC file in correct location")
    print()

    try:
        # Run examples
        example_voltage_control()
        example_current_control()
        example_pwm_control()
        example_disable_all()

        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)

    except Exception as e:
        print(f"\nError running examples: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
