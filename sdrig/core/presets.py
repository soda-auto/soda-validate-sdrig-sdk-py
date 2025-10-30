
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List
from .base import BaseModule

@dataclass
class Step:
    message: str
    signals: Dict[str, Any]
    keepalive: bool = True   # include into periodic keeper
    key: str = ""            # optional key suffix

@dataclass
class Preset:
    steps: List[Step]
    interval: float = 2.5
    key_prefix: str = ""

async def apply_preset(module: BaseModule, preset: Preset):
    """Compile and run preset: send once then keepalive."""
    # send once all steps in order
    for i, step in enumerate(preset.steps):
        frame_id, payload = module.cfg.dbc.encode(step.message, step.signals)
        module.cfg.avtp.send_can(0, (frame_id & 0xFFFFFF00) | 0xFE, payload, eff=True)

    # keepalive
    for i, step in enumerate(preset.steps):
        if not step.keepalive:
            continue
        key = f"{preset.key_prefix}:{i}:{step.key}" if step.key else f"{preset.key_prefix}:{i}"
        def make_builder(s=step):
            def _builder():
                fid, pl = module.cfg.dbc.encode(s.message, s.signals)
                return ((fid & 0xFFFFFF00) | 0xFE, pl)
            return _builder
        module.keeper.ensure(key, preset.interval, make_builder())
