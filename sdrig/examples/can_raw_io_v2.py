
import asyncio, logging
from sdrig.transport.avtp_acf import AvtpAcfClient, AvtpConfig
from sdrig.transport.canio import CanIO, CanFrame
from sdrig.transport.j1939 import make_can_id_j1939

logging.basicConfig(level=logging.INFO)

async def main():
    avtp = AvtpAcfClient(AvtpConfig(iface="eth0", stream_id=1))
    await avtp.start()

    can = CanIO(avtp)
    await can.start()

    # Subscribe to all CAN buses; filter in callback
    def on_frame(f: CanFrame):
        if f.bus == 2:  # only bus 2 in this example
            kind = "FD" if f.fdf else "CL"
            ide = "EFF" if f.eff else "STD"
            print(f"<- bus{f.bus} {kind}/{ide} id=0x{f.can_id:X} data={f.data.hex()}")

    can.on_frame(on_frame)

    # Send classic CAN STD ID on bus 2
    can.send_cl(bus=2, can_id=0x123, data=bytes.fromhex("0102030405060708"))

    # Send CAN FD EFF (J1939) on bus 5
    can_id_j = make_can_id_j1939(pgn=0x18FF50, sa=0x80)  # example PGN/SA
    can.send_fd(bus=5, can_id=can_id_j, data=b"hello over canfd", brs=True)

    try:
        while True:
            await asyncio.sleep(1.0)
    except KeyboardInterrupt:
        pass

    await avtp.stop()

if __name__ == "__main__":
    asyncio.run(main())
