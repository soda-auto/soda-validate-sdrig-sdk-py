from __future__ import annotations
from typing import Dict, Any, Iterable, Optional

def _expand_enable_list(prefix: str, values: Optional[Iterable[int]], count: int) -> Dict[str, int]:
    res: Dict[str, int] = {}
    s = set(values or [])
    for i in range(1, count+1):
        res[f"{prefix}_{i}_enable"] = 1 if i in s else 0
    return res

class ELM:
    """ELM high-level API mirroring UIO for OP_MODE_req."""
    def __init__(self, cfg):
        self.cfg = cfg

    async def set_op_mode(
        self,
        *,
        vo_enable: Optional[Iterable[int]] = None,
        vi_enable: Optional[Iterable[int]] = None,
        co_enable: Optional[Iterable[int]] = None,
        ci_enable: Optional[Iterable[int]] = None,
        dout_enable: Optional[Iterable[int]] = None,
        pwm_mode: Optional[Dict[int, int]] = None,
    ):
        pwm_mode = pwm_mode or {}
        msg = self.cfg.dbc.db.get_message_by_name("OP_MODE_req")

        counts = {"vo": 0, "vi": 0, "co": 0, "ci": 0, "dout": 0, "pwm": 0}
        for s in msg.signals:
            for k in ["vo", "vi", "co", "ci", "dout"]:
                if s.name.startswith(f"{k}_") and s.name.endswith("_enable"):
                    try:
                        idx = int(s.name.split("_")[1])
                        counts[k] = max(counts[k], idx)
                    except Exception:
                        pass
            if s.name.startswith("pwm_") and s.name.endswith("_op_mode"):
                try:
                    idx = int(s.name.split("_")[1])
                    counts["pwm"] = max(counts["pwm"], idx)
                except Exception:
                    pass

        sigs: Dict[str, Any] = {}
        sigs.update(_expand_enable_list("vo", vo_enable, counts["vo"]))
        sigs.update(_expand_enable_list("vi", vi_enable, counts["vi"]))
        sigs.update(_expand_enable_list("co", co_enable, counts["co"]))
        sigs.update(_expand_enable_list("ci", ci_enable, counts["ci"]))
        sigs.update(_expand_enable_list("dout", dout_enable, counts["dout"]))

        for i in range(1, counts["pwm"]+1):
            sigs[f"pwm_{i}_op_mode"] = int(pwm_mode.get(i, 0))

        frame_id, payload = self.cfg.dbc.encode("OP_MODE_req", sigs)
        await self.cfg.tx.send(frame_id, payload, extended=True, can_fd=True)
