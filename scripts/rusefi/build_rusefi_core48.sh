#!/usr/bin/env bash
# Build rusEFI firmware for the OPF core48 board family (default variant core48_21).
#
# Same script is used locally and by .github/workflows/rusefi-core48-autobuild.yml,
# so CI and local builds are identical.
#
# Baseline: opelpanfan/ECU_Build compile_rusefi.sh + .github/workflows/core48_21.yml,
# adapted for current upstream rusEFI (see scripts/rusefi/README.md for the change list).
#
# Usage: scripts/rusefi/build_rusefi_core48.sh [--ref REF] [--variant VARIANT] [options]
#   --ref REF            rusEFI tag/branch/sha, or "latest" (latest stable GitHub release,
#                        default) or "latest-nightly" (newest release incl. prereleases)
#   --variant VARIANT    ECU_Build config dir name (default core48_21)
#   --work DIR           work dir for checkouts (default ./.rusefi-build)
#   --out DIR            artifact output dir (default <work>/out)
#   --toolchain-dir DIR  where the pinned ARM toolchain lives/is installed
#                        (default ~/.cache/opf-rusefi/toolchain)
#   --rusefi-dir DIR     use an existing rusEFI checkout instead of cloning (not modified
#                        beyond firmware/config/boards/core8 + build outputs)
#   --ecu-build-dir DIR  use an existing ECU_Build checkout (read-only)
#   --ecu-build-ref REF  ECU_Build ref to clone (default main)
#   --board-src DIR      use this board config dir directly. Default priority:
#                        --board-src > --ecu-build-dir/config/<variant> >
#                        scripts/rusefi/board-overlay/<variant> (committed, used by CI) > ECU_Build clone
#   --signature-branch N branch name embedded in the TS signature ("rusEFI <N>.<date>.core8.<hash>");
#                        default: the ref for branches/tags, "master" for commit shas
#   --with-console       also build rusefi_console.jar (slower)
#   --no-base-tune       skip the base tune (.msq) generation (rusEFI simulator + tune-tools)
#   --sim-docker         build/run the 32-bit simulator in docker (auto if host lacks gcc -m32)
#   --resolve-only       just print the resolved ref and exit
#   -h|--help
# Env: GITHUB_TOKEN (optional, only to raise GitHub API rate limits), JAVA_HOME,
#      SOURCE_DATE_EPOCH (default: rusEFI commit time -> reproducible __DATE__/__TIME__).
set -euo pipefail

# ---- pinned versions -------------------------------------------------------
TOOLCHAIN_NAME="arm-gnu-toolchain-14.2.rel1-x86_64-arm-none-eabi"   # = rusEFI master CI (14.2.Rel1)
TOOLCHAIN_URL="https://developer.arm.com/-/media/Files/downloads/gnu/14.2.rel1/binrel/${TOOLCHAIN_NAME}.tar.xz"
TOOLCHAIN_SHA256="62a63b981fe391a9cbad7ef51b17e49aeaa3e7b0d029b36ca1e9c3b2a9b78823"
RUSEFI_REPO="https://github.com/rusefi/rusefi.git"
# ECU_Build is a private repo: https works with git credentials, otherwise ssh is tried.
if [ -n "${ECU_BUILD_REPO:-}" ]; then ECU_BUILD_REPOS=("$ECU_BUILD_REPO")
else ECU_BUILD_REPOS=(https://github.com/opelpanfan/ECU_Build.git git@github.com:opelpanfan/ECU_Build.git); fi
# Only the submodules the firmware (+ java code generators) need; skips googletest,
# hardware/*, misc/hex2dfu sources, hw-ci etc.
SUBMODULES=(
  firmware/ChibiOS
  firmware/ChibiOS-Contrib
  firmware/libfirmware
  firmware/ext/lua
  firmware/ext/magic_enum
  firmware/ext/uzlib
  firmware/ext/openblt
  firmware/ext/rusefi-gha
  firmware/controllers/lua/luaaa
  firmware/controllers/can/wideband_firmware
  java_console/luaformatter
  java_console/peak-can-basic
)
SHORT_BOARD_NAME=core8   # ECU_Build board.env: core48 configs are built into upstream's core8 board dir

# ---- args ------------------------------------------------------------------
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -P)
REF=latest
VARIANT=core48_21
WORK="$PWD/.rusefi-build"
OUT=""
TOOLCHAIN_DIR="${HOME}/.cache/opf-rusefi/toolchain"
RUSEFI_DIR=""
ECU_BUILD_DIR=""
ECU_BUILD_REF=main
BOARD_SRC=""
SIG_BRANCH=""
WITH_CONSOLE=0
BASE_TUNE=1
SIM_DOCKER=auto
RESOLVE_ONLY=0

