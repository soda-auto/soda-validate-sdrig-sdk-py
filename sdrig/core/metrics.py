
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import Dict

@dataclass
class Metrics:
    tx_frames: int = 0
    rx_frames: int = 0
    tx_bytes: int = 0
    rx_bytes: int = 0
    tx_errors: int = 0
    rx_errors: int = 0
    last_seen: Dict[str, float] = field(default_factory=dict)  # message_name -> ts
    rtt_hist: Dict[str, float] = field(default_factory=dict)   # message_name -> last RTT

    def mark_tx(self, size: int):
        self.tx_frames += 1
        self.tx_bytes += size

    def mark_rx(self, size: int):
        self.rx_frames += 1
        self.rx_bytes += size

    def mark_error_tx(self):
        self.tx_errors += 1

    def mark_error_rx(self):
        self.rx_errors += 1

    def seen(self, message_name: str):
        self.last_seen[message_name] = time.time()

    def age(self, message_name: str) -> float:
        t = self.last_seen.get(message_name)
        if t is None:
            return float("inf")
        return max(0.0, time.time() - t)
