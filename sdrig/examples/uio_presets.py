import asyncio
from sdrig.config import load_config
from sdrig.modules.uio import UIO

async def main():
    cfg = load_config()
    uio = UIO(cfg)
    # enable VO1, VI1; others default to 0; PWM1 mode=1
    await uio.set_op_mode(vo_enable=[1], vi_enable=[1], pwm_mode={1:1})
    print("UIO: OP_MODE set")

if __name__ == "__main__":
    asyncio.run(main())
