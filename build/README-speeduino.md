# Speeduino builds for OPF boards

`build/build_speeduino.sh [-b core48_21] [-o out] [speeduino_tag]` goes from nothing to flashable artifacts:

1. shallow-clones the pinned `noisymime/speeduino` tag (default: latest GitHub release, or `$SPEEDUINO_TAG`),
2. generates the OPF board support on that clean checkout (embedded Python, anchored edits only):
   - `case <board_id>:` in `setPinMapping()` (init.cpp) from `build/boards/<board>/speeduino/board.json`, and
     forces that board id (OPF firmware only runs on OPF hardware),
   - `[env:opf_<board>]` in platformio.ini, derived from upstream's `[env:black_F407VE]`
     (`board = black_f407zg`, `platform` pinned via `$STM32_PLATFORM`, default `platformio/ststm32@19.5.0`),
   - OPF extras behind `-DOPF_BOARD`: W25Qxx SPI flash EEPROM on SPI2 (CS PA15), SD logging off,
     onboard LPS22HH/LPS25HB I2C baro, CAN2 (`Can1`, PB5/PB6), status LEDs
     (`build/speeduino/common/opf_board.{h,cpp}` + `src/LPS22HH`, `src/LPS25HB`),
   - TunerStudio ini: board name at `pinLayouts[<board_id>]` plus fuel/ign output counts and RTC flag;
     the upstream signature is kept, and the build fails if it differs from the firmware's,
3. builds with PlatformIO and writes `out/<board>/`:
   `speeduino_firmware.bin` (.hex/.elf), `speeduino_tunerstudio.ini`, `base-map.msq`,
   `opf-<board>-speeduino-<tag>.patch` (the generated changes as one reviewable patch), `SHA256SUMS`, `build-info.json`.

If upstream changes code around an anchor, the build stops with `PATCH CONFLICT in <file>: ...`; it never
guesses. Fix the anchor in the embedded Python in `build_speeduino.sh`.

## Base tune
`base-map.msq` is generated for every build from the generated ini: values come from the seed tune
`build/speeduino/common/seed-base-tune-speeduino-202207.msq` (the upstream Speeduino 202207 base tune
used by the old OPF builds) when the constant still exists with the same shape, a valid option and range;
else from the ini `defaultValue`; else a safe in-range fallback. `pinLayout` is set to the board layout.
Generated with TunerStudio settings `mcu_stm32` + `CELSIUS` (AFR, not lambda). Counts and the
fallback list are in `build-info.json` -> `base_tune`. Review the tune before you start an engine with it.

## Adding a board (e.g. core8)
Create `build/boards/<name>/speeduino/board.json` (copy core48_21: `board_id`, `ts_layout_name`,
`pio_board`, `pins`, `unused_pin_vars`, `defines`, `base_tune`). Every board is a separate firmware
build, so different boards may reuse board id 59.

## CI
`.github/workflows/speeduino-autobuild.yml` runs the same script and lives only on `master-speeduino-grok`.
A push to that branch touching the build files resolves the latest noisymime/speeduino release, builds
every variant, uploads the artifacts and publishes `speeduino-<tag>-<variant>` for each variant that has no
release yet (already released variants are skipped). Only `GITHUB_TOKEN` is used (`contents: write` in the
release job only). Toolchain pins: Python 3.12, PlatformIO 6.2.0, ststm32 19.5.0; `~/.platformio` and pip
are cached.

Detecting new upstream releases automatically: GitHub runs `schedule` and `workflow_dispatch` only for
workflows on the default branch (main), so on this branch alone the daily cron and the manual "Run workflow"
button never fire. Until then a new Speeduino release is built by the next push to `master-speeduino-grok`
(an empty commit is enough). Option, for Benas to decide: copy this workflow file (unchanged) to main; the daily
poll then publishes missing releases automatically, and workflow_dispatch (tag, variants, publish_release,
force) becomes available. The build files themselves can stay on this branch only if the scheduled run
checks out `master-speeduino-grok` (add `ref: master-speeduino-grok` to the checkout steps).

## Local requirements
`git`, `python3`, `curl`, `sha256sum`, PlatformIO (`pip install platformio==6.2.0`). Set `PLATFORMIO_VERSION`
to enforce the version. Flashing is not part of the script: use STM32 DFU (`0483:df11`).
