#!/usr/bin/env bash
# Build Speeduino firmware for OPF boards from a clean, pinned upstream (noisymime/speeduino) checkout.
#
#   build/build_speeduino.sh [options] [speeduino_tag]
#
#   -b, --boards LIST   comma separated board variants from build/boards/*/speeduino/board.json (default: all)
#   -w, --work DIR      work dir (default: <repo>/.work-speeduino, or $SPEEDUINO_WORK)
#   -o, --out DIR       output root, artifacts go to DIR/<board>/ (default: <repo>/out)
#   --resolve-only      print the resolved Speeduino tag and exit
#   tag                 Speeduino git tag/branch (default: $SPEEDUINO_TAG, else the latest GitHub release)
#
# Everything OPF specific (pin map, PlatformIO env, OPF sources, TunerStudio ini entries, base tune) is
# generated here from build/boards/<board>/speeduino/board.json and build/speeduino/common/. Upstream files
# are modified only via anchored edits (embedded Python below); if an anchor is missing or ambiguous the
# build stops with "PATCH CONFLICT" instead of producing a silently wrong firmware.
#
# Toolchain pins (override via env): PLATFORMIO_VERSION (checked, not installed), STM32_PLATFORM.
set -euo pipefail

SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO_ROOT=$(cd "$SCRIPT_DIR/.." && pwd)
UPSTREAM_REPO=${SPEEDUINO_REPO:-noisymime/speeduino}
# ststm32 19.5.0 = the platform PlatformIO resolved for upstream's unpinned "platform = ststm32" when 202501.7 was released
STM32_PLATFORM=${STM32_PLATFORM:-platformio/ststm32@19.5.0}
PLATFORMIO_VERSION=${PLATFORMIO_VERSION:-}
WORK=${SPEEDUINO_WORK:-$REPO_ROOT/.work-speeduino}
OUT_ROOT=$REPO_ROOT/out
BOARDS=""
TAG=${SPEEDUINO_TAG:-}
RESOLVE_ONLY=false

die() { echo "ERROR: $*" >&2; exit 1; }
log() { echo "==> $*"; }

while [ $# -gt 0 ]; do
  case "$1" in
    -b|--boards) BOARDS=$2; shift 2 ;;
    -w|--work) WORK=$2; shift 2 ;;
    -o|--out) OUT_ROOT=$2; shift 2 ;;
    --resolve-only) RESOLVE_ONLY=true; shift ;;
    -h|--help) sed -n '2,20p' "$0"; exit 0 ;;
    -*) die "unknown option $1" ;;
    *) TAG=$1; shift ;;
  esac
done

gh_api() { # GET from the GitHub API, authenticated if GITHUB_TOKEN/GH_TOKEN is set (never printed)
  local tok=${GITHUB_TOKEN:-${GH_TOKEN:-}}
  if [ -n "$tok" ]; then curl -fsSL -H "Authorization: Bearer $tok" -H "Accept: application/vnd.github+json" "https://api.github.com/$1"
  else curl -fsSL -H "Accept: application/vnd.github+json" "https://api.github.com/$1"; fi
}

if [ -z "$TAG" ]; then
  TAG=$(gh_api "repos/$UPSTREAM_REPO/releases/latest" | python3 -c 'import json,sys; print(json.load(sys.stdin)["tag_name"])') \
    || die "could not resolve the latest $UPSTREAM_REPO release"
fi
[[ "$TAG" =~ ^[A-Za-z0-9._/-]+$ ]] || die "invalid tag '$TAG'"
if $RESOLVE_ONLY; then echo "$TAG"; exit 0; fi

