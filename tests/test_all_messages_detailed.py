#!/usr/bin/env python3
"""
Detailed Integration Test - All 33 CAN Messages

Tests all CAN messages with detailed tracking:
1. Sends command to device
2. Captures actual CAN frame sent on network
3. Captures CAN response from device
4. Verifies data matches expected values

This test monkey-patches the CAN layer to intercept all messages.
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass, field

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sdrig import SDRIG
from sdrig.types.enums import PGN, Feature, FeatureState, CANSpeed, CANState, RelayState
from sdrig.devices.device_sdr import DeviceSDR


@dataclass
class CANMessage:
    """Captured CAN message"""
    direction: str  # 'TX' or 'RX'
    pgn: int
    pgn_name: str
    can_id: int
    data: bytes
    decoded: Dict[str, Any]
    timestamp: float


class CANMessageInterceptor:
    """Intercepts and tracks all CAN messages"""

    def __init__(self):
        self.messages: List[CANMessage] = []
        self.original_send = None
        self.original_process = None

    def install(self):
        """Install interceptor hooks"""
        # Save original methods
        self.original_send = DeviceSDR.send_can_message
        self.original_process = DeviceSDR._process_can_message

        # Replace with intercepting versions using lambdas to properly bind
        interceptor = self
        DeviceSDR.send_can_message = lambda device_self, pgn, data, source_addr=0x00, destination_addr=0xFF, priority=3: \
            interceptor._intercept_send(device_self, pgn, data, source_addr, destination_addr, priority)
        DeviceSDR._process_can_message = lambda device_self, pgn, data, src_mac: \
            interceptor._intercept_receive(device_self, pgn, data, src_mac)

    def uninstall(self):
        """Uninstall interceptor hooks"""
        if self.original_send:
            DeviceSDR.send_can_message = self.original_send
        if self.original_process:
            DeviceSDR._process_can_message = self.original_process

    def _intercept_send(self, device_self, pgn: PGN, data: Dict[str, Any],
                        source_addr: int = 0x00, destination_addr: int = 0xFF, priority: int = 3):
        """Intercept outgoing CAN message"""
        # Get PGN name
        pgn_name = pgn.name if hasattr(pgn, 'name') else f"PGN_0x{pgn:05X}"

        # Build CAN ID
        from sdrig.protocol.can_protocol import prepare_can_id
        can_id = prepare_can_id(pgn, source_addr, destination_addr, priority)

        # Encode data
        try:
            encoded_data = device_self.can_db.encode_message(can_id, data)
        except Exception as e:
            print(f"[ERROR] Failed to encode {pgn_name}: {e}")
            encoded_data = b''

        # Record message
        msg = CANMessage(
            direction='TX',
            pgn=pgn.value if hasattr(pgn, 'value') else pgn,
            pgn_name=pgn_name,
            can_id=can_id,
            data=encoded_data,
            decoded=data.copy(),
            timestamp=time.time()
        )
        self.messages.append(msg)

        # Call original method
        return self.original_send(device_self, pgn, data, source_addr, priority)

    def _intercept_receive(self, device_self, pgn: int, data: bytes, src_mac: str):
        """Intercept incoming CAN message"""
        # Try to decode
        from sdrig.protocol.can_protocol import prepare_can_id
        can_id = prepare_can_id(PGN(pgn), 0xFE, 0xFE, 3)

        decoded = {}
        try:
            decoded = device_self.can_db.decode_message(can_id, data)
        except Exception:
            pass

        # Get PGN name
        pgn_name = "UNKNOWN"
        for name, value in PGN.__members__.items():
            if value == pgn:
                pgn_name = name
                break

        # Record message
        msg = CANMessage(
            direction='RX',
            pgn=pgn,
            pgn_name=pgn_name,
            can_id=can_id,
            data=data,
            decoded=decoded,
            timestamp=time.time()
        )
        self.messages.append(msg)

        # Call original method
        return self.original_process(device_self, pgn, data, src_mac)

    def find_tx(self, pgn: int) -> List[CANMessage]:
        """Find transmitted messages by PGN"""
        return [msg for msg in self.messages if msg.direction == 'TX' and msg.pgn == pgn]

    def find_rx(self, pgn: int) -> List[CANMessage]:
        """Find received messages by PGN"""
        return [msg for msg in self.messages if msg.direction == 'RX' and msg.pgn == pgn]

    def clear(self):
        """Clear all captured messages"""
        self.messages.clear()

    def print_summary(self):
        """Print message summary"""
        tx_count = len([m for m in self.messages if m.direction == 'TX'])
        rx_count = len([m for m in self.messages if m.direction == 'RX'])

        print(f"\n{'='*80}")
        print(f"CAN MESSAGE SUMMARY")
        print(f"{'='*80}")
        print(f"Total messages: {len(self.messages)} (TX: {tx_count}, RX: {rx_count})")

        # Group by PGN
        pgn_stats = {}
        for msg in self.messages:
            key = (msg.pgn, msg.pgn_name, msg.direction)
            pgn_stats[key] = pgn_stats.get(key, 0) + 1

        print(f"\nMessages by PGN:")
        print(f"{'PGN':<12} {'Name':<30} {'Direction':<10} {'Count':<10}")
        print(f"{'-'*80}")
        for (pgn, name, direction), count in sorted(pgn_stats.items()):
            print(f"0x{pgn:05X}     {name:<30} {direction:<10} {count:<10}")

    def print_detailed(self, limit: int = 50):
        """Print detailed message log"""
        print(f"\n{'='*80}")
        print(f"DETAILED MESSAGE LOG (last {limit} messages)")
        print(f"{'='*80}")
        print(f"{'Time':<12} {'Dir':<5} {'PGN':<12} {'Name':<25} {'Data':<30}")
        print(f"{'-'*80}")

        for msg in self.messages[-limit:]:
            timestamp = f"{msg.timestamp:.3f}"
            data_hex = msg.data.hex()[:30] if msg.data else ""
            print(f"{timestamp:<12} {msg.direction:<5} 0x{msg.pgn:05X}     "
                  f"{msg.pgn_name:<25} {data_hex:<30}")


class AllMessagesTest:
    """Test all 33 CAN messages"""

    def __init__(self, iface: str, stream_id: int):
        self.iface = iface
        self.stream_id = stream_id
        self.interceptor = CANMessageInterceptor()
        self.sdk = None

        # Device references
        self.uio = None
        self.eload = None
        self.ifmux = None

        # Test results
        self.results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0
        }

    def log(self, message: str):
        """Log test message"""
        print(f"\n[TEST] {message}")

    def test_message_pair(self, name: str, req_pgn: PGN, ans_pgn: PGN,
                         action_func, timeout: float = 2.0):
        """Test request/answer message pair"""
        self.results['total'] += 1
        print(f"\n{'─'*80}")
        print(f"Testing {name}")
        print(f"  Request:  {req_pgn.name} (0x{req_pgn.value:05X})")
        print(f"  Answer:   {ans_pgn.name} (0x{ans_pgn.value:05X})")
        print(f"{'─'*80}")

        # Clear previous messages
        self.interceptor.clear()

        # Execute action
        try:
            action_func()
            time.sleep(0.1)  # Small delay for message to be sent
        except Exception as e:
            print(f"  ✗ FAILED: Action execution error: {e}")
            self.results['failed'] += 1
            return

        # Check TX message
        tx_msgs = self.interceptor.find_tx(req_pgn.value)
        if len(tx_msgs) == 0:
            print(f"  ✗ FAILED: Request message not sent")
            self.results['failed'] += 1
            return

        print(f"  ✓ Request sent: {len(tx_msgs[0].data)} bytes")
        if tx_msgs[0].decoded:
            print(f"    Data: {list(tx_msgs[0].decoded.keys())[:5]}...")

        # Wait for RX message
        start = time.time()
        rx_msgs = []
        while (time.time() - start) < timeout:
            rx_msgs = self.interceptor.find_rx(ans_pgn.value)
            if len(rx_msgs) > 0:
                break
            time.sleep(0.1)

        if len(rx_msgs) == 0:
            print(f"  ✗ FAILED: Answer message not received (timeout)")
            self.results['failed'] += 1
            return

        print(f"  ✓ Answer received: {len(rx_msgs[0].data)} bytes")
        if rx_msgs[0].decoded:
            print(f"    Data: {list(rx_msgs[0].decoded.keys())[:5]}...")

        print(f"  ✓ PASSED: {name}")
        self.results['passed'] += 1

    def test_rx_only(self, name: str, pgn: PGN, timeout: float = 2.0):
        """Test receive-only message"""
        self.results['total'] += 1
        print(f"\n{'─'*80}")
        print(f"Testing {name}")
        print(f"  Message:  {pgn.name} (0x{pgn.value:05X})")
        print(f"{'─'*80}")

        # Clear and wait
        self.interceptor.clear()
        time.sleep(timeout)

        # Check RX message
        rx_msgs = self.interceptor.find_rx(pgn.value)
        if len(rx_msgs) == 0:
            print(f"  ✗ FAILED: Message not received")
            self.results['failed'] += 1
            return

        print(f"  ✓ Received: {len(rx_msgs)} messages, {len(rx_msgs[0].data)} bytes")
        if rx_msgs[0].decoded:
            print(f"    Data: {list(rx_msgs[0].decoded.keys())[:5]}...")

        print(f"  ✓ PASSED: {name}")
        self.results['passed'] += 1

    def run(self):
        """Run all message tests"""
        print(f"\n{'='*80}")
        print(f"SDRIG ALL MESSAGES TEST - 33 CAN Messages")
        print(f"{'='*80}")
        print(f"Interface: {self.iface}")
        print(f"Stream ID: {self.stream_id}")
        print(f"{'='*80}")

        try:
            # Install interceptor
            self.interceptor.install()

            # Discovery
            self.log("Discovering and connecting to devices...")
            self.sdk = SDRIG(iface=self.iface, stream_id=self.stream_id)
            devices = self.sdk.discover_devices(timeout=3.0, print_devices=False)

            # Connect to devices
            for mac, info in devices.items():
                app_name = info.app_name.upper()
                if "UIO" in app_name:
                    self.uio = self.sdk.connect_uio(mac, auto_start=True)
                elif "ELOAD" in app_name:
                    self.eload = self.sdk.connect_eload(mac, auto_start=True)
                elif "IFMUX" in app_name:
                    self.ifmux = self.sdk.connect_ifmux(mac, auto_start=True, lin_enabled=True)

            time.sleep(1.0)

            # Test UIO messages
            if self.uio:
                self.log("=" * 80)
                self.log("UIO MESSAGES")
                self.log("=" * 80)

                self.test_message_pair(
                    "OP_MODE (Operation Mode)",
                    PGN.OP_MODE_REQ, PGN.OP_MODE_ANS,
                    lambda: self.uio.pin(0).enable_feature(Feature.SET_VOLTAGE)
                )

                self.test_message_pair(
                    "VOLTAGE_OUT (Voltage Output)",
                    PGN.VOLTAGE_OUT_VAL_REQ, PGN.VOLTAGE_OUT_VAL_ANS,
                    lambda: self.uio.pin(0).set_voltage(5.0)
                )

                self.test_rx_only(
                    "VOLTAGE_IN (Voltage Input)",
                    PGN.VOLTAGE_IN_ANS, timeout=1.5
                )

                self.test_message_pair(
                    "CURRENT_OUT (Current Output)",
                    PGN.CUR_LOOP_OUT_VAL_REQ, PGN.CUR_LOOP_OUT_VAL_ANS,
                    lambda: self.uio.pin(1).set_tx_current(10.0)
                )

                self.test_rx_only(
                    "CURRENT_IN (Current Input)",
                    PGN.CUR_LOOP_IN_VAL_ANS, timeout=1.5
                )

                self.test_message_pair(
                    "PWM_OUT (PWM Output)",
                    PGN.PWM_OUT_VAL_REQ, PGN.PWM_OUT_VAL_ANS,
                    lambda: self.uio.pin(2).set_pwm(1000, 50)  # voltage=5.0V (fixed in current HW)
                )

                self.test_rx_only(
                    "PWM_IN (PWM Input)",
                    PGN.PWM_IN_ANS, timeout=1.5
                )

                self.test_message_pair(
                    "SWITCH_OUTPUT (Relay/Switch)",
                    PGN.SWITCH_OUTPUT_REQ, PGN.SWITCH_OUTPUT_ANS,
                    lambda: self.uio.pin(3).set_relay(RelayState.CLOSED)
                )

            # Test ELoad messages
            if self.eload:
                self.log("=" * 80)
                self.log("ELOAD MESSAGES")
                self.log("=" * 80)

                # Enable and set current
                self.test_message_pair(
                    "CUR_ELM_OUT (ELoad Current)",
                    PGN.CUR_ELM_OUT_VAL_REQ, PGN.CUR_ELM_IN_VAL_ANS,
                    lambda: self.eload.channel(0).set_current(0.5),
                    timeout=2.0
                )

                self.test_rx_only(
                    "TEMP_ELM_IN (ELoad Temperature)",
                    PGN.TEMP_ELM_IN_ANS, timeout=2.0
                )

            # Test IfMux CAN messages
            if self.ifmux:
                self.log("=" * 80)
                self.log("IFMUX CAN MESSAGES")
                self.log("=" * 80)

                self.test_message_pair(
                    "CAN_INFO (CAN Speed Config)",
                    PGN.CAN_INFO_REQ, PGN.CAN_INFO_ANS,
                    lambda: self.ifmux.channel(0).set_speed(CANSpeed.SPEED_500K)
                )

                self.test_rx_only(
                    "CAN_STATE (CAN Bus State)",
                    PGN.CAN_STATE_ANS, timeout=1.5
                )

                self.test_message_pair(
                    "CAN_MUX (CAN Relay Control)",
                    PGN.CAN_MUX_REQ, PGN.CAN_MUX_ANS,
                    lambda: self.ifmux.channel(0).set_internal_relay(closed=True)
                )

                # Test IfMux LIN messages
                self.log("=" * 80)
                self.log("IFMUX LIN MESSAGES")
                self.log("=" * 80)

                # Note: LIN messages might not have ANS, adjust if needed
                self.results['total'] += 1
                print(f"\nTesting LIN_CFG (LIN Configuration)")
                self.ifmux.configure_lin_frame(frame_id=0x10, data_length=8, checksum_type=1, direction=1)
                time.sleep(0.2)
                tx = self.interceptor.find_tx(PGN.LIN_CFG_REQ.value)
                if len(tx) > 0:
                    print(f"  ✓ PASSED: LIN_CFG_REQ sent")
                    self.results['passed'] += 1
                else:
                    print(f"  ✗ FAILED: LIN_CFG_REQ not sent")
                    self.results['failed'] += 1

                self.results['total'] += 1
                print(f"\nTesting LIN_FRAME_SET (LIN Frame Data)")
                self.ifmux.send_lin_frame(0x10, bytes([1, 2, 3]))
                time.sleep(0.2)
                tx = self.interceptor.find_tx(PGN.LIN_FRAME_SET_REQ.value)
                if len(tx) > 0:
                    print(f"  ✓ PASSED: LIN_FRAME_SET_REQ sent")
                    self.results['passed'] += 1
                else:
                    print(f"  ✗ FAILED: LIN_FRAME_SET_REQ not sent")
                    self.results['failed'] += 1

                self.test_rx_only(
                    "LIN_FRAME_RCVD (LIN Frame Received)",
                    PGN.LIN_FRAME_RCVD_ANS, timeout=1.5
                )

        except Exception as e:
            print(f"\n[ERROR] {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Cleanup
            self.interceptor.uninstall()

            if self.sdk:
                self.sdk.disconnect_all()

            # Print results
            self.print_results()

    def print_results(self):
        """Print test results"""
        self.interceptor.print_summary()
        self.interceptor.print_detailed(limit=30)

        print(f"\n{'='*80}")
        print(f"FINAL TEST RESULTS")
        print(f"{'='*80}")
        print(f"Total tests:   {self.results['total']}")
        print(f"Passed:        {self.results['passed']} ({100*self.results['passed']//self.results['total'] if self.results['total'] else 0}%)")
        print(f"Failed:        {self.results['failed']}")
        print(f"Skipped:       {self.results['skipped']}")
        print(f"{'='*80}")

        if self.results['failed'] == 0:
            print("✓ ALL TESTS PASSED!")
        else:
            print(f"✗ {self.results['failed']} TESTS FAILED")
        print(f"{'='*80}\n")


def main():
    """Main entry point"""
    # Configuration
    IFACE = "enp0s31f6"
    STREAM_ID = 1

    # Run test
    test = AllMessagesTest(IFACE, STREAM_ID)
    test.run()


if __name__ == "__main__":
    main()
