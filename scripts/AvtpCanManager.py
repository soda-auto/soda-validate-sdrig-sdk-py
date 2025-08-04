from scapy.all import sendp, sniff, Ether
from typing import Callable, Optional
import threading
import time
from AVTP import AVTPPacket

class AvtpCanManager:
    def __init__(self, iface: str, stream_id: int):
        self.iface = iface
        self.stream_id = stream_id
        self.sequence_number = 0
        self.running = False
        self.recv_thread: Optional[threading.Thread] = None
        self.recv_callback: Optional[Callable[[int, bytes], None]] = None

    def build_packet(self, can_id: int, msg_id: int, data: bytes, extended_id: bool, can_fd: bool) -> Ether:
        
        data = data[:64]
        payload_len = len(data)

        # Quadlets = (ACF  + data) / 4
        # ACF:header(2) + flags (1) + can_id (1) + msg_id (4) + data (64)
        acf_payload_length = 2 + 1 + 1 + 4 + payload_len
        quadlets = (acf_payload_length ) // 4

        # ACF Header:
        # - Message Type: 0b010 (CAN Brief)
        # - Message Length (Quadlets)
        message_type = 0b010
        acf_header = (message_type << 9) | (quadlets & 0x1FFF)

        # Общая длина AVTP-пейлоада (в байтах) — всё после поля sequence_number
        avtp_payload_length = acf_payload_length  

        pkt = Ether(dst="ff:ff:ff:ff:ff:ff", type=0x22F0) / AVTPPacket()
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
        if extended_id == True :
            avtp.flags = avtp.flags | 0x08
        if can_fd == True :
            avtp.flags = avtp.flags | 0x02
        avtp.can_id = can_id
        avtp.msg_id = msg_id

        # Pad data if less than 64 bytes
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
        def process(pkt):
            if AVTPPacket not in pkt:
                return
            avtp = pkt[AVTPPacket]
            if avtp.stream_id() != self.stream_id:
                return
            
            if self.recv_callback:
                self.recv_callback(pkt)

        sniff(iface=self.iface, prn=process, stop_filter=lambda x: not self.running, store=0, filter="ether proto 0x22f0")



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