for t in git python3 pio sha256sum; do command -v "$t" >/dev/null || die "'$t' not found in PATH"; done
PIO_VER=$(pio --version | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
if [ -n "$PLATFORMIO_VERSION" ] && [ "$PIO_VER" != "$PLATFORMIO_VERSION" ]; then
  die "PlatformIO $PIO_VER found, $PLATFORMIO_VERSION required (pip install platformio==$PLATFORMIO_VERSION)"
fi

if [ -z "$BOARDS" ]; then
  BOARDS=$(cd "$SCRIPT_DIR/boards" && for f in */speeduino/board.json; do printf '%s,' "${f%%/*}"; done)
  BOARDS=${BOARDS%,}
fi
[ -n "$BOARDS" ] || die "no boards found under $SCRIPT_DIR/boards/*/speeduino/board.json"

mkdir -p "$WORK"
WORK=$(cd "$WORK" && pwd)
mkdir -p "$OUT_ROOT"
OUT_ROOT=$(cd "$OUT_ROOT" && pwd)
TOOL="$WORK/opf_speeduino.py"

# ---------------------------------------------------------------------------------------------------------
# Embedded generator: anchored source edits, PlatformIO env, TunerStudio ini edits and base tune generation.
# ---------------------------------------------------------------------------------------------------------
cat > "$TOOL" <<'PY'
import configparser, datetime, json, os, re, shutil, sys
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape, quoteattr

class Conflict(Exception):
    pass

def conflict(path, what, detail):
    raise Conflict("PATCH CONFLICT in %s: %s (%s). Upstream Speeduino changed here; update build/build_speeduino.sh." % (path, what, detail))

def rd(p, enc="utf-8"):
    with open(p, encoding=enc, newline="") as f:
        return f.read()

def wr(p, s, enc="utf-8"):
    with open(p, "w", encoding=enc, newline="") as f:
        f.write(s)

# ---------------- C/C++ helpers ----------------
def func_span(src, path, sig_regex, name):
    """Return (body_start, body_end) of the single function matching sig_regex (body_start is just after '{')."""
    ms = list(re.finditer(sig_regex, src))
    if len(ms) != 1:
        conflict(path, "function %s" % name, "signature found %d times, expected 1" % len(ms))
    i = ms[0].end()
    while i < len(src) and src[i] != "{":
        i += 1
    if i >= len(src):
        conflict(path, "function %s" % name, "no opening brace")
    start = i + 1
    depth, j, n = 1, start, len(src)
    while j < n and depth:
        c = src[j]
        if src.startswith("//", j):
            j = src.find("\n", j); j = n if j < 0 else j; continue
        if src.startswith("/*", j):
            j = src.find("*/", j + 2); j = n if j < 0 else j + 2; continue
        if c in "\"'":
            k = j + 1
            while k < n and src[k] != c:
                k += 2 if src[k] == "\\" else 1
            j = k + 1; continue
        if c == "{": depth += 1
        elif c == "}": depth -= 1
        j += 1
    if depth:
        conflict(path, "function %s" % name, "unbalanced braces")
    return start, j - 1

def edit(src, path, pattern, repl, what, lo=0, hi=None, flags=re.M):
    """Replace exactly one regex match of pattern inside src[lo:hi]. repl may use \\1 etc."""
    hi = len(src) if hi is None else hi
    region = src[lo:hi]
    ms = list(re.finditer(pattern, region, flags))
    if len(ms) != 1:
        conflict(path, what, "anchor /%s/ found %d times, expected 1" % (pattern[:80], len(ms)))
    m = ms[0]
    new = m.expand(repl)
    return src[:lo + m.start()] + new + src[lo + m.end():]

def insert_at_body_start(src, path, sig, name, code):
    s, _ = func_span(src, path, sig, name)
    return src[:s] + "\n" + code + src[s:]

# ---------------- apply board ----------------
def load_board(board_dir):
    with open(os.path.join(board_dir, "board.json")) as f:
        b = json.load(f)
    for k in ("name", "board_id", "ts_layout_name", "pio_base_env", "pio_board", "mcu_guard", "pins", "unused_pin"):
        if k not in b:
            raise SystemExit("ERROR: %s/board.json is missing '%s'" % (board_dir, k))
    return b

def apply_board(tree, board_dir, common_dir, platform):
    b = load_board(board_dir)
    fw = os.path.join(tree, "speeduino")
    bid = int(b["board_id"])
    for f in ("init.cpp", "board_stm32_official.h", "board_stm32_official.cpp", "sensors.cpp", "speeduino.ino", "globals.h"):
        p = os.path.join(fw, f)
        if not os.path.isfile(p):
            raise Conflict("PATCH CONFLICT: expected upstream file speeduino/%s is missing" % f)
        if "OPF_BOARD" in rd(p):
            raise SystemExit("ERROR: %s already contains OPF edits - the work tree is not a clean upstream checkout" % p)

    # 1) OPF sources (OPF-owned files, not copies of upstream files)
    for name in ("opf_board.h", "opf_board.cpp"):
        shutil.copy2(os.path.join(common_dir, name), os.path.join(fw, name))
    for d in ("LPS22HH", "LPS25HB"):
        dst = os.path.join(fw, "src", d)
        if os.path.exists(dst):
            raise Conflict("PATCH CONFLICT: upstream now ships speeduino/src/%s - reconcile with build/speeduino/common/src/%s" % (d, d))
        shutil.copytree(os.path.join(common_dir, "src", d), dst)

    # 2) init.cpp: board id forcing + generated case in setPinMapping()
    p = os.path.join(fw, "init.cpp"); s = rd(p)
    globals_h = rd(os.path.join(fw, "globals.h"))
    pinvars = set(re.findall(r"^\s*extern\s+(?:byte|uint8_t)\s+(pin\w+)\s*;", globals_h, re.M))
    allvars = list(b["pins"].keys()) + list(b.get("unused_pin_vars", []))
    missing = [v for v in allvars if v not in pinvars]
    if missing:
        conflict("speeduino/globals.h", "pin variables", "not declared upstream: %s" % ", ".join(missing))
    dup = set(b["pins"]) & set(b.get("unused_pin_vars", []))
    if dup:
        raise SystemExit("ERROR: board.json lists %s both as used and unused" % ", ".join(sorted(dup)))
    sig = r"\bvoid\s+setPinMapping\s*\(\s*byte\s+boardID\s*\)"
    fs, fe = func_span(s, p, sig, "setPinMapping")
    if re.search(r"^\s*case\s+%d\s*:" % bid, s[fs:fe], re.M):
        conflict(p, "setPinMapping()", "upstream already uses board id %d" % bid)
    lines = ["    case %d:" % bid,
             "      #if defined(%s) && defined(OPF_BOARD)" % b["mcu_guard"],
             "      // %s - generated by build/build_speeduino.sh from build/boards/%s/speeduino/board.json" % (b.get("description", b["name"]), b["name"]),
             "      // Pins not used on this board point at an unconnected pin instead of the default 0 (PA0 on STM32)."]
    for v in b.get("unused_pin_vars", []):
        lines.append("      %s = %s;" % (v, b["unused_pin"]))
    for v, pin in b["pins"].items():
        if not re.match(r"^P[A-K]\d{1,2}$", pin):
            raise SystemExit("ERROR: board.json pin %s=%s is not an STM32 pin name" % (v, pin))
        lines.append("      %s = %s;" % (v, pin))
    lines += ["      #endif", "      break;", ""]
    s = edit(s, p, r"^(?=[ \t]*case\s+60\s*:)", "\n".join(lines) + "\n", "setPinMapping() 'case 60:' anchor", fs, fe)
    s = insert_at_body_start(s, p, sig, "setPinMapping",
        "  #if defined(OPF_BOARD)\n"
        "  //OPF firmware only runs on OPF hardware: always use the OPF pin map (also on first boot / blank flash)\n"
        "  boardID = OPF_BOARD_ID;\n"
        "  configPage2.pinMapping = OPF_BOARD_ID;\n"
        "  #endif\n")
    wr(p, s)

    # 3) board_stm32_official.h: SD logging off, SPI flash EEPROM, reserved pins, OPF header
    p = os.path.join(fw, "board_stm32_official.h"); s = rd(p)
    s = edit(s, p, r"^#if defined\(STM32F407xx\)(\s*\n\s*//Comment out this to disable SD logging[^\n]*\n\s*#define SD_LOGGING)",
             r"#if defined(STM32F407xx) && !defined(OPF_BOARD)\1", "SD_LOGGING block")
    s = edit(s, p, r"^(//#define FRAM_AS_EEPROM[^\n]*\n)",
             r"\1#if defined(OPF_BOARD) && defined(OPF_SPI_FLASH_CS)\n  #define USE_SPI_EEPROM OPF_SPI_FLASH_CS /*OPF: W25Qxx SPI flash on OPF_SPI_FLASH_* pins*/\n#endif\n",
             "EEPROM selection comment block")
    s = edit(s, p, r"^([ \t]*)#ifdef USE_SPI_EEPROM\n(\s*#define pinIsReserved\(pin\))",
             r"\1#if defined(OPF_BOARD)\n"
             r"    #define pinIsReserved(pin)  ( ((pin) == PA11) || ((pin) == PA12) || ((pin) == OPF_SPI_FLASH_MOSI) || ((pin) == OPF_SPI_FLASH_MISO) || ((pin) == OPF_SPI_FLASH_SCK) || ((pin) == OPF_SPI_FLASH_CS) ) //USB + OPF SPI flash" "\n"
             r"\1#elif defined(USE_SPI_EEPROM)" "\n" r"\2",
             "pinIsReserved() for USE_SPI_EEPROM")
    s = edit(s, p, r"^(#endif //CORE_STM32\s*\n)", "#if defined(OPF_BOARD)\n  #include \"opf_board.h\"\n#endif\n\\1", "'#endif //CORE_STM32'")
    wr(p, s)

    # 4) board_stm32_official.cpp: SPI flash bus, board init hook
    p = os.path.join(fw, "board_stm32_official.cpp"); s = rd(p)
    s = edit(s, p, r"^([ \t]*)#if defined\(STM32F407xx\)\n(\s*SPIClass SPI_for_flash\(PB5, PB4, PB3\);)",
             r"\1#if defined(OPF_BOARD)" "\n" r"\1  SPIClass SPI_for_flash(OPF_SPI_FLASH_MOSI, OPF_SPI_FLASH_MISO, OPF_SPI_FLASH_SCK);" "\n" r"\1#elif defined(STM32F407xx)" "\n" r"\2",
             "SPI_for_flash definition")
    s = insert_at_body_start(s, p, r"\bvoid\s+initBoard\s*\(\s*(?:void)?\s*\)", "initBoard",
        "    #if defined(OPF_BOARD)\n    opfBoardInit(); //OPF: status LEDs, onboard baro, CAN2\n    #endif\n")
    wr(p, s)

    # 5) sensors.cpp: onboard I2C barometer
    p = os.path.join(fw, "sensors.cpp"); s = rd(p)
    hook = "  #if defined(OPF_BOARD)\n  if (opfReadBaro()) { return; } //OPF: onboard I2C baro sensor\n  #endif\n"
    s = insert_at_body_start(s, p, r"\bvoid\s+readBaro\s*\(\s*void\s*\)", "readBaro", hook)
    fs, fe = func_span(s, p, r"\bvoid\s+initialiseMAPBaro\s*\(\s*void\s*\)", "initialiseMAPBaro")
    s = edit(s, p, r"^(?=[ \t]*//Initialise baro\s*$)", hook, "initialiseMAPBaro() '//Initialise baro' anchor", fs, fe)
    wr(p, s)

    # 6) speeduino.ino: per-loop board hook
    p = os.path.join(fw, "speeduino.ino"); s = rd(p)
    fs, fe = func_span(s, p, r"\bloop\s*\(\s*void\s*\)\s*(?=\{)", "loop")
    s = edit(s, p, r"^([ \t]*LOOP_TIMER = TIMER_mask;[^\n]*\n)",
             "\\1      #if defined(OPF_BOARD)\n      opfBoardLoop(); //OPF: status LEDs\n      #endif\n", "loop() 'LOOP_TIMER = TIMER_mask;'", fs, fe)
    wr(p, s)

    # 7) platformio.ini: own env derived from upstream's base env
    p = os.path.join(tree, "platformio.ini"); txt = rd(p)
    cp = configparser.ConfigParser(interpolation=None, strict=False)
    cp.optionxform = str
    cp.read_string(txt)
    base = "env:" + b["pio_base_env"]
    if not cp.has_section(base):
        conflict(p, "[%s]" % base, "section not found")
    env = "opf_" + b["name"]
    if cp.has_section("env:" + env):
        raise SystemExit("ERROR: platformio.ini already has [env:%s]" % env)
    src = dict(cp.items(base))
    for k in ("framework", "lib_deps", "build_flags"):
        if k not in src:
            conflict(p, "[%s] %s" % (base, k), "option missing")
    flags = " ".join(src["build_flags"].split())
    defs = ["-DOPF_BOARD", "-DOPF_BOARD_ID=%d" % bid, '-DOPF_BOARD_NAME=\\"%s\\"' % b["name"]]
    for k, v in b.get("defines", {}).items():
        defs.append("-D%s=%s" % (k, v))
    out = ["", "; ---- generated by OPF build/build_speeduino.sh from build/boards/%s/speeduino/board.json (based on [%s]) ----" % (b["name"], base),
           "[env:%s]" % env, "platform = %s" % platform, "board = %s" % b["pio_board"]]
    for k, v in src.items():
        if k in ("platform", "board", "build_flags"):
            continue
        out.append("%s = %s" % (k, " ".join(v.split()) if "\n" not in v.strip() else v))
    out.append("build_flags = %s %s" % (flags, " ".join(defs)))
    txt = txt.rstrip("\n") + "\n" + "\n".join(out) + "\n"
    wr(p, txt)
    return env

# ---------------- TunerStudio ini ----------------
def ini_edit(src_ini, dst_ini, board_dir):
    b = load_board(board_dir)
    bid = int(b["board_id"]); name = b["ts_layout_name"]
    s = rd(src_ini, "latin-1")
    # pinLayouts #define (the active one, not the commented copy)
    ms = list(re.finditer(r"^([ \t]*#define\s+pinLayouts\s*=\s*)(.*)$", s, re.M))
    if len(ms) != 1:
        conflict(src_ini, "'#define pinLayouts'", "found %d times, expected 1" % len(ms))
    m = ms[0]
    toks = list(re.finditer(r'"[^"]*"|\$\w+', m.group(2)))
    if len(toks) <= bid or toks[bid].group(0).startswith("$"):
        conflict(src_ini, "pinLayouts", "index %d is not an explicit entry" % bid)
    cur = toks[bid].group(0)
    if cur == '"%s"' % name:
        raise SystemExit("ERROR: ini already contains %s at index %d (not a clean upstream ini?)" % (name, bid))
    if cur != '"INVALID"':
        conflict(src_ini, "pinLayouts[%d]" % bid, "upstream now uses this id for %s" % cur)
    if '"%s"' % name in m.group(2):
        conflict(src_ini, "pinLayouts", "name %s already used by another board" % name)
    body = m.group(2)
    body = body[:toks[bid].start()] + '"%s"' % name + body[toks[bid].end():]
    s = s[:m.start(2)] + body + s[m.end(2):]
    # board capability arrays
    for arr, key in (("boardFuelOutputs", "fuel_outputs"), ("boardIgnOutputs", "ign_outputs"), ("boardHasRTC", "has_rtc")):
        if key not in b:
            continue
        ms = list(re.finditer(r"^([ \t]*defaultValue\s*=\s*%s\s*,)(.*)$" % arr, s, re.M))
        if len(ms) != 1:
            conflict(src_ini, "defaultValue %s" % arr, "found %d times" % len(ms))
        m = ms[0]
        vals = list(re.finditer(r"\S+", m.group(2)))
        if len(vals) <= bid:
            conflict(src_ini, arr, "has only %d entries" % len(vals))
        v = vals[bid]; new = str(int(b[key]))
        body = m.group(2)
        width = len(v.group(0))
        body = body[:v.start()] + new.ljust(width) + body[v.end():] if len(new) <= width else body[:v.start()] + new + body[v.end():]
        s = s[:m.start(2)] + body + s[m.end(2):]
    wr(dst_ini, s, "latin-1")
    sigm = re.search(r'^\s*signature\s*=\s*"([^"]+)"', s, re.M)
    return sigm.group(1) if sigm else None

# ---------------- base tune ----------------
def ini_constants(ini_text, symbols):
    """Very small TS ini reader: [Constants] page/constant definitions, #define macros, defaultValue lines."""
    defines, consts, defaults, page_sizes = {}, {}, {}, []
    section, page = None, None
    stack = []  # (active, taken)
    for raw in ini_text.splitlines():
        line = raw.split(";", 1)[0].rstrip() if not raw.lstrip().startswith("#") else raw.strip()
        st = line.strip()
        if not st:
            continue
        if st.startswith("#"):
            tok = st.split()
            d = tok[0]
            parent = all(a for a, _ in stack)
            if d == "#if":
                c = tok[1] in symbols; stack.append((c, c)); continue
            if d == "#elif":
                a, taken = stack.pop(); c = (not taken) and tok[1] in symbols; stack.append((c, taken or c)); continue
            if d == "#else":
                a, taken = stack.pop(); stack.append((not taken, True)); continue
            if d == "#endif":
                stack.pop(); continue
            if d == "#define" and parent:
                mm = re.match(r"#define\s+(\w+)\s*=\s*(.*)$", st)
                if mm: defines[mm.group(1)] = mm.group(2)
            continue
        if not all(a for a, _ in stack):
            continue
        if st.startswith("["):
            section = st.strip("[]"); continue
        if section == "Constants":
            mm = re.match(r"page\s*=\s*(\d+)", st)
            if mm: page = int(mm.group(1)); continue
            mm = re.match(r"pageSize\s*=\s*(.*)", st)
            if mm: page_sizes = [int(x) for x in re.findall(r"\d+", mm.group(1))]; continue
            mm = re.match(r"(\w+)\s*=\s*(scalar|bits|array|string)\s*,(.*)$", st)
            if mm and page is not None and mm.group(1) not in consts:
                consts[mm.group(1)] = (page, mm.group(2), mm.group(3))
        elif section == "ConstantsExtensions":
            mm = re.match(r"defaultValue\s*=\s*(\w+)\s*,\s*(.*)$", st)
            if mm: defaults[mm.group(1)] = mm.group(2).strip()
    return defines, consts, defaults, page_sizes

def split_fields(rest):
    return [f.strip() for f in re.findall(r'\s*("[^"]*"|\[[^\]]*\]|\{[^}]*\}|[^,]+)', rest)]

def expand_options(fields, defines):
    opts = []
    for f in fields:
        if f.startswith("$"):
            opts += expand_options(split_fields(defines.get(f[1:], "")), defines)
        elif f.startswith('"'):
            opts.append(f)
    return opts

def num(x):
    try: return float(x)
    except Exception: return None

def gen_tune(ini_path, seed_path, board_dir, out_path, fw_info, write_date, symbols):
    b = load_board(board_dir)
    text = rd(ini_path, "latin-1")
    sig = re.search(r'^\s*signature\s*=\s*"([^"]+)"', text, re.M).group(1)
    defines, consts, defaults, page_sizes = ini_constants(text, symbols)
    seed = {}
    if seed_path:
        root = ET.parse(seed_path).getroot()
        for c in root.iter():
            if c.tag.endswith("constant") and c.get("name"):
                seed[c.get("name")] = (c.text or "").strip()
    overrides = b.get("base_tune", {}).get("overrides", {})
    stats = {"constants": 0, "from_seed": 0, "from_ini_default": 0, "fallback": 0, "overridden": 0, "fallback_names": []}
    pages, last_off = {}, {}
    for name, (page, kind, rest) in consts.items():
        f = split_fields(rest)
        off = f[1] if len(f) > 1 else ""
        if off == "lastOffset": off = last_off.get(page, "")
        last_off[page] = off
        slot = (off, f[2] if kind == "bits" and len(f) > 2 else "")
        if kind == "string":
            continue
        attrs, val, src = {"name": name}, None, None
        if kind == "bits":
            opts = expand_options(f[3:], defines)
            valid = [o for o in opts if o != '"INVALID"']
            def ok(v): return v in valid
            dflt = None
            if name in defaults:
                d = defaults[name].split()[0]
                if d.startswith('"'): dflt = d if ok(d) else None
                elif d.isdigit() and int(d) < len(opts) and ok(opts[int(d)]): dflt = opts[int(d)]
            cand = [("override", overrides.get(name)), ("seed", seed.get(name)), ("default", dflt), ("fallback", valid[0] if valid else None)]
            for src, v in cand:
                if v is not None and ok(v):
                    val = v; break
            if name in overrides and src != "override":
                raise SystemExit("ERROR: base_tune override %s=%s is not a valid option in the generated ini" % (name, overrides[name]))
        else:
            units = f[2].strip('"') if len(f) > 2 and f[2].startswith('"') else ""
            if kind == "scalar":
                n, lo, hi, digits = 1, num(f[5]) if len(f) > 5 else None, num(f[6]) if len(f) > 6 else None, f[7] if len(f) > 7 else "0"
            else:
                shape = re.findall(r"\d+", f[2]); units = f[3].strip('"') if len(f) > 3 and f[3].startswith('"') else ""
                cols, rows = (int(shape[0]), int(shape[1])) if len(shape) == 2 else (1, int(shape[0]))
                n = cols * rows; attrs.update({"cols": str(cols), "rows": str(rows)})
                lo, hi, digits = (num(f[6]) if len(f) > 6 else None), (num(f[7]) if len(f) > 7 else None), (f[8] if len(f) > 8 else "0")
            attrs["units"] = units
            if re.match(r"^\d+$", str(digits)): attrs["digits"] = digits
            def ok(v):
                xs = [num(x) for x in str(v).split()]
                if len(xs) != n or any(x is None for x in xs): return False
                if lo is not None and hi is not None and any(x < lo - 1e-6 or x > hi + 1e-6 for x in xs): return False
                return True
            dflt = defaults.get(name)
            if dflt is not None and kind == "array" and len(dflt.split()) == 1: dflt = " ".join([dflt] * n)
            base = 0.0
            if lo is not None and hi is not None: base = min(max(0.0, lo), hi)
            fb = " ".join(["%g" % base] * n)
            cand = [("override", overrides.get(name)), ("seed", seed.get(name)), ("default", dflt), ("fallback", fb)]
            for src, v in cand:
                if v is not None and ok(v):
                    val = v; break
            if name in overrides and src != "override":
                raise SystemExit("ERROR: base_tune override %s=%s is out of range/shape" % (name, overrides[name]))
            if kind == "array":
                xs = val.split(); c = int(attrs["cols"])
                val = "\n" + "\n".join("         " + " ".join(xs[i:i + c]) + " " for i in range(0, len(xs), c)) + "\n"
        if val is None:
            stats.setdefault("skipped", []).append(name); continue
        stats["constants"] += 1
        stats[{"override": "overridden", "seed": "from_seed", "default": "from_ini_default", "fallback": "fallback"}[src]] += 1
        if src == "fallback": stats["fallback_names"].append(name)
        pages.setdefault(page, []).append((attrs, val, src, slot))
    # constants sharing a page offset (and bit range) are aliases (e.g. afrTable/lambdaTable): never let a fallback value
    # overwrite an alias that has a real (seed/default/override) value
    for pg, items in pages.items():
        real = {off for _, _, src, off in items if src != "fallback"}
        keep, seen_fb = [], set()
        for it in items:
            dup_fb = it[2] == "fallback" and it[3] in seen_fb
            if it[2] == "fallback": seen_fb.add(it[3])
            if it[2] == "fallback" and (it[3] in real or dup_fb):
                stats["fallback"] -= 1; stats["constants"] -= 1
                stats["fallback_names"].remove(it[0]["name"])
                stats.setdefault("skipped_alias", []).append(it[0]["name"])
                continue
            keep.append(it)
        pages[pg] = keep
    out = ['<?xml version="1.0" encoding="ISO-8859-1"?>', '<msq xmlns="http://www.msefi.com/:msq">',
           '<bibliography author=%s tuneComment=%s writeDate=%s/>' % (quoteattr("OPF build_speeduino.sh"),
               quoteattr("Base tune for %s (board id %d, layout %s), generated from the %s ini; seed values from %s" % (b["name"], b["board_id"], b["ts_layout_name"], sig, os.path.basename(seed_path) if seed_path else "none")),
               quoteattr(write_date)),
           '<versionInfo fileFormat="5.0" firmwareInfo=%s nPages="%d" signature=%s/>' % (quoteattr(fw_info), len(page_sizes), quoteattr(sig))]
    for pg in sorted(pages):
        size = page_sizes[pg - 1] if pg - 1 < len(page_sizes) else 0
        out.append('<page number="%d" size="%d">' % (pg - 1, size))
        for attrs, val, _src, _off in pages[pg]:
            a = " ".join("%s=%s" % (k, quoteattr(v)) for k, v in sorted(attrs.items()))
            out.append("<constant %s>%s</constant>" % (a, escape(val)))
        out.append("</page>")
    out.append("</msq>")
    wr(out_path, "\n".join(out) + "\n", "latin-1")
    # self check
    root = ET.parse(out_path).getroot()
    vi = [e for e in root.iter() if e.tag.endswith("versionInfo")][0]
    assert vi.get("signature") == sig
    pl = [e for e in root.iter() if e.tag.endswith("constant") and e.get("name") == "pinLayout"]
    assert pl and pl[0].text == '"%s"' % b["ts_layout_name"], "pinLayout not set to board layout"
    stats["signature"] = sig
    return stats

def main():
    cmd = sys.argv[1]
    try:
        if cmd == "apply":
            print(apply_board(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5]))
        elif cmd == "ini":
            print(ini_edit(sys.argv[2], sys.argv[3], sys.argv[4]))
        elif cmd == "tune":
            st = gen_tune(sys.argv[2], sys.argv[3] or None, sys.argv[4], sys.argv[5], sys.argv[6], sys.argv[7], set(sys.argv[8].split(",")))
            print(json.dumps(st))
        elif cmd == "board":
            print(json.dumps(load_board(sys.argv[2])))
        else:
            raise SystemExit("unknown command " + cmd)
    except Conflict as e:
        print("\n*** %s\n" % e, file=sys.stderr)
        sys.exit(3)

