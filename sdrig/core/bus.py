
from __future__ import annotations
import asyncio, logging
from typing import List, Tuple
from ..transport.avtp_acf import AvtpAcfClient
from ..transport.j1939 import CTRL_BUS_ID

log = logging.getLogger(__name__)

class BatchSender:
    """Aggregate multiple CAN Brief blocks into a single AVTP frame when possible."""
    def __init__(self, avtp: AvtpAcfClient, max_payload: int = 64):
        self.avtp = avtp
        self.max_payload = max_payload
        self._q: asyncio.Queue[Tuple[int, bytes]] = asyncio.Queue()
        self._task = None
        self._running = False

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except Exception:
                pass
            self._task = None

    async def send(self, can_id: int, payload: bytes):
        await self._q.put((can_id, payload))

    async def _loop(self):
        while self._running:
            try:
                can_id, payload = await self._q.get()
            except asyncio.CancelledError:
                break

            # collect small burst for 5 ms
            blocks = [self.avtp.build_acf_can_brief(CTRL_BUS_ID, can_id, payload, eff=True)]
            size = len(blocks[0])
            try:
                start = asyncio.get_running_loop().time()
                while (asyncio.get_running_loop().time() - start) < 0.005:
                    try:
                        next_can_id, next_payload = self._q.get_nowait()
                        block = self.avtp.build_acf_can_brief(CTRL_BUS_ID, next_can_id, next_payload, eff=True)
                        if size + len(block) > self.max_payload:
                            # flush current batch
                            self.avtp.send_acf_blocks(blocks)
                            blocks = [block]
                            size = len(block)
                        else:
                            blocks.append(block)
                            size += len(block)
                    except asyncio.QueueEmpty:
                        break
                # flush remain
                self.avtp.send_acf_blocks(blocks)
            except Exception as e:
                log.debug("BatchSender error: %s", e)
