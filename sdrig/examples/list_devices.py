import os
import time
import socket
import struct
import cantools
from typing import Dict, Any, Optional
from sdrig.transport.avtp_can_manager import AvtpCanManager

MODULE_INFO      = 0x0C01FEFE
MODULE_INFO_EX   = 0x0C08FEFE
MODULE_INFO_BOOT = 0x0C02FEFE
PIN_INFO         = 0x0C10FEFE

class CanMessageHandler:
    def __init__(self, dbc_path: str):
        self.db = cantools.database.load_file(dbc_path)
        self.devices: Dict[str, Dict[str, Any]] = {}

    @staticmethod
    def is_j1939(can_id: int) -> bool:
        return can_id > 0x7FF

    @staticmethod
    def fix_can_id_j1939(can_id: int) -> int:
        # normalize SA to 0xFE to match wildcard entries in DBC
        if not CanMessageHandler.is_j1939(can_id):
            return can_id
        return (can_id & 0xFFFFFF00) | 0x000000FE

    def parse_acf_can_message(self, message: bytes, mac_str: str):
        # ACF-CAN Brief header
        message_type = (message[0] >> 1) & 0x7F
        quadlets = ((message[0] & 0x01) << 8) | (message[1] & 0xFF)
        flags = message[2] & 0xFF
        bus_id = message[3] & 0x1F
        can_id = ((message[4] & 0x1F) << 24) | (message[5] << 16) | (message[6] << 8) | (message[7] & 0xFF)
        can_id = self.fix_can_id_j1939(can_id)
        total_len = quadlets * 4
        data = message[8:total_len]

        if bus_id != 0:
            return  # listen only CAN bus 0 for discovery

        try:
            decoded = self.db.decode_message(can_id, data)
        except Exception:
            return

        if mac_str not in self.devices:
            self.devices[mac_str] = {}

        if can_id == MODULE_INFO:
            self.devices[mac_str]['MODULE_INFO'] = decoded
        elif can_id == MODULE_INFO_EX:
            self.devices[mac_str]['MODULE_INFO_EX'] = decoded
        elif can_id == MODULE_INFO_BOOT:
            self.devices[mac_str]['MODULE_INFO_BOOT'] = decoded
        elif can_id == PIN_INFO:
            self.devices[mac_str]['PIN_INFO'] = decoded

    def parse_avtp_frame(self, frame: bytes):
        # parse minimal Ethernet + AVTP NTSCF envelope
        b = frame
        if len(b) < 26:
            return
        # EtherType 0x22F0
        eth_type = (b[12] << 8) | b[13]
        if eth_type != 0x22F0:
            return
        subtype = b[14]
        if subtype != 0x82:  # NTSCF
            return
        data_len = ((b[15] & 0x07) << 8) | b[16]
        offset = 26
        src_mac = b[6:12]
        mac_str = ":".join(f"{x:02x}" for x in src_mac)
        end = 26 + data_len
        # iterate ACF messages inside
        while offset + 2 <= end and offset + 2 <= len(b):
            # first 2 bytes provide quadlets
            if offset + 2 > len(b):
                break
            quadlets = ((b[offset] & 0x01) << 8) | b[offset+1]
            msg_len = quadlets * 4
            if msg_len <= 0 or offset + msg_len > len(b):
                break
            acf = b[offset:offset+msg_len]
            try:
                self.parse_acf_can_message(acf, mac_str)
            except Exception:
                pass
            offset += msg_len

    def print_devices(self):
        print(f"Devices found: {len(self.devices)}")
        for mac, info in self.devices.items():
            name = hw = ver = build = crc = ip = ""
            if 'MODULE_INFO' in info:
                mi = info['MODULE_INFO']
                try:
                    fw_name = (mi['module_app_fw_name_1'].to_bytes(8, 'little') +
                               mi['module_app_fw_name_2'].to_bytes(8, 'little') +
                               mi['module_app_fw_name_3'].to_bytes(8, 'little')).decode('utf-8', errors='ignore').rstrip("\x00")
                    name = fw_name
                    ver = f"{mi['module_app_ver_gen']}.{mi['module_app_ver_major']}.{mi['module_app_ver_minor']}.{mi['module_app_ver_fix']}.{mi['module_app_ver_build']} {mi['module_app_target']}"
                    build = f"{mi['module_app_build_day']:02d}/{mi['module_app_build_month']:02d}/{mi['module_app_build_year']:04d} {mi['module_app_build_hour']:02d}:{mi['module_app_build_min']:02d}"
                    crc = f"{mi['module_app_crc']:08X}"
                    hw = (mi['module_app_hw_name_1'].to_bytes(8, 'little') +
                          mi['module_app_hw_name_2'].to_bytes(8, 'little')).decode('utf-8', errors='ignore').rstrip("\x00")
                except Exception:
                    pass
            if 'MODULE_INFO_EX' in info:
                mix = info['MODULE_INFO_EX']
                try:
                    ip = socket.inet_ntoa(mix['module_ip_addr'].to_bytes(4, 'big'))
                except Exception:
                    pass
            if name and hw:
                print("|-------------------------------------------------------------------|")
                print(f"Device Name   | {name}")
                print(f"Device HW     | {hw}")
                print(f"Device Version| {ver} | {build} | {crc}")
                print(f"MAC Address   | {mac}")
                if ip:
                    print(f"IP Address    | {ip}")

def main():
    iface = os.environ.get("SDRIG_IFACE", "enp2s0")
    stream_id_raw = os.environ.get("SDRIG_STREAM_ID", "1")
    dbc_path = os.environ.get("SDRIG_DBC", "soda_xil_fd.dbc")
    try:
        stream_id = int(stream_id_raw, 0)
    except ValueError:
        stream_id = 1

    print(f"Using IFACE={iface}, STREAM_ID={stream_id}, DBC={dbc_path}")
    handler = CanMessageHandler(dbc_path)
    mgr = AvtpCanManager(iface=iface, stream_id=stream_id)

    # start receiving with robust callback
    mgr.start_receiving(handler.parse_avtp_frame)

    # discovery CAN brief (PGN request 0x0400FFFE on bus 0)
    bus0_can_id = 0x0400FFFE
    data = bytes(b'\x1f\x00\x00\x00\x00\x00\x00\x00')

    # initial burst to "wake up" devices
    for _ in range(5):
        try:
            mgr.send_can_message(0, bus0_can_id, data, True, False)
        except Exception:
            pass
        time.sleep(0.05)

    try:
        while True:
            try:
                mgr.send_can_message(0, bus0_can_id, data, True, False)
            except Exception:
                pass
            handler.print_devices()
            time.sleep(1.0)
    except KeyboardInterrupt:
        mgr.stop_receiving()

if __name__ == "__main__":
    main()
