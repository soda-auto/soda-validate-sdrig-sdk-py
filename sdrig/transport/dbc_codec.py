
from __future__ import annotations
import cantools

class DbCodec:
    def __init__(self, dbc_path: str):
        self.db = cantools.database.load_file(dbc_path)

    def encode(self, message_name: str, signals: dict) -> tuple[int, bytes]:
        msg = self.db.get_message_by_name(message_name)
        data = msg.encode(signals)
        return msg.frame_id, data

    def decode(self, can_id: int, data: bytes):
        try:
            msg = self.db.get_message_by_frame_id(can_id)
            return msg.name, msg.decode(data)
        except Exception:
            return None
