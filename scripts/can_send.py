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

def resolve_dst(s: str) -> str:
    s = s.strip()
    if ":" in s:
        return s.upper()
    return TARGETS.get(s, "FF:FF:FF:FF:FF:FF")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iface", default="enp2s0.3900")
    ap.add_argument("--stream-id", type=int, default=1)
    ap.add_argument("--bus", type=lambda x: int(x, 0), default=0x00,
                    help="ACF/CAN route id (first parameter to AvtpCanManager.send_can_message)")
    ap.add_argument("--msg-id", type=lambda x: int(x, 0), required=True,
                    help="CAN message id (e.g. 0x18FF50E5)")
    ap.add_argument("--data", default="1122334455667788",
                    help="hex payload, up to 64 bytes (<=128 hex chars)")
    ap.add_argument("--ext", action="store_true", help="use 29-bit (extended) ID")
    ap.add_argument("--fd", action="store_true", help="set CAN-FD flag")
    ap.add_argument("--dst", default="FF:FF:FF:FF:FF:FF",
                    help="target MAC or alias (UIO1/UIO2/UIO3/ELM1/ELM2/IFMUX)")
    args = ap.parse_args()

    payload = bytes.fromhex(args.data)
    if len(payload) > 64:
        raise SystemExit("payload too long (max 64 bytes)")

    dst = resolve_dst(args.dst)
    mgr = AvtpCanManager(iface=args.iface, stream_id=args.stream_id)
    mgr.send_can_message(args.bus, args.msg_id, payload,
                         extended_id=args.ext, can_fd=args.fd, dst=dst)
    print(f"Frame sent to {dst}: bus=0x{args.bus:X} msg_id=0x{args.msg_id:X} dlc={len(payload)} ext={int(args.ext)} fd={int(args.fd)}")

if __name__ == "__main__":
    main()
