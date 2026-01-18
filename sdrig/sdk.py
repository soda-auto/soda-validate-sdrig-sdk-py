"""
SDRIG SDK - High-level API

This module provides the main SDK interface for working with SDRIG devices.
It offers a simple, Pythonic API with context manager support.
"""

from typing import Dict, Optional
from pathlib import Path
from .devices.device_uio import DeviceUIO
from .devices.device_eload import DeviceELoad
from .devices.device_ifmux import DeviceIfMux
from .utils.device_manager import DeviceManager
from .utils.logger import get_logger, SDRIGLogger
from .types.structs import ModuleInfo
from .types.enums import DeviceType

logger = get_logger('sdk')


class SDRIG:
    """
    Main SDK interface for SDRIG devices

    Provides high-level API for device discovery and connection with
    context manager support for proper resource management.

    Example usage:
        ```python
        with SDRIG(iface="enp0s31f6", stream_id=1) as sdk:
            devices = sdk.discover_devices()

            uio = sdk.connect_uio("82:7B:C4:B1:92:F2")
            uio.start()

            # Set voltage on pin 0
            uio.pin(0).set_voltage(12.0)

            # Read current on pin 1
            current = uio.pin(1).get_current()

            uio.stop()
        ```
    """

    def __init__(
        self,
        iface: str,
        stream_id: int,
        dbc_path: Optional[str] = None,
        debug: bool = False
    ):
        """
        Initialize SDRIG SDK

        Args:
            iface: Network interface name (e.g., "enp0s31f6")
            stream_id: AVTP stream ID
            dbc_path: Optional path to DBC file (defaults to ./soda_xil_fd.dbc)
            debug: Enable debug logging
        """
        self.iface = iface
        self.stream_id = stream_id

        # Default DBC path
        if dbc_path is None:
            dbc_path = str(Path(__file__).parent.parent / "soda_xil_fd.dbc")
        self.dbc_path = dbc_path

        # Enable debug mode if requested
        if debug:
            SDRIGLogger.enable_debug_mode()

        # Device manager
        self.device_manager = DeviceManager(iface, stream_id, dbc_path)

        # Connected devices
        self._connected_devices: Dict[str, object] = {}

        logger.info(
            f"SDRIG SDK initialized: iface={iface}, stream_id={stream_id}, "
            f"dbc={dbc_path}"
        )

    def discover_devices(self, timeout: float = 3.0, print_devices: bool = True) -> Dict[str, ModuleInfo]:
        """
        Discover all SDRIG devices on the network

        Args:
            timeout: Discovery timeout in seconds
            print_devices: Print discovered devices to console

        Returns:
            Dictionary of MAC address -> ModuleInfo
        """
        logger.info("Starting device discovery...")
        devices = self.device_manager.discover_devices(timeout)

        if print_devices:
            self.device_manager.print_devices()

        return devices

    def connect_uio(self, mac_address: str, auto_start: bool = False) -> DeviceUIO:
        """
        Connect to UIO device

        Args:
            mac_address: Device MAC address
            auto_start: Automatically start device

        Returns:
            DeviceUIO instance
        """
        mac = mac_address.upper()

        if mac in self._connected_devices:
            logger.warning(f"Device {mac} already connected")
            return self._connected_devices[mac]

        device = DeviceUIO(mac, self.iface, self.stream_id, self.dbc_path)
        self._connected_devices[mac] = device

        if auto_start:
            device.start()

        logger.info(f"Connected to UIO device: {mac}")
        return device

    def connect_eload(self, mac_address: str, auto_start: bool = False) -> DeviceELoad:
        """
        Connect to ELoad device

        Args:
            mac_address: Device MAC address
            auto_start: Automatically start device

        Returns:
            DeviceELoad instance
        """
        mac = mac_address.upper()

        if mac in self._connected_devices:
            logger.warning(f"Device {mac} already connected")
            return self._connected_devices[mac]

        device = DeviceELoad(mac, self.iface, self.stream_id, self.dbc_path)
        self._connected_devices[mac] = device

        if auto_start:
            device.start()

        logger.info(f"Connected to ELoad device: {mac}")
        return device

    def connect_ifmux(
        self,
        mac_address: str,
        auto_start: bool = False,
        lin_enabled: bool = False
    ) -> DeviceIfMux:
        """
        Connect to IfMux device

        Args:
            mac_address: Device MAC address
            auto_start: Automatically start device
            lin_enabled: Enable LIN support

        Returns:
            DeviceIfMux instance
        """
        mac = mac_address.upper()

        if mac in self._connected_devices:
            logger.warning(f"Device {mac} already connected")
            return self._connected_devices[mac]

        device = DeviceIfMux(mac, self.iface, self.stream_id, self.dbc_path, lin_enabled)
        self._connected_devices[mac] = device

        if auto_start:
            device.start()

        logger.info(f"Connected to IfMux device: {mac}")
        return device

    def disconnect(self, mac_address: str):
        """
        Disconnect from device

        Args:
            mac_address: Device MAC address
        """
        mac = mac_address.upper()

        if mac not in self._connected_devices:
            logger.warning(f"Device {mac} not connected")
            return

        device = self._connected_devices[mac]

        # Stop device if running
        if hasattr(device, 'stop'):
            device.stop()

        del self._connected_devices[mac]
        logger.info(f"Disconnected from device: {mac}")

    def disconnect_all(self):
        """Disconnect from all devices"""
        for mac in list(self._connected_devices.keys()):
            self.disconnect(mac)

    def get_connected_devices(self) -> Dict[str, object]:
        """
        Get all connected devices

        Returns:
            Dictionary of MAC address -> device instance
        """
        return self._connected_devices.copy()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - cleanup all devices"""
        logger.info("Cleaning up SDRIG SDK")
        self.disconnect_all()
        return False

    def __repr__(self) -> str:
        return (
            f"SDRIG(iface={self.iface}, stream_id={self.stream_id}, "
            f"devices={len(self._connected_devices)})"
        )


# Convenience function for quick device discovery
def discover(
    iface: str = "enp0s31f6",
    stream_id: int = 1,
    dbc_path: Optional[str] = None,
    timeout: float = 3.0
) -> Dict[str, ModuleInfo]:
    """
    Quick device discovery

    Args:
        iface: Network interface name
        stream_id: AVTP stream ID
        dbc_path: Optional path to DBC file
        timeout: Discovery timeout

    Returns:
        Dictionary of discovered devices
    """
    with SDRIG(iface, stream_id, dbc_path) as sdk:
        return sdk.discover_devices(timeout)
