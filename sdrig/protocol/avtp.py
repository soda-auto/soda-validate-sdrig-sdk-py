"""
AVTP (Audio Video Transport Protocol) packet handling

This module provides improved AVTP packet structures based on IEEE 1722
with better typing, validation, and ACF-CAN support.
"""

from scapy.packet import Packet
from scapy.fields import (
    BitField, ByteField, XByteField, ShortField, IntField, StrFixedLenField
)
from scapy.layers.l2 import Ether
from typing import Tuple
from ..utils.logger import get_logger

logger = get_logger('avtp')

# AVTP EtherType
AVTP_ETHERTYPE = 0x22F0

# AVTP Subtypes
AVTP_SUBTYPE_NTSCF = 0x82  # Non-Time-Synchronous Control Format

# ACF Message Types
ACF_MSG_TYPE_CAN_BRIEF = 0x02


class AVTPPacket(Packet):
    """
    AVTP Packet with ACF-CAN support

    IEEE 1722 Non-Time-Synchronous Control Format with ACF-CAN Brief
    """

    name = "AVTPPacket"

    fields_desc = [
        # AVTP Common Header (12 bytes total)
        XByteField("subtype", AVTP_SUBTYPE_NTSCF),  # AVTP Subtype
        ByteField("version_cd", 0x80),  # Version (0) + Control/Data + Stream ID Valid
        ByteField("data_length", 0x00),  # Payload length in bytes
        ByteField("sequence_number", 0),  # Sequence number
        IntField("stream_id_high", 0),  # Stream ID high 32 bits
        IntField("stream_id_low", 1),  # Stream ID low 32 bits

        # ACF-CAN Message Header
        ShortField("acf_header", 0x0404),  # Message Type + Length in quadlets
        ByteField("flags", 0x08),  # Padding, MTV, RTR, EFF, BRS, FDF, ESI
        ByteField("can_id", 0x01),  # CAN Bus Identifier
        IntField("msg_id", 0),  # CAN Message ID

        # CAN Data (up to 64 bytes for CAN-FD)
        StrFixedLenField("data", b'\x00' * 64, length=64)
    ]

    def extract_padding(self, s):
        """No automatic padding extraction"""
        return "", s

    def get_stream_id(self) -> int:
        """
        Get 64-bit stream ID

        Returns:
            Stream ID as integer
        """
        return (self.stream_id_high << 32) | self.stream_id_low

    def set_stream_id(self, stream_id: int):
        """
        Set 64-bit stream ID

        Args:
            stream_id: 64-bit stream identifier
        """
        if stream_id < 0 or stream_id > 0xFFFFFFFFFFFFFFFF:
            raise ValueError(f"Stream ID must be 0-{0xFFFFFFFFFFFFFFFF}")

        self.stream_id_high = (stream_id >> 32) & 0xFFFFFFFF
        self.stream_id_low = stream_id & 0xFFFFFFFF

    def get_acf_message_type(self) -> int:
        """
        Extract ACF message type from header

        Returns:
            Message type (3 bits)
        """
        return (self.acf_header >> 9) & 0x07

    def get_acf_length_quadlets(self) -> int:
        """
        Extract ACF message length in quadlets

        Returns:
            Message length in quadlets (4-byte units)
        """
        return self.acf_header & 0x1FF

    def set_acf_header(self, msg_type: int, length_quadlets: int):
        """
        Set ACF header with message type and length

        Args:
            msg_type: Message type (0-7)
            length_quadlets: Message length in quadlets
        """
        if msg_type < 0 or msg_type > 7:
            raise ValueError(f"Message type must be 0-7, got {msg_type}")
        if length_quadlets < 0 or length_quadlets > 0x1FF:
            raise ValueError(f"Length must be 0-{0x1FF}, got {length_quadlets}")

        self.acf_header = (msg_type << 9) | (length_quadlets & 0x1FF)

    def get_padding_length(self) -> int:
        """Get padding length from flags"""
        return (self.flags >> 6) & 0x03

    def is_timestamp_valid(self) -> bool:
        """Check if message timestamp is valid (MTV flag)"""
        return bool(self.flags & 0x20)

    def is_remote_frame(self) -> bool:
        """Check if CAN remote frame (RTR flag)"""
        return bool(self.flags & 0x10)

    def is_extended_id(self) -> bool:
        """Check if CAN extended ID (EFF flag)"""
        return bool(self.flags & 0x08)

    def is_can_fd(self) -> bool:
        """Check if CAN-FD format (FDF flag)"""
        return bool(self.flags & 0x02)

    def is_bit_rate_switch(self) -> bool:
        """Check if bit rate switch (BRS flag)"""
        return bool(self.flags & 0x04)

    def set_flags(self, extended_id: bool = False, can_fd: bool = False,
                  brs: bool = False, mtv: bool = False, rtr: bool = False):
        """
        Set CAN flags

        Args:
            extended_id: Extended CAN ID (29-bit)
            can_fd: CAN-FD format
            brs: Bit rate switch
            mtv: Message timestamp valid
            rtr: Remote transmission request
        """
        self.flags = 0
        if extended_id:
            self.flags |= 0x08
        if can_fd:
            self.flags |= 0x02
        if brs:
            self.flags |= 0x04
        if mtv:
            self.flags |= 0x20
        if rtr:
            self.flags |= 0x10

    def get_can_bus_id(self) -> int:
        """Get CAN bus identifier (0-31)"""
        return self.can_id & 0x1F

    def get_payload_data(self) -> bytes:
        """
        Get actual payload data without padding

        Returns:
            Payload bytes
        """
        # Calculate actual data length from ACF header
        acf_length_bytes = self.get_acf_length_quadlets() * 4
        # ACF header itself is 2 + 1 + 1 + 4 = 8 bytes before data
        payload_length = acf_length_bytes - 8
        return bytes(self.data[:payload_length])


