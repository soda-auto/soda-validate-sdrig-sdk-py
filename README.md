# SDR Py Project
## INSTALLATION
```
pip install -r requirements.txt --user
```

## ABOUT
Python code for SDRig control via **AVTP ACF-CAN** frames

## how to use
```
sudo docker build -t sdr-py-avtp .
sudo docker run --rm -it --network host --cap-add NET_ADMIN --cap-add NET_RAW --env-file .env -v "$PWD/":/app --entrypoint /bin/bash sdr-py-avtp
```
in container setup the env vars end exec commands
```
export SDRIG_IFACE=enp2s0.3900
export SDRIG_STREAM_ID=1
export SDRIG_DBC=/app/soda_xil_fd.dbc
export PYTHONPATH=/app
python scripts/devices_list.py
python scripts/can_send.py --msg-id 0x18FF50E5 --ext --dst 66:6a:db:b3:06:27
```