usage() { sed -n '2,33p' "$0" | sed 's/^# \{0,1\}//'; }
while [ $# -gt 0 ]; do
  case "$1" in
    --ref) REF=$2; shift 2 ;;
    --variant) VARIANT=$2; shift 2 ;;
    --work) WORK=$2; shift 2 ;;
    --out) OUT=$2; shift 2 ;;
    --toolchain-dir) TOOLCHAIN_DIR=$2; shift 2 ;;
    --rusefi-dir) RUSEFI_DIR=$2; shift 2 ;;
    --ecu-build-dir) ECU_BUILD_DIR=$2; shift 2 ;;
    --ecu-build-ref) ECU_BUILD_REF=$2; shift 2 ;;
    --board-src) BOARD_SRC=$2; shift 2 ;;
    --signature-branch) SIG_BRANCH=$2; shift 2 ;;
    --with-console) WITH_CONSOLE=1; shift ;;
    --no-base-tune) BASE_TUNE=0; shift ;;
    --sim-docker) SIM_DOCKER=1; shift ;;
    --resolve-only) RESOLVE_ONLY=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage >&2; exit 2 ;;
  esac
done
[ -n "$REF" ] || REF=latest
[ -n "$VARIANT" ] || VARIANT=core48_21
case "$VARIANT" in *[!A-Za-z0-9_.-]*) echo "Invalid variant: $VARIANT" >&2; exit 2 ;; esac

log() { printf '\n=== %s\n' "$*"; }
die() { echo "ERROR: $*" >&2; exit 1; }

gh_api() {
  local auth=()
  [ -n "${GITHUB_TOKEN:-}" ] && auth=(-H "Authorization: Bearer ${GITHUB_TOKEN}")
  curl -fsSL --retry 3 -H "Accept: application/vnd.github+json" "${auth[@]}" "https://api.github.com/$1"
}
json_field() { python3 -c 'import json,sys; d=json.load(sys.stdin); d=d[0] if isinstance(d,list) else d; print(d.get(sys.argv[1]) or "")' "$1"; }

# ---- resolve ref ------------------------------------------------------------
case "$REF" in
  latest)         REF=$(gh_api repos/rusefi/rusefi/releases/latest | json_field tag_name) ;;
  latest-nightly) REF=$(gh_api "repos/rusefi/rusefi/releases?per_page=1" | json_field tag_name) ;;
esac
[ -n "$REF" ] || die "could not resolve rusEFI ref"
SAFE_REF=$(printf '%s' "$REF" | tr -c 'A-Za-z0-9._-' '-')
PREFIX="rusefi-${SAFE_REF}-${VARIANT}"
if [ "$RESOLVE_ONLY" = 1 ]; then echo "$REF"; exit 0; fi

mkdir -p "$WORK"
WORK=$(cd "$WORK" && pwd -P)
OUT=${OUT:-$WORK/out}
mkdir -p "$OUT"; OUT=$(cd "$OUT" && pwd -P)
rm -f "$OUT/${PREFIX}".* "$OUT/${PREFIX}"-base.msq "$OUT/SHA256SUMS"
echo "rusEFI ref: $REF  variant: $VARIANT  out: $OUT"

# ---- tool checks -----------------------------------------------------------
log "Checking host tools"
export PATH="$PATH:/usr/sbin"
missing=()
for t in git curl make python3 zip 7z mcopy mkfs.fat xxd sha256sum strings java; do
  command -v "$t" >/dev/null 2>&1 || missing+=("$t")
