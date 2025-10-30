
from __future__ import annotations

CTRL_BUS_ID = 0
WILDCARD_SA = 0xFE  # 254 — wildcard SA in requests

def make_can_id_j1939(pgn: int, sa: int, priority: int = 6, dp: int = 0) -> int:
    """Build a 29-bit J1939 CAN ID (EFF).
    PRI(3) | DP(1) | PF(8) | PS(8) | SA(8)
    """
    pf = (pgn >> 8) & 0xFF
    ps = pgn & 0xFF
    return ((priority & 0x7) << 26) | ((dp & 0x1) << 24) | (pf << 16) | (ps << 8) | (sa & 0xFF)

def extract_pgn(can_id: int) -> int:
    return (can_id >> 8) & 0x3FFFF

def is_j1939(can_id: int) -> bool:
    return can_id > 0x7FF

def wildcard_sa(can_id: int) -> int:
    """Replace SA with 0xFE (wildcard)."""
    if not is_j1939(can_id):
        return can_id
    return (can_id & 0xFFFFFF00) | 0x000000FE