main()
PY

# ---------------------------------------------------------------------------------------------------------
PRISTINE="$WORK/speeduino-$TAG-pristine"
if [ -d "$PRISTINE/.git" ] && [ "$(git -C "$PRISTINE" config --get opf.tag || true)" = "$TAG" ]; then
  log "reusing pristine Speeduino $TAG checkout (reset + clean)"
  git -C "$PRISTINE" reset -q --hard && git -C "$PRISTINE" clean -qfdx
else
  rm -rf "$PRISTINE"
  log "cloning $UPSTREAM_REPO @ $TAG (shallow)"
  git -c advice.detachedHead=false clone -q --depth 1 --branch "$TAG" "https://github.com/$UPSTREAM_REPO.git" "$PRISTINE"
  git -C "$PRISTINE" config opf.tag "$TAG"
fi
SPEEDUINO_COMMIT=$(git -C "$PRISTINE" rev-parse HEAD)
SPEEDUINO_DATE=$(git -C "$PRISTINE" log -1 --format=%cI)
FW_SIG=$(grep -ohE 'F\("speeduino [0-9]+[^"]*"\)' "$PRISTINE/speeduino/comms_legacy.cpp" | head -1 | sed -E 's/F\("(.*)"\)/\1/')
OPF_COMMIT=$(git -C "$REPO_ROOT" rev-parse HEAD 2>/dev/null || echo unknown)
OPF_DIRTY=$(git -C "$REPO_ROOT" status --porcelain -- build 2>/dev/null | grep -q . && echo true || echo false)

