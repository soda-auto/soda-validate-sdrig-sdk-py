#!/usr/bin/env python3
"""
Example 01: Device Discovery

This example demonstrates how to discover SDRIG devices on the network.
"""

from sdrig import SDRIG

def main():
    """Discover all SDRIG devices on the network"""
    print("SDRIG Device Discovery Example")
    print("=" * 70)

    # Create SDK instance
    with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
        # Discover devices (will print automatically)
        print("\nDiscovering devices...")
        devices = sdk.discover_devices(timeout=3.0)

        # Access device information
        print(f"\nTotal devices found: {len(devices)}")

        for mac, info in devices.items():
            print(f"\nDevice: {mac}")
            print(f"  Name: {info.app_name}")
            print(f"  Hardware: {info.hw_name}")
            print(f"  Version: {info.version}")
            print(f"  IP: {info.ip_address}")


if __name__ == "__main__":
    main()
