# Base tunes

Reference FOME base tunes (board defaults as TunerStudio `.msq`), one folder per board variant.
They are produced by `scripts/fome/build_fome.sh` (locally and in the `FOME autobuild` workflow, which
attaches `<variant>_base_tune.msq` to every build artifact/release); the copies here are snapshots
for the FOME release named in the file name.

How they are made: the FOME simulator is built with the board's `board_configuration.cpp`
(`scripts/fome/patches/*`), started, and its default configuration page is read over the
TunerStudio protocol (signature must equal the firmware's ini), then converted with
`scripts/fome/ini2msq.py` and round-trip verified. Checked against a real core48 running FOME
9f45bdeeb5: the generated page is byte-identical to the ECU's own defaults.

Board pinout, trigger and engine basics that the firmware defaults leave unset are kept per variant in
`<variant>/tune_overrides.txt` (FOME ini field = label/value, validated against the ini, duplicate pins refused)
and applied by `scripts/fome/apply_tune_overrides.py` after the simulator read; see `core48_21/PINOUT.md`.
The same script can apply them to a connected ECU (`--ecu /dev/ttyACM0 --backup DIR`, close TunerStudio first).

Open in TunerStudio with a project using the matching `fome_tunerstudio.ini`
(File > Open Tune), adjust, then burn. Not a running tune - set engine/sensor parameters first.
