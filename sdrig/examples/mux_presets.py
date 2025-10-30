
import asyncio, logging
from sdrig.transport.avtp_acf import AvtpAcfClient, AvtpConfig
from sdrig.transport.dbc_codec import DbCodec
from sdrig.core.base import ModuleCommonCfg
from sdrig.modules.mux import Mux, MuxCfg

logging.basicConfig(level=logging.INFO)

async def main():
    dbc = DbCodec("soda_xil_fd.dbc")
    avtp = AvtpAcfClient(AvtpConfig(iface="eth0", stream_id=1))
    await avtp.start()

    mux = Mux(MuxCfg(dbc=dbc, avtp=avtp))
    await mux.start()

    await mux.set_can_speeds({1:500000}, speeds_fd={1:2000000})
    await mux.set_mux_relays(int_enable={1:1}, ext_out={1:3})
    await mux.lin_config([{'id':0x12, 'enable':1, 'dir_transmit':0, 'cst_classic':1, 'length':8}])

    try:
        while True:
            await asyncio.sleep(1.0)
    except KeyboardInterrupt:
        await mux.stop()
        await avtp.stop()

if __name__ == "__main__":
    asyncio.run(main())
