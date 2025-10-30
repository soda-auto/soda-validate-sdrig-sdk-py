
# sdrig Python SDK (draft)

Asyncio-based SDK for SODA SDRig over AVTP + ACF-CAN.

## Requirements
- Python 3.10+
- `scapy`, `cantools`
- `AVTP.py` available in `PYTHONPATH` (the one you already have).

## Quick start
```
python -m sdrig.examples.list_devices
python -m sdrig.examples.mux_presets
python -m sdrig.examples.uio_presets
python -m sdrig.examples.elm_presets
```


## v2 features
- **Metrics**: TX/RX frames & bytes, last-seen per message, simple RTT hooks.
- **Watchdog**: alert on stale `*_ans` messages (e.g., `VOLTAGE_IN_ans` > 4s).
- **Batch sender**: bundles multiple ACF blocks into one AVTP frame when possible.
- **PCAP capture**: `enable_pcap()` + `flush_pcap()`.
- **DSL Presets**: declaratively define steps; see `examples/*_preset_dsl_v2.py`.

Run:
```
python -m sdrig.examples.uio_preset_dsl_v2
python -m sdrig.examples.mux_preset_dsl_v2
python -m sdrig.examples.pcap_capture_v2
```
