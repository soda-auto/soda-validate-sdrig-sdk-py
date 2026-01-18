"""
Device Manager for discovery and management

This module provides utilities for discovering SDRIG devices on the network
and managing their lifecycle.
"""

import time
from typing import Dict, List, Optional
from ..protocol.avtp_manager import AvtpCanManager
from ..protocol.can_messages import CANMessageDatabase, ModuleInfoMessage, ModuleInfoExMessage
from ..protocol.can_protocol import extract_pgn, normalize_can_id_for_dbc
from ..types.enums import PGN, DeviceType
from ..types.structs import ModuleInfo
from ..utils.logger import get_logger
import struct

logger = get_logger('device_manager')


class DeviceManager:
    """
    Manager for device discovery and monitoring

    Handles discovery of all SDRIG devices on the network and provides
    information about available devices.
    """

    def __init__(self, iface: str, stream_id: int, dbc_path: str):
        """
        Initialize device manager

        Args:
            iface: Network interface name
            stream_id: AVTP stream ID
            dbc_path: Path to DBC file
        """
        self.iface = iface
        self.stream_id = stream_id
        self.dbc_path = dbc_path

        # AVTP manager for discovery
        self.avtp_manager = AvtpCanManager(iface, stream_id)

        # CAN database
        self.can_db = CANMessageDatabase(dbc_path)

        # Discovered devices
        self.devices: Dict[str, ModuleInfo] = {}

        logger.info(f"Device Manager initialized on {iface}")

    def discover_devices(self, timeout: float = 3.0) -> Dict[str, ModuleInfo]:
        """
        Discover all devices on the network

        Args:
            timeout: Discovery timeout in seconds

        Returns:
            Dictionary of MAC address -> ModuleInfo
        """
        logger.info(f"Starting device discovery (timeout={timeout}s)")
        logger.info(f"Using interface: {self.iface}, stream_id: {self.stream_id}")

        # Clear previous devices
        self.devices.clear()

        # Start receiving (disable stream_id filter to accept responses from all devices)
        logger.info("Starting AVTP receiver with filter_stream_id=False")
        self.avtp_manager.start_receiving(self._on_discovery_frame, filter_stream_id=False)
        logger.info(f"AVTP receiver running: {self.avtp_manager.is_running()}")

        # Send discovery request (broadcast MODULE_INFO request)
        discovery_msg_id = 0x0400FF00  # OP_MODE_REQ broadcast
        discovery_data = bytes([0x1F, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])

        # Send multiple requests
        for _ in range(3):
            self.avtp_manager.send_can_message(
                can_bus_id=0,
                msg_id=discovery_msg_id,
                data=discovery_data,
                extended_id=True,
                can_fd=False,
                dst_mac="FF:FF:FF:FF:FF:FF"
            )
            time.sleep(0.05)

        # Wait for responses
        start_time = time.time()
        while (time.time() - start_time) < timeout:
            time.sleep(0.1)

        # Stop receiving
        self.avtp_manager.stop_receiving()

        logger.info(f"Discovery complete: Found {len(self.devices)} devices")
        return self.devices.copy()

    def _on_discovery_frame(self, frame: bytes):
        """
        Handle received frame during discovery

        Args:
            frame: Raw AVTP frame bytes
        """
        logger.debug(f"Discovery callback invoked: frame_len={len(frame)}")
        try:
            self._parse_avtp_frame(frame)
        except Exception as e:
            logger.error(f"Error parsing discovery frame: {e}", exc_info=True)

    def _parse_avtp_frame(self, frame: bytes):
        """
        Parse AVTP frame and extract device information

        Args:
            frame: Raw frame bytes
        """
        # Skip Ethernet header (14 bytes) and AVTP header (12 bytes)
        offset = 26

        # Extract header fields
        if len(frame) < 26:
            logger.debug(f"Frame too short: {len(frame)} < 26")
            return

        src_mac = frame[6:12]
        src_mac_str = ':'.join(f'{b:02X}' for b in src_mac)

        # Extract AVTP fields
        avtp_subtype = frame[14]
        ethernet_type = struct.unpack('!H', frame[12:14])[0]
        data_length = ((frame[15] & 0x07) << 8) | frame[16]

        logger.debug(
            f"Frame from {src_mac_str}: eth_type=0x{ethernet_type:04X}, "
            f"subtype=0x{avtp_subtype:02X}, data_len={data_length}, frame_len={len(frame)}"
        )

        # Validate data_length doesn't exceed frame size (BUGFIX: same as device_sdr.py)
        if data_length > (len(frame) - 26):
            logger.debug(
                f"Invalid AVTP data_length {data_length} exceeds frame size {len(frame) - 26}, "
                f"dropping frame from {src_mac_str}"
            )
            return

        # Check for Non-Time-Synchronous Control Format
        if avtp_subtype != 0x82 or ethernet_type != 0x22F0:
            logger.debug(f"Skipping non-NTSCF frame: subtype=0x{avtp_subtype:02X}, eth_type=0x{ethernet_type:04X}")
            return

        logger.debug(f"Processing NTSCF frame from {src_mac_str}, data_length={data_length}")

        # Temporarily INFO for debugging discovery issues
        # logger.debug(f"Processing AVTP frame from {src_mac_str}, data_length={data_length}")

        # Process each ACF-CAN message in the frame
        message_count = 0
        while offset < (data_length + 26) and offset + 2 <= len(frame):
            # Read ACF header
            acf_header = struct.unpack_from('!H', frame, offset)[0]
            message_length_quadlets = acf_header & 0xFF
            message_length_bytes = message_length_quadlets * 4

            if offset + message_length_bytes > len(frame):
                logger.debug(f"ACF message exceeds frame: offset={offset}, msg_len={message_length_bytes}, frame_len={len(frame)}")
                break

            # Extract ACF-CAN message
            message_count += 1
            logger.debug(f"Extracting ACF message #{message_count}: offset={offset}, len={message_length_bytes}")
            acf_can_message = frame[offset:offset + message_length_bytes]
            self._parse_acf_can_message(acf_can_message, src_mac_str)

            offset += message_length_bytes

        logger.debug(f"Processed {message_count} ACF messages from frame")

    def _parse_acf_can_message(self, message: bytes, src_mac: str):
        """
        Parse ACF-CAN message and extract device info

        Args:
            message: ACF-CAN message bytes
            src_mac: Source MAC address
        """
        if len(message) < 8:
            return

        # Extract fields
        frame_length_quadlets = ((message[0] & 0x01) << 8) | message[1]
        frame_length = (frame_length_quadlets * 4) - 8
        can_id = ((message[4] & 0x1F) << 24) | (message[5] << 16) | (message[6] << 8) | message[7]

        # Normalize CAN ID for DBC lookup (handles PDU1/PDU2)
        can_id = normalize_can_id_for_dbc(can_id)

        # Extract data
        data = message[8:8 + frame_length]

        # Extract PGN
        pgn = extract_pgn(can_id)

        # Decode message
        try:
            logger.debug(f"Attempting decode: CAN ID 0x{can_id:08X}, PGN=0x{pgn:04X}, data_len={len(data)}, src={src_mac}")
            decoded = self.can_db.decode_message(can_id, data)
            if not decoded:
                logger.debug(f"decode_message returned None/empty for CAN ID 0x{can_id:08X}")
                return

            logger.debug(f"Successfully decoded PGN 0x{pgn:04X} from {src_mac}: {list(decoded.keys())}")

            # Handle MODULE_INFO messages
            if pgn == PGN.MODULE_INFO.value:
                if src_mac not in self.devices:
                    self.devices[src_mac] = ModuleInfo(mac_address=src_mac)

                msg_info = ModuleInfoMessage.from_decoded(decoded, src_mac)
                module_info = self.devices[src_mac]
                module_info.app_name = msg_info.app_name
                module_info.hw_name = msg_info.hw_name
                module_info.version = msg_info.version
                module_info.build_date = msg_info.build_date
                module_info.crc = f"{msg_info.crc:08X}"
                module_info.raw_data.update(decoded)

                logger.debug(f"Found device: {src_mac} - {msg_info.app_name}")

            elif pgn == PGN.MODULE_INFO_EX.value:
                if src_mac not in self.devices:
                    self.devices[src_mac] = ModuleInfo(mac_address=src_mac)

                msg_info_ex = ModuleInfoExMessage.from_decoded(decoded, src_mac)
                module_info = self.devices[src_mac]
                module_info.ip_address = msg_info_ex.ip_address
                module_info.chip_uid = msg_info_ex.chip_uid
                module_info.raw_data.update(decoded)

                logger.debug(f"Device {src_mac} IP: {msg_info_ex.ip_address}")

        except Exception as e:
            logger.debug(f"Failed to decode CAN message 0x{can_id:08X}: {e}")

    def get_device_type(self, module_info: ModuleInfo) -> DeviceType:
        """
        Determine device type from module info

        Args:
            module_info: Module information

        Returns:
            Device type
        """
        app_name = module_info.app_name.upper()

        if "UIO" in app_name or "UNIVERSAL" in app_name:
            return DeviceType.UIO
        elif "ELOAD" in app_name or "LOAD" in app_name:
            return DeviceType.ELOAD
        elif "IFMUX" in app_name or "MUX" in app_name:
            return DeviceType.IFMUX
        else:
            return DeviceType.UNKNOWN

    def print_devices(self):
        """Print discovered devices to console"""
        print(f"\nDiscovered Devices: {len(self.devices)}")
        print("=" * 70)

        for mac, info in self.devices.items():
            device_type = self.get_device_type(info)
            print(f"\nDevice Type   : {device_type.value}")
            print(f"Device Name   : {info.app_name}")
            print(f"Hardware      : {info.hw_name}")
            print(f"Version       : {info.version}")
            print(f"Build Date    : {info.build_date}")
            print(f"CRC           : {info.crc}")
            print(f"MAC Address   : {mac}")
            if info.ip_address:
                print(f"IP Address    : {info.ip_address}")
            if info.chip_uid:
                print(f"Chip UID      : {info.chip_uid}")
            print("-" * 70)
