#!/usr/bin/env python3
"""
Example 03: UIO PWM Control

This example demonstrates how to generate PWM signals on UIO pins.
"""

import time
from sdrig import SDRIG

def main():
    """Generate PWM signals on UIO pins"""
    print("SDRIG UIO PWM Control Example")
    print("=" * 70)

    # UIO device MAC address (replace with your device)
    UIO_MAC = "82:7B:C4:B1:92:F2"

    with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
        # Connect to UIO device
        print(f"\nConnecting to UIO device: {UIO_MAC}")
        uio = sdk.connect_uio(UIO_MAC, auto_start=True)

        # Wait for initialization
        time.sleep(2)

        # Configure PWM outputs
        # Note: Current hardware revision outputs PWM at fixed 5V level
        # set_pwm() automatically enables both PWM output and ICU input for monitoring
        pwm_configs = [
            (0, 100, 25.0),     # Pin 0: 100Hz, 25% duty (5V fixed)
            (1, 1000, 50.0),    # Pin 1: 1kHz, 50% duty (5V fixed)
            (2, 5000, 75.0),    # Pin 2: 5kHz, 75% duty (5V fixed)
        ]

        for pin_num, freq, duty in pwm_configs:
            print(f"\nPin {pin_num}: Setting PWM to {freq}Hz, {duty}% (5V fixed)")
            uio.pin(pin_num).set_pwm(freq, duty)  # voltage defaults to 5.0V
            time.sleep(0.5)

        # Let PWM run for a few seconds
        print("\nPWM signals running...")
        time.sleep(5)

        # Read PWM measurements
        print("\nReading PWM values...")
        for pin_num in range(3):
            freq, duty, voltage = uio.pin(pin_num).get_pwm()
            print(f"Pin {pin_num}: {freq:.1f}Hz, {duty:.1f}%, {voltage:.2f}V")

        # Disable all pins
        print("\nDisabling all pins...")
        uio.disable_all_pins()

        print("\nExample completed!")


if __name__ == "__main__":
    main()
