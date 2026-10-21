#!/usr/bin/env bash
# Build FOME firmware + base tune for an OPF ECU board variant (core48_21, ...).
# Same script is used by .github/workflows/fome-autobuild.yml and for local builds.
#
# usage: scripts/fome/build_fome.sh [--ref REF] [--variant VARIANT] [--work DIR] [--out DIR] [--jobs N]
#                                   [--overlay-dir DIR] [--resolve-only]
#   --ref       FOME tag / branch / commit SHA, or "latest" (default: latest FOME-Tech/fome-fw release)
#   --variant   board variant in scripts/fome/board-overlay (default: core48_21)
#   --work      work directory (FOME checkout, java tools)    (default: ~/.cache/opf-fome-build)
#   --out       output directory                              (default: <work>/out/<variant>)
#   --jobs      parallel make jobs                            (default: nproc)
#   --overlay-dir  directory holding <variant>/ board files   (default: scripts/fome/board-overlay)
#   --resolve-only print the resolved FOME ref and exit
#   (short forms -r -b -w -o -j -c still work)
# env:
#   FOME_REPO          default https://github.com/FOME-Tech/fome-fw.git
#   TOOLCHAIN_CACHE    where the ARM toolchain is unpacked (default <work>/toolchain); sha256-checked
#   USE_BUNDLED_TOOLCHAIN=1  use FOME's build-tools submodule instead of the identical ARM tarball
#   GITHUB_TOKEN/GH_TOKEN    optional, only used for the GitHub API "latest release" lookup
#   BASE_TUNE=1|0      generate <variant>_base_tune.msq from the board defaults (default 1). Needs a
#                      32-bit capable gcc (apt: gcc-multilib g++-multilib) or M32_SYSROOT (see
#                      scripts/fome/setup_m32_sysroot.sh, no sudo needed)
#   M32_SYSROOT        extracted 32-bit libc/libstdc++ dev files used when gcc -m32 is not installed
#   SOURCE_DATE_EPOCH  reproducible-build timestamp (default: FOME commit time)
set -euo pipefail

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "==> $*"; }

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
VARIANT=core48_21; FOME_REF=""; BOARDS_DIR="$SCRIPT_DIR/board-overlay"
WORK="${HOME}/.cache/opf-fome-build"; OUT=""; JOBS=$(nproc); RESOLVE_ONLY=0
usage() { sed -n '2,26p' "$0" | sed 's/^# \{0,1\}//'; }
while [ $# -gt 0 ]; do case "$1" in
  --ref|-r) FOME_REF=$2; shift 2;; --variant|-b) VARIANT=$2; shift 2;; --work|-w) WORK=$2; shift 2;;
  --out|-o) OUT=$2; shift 2;; --jobs|-j) JOBS=$2; shift 2;; --overlay-dir|-c) BOARDS_DIR=$2; shift 2;;
  --resolve-only) RESOLVE_ONLY=1; shift;; -h|--help) usage; exit 0;;
  *) echo "unknown argument: $1" >&2; usage >&2; exit 2;; esac; done
[ "$FOME_REF" = latest ] && FOME_REF=""
FOME_REPO=${FOME_REPO:-https://github.com/FOME-Tech/fome-fw.git}
mkdir -p "$WORK"; WORK=$(cd "$WORK" && pwd)
OUT=${OUT:-$WORK/out/$VARIANT}
TOOLCHAIN_CACHE=${TOOLCHAIN_CACHE:-$WORK/toolchain}
FOME="$WORK/fome"; FW="$FOME/firmware"

# FOME board folder the variant overlays (core48_21 -> core48, core8_24c -> core8)
case "$VARIANT" in core48*) FOME_BOARD=core48;; core8*) FOME_BOARD=core8;; *) FOME_BOARD=${FOME_BOARD:?set FOME_BOARD for variant $VARIANT};; esac
[ -d "$BOARDS_DIR/$VARIANT" ] || die "board config $BOARDS_DIR/$VARIANT not found"

# ---- resolve FOME ref --------------------------------------------------------------------------
TOKEN=${GITHUB_TOKEN:-${GH_TOKEN:-}}
if [ -z "$FOME_REF" ]; then
  FOME_REF=$(curl -fsSL ${TOKEN:+-H "Authorization: Bearer $TOKEN"} \
      https://api.github.com/repos/FOME-Tech/fome-fw/releases/latest 2>/dev/null \
      | python3 -c 'import json,sys;print(json.load(sys.stdin)["tag_name"])' 2>/dev/null) \
    || FOME_REF=$(curl -fsSI https://github.com/FOME-Tech/fome-fw/releases/latest \
      | sed -nE 's#^location: .*/releases/tag/([^[:space:]]+).*#\1#Ip' | tr -d '\r') # API rate-limited: use the web redirect
  [ -n "$FOME_REF" ] || die "could not look up latest FOME release"
fi
if [ "$RESOLVE_ONLY" = 1 ]; then echo "$FOME_REF"; exit 0; fi

