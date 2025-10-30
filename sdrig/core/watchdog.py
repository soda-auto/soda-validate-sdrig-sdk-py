
from __future__ import annotations
import asyncio, logging, time
from typing import Callable, Dict, Optional
from .metrics import Metrics

log = logging.getLogger(__name__)

class Watchdog:
    def __init__(self, metrics: Metrics):
        self.metrics = metrics
        self._tasks = []
        self._running = False

    async def start(self, checks: Dict[str, float], on_stale: Optional[Callable[[str, float], None]] = None):
        """checks: message_name -> max silence seconds"""
        if self._running:
            return
        self._running = True

        async def _loop():
            while self._running:
                for name, max_silence in checks.items():
                    age = self.metrics.age(name)
                    if age > max_silence:
                        if on_stale:
                            try:
                                on_stale(name, age)
                            except Exception:
                                pass
                        else:
                            log.warning("Watchdog: %s stale (%.1fs)", name, age)
                await asyncio.sleep(1.0)

        self._tasks.append(asyncio.create_task(_loop()))

    async def stop(self):
        self._running = False
        for t in self._tasks:
            t.cancel()
        self._tasks.clear()
