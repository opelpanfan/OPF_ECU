#!/usr/bin/env bash
# Copy a firmware out/ directory into release assets named <tag>.<ext>, matching rusEFI.
# Usage: stage_release_assets.sh <tag> <out_dir> <stage_dir>
# Recognizes rusEFI-style already-prefixed files, plus FOME and Speeduino short names.
set -euo pipefail
TAG=$1 OUT=$2 STAGE=$3
mkdir -p "$STAGE"
# If the build already used the tag prefix (rusEFI), copy those through.
shopt -s nullglob
pref=0
for f in "$OUT/$TAG".* "$OUT/$TAG"-*; do
  [ -e "$f" ] || continue
  cp "$f" "$STAGE/"; pref=1
done
copy() { [ -f "$1" ] && cp "$1" "$STAGE/$2"; }
if [ "$pref" -eq 0 ]; then
  copy "$OUT/fome.bin"              "$TAG.bin"
  copy "$OUT/fome.elf"              "$TAG.elf"
  copy "$OUT/fome_update.srec"      "$TAG.update.srec"
  copy "$OUT/fome_bl.srec"          "$TAG.bl.srec"
  copy "$OUT/fome_tunerstudio.ini"  "$TAG.ini"
  copy "$OUT/fome_console.zip"      "$TAG.console.zip"
  copy "$OUT/build-info.txt"        "$TAG.build-info.txt"
  for f in "$OUT"/*_base_tune.msq; do copy "$f" "$TAG-base.msq"; done
  for f in "$OUT"/*-manual.md; do copy "$f" "$TAG-manual.md"; done
  copy "$OUT/speeduino_firmware.bin"     "$TAG.bin"
  copy "$OUT/speeduino_firmware.hex"     "$TAG.hex"
  copy "$OUT/speeduino_firmware.elf"     "$TAG.elf"
  copy "$OUT/speeduino_tunerstudio.ini"  "$TAG.ini"
  copy "$OUT/base-map.msq"               "$TAG-base.msq"
  copy "$OUT/build-info.json"            "$TAG.build-info.json"
  for f in "$OUT"/opf-*.patch; do copy "$f" "$TAG.patch"; done
fi
# Always include a SHA256SUMS that matches the staged names.
(cd "$STAGE" && sha256sum * 2>/dev/null | grep -v ' SHA256SUMS$' > SHA256SUMS || true)
ls -1 "$STAGE"
