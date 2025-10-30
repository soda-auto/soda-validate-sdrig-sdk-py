
from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Optional, List
from .avtp_acf import AvtpAcfClient, iter_acf_blocks, parse_can_brief

# Flag bits as used in AvtpAcfClient.build_acf_can_brief()
FLAG_TS_VALID = 0x20
FLAG_EFF      = 0x08  # 29-bit ID
FLAG_BRS      = 0x04  # CAN FD bitrate switch
FLAG_FDF      = 0x02  # CAN FD frame

@dataclass
class CanFrame:
    bus: int
    can_id: int
    data: bytes
    eff: bool = True
    fdf: bool = False
    brs: bool = False
    ts_valid: bool = False

class CanIO:
    """High-level CAN/CAN-FD send/receive on top of AvtpAcfClient."""
    def __init__(self, avtp: AvtpAcfClient):
        self.includes: list[CanFilter] = []
        self.excludes: list[CanFilter] = []
        self.avtp = avtp
        self._handlers: List[Callable[[CanFrame], None]] = []
        self._started = False

    def on_frame(self, cb: Callable[[CanFrame], None]):
        """Register receive callback (after filters)."""
        self._handlers.append(cb)

    async def start(self):
        if self._started:
            return
        self._started = True
        self.avtp.subscribe(self._on_payload)

    def _on_payload(self, src_mac: bytes, acf_payload: bytes):
        for block in iter_acf_blocks(acf_payload):
            try:
                bus_id, can_id, flags, data, msg_type = parse_can_brief(block)
            except Exception:
                continue
            f = CanFrame(
                bus=bus_id,
                can_id=can_id,
                data=data,
                eff=bool(flags & FLAG_EFF),
                fdf=bool(flags & FLAG_FDF),
                brs=bool(flags & FLAG_BRS),
                ts_valid=bool(flags & FLAG_TS_VALID),
            )
            if not self._passes(f):
                continue
            for h in list(self._handlers):
                try:
                    h(f)
                except Exception:
                    pass

    # -------- Send helpers --------
    def send(self, frame: CanFrame):
        self.avtp.send_can(frame.bus, frame.can_id, frame.data, eff=frame.eff, fdf=frame.fdf, brs=frame.brs)

    def send_cl(self, bus: int, can_id: int, data: bytes, eff: Optional[bool] = None):
        """Send classic CAN (<=8 bytes). If eff is None, auto based on can_id."""
        if eff is None:
            eff = bool(can_id > 0x7FF)
        self.avtp.send_can(bus, can_id, data[:8], eff=eff, fdf=False, brs=False)

    def send_fd(self, bus: int, can_id: int, data: bytes, brs: bool = True, eff: Optional[bool] = None):
        """Send CAN FD (<=64 bytes). If eff is None, auto based on can_id."""
        if eff is None:
            eff = bool(can_id > 0x7FF)
        self.avtp.send_can(bus, can_id, data[:64], eff=eff, fdf=True, brs=brs)


    # -------- Filters API --------
    def add_include(self, flt: CanFilter):
        self.includes.append(flt)

    def add_exclude(self, flt: CanFilter):
        self.excludes.append(flt)

    def clear_filters(self):
        self.includes.clear()
        self.excludes.clear()

    def _passes(self, f: CanFrame) -> bool:
        inc_ok = True if not self.includes else any(fl.match(f) for fl in self.includes)
        if not inc_ok:
            return False
        exc_ok = not any(fl.match(f) for fl in self.excludes)
        return exc_ok

    def add_id_mask_filter(self, bus: int, id_match: int, id_mask: int, *, fd_only: bool | None = None, eff: bool | None = None, include=True):
        flt = CanFilter(buses={bus}, id_match=id_match, id_mask=id_mask, fdf=fd_only, eff=eff)
        (self.add_include if include else self.add_exclude)(flt)
        return flt

    # -------- PCAP helpers (AVTP-level capture) --------
    def enable_pcap(self, filepath: str):
        \"\"\"Enable AVTP PCAP capture for all CAN traffic.\"\"\"
        self.avtp.enable_pcap(filepath)

    def flush_pcap(self):
        self.avtp.flush_pcap()
