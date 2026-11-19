# OPF_ECU firmware builds (`master-grok`)

This branch is the public, single source of truth for OPF board configs and
firmware CI. It follows the existing OPF_ECU autobuild conventions
(`scripts/rusefi`, `scripts/fome`, `scripts/speeduino`, GitHub Releases,
artifacts on per-board branches) and vendors every STM32F407 `config/<board>`
folder so CI no longer needs the private ECU_Build repo.

Do not push this work to `main` or `master`. Workflows run only on a `v*` tag
push or `workflow_dispatch`. A `v*` tag builds every board and publishes
releases that do not already exist. `workflow_dispatch` is a dry run unless
`dry_run=false`.

All boards on this branch are STM32F407. Teensy is not built, and Teensy
targets are not present in the rusEFI, FOME, or Speeduino matrices.

## Layout

| Path | Role |
| --- | --- |
| `config/<board>/` | Board sources copied from ECU_Build (pin maps, `board.h`, connectors, manuals) |
| `config/opf33/board.yaml` | OPF33 V1.1 single-file description (MCU, 33-pin map, sensors, docs) |
| `config/opf33/readme.md` | Generated V1.1 manual (release notes). Not the old retitled OPF48 pinout. |
| `config/opf33_fome/` | FOME-specific OPF33 overlay (`compile_opf33.sh`, old FOME hook API) |
| `tools/boardgen/` | Generates rusEFI/FOME overlays, the manual, and `docs/<board>.html` |
| `docs/opf33.html` | Generated 33-pin V1.1 pinout page. Live on GitHub Pages only after it is on `main`. |
| `scripts/rusefi/` | Shared rusEFI build script (CI + local) |
| `scripts/fome/` | Shared FOME build script (CI + local) |
| `scripts/speeduino/` | Shared Speeduino build script (CI + local), official `speeduino/speeduino` |

CI still builds the hand-written `config/` files (known-good fallback). Generated
overlays live under `config/opf33/generated/` for review.

## Pins used for the first OPF33 builds

- rusEFI: `df128dec524d820bb767bcc503d8561ef01e258c`
- FOME: `3b772a890ae0703793b14f08822c20f34b386b8c`
- Speeduino: `202501.7` (commit `cd3d0e38d276a7bd087a9dc86fd976780539ce8f` on `speeduino/speeduino`)

`workflow_dispatch` can override `ref` (including `latest`) and `variant`.
A `v*` tag push builds every board and publishes missing releases (not a dry
run). Manual dispatch publishes only when `dry_run=false`. An existing release
is never overwritten, and release creation passes `--latest=false`.

## Local build

```sh
scripts/rusefi/build_rusefi.sh --ref df128dec524d820bb767bcc503d8561ef01e258c --variant opf33
scripts/fome/build_fome.sh --ref 3b772a890ae0703793b14f08822c20f34b386b8c --variant opf33
scripts/speeduino/build_speeduino.sh --ref 202501.7 --variant opf33
python3 tools/boardgen/generate_board.py config/opf33/board.yaml --docs-dir docs
```

## Speeduino board coverage

A Speeduino `board-overlay/<variant>/board.json` is required to build a board.
Default matrix variants are every overlay present (currently `opf33` and
`core48_21`). Other STM32F407 configs are in `config/` for rusEFI/FOME but are
not in the Speeduino matrix yet because their `board_configuration.cpp` does
not spell out a complete Speeduino pin map (fuel/fan/idle/CLT/IAT/TPS often
missing). `opf33_fome` is the same hardware as `opf33`, not a second Speeduino
board. Teensy boards are not built.

## Shell scripts on this branch

Every `.sh` file was checked against `.github/workflows` and `scripts/` before
any deletion. All current scripts are referenced; none were removed.


## CI workflows

All three workflows live on `master-grok` and share the same naming:

| Workflow | File | Release tag | Assets |
| --- | --- | --- | --- |
| rusEFI autobuild | `.github/workflows/rusefi-autobuild.yml` | `rusefi-<ref>-<variant>` | `<tag>.bin`, `<tag>.ini`, `<tag>-base.msq`, `<tag>-manual.md`, ... |
| FOME autobuild | `.github/workflows/fome-autobuild.yml` | `fome-<ref>-<variant>` | same prefix (`<tag>.update.srec` / `<tag>.bl.srec` for OpenBLT) |
| Speeduino autobuild | `.github/workflows/speeduino-autobuild.yml` | `speeduino-<ref>-<variant>` | same prefix |

The board matrix is generated from `config/<board>/` by `scripts/ci/list_boards.py`. A new board folder is picked up with no workflow edit. Every unique board is built for all three firmwares. `config/opf33_fome/` is the FOME overlay for OPF33, not a separate board (logged as a skip in the job summary). Teensy is not built.
