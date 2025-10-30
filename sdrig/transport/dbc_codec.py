from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Tuple
import cantools

@dataclass
class DbcCodec:
    """Thin wrapper over cantools that auto-fills required signals.

    It helps when a DBC message has many mandatory fields:
    - missing signals are filled with signal.initial if present,
    - otherwise 0 clamped to [minimum, maximum] if bounds exist.
    """
    db: cantools.database.Database

    def _fill_required(self, msg, signals: Dict[str, Any]) -> Dict[str, Any]:
        filled = dict(signals or {})
        for s in msg.signals:
            if s.name in filled:
                continue
            # Multiplexing: only fill base (non-multiplexed) or active branch if multiplexer present
            if s.is_multiplexer:
                # if user didn't provide mux selector, set to 0 by default
                if s.name not in filled:
                    filled[s.name] = 0
                continue
            # For multiplexed signals: if they have multiplexer ids and selector absent,
            # we skip — cantools will ignore inactive branches.
            if s.multiplexer_ids is not None:
                # will be encoded only if the corresponding mux value is provided;
                # otherwise we ignore silently
                continue
            # Defaulting strategy
            if getattr(s, "initial", None) is not None:
                val = s.initial
            else:
                val = 0
                if s.minimum is not None and val < s.minimum:
                    val = s.minimum
                if s.maximum is not None and val > s.maximum:
                    val = s.maximum
            filled[s.name] = val
        return filled

    def encode(self, message_name: str, signals: Dict[str, Any]) -> Tuple[int, bytes]:
        msg = self.db.get_message_by_name(message_name)
        filled = self._fill_required(msg, signals)
        data = msg.encode(filled)
        frame_id = msg.frame_id
        return frame_id, data
