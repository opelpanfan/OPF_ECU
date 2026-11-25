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
| `scripts/docs/generate_pinout.py` | Regenerates interactive `docs/<board>.html` pinouts and the `<!-- PINOUT -->` section of `config/<board>/readme.md` from connector YAMLs |
| `docs/opf33.html` | Generated 33-pin V1.1 pinout page. Live on GitHub Pages only after it is on `main`. |
| `scripts/rusefi/` | Shared rusEFI build script (CI + local) |
| `scripts/fome/` | Shared FOME build script (CI + local) |
| `scripts/speeduino/` | Shared Speeduino build script (CI + local), official `speeduino/speeduino` |

CI still builds the hand-written `config/` files (known-good fallback). Generated
overlays live under `config/opf33/generated/` for review.

## Pinned upstream versions (CI defaults)

Bumped 2026-11-25 (previous pins: rusEFI `4e068e8a73e94f9922c2f0907667d8ba77f9bfc9`, FOME `71a6e6ec246ee16b87e0667df1b79e8e838a05b2`). Speeduino release `202501.7` is still the newest GitHub release. Speeduino also builds pinned master.

- rusEFI: `34b1633bc25fa948efe66dd93bdde1e173357fc9` (`rusefi/rusefi` master)
- FOME: `477f9e471aaf5e29180a70dbc7230d259199b40a` (`FOME-Tech/fome-fw` master)
- Speeduino release: `202501.7` (commit `cd3d0e38d276a7bd087a9dc86fd976780539ce8f` on `speeduino/speeduino`)
- Speeduino master: `b59336df1fa80c29f6a08cd5376604744a275bce` (`speeduino/speeduino` master, 2026-11-21)

`workflow_dispatch` can override `ref` (including `latest`) and `variant`.
A `v*` tag push builds every board and publishes missing releases (not a dry
run). Manual dispatch publishes only when `dry_run=false`. An existing release
is never overwritten, and release creation passes `--latest=false`.

## Local build

```sh
scripts/rusefi/build_rusefi.sh --ref 34b1633bc25fa948efe66dd93bdde1e173357fc9 --variant opf33
scripts/fome/build_fome.sh --ref 477f9e471aaf5e29180a70dbc7230d259199b40a --variant opf33
scripts/speeduino/build_speeduino.sh --ref 202501.7 --variant opf33
scripts/speeduino/build_speeduino.sh --ref b59336df1fa80c29f6a08cd5376604744a275bce --variant opf33
python3 tools/boardgen/generate_board.py config/opf33/board.yaml --docs-dir docs
```

## Speeduino board coverage

Every board under `config/` that has `scripts/speeduino/board-overlay/<board>/board.json`
is built twice: release `202501.7` and pinned master `b59336df1fa80c29f6a08cd5376604744a275bce`.
`opf33_fome` is the same hardware as `opf33`, not a second Speeduino board. Teensy is not built.

Artifact names do not collide:

| Ref | Firmware / ini / base tune |
| --- | --- |
| `202501.7` | `speeduino-202501.7-<board>.bin`, `.ini`, `-base.msq` |
| master SHA | `speeduino-master-b59336df1f-<board>.bin`, `.ini`, `-base.msq` |

The short names inside each build directory (`speeduino_firmware.bin`, `speeduino_tunerstudio.ini`, `base-map.msq`) are what the board branch still publishes, and only for the release pin. Master is a separate GitHub release (`speeduino-master-<10-char sha>-<board>`).

On master, Speeduino stores pins in `pinNumbers_t` (`setInjectorPin` / `setCoilPin` / `pins.pinX`). The same GPIO map is applied. Upstream removed spare/display/`pinMAP2` variables; those stay `NOT_A_PIN`. `pinSpareTemp1` was a future-use input (PA6 or PA7 on some boards) with no firmware consumer, so it is not reassigned to another function.

## Shell scripts on this branch

Every `.sh` file was checked against `.github/workflows` and `scripts/` before
any deletion. All current scripts are referenced; none were removed.


## CI workflows

All three workflows live on `master-grok` and share the same naming:

| Workflow | File | Release tag | Assets |
| --- | --- | --- | --- |
| rusEFI autobuild | `.github/workflows/rusefi-autobuild.yml` | `rusefi-<ref>-<variant>` | `<tag>.bin`, `<tag>.ini`, `<tag>-base.msq`, `<tag>-manual.md`, ... |
| FOME autobuild | `.github/workflows/fome-autobuild.yml` | `fome-<ref>-<variant>` | same prefix (`<tag>.update.srec` / `<tag>.bl.srec` for OpenBLT) |
| Speeduino autobuild | `.github/workflows/speeduino-autobuild.yml` | `speeduino-202501.7-<variant>` and `speeduino-master-<sha10>-<variant>` | `<tag>.bin`, `<tag>.ini`, `<tag>-base.msq`, ... |

The board matrix is generated from `config/<board>/` by `scripts/ci/list_boards.py`. A new board folder is picked up with no workflow edit. Every unique board is built for rusEFI, FOME, and both Speeduino refs. `config/opf33_fome/` is the FOME overlay for OPF33, not a separate board (logged as a skip in the job summary). Teensy is not built.