for BOARD in ${BOARDS//,/ }; do
  BDIR="$SCRIPT_DIR/boards/$BOARD/speeduino"
  [ -f "$BDIR/board.json" ] || die "unknown board '$BOARD' (no $BDIR/board.json)"
  log "[$BOARD] preparing source tree"
  TREE="$WORK/build-$BOARD"
  rm -rf "$TREE"
  cp -a "$PRISTINE" "$TREE"
  ENV=$(python3 "$TOOL" apply "$TREE" "$BDIR" "$SCRIPT_DIR/speeduino/common" "$STM32_PLATFORM") || die "[$BOARD] board generation failed (see message above)"
  ( cd "$TREE" && git add -A && git -c user.name=opf-build -c user.email=opf-build@localhost commit -qm "OPF $BOARD generated board support" ) 
  git -C "$TREE" format-patch -1 --stdout HEAD > "$WORK/opf-$BOARD.patch"

  log "[$BOARD] building env $ENV with PlatformIO $PIO_VER ($STM32_PLATFORM)"
  if ! ( cd "$TREE" && pio run -e "$ENV" ) 2>&1 | tee "$WORK/pio-$BOARD.log"; then die "[$BOARD] PlatformIO build failed (log: $WORK/pio-$BOARD.log)"; fi
  BUILD="$TREE/.pio/build/$ENV"
  [ -f "$BUILD/firmware.bin" ] || die "[$BOARD] firmware.bin not produced"

  OUT="$OUT_ROOT/$BOARD"
  rm -rf "$OUT"; mkdir -p "$OUT"
  cp "$BUILD/firmware.bin" "$OUT/speeduino_firmware.bin"
  cp "$BUILD/firmware.elf" "$OUT/speeduino_firmware.elf"
  PIO_PKGS=$(cd "$TREE" && pio pkg list -e "$ENV" 2>/dev/null | grep -E '@ [0-9]' | sed -E 's/^[^A-Za-z]*//; s/ \(required.*//' || true)
  PIO_CORE=${PLATFORMIO_CORE_DIR:-$HOME/.platformio}
  TC_VER=$(printf '%s\n' "$PIO_PKGS" | sed -nE 's/^toolchain-gccarmnoneeabi @ ([0-9.]+).*/\1/p')
  TC_DIR=""
  for d in "$PIO_CORE"/packages/toolchain-gccarmnoneeabi*; do
    v=$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["version"])' "$d/package.json" 2>/dev/null || true)
    [ "$v" = "$TC_VER" ] && TC_DIR=$d
  done
  [ -n "$TC_DIR" ] || die "[$BOARD] toolchain-gccarmnoneeabi $TC_VER not found under $PIO_CORE/packages"
  OBJCOPY="$TC_DIR/bin/arm-none-eabi-objcopy"
  [ -x "$OBJCOPY" ] && "$OBJCOPY" -O ihex "$BUILD/firmware.elf" "$OUT/speeduino_firmware.hex"
  cp "$WORK/opf-$BOARD.patch" "$OUT/opf-$BOARD-speeduino-$TAG.patch"

  INI_SIG=$(python3 "$TOOL" ini "$TREE/reference/speeduino.ini" "$OUT/speeduino_tunerstudio.ini" "$BDIR") || die "[$BOARD] ini generation failed"
  [ -n "$FW_SIG" ] && [ "$INI_SIG" != "$FW_SIG" ] && die "[$BOARD] ini signature '$INI_SIG' != firmware signature '$FW_SIG'"

  SEED=$(python3 -c 'import json,os,sys; b=json.load(open(sys.argv[1]+"/board.json")); s=b.get("base_tune",{}).get("seed"); print(os.path.normpath(os.path.join(sys.argv[1],s)) if s else "")' "$BDIR")
  TUNE_STATS=$(python3 "$TOOL" tune "$OUT/speeduino_tunerstudio.ini" "$SEED" "$BDIR" "$OUT/base-map.msq" \
               "Speeduino+$TAG" "$SPEEDUINO_DATE" "mcu_stm32,CELSIUS") || die "[$BOARD] base tune generation failed"

  # memory usage as reported by PlatformIO's size check
  read -r RAM_USED RAM_MAX < <(sed -nE 's/^RAM:.*used ([0-9]+) bytes from ([0-9]+) bytes.*/\1 \2/p' "$WORK/pio-$BOARD.log" | tail -1)
  read -r ROM_USED ROM_MAX < <(sed -nE 's/^Flash:.*used ([0-9]+) bytes from ([0-9]+) bytes.*/\1 \2/p' "$WORK/pio-$BOARD.log" | tail -1)
  [ -n "${ROM_USED:-}" ] && [ -n "${RAM_USED:-}" ] || die "[$BOARD] could not read memory usage from the PlatformIO log"
  PLATFORM_VER=$(printf '%s\n' "$PIO_PKGS" | sed -nE 's/^Platform ststm32 @ ([0-9.]+).*/\1/p')
  GCC_VER=$("$TC_DIR/bin/arm-none-eabi-gcc" -dumpversion 2>/dev/null || echo unknown)

  ( cd "$OUT" && sha256sum speeduino_firmware.bin speeduino_firmware.elf $( [ -f speeduino_firmware.hex ] && echo speeduino_firmware.hex ) \
      speeduino_tunerstudio.ini base-map.msq "opf-$BOARD-speeduino-$TAG.patch" > SHA256SUMS )

  python3 - "$OUT/build-info.json" <<EOF
