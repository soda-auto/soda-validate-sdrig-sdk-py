import asyncio
from sdrig.config import load_config
from sdrig.modules.elm import ELM

async def main():
    cfg = load_config()
    elm = ELM(cfg)
    await elm.set_op_mode(vo_enable=[1], vi_enable=[1], co_enable=[1], ci_enable=[1], dout_enable=[2], pwm_mode={1:1})
    print("ELM: OP_MODE set")

if __name__ == "__main__":
    asyncio.run(main())
