
import asyncio, logging, time
from sdrig.transport.avtp_acf import AvtpAcfClient, AvtpConfig
from sdrig.transport.dbc_codec import DbCodec
from sdrig.modules.uio import Uio, UioCfg
from sdrig.core.presets import Preset, Step, apply_preset

logging.basicConfig(level=logging.INFO)

async def main():
    dbc = DbCodec("soda_xil_fd.dbc")
    avtp = AvtpAcfClient(AvtpConfig(iface="eth0", stream_id=1))
    await avtp.start()
    uio = Uio(UioCfg(dbc=dbc, avtp=avtp))
    await uio.start()

    # Simple VO preset for ch1
    preset = Preset(steps=[
        Step("OP_MODE_req", {"vo_enable":[1], "vi_enable":[1]}, keepalive=True, key="mode"),
        Step("SWITCH_OUTPUT_req", {"vo":[1]}, keepalive=True, key="switch"),
        Step("VOLTAGE_OUT_VAL_req", {"voltage_o_1_value": 12.0}, keepalive=True, key="value"),
    ], interval=2.0, key_prefix="uio:vo1")

    await apply_preset(uio, preset)

    # Start watchdog for VOLTAGE_IN_ans
    await uio.watchdog.start({"VOLTAGE_IN_ans": 4.0}, on_stale=lambda name, age: print("STALE", name, age))

    # Dump metrics each 5s
    async def reporter():
        while True:
            m = uio.metrics
            print(f"TX={m.tx_frames}/{m.tx_bytes} RX={m.rx_frames}/{m.rx_bytes} last VI age={m.age('VOLTAGE_IN_ans'):.1f}s")
            await asyncio.sleep(5.0)
    asyncio.create_task(reporter())

    try:
        while True:
            vi = await uio.read_voltage_in_once(timeout=1.0)
            print("VOLTAGE_IN:", vi)
            await asyncio.sleep(1.0)
    except KeyboardInterrupt:
        await uio.stop(); await avtp.stop()

if __name__ == "__main__":
    asyncio.run(main())
