#!/usr/bin/env python3
"""
UIO Pin Control Script

This script allows you to control UIO module pins by setting:
- Voltage output (0-24V)
- Current output (0-20mA)
- PWM output (20Hz-5kHz, 0-100% duty cycle)

Usage:
    # Set voltage on pin 0 to 12V
    python pins_write.py --dst UIO1 --pin 0 --voltage 12.0

    # Set current on pin 1 to 10mA
    python pins_write.py --dst UIO1 --pin 1 --current 10.0

    # Set PWM on pin 2 to 1kHz, 50% duty
    python pins_write.py --dst UIO1 --pin 2 --pwm-freq 1000 --pwm-duty 50

    # Disable all features on pin 0
    python pins_write.py --dst UIO1 --pin 0 --disable
"""

import argparse
import sys
import time
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from AvtpCanManager import AvtpCanManager
import cantools

# Target device aliases
TARGETS = {
    "UIO1": "82:7B:C4:B1:92:F2",
    "UIO2": "EA:42:53:AA:03:A3",
    "UIO3": "AE:FF:85:97:E1:95",
}

# CAN Message IDs (from DBC)
MSG_OP_MODE_REQ = 2367815422
MSG_SWITCH_OUTPUT_REQ = 2367946494
MSG_VOLTAGE_OUT_VAL_REQ = 2367094526
MSG_CUR_LOOP_OUT_VAL_REQ = 2368143102
MSG_PWM_OUT_VAL_REQ = 2366832382

# Feature states (op_mode values)
OP_MODE_UNKNOWN = 0
OP_MODE_IDLE = 1
OP_MODE_DISABLED = 2
OP_MODE_OPERATE = 3
OP_MODE_WARNING = 4
OP_MODE_ERROR = 5