export PATH="$PATH:/usr/sbin:/sbin"   # mkfs.fat lives in sbin on Debian/Ubuntu
for t in git curl python3 java make xxd strings sha256sum zip gzip mcopy mkfs.fat; do
  command -v $t >/dev/null || die "missing tool: $t (Ubuntu: sudo apt-get install -y git curl python3 openjdk-17-jdk-headless make xxd binutils zip mtools dosfstools)"
done

log "variant=$VARIANT fome_board=$FOME_BOARD fome_ref=$FOME_REF jobs=$JOBS"

# ---- shallow checkout of exactly that ref --------------------------------------------------------
if [ ! -d "$FOME/.git" ]; then
  git init -q "$FOME"; git -C "$FOME" remote add origin "$FOME_REPO"
fi
git -C "$FOME" fetch -q --depth 1 --no-tags origin "$FOME_REF" || die "FOME ref '$FOME_REF' not found"
# local branch named after the ref: FOME embeds the branch name in the TunerStudio signature
REF_BRANCH=$(sed -E 's#[^A-Za-z0-9._-]+#-#g' <<<"$FOME_REF"); [[ "$FOME_REF" =~ ^[0-9a-f]{40}$ ]] && REF_BRANCH=${FOME_REF:0:10}
git -C "$FOME" checkout -q -f -B "$REF_BRANCH" FETCH_HEAD
git -C "$FOME" clean -qfdx firmware/config/boards firmware/deliver firmware/build firmware/.dep firmware/bootloader/blbuild simulator/build simulator/.dep 2>/dev/null || true
FOME_SHA=$(git -C "$FOME" rev-parse HEAD)
log "FOME commit $FOME_SHA"
# Reproducibility: __DATE__/__TIME__ ("*** Compiled: ...") follow SOURCE_DATE_EPOCH (gcc >= 7), pinned to the
# FOME commit time; TZ=UTC so the date FOME's generator puts into the TS signature is the same on CI and locally.
# (The signature date itself is the build day - upstream behaviour - so bins match for builds on the same UTC day.)
export TZ=UTC
export SOURCE_DATE_EPOCH="${SOURCE_DATE_EPOCH:-$(git -C "$FOME" log -1 --format=%ct HEAD)}"

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
    curl -fsSL --retry 3 -o "$TOOLCHAIN_CACHE/$PLATFORM.tar.xz" "$URL" || die "toolchain download failed"
    # pinned checksums of toolchains FOME uses; unknown (newer) ones are checked against ARM's published .sha256asc
    case "$PLATFORM" in
      arm-gnu-toolchain-11.3.rel1-x86_64-arm-none-eabi) TC_SHA=d420d87f68615d9163b99bbb62fe69e85132dc0a8cd69fca04e813597fe06121;;
      *) TC_SHA=$(curl -fsSL --retry 3 "$URL.sha256asc" | awk '{print $1}') || die "no checksum for $PLATFORM"
         echo "WARNING: $PLATFORM not pinned in build_fome.sh, using ARM's published sha256 $TC_SHA" >&2;;
    esac
    echo "$TC_SHA  $TOOLCHAIN_CACHE/$PLATFORM.tar.xz" | sha256sum -c - || die "toolchain checksum mismatch"
    tar -xJf "$TOOLCHAIN_CACHE/$PLATFORM.tar.xz" -C "$TOOLCHAIN_CACHE" && rm -f "$TOOLCHAIN_CACHE/$PLATFORM.tar.xz"
  fi
fi
[ -x "$TC/bin/arm-none-eabi-gcc" ] || die "compiler missing at $TC"
export TRGT="$TC/bin/arm-none-eabi-"
# write_firmware_checksum.sh calls plain objcopy/objdump; host binutils may not read ARM ELF
SHIMS="$WORK/shims"; mkdir -p "$SHIMS"
for t in objcopy objdump; do ln -sf "$TC/bin/arm-none-eabi-$t" "$SHIMS/$t"; done
# Reproducible ini.zip inside the USB mass-storage image (create_ini_image.sh runs `zip -j fome.ini.zip <ini>`):
# zip copies of the inputs with mtime = SOURCE_DATE_EPOCH and without extra (uid/atime) fields.
REAL_ZIP=$(PATH="${PATH//$SHIMS:/}" command -v zip)
REAL_GZIP=$(PATH="${PATH//$SHIMS:/}" command -v gzip)
cat > "$SHIMS/zip" <<SHIM
#!/bin/bash
set -euo pipefail
tmp=\$(mktemp -d); trap 'rm -rf "\$tmp"' EXIT
args=()
for a in "\$@"; do
  if [ -f "\$a" ] && [[ "\$a" != *.zip ]]; then
    mkdir -p "\$tmp/\$(dirname "\$a")"; cp "\$a" "\$tmp/\$a"; touch -d "@\${SOURCE_DATE_EPOCH}" "\$tmp/\$a"; a="\$tmp/\$a"
  fi
  args+=("\$a")
done
exec "$REAL_ZIP" -X "\${args[@]}"
SHIM
chmod +x "$SHIMS/zip"
printf '#!/bin/sh\nexec "%s" -n "$@"\n' "$REAL_GZIP" > "$SHIMS/gzip"; chmod +x "$SHIMS/gzip"  # no name/mtime in gzip header
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