import json, sys
tune = json.loads('''$TUNE_STATS''')
rom_used, rom, ram_used, ram = $ROM_USED, $ROM_MAX, $RAM_USED, $RAM_MAX
pkgs = [l for l in """$PIO_PKGS""".splitlines() if l.strip()]
info = {
  "board": "$BOARD", "pio_env": "$ENV", "speeduino_repo": "$UPSTREAM_REPO", "speeduino_tag": "$TAG",
  "speeduino_commit": "$SPEEDUINO_COMMIT", "speeduino_commit_date": "$SPEEDUINO_DATE",
  "firmware_signature": "$FW_SIG", "ini_signature": "$INI_SIG",
  "opf_ecu_commit": "$OPF_COMMIT", "opf_build_dir_dirty": "$OPF_DIRTY" == "true",
  "platformio_version": "$PIO_VER", "platform_spec": "$STM32_PLATFORM", "ststm32_version": "$PLATFORM_VER",
  "pio_packages": pkgs, "arm_gcc_version": "$GCC_VER",
  "flash_used_bytes": rom_used, "flash_total_bytes": rom, "flash_used_pct": round(100.0*rom_used/rom, 1),
  "ram_used_bytes": ram_used, "ram_total_bytes": ram, "ram_used_pct": round(100.0*ram_used/ram, 1),
  "firmware_bin_note": "speeduino_firmware.bin carries the 16-byte DFU suffix added by PlatformIO (upload_protocol = dfu), as upstream's black_F407VE build does",
  "base_tune": tune,
  "sha256": dict(reversed(l.split()) for l in open("$OUT/SHA256SUMS").read().splitlines()),
}
json.dump(info, open(sys.argv[1], "w"), indent=2)
print(json.dumps({k: info[k] for k in ("board","speeduino_tag","flash_used_bytes","flash_total_bytes","flash_used_pct","ram_used_bytes","ram_total_bytes","ram_used_pct")}))
EOF
  ( cd "$OUT" && sha256sum -c --quiet SHA256SUMS ) || die "[$BOARD] checksum verification failed"
  log "[$BOARD] artifacts in $OUT"
  ls -l "$OUT"
done
