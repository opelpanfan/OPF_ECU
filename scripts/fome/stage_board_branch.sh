#!/usr/bin/env bash
# Copy a build_fome.sh output into the fome/ folder of a checkout of the board branch (e.g. core48_21),
# using the names that branch's readme.md download buttons link to (same layout as rusefi/):
#   fome/fome_firmware.bin  fome/fome_tunerstudio.ini  fome/fome_console.zip
# plus fome/fome_update.srec (OpenBLT update), fome/fome_base_tune.msq (board defaults) and fome/build-info.txt.
# Only fome/ is touched; nothing is committed or pushed here.
# usage: scripts/fome/stage_board_branch.sh <build_out_dir> <board_branch_checkout>
set -euo pipefail
OUT=${1:?build output dir}; DST=${2:?board branch checkout}
[ -f "$OUT/fome.bin" ] && [ -f "$OUT/build-info.txt" ] || { echo "not a build_fome.sh output: $OUT" >&2; exit 1; }
[ -d "$DST/.git" ] || { echo "not a git checkout: $DST" >&2; exit 1; }
F="$DST/fome"; mkdir -p "$F"
cp "$OUT/fome.bin" "$F/fome_firmware.bin"
cp "$OUT/fome_tunerstudio.ini" "$F/fome_tunerstudio.ini"
cp "$OUT/fome_update.srec" "$F/fome_update.srec"
cp "$OUT/build-info.txt" "$F/build-info.txt"
[ -f "$OUT/fome_console.zip" ] && cp "$OUT/fome_console.zip" "$F/fome_console.zip"
msq=$(ls "$OUT"/*_base_tune.msq 2>/dev/null | head -1 || true)
[ -n "$msq" ] && cp "$msq" "$F/fome_base_tune.msq"
(cd "$F" && sha256sum $(ls | grep -v '^SHA256SUMS$' | LC_ALL=C sort) > SHA256SUMS)
git -C "$DST" status --short -- fome/
