#!/usr/bin/env bash
# Build FOME firmware for an OPF ECU board variant (core48_21, ...).
# Same script is used by .github/workflows/fome-autobuild.yml and for local builds.
#
# usage: build/build_fome.sh [-b variant] [-r fome_ref] [-c boards_dir] [-w workdir] [-o outdir] [-j jobs]
#   -b  board variant folder in boards_dir         (default: core48_21)
#   -r  FOME tag / branch / commit SHA             (default: latest FOME-Tech/fome-fw release)
#   -c  directory holding <variant>/ board configs (default: build/boards next to this script)
#   -w  work directory (FOME checkout, toolchain)  (default: ~/.cache/opf-fome-build)
#   -o  output directory                           (default: <workdir>/out/<variant>)
#   -j  parallel make jobs                         (default: nproc)
# env:
#   FOME_REPO          default https://github.com/FOME-Tech/fome-fw.git
#   TOOLCHAIN_CACHE    where the ARM toolchain is unpacked (default <workdir>/toolchain)
#   USE_BUNDLED_TOOLCHAIN=1  use FOME's build-tools submodule instead of the identical ARM tarball
#   GITHUB_TOKEN/GH_TOKEN    optional, only used for the GitHub API "latest release" lookup
set -euo pipefail

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "==> $*"; }

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VARIANT=core48_21; FOME_REF=""; BOARDS_DIR="$SCRIPT_DIR/boards"
WORK="${HOME}/.cache/opf-fome-build"; OUT=""; JOBS=$(nproc)
while getopts "b:r:c:w:o:j:h" o; do case $o in
  b) VARIANT=$OPTARG;; r) FOME_REF=$OPTARG;; c) BOARDS_DIR=$OPTARG;; w) WORK=$OPTARG;;
  o) OUT=$OPTARG;; j) JOBS=$OPTARG;; *) sed -n '2,20p' "$0"; exit 2;; esac; done
FOME_REPO=${FOME_REPO:-https://github.com/FOME-Tech/fome-fw.git}
mkdir -p "$WORK"; WORK=$(cd "$WORK" && pwd)
OUT=${OUT:-$WORK/out/$VARIANT}
TOOLCHAIN_CACHE=${TOOLCHAIN_CACHE:-$WORK/toolchain}
FOME="$WORK/fome"; FW="$FOME/firmware"

# FOME board folder the variant overlays (core48_21 -> core48, core8_24c -> core8)
case "$VARIANT" in core48*) FOME_BOARD=core48;; core8*) FOME_BOARD=core8;; *) FOME_BOARD=${FOME_BOARD:?set FOME_BOARD for variant $VARIANT};; esac
[ -d "$BOARDS_DIR/$VARIANT" ] || die "board config $BOARDS_DIR/$VARIANT not found"

export PATH="$PATH:/usr/sbin:/sbin"   # mkfs.fat lives in sbin on Debian/Ubuntu
for t in git curl python3 java make xxd strings sha256sum zip gzip mcopy mkfs.fat; do
  command -v $t >/dev/null || die "missing tool: $t (Ubuntu: sudo apt-get install -y git curl python3 openjdk-17-jdk-headless make xxd binutils zip mtools dosfstools)"
done

