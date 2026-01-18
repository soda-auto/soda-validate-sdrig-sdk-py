#!/usr/bin/env python3
"""
Example 02b: UIO Current Loop Control

This example demonstrates how to control current loop (0-20mA) output on UIO pins.
Current loops are commonly used in industrial sensors and control systems.

Typical usage:
- 4-20mA standard: 4mA = 0%, 20mA = 100% (live zero for fault detection)
- 0-20mA standard: 0mA = 0%, 20mA = 100%
"""

import time
from sdrig import SDRIG

def main():
    """Control UIO current loop outputs"""
    print("SDRIG UIO Current Loop Control Example")
    print("=" * 70)

    # UIO device MAC address (replace with your device)
    UIO_MAC = "82:7B:C4:B1:92:F2"

    with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
        # Connect to UIO device
        print(f"\nConnecting to UIO device: {UIO_MAC}")
        uio = sdk.connect_uio(UIO_MAC, auto_start=True)

       
        # Example 1: Basic current output (0-20mA range)
        print("\n" + "=" * 70)
        print("Example 1: Basic Current Output (0-20mA)")
        print("=" * 70)

        current_values = [0.0, 5.0, 10.0, 15.0, 20.0]
        for current in current_values:
            print(f"\nSetting pin 0 to {current:.1f}mA")
            uio.pin(0).set_tx_current(current)
            time.sleep(1)

            # Read back current value
            read_current = uio.pin(0).get_tx_current()
            print(f"Pin 0 readback: {read_current:.2f}mA")

        # Example 2: 4-20mA industrial standard (simulating sensor values)
        print("\n" + "=" * 70)
        print("Example 2: 4-20mA Industrial Standard")
        print("=" * 70)
        print("Simulating sensor reading: 0% = 4mA, 100% = 20mA\n")

        # Function to convert percentage to 4-20mA
        def percent_to_current(percent):
            """Convert 0-100% to 4-20mA range"""
            return 4.0 + (percent / 100.0) * 16.0

        # Simulate different sensor readings
        sensor_readings = [0, 25, 50, 75, 100]  # Percentages

        for percent in sensor_readings:
            current = percent_to_current(percent)
            print(f"Sensor: {percent:3d}% -> {current:.2f}mA on pin 1")
            uio.pin(1).set_tx_current(current)
            time.sleep(1)

        # Example 3: Multiple pins with different current values
        print("\n" + "=" * 70)
        print("Example 3: Multiple Pins")
        print("=" * 70)

        pin_currents = [
            (0, 4.0),   # Pin 0: 4mA (0% sensor value)
            (1, 12.0),  # Pin 1: 12mA (50% sensor value)
            (2, 20.0),  # Pin 2: 20mA (100% sensor value)
        ]

        print("\nSetting multiple pins:")
        for pin_num, current in pin_currents:
            print(f"  Pin {pin_num}: {current:.1f}mA")
            uio.pin(pin_num).set_tx_current(current)
            time.sleep(0.5)

        # Read back all values
        print("\nReading back all values...")
        time.sleep(1)
        for pin_num, _ in pin_currents:
            current = uio.pin(pin_num).get_tx_current()
            print(f"  Pin {pin_num}: {current:.2f}mA")

        # Example 4: Current input measurement
        print("\n" + "=" * 70)
        print("Example 4: Current Input Measurement")
        print("=" * 70)
        print("(Connect external current source to measure)\n")

        print("Monitoring pin 3 for 5 seconds...")
        for i in range(10):
            current = uio.pin(3).get_rx_current()
            if current > 0.1:  # Threshold to detect signal
                print(f"  Sample {i+1}: {current:.2f}mA")
            else:
                print(f"  Sample {i+1}: No signal detected")
            time.sleep(0.5)

        # Disable all pins
        print("\n" + "=" * 70)
        print("Disabling all pins...")
        uio.disable_all_pins()

        print("\nExample completed!")
        print("=" * 70)


if __name__ == "__main__":
    main()
