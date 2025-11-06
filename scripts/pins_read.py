#!/usr/bin/env python3
from pathlib import Path
import time
import argparse
from AvtpCanManager import AvtpCanManager
from devices_list import CanMessageHandler

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
    ap.add_argument("--dbc", default="soda_xil_fd.dbc")
    ap.add_argument("--dst", default="FF:FF:FF:FF:FF:FF",
                    help="target MAC or alias; default broadcast")
    args = ap.parse_args()

    dbc_path = Path(args.dbc)
    if not dbc_path.exists():
        raise SystemExit(f"DBC not found: {dbc_path}")

    handler = CanMessageHandler(str(dbc_path))
    mgr = AvtpCanManager(iface=args.iface, stream_id=args.stream_id)
    dst = resolve_dst(args.dst)

    def on_raw(raw: bytes):
        # Reuse existing parser that fills handler.devices with MODULE_INFO / PIN_INFO
        handler.parse_avtp_frame(raw)

    mgr.start_receiving(on_raw)

    # Discovery/poll (your pattern); ext 29-bit
    can_id = 0x00
    msg_id = 0x0400FFFE
    data   = bytes([0x1F, 0, 0, 0, 0, 0, 0, 0])

    for _ in range(3):
        mgr.send_can_message(can_id, msg_id, data, extended_id=True, can_fd=False, dst=dst)
        time.sleep(0.05)

    print("Waiting for MODULE_INFO / PIN_INFO ... (Ctrl+C to stop)")
    try:
        while True:
            mgr.send_can_message(can_id, msg_id, data, extended_id=True, can_fd=False, dst=dst)
            for mac, dev in handler.devices.items():
                if "PIN_INFO" in dev:
                    pin_info = dev["PIN_INFO"]
                    print(f"\n{mac} — PIN_INFO:")
                    for k, v in pin_info.items():
                        print(f"  {k}: {v}")
            time.sleep(1.0)
    except KeyboardInterrupt:
        pass
    finally:
        mgr.stop_receiving()

if __name__ == "__main__":
    main()
