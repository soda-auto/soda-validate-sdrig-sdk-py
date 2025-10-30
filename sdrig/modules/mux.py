from __future__ import annotations
from typing import Dict, Any, Optional

class Mux:
    """MUX high-level API.

    set_can_speeds accepts sparse dicts:
      speeds={1:500000} speeds_fd={1:2000000}
    The method introspects the DBC message "CAN_INFO_req" and auto-fills
    all required fields (can{N}_speed and can{N}_speed_fd) with 0 if missing.
    """
    def __init__(self, cfg):
        self.cfg = cfg

    async def set_can_speeds(self, speeds: Optional[Dict[int,int]] = None, *, speeds_fd: Optional[Dict[int,int]] = None):
        speeds = speeds or {}
        speeds_fd = speeds_fd or {}

        # Build signals dynamically from DBC message definition
        msg = self.cfg.dbc.db.get_message_by_name("CAN_INFO_req")
        sigs: Dict[str, Any] = {}

        for s in msg.signals:
            name = s.name
            # Match patterns can{idx}_speed and can{idx}_speed_fd
            if name.startswith("can") and name.endswith("_speed"):
                try:
                    idx = int(name[3:-6])  # between 'can' and '_speed'
                    sigs[name] = int(speeds.get(idx, 0))
                except Exception:
                    pass
            elif name.startswith("can") and name.endswith("_speed_fd"):
                try:
                    idx = int(name[3:-9])  # between 'can' and '_speed_fd'
                    sigs[name] = int(speeds_fd.get(idx, 0))
                except Exception:
                    pass

        frame_id, payload = self.cfg.dbc.encode("CAN_INFO_req", sigs)
        await self.cfg.tx.send(frame_id, payload, extended=True, can_fd=True)
