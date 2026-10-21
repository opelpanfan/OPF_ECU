#!/usr/bin/env bash
# Publish a build_fome.sh output into fome/ of a checkout of the board branch (e.g. core48_21).
# Flat layout with fixed names (same scheme as rusefi/ on that branch; the branch readme links to these):
#   fome/fome_firmware.bin    OpenBLT + FOME combined image, flash at 0x08000000 (DFU)
#   fome/fome_firmware.srec   FOME application only, update through the OpenBLT bootloader
#   fome/fome_tunerstudio.ini fome/fome_console.zip fome/fome_base_tune.msq fome/fome_build_info.txt fome/SHA256SUMS
# Only fome/ is touched; the script refuses if anything outside fome/ is staged or modified.
# usage: scripts/fome/stage_board_branch.sh <build_out_dir> <board_branch_checkout> [--push "<commit message>"]
#   --push: normal commit + `git push origin HEAD:<branch>`; on rejection fetch + rebase + retry (max 5), never force.
set -euo pipefail
OUT=${1:?build output dir}; DST=${2:?board branch checkout}; PUSH=0; MSG=""
if [ "${3:-}" = --push ]; then PUSH=1; MSG=${4:?commit message}; fi
OUT=$(cd "$OUT" && pwd)
[ -f "$OUT/fome.bin" ] && [ -f "$OUT/build-info.txt" ] || { echo "not a build_fome.sh output: $OUT" >&2; exit 1; }
cd "$DST"; git rev-parse --is-inside-work-tree >/dev/null || { echo "not a git checkout: $DST" >&2; exit 1; }
BRANCH=$(git rev-parse --abbrev-ref HEAD)

stage() {
  local F=fome
  mkdir -p "$F"
  find "$F" -maxdepth 1 -type f -delete      # fome/ is fully owned by this script (flat)
  cp "$OUT/fome.bin" "$F/fome_firmware.bin"
  cp "$OUT/fome_update.srec" "$F/fome_firmware.srec"
  cp "$OUT/fome_tunerstudio.ini" "$F/fome_tunerstudio.ini"
  [ -f "$OUT/fome_console.zip" ] && cp "$OUT/fome_console.zip" "$F/fome_console.zip"
  local msq; msq=$(ls "$OUT"/*_base_tune.msq 2>/dev/null | head -1 || true)
  [ -n "$msq" ] && cp "$msq" "$F/fome_base_tune.msq"
  cp "$OUT/build-info.txt" "$F/fome_build_info.txt"
  (cd "$F" && sha256sum $(ls | grep -vx SHA256SUMS | LC_ALL=C sort) > SHA256SUMS)
  git add -A -- "$F"
  local outside
  outside=$( { git diff --cached --name-only; git diff --name-only; } | grep -v '^fome/' || true)
  if [ -n "$outside" ]; then echo "refusing: changes outside fome/:" >&2; echo "$outside" >&2; exit 1; fi
}

stage
git status --short -- fome/
[ "$PUSH" = 1 ] || exit 0
if git diff --cached --quiet; then echo "fome/ already up to date on $BRANCH"; exit 0; fi
git commit -q -m "$MSG"
for attempt in 1 2 3 4 5; do
  if git push origin "HEAD:$BRANCH"; then echo "pushed $(git rev-parse HEAD) to $BRANCH"; exit 0; fi
  echo "push rejected (attempt $attempt), fetch + rebase"
  git fetch -q origin "$BRANCH"
  if ! git rebase -q "origin/$BRANCH"; then
    # someone else changed fome/: drop our commit, re-stage on top of theirs
    git rebase --abort || true
    git reset -q --hard "origin/$BRANCH"; stage
    git diff --cached --quiet && { echo "fome/ already up to date on $BRANCH"; exit 0; }
    git commit -q -m "$MSG"
  fi
  sleep $((attempt * 5))
done
echo "could not push to $BRANCH after 5 attempts" >&2; exit 1
