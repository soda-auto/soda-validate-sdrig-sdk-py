# AvtpCanManager.py
from scapy.all import sendp, sniff, Ether, get_if_hwaddr
from typing import Callable, Optional
import threading
from scapy.config import conf
import time
import os
from AVTP import AVTPPacket

class AvtpCanManager:
    def __init__(self, iface: str, stream_id: Optional[int] = None):
        self.iface = iface
        self.stream_id = stream_id
        self.sequence_number = 0
        self.running = False
        self.recv_thread: Optional[threading.Thread] = None
        self.recv_callback: Optional[Callable[[int, bytes], None]] = None
        # важно: чтобы scapy не брал loopback/дефолт, явно укажем интерфейс
        conf.iface = self.iface

    def _get_src_mac(self) -> Optional[str]:
        # 1) явная переменная окружения — пригодится для CI/контейнеров
        forced = os.getenv("SDRIG_SRC_MAC")
        if forced and forced != "00:00:00:00:00:00":
            return forced

        # 2) пробуем MAC интерфейса
        try:
            mac = get_if_hwaddr(self.iface)
            if mac and mac != "00:00:00:00:00:00":
                return mac
        except Exception:
            pass

        # 3) VLAN fallback: берем MAC у родителя (enp2s0.3900 -> enp2s0)
        if "." in self.iface:
            parent = self.iface.split(".", 1)[0]
            try:
                mac = get_if_hwaddr(parent)
                if mac and mac != "00:00:00:00:00:00":
                    return mac
            except Exception:
                pass
            # 4) на всякий случай читаем sysfs
            for cand in (self.iface, parent):
                try:
                    with open(f"/sys/class/net/{cand}/address") as f:
                        mac = f.read().strip()
                        if mac and mac != "00:00:00:00:00:00":
                            return mac
                except Exception:
                    pass
        return None

    def build_packet(self, can_id: int, msg_id: int, data: bytes, extended_id: bool, can_fd: bool) -> Ether:
        data = data[:64]
        payload_len = len(data)

        # ACF: header(2) + flags(1) + can_id(1) + msg_id(4) + data(N)
        acf_payload_length = 2 + 1 + 1 + 4 + payload_len
        quadlets = acf_payload_length // 4

        message_type = 0b010  # CAN Brief
        acf_header = (message_type << 9) | (quadlets & 0x1FFF)

        avtp_payload_length = acf_payload_length

        # <-- фикс: явно задаём src MAC
        src_mac = self._get_src_mac()
        eth = Ether(dst="ff:ff:ff:ff:ff:ff", type=0x22F0)
        if src_mac:
            eth.src = src_mac

        pkt = eth / AVTPPacket()
        avtp = pkt[AVTPPacket]
        avtp.subtype = 0x82
        avtp.version_cd = 0x80
        avtp.sequence_number = self.sequence_number
        avtp.stream_id_high = (self.stream_id >> 32) & 0xFFFFFFFF
        avtp.stream_id_low = self.stream_id & 0xFFFFFFFF
        avtp.data_length = avtp_payload_length

        avtp.acf_header = acf_header
        avtp.flags = 0x00
        if extended_id:
            avtp.flags |= 0x08
        if can_fd:
            avtp.flags |= 0x02
        avtp.can_id = can_id
        avtp.msg_id = msg_id

        if len(data) < 64:
            data += b'\x00' * (64 - len(data))
        avtp.data = data

        self.sequence_number = (self.sequence_number + 1) % 256
        return pkt

    def send_can_message(self, can_id: int, msg_id: int, data: bytes, extended_id: bool, can_fd: bool):
        pkt = self.build_packet(can_id, msg_id, data, extended_id, can_fd)
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
                # Никогда не падаем из-за одного кривого кадра
                pass

        sniff(iface=self.iface, prn=process, store=0, stop_filter=lambda x: not self.running)

