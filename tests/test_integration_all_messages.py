#!/usr/bin/env python3
"""
Integration Test - All Modules and Messages

Tests all 33+ CAN messages across UIO, ELoad, and IfMux modules.
Verifies that commands are sent correctly and responses are received.
"""

import sys
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sdrig import SDRIG
from sdrig.types.enums import PGN, Feature, FeatureState, CANSpeed, CANState, RelayState
from sdrig.utils.logger import SDRIGLogger


class MessageTracker:
    """Tracks sent and received CAN messages for verification"""

    def __init__(self):
        self.sent_messages = []
        self.received_messages = []

    def on_message_sent(self, pgn: int, data: dict):
        """Record sent message"""
        self.sent_messages.append({
            'pgn': pgn,
            'data': data,
            'timestamp': time.time()
        })

    def on_message_received(self, pgn: int, data: dict):
        """Record received message"""
        self.received_messages.append({
            'pgn': pgn,
            'data': data,
            'timestamp': time.time()
        })

    def find_sent(self, pgn: int):
        """Find sent message by PGN"""
        return [msg for msg in self.sent_messages if msg['pgn'] == pgn]

    def find_received(self, pgn: int):
        """Find received message by PGN"""
        return [msg for msg in self.received_messages if msg['pgn'] == pgn]

    def clear(self):
        """Clear all tracked messages"""
        self.sent_messages.clear()
        self.received_messages.clear()

    def print_summary(self):
        """Print summary of messages"""
        print(f"\n{'='*70}")
        print(f"MESSAGE TRACKER SUMMARY")
        print(f"{'='*70}")
        print(f"Sent messages:     {len(self.sent_messages)}")
        print(f"Received messages: {len(self.received_messages)}")

        # Group by PGN
        sent_pgns = {}
        for msg in self.sent_messages:
            pgn = msg['pgn']
            sent_pgns[pgn] = sent_pgns.get(pgn, 0) + 1

        received_pgns = {}
        for msg in self.received_messages:
            pgn = msg['pgn']
            received_pgns[pgn] = received_pgns.get(pgn, 0) + 1

        print(f"\nSent PGNs:")
        for pgn, count in sorted(sent_pgns.items()):
            pgn_name = get_pgn_name(pgn)
            print(f"  0x{pgn:05X} {pgn_name:30s}: {count}")

        print(f"\nReceived PGNs:")
        for pgn, count in sorted(received_pgns.items()):
            pgn_name = get_pgn_name(pgn)
            print(f"  0x{pgn:05X} {pgn_name:30s}: {count}")


def get_pgn_name(pgn: int) -> str:
    """Get human-readable PGN name"""
    for name, value in PGN.__members__.items():
        if value == pgn:
            return name
    return "UNKNOWN"


