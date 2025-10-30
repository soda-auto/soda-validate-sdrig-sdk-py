
import asyncio, logging
from sdrig.transport.avtp_acf import AvtpAcfClient, AvtpConfig
from sdrig.transport.dbc_codec import DbCodec
from sdrig.core.base import ModuleCommonCfg, BaseModule

logging.basicConfig(level=logging.INFO)

async def main():
    dbc = DbCodec("soda_xil_fd.dbc")
    avtp = AvtpAcfClient(AvtpConfig(iface="eth0", stream_id=1))
    avtp.enable_pcap("traffic.pcap")
    await avtp.start()
    base = BaseModule(ModuleCommonCfg(dbc=dbc, avtp=avtp))
    await base.start()

    try:
        while True:
            await asyncio.sleep(1.0)
    except KeyboardInterrupt:
        avtp.flush_pcap()
        await base.stop(); await avtp.stop()

if __name__ == "__main__":
    asyncio.run(main())
