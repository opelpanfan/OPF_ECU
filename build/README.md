# OPF ECU - FOME firmware build

`build_fome.sh` builds FOME (https://github.com/FOME-Tech/fome-fw) for an OPF ECU board variant.
The same script runs in GitHub Actions (`.github/workflows/fome-autobuild.yml`) and locally.

## Layout

- `boards/<variant>/` - board config overlaid onto FOME's `firmware/config/boards/<core48|core8>/`
  (copied from ECU_Build `config/<variant>`; that repo is private so CI cannot check it out with
  `GITHUB_TOKEN`). Add a variant by copying its ECU_Build config folder here.
- `fome_board_fixups.py` - adapts the board files to the FOME version being built; each fixup only
  applies when that FOME no longer has the feature (e.g. UART/bluetooth removed in FOME #730).
- `build_fome.sh` - checkout, toolchain, build, verify, package.

## Local build

```
build/build_fome.sh                               # latest FOME release, core48_21
build/build_fome.sh -r release_260501_02 -b core48_21
build/build_fome.sh -r master -c /path/to/ECU_Build/config -b core48_21 -w ~/fome-work
```

Needs git, curl, python3, java 17, make, xxd, binutils, zip, mtools, dosfstools (mkfs.fat). No sudo needed for the build itself. Output (default
`~/.cache/opf-fome-build/out/<variant>`): `fome.bin` (OpenBLT + FOME, flash at 0x08000000 via DFU),
`fome_update.srec` (update through OpenBLT), `fome_bl.srec`, `fome.elf`, `fome_tunerstudio.ini`,
`SHA256SUMS`, `build-info.txt`, `release-notes.md`.

## What the script does

1. Resolves the FOME ref (default: latest release) and does a depth-1 fetch of exactly that ref.
2. Initialises only the submodules the firmware needs (no googletest / luaformatter / hex2dfu, and no
   1.9 GB build-tools repo - see 3).
3. Reads the toolchain FOME pins in `firmware/use_arm_gcc.mk` (currently `arm-gnu-toolchain-11.3.rel1`)
   and downloads that exact ARM release once (cached). `USE_BUNDLED_TOOLCHAIN=1` uses FOME's submodule.
4. Builds the Java code generators only when `java_tools` changed (tree-hash stamp).
5. Overlays the board config, applies fixups, runs FOME's `compile_<board>.sh` with `make -j$(nproc)`.
6. Fails if the TunerStudio signature in `fome.bin` differs from the generated ini; writes SHA256 sums.

## CI

- daily schedule: if FOME has a release without a matching `fome-<tag>-<variant>` release here,
  build and publish it (only runs from the default branch).
- workflow_dispatch: any ref/variants; `publish_release` is off by default.
- push to `master-fome-grok` touching build files: validation build, artifacts only.
