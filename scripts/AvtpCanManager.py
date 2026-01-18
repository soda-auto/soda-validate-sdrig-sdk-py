from scapy.all import sendp, sniff, Ether, get_if_hwaddr  # type: ignore
from typing import Callable, Optional
import threading
from scapy.config import conf  # type: ignore
import time
from AVTP import AVTPPacket
import os


class AvtpCanManager:
    # def __init__(self, iface: str, stream_id: int):
    def __init__(self, iface: str, stream_id: Optional[int] = None):
        self.iface = iface
        self.stream_id = stream_id
        self.sequence_number = 0
        self.running = False
        self.recv_thread: Optional[threading.Thread] = None
        self.recv_callback: Optional[Callable[[int, bytes], None]] = None
        self.src_mac = self._resolve_src_mac()

    # --- minimal MAC fix helpers ---
    def _read_sys_mac(self, iface: str) -> Optional[str]:
        p = f"/sys/class/net/{iface}/address"
        try:
            if os.path.exists(p):
                mac = open(p).read().strip()
                if mac and not mac.startswith("00:00:00"):
                    return mac
        except Exception:
            pass
        return None

    def _resolve_src_mac(self) -> str:
        mac = None
        # 1) try scapy
        try:
            mac = get_if_hwaddr(self.iface)
        except Exception:
            mac = None
        if not mac or mac.startswith("00:00:00"):
            # 2) try /sys
            mac = self._read_sys_mac(self.iface)

        if (not mac or mac.startswith("00:00:00")) and "." in self.iface:
            # 3) if VLAN - get MAC from parent
            parent = self.iface.split(".", 1)[0]
            mac = self._read_sys_mac(parent) or (get_if_hwaddr(parent) if parent else None)

        if not mac or mac.startswith("00:00:00"):
            raise RuntimeError(
                f"Cannot determine valid MAC for {self.iface}. "
                f"Mount /sys/class/net into the container (ro) or run on host."
            )
        return mac

    def build_packet(self, can_id: int, msg_id: int, data: bytes, extended_id: bool, can_fd: bool, dst: str) -> Ether:

        data = data[:64]
        payload_len = len(data)

        # Quadlets = (ACF  + data) / 4
        # ACF:header(2) + flags (1) + can_id (1) + msg_id (4) + data (64)
        acf_payload_length = 2 + 1 + 1 + 4 + payload_len
        quadlets = (acf_payload_length) // 4

        # ACF Header:
        # - Message Type: 0b010 (CAN Brief)
        # - Message Length (Quadlets)
        message_type = 0b010
        acf_header = (message_type << 9) | (quadlets & 0x1FFF)

        # Total AVTP payload length (in bytes) - everything after sequence_number field
        avtp_payload_length = acf_payload_length

        # >>> Only behavior we change: set src MAC <<<
        pkt = Ether(dst=dst, src=self.src_mac, type=0x22F0) / AVTPPacket()
        avtp = pkt[AVTPPacket]

        avtp.subtype = 0x82
        avtp.version_cd = 0x80
        avtp.sequence_number = self.sequence_number
        avtp.stream_id_high = (self.stream_id >> 32) & 0xFFFFFFFF
        avtp.stream_id_low = self.stream_id & 0xFFFFFFFF
        avtp.data_length = avtp_payload_length

        avtp.acf_header = acf_header
        avtp.flags = 0x00
        # if timestamp_valid == True :
        #     avtp.flags = avtp.flags | 0x20
        if extended_id is True:
            avtp.flags = avtp.flags | 0x08
        if can_fd is True:
            avtp.flags = avtp.flags | 0x02
        avtp.can_id = can_id
        avtp.msg_id = msg_id

        # Pad data if less than 64 bytes
        if len(data) < 64:
            data += b'\x00' * (64 - len(data))
        avtp.data = data

        self.sequence_number = (self.sequence_number + 1) % 256
        return pkt

    def send_can_message(self, can_id: int, msg_id: int, data: bytes, extended_id: bool, can_fd: bool, dst: str):
        pkt = self.build_packet(can_id, msg_id, data, extended_id, can_fd, dst)
        sendp(pkt, iface=self.iface, verbose=False)

    def start_receiving(self, callback: Callable[[int, bytes], None]):
        self.recv_callback = callback
        self.running = True
        self.recv_thread = threading.Thread(target=self._recv_loop, daemon=True)
        self.recv_thread.start()

    def stop_receiving(self):
        self.running = False
        if self.recv_thread:
            self.recv_thread.join()

    def _recv_loop(self):
        conf.use_pcap = False

        def process(pkt):
            try:
                if AVTPPacket not in pkt:
                    return
                if self.stream_id is not None:
                    try:
                        if pkt[AVTPPacket].stream_id() != self.stream_id:
                            return
                    except Exception:
                        return
                if self.recv_callback:
                    self.recv_callback(bytes(pkt))
            except Exception:
                # Never crash from a single bad frame
                pass

        sniff(iface=self.iface, prn=process, store=0, stop_filter=lambda x: not self.running)


def on_can_message(pkt):
    avtp = pkt[AVTPPacket]
    can_id = avtp.can_id
    msg_id = avtp.msg_id
    data = bytes(pkt[AVTPPacket].payload)
    print(f"Rcv CAN# {can_id}: MSG ID=0x{msg_id:X}, data={data.hex()}")


if __name__ == "__main__":
    manager = AvtpCanManager(iface="lo", stream_id=1)
    manager.start_receiving(on_can_message)

    manager.send_can_message(0x01, 0x123, b'\x11\x22\x33\x44\x55\x66\x77\x88', False, True)

    try:
        while True:
            manager.send_can_message(0x01, 0x123, b'\x11\x22\x33\x44\x55\x66\x77\x88', False, True)
            time.sleep(1)
    except KeyboardInterrupt:
        manager.stop_receiving()
