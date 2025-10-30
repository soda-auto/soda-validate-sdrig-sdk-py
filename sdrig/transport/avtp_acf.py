
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional, Iterable, Tuple, List
import asyncio, struct, logging
from scapy.layers.l2 import Ether
from scapy.all import sendp, sniff
from AVTP import AVTPPacket, AVTP_ETHERTYPE  # Provided by user env

log = logging.getLogger(__name__)

@dataclass
class AvtpConfig:
    iface: str
    stream_id: int
    dst_mac: str = "ff:ff:ff:ff:ff:ff"

class AvtpAcfClient:
    """AVTP client for ACF-CAN 'CAN Brief' messages (single or bundled)."""
    def __init__(self, cfg: AvtpConfig):
        self.on_rx = []  # callbacks(pkt_bytes)
        self.on_tx = []  # callbacks(pkt_bytes)
        self._pcap_path = None
        self._pcap_buf = []
        self.cfg = cfg
        self._seq = 0
        self._rx_task: Optional[asyncio.Task] = None
        self._stopped = asyncio.Event()
        self._subscribers: List[Callable[[bytes, bytes], None]] = []  # (src_mac_bytes, acf_payload)

    def subscribe(self, cb: Callable[[bytes, bytes], None]) -> None:
        self._subscribers.append(cb)

    def _build_packet(self, acf_payload: bytes) -> Ether:
        pkt = Ether(dst=self.cfg.dst_mac, type=AVTP_ETHERTYPE) / AVTPPacket()
        avtp = pkt[AVTPPacket]
        avtp.subtype = 0x82   # Non Time Synchronous Control Format
        avtp.version_cd = 0x80
        avtp.sequence_number = self._seq
        avtp.set_stream_id(self.cfg.stream_id)
        avtp.data_length = len(acf_payload)

        # align to 4 and pad to 64 for current AVTP.py structure
        pad_len = (-len(acf_payload)) % 4
        payload = acf_payload + (b"\x00" * pad_len)
        if len(payload) < 64:
            payload = payload + b"\x00" * (64 - len(payload))
        avtp.acf_header = 0
        avtp.data = payload[:64]

        self._seq = (self._seq + 1) & 0xFF
        return pkt

    @staticmethod
    def build_acf_can_brief(bus_id: int, msg_id: int, data: bytes, *, eff=True, fdf=False, brs=False, ts_valid=False) -> bytes:
        msg_type = 0b010  # CAN Brief
        flags = (0x00 |
                 (0x20 if ts_valid else 0) |
                 (0x08 if eff else 0) |
                 (0x04 if brs else 0) |
                 (0x02 if fdf else 0))
        data = data[:64]
        header_bytes = 2 + 1 + 1 + 4
        quadlets = (header_bytes + len(data) + 3) // 4
        header = ((msg_type & 0x7F) << 9) | (quadlets & 0x1FF)
        b = bytearray()
        b += struct.pack("!H", header)
        b += struct.pack("!B", flags)
        b += struct.pack("!B", bus_id & 0x1F)
        b += struct.pack("!I", msg_id)
        b += data
        while len(b) % 4:
            b += b"\x00"
        return bytes(b)

    @staticmethod
    def bundle_acf(blocks: Iterable[bytes]) -> bytes:
        return b"".join(blocks)

    def send_can(self, bus_id: int, msg_id: int, data: bytes, *, eff=True, fdf=False, brs=False):
        acf = self.build_acf_can_brief(bus_id, msg_id, data, eff=eff, fdf=fdf, brs=brs)
        pkt = self._build_packet(acf)
        raw = bytes(pkt)
        try:
            for cb in self.on_tx:
                cb(raw)
        except Exception:
            pass
        sendp(pkt, iface=self.cfg.iface, verbose=False)
        if self._pcap_path is not None:
            self._pcap_buf.append(pkt)

    def send_acf_blocks(self, blocks: List[bytes]):
        payload = self.bundle_acf(blocks)
        pkt = self._build_packet(payload)
        raw = bytes(pkt)
        try:
            for cb in self.on_tx:
                cb(raw)
        except Exception:
            pass
        sendp(pkt, iface=self.cfg.iface, verbose=False)
        if self._pcap_path is not None:
            self._pcap_buf.append(pkt)

    async def start(self):
        self._stopped.clear()

        def _process(pkt):
            if AVTPPacket not in pkt:
                return
            av = pkt[AVTPPacket]
            if av.stream_id() != self.cfg.stream_id:
                return
            raw = bytes(pkt)
            if len(raw) < 26:
                return
            data_length = ((raw[15] & 0x07) << 8) | (raw[16] & 0xFF)
            start = 14 + 12  # Ethernet(14) + AVTP(12)
            acf = raw[start : start + data_length]
            src_mac = raw[6:12]
            try:
                for cb in self.on_rx:
                    cb(raw)
            except Exception:
                pass
            for cb in list(self._subscribers):
                try:
                    cb(src_mac, acf)
                except Exception:
                    pass

        def _sniff():
            sniff(iface=self.cfg.iface,
                  store=False,
                  prn=_process,
                  filter="ether proto 0x22f0",
                  stop_filter=lambda _: self._stopped.is_set())

        self._rx_task = asyncio.create_task(asyncio.to_thread(_sniff))

    async def stop(self):
        self._stopped.set()
        if self._rx_task:
            await self._rx_task

def iter_acf_blocks(acf_payload: bytes) -> Iterable[bytes]:
    off = 0
    n = len(acf_payload)
    while off + 2 <= n:
        header = struct.unpack_from("!H", acf_payload, off)[0]
        quadlets = header & 0x1FF
        length = quadlets * 4
        if length <= 0 or off + length > n:
            break
        yield acf_payload[off : off + length]
        off += length

def parse_can_brief(block: bytes) -> Tuple[int, int, int, bytes, int]:
    if len(block) < 8:
        raise ValueError("ACF block too small")
    header = struct.unpack_from("!H", block, 0)[0]
    msg_type = (header >> 9) & 0x7F
    flags = block[2]
    bus_id = block[3] & 0x1F
    can_id = ((block[4] & 0x1F) << 24) | (block[5] << 16) | (block[6] << 8) | (block[7])
    data = block[8:]
    return bus_id, can_id, flags, data, msg_type


    def enable_pcap(self, path: str):
        """Enable pcap buffering; call flush_pcap() to write file."""
        self._pcap_path = path
        self._pcap_buf = []

    def flush_pcap(self):
        if not self._pcap_path or not self._pcap_buf:
            return
        try:
            from scapy.utils import wrpcap
            wrpcap(self._pcap_path, self._pcap_buf)
            self._pcap_buf = []
        except Exception:
            pass
