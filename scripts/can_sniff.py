#!/usr/bin/env python3
import argparse
from scapy.layers.l2 import Ether  # type: ignore
from AVTP import AVTPPacket        # type: ignore
from AvtpCanManager import AvtpCanManager

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iface", default="enp2s0.3900")
    ap.add_argument("--stream-id", type=int, default=1)
    args = ap.parse_args()

    mgr = AvtpCanManager(iface=args.iface, stream_id=args.stream_id)

    def on_raw(raw: bytes):
        pkt = Ether(raw)
        if AVTPPacket not in pkt:
            return
        avtp = pkt[AVTPPacket]
        flags = int(getattr(avtp, "flags", 0))
        is_fd = bool(flags & 0x02)
        is_ext = bool(flags & 0x08)
        can_id = int(getattr(avtp, "can_id", 0))
        msg_id = int(getattr(avtp, "msg_id", 0))
        data = bytes(getattr(avtp, "data", b""))
        print(f"can_id=0x{can_id:02X} msg_id=0x{msg_id:08X} ext={int(is_ext)} fd={int(is_fd)} dlc={len(data)} data={data.hex()}")

    mgr.start_receiving(on_raw)
    print("Sniffing... Ctrl+C to stop")
    try:
        while True:
            pass
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