done
[ ${#missing[@]} -eq 0 ] || die "missing tools: ${missing[*]}
 Ubuntu: sudo apt-get install -y make git curl python3 zip 7zip mtools dosfstools xxd binutils openjdk-17-jdk
 (no root: apt-get download <pkg> && dpkg -x <pkg>.deb ~/opt/root, then add ~/opt/root/usr/bin to PATH)"
JAVA_MAJOR=$(java -version 2>&1 | sed -nE '1s/.*version "([0-9]+).*/\1/p')
[ "${JAVA_MAJOR:-0}" -ge 17 ] || die "Java 17+ required (found ${JAVA_MAJOR:-none}); set JAVA_HOME/PATH"

# ---- pinned toolchain ------------------------------------------------------
log "ARM toolchain ${TOOLCHAIN_NAME}"
TC_BIN="$TOOLCHAIN_DIR/$TOOLCHAIN_NAME/bin"
if [ ! -x "$TC_BIN/arm-none-eabi-gcc" ]; then
  mkdir -p "$TOOLCHAIN_DIR"
  tarball="$TOOLCHAIN_DIR/${TOOLCHAIN_NAME}.tar.xz"
  curl -fL --retry 3 -o "$tarball" "$TOOLCHAIN_URL"
  echo "${TOOLCHAIN_SHA256}  $tarball" | sha256sum -c -
  tar -xJf "$tarball" -C "$TOOLCHAIN_DIR"
  rm -f "$tarball"
fi
export PATH="$TC_BIN:$PATH"
arm-none-eabi-gcc --version | head -1
arm-none-eabi-gcc --version | grep -q '14\.2\.1' || die "unexpected arm-none-eabi-gcc version"

# ---- ECU_Build board config -------------------------------------------------
if [ -z "$BOARD_SRC" ] && [ -z "$ECU_BUILD_DIR" ] && [ -d "$SCRIPT_DIR/board-overlay/$VARIANT" ]; then
  BOARD_SRC="$SCRIPT_DIR/board-overlay/$VARIANT"
fi
if [ -z "$BOARD_SRC" ]; then
  if [ -z "$ECU_BUILD_DIR" ]; then
    ECU_BUILD_DIR="$WORK/ECU_Build"
    log "Fetching ECU_Build@$ECU_BUILD_REF"
    ok=0
    for url in "${ECU_BUILD_REPOS[@]}"; do
      rm -rf "$ECU_BUILD_DIR"; git init -q "$ECU_BUILD_DIR"
      git -C "$ECU_BUILD_DIR" remote add origin "$url"
      if GIT_TERMINAL_PROMPT=0 GIT_SSH_COMMAND="ssh -o BatchMode=yes" \
         git -C "$ECU_BUILD_DIR" fetch -q --depth 1 origin "$ECU_BUILD_REF" 2>/dev/null; then ok=1; break; fi
    done
    [ "$ok" = 1 ] || die "cannot fetch private opelpanfan/ECU_Build (no credentials). Use --ecu-build-dir/--board-src,
 or provide scripts/rusefi/board-overlay/$VARIANT (see scripts/rusefi/README.md)"
    git -C "$ECU_BUILD_DIR" checkout -q --force FETCH_HEAD
  fi
  BOARD_SRC="$ECU_BUILD_DIR/config/$VARIANT"
fi
[ -f "$BOARD_SRC/board.mk" ] || die "no board config for variant $VARIANT ($BOARD_SRC)"
BOARD_SRC=$(cd "$BOARD_SRC" && pwd -P)
echo "board config: $BOARD_SRC"

# ---- rusEFI checkout (shallow, only needed submodules) -----------------------
if [ -z "$RUSEFI_DIR" ]; then
  RUSEFI_DIR="$WORK/rusefi"
  log "Fetching rusEFI@$REF (shallow)"
  if [ ! -d "$RUSEFI_DIR/.git" ]; then git init -q "$RUSEFI_DIR"; git -C "$RUSEFI_DIR" remote add origin "$RUSEFI_REPO"; fi
  if [[ "$REF" =~ ^[0-9a-f]{7,39}$ ]]; then
    # abbreviated sha: needs history to expand
    git -C "$RUSEFI_DIR" fetch -q --filter=blob:none origin
    REF_SHA=$(git -C "$RUSEFI_DIR" rev-parse --verify "${REF}^{commit}")
    git -C "$RUSEFI_DIR" fetch -q --depth 1 origin "$REF_SHA"
  else
    git -C "$RUSEFI_DIR" fetch -q --depth 1 origin "$REF" || \
      git -C "$RUSEFI_DIR" fetch -q --depth 1 origin "refs/tags/$REF:refs/tags/$REF"
  fi
  git -C "$RUSEFI_DIR" checkout -q --force --detach FETCH_HEAD 2>/dev/null || git -C "$RUSEFI_DIR" checkout -q --force --detach "refs/tags/$REF"
  git -C "$RUSEFI_DIR" clean -qfdx -e firmware/build -e firmware/.dep
  ( cd "$RUSEFI_DIR" && git submodule sync -q && \
    git -c submodule.fetchJobs="$(nproc)" submodule update -q --init --depth 1 --force "${SUBMODULES[@]}" )
fi
RUSEFI_DIR=$(cd "$RUSEFI_DIR" && pwd -P)
FW="$RUSEFI_DIR/firmware"
RUSEFI_SHA=$(git -C "$RUSEFI_DIR" rev-parse HEAD)
echo "rusEFI commit: $RUSEFI_SHA"
# gen_signature.sh uses `git branch --show-current`, falling back to $AUTOMATION_REF when detached
if [ -z "$SIG_BRANCH" ]; then
  if [[ "$REF" =~ ^[0-9a-f]{7,40}$ ]]; then SIG_BRANCH=master; else SIG_BRANCH=$REF; fi
fi
export AUTOMATION_REF="$SIG_BRANCH"
# reproducible builds: gcc uses SOURCE_DATE_EPOCH for __DATE__/__TIME__
SOURCE_DATE_EPOCH=${SOURCE_DATE_EPOCH:-$(git -C "$RUSEFI_DIR" log -1 --format=%ct HEAD)}
export SOURCE_DATE_EPOCH
cur=$(git -C "$RUSEFI_DIR" branch --show-current)
if [ -n "$cur" ] && [ "$cur" != "$SIG_BRANCH" ]; then
  echo "WARN: rusEFI checkout is on branch '$cur'; signature will use '$cur', not '$SIG_BRANCH'"
fi

# ---- repo patches (scripts/rusefi/patches/*.patch, applied to the clean checkout) ----
for p in "$SCRIPT_DIR"/patches/*.patch; do
  [ -e "$p" ] || continue
  if git -C "$RUSEFI_DIR" apply --reverse --check "$p" 2>/dev/null; then
    echo "patch already applied: ${p##*/}"
  else
    git -C "$RUSEFI_DIR" apply "$p"; echo "applied patch: ${p##*/}"
  fi
done

# ---- console jar (optional, baseline step) -----------------------------------
if [ "$WITH_CONSOLE" = 1 ]; then
  log "Building console jar"
  ( cd "$RUSEFI_DIR" && ./gradlew --no-daemon :ui:shadowJar )   # gradlew moved to repo root upstream
fi

# ---- board config (baseline steps + current-upstream fixups) ---------------
log "Preparing board config $VARIANT -> config/boards/$SHORT_BOARD_NAME"
BD="$FW/config/boards/$SHORT_BOARD_NAME"
mkdir -p "$BD"
cp -r "$BOARD_SRC/." "$BD/"
sed -i 's/core48/core8/g' "$BD/board.mk" "$BD/board.h"
grep -q 'engine_type_e::MINIMAL_PINS' "$BD/board.mk" || sed -i 's/MINIMAL_PINS/engine_type_e::MINIMAL_PINS/g' "$BD/board.mk"
# current PinoutLogic rejects unknown yaml keys: strip doc-only keys
if compgen -G "$BD/connectors/*.yaml" >/dev/null; then
  sed -i -E '/^[[:space:]]+(pin_name|alternative1|alternative2):/d' "$BD"/connectors/*.yaml
fi
# board-API adaptation (setup_custom_board_overrides(), setLuaScript(), includes);
# no-op for the already-ported board-overlay sources, needed for raw ECU_Build sources
python3 "$SCRIPT_DIR/rusefi_board_fixups.py" "$BD/board_configuration.cpp"

# ---- build -------------------------------------------------------------------
log "Building (make -j$(nproc))"
cd "$FW"
rm -rf .dep build pch/pch.h.gch.sh
make clean >/dev/null 2>&1 || true
# BOARD_DIR explicit: the meta-env fallback yields "././config/boards/core8" which breaks
# the generated connectors target. compile.sh already runs make -j$(nproc).
BOARD_DIR="config/boards/$SHORT_BOARD_NAME" bash bin/compile.sh "config/boards/$SHORT_BOARD_NAME/board.env"

# DFU image (upstream only makes it in bundle mode); same hex2dfu call as bundle.mk
BASE=$(arm-none-eabi-objdump -h -j .vectors build/rusefi.elf | awk '/.vectors/ {print $5}')
CK=$(printf '0x%X' $((0x$BASE + 0x1C)))
../misc/encedo_hex2dfu/hex2dfu.bin -i build/rusefi.hex -c "$CK" -o build/rusefi.dfu >/dev/null

# ---- signature check: firmware TS signature must equal generated .ini signature -
log "Checking TunerStudio signature"
INI="tunerstudio/generated/rusefi_${SHORT_BOARD_NAME}.ini"
[ -f "$INI" ] || die "missing $INI"
INI_SIG=$(sed -nE 's/^[[:space:]]*signature[[:space:]]*=[[:space:]]*"([^"]+)".*/\1/p' "$INI" | head -1)
HDR_SIG=$(sed -nE 's/^#define[[:space:]]+TS_SIGNATURE[[:space:]]+"([^"]+)".*/\1/p' "controllers/generated/signature_${SHORT_BOARD_NAME}.h" 2>/dev/null | head -1 || true)
[ -n "$INI_SIG" ] || die "no signature= in $INI"
if ! LC_ALL=C grep -aqF -- "$INI_SIG" build/rusefi.bin; then
  echo "ini signature : $INI_SIG"; echo "fw signatures :"; strings -n 12 build/rusefi.bin | grep -E "^rusEFI .*\.${SHORT_BOARD_NAME}\." || true
  die "signature mismatch: firmware does not contain the .ini signature"
fi
if [ -n "$HDR_SIG" ] && [ "$HDR_SIG" != "$INI_SIG" ]; then die "signature mismatch: header '$HDR_SIG' vs ini '$INI_SIG'"; fi
echo "OK: $INI_SIG"

# ---- base tune: rusEFI canned-tune process (simulator default config -> .msq) ----------
# The simulator is built with this board's board_configuration.cpp (via a generated
# sim-only board_common.mk + patches/0002), runs 10 s and dumps its config image;
# tune-tools WriteSimulatorConfiguration converts it to .msq using the board .ini.
MSQ=""
if [ "$BASE_TUNE" = 1 ]; then
  log "Generating base tune"
  cat > "$BD/board_common.mk" <<'MK'
# generated by OPF scripts/rusefi/build_rusefi_core48.sh: simulator-only (base tune generation)
BOARDCPPSRC += $(PROJECT_DIR)/config/boards/core8/board_configuration.cpp
OPF_SERIAL_SPEED := $(or $(shell sed -nE 's/^\#define[[:space:]]+SERIAL_SPEED[[:space:]]+([0-9]+).*/\1/p' $(BOARD_DIR)/board.h),115200)
DDEFS += -DSERIAL_SPEED=$(OPF_SERIAL_SPEED)
MK
  SIM="$RUSEFI_DIR/simulator"
  rm -rf "$SIM/build" "$SIM/.dep" "$SIM"/generated/simulator_tune_image*.bin "$SIM/generated/opf"
  # shellcheck disable=SC2016
  SIM_CMD='make -r OS=Linux SUBMAKE=yes -j"$(nproc)" >sim_build.log 2>&1 || { tail -40 sim_build.log; exit 1; }; timeout 300 ./build/rusefi_simulator 10 >sim_run.log 2>&1 || { tail -40 sim_run.log; exit 1; }'
  if [ "$SIM_DOCKER" = auto ]; then
    if printf 'int main(){return 0;}' | g++ -m32 -x c++ - -o /dev/null >/dev/null 2>&1; then SIM_DOCKER=0
    elif command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1; then SIM_DOCKER=1
    else die "base tune needs gcc-multilib/g++-multilib (or docker); use --no-base-tune to skip"; fi
  fi
  if [ "$SIM_DOCKER" = 1 ]; then
    echo "simulator: docker (opf-rusefi-sim:24.04)"
    docker build -q -t opf-rusefi-sim:24.04 - < "$SCRIPT_DIR/simulator.Dockerfile" >/dev/null
    docker run --rm --user "$(id -u):$(id -g)" -v "$RUSEFI_DIR:$RUSEFI_DIR" -w "$SIM" \
      -e BOARD_DIR="$BD" -e SHORT_BOARD_NAME="$SHORT_BOARD_NAME" -e SOURCE_DATE_EPOCH \
      opf-rusefi-sim:24.04 bash -c "$SIM_CMD"
  else
    echo "simulator: native gcc -m32"
    ( cd "$SIM" && BOARD_DIR="$BD" SHORT_BOARD_NAME="$SHORT_BOARD_NAME" bash -c "$SIM_CMD" )
  fi
  [ -f "$SIM/generated/simulator_tune_image.bin" ] || die "simulator did not write generated/simulator_tune_image.bin"
  ( cd "$RUSEFI_DIR" && ./gradlew --no-daemon -q :tune-tools:shadowJar )
  # output folder must be relative to simulator/ (tune-tools prefixes ROOT_FOLDER=../simulator/)
  ( cd "$SIM" && DEFAULT_TUNE_OUTPUT_FOLDER=generated/opf/ bash write_tune.sh "../firmware/$INI" >write_tune.log 2>&1 ) || {
    tail -30 "$SIM/write_tune.log"; die "write_tune.sh failed"; }
  MSQ="$SIM/generated/opf/simulator_tune.msq"
  [ -s "$MSQ" ] || die "no base tune produced"
  MSQ_SIG=$(sed -nE 's/.*signature="([^"]+)".*/\1/p' "$MSQ" | head -1)
  [ "$MSQ_SIG" = "$INI_SIG" ] || die "base tune signature '$MSQ_SIG' != ini '$INI_SIG'"
  echo "OK: base tune $(grep -c '<constant' "$MSQ") constants, signature $MSQ_SIG"
fi

# ---- collect artifacts -----------------------------------------------------
log "Collecting artifacts -> $OUT"
cp "$INI" "$OUT/${PREFIX}.ini"
for e in bin hex srec dfu; do
  [ -f "build/rusefi.$e" ] && cp "build/rusefi.$e" "$OUT/${PREFIX}.$e"
done
cp build/rusefi.elf "$OUT/${PREFIX}.elf"
[ -n "$MSQ" ] && cp "$MSQ" "$OUT/${PREFIX}-base.msq"
if [ "$WITH_CONSOLE" = 1 ] && [ -f "$RUSEFI_DIR/java_console_binary/rusefi_console.jar" ]; then
  cp "$RUSEFI_DIR/java_console_binary/rusefi_console.jar" "$OUT/${PREFIX}.console.jar"
fi
{
  echo "rusefi_ref=$REF"
  echo "rusefi_commit=$RUSEFI_SHA"
  echo "variant=$VARIANT"
  echo "board_src=$BOARD_SRC"
  echo "board_src_commit=$(git -C "$BOARD_SRC" rev-parse HEAD 2>/dev/null || echo unknown)"
  echo "ts_signature=$INI_SIG"
  echo "signature_branch=$SIG_BRANCH"
  echo "toolchain=$TOOLCHAIN_NAME"
  echo "java=$(java -version 2>&1 | head -1)"
  echo "source_date_epoch=$SOURCE_DATE_EPOCH"
  echo "built_utc=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$OUT/${PREFIX}.build-info.txt"
( cd "$OUT" && sha256sum "${PREFIX}"[.-]* > SHA256SUMS && cat SHA256SUMS )

if [ -n "${GITHUB_OUTPUT:-}" ]; then
  { echo "prefix=$PREFIX"; echo "rusefi_ref=$REF"; echo "rusefi_commit=$RUSEFI_SHA"; echo "signature=$INI_SIG"; echo "out=$OUT"; } >> "$GITHUB_OUTPUT"
fi
log "DONE: $PREFIX"
