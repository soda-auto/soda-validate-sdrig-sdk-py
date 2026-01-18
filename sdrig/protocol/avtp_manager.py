"""
AVTP CAN Manager for sending and receiving AVTP messages

This module provides a high-level interface for AVTP communication
with threading support and message routing.
"""

import threading
import os
from pathlib import Path
from typing import Callable, Optional
from scapy.all import sendp, sniff, get_if_hwaddr
from scapy.config import conf
from .avtp import AVTPBuilder, AVTPPacket, AVTP_ETHERTYPE
from ..utils.logger import get_logger

logger = get_logger('avtp_manager')


class AvtpCanManager:
    """
    Manager for AVTP CAN communication

    Handles sending and receiving AVTP packets over Ethernet with
    proper MAC address resolution and threading.
    """

    def __init__(self, iface: str, stream_id: Optional[int] = None):
        """
        Initialize AVTP CAN manager

        Args:
            iface: Network interface name (e.g., "enp0s31f6")
            stream_id: Optional 64-bit stream ID for filtering
        """
        self.iface = iface
        self.stream_id = stream_id
        self.running = False
        self.recv_thread: Optional[threading.Thread] = None
        self.recv_callback: Optional[Callable[[bytes], None]] = None
        self.filter_stream_id = True  # Default: filter by stream_id
        self.src_mac = self._resolve_src_mac()

        # Create AVTP builder if stream_id provided
        self.builder = AVTPBuilder(stream_id) if stream_id else None

        logger.info(f"AVTP Manager initialized on {iface} with MAC {self.src_mac}")
        if stream_id:
            logger.info(f"Stream ID: {stream_id}")

    def _read_sys_mac(self, iface: str) -> Optional[str]:
        """
        Read MAC address from /sys/class/net

        Args:
            iface: Interface name

        Returns:
            MAC address or None
        """
        path = Path(f"/sys/class/net/{iface}/address")
        try:
            if path.exists():
                mac = path.read_text().strip()
                if mac and not mac.startswith("00:00:00"):
                    return mac
        except Exception as e:
            logger.debug(f"Failed to read MAC from {path}: {e}")
        return None

    def _resolve_src_mac(self) -> str:
        """
        Resolve source MAC address for the interface

        Returns:
            MAC address string

        Raises:
            RuntimeError: If MAC cannot be resolved
        """
        mac = None

        # Try scapy first
        try:
            mac = get_if_hwaddr(self.iface)
        except Exception as e:
            logger.debug(f"Scapy MAC resolution failed: {e}")
            mac = None

        # If invalid or null MAC, try /sys
        if not mac or mac.startswith("00:00:00"):
            mac = self._read_sys_mac(self.iface)

        # If VLAN interface, try parent interface
        if (not mac or mac.startswith("00:00:00")) and "." in self.iface:
            parent = self.iface.split(".", 1)[0]
            mac = self._read_sys_mac(parent)
            if not mac:
                try:
                    mac = get_if_hwaddr(parent)
                except Exception:
                    pass

        # Validate final MAC
        if not mac or mac.startswith("00:00:00"):
            raise RuntimeError(
                f"Cannot determine valid MAC for {self.iface}. "
                f"Mount /sys/class/net into container (ro) or run on host."
            )

        return mac

    def send_can_message(
        self,
        can_bus_id: int,
        msg_id: int,
        data: bytes,
        extended_id: bool = True,
        can_fd: bool = True,
        dst_mac: str = "FF:FF:FF:FF:FF:FF"
    ):
        """
        Send CAN message via AVTP

        Args:
            can_bus_id: CAN bus identifier (0-31)
            msg_id: CAN message ID
            data: Message payload
            extended_id: Use extended CAN ID (29-bit)
            can_fd: Use CAN-FD format
            dst_mac: Destination MAC address (default: broadcast)
        """
        if not self.builder:
            raise RuntimeError("Cannot send without stream_id")

        # Build packet
        pkt = self.builder.build_can_packet(
            dst_mac=dst_mac,
            src_mac=self.src_mac,
            can_bus_id=can_bus_id,
            msg_id=msg_id,
            data=data,
            extended_id=extended_id,
            can_fd=can_fd
        )

        # Send packet
        sendp(pkt, iface=self.iface, verbose=False)
        logger.debug(
            f"Sent CAN message: bus={can_bus_id}, id=0x{msg_id:X}, "
            f"len={len(data)}, ext={extended_id}, fd={can_fd}"
        )

    def start_receiving(self, callback: Callable[[bytes], None], filter_stream_id: bool = True):
        """
        Start receiving AVTP messages in background thread

        Args:
            callback: Function to call with received packets (raw bytes)
            filter_stream_id: If True, only accept packets with matching stream_id (default: True)
                             Set to False for device discovery to accept all stream IDs
        """
        if self.running:
            logger.warning("Receiver already running")
            return

        self.recv_callback = callback
        self.filter_stream_id = filter_stream_id
        self.running = True
        self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.recv_thread.start()
        logger.info(f"AVTP receiver started (stream_id filter: {filter_stream_id})")

    def stop_receiving(self):
        """Stop receiving AVTP messages"""
        if not self.running:
            return

        self.running = False
        if self.recv_thread:
            self.recv_thread.join(timeout=5.0)
            if self.recv_thread.is_alive():
                logger.warning("Receiver thread did not stop gracefully")
            else:
                logger.info("AVTP receiver stopped")
        self.recv_thread = None

    def _recv_loop(self):
        """Background thread for receiving packets"""
        conf.use_pcap = False

        def process(pkt):
            try:
                # Check if AVTP packet
                if AVTPPacket not in pkt:
                    logger.debug("Received non-AVTP packet")
                    return

                logger.debug(f"Received AVTP packet: filter_enabled={self.filter_stream_id}")

                # Filter by stream ID if configured and filtering enabled
                if self.stream_id is not None and self.filter_stream_id:
                    try:
                        pkt_stream_id = pkt[AVTPPacket].get_stream_id()
                        logger.debug(f"Stream ID check: packet={pkt_stream_id}, expected={self.stream_id}")
                        if pkt_stream_id != self.stream_id:
                            logger.debug(f"Dropping packet: stream_id mismatch")
                            return
                    except Exception as e:
                        logger.debug(f"Error checking stream_id: {e}")
                        return

                logger.debug("Calling recv_callback with packet")
                # Call user callback with raw packet bytes
                if self.recv_callback:
                    self.recv_callback(bytes(pkt))
                else:
                    logger.warning("recv_callback is None!")

            except Exception as e:
                # Never crash from a single bad frame
                logger.error(f"Error processing packet: {e}", exc_info=True)

        # Sniff packets
        try:
            sniff(
                iface=self.iface,
                prn=process,
                store=0,
                stop_filter=lambda x: not self.running,
                filter=f"ether proto 0x{AVTP_ETHERTYPE:04X}"
            )
        except Exception as e:
            logger.error(f"Sniffing error: {e}")
            self.running = False

    def is_running(self) -> bool:
        """Check if receiver is running"""
        return self.running

    def reset_sequence(self):
        """Reset sequence number counter"""
        if self.builder:
            self.builder.reset_sequence()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.stop_receiving()
        return False
