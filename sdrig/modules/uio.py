
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict
from ..core.base import BaseModule, ModuleCommonCfg

@dataclass
class UioCfg(ModuleCommonCfg):
    pass

class Uio(BaseModule):
    async def set_op_mode(self, **modes):
        frame_id, payload = self.cfg.dbc.encode("OP_MODE_req", modes)
        self.cfg.avtp.send_can(0, (frame_id & 0xFFFFFF00) | 0xFE, payload, eff=True)

    async def switch_output(self, **sel):
        frame_id, payload = self.cfg.dbc.encode("SWITCH_OUTPUT_req", sel)
        self.cfg.avtp.send_can(0, (frame_id & 0xFFFFFF00) | 0xFE, payload, eff=True)

    async def set_voltage_out(self, values: Dict[int, float]):
        sigs = {f"voltage_o_{ch}_value": float(v) for ch, v in values.items()}
        frame_id, payload = self.cfg.dbc.encode("VOLTAGE_OUT_VAL_req", sigs)
        self.cfg.avtp.send_can(0, (frame_id & 0xFFFFFF00) | 0xFE, payload, eff=True)

    async def set_pwm_out(self, values: Dict[int, dict]):
        sigs = {}
        for ch, cfg in values.items():
            sigs[f"pwm_o_{ch}_voltage"] = float(cfg.get("voltage", 5.0))
            sigs[f"pwm_o_{ch}_frequency"] = float(cfg.get("frequency", 1000))
            sigs[f"pwm_o_{ch}_duty"] = float(cfg.get("duty", 50.0))
        frame_id, payload = self.cfg.dbc.encode("PWM_OUT_VAL_req", sigs)
        self.cfg.avtp.send_can(0, (frame_id & 0xFFFFFF00) | 0xFE, payload, eff=True)

    async def set_current_out(self, values_ma: Dict[int, float]):
        sigs = {f"cur_ma_o_{ch}_value": float(v) for ch, v in values_ma.items()}
        frame_id, payload = self.cfg.dbc.encode("CUR_LOOP_OUT_VAL_req", sigs)
        self.cfg.avtp.send_can(0, (frame_id & 0xFFFFFF00) | 0xFE, payload, eff=True)

    async def read_voltage_in_once(self, timeout=1.0) -> dict:
        return await self.wait_for("VOLTAGE_IN_ans", timeout=timeout)

    async def read_pwm_in_once(self, timeout=1.0) -> dict:
        return await self.wait_for("PWM_IN_ans", timeout=timeout)

    async def read_current_in_once(self, timeout=1.0) -> dict:
        return await self.wait_for("CUR_LOOP_IN_VAL_ans", timeout=timeout)

    async def read_pwm_out_once(self, timeout=1.0) -> dict:
        return await self.wait_for("PWM_OUT_VAL_ans", timeout=timeout)

    async def read_voltage_out_once(self, timeout=1.0) -> dict:
        return await self.wait_for("VOLTAGE_OUT_VAL_ans", timeout=timeout)

    async def read_current_out_once(self, timeout=1.0) -> dict:
        return await self.wait_for("CUR_LOOP_OUT_VAL_ans", timeout=timeout)