# Bind AVTP packet to Ethernet
from scapy.packet import bind_layers
bind_layers(Ether, AVTPPacket, type=AVTP_ETHERTYPE)


class AVTPBuilder:
    """Helper class to build AVTP packets"""

    def __init__(self, stream_id: int):
        """
        Initialize AVTP builder

        Args:
            stream_id: 64-bit stream identifier
        """
        self.stream_id = stream_id
        self.sequence_number = 0

    def build_can_packet(
        self,
        dst_mac: str,
        src_mac: str,
        can_bus_id: int,
        msg_id: int,
        data: bytes,
        extended_id: bool = True,
        can_fd: bool = True
    ) -> Ether:
        """
        Build AVTP packet with CAN message

        Args:
            dst_mac: Destination MAC address
            src_mac: Source MAC address
            can_bus_id: CAN bus identifier (0-31)
            msg_id: CAN message ID
            data: CAN payload data (up to 64 bytes)
            extended_id: Use extended CAN ID (29-bit)
            can_fd: Use CAN-FD format

        Returns:
            Complete Ethernet packet with AVTP
        """
        # Limit data to 64 bytes
        data = data[:64]
        payload_len = len(data)

        # Calculate ACF message length in quadlets
        # ACF structure: header(2) + flags(1) + can_id(1) + msg_id(4) + data
        acf_payload_length = 8 + payload_len
        quadlets = (acf_payload_length + 3) // 4  # Round up to quadlets

        # Build Ethernet frame
        pkt = Ether(dst=dst_mac, src=src_mac, type=AVTP_ETHERTYPE) / AVTPPacket()
        avtp = pkt[AVTPPacket]

        # Set AVTP header
        avtp.subtype = AVTP_SUBTYPE_NTSCF
        avtp.version_cd = 0x80  # Version 0, Stream ID valid
        avtp.sequence_number = self.sequence_number
        avtp.set_stream_id(self.stream_id)
        avtp.data_length = acf_payload_length

        # Set ACF header
        avtp.set_acf_header(ACF_MSG_TYPE_CAN_BRIEF, quadlets)

        # Set flags
        avtp.set_flags(extended_id=extended_id, can_fd=can_fd)
        avtp.can_id = can_bus_id & 0x1F
        avtp.msg_id = msg_id

        # Set data with padding
        if len(data) < 64:
            data += b'\x00' * (64 - len(data))
        avtp.data = data

        # Increment sequence number
        self.sequence_number = (self.sequence_number + 1) % 256

        return pkt

    def reset_sequence(self):
        """Reset sequence number to 0"""
        self.sequence_number = 0
