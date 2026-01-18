#!/usr/bin/env python3
"""
Example 04: ELoad (Electronic Load) Control

This example demonstrates how to control electronic load channels with:
- Current sinking (0-10A per channel)
- Voltage monitoring
- Digital output relay control (4 relays)
- Power monitoring (per channel and total)

Hardware specs:
- 8 channels, 0-10A each
- 200W per channel max
- 600W total max
- 4 digital output relays (dout_1 to dout_4)
"""

import time
from sdrig import SDRIG

def main():
    """Control ELoad device"""
    print("SDRIG ELoad Control Example")
    print("=" * 70)

    # ELoad device MAC address (replace with your device)
    ELOAD_MAC = "86:12:35:9B:FD:45"  # ELM1

    with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
        # Connect to ELoad device
        print(f"\nConnecting to ELoad device: {ELOAD_MAC}")
        eload = sdk.connect_eload(ELOAD_MAC, auto_start=True)
        time.sleep(2)  # Wait for initialization
       
        # Example 1: Basic Current Sinking
        print("\n" + "=" * 70)
        print("Example 1: Current Sinking Control")
        print("=" * 70)

        print("\nSetting channel 0 to sink 2.5A...")
        eload.channel(0).set_current(2.5)
        time.sleep(2)

        # Read measurements
        voltage = eload.channel(0).get_voltage()
        current = eload.channel(0).get_current()
        power = eload.channel(0).get_power()
        

        print(f"Channel 0 measurements:")
        print(f"  Voltage: {voltage:.2f}V")
        print(f"  Current: {current:.3f}A")
        print(f"  Power: {power:.2f}W")
        

        # Example 2: Multiple Channels
        print("\n" + "=" * 70)
        print("Example 2: Multiple Channel Control")
        print("=" * 70)

        channels_config = [
            (0, 1.0),   # Channel 0: 1.0A
            (1, 2.5),   # Channel 1: 2.5A
            (2, 5.0),   # Channel 2: 5.0A
        ]

        print("\nConfiguring multiple channels:")
        for channel_id, current_target in channels_config:
            print(f"  Channel {channel_id}: {current_target}A")
            eload.channel(channel_id).set_current(current_target)
            time.sleep(1.5)

        # Monitor all channels
        print("\nMonitoring all active channels for 10 seconds...")
        for i in range(5):
            time.sleep(2)
            print(f"\n--- Sample {i+1}/5 ---")
            total_power = 0
            for channel_id, _ in channels_config:
                ch = eload.channel(channel_id)
                voltage = ch.get_voltage()
                current = ch.get_current()
                power = ch.get_power()
                total_power += power

                print(f"Ch{channel_id}: {voltage:.1f}V, {current:.2f}A, "
                      f"{power:.1f}W")

            print(f"Total Power: {total_power:.1f}W")

        # Example 3: Voltage Source Mode (Power Supply)
        print("\n" + "=" * 70)
        print("Example 3: Voltage Source Mode (Power Supply)")
        print("=" * 70)
        print("ELoad can work as a voltage source (power supply mode)")

        # Disable all current sinking first
        print("\nDisabling all channels...")
        eload.disable_all_channels()
        time.sleep(1)

        # Enable voltage source mode
        print("\nEnabling voltage source mode on channel 0...")
        eload.channel(0).set_voltage(12.0)  # Output 12V
        time.sleep(2)

        voltage = eload.channel(0).get_voltage()
        current = eload.channel(0).get_current()
        print(f"Channel 0 voltage source: {voltage:.2f}V, load current: {current:.3f}A")

        # Test different voltages
        print("\nTesting different voltage levels...")
        for test_voltage in [5.0, 12.0, 24.0]:
            eload.channel(0).set_voltage(test_voltage)
            time.sleep(1)
            measured = eload.channel(0).get_voltage()
            print(f"  Set: {test_voltage:.1f}V -> Measured: {measured:.2f}V")

        # Example 4: Voltage Monitoring (Disabled Mode)
        print("\n" + "=" * 70)
        print("Example 4: Voltage Monitoring (Disabled Mode)")
        print("=" * 70)
        print("ELoad can measure voltage when disabled (no current sink/source)")

        # Disable all modes - just measure voltage
        print("\nDisabling all modes on channel 0...")
        eload.channel(0).set_current(0.0)  # Disable current sink
        eload.channel(0).set_voltage(0.0)  # Disable voltage source
        time.sleep(1)

        print("Connect external voltage source to channel 0...")
        time.sleep(1)

        voltage = eload.channel(0).get_voltage()
        print(f"Channel 0 measured voltage (disabled): {voltage:.2f}V")

        # Example 5: Digital Output Relay Control
        print("\n" + "=" * 70)
        print("Example 5: Digital Output Relay Control")
        print("=" * 70)
        print("ELoad has 4 digital output relays (dout_1 to dout_4)")

        # Test relay control
        print("\nTesting relays...")
        for relay_id in range(4):
            print(f"\nRelay {relay_id+1} (dout_{relay_id+1}):")

            # Close relay
            print(f"  Closing relay...")
            eload.set_relay(relay_id, closed=True)
            time.sleep(1.5)

            # Check state
            state = eload.get_relay(relay_id)
            print(f"  State: {'CLOSED' if state else 'OPEN'}")

            time.sleep(1)

            # Open relay
            print(f"  Opening relay...")
            eload.set_relay(relay_id, closed=False)
            time.sleep(1.5)

            # Check state
            state = eload.get_relay(relay_id)
            print(f"  State: {'CLOSED' if state else 'OPEN'}")

        # Example 6: Power Limiting
        print("\n" + "=" * 70)
        print("Example 6: Power Limiting (Safety)")
        print("=" * 70)

        max_channel_power = 200.0  # W
        max_total_power = 600.0  # W

        print(f"\nPower limits:")
        print(f"  Per channel: {max_channel_power}W")
        print(f"  Total: {max_total_power}W")

        # Calculate safe current for 12V input
        test_voltage = 12.0  # Assume 12V input
        safe_current = max_channel_power / test_voltage

        print(f"\nFor {test_voltage}V input:")
        print(f"  Safe current per channel: {safe_current:.2f}A")
        print(f"  Max channels at full power: {int(max_total_power / max_channel_power)}")

        # Example 7: Ramp Current
        print("\n" + "=" * 70)
        print("Example 7: Current Ramping")
        print("=" * 70)

        print("\nRamping channel 0 from 0A to 5A...")
        for current in [0.0, 1.0, 2.0, 3.0, 4.0, 5.0]:
            eload.channel(0).set_current(current)
            time.sleep(1)

            measured_current = eload.channel(0).get_current()
            voltage = eload.channel(0).get_voltage()
            power = eload.channel(0).get_power()

            print(f"  Target: {current:.1f}A -> Measured: {measured_current:.2f}A, "
                  f"{voltage:.1f}V, {power:.1f}W")

        # Cleanup: Disable all channels
        print("\n" + "=" * 70)
        print("Disabling all channels...")
        eload.disable_all_channels()

        # Turn off all relays
        print("Opening all relays...")
        for relay_id in range(4):
            eload.set_relay(relay_id, closed=False)

        print("\nExample completed!")
        print("=" * 70)


if __name__ == "__main__":
    main()
