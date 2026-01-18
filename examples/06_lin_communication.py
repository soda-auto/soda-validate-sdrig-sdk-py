#!/usr/bin/env python3
"""
Example 06: LIN Communication via IfMux

This example demonstrates how to configure and use LIN (Local Interconnect Network)
communication through the IfMux device.

LIN is a single-wire serial network protocol used in automotive applications.
"""

import time
from sdrig import SDRIG

def main():
    """LIN Communication Example"""
    print("SDRIG LIN Communication Example")
    print("=" * 70)

    # IfMux device MAC address (replace with your device)
    IFMUX_MAC = "66:6A:DB:B3:06:27"

    with SDRIG(iface="enp0s31f6", stream_id=1, debug=True) as sdk:
        # Connect to IfMux device with LIN enabled
        print(f"\nConnecting to IfMux device: {IFMUX_MAC}")
        print("Note: LIN support must be enabled!")

        ifmux = sdk.connect_ifmux(
            IFMUX_MAC,
            auto_start=True,
            lin_enabled=True  # Enable LIN support
        )

        # Wait for initialization
        print("\nWaiting for device to initialize...")
        time.sleep(2)

        # =====================================================================
        # Step 1: Configure LIN Frames
        # =====================================================================
        print("\n" + "=" * 70)
        print("Step 1: Configuring LIN Frames")
        print("=" * 70)

        # LIN Frame Configuration Parameters:
        # - frame_id: LIN frame ID (0-63)
        # - data_length: Data length in bytes (1-8)
        # - checksum_type: 0=classic, 1=enhanced (default)

        # Configure frame ID 0x3C (common for LIN master request)
        print("\nConfiguring LIN Frame ID 0x3C (Master Request)")
        ifmux.configure_lin_frame(
            frame_id=0x3C,
            data_length=8,
            checksum_type=1  # Enhanced checksum
        )
        time.sleep(0.5)

        # Configure frame ID 0x3D (common for LIN slave response)
        print("Configuring LIN Frame ID 0x3D (Slave Response)")
        ifmux.configure_lin_frame(
            frame_id=0x3D,
            data_length=8,
            checksum_type=1
        )
        time.sleep(0.5)

        # =====================================================================
        # Step 2: Send LIN Frames
        # =====================================================================
        print("\n" + "=" * 70)
        print("Step 2: Sending LIN Frames")
        print("=" * 70)

        # Example 1: Send diagnostic request
        print("\nSending diagnostic request (Frame ID 0x3C)...")
        diagnostic_data = bytes([0x3C, 0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06])
        ifmux.send_lin_frame(0x3C, diagnostic_data)
        print(f"  Sent: {diagnostic_data.hex()}")
        time.sleep(0.5)

        # Example 2: Send actuator control command
        print("\nSending actuator control (Frame ID 0x20)...")
        # First configure the frame
        ifmux.configure_lin_frame(frame_id=0x20, data_length=4)
        time.sleep(0.2)

        # Then send data
        actuator_data = bytes([0x20, 0xFF, 0x00, 0xAA])
        ifmux.send_lin_frame(0x20, actuator_data)
        print(f"  Sent: {actuator_data.hex()}")
        time.sleep(0.5)

        # Example 3: Multiple frame transmission
        print("\nSending multiple frames...")
        for i in range(5):
            frame_id = 0x10 + i
            # Configure each frame
            ifmux.configure_lin_frame(frame_id=frame_id, data_length=2)
            time.sleep(0.1)

            # Send frame data
            data = bytes([frame_id, i * 10])
            ifmux.send_lin_frame(frame_id, data)
            print(f"  Frame {frame_id:02X}: {data.hex()}")
            time.sleep(0.3)

        # =====================================================================
        # Step 3: Monitor LIN Traffic
        # =====================================================================
        print("\n" + "=" * 70)
        print("Step 3: Monitoring LIN Traffic")
        print("=" * 70)
        print("\nListening for LIN frames for 10 seconds...")
        print("(Received frames will appear in debug log)")

        # LIN frames are automatically received and logged by the device
        # They will appear in the _handle_lin_frame callback
        # To see them, make sure debug mode is enabled

        for i in range(10):
            time.sleep(1)
            print(f"  Monitoring... {i+1}/10s")

        # =====================================================================
        # Advanced: Custom LIN Frame Callback
        # =====================================================================
        print("\n" + "=" * 70)
        print("Advanced: Custom Frame Processing")
        print("=" * 70)

        # You can register a custom callback for processing LIN frames
        # by accessing the device's message handling system

        print("\nNote: To implement custom LIN frame processing:")
        print("1. Register a callback for PGN.LIN_FRAME_RCVD_ANS")
        print("2. Process received frames in your callback")
        print("3. Example:")
        print("""
        def on_lin_frame(pgn, data, src_mac):
            decoded = ifmux.can_db.decode_message(pgn, data)
            frame_id = decoded.get('frame_id', 0)
            frame_data = decoded.get('data', b'')
            print(f"LIN Frame {frame_id:02X}: {frame_data.hex()}")

        ifmux.register_message_callback(
            PGN.LIN_FRAME_RCVD_ANS.value,
            on_lin_frame
        )
        """)

        print("\n" + "=" * 70)
        print("LIN Communication Example Completed!")
        print("=" * 70)