class IntegrationTest:
    """Main integration test class"""

    def __init__(self, iface: str, stream_id: int):
        self.iface = iface
        self.stream_id = stream_id
        self.tracker = MessageTracker()
        self.sdk = None

        # Device references
        self.uio = None
        self.eload = None
        self.ifmux = None

        # Test statistics
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0

    def log(self, message: str):
        """Log test message"""
        print(f"[TEST] {message}")

    def assert_true(self, condition: bool, message: str):
        """Assert condition is true"""
        self.tests_run += 1
        if condition:
            self.tests_passed += 1
            print(f"  ✓ PASS: {message}")
        else:
            self.tests_failed += 1
            print(f"  ✗ FAIL: {message}")

    def assert_pgn_sent(self, pgn: int, message: str = ""):
        """Assert that PGN was sent"""
        sent = self.tracker.find_sent(pgn)
        pgn_name = get_pgn_name(pgn)
        msg = message or f"PGN {pgn_name} (0x{pgn:05X}) was sent"
        self.assert_true(len(sent) > 0, msg)

    def assert_pgn_received(self, pgn: int, message: str = "", timeout: float = 2.0):
        """Assert that PGN was received within timeout"""
        pgn_name = get_pgn_name(pgn)
        msg = message or f"PGN {pgn_name} (0x{pgn:05X}) was received"

        start = time.time()
        while (time.time() - start) < timeout:
            received = self.tracker.find_received(pgn)
            if len(received) > 0:
                self.assert_true(True, msg)
                return
            time.sleep(0.1)

        self.assert_true(False, f"{msg} (timeout)")

    def discover_and_connect(self):
        """Discover devices and connect to them"""
        self.log("=" * 70)
        self.log("PHASE 1: DEVICE DISCOVERY AND CONNECTION")
        self.log("=" * 70)

        # Create SDK
        self.sdk = SDRIG(iface=self.iface, stream_id=self.stream_id)

        # Discover devices
        self.log("Discovering devices...")
        devices = self.sdk.discover_devices(timeout=3.0, print_devices=False)

        self.assert_true(len(devices) > 0, f"Found {len(devices)} devices")

        # Connect to devices by type
        for mac, info in devices.items():
            app_name = info.app_name.upper()

            if "UIO" in app_name or "UNIVERSAL" in app_name:
                self.log(f"Connecting to UIO device: {mac}")
                self.uio = self.sdk.connect_uio(mac, auto_start=True)

            elif "ELOAD" in app_name or "LOAD" in app_name:
                self.log(f"Connecting to ELoad device: {mac}")
                self.eload = self.sdk.connect_eload(mac, auto_start=True)

            elif "IFMUX" in app_name or "MUX" in app_name:
                self.log(f"Connecting to IfMux device: {mac}")
                self.ifmux = self.sdk.connect_ifmux(mac, auto_start=True, lin_enabled=True)

        # Wait for devices to start
        time.sleep(1.0)

        self.assert_true(self.uio is not None, "UIO device found and connected")
        self.assert_true(self.eload is not None, "ELoad device found and connected")
        self.assert_true(self.ifmux is not None, "IfMux device found and connected")

    def test_device_info_messages(self):
        """Test MODULE_INFO, MODULE_INFO_EX, PIN_INFO messages"""
        self.log("\n" + "=" * 70)
        self.log("PHASE 2: DEVICE INFORMATION MESSAGES")
        self.log("=" * 70)

        # These messages are sent automatically during discovery
        # Just verify we received them

        self.log("Testing MODULE_INFO (0x001FE)...")
        self.assert_pgn_received(PGN.MODULE_INFO, "MODULE_INFO received")

        self.log("Testing MODULE_INFO_EX (0x008FE)...")
        self.assert_pgn_received(PGN.MODULE_INFO_EX, "MODULE_INFO_EX received")

        self.log("Testing PIN_INFO (0x010FE)...")
        self.assert_pgn_received(PGN.PIN_INFO, "PIN_INFO received")

    def test_uio_messages(self):
        """Test all UIO messages"""
        if not self.uio:
            self.log("\nSkipping UIO tests - no UIO device found")
            return

        self.log("\n" + "=" * 70)
        self.log("PHASE 3: UIO MESSAGES")
        self.log("=" * 70)

        # Test OP_MODE messages
        self.log("\nTesting OP_MODE_REQ (0x121FE) / OP_MODE_ANS (0x120FE)...")
        self.uio.pin(0).enable_feature(Feature.SET_VOLTAGE)
        time.sleep(0.2)
        self.assert_pgn_sent(PGN.OP_MODE_REQ, "OP_MODE_REQ sent")
        self.assert_pgn_received(PGN.OP_MODE_ANS, "OP_MODE_ANS received", timeout=1.0)

        # Test VOLTAGE_OUT messages
        self.log("\nTesting VOLTAGE_OUT_VAL_REQ (0x116FE) / VOLTAGE_OUT_VAL_ANS (0x117FE)...")
        self.uio.pin(0).set_voltage(5.0)
        time.sleep(0.2)
        self.assert_pgn_sent(PGN.VOLTAGE_OUT_VAL_REQ, "VOLTAGE_OUT_VAL_REQ sent")
        self.assert_pgn_received(PGN.VOLTAGE_OUT_VAL_ANS, "VOLTAGE_OUT_VAL_ANS received", timeout=1.0)

        # Test VOLTAGE_IN messages
        self.log("\nTesting VOLTAGE_IN_ANS (0x114FE)...")
        self.uio.pin(1).enable_feature(Feature.GET_VOLTAGE)
        time.sleep(0.5)
        self.assert_pgn_received(PGN.VOLTAGE_IN_ANS, "VOLTAGE_IN_ANS received", timeout=2.0)
        voltage = self.uio.pin(1).get_voltage()
        self.assert_true(voltage >= 0, f"Voltage reading: {voltage:.2f}V")

        # Test CURRENT_OUT messages
        self.log("\nTesting CUR_LOOP_OUT_VAL_REQ (0x126FE) / CUR_LOOP_OUT_VAL_ANS (0x127FE)...")
        self.uio.pin(2).enable_feature(Feature.SET_CURRENT)
        time.sleep(0.2)
        self.uio.pin(2).set_tx_current(10.0)  # 10 mA
        time.sleep(0.2)
        self.assert_pgn_sent(PGN.CUR_LOOP_OUT_VAL_REQ, "CUR_LOOP_OUT_VAL_REQ sent")
        self.assert_pgn_received(PGN.CUR_LOOP_OUT_VAL_ANS, "CUR_LOOP_OUT_VAL_ANS received", timeout=1.0)

        # Test CURRENT_IN messages
        self.log("\nTesting CUR_LOOP_IN_VAL_ANS (0x128FE)...")
        self.uio.pin(3).enable_feature(Feature.GET_CURRENT)
        time.sleep(0.5)
        self.assert_pgn_received(PGN.CUR_LOOP_IN_VAL_ANS, "CUR_LOOP_IN_VAL_ANS received", timeout=2.0)
        current = self.uio.pin(3).get_rx_current()
        self.assert_true(current >= 0, f"Current reading: {current:.2f}mA")

        # Test PWM_OUT messages
        # Note: Current HW outputs PWM at fixed 5V level
        self.log("\nTesting PWM_OUT_VAL_REQ (0x112FE) / PWM_OUT_VAL_ANS (0x113FE)...")
        self.uio.pin(4).enable_feature(Feature.SET_PWM)
        time.sleep(0.2)
        self.uio.pin(4).set_pwm(frequency=1000, duty_cycle=50.0)  # voltage defaults to 5.0V
        time.sleep(0.2)
        self.assert_pgn_sent(PGN.PWM_OUT_VAL_REQ, "PWM_OUT_VAL_REQ sent")
        self.assert_pgn_received(PGN.PWM_OUT_VAL_ANS, "PWM_OUT_VAL_ANS received", timeout=1.0)

        # Test PWM_IN messages
        self.log("\nTesting PWM_IN_ANS (0x122FE)...")
        self.uio.pin(5).enable_pwm_input()
        time.sleep(0.5)
        self.assert_pgn_received(PGN.PWM_IN_ANS, "PWM_IN_ANS received", timeout=2.0)

        # Test SWITCH_OUTPUT messages
        self.log("\nTesting SWITCH_OUTPUT_REQ (0x123FE) / SWITCH_OUTPUT_ANS (0x124FE)...")
        self.uio.pin(6).set_relay(RelayState.CLOSED)
        time.sleep(0.2)
        self.assert_pgn_sent(PGN.SWITCH_OUTPUT_REQ, "SWITCH_OUTPUT_REQ sent")
        self.assert_pgn_received(PGN.SWITCH_OUTPUT_ANS, "SWITCH_OUTPUT_ANS received", timeout=1.0)

        # Cleanup - disable all
        self.log("\nCleaning up UIO...")
        self.uio.pin(0).set_voltage(0)
        self.uio.pin(2).set_tx_current(0)
        self.uio.pin(4).set_pwm(0, 0)  # Disable PWM (voltage parameter not needed)
        self.uio.pin(6).set_relay(RelayState.OPEN)
        time.sleep(0.5)

    def test_eload_messages(self):
        """Test all ELoad messages"""
        if not self.eload:
            self.log("\nSkipping ELoad tests - no ELoad device found")
            return

        self.log("\n" + "=" * 70)
        self.log("PHASE 4: ELOAD MESSAGES")
        self.log("=" * 70)

        # Test CUR_ELM_OUT messages
        self.log("\nTesting CUR_ELM_OUT_VAL_REQ (0x129FE)...")
        self.eload.channel(0).set_current(0.5)  # 0.5A
        time.sleep(0.2)
        self.assert_pgn_sent(PGN.CUR_ELM_OUT_VAL_REQ, "CUR_ELM_OUT_VAL_REQ sent")

        # Test CUR_ELM_IN messages
        self.log("\nTesting CUR_ELM_IN_VAL_ANS (0x12AFE)...")
        time.sleep(1.0)  # Wait for measurement
        self.assert_pgn_received(PGN.CUR_ELM_IN_VAL_ANS, "CUR_ELM_IN_VAL_ANS received", timeout=2.0)
        current = self.eload.channel(0).get_current()
        self.assert_true(current >= 0, f"Current measurement: {current:.3f}A")

        # Test TEMP_ELM messages
        self.log("\nTesting TEMP_ELM_IN_ANS (0x12EFE)...")
        time.sleep(1.0)
        self.assert_pgn_received(PGN.TEMP_ELM_IN_ANS, "TEMP_ELM_IN_ANS received", timeout=2.0)
        temp = self.eload.channel(0).get_temperature()
        self.assert_true(temp > 0, f"Temperature reading: {temp:.1f}°C")

        # Cleanup
        self.log("\nCleaning up ELoad...")
        self.eload.disable_all_channels()
        time.sleep(0.5)

    def test_ifmux_can_messages(self):
        """Test IfMux CAN messages"""
        if not self.ifmux:
            self.log("\nSkipping IfMux CAN tests - no IfMux device found")
            return

        self.log("\n" + "=" * 70)
        self.log("PHASE 5: IFMUX CAN MESSAGES")
        self.log("=" * 70)

        # Test CAN_INFO messages
        self.log("\nTesting CAN_INFO_REQ (0x021FE) / CAN_INFO_ANS (0x020FE)...")
        self.ifmux.channel(0).set_speed(CANSpeed.CAN_500K, CANSpeed.CAN_FD_2M)
        time.sleep(0.2)
        self.assert_pgn_sent(PGN.CAN_INFO_REQ, "CAN_INFO_REQ sent")
        self.assert_pgn_received(PGN.CAN_INFO_ANS, "CAN_INFO_ANS received", timeout=1.0)

        # Test CAN_STATE messages
        self.log("\nTesting CAN_STATE_ANS (0x022FE)...")
        time.sleep(0.5)
        self.assert_pgn_received(PGN.CAN_STATE_ANS, "CAN_STATE_ANS received", timeout=2.0)
        state = self.ifmux.can(0).get_state()
        self.assert_true(state is not None, f"CAN state: {state}")

        # Test CAN_MUX messages
        self.log("\nTesting CAN_MUX_REQ (0x028FE) / CAN_MUX_ANS (0x029FE)...")
        self.ifmux.channel(0).set_internal_relay(closed=True)
        time.sleep(0.2)
        self.assert_pgn_sent(PGN.CAN_MUX_REQ, "CAN_MUX_REQ sent")
        self.assert_pgn_received(PGN.CAN_MUX_ANS, "CAN_MUX_ANS received", timeout=1.0)

    def test_ifmux_lin_messages(self):
        """Test IfMux LIN messages"""
        if not self.ifmux:
            self.log("\nSkipping IfMux LIN tests - no IfMux device found")
            return

        self.log("\n" + "=" * 70)
        self.log("PHASE 6: IFMUX LIN MESSAGES")
        self.log("=" * 70)

        # Test LIN_CFG messages
        self.log("\nTesting LIN_CFG_REQ (0x040FE)...")
        self.ifmux.configure_lin_frame(frame_id=0x10, data_length=8, checksum_type=1, direction=1)
        time.sleep(0.2)
        self.assert_pgn_sent(PGN.LIN_CFG_REQ, "LIN_CFG_REQ sent")

        # Test LIN_FRAME_SET messages
        self.log("\nTesting LIN_FRAME_SET_REQ (0x042FE)...")
        self.ifmux.send_lin_frame(frame_id=0x10, data=bytes([0x01, 0x02, 0x03]))
        time.sleep(0.2)
        self.assert_pgn_sent(PGN.LIN_FRAME_SET_REQ, "LIN_FRAME_SET_REQ sent")

        # Test LIN_FRAME_RCVD messages
        self.log("\nTesting LIN_FRAME_RCVD_ANS (0x043FE)...")
        time.sleep(0.5)
        self.assert_pgn_received(PGN.LIN_FRAME_RCVD_ANS, "LIN_FRAME_RCVD_ANS received", timeout=2.0)

    def run(self):
        """Run all tests"""
        print("\n" + "=" * 70)
        print("SDRIG INTEGRATION TEST - ALL MODULES AND MESSAGES")
        print("=" * 70)
        print(f"Interface: {self.iface}")
        print(f"Stream ID: {self.stream_id}")
        print("=" * 70)

        try:
            # Phase 1: Discovery and connection
            self.discover_and_connect()

            # Phase 2: Device info messages
            self.test_device_info_messages()

            # Phase 3: UIO messages
            self.test_uio_messages()

            # Phase 4: ELoad messages
            self.test_eload_messages()

            # Phase 5: IfMux CAN messages
            self.test_ifmux_can_messages()

            # Phase 6: IfMux LIN messages
            self.test_ifmux_lin_messages()

        except Exception as e:
            self.log(f"ERROR: {e}")
            import traceback
            traceback.print_exc()

        finally:
            # Print summary
            self.print_summary()

            # Cleanup
            if self.sdk:
                self.sdk.disconnect_all()

    def print_summary(self):
        """Print test summary"""
        self.tracker.print_summary()

        print(f"\n{'='*70}")
        print(f"TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Tests run:    {self.tests_run}")
        print(f"Tests passed: {self.tests_passed} ({100*self.tests_passed//self.tests_run if self.tests_run else 0}%)")
        print(f"Tests failed: {self.tests_failed}")
        print(f"{'='*70}")

        if self.tests_failed == 0:
            print("✓ ALL TESTS PASSED!")
        else:
            print(f"✗ {self.tests_failed} TESTS FAILED")
        print(f"{'='*70}\n")


def main():
    """Main entry point"""
    # Enable debug logging
    SDRIGLogger.enable_debug_mode()

    # Configuration
    IFACE = "enp0s31f6"
    STREAM_ID = 1

    # Run test
    test = IntegrationTest(IFACE, STREAM_ID)
    test.run()


if __name__ == "__main__":
    main()
