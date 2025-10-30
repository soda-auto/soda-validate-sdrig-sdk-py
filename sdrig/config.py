# sdrig/config.py
from dataclasses import dataclass
from typing import Optional, Union, Tuple, Dict, Any
import os

import cantools
from sdrig.transport.avtp_acf import AvtpConfig
from sdrig.transport.dbc_codec import DbcCodec  # есть в SDK, но без from_file

# ---- совместимый shim поверх cantools ---------------------------------------
class _CantoolsShim:
    def __init__(self, db: cantools.database.Database):
        self._db = db

    def encode(self, message_name: str, signals: Dict[str, Any]) -> Tuple[int, bytes]:
        msg = self._db.get_message_by_name(message_name)
        data = msg.encode(signals)  # bytearray
        return msg.frame_id, bytes(data)

    def decode(self, frame_id: int, data: bytes) -> Dict[str, Any]:
        msg = self._db.get_message_by_frame_id(frame_id)
        return msg.decode(bytes(data))

# ---- helpers ----------------------------------------------------------------
@dataclass
class SdrigConfig:
    iface: str
    stream_id: Optional[int]
    dbc: object         # DbcCodec или _CantoolsShim
    avtp: AvtpConfig

def _env(name: str, *, required: bool = False, default: Optional[str] = None) -> Optional[str]:
    v = os.environ.get(name, default)
    if required and (v is None or v == ""):
        raise RuntimeError(f"Environment variable {name} is required")
    return v

def _parse_stream_id(v: Optional[Union[str, int]]) -> Optional[int]:
    if v is None or v == "":
        return None
    if isinstance(v, int):
        return v
    s = v.strip()
    base = 16 if s.lower().startswith("0x") else 10
    return int(s, base)

def _make_dbc(dbc_path: str):
    # 1) если есть DbcCodec.from_file
    if hasattr(DbcCodec, "from_file"):
        return DbcCodec.from_file(dbc_path)  # новые версии
    # 2) попробуем конструктор с путём
    try:
        return DbcCodec(dbc_path)  # некоторые версии принимают путь в __init__
    except Exception:
        pass
    # 3) соберём shim из cantools
    db = cantools.database.load_file(dbc_path)
    return _CantoolsShim(db)

def load_config(
    dbc_path: Optional[str] = None,
    iface: Optional[str] = None,
    stream_id: Optional[Union[str, int]] = None,
) -> SdrigConfig:
    iface = iface or _env("SDRIG_IFACE", required=True)
    if stream_id is None:
        stream_id = _env("SDRIG_STREAM_ID")
    stream_id_int = _parse_stream_id(stream_id)

    dbc_path = dbc_path or _env("SDRIG_DBC", required=True)
    dbc = _make_dbc(dbc_path)

    avtp = AvtpConfig(iface=iface, stream_id=stream_id_int)
    return SdrigConfig(iface=iface, stream_id=stream_id_int, dbc=dbc, avtp=avtp)
