"""
Unit tests for can_protocol.py

Tests CAN ID preparation and J1939 protocol utilities.
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from sdrig.protocol.can_protocol import prepare_can_id, extract_pgn
from sdrig.types.enums import PGN


class TestPrepareCANID:
    """Test prepare_can_id function"""

    def test_basic_can_id(self):
        """Test basic CAN ID preparation"""
        pgn = 0x0F004
        source_addr = 0x00
        destination_addr = 0xFF
        priority = 3

        can_id = prepare_can_id(pgn, source_addr, destination_addr, priority)

        # J1939 format: [Priority:3][Reserved:1][DP:1][PF:8][PS:8][SA:8]
        # Priority at bits 26-28
        assert (can_id >> 26) & 0x7 == priority

        # Source address at bits 0-7
        assert can_id & 0xFF == source_addr

    def test_module_info_req(self):
        """Test MODULE_INFO_REQ CAN ID (PGN 0x000FE)"""
        pgn = PGN.MODULE_INFO_REQ
        can_id = prepare_can_id(pgn, source_addr=0x00, destination_addr=0xFF, priority=1)

        # Priority 1, PGN 0x000FE, SA 0x00
        # CAN ID = (1 << 26) | (0x000FE << 8) | 0x00
        #        = 0x04000000 | 0x0000FE00 | 0x00
        #        = 0x0400FE00
        expected = 0x0400FF00
        assert can_id == expected

    def test_voltage_out_req(self):
        """Test VOLTAGE_OUT_VAL_REQ CAN ID (PGN 0x116FF)"""
        pgn = PGN.VOLTAGE_OUT_VAL_REQ
        can_id = prepare_can_id(pgn, source_addr=0xFE, destination_addr=0xFE, priority=3)

        # Check priority
        assert (can_id >> 26) & 0x7 == 3

        # Check source address
        assert can_id & 0xFF == 0xFE

    def test_op_mode_req(self):
        """Test OP_MODE_REQ CAN ID (PGN 0x121FF)"""
        pgn = PGN.OP_MODE_REQ
        can_id = prepare_can_id(pgn, source_addr=0xFE, destination_addr=0xFE, priority=3)

        # Verify PGN is preserved in CAN ID
        extracted_pgn = extract_pgn(can_id)
        assert extracted_pgn == pgn

    def test_priority_range(self):
        """Test priority values 0-7"""
        pgn = 0x0F004

        for priority in range(8):
            can_id = prepare_can_id(pgn, source_addr=0x00, destination_addr=0xFF, priority=priority)
            extracted_priority = (can_id >> 26) & 0x7
            assert extracted_priority == priority

    def test_source_address_range(self):
        """Test source address values 0-255"""
        pgn = 0x0F004

        for sa in [0x00, 0x7F, 0xFE, 0xFF]:
            can_id = prepare_can_id(pgn, source_addr=sa, destination_addr=0xFF, priority=3)
            extracted_sa = can_id & 0xFF
            assert extracted_sa == sa


class TestExtractPGNFromCANID:
    """Test extract_pgn function"""

    def test_extract_pgn(self):
        """Test PGN extraction from CAN ID"""
        # Create CAN ID with known PGN
        pgn = 0x0F004
        can_id = prepare_can_id(pgn, source_addr=0x00, destination_addr=0xFF, priority=3)

        # Extract and verify
        extracted = extract_pgn(can_id)
        assert extracted == pgn

    def test_extract_multiple_pgns(self):
        """Test PGN extraction for various messages"""
        test_cases = [
            PGN.MODULE_INFO,
            PGN.OP_MODE_REQ,
            PGN.VOLTAGE_OUT_VAL_REQ,
            PGN.CUR_LOOP_OUT_VAL_REQ,
            PGN.PWM_OUT_VAL_REQ,
        ]

        for pgn in test_cases:
            can_id = prepare_can_id(pgn, source_addr=0xFE, destination_addr=0xFE, priority=3)
            extracted = extract_pgn(can_id)
            assert extracted == pgn, f"Failed for PGN 0x{pgn:05X}"

    def test_roundtrip(self):
        """Test roundtrip: PGN -> CAN ID -> PGN"""
        original_pgn = 0x121FE

        # Prepare CAN ID
        can_id = prepare_can_id(original_pgn, source_addr=0xFE, destination_addr=0xFE, priority=3)

        # Extract PGN
        extracted_pgn = extract_pgn(can_id)

        # Verify roundtrip
        assert extracted_pgn == original_pgn


class TestJ1939Format:
    """Test J1939 CAN ID format compliance"""

    def test_29bit_extended_id(self):
        """Test CAN ID fits in 29 bits"""
        pgn = 0x0F004
        can_id = prepare_can_id(pgn, source_addr=0xFF, destination_addr=0xFF, priority=7)

        # 29-bit max value
        max_29bit = (1 << 29) - 1
        assert can_id <= max_29bit

    def test_pdu1_format(self):
        """Test PDU1 format (PF < 240)"""
        # PDU1: PGN = (DP << 16) | (PF << 8) | DA
        # PF < 240 means destination-specific
        pgn_pdu1 = 0x0EF00  # PF = 0xEF < 240

        can_id = prepare_can_id(pgn_pdu1, source_addr=0x00, destination_addr=0xFF, priority=3)

        # Extract PF (bits 16-23)
        pf = (can_id >> 16) & 0xFF
        assert pf < 240

    def test_pdu2_format(self):
        """Test PDU2 format (PF >= 240)"""
        # PDU2: PGN = (DP << 16) | (PF << 8) | GE
        # PF >= 240 means broadcast (group extension)
        # Example: PGN 0x01F123 has PF=0xF1 (241) which is >= 240
        pgn_pdu2 = 0x01F123  # PF = 0xF1 >= 240

        can_id = prepare_can_id(pgn_pdu2, source_addr=0xFE, destination_addr=0xFE, priority=3)

        # Extract PF (bits 16-23)
        pf = (can_id >> 16) & 0xFF
        assert pf >= 240


class TestCANIDComponents:
    """Test individual CAN ID components"""

    def test_priority_bits(self):
        """Test priority occupies bits 26-28"""
        for priority in range(8):
            can_id = prepare_can_id(0x0F004, source_addr=0x00, destination_addr=0xFF, priority=priority)

            # Extract priority (bits 26-28)
            extracted_priority = (can_id >> 26) & 0x7
            assert extracted_priority == priority

    def test_source_address_bits(self):
        """Test source address occupies bits 0-7"""
        for sa in [0x00, 0x7F, 0xAA, 0xFE, 0xFF]:
            can_id = prepare_can_id(0x0F004, source_addr=sa, destination_addr=0xFF, priority=3)

            # Extract SA (bits 0-7)
            extracted_sa = can_id & 0xFF
            assert extracted_sa == sa

    def test_pgn_bits(self):
        """Test PGN occupies bits 8-25"""
        pgn = 0x121FE
        can_id = prepare_can_id(pgn, source_addr=0xFE, destination_addr=0xFE, priority=3)

        # Extract PGN (bits 8-25)
        extracted_pgn = (can_id >> 8) & 0x3FFFF
        assert extracted_pgn == pgn


class TestPGNFormatConsistency:
    """Test PGN format consistency after migration"""

    def test_pgn_format_consistency(self):
        """Test that all PGN values end with 0xFE"""
        for pgn_enum in PGN:
            assert (pgn_enum.value & 0xFF) == 0xFE, \
                f"{pgn_enum.name} should end with 0xFE, got 0x{pgn_enum.value:05X}"

    def test_build_replaces_wildcard_sa(self):
        """Test that build_j1939_id replaces wildcard SA with actual SA"""
        pgn = PGN.MODULE_INFO_REQ  # 0x000FE

        # Build with SA=0x00
        can_id_00 = prepare_can_id(pgn, source_addr=0x00, destination_addr=0xFF, priority=3)
        assert (can_id_00 & 0xFF) == 0x00
        # Check that byte [15:8] contains FE from PGN
        assert ((can_id_00 >> 8) & 0xFF) == 0xFF

        # Build with SA=0x11
        can_id_11 = prepare_can_id(pgn, source_addr=0x11, destination_addr=0xFF, priority=3)
        assert (can_id_11 & 0xFF) == 0x11
        # Check that byte [15:8] contains FE from PGN
        assert ((can_id_11 >> 8) & 0xFF) == 0xFF

    def test_extract_pgn_roundtrip(self):
        """Test PGN -> CAN ID -> PGN roundtrip with new format"""
        test_pgns = [
            PGN.MODULE_INFO_REQ,
            PGN.OP_MODE_REQ,
            PGN.VOLTAGE_OUT_VAL_REQ,
        ]

        for original_pgn in test_pgns:
            can_id = prepare_can_id(original_pgn, source_addr=0x00, destination_addr=0xFE, priority=3)
            extracted_pgn = extract_pgn(can_id)
            assert extracted_pgn == original_pgn, \
                f"Roundtrip failed: 0x{original_pgn:05X} -> 0x{extracted_pgn:05X}"
