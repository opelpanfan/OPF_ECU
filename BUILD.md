# OPF_ECU firmware builds (`master-grok`)

This branch is the public, single source of truth for OPF board configs and
firmware CI. It follows the existing OPF_ECU autobuild conventions
(`scripts/rusefi`, `scripts/fome`, GitHub Releases, artifacts on per-board
branches) and vendors every `ECU_Build` `config/<board>` folder so CI no longer
needs the private repo.

Do not push this work to `main` or `master`. Scheduled workflows still only run
from the default branch (`main`); until these workflow files are on `main`,
builds start from a push to `master-grok` or `workflow_dispatch`.

## Layout

| Path | Role |
| --- | --- |
| `config/<board>/` | Board sources copied from ECU_Build (pin maps, `board.h`, connectors, manuals) |
| `config/opf33/board.yaml` | OPF33 V1.1 single-file description (MCU, 33-pin map, sensors, docs) |
| `config/opf33/readme.md` | Generated V1.1 manual (release notes). Not the old retitled OPF48 pinout. |
| `config/opf33_fome/` | FOME-specific OPF33 overlay (`compile_opf33.sh`, old FOME hook API) |
| `tools/boardgen/` | Generates rusEFI/FOME overlays, the manual, and `docs/<board>.html` |
| `docs/opf33.html` | Generated 33-pin V1.1 pinout page. Live on GitHub Pages only after it is on `main`. |
| `scripts/rusefi/` | Shared rusEFI build script (CI + local), already used on `master-rusefi-grok` |
| `scripts/fome/` | Shared FOME build script (CI + local), already used on `master-fome-grok` |

CI still builds the hand-written `config/` files (known-good fallback). Generated
overlays live under `config/opf33/generated/` for review.

## Pins used for the first OPF33 builds

- rusEFI: `df128dec524d820bb767bcc503d8561ef01e258c`
- FOME: `3b772a890ae0703793b14f08822c20f34b386b8c`

`workflow_dispatch` can override `ref` (including `latest`) and `variant`.
Publishing a release and committing firmware to the board branch (`opf33/rusefi`
or `opf33/fome`) happens only when `dry_run=false`. Push validation never
publishes.

## Local build

```sh
scripts/rusefi/build_rusefi_core48.sh --ref df128dec524d820bb767bcc503d8561ef01e258c --variant opf33
scripts/fome/build_fome.sh --ref 3b772a890ae0703793b14f08822c20f34b386b8c --variant opf33
python3 tools/boardgen/generate_board.py config/opf33/board.yaml --docs-dir docs
```

## Other boards

Every ECU_Build `config/<board>` folder is on this branch. Matrix builds for the
other boards come after OPF33 rusEFI and FOME are green and a release exists.
