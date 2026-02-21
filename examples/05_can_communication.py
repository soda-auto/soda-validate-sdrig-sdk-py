#!/usr/bin/env python3
"""
Example 05: CAN Communication via IfMux

This example demonstrates how to send and receive CAN messages in both
classic CAN and CAN FD modes.

Channel 0 and Channel 1 are physically connected, forming a loopback network.
Messages sent on one channel will be received on the other.
"""

import time
from sdrig import SDRIG, CANSpeed, CANFDSpeed

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


def example_classic_can(ifmux):
    """Classic CAN at 500 kbps"""
    global received_count
    received_count = 0

    print("\n" + "=" * 70)
    print("Part 1: Classic CAN at 500 kbps")
    print("=" * 70)

    # Configure both channels for classic CAN at 500 kbps
    ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)
    ifmux.channel(0).set_internal_relay(True)

    ifmux.channel(1).set_speed(CANSpeed.SPEED_500K)
    ifmux.channel(1).set_internal_relay(True)

    time.sleep(1)

    # Send classic CAN messages (max 8 bytes payload)
    print("\nSending classic CAN messages on Channel 0...")
    for i in range(5):
        can_id = 0x123
        data = bytes([0x01, 0x02, 0x03, 0x04, i, 0x00, 0x00, 0x00])

        print(f"  -> Sent #{i+1}: ID=0x{can_id:03X}, Data={data.hex()}")

        ifmux.send_raw_can(
            channel_id=0,
            can_id=can_id,
            data=data,
            extended=False,
            fd=False
        )
        time.sleep(0.5)

    time.sleep(1)
    print_channel_stats(ifmux, [0, 1])
    print(f"\n  Messages received via callback: {received_count}")


def example_can_fd(ifmux):
    """CAN FD with 500K arbitration / 2M data"""
    global received_count
    received_count = 0

    print("\n" + "=" * 70)
    print("Part 2: CAN FD (arbitration 500K, data 2M)")
    print("=" * 70)

    # Configure both channels for CAN FD
    # CAN FD requires BOTH arbitration speed (classic) and data speed (FD)
    ifmux.channel(0).set_speed_fd(
        data_speed=CANFDSpeed.SPEED_2M,
        arbitration_speed=CANSpeed.SPEED_500K,
    )
    ifmux.channel(0).set_internal_relay(True)

    ifmux.channel(1).set_speed_fd(
        data_speed=CANFDSpeed.SPEED_2M,
        arbitration_speed=CANSpeed.SPEED_500K,
    )
    ifmux.channel(1).set_internal_relay(True)

    time.sleep(1)

    # Send CAN FD messages (up to 64 bytes payload)
    print("\nSending CAN FD messages on Channel 0...")
    for i in range(5):
        can_id = 0x456
        # CAN FD supports payloads up to 64 bytes
        data = bytes([0xFD, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07,
                      0x08, 0x09, 0x0A, 0x0B, i, 0x00, 0x00, 0x00])

        print(f"  -> Sent #{i+1}: ID=0x{can_id:03X}, Data={data.hex()} ({len(data)} bytes)")

        ifmux.send_raw_can(
            channel_id=0,
            can_id=can_id,
            data=data,
            extended=False,
            fd=True
        )
        time.sleep(0.5)

    time.sleep(1)
    print_channel_stats(ifmux, [0, 1])
    print(f"\n  Messages received via callback: {received_count}")


def print_channel_stats(ifmux, channels):
    """Print CAN channel statistics"""
    print("\nChannel status:")
    for ch_num in channels:
        channel = ifmux.channel(ch_num)
        stats = channel.get_stats()
        print(f"  Channel {ch_num}: State={stats['state']}, "
              f"TX={stats['tx_count']}, RX={stats['rx_count']}, "
              f"Errors={stats['error_count']}, LEC={stats['lec']}")


def main():
    """Send and receive CAN messages in classic and FD modes"""
    print("SDRIG CAN Communication Example")
    print("Note: Channel 0 and 1 are connected by wire (loopback)")

    # IfMux device MAC address (replace with your device)
    IFMUX_MAC = "66:6A:DB:B3:06:27"

    with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
        # Connect to IfMux device
        print(f"\nConnecting to IfMux device: {IFMUX_MAC}")
        ifmux = sdk.connect_ifmux(IFMUX_MAC, auto_start=True)

        # Register callback for CAN messages
        ifmux.register_raw_can_callback(on_can_message_received)

        # Wait for initialization
        time.sleep(2)

        # Part 1: Classic CAN
        example_classic_can(ifmux)

        # Part 2: CAN FD
        example_can_fd(ifmux)

        print("\n" + "=" * 70)
        print("Example completed!")
        print("=" * 70)


if __name__ == "__main__":
    main()