# ---- base tune: FOME simulator built with this board's defaults -> page image -> .msq -----------
if [ "${BASE_TUNE:-1}" = 1 ]; then
  log "base tune: building simulator with $VARIANT board defaults"
  M32_OPT=""
  if ! echo 'int main(){return 0;}' | gcc -m32 -x c - -o "$WORK/.m32test" 2>/dev/null; then
    [ -n "${M32_SYSROOT:-}" ] || die "base tune needs 32-bit gcc: sudo apt-get install gcc-multilib g++-multilib, or run scripts/fome/setup_m32_sysroot.sh and set M32_SYSROOT (or BASE_TUNE=0 to skip)"
    GV=$(gcc -dumpversion | cut -d. -f1); R=$M32_SYSROOT
    M32_OPT="-B$R/usr/lib/gcc/x86_64-linux-gnu/$GV/32 -B$R/usr/lib32 -L$R/usr/lib/gcc/x86_64-linux-gnu/$GV/32 -L$R/usr/lib32 -isystem $R/usr/include/x86_64-linux-gnu/c++/$GV/32 -idirafter $R/usr/include/x86_64-linux-gnu -idirafter /usr/include/x86_64-linux-gnu -static"
  fi
  for p in "$SCRIPT_DIR"/patches/*.patch; do
    git -C "$FOME" apply --check "$p" || die "simulator patch $(basename "$p") does not apply to this FOME ref"
    git -C "$FOME" apply "$p"; log "applied $(basename "$p")"
  done
  mkdir -p "$FOME/simulator/build" && echo done > "$FOME/simulator/build/java_tools.cookie"
  make -C "$FOME/simulator" -j"$JOBS" BOARD_DIR="../firmware/config/boards/$FOME_BOARD" PROJECT_BOARD="$FOME_BOARD" \
       SIM_WITH_BOARD_DEFAULTS=1 SANITIZE=no RUSEFI_OPT="-DSIM_WITH_BOARD_DEFAULTS $M32_OPT" > "$WORK/simulator_build.log" 2>&1 \
    || { tail -30 "$WORK/simulator_build.log"; die "simulator build failed (log: $WORK/simulator_build.log)"; }
  SIMDIR=$(mktemp -d); PAGE_SIZE=$(grep -m1 -oE '^pageSize\s*=\s*[0-9]+' "$OUT/fome_tunerstudio.ini" | grep -oE '[0-9]+$')
  (cd "$SIMDIR" && exec "$FOME/simulator/build/fome_simulator" 60 > "$SIMDIR/sim.log" 2>&1) & SIMPID=$!
  if ! python3 "$SCRIPT_DIR/ts_read_page.py" tcp:127.0.0.1:29001 "$PAGE_SIZE" "$OUT/${VARIANT}_base_tune.bin" --expect-signature "$SIG_INI"; then
    kill $SIMPID 2>/dev/null; tail -20 "$SIMDIR/sim.log"; die "could not read defaults from simulator"
  fi
  kill $SIMPID 2>/dev/null; wait $SIMPID 2>/dev/null || true; rm -rf "$SIMDIR"
  python3 "$SCRIPT_DIR/ini2msq.py" "$OUT/fome_tunerstudio.ini" "$OUT/${VARIANT}_base_tune.bin" "$OUT/${VARIANT}_base_tune.msq" \
    --comment "Base tune: FOME $FOME_REF defaults for $VARIANT (generated by OPF build)" || die "msq generation failed"
  python3 "$SCRIPT_DIR/ini2msq.py" --verify "$OUT/fome_tunerstudio.ini" "$OUT/${VARIANT}_base_tune.bin" "$OUT/${VARIANT}_base_tune.msq" \
    || die "msq verification failed"
fi

(cd "$OUT" && sha256sum fome.bin fome_update.srec fome_bl.srec fome.elf fome_tunerstudio.ini *_base_tune.msq *_base_tune.bin 2>/dev/null > SHA256SUMS)
cat > "$OUT/build-info.txt" <<INFO
variant=$VARIANT
fome_board=$FOME_BOARD
fome_ref=$FOME_REF
fome_commit=$FOME_SHA
signature=$SIG_INI
toolchain=$PLATFORM
config_source=$BOARDS_DIR/$VARIANT
built_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)
source_date_epoch=$SOURCE_DATE_EPOCH
INFO
cat > "$OUT/release-notes.md" <<NOTES
FOME firmware for **$VARIANT** (FOME board \`$FOME_BOARD\`, OpenBLT bootloader included).

- FOME ref: \`$FOME_REF\` - commit [\`${FOME_SHA:0:10}\`](https://github.com/FOME-Tech/fome-fw/commit/$FOME_SHA)
- TunerStudio signature: \`$SIG_INI\`
- Toolchain: \`$PLATFORM\`
- Base tune: \`${VARIANT}_base_tune.msq\` (FOME defaults for this board, generated by the FOME simulator built with the board config) - load in TunerStudio as a starting point

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
log "done -> $OUT"; ls -l "$OUT"; echo "SHA256SUMS:"; cat "$OUT/SHA256SUMS"
