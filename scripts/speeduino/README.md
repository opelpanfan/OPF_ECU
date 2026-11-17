# Speeduino builds for OPF boards

Same layout as `scripts/rusefi/` and `scripts/fome/`:

| Path | Purpose |
|---|---|
| `build_speeduino.sh` | the one build script, used locally and by CI with the same arguments |
| `board-overlay/<variant>/board.json` | board definition (pins, board id, PlatformIO env, board branch); `legacy/` = old ECU_Build ini |
| `common/` | OPF sources copied into the Speeduino tree (`opf_board.{h,cpp}`, `src/LPS22HH`, `src/LPS25HB`) |
| `base-tune/` | seed tune for the generated base tune |
| `readme_section.py` | generates/guards the `<!-- SPEEDUINO:START/END -->` section of the board branch readme |

```
scripts/speeduino/build_speeduino.sh [--ref latest|<tag>] [--variant core48_21[,..]] [--out out] [--work DIR] [-j N] [--keep]
```

goes from nothing to flashable artifacts (a bare positional argument is the same as `--ref`):

1. shallow-clones `noisymime/speeduino` at the ref (default `latest` = latest GitHub release; resolved via the
   API, or the `releases/latest` redirect when the API is rate limited),
2. generates the OPF board support on that clean checkout (embedded Python, anchored edits only):
   - `case <board_id>:` in `setPinMapping()` (init.cpp) from `board-overlay/<variant>/board.json`, and forces
     that board id (OPF firmware only runs on OPF hardware),
   - `[env:opf_<variant>]` in platformio.ini, derived from upstream's `[env:black_F407VE]`
     (`board = black_f407zg`, `platform` pinned via `$STM32_PLATFORM`, default `platformio/ststm32@19.5.0`),
   - OPF extras behind `-DOPF_BOARD`: W25Qxx SPI flash EEPROM on SPI2 (CS PA15), SD logging off,
     onboard LPS22HH/LPS25HB I2C baro, CAN2 (`Can1`, PB5/PB6), status LEDs,
   - TunerStudio ini: board name at `pinLayouts[<board_id>]` plus fuel/ign output counts and RTC flag,
3. builds with PlatformIO (`pio run -j N`, default `nproc`) and writes `out/<variant>/`:
   `speeduino_firmware.bin` (.hex/.elf), `speeduino_tunerstudio.ini`, `base-map.msq`,
   `opf-<variant>-speeduino-<tag>.patch` (the generated changes as one reviewable patch), `build-info.json`
   and `SHA256SUMS` (verified with `sha256sum -c`),
4. fails if the ini signature differs from the firmware signature (or either cannot be read),
5. removes the temporary upstream checkout and build trees from the work dir on exit (also on failure);
   `--keep` keeps them. Small logs (`pio-<variant>.log`) and the generated patch stay in the work dir.

If upstream changes code around an anchor, the build stops with `PATCH CONFLICT in <file>: ...`; it never
guesses. Fix the anchor in the embedded Python in `build_speeduino.sh`.

## Base tune
`base-map.msq` is generated per variant for every build from the generated ini: values come from the seed tune
`base-tune/seed-base-tune-speeduino-202207.msq` (the upstream Speeduino 202207 base tune used by the old OPF
builds) when the constant still exists with the same shape, a valid option and range; else from the ini
`defaultValue`; else a safe in-range fallback. `pinLayout` is set to the board layout. Generated with
TunerStudio settings `mcu_stm32` + `CELSIUS` (AFR, not lambda). Counts and the fallback list are in
`build-info.json` -> `base_tune`. Review the tune before you start an engine with it.

## Adding a board (e.g. core8)
Create `board-overlay/<variant>/board.json` (copy core48_21: `board_id`, `ts_layout_name`, `pio_board`, `pins`,
`unused_pin_vars`, `defines`, `base_tune`, and `firmware_branch`/`firmware_dir`/`firmware_readme` for the
board branch). Every board is a separate firmware build, so different boards may reuse board id 59.

## CI (`.github/workflows/speeduino-autobuild.yml`)
Jobs: `plan` -> `build` (matrix over variants) -> `release` -> `firmware-branch`. Only `GITHUB_TOKEN` is used
(`contents: write` in the release and board-branch jobs). Pins: Python 3.12, PlatformIO 6.2.0 (pip),
ststm32 19.5.0 (gcc 12.3.1); `~/.platformio` and pip are cached; checkouts are shallow.

- **schedule** (every 6h): latest upstream release; builds and publishes each variant whose release
  `speeduino-<tag>-<variant>` is missing (or whose board branch / readme section is outdated).
- **workflow_dispatch**: `ref` (default `latest`), `variant` (default `core48_21`, comma list or `all`),
  `dry_run` (default `true`: build + artifacts only, no release, no board-branch commit; the planned board
  branch change is printed), `force` (build even if already published; an existing release is never modified).
- **push** to `master-speeduino-grok` (scripts/speeduino/**, the workflow): always builds every variant
  (validation) and publishes what is missing: creates the release only if it does not exist and commits to
  the board branch only if something would change. A rebuild of an already published tag is a no-op.

schedule and workflow_dispatch only fire for workflows on the repository's DEFAULT branch (main). While this
workflow lives only on `master-speeduino-grok`, new upstream releases are built by the next push to that branch
(an empty commit is enough). Option, for Benas to decide: copy the workflow file to main and add
`ref: master-speeduino-grok` to its `actions/checkout` steps that check out the build scripts (plan, build,
firmware-branch `src`), so the cron/dispatch runs use the scripts from this branch.

### Board branch (`firmware-branch` job)
Commits `speeduino_firmware.bin`, `speeduino_firmware.hex`, `speeduino_tunerstudio.ini`, `base-map.msq`
(+ `SHA256SUMS`, `build-info.json`) to `<firmware_branch>:<firmware_dir>/` from board.json
(core48_21 -> `core48_21:speeduino/`, the paths the branch readme links to). `build-info.json`/`SHA256SUMS`
are only rewritten when the firmware files change, so rebuilding the same tag commits nothing. Plain commit +
push, never force; a rejected push is retried up to 5 times with fetch + rebase.

Readme: when board.json sets `firmware_readme` (core48_21: `readme.md`), `readme_section.py` regenerates the
text between `<!-- SPEEDUINO:START -->` and `<!-- SPEEDUINO:END -->`. The visible text is exactly the original
hand-written block (`## Speeduino Firmware`, the "Right click" hint and the two download badges for
`speeduino_firmware.bin` and `speeduino_tunerstudio.ini`); an invisible stamp comment (Speeduino tag + format
version `FMT`) lets the plan job detect an outdated section. Never edit inside the markers by hand. If the
markers are missing, the existing `## Speeduino ...` block is wrapped in them; without such a block the section
is appended at the end. FOME:START/END, RUSEFI:START/END and all other text stay byte-for-byte unchanged
(line endings preserved). Bump `FMT` when the generated text changes.

Guard (before the commit, after every rebase and after the push): any path outside `<firmware_dir>/` fails the
job, except the readme, which is allowed only if old and new are identical once the SPEEDUINO section is
stripped from both.

## Local requirements
`git`, `python3`, `curl`, `sha256sum`, PlatformIO (`pip install platformio==6.2.0`). Set `PLATFORMIO_VERSION`
to enforce the version. Flashing is not part of the script: use STM32 DFU (`0483:df11`).
