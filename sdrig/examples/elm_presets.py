
import asyncio, logging
from sdrig.transport.avtp_acf import AvtpAcfClient, AvtpConfig
from sdrig.transport.dbc_codec import DbCodec
from sdrig.modules.elm import Elm, ElmCfg

logging.basicConfig(level=logging.INFO)

async def main():
    dbc = DbCodec("soda_xil_fd.dbc")
    avtp = AvtpAcfClient(AvtpConfig(iface="eth0", stream_id=1))
    await avtp.start()

    elm = Elm(ElmCfg(dbc=dbc, avtp=avtp))
    await elm.start()

    await elm.set_op_mode(vo_enable=[1], vi_enable=[1], co_enable=[1], ci_enable=[1], dout_enable=[2])
    await elm.set_voltage_out({1: 5.0})
    await elm.set_current_out({1: 2.0})
    await elm.set_dout({2: 1})

    vi = await elm.read_voltage_in_once(timeout=2.0)
    print("VOLTAGE_IN:", vi)
    ci = await elm.read_current_in_once(timeout=2.0)
    print("CUR_ELM_IN:", ci)

    try:
        while True:
            await asyncio.sleep(1.0)
    except KeyboardInterrupt:
        await elm.stop()
        await avtp.stop()

if __name__ == "__main__":
    asyncio.run(main())
