"""
Base Device class for SDRIG SDK

This module provides the base DeviceSDR class that all device types inherit from.
It handles AVTP communication, message routing, and lifecycle management.
"""

import time
import struct
import threading
from abc import ABC, abstractmethod
from typing import Optional, Dict, Callable, Any
from ..protocol.avtp_manager import AvtpCanManager
from ..protocol.can_messages import CANMessageDatabase
from ..protocol.can_protocol import extract_pgn, prepare_can_id
from ..utils.task_monitor import TaskMonitor
from ..utils.logger import get_logger
from ..types.enums import DeviceType, PGN
from ..types.structs import ModuleInfo, DeviceHealth

logger = get_logger('device_sdr')


class DeviceSDR(ABC):
    """
    Base class for all SDRIG devices

    Provides common functionality for device communication, message routing,
    and lifecycle management.
    """

    def __init__(
        self,
        mac_address: str,
        iface: str,
        stream_id: int,
        dbc_path: str
    ):
        """
        Initialize SDRIG device

        Args:
            mac_address: Device MAC address
            iface: Network interface name
            stream_id: AVTP stream ID
            dbc_path: Path to DBC file
        """
        self.mac_address = mac_address.upper()
        self.iface = iface
        self.stream_id = stream_id
        self.dbc_path = dbc_path

        # AVTP manager
        self.avtp_manager = AvtpCanManager(iface, stream_id)

        # CAN message database
        self.can_db = CANMessageDatabase(dbc_path)

        # Task monitor for periodic tasks
        self.task_monitor = TaskMonitor()

        # Module information
        self.module_info: Optional[ModuleInfo] = None

        # Device health
        self.health = DeviceHealth(
            mac_address=mac_address,
            last_seen=time.time(),
            is_active=False
        )

        # Message callbacks
        self._message_callbacks: Dict[int, Callable[[int, bytes, str], None]] = {}
        self._message_callbacks_lock = threading.RLock()

        # Running state
        self._running = False
        self._initialized = False

        logger.info(f"Device {self.device_type().value} created: {mac_address}")

    @abstractmethod
    def device_type(self) -> DeviceType:
        """
        Get device type

        Returns:
            Device type enum
        """
        pass

    @abstractmethod
    def _setup_periodic_tasks(self):
        """
        Setup device-specific periodic tasks

        Override in subclass to add periodic tasks like MODULE_INFO requests
        """
        pass

    @abstractmethod
    def _process_can_message(self, pgn: int, data: bytes, src_mac: str):
        """
        Process received CAN message

        Override in subclass to handle device-specific messages

        Args:
            pgn: Parameter Group Number
            data: Message data
            src_mac: Source MAC address
        """
        pass

    def start(self):
        """Start device data acquisition"""
        if self._running:
            logger.warning(f"Device {self.mac_address} already running")
            return

        logger.info(f"Starting device {self.mac_address}")

        # Start AVTP receiver
        self.avtp_manager.start_receiving(self._on_avtp_frame)

        # Setup periodic tasks
        self._setup_periodic_tasks()

        # Start task monitor
        self.task_monitor.start()

        self._running = True
        self.health.is_active = True

        logger.info(f"Device {self.mac_address} started")

    def stop(self):
        """Stop device data acquisition"""
        if not self._running:
            return

        logger.info(f"Stopping device {self.mac_address}")

        # Stop task monitor
        self.task_monitor.stop()

        # Stop AVTP receiver
        self.avtp_manager.stop_receiving()

        self._running = False
        self.health.is_active = False

        logger.info(f"Device {self.mac_address} stopped")

    def is_running(self) -> bool:
        """Check if device is running"""
        return self._running

    def is_alive(self) -> bool:
        """Check if device is responsive"""
        return self.health.is_alive(time.time())

    def send_can_message(
        self,
        pgn: PGN,
        data: Dict[str, Any],
        source_addr: int = 0x00,
        destination_addr: int = 0xFF,
        priority: int = 3
    ):
        """
        Send CAN message to device

        Args:
            pgn: Parameter Group Number
            data: Message data dictionary
            source_addr: Source address (default 0x00)
            priority: Message priority (default 3)
        """
        # Build CAN ID
        can_id = prepare_can_id(pgn, source_addr, destination_addr, priority)
        dnc_can_id = prepare_can_id(pgn, 0xFE, 0xFE, priority)
        # Encode message
        try:
            encoded_data = self.can_db.encode_message(dnc_can_id, data)
        except Exception as e:
            logger.error(f"Failed to encode message {pgn.name}: {e}")
            raise

        # Send via AVTP
        self.avtp_manager.send_can_message(
            can_bus_id=0,  # Internal bus
            msg_id=can_id,
            data=encoded_data,
            extended_id=True,
            can_fd=True,
            dst_mac=self.mac_address
        )

        logger.debug(f"Sent {pgn.name} to {self.mac_address}")

    def send_raw_can_message(
        self,
        can_id: int,
        data: bytes,
        extended_id: bool = True,
        can_fd: bool = True
    ):
        """
        Send raw CAN message

        Args:
            can_id: CAN message ID
            data: Raw message data
            extended_id: Use extended ID
            can_fd: Use CAN-FD
        """
        self.avtp_manager.send_can_message(
            can_bus_id=0,
            msg_id=can_id,
            data=data,
            extended_id=extended_id,
            can_fd=can_fd,
            dst_mac=self.mac_address
        )

    def request_module_info(self):
        """Request MODULE_INFO from device"""
        # Send MODULE_INFO_req to keep device awake
        # MODULE_INFO_req has 6 bit flags to request different info types:
        # - module_info_base_req (bit 0)
        # - module_info_ex_req (bit 1)
        # - module_info_pin_info_req (bit 2)
        # - module_info_can_info_req (bit 3)
        # - module_info_can_mux_req (bit 4)
        # - module_info_boot_req (bit 5)
        # All flags set to 0 = heartbeat only (no response data)
        try:
            data = {
                'module_info_base_req': 0,
                'module_info_ex_req': 0,
                'module_info_pin_info_req': 0,
                'module_info_can_info_req': 0,
                'module_info_can_mux_req': 0,
                'module_info_boot_req': 0,
            }
            self.send_can_message(PGN.MODULE_INFO_REQ, data)
            logger.debug(f"Sent MODULE_INFO_req to {self.mac_address}")
        except Exception as e:
            logger.debug(f"Failed to send module_info request: {e}")

        

    def register_message_callback(self, pgn: int, callback: Callable[[int, bytes, str], None]):
        """
        Register callback for specific PGN

        Args:
            pgn: Parameter Group Number
            callback: Callback function(pgn, data, src_mac)
        """
        with self._message_callbacks_lock:
            self._message_callbacks[pgn] = callback
            logger.debug(f"Registered callback for PGN 0x{pgn:04X}")

    def unregister_message_callback(self, pgn: int):
        """
        Unregister callback for PGN

        Args:
            pgn: Parameter Group Number
        """
        with self._message_callbacks_lock:
            if pgn in self._message_callbacks:
                del self._message_callbacks[pgn]
                logger.debug(f"Unregistered callback for PGN 0x{pgn:04X}")

    def _on_avtp_frame(self, frame: bytes):
        """
        Handle received AVTP frame

        Args:
            frame: Raw AVTP frame bytes
        """
        try:
            # Update health
            self.health.last_seen = time.time()
            self.health.message_count += 1

            # Parse AVTP frame
            self._parse_avtp_frame(frame)

        except Exception as e:
            logger.error(f"Error processing AVTP frame: {e}")
            self.health.error_count += 1

    def _parse_avtp_frame(self, frame: bytes):
        """
        Parse AVTP frame and extract CAN messages

        Args:
            frame: Raw frame bytes
        """
        # Skip Ethernet header (14 bytes) and AVTP header (12 bytes)
        offset = 26

        # Extract header fields
        if len(frame) < 26:
            return

        src_mac = frame[6:12]
        src_mac_str = ':'.join(f'{b:02X}' for b in src_mac)

        # Only process messages from our device
        if src_mac_str != self.mac_address:
            return

        # Extract AVTP fields
        avtp_subtype = frame[14]
        ethernet_type = struct.unpack('!H', frame[12:14])[0]
        data_length = ((frame[15] & 0x07) << 8) | frame[16]

        # Validate data_length doesn't exceed frame size
        if data_length > (len(frame) - 26):
            logger.warning(
                f"Invalid AVTP data_length {data_length} exceeds frame size {len(frame) - 26}, "
                f"dropping frame from {src_mac_str}"
            )
            return

        # Check for Non-Time-Synchronous Control Format
        if avtp_subtype != 0x82 or ethernet_type != 0x22F0:
            logger.debug(f"Skipping non-NTSCF AVTP frame: subtype=0x{avtp_subtype:02X}, type=0x{ethernet_type:04X}")
            return

        # Process each ACF-CAN message in the frame
        while offset < (data_length + 26) and offset + 2 <= len(frame):
            # Read ACF header
            acf_header = struct.unpack_from('!H', frame, offset)[0]
            message_length_quadlets = acf_header & 0xFF
            message_length_bytes = message_length_quadlets * 4

            if offset + message_length_bytes > len(frame):
                break

            # Extract ACF-CAN message
            acf_can_message = frame[offset:offset + message_length_bytes]
            self._parse_acf_can_message(acf_can_message, src_mac_str)

            offset += message_length_bytes

    def _parse_acf_can_message(self, message: bytes, src_mac: str):
        """
        Parse ACF-CAN message

        Args:
            message: ACF-CAN message bytes
            src_mac: Source MAC address
        """
        if len(message) < 8:
            return

        # Extract fields
        message_type = (message[0] >> 1) & 0x7F
        message_length_quadlets = ((message[0] & 0x01) << 8) | message[1]
        bus_id = message[3] & 0x1F
        frame_length = (message_length_quadlets * 4) - 8
        can_id = ((message[4] & 0x1F) << 24) | (message[5] << 16) | (message[6] << 8) | message[7]

        # Extract data
        data = message[8:8 + frame_length]

        # Extract PGN (without modifying SA/DA)
        pgn = extract_pgn(can_id)

        # ACF-CAN provides 29-bit CAN ID
        # DBC lookup will add extended bit internally if needed
        # Decode message (CAN DB will handle SA/DA normalization)
        try:
            decoded = self.can_db.decode_message(can_id, data)
            if decoded:
                # Log received message for diagnostics
                msg_name = self.can_db.get_message_name(can_id) or f"0x{pgn:04X}"
                logger.debug(f"Received CAN message: {msg_name} (PGN=0x{pgn:04X}) from {src_mac}")

                # Get callback OUTSIDE of lock to avoid deadlock
                callback = None
                with self._message_callbacks_lock:
                    callback = self._message_callbacks.get(pgn)

                # Call registered callback (outside lock)
                if callback:
                    try:
                        callback(pgn, data, src_mac)
                    except Exception as e:
                        logger.error(f"Error in callback for PGN 0x{pgn:04X}: {e}")

                # Call device-specific handler
                self._process_can_message(pgn, data, src_mac)

        except Exception as e:
            logger.debug(f"Failed to decode CAN message 0x{can_id:08X}: {e}")

    def __enter__(self):
        """Context manager entry"""
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop()
        return False

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"mac={self.mac_address}, "
            f"type={self.device_type().value}, "
            f"running={self._running})"
        )
