
import asyncio, logging
from sdrig.transport.avtp_acf import AvtpAcfClient, AvtpConfig
from sdrig.transport.dbc_codec import DbCodec
from sdrig.modules.uio import Uio, UioCfg

logging.basicConfig(level=logging.INFO)

async def main():
    dbc = DbCodec("soda_xil_fd.dbc")
    avtp = AvtpAcfClient(AvtpConfig(iface="eth0", stream_id=1))
    await avtp.start()

    uio = Uio(UioCfg(dbc=dbc, avtp=avtp))
    await uio.start()

    await uio.set_op_mode(vo_enable=[1], vi_enable=[1])
    await uio.switch_output(vo=[1])  # depends on DBC mapping
    await uio.set_voltage_out({1: 12.0})
    vi = await uio.read_voltage_in_once(timeout=2.0)
    print("VOLTAGE_IN:", vi)

    await uio.set_op_mode(pwm_out=[3], icu_in=[3])
    await uio.set_pwm_out({3: {'voltage':5.0, 'frequency':1000, 'duty':33.3}})
    icu = await uio.read_pwm_in_once(timeout=2.0)
    print("PWM_IN:", icu)

    await uio.set_op_mode(clo_out=[4], cli_in=[4])
    await uio.set_current_out({4: 12.0})
    cli = await uio.read_current_in_once(timeout=2.0)
    print("CUR_LOOP_IN:", cli)

    try:
        while True:
            await asyncio.sleep(1.0)
    except KeyboardInterrupt:
        await uio.stop()
        await avtp.stop()

if __name__ == "__main__":
    asyncio.run(main())
