#!/usr/bin/env python3
import argparse
from AvtpCanManager import AvtpCanManager

TARGETS = {
    "UIO1": "82:7B:C4:B1:92:F2",
    "UIO2": "EA:42:53:AA:03:A3",
    "UIO3": "AE:FF:85:97:E1:95",
    "ELM1": "86:12:35:9B:FD:45",
    "ELM2": "22:5D:94:7E:49:46",
    "IFMUX": "66:6A:DB:B3:06:27",
}

# TODO: replace with your actual CAN Message ID for UIO control (likely 29-bit)
CAN_MSG_ID_UIO_CTRL = 0x04001001  # <-- PLACEHOLDER

def resolve_dst(s: str) -> str:
    s = s.strip()
    if ":" in s:
        return s.upper()
    return TARGETS.get(s, "FF:FF:FF:FF:FF:FF")

def build_set_pin_payload(pin: int, voltage: float) -> bytes:
    """
    Encode Set-Pin payload per your protocol.
    Placeholder: command code = 0x21, voltage in millivolts.
    """
    CMD_SET_PIN = 0x21  # <-- PLACEHOLDER
    mv = max(0, int(round(voltage * 1000)))
    return bytes([
        CMD_SET_PIN,
        pin & 0xFF,
        (mv >> 0) & 0xFF,
        (mv >> 8) & 0xFF,
        (mv >> 16) & 0xFF,
        0x00, 0x00, 0x00
    ])

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iface", default="enp2s0.3900")
    ap.add_argument("--stream-id", type=int, default=1)
    ap.add_argument("--can-id", type=lambda x: int(x, 0), default=0x00,
                    help="ACF/CAN route id (first parameter to send_can_message)")
    ap.add_argument("--pin", type=int, required=True)
    ap.add_argument("--voltage", type=float, default=12.0)
    ap.add_argument("--ext", action="store_true", default=True, help="use 29-bit ID")
    ap.add_argument("--fd", action="store_true", help="set CAN-FD flag if needed")
    ap.add_argument("--dst", default="UIO1", help="target MAC or alias")
    args = ap.parse_args()

    payload = build_set_pin_payload(args.pin, args.voltage)
    dst = resolve_dst(args.dst)

    mgr = AvtpCanManager(iface=args.iface, stream_id=args.stream_id)
    mgr.send_can_message(args.can_id, CAN_MSG_ID_UIO_CTRL, payload,
                         extended_id=args.ext, can_fd=args.fd, dst=dst)
    print(f"Set-pin command sent to {dst} (template — replace IDs/encoding per spec).")

if __name__ == "__main__":
    main()