# ---- resolve FOME ref --------------------------------------------------------------------------
TOKEN=${GITHUB_TOKEN:-${GH_TOKEN:-}}
if [ -z "$FOME_REF" ]; then
  FOME_REF=$(curl -fsSL ${TOKEN:+-H "Authorization: Bearer $TOKEN"} \
      https://api.github.com/repos/FOME-Tech/fome-fw/releases/latest | python3 -c 'import json,sys;print(json.load(sys.stdin)["tag_name"])') \
    || die "could not look up latest FOME release"
fi
log "variant=$VARIANT fome_board=$FOME_BOARD fome_ref=$FOME_REF jobs=$JOBS"

# ---- shallow checkout of exactly that ref --------------------------------------------------------
if [ ! -d "$FOME/.git" ]; then
  git init -q "$FOME"; git -C "$FOME" remote add origin "$FOME_REPO"
fi
git -C "$FOME" fetch -q --depth 1 --no-tags origin "$FOME_REF" || die "FOME ref '$FOME_REF' not found"
# local branch named after the ref: FOME embeds the branch name in the TunerStudio signature
REF_BRANCH=$(sed -E 's#[^A-Za-z0-9._-]+#-#g' <<<"$FOME_REF"); [[ "$FOME_REF" =~ ^[0-9a-f]{40}$ ]] && REF_BRANCH=${FOME_REF:0:10}
git -C "$FOME" checkout -q -f -B "$REF_BRANCH" FETCH_HEAD
git -C "$FOME" clean -qfdx firmware/config/boards firmware/deliver firmware/build firmware/.dep firmware/bootloader/blbuild 2>/dev/null || true
FOME_SHA=$(git -C "$FOME" rev-parse HEAD)
log "FOME commit $FOME_SHA"

# ---- submodules: only what the firmware build needs -------------------------------------------
SKIP="unit_tests/googletest java_console/luaformatter misc/hex2dfu"
[ "${USE_BUNDLED_TOOLCHAIN:-0}" = 1 ] || SKIP="$SKIP firmware/ext/build-tools"
SUBS=$(git -C "$FOME" config -f .gitmodules --get-regexp '\.path$' | awk '{print $2}' | grep -vxF -f <(tr ' ' '\n' <<<"$SKIP"))
log "submodules: $(echo $SUBS)"
git -C "$FOME" submodule update --init --depth 1 --jobs 8 -- $SUBS || die "submodule checkout failed"

# ---- ARM toolchain pinned to the version FOME ships ----------------------------------------------
PLATFORM=$(grep -oE 'arm-gnu-toolchain-[^ ]*-x86_64-arm-none-eabi' "$FW/use_arm_gcc.mk" | grep -v darwin | head -1)
[ -n "$PLATFORM" ] || die "cannot determine FOME toolchain from use_arm_gcc.mk"
if [ "${USE_BUNDLED_TOOLCHAIN:-0}" = 1 ]; then
  TC="$FW/ext/build-tools/$PLATFORM"
else
  TC="$TOOLCHAIN_CACHE/$PLATFORM"
  if [ ! -x "$TC/bin/arm-none-eabi-gcc" ]; then
    VER=$(sed -E 's/arm-gnu-toolchain-([^-]+)-.*/\1/' <<<"$PLATFORM")
    URL="https://developer.arm.com/-/media/Files/downloads/gnu/$VER/binrel/$PLATFORM.tar.xz"
    log "downloading $URL"
    mkdir -p "$TOOLCHAIN_CACHE"
    curl -fsSL --retry 3 "$URL" | tar -xJ -C "$TOOLCHAIN_CACHE" || die "toolchain download failed"
  fi
fi
[ -x "$TC/bin/arm-none-eabi-gcc" ] || die "compiler missing at $TC"
export TRGT="$TC/bin/arm-none-eabi-"
# write_firmware_checksum.sh calls plain objcopy/objdump; host binutils may not read ARM ELF
SHIMS="$WORK/shims"; mkdir -p "$SHIMS"
for t in objcopy objdump; do ln -sf "$TC/bin/arm-none-eabi-$t" "$SHIMS/$t"; done
export PATH="$SHIMS:$PATH"
log "toolchain: $("${TRGT}gcc" --version | head -1)"

# ---- java code generators (cached by java_tools tree hash) ---------------------------------------
JT_TREE=$(git -C "$FOME" rev-parse HEAD:java_tools)
if [ "$(cat "$FOME/java_tools/.built_tree" 2>/dev/null)" != "$JT_TREE" ] || [ ! -f "$FOME/java_tools/ConfigDefinition.jar" ]; then
  log "building java_tools"
  (cd "$FOME/java_tools" && ./build_tools.sh) || die "java_tools build failed"
  echo "$JT_TREE" > "$FOME/java_tools/.built_tree"
else
  log "java_tools up to date ($JT_TREE)"
fi
# jars are fresh: tell the Makefile so it does not re-run gradle
mkdir -p "$FW/build" && echo done > "$FW/build/java_tools.cookie"

# ---- board overlay + fixups -------------------------------------------------------------------
BD="$FW/config/boards/$FOME_BOARD"
[ -f "$BD/compile_$FOME_BOARD.sh" ] || die "this FOME ref has no config/boards/$FOME_BOARD/compile_$FOME_BOARD.sh"
cp -r "$BOARDS_DIR/$VARIANT/." "$BD/"
python3 "$SCRIPT_DIR/fome_board_fixups.py" "$FW" "$BD"

# parallel make: upstream common_make.sh hardcodes -j20
sed -i -E "s/make -j[0-9]+/make -j$JOBS/g" "$FW/config/boards/common_make.sh"

# ---- build (upstream per-board script: OpenBLT bootloader + main firmware + combined image) ------
log "building"
(cd "$BD" && bash "./compile_$FOME_BOARD.sh") || die "firmware build failed"

# ---- collect + verify --------------------------------------------------------------------------
rm -rf "$OUT"; mkdir -p "$OUT"
INI="$FW/tunerstudio/generated/fome_$FOME_BOARD.ini"
[ -f "$FW/deliver/fome.bin" ] || die "deliver/fome.bin missing"
cp "$FW/deliver/fome.bin" "$OUT/"
for f in fome_update.srec fome_bl.srec; do [ -f "$FW/deliver/$f" ] && cp "$FW/deliver/$f" "$OUT/"; done
cp "$FW/build/fome.elf" "$OUT/"
cp "$INI" "$OUT/fome_tunerstudio.ini"

SIG_INI=$(grep -m1 -E '^\s*signature\s*=' "$INI" | sed -E 's/^[^"]*"([^"]*)".*/\1/')
SIG_BIN=$(strings -n 8 "$OUT/fome.bin" | grep -m1 -F "$SIG_INI" || true)
[ -n "$SIG_INI" ] && [ "$SIG_BIN" = "$SIG_INI" ] || die "signature mismatch: ini='$SIG_INI' bin='$SIG_BIN'"
log "signature OK: $SIG_INI"

(cd "$OUT" && sha256sum fome.bin fome_update.srec fome_bl.srec fome.elf fome_tunerstudio.ini 2>/dev/null > SHA256SUMS)
cat > "$OUT/build-info.txt" <<INFO
variant=$VARIANT
fome_board=$FOME_BOARD
fome_ref=$FOME_REF
fome_commit=$FOME_SHA
signature=$SIG_INI
toolchain=$PLATFORM
config_source=$BOARDS_DIR/$VARIANT
built_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
INFO
cat > "$OUT/release-notes.md" <<NOTES
FOME firmware for **$VARIANT** (FOME board \`$FOME_BOARD\`, OpenBLT bootloader included).

- FOME ref: \`$FOME_REF\` - commit [\`${FOME_SHA:0:10}\`](https://github.com/FOME-Tech/fome-fw/commit/$FOME_SHA)
- TunerStudio signature: \`$SIG_INI\`
- Toolchain: \`$PLATFORM\`

Flash \`fome.bin\` at 0x08000000 via DFU (e.g. \`dfu-util -d 0483:df11 -a 0 -s 0x08000000:leave -D fome.bin\`);
later updates can use \`fome_update.srec\` through the OpenBLT bootloader. Settings reset to defaults when
coming from rusEFI or an older FOME config layout - back up your tune first.

\`\`\`
$(cat "$OUT/SHA256SUMS")
\`\`\`
NOTES
if [ -n "${GITHUB_OUTPUT:-}" ]; then
  { echo "fome_commit=$FOME_SHA"; echo "signature=$SIG_INI"; echo "out=$OUT"; } >> "$GITHUB_OUTPUT"
fi
log "done -> $OUT"; ls -l "$OUT"
