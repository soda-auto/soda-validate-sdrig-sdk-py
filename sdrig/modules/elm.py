
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from ..core.base import BaseModule, ModuleCommonCfg

@dataclass
class ElmCfg(ModuleCommonCfg):
    pass

class Elm(BaseModule):
    async def set_op_mode(self, **modes):
        frame_id, payload = self.cfg.dbc.encode("OP_MODE_req", modes)
        self.cfg.avtp.send_can(0, (frame_id & 0xFFFFFF00) | 0xFE, payload, eff=True)

    async def set_voltage_out(self, values: Dict[int, float]):
        sigs = {f"voltage_o_{ch}_value": float(v) for ch, v in values.items()}
        frame_id, payload = self.cfg.dbc.encode("VOLTAGE_OUT_VAL_req", sigs)
        self.cfg.avtp.send_can(0, (frame_id & 0xFFFFFF00) | 0xFE, payload, eff=True)

    async def set_current_out(self, values: Dict[int, float]):
        sigs = {f"cur_elm_o_{ch}_value": float(v) for ch, v in values.items()}
        frame_id, payload = self.cfg.dbc.encode("CUR_ELM_OUT_VAL_req", sigs)
        self.cfg.avtp.send_can(0, (frame_id & 0xFFFFFF00) | 0xFE, payload, eff=True)

    async def set_dout(self, state: Dict[int, int]):
        sigs = {f"switch_dout_{ch}": int(v) for ch, v in state.items()}
        frame_id, payload = self.cfg.dbc.encode("SWITCH_DOUT_req", sigs)
        self.cfg.avtp.send_can(0, (frame_id & 0xFFFFFF00) | 0xFE, payload, eff=True)

    async def read_voltage_in_once(self, timeout=1.0) -> dict:
        return await self.wait_for("VOLTAGE_IN_ans", timeout=timeout)

    async def read_current_in_once(self, timeout=1.0) -> dict:
        return await self.wait_for("CUR_ELM_IN_VAL_ans", timeout=timeout)

    async def read_temp_in_once(self, timeout=1.0) -> dict:
        return await self.wait_for("TEMP_ELM_IN_ans", timeout=timeout)

    async def read_voltage_out_once(self, timeout=1.0) -> dict:
        return await self.wait_for("VOLTAGE_OUT_VAL_ans", timeout=timeout)

    async def read_current_out_once(self, timeout=1.0) -> dict:
        return await self.wait_for("CUR_ELM_OUT_VAL_ans", timeout=timeout)

    async def read_dout_once(self, timeout=1.0) -> dict:
        return await self.wait_for("SWITCH_DOUT_ans", timeout=timeout)
