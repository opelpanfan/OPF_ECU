# rusEFI auto-build for the OPF core48 board

* `build_rusefi_core48.sh` – builds rusEFI for a core48 variant (default `core48_21`). Used by CI and locally.
* `rusefi_board_fixups.py` – adapts ECU_Build `board_configuration.cpp` to the current rusEFI board API.
* `../../.github/workflows/rusefi-core48-autobuild.yml` – polls rusefi/rusefi releases and builds new ones.

## Local build

```sh
# needs: git curl make python3 zip 7z mcopy mkfs.fat xxd binutils, Java 17+,
#        gcc-multilib g++-multilib (or docker) for the base tune
scripts/rusefi/build_rusefi_core48.sh                           # latest stable rusEFI release, core48_21
scripts/rusefi/build_rusefi_core48.sh --ref 2026-10-21          # a nightly tag
scripts/rusefi/build_rusefi_core48.sh --ref master --variant core48_21 --ecu-build-dir ~/Projects/ECU_Build
```

Artifacts land in `.rusefi-build/out/` (or `--out`):
`rusefi-<tag>-<variant>.{bin,hex,srec,dfu,ini,elf,build-info.txt}`, `rusefi-<tag>-<variant>-base.msq`
+ `SHA256SUMS`.

Base tune: rusEFI's own canned-tune process – the 32-bit Linux simulator is built with this board's
`board_configuration.cpp` (generated sim-only `board_common.mk` + `patches/0002`), run for 10 s to dump its
default config image, and `tune-tools` `WriteSimulatorConfiguration` turns it into an `.msq` using the
board `.ini`. The build fails if the msq signature differs from the ini. Without `gcc -m32` the simulator
is built in docker (`simulator.Dockerfile`); `--no-base-tune` skips it.

`SOURCE_DATE_EPOCH` defaults to the rusEFI commit time, so `__DATE__/__TIME__` are reproducible; the
TS signature still embeds the (London) build date, so identical `.bin`s need the same build day.
The pinned ARM toolchain (`arm-gnu-toolchain-14.2.rel1`, sha256-verified) is installed once into
`~/.cache/opf-rusefi/toolchain`.

## CI

* **Schedule** (every 6 h, default branch only): resolves the latest rusEFI release
  (stable; set repo variable `RUSEFI_TRACK=nightly` to follow nightlies), and builds only if
  release `rusefi-<tag>-<variant>` does not exist in this repo yet; then publishes that release.
* **workflow_dispatch**: inputs `ref` (default `latest`), `variant` (default `core48_21`),
  `dry_run` (default **true** = artifacts only, no release), `force`.
* **push** to `master-rusefi-grok` touching these files: validation build, never publishes.
* Board sources: `opelpanfan/ECU_Build` is private and `GITHUB_TOKEN` cannot read it, so all
  customizations are committed here and applied automatically to a clean upstream checkout:
  * `board-overlay/<variant>/` – `ECU_Build/config/<variant>` with `board_configuration.cpp` already
    ported to the current rusEFI board API (copied to `firmware/config/boards/core8/`).
  * `patches/*.patch` – changes to upstream rusEFI files (`git apply`), e.g. gradle `networkTimeout`.
  * `rusefi_board_fixups.py` – same port done programmatically (no-op on the overlay; used for raw
    ECU_Build sources via `--ecu-build-dir`).
* TS signature: `rusEFI <branch>.<YYYY.MM.DD London build date>.core8.<hash>`; branch = ref name
  (`master` for commit shas, override with `--signature-branch`).

## Board branch publishing

After a successful **non-dry-run** build (scheduled new release, or dispatch with `dry_run=false`) the
workflow commits the firmware into `rusefi/` of the OPF_ECU board branch named like the variant
(`core48_21`) and pushes it with `GITHUB_TOKEN` (normal push; on non-fast-forward it fetches, rebases
and retries up to 5 times; never forces). Only `rusefi/` is touched (`fome/`, `speeduino/` and the
top-level `readme.md` belong to other workflows). Dry runs and push-validation builds only stage the
files and print the planned diff.

Layout (mirrors the existing branch: flat `rusefi/`, fixed names):

```
rusefi/rusefi_firmware.bin      rusefi/rusefi_tunerstudio.ini   rusefi/rusefi_console.zip   (existing names)
rusefi/rusefi_firmware.hex      rusefi/rusefi_firmware.srec     rusefi/rusefi_firmware.dfu
rusefi/rusefi_base_tune.msq     rusefi/rusefi_build_info.txt    rusefi/SHA256SUMS
```

Locally: `--publish-branch core48_21 [--publish-dry-run] [--publish-dir DIR]` (off by default).

## Changes vs. ECU_Build `compile_rusefi.sh` / `core48_21.yml`

1. GCC 12.3.Rel1 -> pinned Arm GNU Toolchain 14.2.Rel1 (what rusEFI CI uses), Java 11 -> 17.
2. Extra host tools: `7zip`, `mtools`, `dosfstools`, `xxd` (rusEFI RAM-disk image).
3. Shallow single-ref fetch of rusEFI + only needed submodules (adds `ext/magic_enum`, `ext/rusefi-gha`).
4. No `git pull/reset` into the work tree, no commit/push of outputs, no interactive-pinout step.
5. `gradlew` moved to repo root; console jar is optional (`--with-console`).
6. Connector yaml: doc-only keys `pin_name`/`alternative1`/`alternative2` stripped (rejected by PinoutLogic).
7. `board_configuration.cpp` (`board-overlay/`): `setBoardConfigOverrides`/`setBoardDefaultConfiguration` registered via
   `setup_custom_board_overrides()`; `strncpy(config->luaScript, ...)` -> `setLuaScript(...)`.
8. Build via `BOARD_DIR=config/boards/core8 bin/compile.sh config/boards/core8/board.env` (`make -j$(nproc)`).
9. `.dfu` generated with `hex2dfu` (upstream only creates it in bundle mode); `SHA256SUMS`.
10. gradle wrapper `networkTimeout` 10000 -> 300000 (`patches/0001-...`).
11. Base tune `.msq` via simulator (`patches/0002` makes the simulator's `setup_custom_board_overrides` weak).
12. Build fails if the TunerStudio signature in the firmware/header differs from the generated `.ini`.

## Verification (2026-10-21)

Fresh clone of this branch, `build_rusefi_core48.sh --ref f9115629c6a1f75a2bd325c3cc447a8971c81746`:
signature `rusEFI master.2026.10.21.core8.3847534957` and `.ini` identical to the manual local build;
`.bin` identical except the 5-byte `__TIME__` string (now pinned via `SOURCE_DATE_EPOCH`).