class UIOPinController:
    """Controller for UIO module pins"""

    def __init__(self, iface: str, stream_id: int, dbc_path: str):
        self.mgr = AvtpCanManager(iface=iface, stream_id=stream_id)
        self.db = cantools.database.load_file(dbc_path)

    def _send_message(self, msg_name: str, data: dict, dst_mac: str, can_bus: int = 0):
        """Encode and send a CAN message"""
        msg = self.db.get_message_by_name(msg_name)
        payload = msg.encode(data)

        # Pad to at least 8 bytes (CAN FD can be longer)
        if len(payload) < 8:
            payload += b'\x00' * (8 - len(payload))

        self.mgr.send_can_message(
            can_id=can_bus,
            msg_id=msg.frame_id,
            data=payload,
            extended_id=True,
            can_fd=True,
            dst=dst_mac
        )

    def disable_all_features(self, pin: int, dst_mac: str):
        """Disable all features on a specific pin"""
        print(f"Disabling all features on pin {pin}...")

        # Create OP_MODE_req message with all features disabled
        op_mode_data = {}
        for i in range(1, 9):
            op_mode_data[f'vlt_i_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'vlt_o_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'cur_i_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'cur_o_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'pwm_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'icu_{i}_op_mode'] = OP_MODE_DISABLED

        self._send_message('OP_MODE_req', op_mode_data, dst_mac)

        # Create SWITCH_OUTPUT_req with all relays off
        switch_data = {}
        for i in range(1, 9):
            switch_data[f'sel_vlt_o_{i}'] = 0
            switch_data[f'sel_cur_o_{i}'] = 0
            switch_data[f'sel_cur_i_{i}'] = 0
            switch_data[f'sel_pwm_{i}'] = 0
            switch_data[f'sel_icu_{i}'] = 0

        self._send_message('SWITCH_OUTPUT_req', switch_data, dst_mac)
        print("All features disabled")

    def set_voltage(self, pin: int, voltage: float, dst_mac: str):
        """Set voltage output on a pin"""
        if not (0 <= pin < 8):
            raise ValueError("Pin must be 0-7")
        if not (0 <= voltage <= 24):
            raise ValueError("Voltage must be 0-24V")

        pin_num = pin + 1  # DBC uses 1-based indexing

        print(f"Setting pin {pin} to {voltage}V...")

        # Step 1: Enable voltage output feature in OP_MODE_req
        op_mode_data = {}
        for i in range(1, 9):
            # Disable all features by default
            op_mode_data[f'vlt_i_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'vlt_o_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'cur_i_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'cur_o_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'pwm_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'icu_{i}_op_mode'] = OP_MODE_DISABLED

        # Enable voltage output for target pin
        op_mode_data[f'vlt_o_{pin_num}_op_mode'] = OP_MODE_OPERATE

        self._send_message('OP_MODE_req', op_mode_data, dst_mac)
        time.sleep(0.05)

        # Step 2: Set relay state in SWITCH_OUTPUT_req
        switch_data = {}
        for i in range(1, 9):
            switch_data[f'sel_vlt_o_{i}'] = 1 if i == pin_num else 0
            switch_data[f'sel_cur_o_{i}'] = 0
            switch_data[f'sel_cur_i_{i}'] = 0
            switch_data[f'sel_pwm_{i}'] = 0
            switch_data[f'sel_icu_{i}'] = 0

        self._send_message('SWITCH_OUTPUT_req', switch_data, dst_mac)
        time.sleep(0.05)

        # Step 3: Set voltage value in VOLTAGE_OUT_VAL_req
        voltage_data = {}
        for i in range(1, 9):
            voltage_data[f'vlt_o_{i}_value'] = voltage if i == pin_num else 0.0

        self._send_message('VOLTAGE_OUT_VAL_req', voltage_data, dst_mac)

        print(f"Pin {pin} set to {voltage}V")

    def set_current(self, pin: int, current: float, dst_mac: str):
        """Set current loop output on a pin"""
        if not (0 <= pin < 8):
            raise ValueError("Pin must be 0-7")
        if not (0 <= current <= 20):
            raise ValueError("Current must be 0-20mA")

        pin_num = pin + 1

        print(f"Setting pin {pin} to {current}mA...")

        # Step 1: Enable current output feature
        op_mode_data = {}
        for i in range(1, 9):
            op_mode_data[f'vlt_i_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'vlt_o_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'cur_i_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'cur_o_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'pwm_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'icu_{i}_op_mode'] = OP_MODE_DISABLED

        op_mode_data[f'cur_o_{pin_num}_op_mode'] = OP_MODE_OPERATE

        self._send_message('OP_MODE_req', op_mode_data, dst_mac)
        time.sleep(0.05)

        # Step 2: Set relay state
        switch_data = {}
        for i in range(1, 9):
            switch_data[f'sel_vlt_o_{i}'] = 0
            switch_data[f'sel_cur_o_{i}'] = 1 if i == pin_num else 0
            switch_data[f'sel_cur_i_{i}'] = 0
            switch_data[f'sel_pwm_{i}'] = 0
            switch_data[f'sel_icu_{i}'] = 0

        self._send_message('SWITCH_OUTPUT_req', switch_data, dst_mac)
        time.sleep(0.05)

        # Step 3: Set current value
        current_data = {}
        for i in range(1, 9):
            current_data[f'cur_ma_o_{i}_value'] = current if i == pin_num else 0.0

        self._send_message('CUR_LOOP_OUT_VAL_req', current_data, dst_mac)

        print(f"Pin {pin} set to {current}mA")

    def set_pwm(self, pin: int, frequency: float, duty: float, voltage: float, dst_mac: str):
        """Set PWM output on a pin"""
        if not (0 <= pin < 8):
            raise ValueError("Pin must be 0-7")
        if not (20 <= frequency <= 5000):
            raise ValueError("Frequency must be 20-5000Hz")
        if not (0 <= duty <= 100):
            raise ValueError("Duty cycle must be 0-100%")
        if not (5 <= voltage <= 30.5):
            raise ValueError("PWM voltage must be 5-30.5V")

        pin_num = pin + 1

        print(f"Setting pin {pin} to PWM: {frequency}Hz, {duty}%, {voltage}V...")

        # Step 1: Enable PWM output feature
        op_mode_data = {}
        for i in range(1, 9):
            op_mode_data[f'vlt_i_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'vlt_o_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'cur_i_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'cur_o_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'pwm_{i}_op_mode'] = OP_MODE_DISABLED
            op_mode_data[f'icu_{i}_op_mode'] = OP_MODE_DISABLED

        op_mode_data[f'pwm_{pin_num}_op_mode'] = OP_MODE_OPERATE

        self._send_message('OP_MODE_req', op_mode_data, dst_mac)
        time.sleep(0.05)

        # Step 2: Set relay state
        switch_data = {}
        for i in range(1, 9):
            switch_data[f'sel_vlt_o_{i}'] = 0
            switch_data[f'sel_cur_o_{i}'] = 0
            switch_data[f'sel_cur_i_{i}'] = 0
            switch_data[f'sel_pwm_{i}'] = 1 if i == pin_num else 0
            switch_data[f'sel_icu_{i}'] = 0

        self._send_message('SWITCH_OUTPUT_req', switch_data, dst_mac)
        time.sleep(0.05)

        # Step 3: Set PWM values
        pwm_data = {}
        for i in range(1, 9):
            if i == pin_num:
                pwm_data[f'pwm_{i}_frequency'] = int(frequency)
                pwm_data[f'pwm_{i}_duty'] = duty
                pwm_data[f'pwm_{i}_voltage'] = voltage
            else:
                pwm_data[f'pwm_{i}_frequency'] = 0
                pwm_data[f'pwm_{i}_duty'] = 0
                pwm_data[f'pwm_{i}_voltage'] = 5.0  # Min value

        self._send_message('PWM_OUT_VAL_req', pwm_data, dst_mac)

        print(f"Pin {pin} set to PWM: {frequency}Hz, {duty}%, {voltage}V")


def resolve_dst(s: str) -> str:
    """Resolve device name or MAC address"""
    s = s.strip()
    if ":" in s:
        return s.upper()
    return TARGETS.get(s, s)


def main():
    parser = argparse.ArgumentParser(
        description='Control UIO module pins',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument("--iface", default="enp0s31f6",
                        help="Network interface (default: enp0s31f6)")
    parser.add_argument("--stream-id", type=int, default=1,
                        help="AVTP stream ID (default: 1)")
    parser.add_argument("--dbc", default="soda_xil_fd.dbc",
                        help="DBC file path (default: soda_xil_fd.dbc)")
    parser.add_argument("--dst", default="UIO1",
                        help="Target device MAC or alias (UIO1/UIO2/UIO3)")
    parser.add_argument("--pin", type=int, required=True,
                        help="Pin number (0-7)")

    # Operation selection
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--voltage", type=float,
                       help="Set voltage output in volts (0-24V)")
    group.add_argument("--current", type=float,
                       help="Set current loop output in mA (0-20mA)")
    group.add_argument("--pwm", action="store_true",
                       help="Set PWM output (requires --pwm-freq, --pwm-duty, --pwm-voltage)")
    group.add_argument("--disable", action="store_true",
                       help="Disable all features on pin")

    # PWM parameters
    parser.add_argument("--pwm-freq", type=float,
                        help="PWM frequency in Hz (20-5000)")
    parser.add_argument("--pwm-duty", type=float,
                        help="PWM duty cycle in %% (0-100)")
    parser.add_argument("--pwm-voltage", type=float, default=12.0,
                        help="PWM voltage level in V (5-30.5, default: 12)")

    args = parser.parse_args()

    # Validate DBC file
    dbc_path = Path(args.dbc)
    if not dbc_path.exists():
        print(f"Error: DBC file not found: {dbc_path}")
        return 1

    # Resolve target MAC address
    dst_mac = resolve_dst(args.dst)

    # Validate PWM parameters
    if args.pwm:
        if args.pwm_freq is None or args.pwm_duty is None:
            print("Error: --pwm requires --pwm-freq and --pwm-duty")
            return 1

    try:
        # Create controller
        controller = UIOPinController(
            iface=args.iface,
            stream_id=args.stream_id,
            dbc_path=str(dbc_path)
        )

        # Execute command
        if args.disable:
            controller.disable_all_features(args.pin, dst_mac)
        elif args.voltage is not None:
            controller.set_voltage(args.pin, args.voltage, dst_mac)
        elif args.current is not None:
            controller.set_current(args.pin, args.current, dst_mac)
        elif args.pwm:
            controller.set_pwm(
                args.pin,
                args.pwm_freq,
                args.pwm_duty,
                args.pwm_voltage,
                dst_mac
            )

        print("Command sent successfully")
        return 0

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
