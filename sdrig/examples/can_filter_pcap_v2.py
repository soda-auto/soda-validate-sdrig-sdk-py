
import asyncio, logging
from sdrig.transport.avtp_acf import AvtpAcfClient, AvtpConfig
from sdrig.transport.canio import CanIO, CanFrame, CanFilter
from sdrig.transport.j1939 import make_can_id_j1939

logging.basicConfig(level=logging.INFO)

async def main():
    avtp = AvtpAcfClient(AvtpConfig(iface="eth0", stream_id=1))
    avtp.enable_pcap("avtp_can.pcap")   # write AVTP frames with CAN payloads
    await avtp.start()

    can = CanIO(avtp)
    await can.start()

    # Include: only bus 2, only CAN-FD and IDs with mask 0x1FFFFF00 == 0x18FF5000 (PGN 0xFF50)
    can.add_include(CanFilter(buses={2}, fdf=True, id_mask=0x1FFFFF00, id_match=0x18FF5000))
    # Exclude: drop a specific source id if needed (example)
    # can.add_exclude(CanFilter(ids={0x18FF5000 | 0x80}))  # example

    def on_frame(f: CanFrame):
        kind = "FD" if f.fdf else "CL"
        ide  = "EFF" if f.eff else "STD"
        print(f"<- bus{f.bus} {kind}/{ide} id=0x{f.can_id:X} data={f.data.hex()}")

    can.on_frame(on_frame)

    # Send one FD frame that passes the filter (bus 2, PGN=0xFF50, SA=0x80)
    can_id_j = make_can_id_j1939(pgn=0x18FF50, sa=0x80)
    can.send_fd(bus=2, can_id=can_id_j, data=b"filtered hello", brs=True)

    try:
        while True:
            await asyncio.sleep(1.0)
    except KeyboardInterrupt:
        can.flush_pcap()
        await avtp.stop()

if __name__ == "__main__":
    asyncio.run(main())
