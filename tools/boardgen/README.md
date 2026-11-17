# board.yaml format and generator

One YAML file describes a custom ECU (MCU, connector pinout, outputs, sensors,
CAN, disabled features, docs). This generator turns it into rusEFI and FOME
board overlays plus a board manual.

OPF33 is the reference board: `config/opf33/board.yaml`.

```
python3 tools/boardgen/generate_board.py config/opf33/board.yaml
```

Requires Python 3 and PyYAML.

## What it writes

| Output | Purpose |
| --- | --- |
| `config/<id>/generated/rusefi/` | rusEFI `board_configuration.cpp`, `board.mk`, `prepend.txt`, `board.env` |
| `config/<id>/generated/fome/` | FOME `board_configuration.cpp`, `board.mk`, `prepend.txt`, `compile_<id>.sh` |
| `config/<id>/generated/README.md` | Board manual (V1.1 pinout, release download buttons) |
| `config/<id>/readme.md` | Same manual; used as GitHub Release notes |

It does **not** generate `board.h` (STM32 pin mux stays hand-written) and it
does **not** overwrite the hand-written `config/<id>/board_configuration.cpp`
or `config/<id>_fome/*`. CI still builds those known-good fallbacks. Compare
and adopt the generated overlays when they have been reviewed.

## Schema (OPF33 example)

Top-level keys in `config/opf33/board.yaml`:

- **board** - `id`, `name`, `hardware_revision`, `mcu`, `cpu` (`ARCH_STM32F4`), `author`, `family`
- **firmware.rusefi** - `overlay_as` (directory name under rusEFI `config/boards/`, `core8` for OPF33), `short_board_name`, `firmware_id`, `hook_api` (`setup_custom_board_overrides`), `lua_api` (`setLuaScript`)
- **firmware.fome** - `overlay_as` (`opf33`), `short_board_name`, `hook_api` (`setBoardDefaultConfiguration`), `lua_api` (`config_luaScript`), `use_openblt`
- **firmware.default_engine_type**, **firmware.ram_unused_size**
- **features** - injector/coil/low-side counts, VR/Hall, analogues, CAN, on-board MAP/wideband/baro/SD, flags for DBW/EGT/stepper/knock
- **analog** - `input_divider` (1.56), `vbatt_divider` (7.34), `adc_vcc` (3.3)
- **leds**, **sd_card**, **serial**, **baro**, **can**
- **outputs** - `injectors[]`, `ignition[]`, `fuel_pump`, `fan`, `idle_solenoid`, `boost`, `tacho` (STM32 names like `PD13`)
- **sensors** - `clt` / `iat` / `tps` / `map` / `afr` / `vbatt` with `pin`, `adc`, optional `bias_ohms`, `type`, `ego`
- **trigger** - `type` (`TT_TOOTHED_WHEEL_60_2`), primary/secondary pins and jumpers
- **disabled** - features left unassigned (`etb`, `egt`, `stepper`, `knock`, `can2`)
- **lua** - default Lua script body
- **connector.pins** - the 33-pin V1.1 map (`pin`, `silk`, `net`, `mcu`, `function`, `note`, optional `alt_mcu`, `pullup_ohms`, `via`)
- **docs.release_links** - rolling tags (`opf33-rusefi-latest`, `opf33-fome-latest`) and asset names
- **docs.images** - PCB TOP/BACK and Hall/VR setup image URLs
- **docs.notes** - manual footnotes

rusEFI and FOME hook APIs differ on purpose. The generator emits current rusEFI
overrides (`setup_custom_board_overrides` + `setLuaScript`) and the older FOME
hooks (`setBoardDefaultConfiguration` + `strncpy(config->luaScript, ...)`). Do
not "port" FOME to `setLuaScript` at the pinned FOME revision.

## Adding another board later

1. Copy `config/opf33/board.yaml` to `config/<id>/board.yaml` and edit the pin map.
2. Keep a hand-written `board.h`.
3. Run the generator.
4. Add a workflow that overlays the board (or the generated files, once reviewed) and publishes unique + rolling `latest` release tags.
5. Do not mass-port legacy `config/*` folders until this format is accepted.

Releases stay on private `opelpanfan/ECU_Build` for now. Download URLs require a
GitHub login. This tool does not push to `opelpanfan/OPF_ECU` or change
repository visibility.
