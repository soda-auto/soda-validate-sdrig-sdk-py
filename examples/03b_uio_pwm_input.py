#!/usr/bin/env python3
"""
Example 03b: UIO PWM Input Measurement

This example demonstrates how to measure external PWM signals on UIO pins
using the ICU (Input Capture Unit) without generating PWM output.
"""

import time
from sdrig import SDRIG

def main():
    """Measure external PWM signals on UIO pins"""
    print("SDRIG UIO PWM Input Measurement Example")
    print("=" * 70)

    # UIO device MAC address (replace with your device)
    UIO_MAC = "82:7B:C4:B1:92:F2"

    with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
        # Connect to UIO device
        print(f"\nConnecting to UIO device: {UIO_MAC}")
        uio = sdk.connect_uio(UIO_MAC, auto_start=True)

       
        # Enable PWM input measurement on pins 0-2
        # This enables the ICU (Input Capture Unit) to measure external PWM signals
        print("\nEnabling PWM input measurement on pins 0-2...")
        for pin_num in range(3):
            uio.pin(pin_num).enable_pwm_input()
            print(f"Pin {pin_num}: ICU enabled for PWM measurement")

        # Measure PWM signals for 10 seconds
        print("\nMeasuring PWM signals for 10 seconds...")
        print("(Connect external PWM source to pins 0-2)")
        print()

        for i in range(20):  # 20 samples over 10 seconds
            print(f"Sample {i+1}/20:")
            for pin_num in range(3):
                freq, duty, voltage = uio.pin(pin_num).get_pwm()
                # Note: ICU measures only frequency and duty cycle, not voltage
                if freq > 0:
                    print(f"  Pin {pin_num}: {freq:.1f}Hz, {duty:.1f}%")
                else:
                    print(f"  Pin {pin_num}: No signal detected")
            print()
            time.sleep(0.5)

        # Disable all pins
        print("Disabling all pins...")
        uio.disable_all_pins()

        print("\nExample completed!")


if __name__ == "__main__":
    main()