def example_lin_sensor_reading():
    """
    Example: Read sensor data via LIN

    This demonstrates a common LIN use case: reading sensor values
    """
    print("\nExample: LIN Sensor Reading")
    print("=" * 70)

    with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
        ifmux = sdk.connect_ifmux("66:6A:DB:B3:06:27", auto_start=True, lin_enabled=True)
        time.sleep(2)

        # Configure sensor frame (Frame ID 0x27 - temperature sensor example)
        SENSOR_FRAME_ID = 0x27
        ifmux.configure_lin_frame(
            frame_id=SENSOR_FRAME_ID,
            data_length=2,  # 2 bytes: temperature value
            checksum_type=1
        )

        # Request sensor data (in real LIN, master sends header, slave responds)
        print(f"\nReading temperature sensor (Frame ID 0x{SENSOR_FRAME_ID:02X})...")

        # Send request (could be empty or with specific command)
        request_data = bytes([SENSOR_FRAME_ID, 0x00])
        ifmux.send_lin_frame(SENSOR_FRAME_ID, request_data)

        # Wait for response (would be handled in callback)
        time.sleep(1)

        print("Sensor data request sent. Response will be in debug log.")


def example_lin_actuator_control():
    """
    Example: Control an actuator via LIN

    This demonstrates controlling a LIN actuator (e.g., window motor, mirror)
    """
    print("\nExample: LIN Actuator Control")
    print("=" * 70)

    with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
        ifmux = sdk.connect_ifmux("66:6A:DB:B3:06:27", auto_start=True, lin_enabled=True)
        time.sleep(2)

        # Configure actuator frame (Frame ID 0x30 - window motor example)
        ACTUATOR_FRAME_ID = 0x30
        ifmux.configure_lin_frame(
            frame_id=ACTUATOR_FRAME_ID,
            data_length=3,  # Command + speed + position
            checksum_type=1
        )

        print(f"\nControlling window motor (Frame ID 0x{ACTUATOR_FRAME_ID:02X})...")

        # Move window up
        print("  Command: Move Up")
        command_data = bytes([
            ACTUATOR_FRAME_ID,
            0x01,  # Command: Move up
            0x64,  # Speed: 100
            0xFF   # Position: Maximum
        ])
        ifmux.send_lin_frame(ACTUATOR_FRAME_ID, command_data)
        time.sleep(2)

        # Stop window
        print("  Command: Stop")
        stop_data = bytes([ACTUATOR_FRAME_ID, 0x00, 0x00, 0x00])
        ifmux.send_lin_frame(ACTUATOR_FRAME_ID, stop_data)

        print("Actuator control completed.")


if __name__ == "__main__":
    # Run main example
    main()

    # Uncomment to run additional examples:
    # example_lin_sensor_reading()
    # example_lin_actuator_control()
