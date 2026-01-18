#!/usr/bin/env python3
"""
Example 02: UIO Voltage Control

This example demonstrates how to control voltage output on UIO pins.
"""

import time
from sdrig import SDRIG

def main():
    """Control UIO voltage outputs"""
    print("SDRIG UIO Voltage Control Example")
    print("=" * 70)

    # UIO device MAC address (replace with your device)
    UIO_MAC = "82:7B:C4:B1:92:F2"

    with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
        # Connect to UIO device
        print(f"\nConnecting to UIO device: {UIO_MAC}")
        uio = sdk.connect_uio(UIO_MAC, auto_start=True)

        

        # Set voltage on multiple pins
        voltages = [5.0] #, 12.0, 24.0]
        for pin_num, voltage in enumerate(voltages):
            print(f"\nSetting pin {pin_num} to {voltage}V")
            uio.pin(pin_num).set_voltage(voltage)
            # time.sleep(0.1)

        # Read back voltage values
        print("\nReading voltage values...")
        time.sleep(1)
        for pin_num in range(1):
            voltage = uio.pin(pin_num).get_voltage()
            print(f"Pin {pin_num}: {voltage:.2f}V")

        # Disable all pins
        print("\nDisabling all pins...")
        uio.disable_all_pins()

        print("\nExample completed!")


if __name__ == "__main__":
    main()
