# OPF ECU - FOME firmware build

`build_fome.sh` builds FOME (https://github.com/FOME-Tech/fome-fw) for an OPF ECU board variant.
The same script runs in GitHub Actions (`.github/workflows/fome-autobuild.yml`) and locally.

## Layout

- `board-overlay/<variant>/` - board config overlaid onto FOME's `firmware/config/boards/<core48|core8>/`
  (copied from ECU_Build `config/<variant>`; that repo is private so CI cannot check it out with
  `GITHUB_TOKEN`). Add a variant by copying its ECU_Build config folder here.
- `fome_board_fixups.py` - adapts the board files to the FOME version being built; each fixup only
  applies when that FOME no longer has the feature (e.g. UART/bluetooth removed in FOME #730).
- `build_fome.sh` - checkout, toolchain, build, verify, package, base tune.
- `patches/*.patch` - applied (after the firmware build) so the FOME simulator compiles the
  board's `board_configuration.cpp` and applies its defaults (0001), and uses the same values as the
  real ECU where FOME's simulator differs (0002); used only for base-tune generation.
- `stage_board_branch.sh` - copies a build into `fome/` of a board-branch checkout (used by CI).
- `ts_read_page.py` - TunerStudio binary-protocol client (TCP simulator or serial ECU): signature + page.
- `ini2msq.py` - page image + ini -> TunerStudio `.msq`, with a re-encode verification.
- `setup_m32_sysroot.sh` - no-sudo alternative to `gcc-multilib` for the 32-bit simulator build.
- `base-tune/<variant>/` - committed reference base tunes (every build regenerates `<variant>_base_tune.msq`).

## Local build

```
scripts/fome/build_fome.sh                                    # latest FOME release, core48_21
scripts/fome/build_fome.sh --ref release_260501_02 --variant core48_21
scripts/fome/build_fome.sh --ref master --overlay-dir /path/to/ECU_Build/config --work ~/fome-work
scripts/fome/build_fome.sh --resolve-only                     # print the latest FOME release tag
```

Needs git, curl, python3, java 17, make, xxd, binutils, zip, mtools, dosfstools (mkfs.fat), and for the
base tune a 32-bit capable gcc (`gcc-multilib g++-multilib`) - or, without sudo,
`eval $(scripts/fome/setup_m32_sysroot.sh)` once and keep `M32_SYSROOT` exported. `BASE_TUNE=0` skips it. Output (default
`~/.cache/opf-fome-build/out/<variant>`): `fome.bin` (OpenBLT + FOME, flash at 0x08000000 via DFU),
`fome_update.srec` (update through OpenBLT), `fome_bl.srec`, `fome.elf`, `fome_tunerstudio.ini`,
`fome_console.zip` (FOME console, `CONSOLE=0` skips it),
`<variant>_base_tune.msq` + `.bin` (board defaults as a TunerStudio tune), `SHA256SUMS`,
`build-info.txt`, `release-notes.md`.

## What the script does

1. Resolves the FOME ref (default: latest release) and does a depth-1 fetch of exactly that ref.
2. Initialises only the submodules the firmware needs (no googletest / luaformatter / hex2dfu, and no
   1.9 GB build-tools repo - see 3).
3. Reads the toolchain FOME pins in `firmware/use_arm_gcc.mk` (currently `arm-gnu-toolchain-11.3.rel1`)
   and downloads that exact ARM release once (cached, sha256-verified: pinned hash, else ARM's `.sha256asc`). `USE_BUNDLED_TOOLCHAIN=1` uses FOME's submodule.
4. Builds the Java code generators only when `java_tools` changed (tree-hash stamp).
5. Overlays the board config, applies fixups, runs FOME's `compile_<board>.sh` with `make -j$(nproc)`.
6. Fails if the TunerStudio signature in `fome.bin` differs from the generated ini.
7. Base tune: applies `patches/`, builds the FOME simulator with the board config
   (`SIM_WITH_BOARD_DEFAULTS`), starts it, reads the default config page over the TunerStudio protocol
   (signature must equal the firmware ini), converts it to `<variant>_base_tune.msq` and verifies the
   msq re-encodes to the identical bytes. Then writes SHA256 sums and release notes.

## CI (`.github/workflows/fome-autobuild.yml`)

Same structure as the rusEFI workflow (`scripts/rusefi/`):
- schedule every 6h: resolves the latest FOME release; if `fome/build-info.txt` on the board branch
  (`core48_21`) has a different FOME commit, builds and commits the result there. GitHub runs schedules
  only from the default branch (`main`), so this workflow file must be on `main` for the cron to fire.
- workflow_dispatch: `ref` (default `latest`), `variant` (default `core48_21`), `dry_run` (default true =
  artifacts only), `force` (rebuild/commit even if the board branch already has that commit).
- push to `master-fome-grok` touching `scripts/fome/**` or the workflow: validation build, artifacts only.
- Publishing = a normal commit on the board branch touching only `fome/` (`fome_firmware.bin`,
  `fome_tunerstudio.ini`, `fome_console.zip` - the names the branch readme links to - plus
  `fome_update.srec`, `fome_base_tune.msq`, `build-info.txt`, `SHA256SUMS`); rebase+retry if the branch
  moved, never force-pushed. `rusefi/`, `speeduino/` and `readme.md` are left alone.
- GitHub releases (`fome-<tag>-<variant>`) are off; set repo variable `FOME_CREATE_RELEASES=true` to enable.
- Only `GITHUB_TOKEN` is used (`contents: read`; `contents: write` for the build job's publish steps).

## Reproducibility

`SOURCE_DATE_EPOCH` (default: FOME commit time) pins `__DATE__/__TIME__`, the zip/gzip shims make the
embedded USB ini image deterministic, and `TZ=UTC` is forced. Two builds of the same FOME commit on the
same UTC day give identical `fome.bin`, `.srec`, `.ini` and base tune on any machine (`fome.elf` differs only
in debug-info paths of the work directory); across days only the date inside FOME's
TunerStudio signature (upstream behaviour) changes.
