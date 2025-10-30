import asyncio
import os
from sdrig.config import load_config
from sdrig.modules.mux import Mux

async def main():
    cfg = load_config()
    mux = Mux(cfg)
    # Example: only bus #1 provided; the rest auto-filled with 0
    await mux.set_can_speeds({1: 500_000}, speeds_fd={1: 2_000_000})
    print("MUX: CAN speeds applied")

if __name__ == "__main__":
    asyncio.run(main())
