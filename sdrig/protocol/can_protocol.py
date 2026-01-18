"""
CAN Protocol utilities

This module provides utilities for CAN/J1939 protocol handling including
PGN extraction, CAN ID manipulation, and message routing.
"""

from typing import Tuple
from ..types.enums import PGN, J1939Address


def is_j1939(can_id: int) -> bool:
    """
    Check if CAN ID follows J1939 format (extended frame)

    Args:
        can_id: CAN message ID

    Returns:
        True if J1939 format
    """
    return can_id > 0x7FF


def extract_pgn(can_id: int) -> int:
    """
    Extract Parameter Group Number from J1939 CAN ID

    For PDU1 format (destination-specific): Replace DA [15:8] with 0xFE
    For PDU2 format (broadcast): Keep GE [15:8] as-is

    Args:
        can_id: CAN message ID

    Returns:
        PGN value with 0xFE in lowest byte for PDU1 format
    """
    if is_pdu1_format(can_id):
        # PDU1: Replace DA byte with 0xFE, keep DP and PF
        return ((can_id >> 8) & 0x3FF00) | 0x000FE
    else:
        # PDU2: Keep GE byte as-is
        return (can_id >> 8) & 0x3FFFF


def is_pdu1_format(can_id: int) -> bool:
    """
    Check if CAN ID uses PDU1 format (destination specific)

    In J1939:
    - PDU Format (PF) is in bits [23:16]
    - PDU1: PF < 240 (0xF0) - PS byte contains Destination Address
    - PDU2: PF >= 240 - PS byte contains Group Extension

    Args:
        can_id: CAN message ID

    Returns:
        True if PDU1 format (destination specific)
    """
    pdu_format = (can_id >> 16) & 0xFF
    return pdu_format < 0xF0


def normalize_can_id_for_dbc(can_id: int) -> int:
    """
    Normalize CAN ID for DBC lookup

    For standard CAN (11-bit): Return as-is without modification
    For J1939/Extended (29-bit):
      - PDU1 (destination specific): Replace both DA and SA with 0xFE
      - PDU2 (broadcast): Replace only SA with 0xFE, keep Group Extension

    Args:
        can_id: Original CAN ID

    Returns:
        Normalized CAN ID for DBC lookup (extended IDs get extended frame bit)
    """
    # Check if J1939/Extended format (29-bit)
    if not is_j1939(can_id):
        # Standard CAN (11-bit): return as-is
        return can_id

    # J1939/Extended format: normalize based on PDU type
    if is_pdu1_format(can_id):
        # PDU1: Replace PS (DA) and SA with 0xFE
        # Keep Priority [28:26] and PF [23:16]
        normalized = (can_id & 0xFFFF0000) | 0xFEFE
    else:
        # PDU2: Keep PS (Group Extension), replace only SA with 0xFE
        # Keep Priority [28:26], PF [23:16], and PS [15:8]
        normalized = (can_id & 0xFFFFFF00) | 0xFE

    # Add extended frame bit [31] for DBC requirement
    return normalized | 0x80000000


def extract_source_address(can_id: int) -> int:
    """
    Extract source address from J1939 CAN ID

    Args:
        can_id: CAN message ID

    Returns:
        Source address (0-255)
    """
    return can_id & 0xFF


def extract_priority(can_id: int) -> int:
    """
    Extract priority from J1939 CAN ID

    Args:
        can_id: CAN message ID

    Returns:
        Priority (0-7)
    """
    return (can_id >> 26) & 0x07


def build_j1939_id(
    pgn: int,
    source_addr: int = J1939Address.NULL_SA,
    destination_addr: int = J1939Address.BROADCAST_DA,
    priority: int = 3
) -> int:
    """
    Build J1939 CAN ID from components

    For PDU1 format: Replace 0xFE in PGN with actual destination_addr
    For PDU2 format: Keep Group Extension from PGN, use source_addr

    Args:
        pgn: Parameter Group Number (may have 0xFE in lowest byte for PDU1)
        source_addr: Source address (default J1939Address.NULL_SA)
        destination_addr: Destination address (default J1939Address.BROADCAST_DA, used for PDU1 only)
        priority: Message priority (default 3 to match C++ ROS2 implementation)

    Returns:
        29-bit CAN ID (extended frame indicator handled separately by AVTP layer)
    """
    # Check PDU format by examining PF byte [16:8] in PGN
    pf = (pgn >> 8) & 0xFF

    if pf < 0xF0:
        # PDU1: Destination-specific
        # PGN format: (DP << 16) | (PF << 8) | 0xFE
        # Replace 0xFE with actual destination_addr
        return ((priority & 0x07) << 26) | ((pgn & 0x3FF00) << 8) | ((destination_addr & 0xFF) << 8) | (source_addr & 0xFF)
    else:
        # PDU2: Broadcast with Group Extension
        # PGN format: (DP << 16) | (PF << 8) | GE
        # Keep GE from PGN, use source_addr
        return ((priority & 0x07) << 26) | ((pgn & 0x3FFFF) << 8) | (source_addr & 0xFF) 


def prepare_can_id(
    pgn: PGN | int,
    source_addr: int = J1939Address.NULL_SA,
    destination_addr: int = J1939Address.BROADCAST_DA,
    priority: int = 3
) -> int:
    """
    Prepare CAN ID for a given PGN

    Args:
        pgn: Parameter Group Number (enum or int)
        source_addr: Source address (default J1939Address.NULL_SA)
        destination_addr: Destination address (default J1939Address.BROADCAST_DA, used for PDU1 only)
        priority: Message priority (default 3)

    Returns:
        Complete CAN ID
    """
    pgn_value = pgn.value if isinstance(pgn, PGN) else pgn
    return build_j1939_id(pgn_value, source_addr, destination_addr, priority)


def parse_can_id(can_id: int) -> Tuple[int, int, int]:
    """
    Parse J1939 CAN ID into components

    Args:
        can_id: CAN message ID

    Returns:
        Tuple of (priority, pgn, source_address)
    """
    priority = extract_priority(can_id)
    pgn = extract_pgn(can_id)
    source_addr = extract_source_address(can_id)
    return priority, pgn, source_addr


def get_dlc_from_length(data_length: int) -> int:
    """
    Get DLC code from data length (for CAN-FD)

    Args:
        data_length: Actual data length in bytes

    Returns:
        DLC code
    """
    if data_length <= 8:
        return data_length
    elif data_length <= 12:
        return 9
    elif data_length <= 16:
        return 10
    elif data_length <= 20:
        return 11
    elif data_length <= 24:
        return 12
    elif data_length <= 32:
        return 13
    elif data_length <= 48:
        return 14
    elif data_length <= 64:
        return 15
    else:
        return 15


def get_length_from_dlc(dlc: int) -> int:
    """
    Get data length from DLC code (for CAN-FD)

    Args:
        dlc: DLC code

    Returns:
        Data length in bytes
    """
    if dlc <= 8:
        return dlc
    elif dlc == 9:
        return 12
    elif dlc == 10:
        return 16
    elif dlc == 11:
        return 20
    elif dlc == 12:
        return 24
    elif dlc == 13:
        return 32
    elif dlc == 14:
        return 48
    elif dlc == 15:
        return 64
    else:
        return 8
