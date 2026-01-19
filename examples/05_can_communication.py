#!/usr/bin/env python3
"""
Example 05: CAN Communication via IfMux

This example demonstrates how to send and receive CAN messages.
Channel 0 and Channel 1 are physically connected, forming a loopback network.
Messages sent on Channel 1 will be received on Channel 2.
"""

import time
from sdrig import SDRIG, CANSpeed

# Counter for received messages
received_count = 0

def on_can_message_received(channel_id: int, can_id: int, data: bytes):
    """
    Callback function for received CAN messages

    Args:
        channel_id: CAN channel that received the message (0-7)
        can_id: CAN message ID
        data: Message data bytes
    """
    global received_count
    received_count += 1

    print(f"  <- Received on Channel {channel_id-1}: "
          f"ID=0x{can_id:08X}, Data={data.hex()}")

def main():
    """Send and receive CAN messages"""
    print("SDRIG CAN Communication Example (Loopback)")
    print("=" * 70)
    print("Note: Channel 0 and 1 are connected by wire")
    print("      Messages sent on Channel 1 will appear on Channel 2")
    print("=" * 70)

    # IfMux device MAC address (replace with your device)
    IFMUX_MAC = "66:6A:DB:B3:06:27"

    with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
        # Connect to IfMux device
        print(f"\nConnecting to IfMux device: {IFMUX_MAC}")
        ifmux = sdk.connect_ifmux(IFMUX_MAC, auto_start=True)

        # Register callback for CAN messages
        print("\nRegistering CAN message callback...")
        ifmux.register_raw_can_callback(on_can_message_received)

        # Wait for initialization
        time.sleep(2)

        # Configure CAN channels
        print("\nConfiguring CAN channels...")

        # Channel 0: 500 kbps
        ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)
        ifmux.channel(0).set_internal_relay(True) # Enable internal relay
        #ifmux.channel(0).set_external_relay(1, True)  # Connect to Channel 1 via relay matrix optional
        #ifmux.channel(0).set_external_relay(0, True)  # Connect to Channel 1 via relay matrix optional

        # Channel 1: 500 kbps
        ifmux.channel(1).set_speed(CANSpeed.SPEED_500K)
        ifmux.channel(1).set_internal_relay(True)   # Enable internal relay
        #ifmux.channel(1).set_external_relay(0, True)  # Connect to Channel 0 via relay matrix optional
        #ifmux.channel(1).set_external_relay(1, True)  # Connect to Channel 0 via relay matrix optional

        time.sleep(1)

        # Send CAN messages
        print("\nSending CAN messages on Channel 1...")
        print("(Should be received on Channel 2 due to loopback)")
        print()

        for i in range(5):
            # Standard CAN message
            can_id = 0x123
            data = bytes([0x01, 0x02, 0x03, 0x04, i, 0x00, 0x00, 0x00])

            print(f"Sent #{i+1}: ID=0x{can_id:03X}, Data={data.hex()}")

            ifmux.send_raw_can(
                channel_id=0,
                can_id=can_id,
                data=data,
                extended=False,
                fd=False
            )

            time.sleep(0.5)

        # Wait a bit for any late messages
        print("\nWaiting for messages...")
        time.sleep(1)

        # Read CAN channel status
        print("\nReading CAN channel status...")
        for ch_num in range(2):
            channel = ifmux.channel(ch_num)
            stats = channel.get_stats()

            print(f"\nChannel {ch_num}:")
            print(f"  State: {stats['state']}")
            print(f"  Speed: {channel.state.speed} bps")
            print(f"  TX Count: {stats['tx_count']}")
            print(f"  RX Count: {stats['rx_count']}")
            print(f"  Error Count: {stats['error_count']}")
            print(f"  Last Error: {stats['lec']}")

        # Summary
        print("\n" + "=" * 70)
        print(f"Summary:")
        print(f"  Messages sent: 5")
        print(f"  Messages received via callback: {received_count}")
        print(f"  Expected: 5 (due to loopback on Channel 2)")
        print("=" * 70)
        print("\nExample completed!")


if __name__ == "__main__":
    main()
