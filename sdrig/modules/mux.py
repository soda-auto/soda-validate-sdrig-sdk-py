
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, List, Optional
from ..core.base import BaseModule, ModuleCommonCfg
from ..transport.j1939 import CTRL_BUS_ID, WILDCARD_SA

@dataclass
class MuxCfg(ModuleCommonCfg):
    pgn_can_info_req: int = 0x021FF
    pgn_can_mux_req: int  = 0x028FF
    pgn_lin_cfg_req: int  = 0x040FF
    pgn_lin_set_req: int  = 0x042FF

class Mux(BaseModule):
    async def set_can_speeds(self, speeds: Dict[int, int], speeds_fd: Optional[Dict[int, int]] = None):
        sigs = {}
        for ch, br in speeds.items():
            sigs[f"can{ch}_speed"] = int(br)
        if speeds_fd:
            for ch, br in speeds_fd.items():
                sigs[f"can{ch}_speed_fd"] = int(br)
        frame_id, payload = self.cfg.dbc.encode("CAN_INFO_req", sigs)
        self.cfg.avtp.send_can(CTRL_BUS_ID, (frame_id & 0xFFFFFF00) | WILDCARD_SA, payload, eff=True)

    async def set_mux_relays(self, int_enable: Optional[Dict[int, int]] = None, ext_out: Optional[Dict[int, int]] = None):
        sigs = {}
        if int_enable:
            for ch, en in int_enable.items():
                sigs[f"can_mux_int_can{ch}_en"] = int(en)
        if ext_out:
            for ch, out in ext_out.items():
                sigs[f"can_mux_ext_can{ch}_out"] = int(out)
        frame_id, payload = self.cfg.dbc.encode("CAN_MUX_req", sigs)
        self.cfg.avtp.send_can(CTRL_BUS_ID, (frame_id & 0xFFFFFF00) | WILDCARD_SA, payload, eff=True)

    async def lin_config(self, frames: List[dict]):
        sigs = {}
        for i, fr in enumerate(frames[:62]):
            sigs[f"lin_cfg_frm{i}_enable"] = 1 if fr.get("enable", True) else 0
            sigs[f"lin_cfg_frm{i}_dir_transmit"] = 1 if fr.get("dir_transmit", False) else 0
            sigs[f"lin_cfg_frm{i}_cst_classic"] = 1 if fr.get("cst_classic", True) else 0
            sigs[f"lin_cfg_frm{i}_len"] = int(fr.get("length", 8))
        frame_id, payload = self.cfg.dbc.encode("LIN_CFG_req", sigs)
        self.cfg.avtp.send_can(CTRL_BUS_ID, (frame_id & 0xFFFFFF00) | WILDCARD_SA, payload, eff=True)

    async def lin_send_frame(self, frame_id: int, data: bytes):
        d = bytes(data[:8]) + b"\x00" * max(0, 8 - len(data))
        frame_id_enc, payload = self.cfg.dbc.encode("LIN_FRAME_SET_req", {
            "lin_frame_id": frame_id,
            **{f"lin_frame_data{i}": d[i] for i in range(8)}
        })
        self.cfg.avtp.send_can(CTRL_BUS_ID, (frame_id_enc & 0xFFFFFF00) | WILDCARD_SA, payload, eff=True)
