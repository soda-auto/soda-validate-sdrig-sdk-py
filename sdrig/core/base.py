
from __future__ import annotations
import asyncio, logging
from dataclasses import dataclass
from .metrics import Metrics
from .bus import BatchSender
from .watchdog import Watchdog
from typing import Dict, Callable, List
from ..transport.avtp_acf import AvtpAcfClient, iter_acf_blocks, parse_can_brief
from ..transport.dbc_codec import DbCodec
from ..transport.j1939 import CTRL_BUS_ID, wildcard_sa

log = logging.getLogger(__name__)

@dataclass
class ModuleCommonCfg:
    dbc: DbCodec
    avtp: AvtpAcfClient
    pgn_module_info_req: int = 0x000FF
    heartbeat_period_s: float = 5.0

class BaseModule:
    def __init__(self, cfg: ModuleCommonCfg):
        self.metrics = Metrics()
        self.watchdog = Watchdog(self.metrics)
        self.batch = BatchSender(cfg.avtp)
        self._rx_sizes = 0
        self.cfg = cfg
        self._tasks: List[asyncio.Task] = []
        self._running = False
        self._subscribers: Dict[str, List[Callable[[dict], None]]] = {}
        self._futures: Dict[str, List[asyncio.Future]] = {}

    async def start(self):
        if self._running:
            return
        self._running = True
        self.cfg.avtp.subscribe(self._on_avtp_payload)
        await self.batch.start()
        # metrics hooks
        self.cfg.avtp.on_rx.append(lambda raw: self.metrics.mark_rx(len(raw)))
        self.cfg.avtp.on_tx.append(lambda raw: self.metrics.mark_tx(len(raw)))
        self._tasks.append(asyncio.create_task(self._heartbeat_loop()))

    async def stop(self):
        self._running = False
        for t in self._tasks:
            t.cancel()
        self._tasks.clear()

    async def _heartbeat_loop(self):
        while self._running:
            try:
                frame_id, data = self.cfg.dbc.encode("MODULE_INFO_req", {"module_info_base_req": 1})
                can_id = wildcard_sa(frame_id)
                await self.batch.send(can_id, data)
            except Exception as e:
                log.debug("heartbeat error: %s", e)
            await asyncio.sleep(self.cfg.heartbeat_period_s)

    def _on_avtp_payload(self, src_mac: bytes, acf_payload: bytes):
        for block in iter_acf_blocks(acf_payload):
            try:
                bus_id, can_id, flags, data, msg_type = parse_can_brief(block)
            except Exception:
                continue
            if bus_id != 0:
                continue
            dec = self.cfg.dbc.decode(can_id, data)
            if not dec:
                continue
            name, signals = dec
            self.metrics.seen(name)
            for cb in self._subscribers.get(name, []):
                try:
                    cb(signals)
                except Exception:
                    pass
            futs = self._futures.get(name, [])
            for fut in futs:
                if not fut.done():
                    fut.set_result(signals)
            self._futures[name] = [f for f in futs if not f.done()]

    def on(self, message_name: str, cb: Callable[[dict], None]):
        self._subscribers.setdefault(message_name, []).append(cb)

    async def wait_for(self, message_name: str, timeout: float = 1.0) -> dict:
        fut = asyncio.get_running_loop().create_future()
        self._futures.setdefault(message_name, []).append(fut)
        return await asyncio.wait_for(fut, timeout=timeout)
