
import asyncio, logging
from sdrig.transport.avtp_acf import AvtpAcfClient, AvtpConfig
from sdrig.transport.dbc_codec import DbCodec
from sdrig.modules.mux import Mux, MuxCfg
from sdrig.core.presets import Preset, Step, apply_preset

logging.basicConfig(level=logging.INFO)

async def main():
    dbc = DbCodec("soda_xil_fd.dbc")
    avtp = AvtpAcfClient(AvtpConfig(iface="eth0", stream_id=1))
    await avtp.start()
    mux = Mux(MuxCfg(dbc=dbc, avtp=avtp))
    await mux.start()

    preset = Preset(steps=[
        Step("CAN_INFO_req", {"can1_speed":500000, "can1_speed_fd":2000000}, keepalive=True, key="speed"),
        Step("CAN_MUX_req", {"can_mux_int_can1_en":1, "can_mux_ext_can1_out":3}, keepalive=True, key="mux"),
    ], interval=2.0, key_prefix="mux:can1")

    await apply_preset(mux, preset)

    try:
        while True:
            await asyncio.sleep(1.0)
    except KeyboardInterrupt:
        await mux.stop(); await avtp.stop()

if __name__ == "__main__":
    asyncio.run(main())
