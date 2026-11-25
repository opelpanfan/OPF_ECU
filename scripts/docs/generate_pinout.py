#!/usr/bin/env python3
"""Generate interactive pinout pages and a README firmware section from connector YAMLs.

Only data already in the repo is used: config/<board>/connectors/*.yaml,
board_configuration.cpp GPIO assignments, and scripts/speeduino/board-overlay/<board>/board.json.
A cell with no matching assignment is marked unknown. Nothing is inferred from the pin name alone
beyond normalising an explicit id/pin_name such as D6 or PG3 to the P-prefixed form used by the
firmware maps (D6 -> PD6).

Usage: python3 scripts/docs/generate_pinout.py
"""
from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    sys.exit("PyYAML is required")

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"
DOCS = ROOT / "docs"
OVERLAY = ROOT / "scripts" / "speeduino" / "board-overlay"

# Pinned refs. Release tags follow the autobuild workflows.
RUSEFI = "34b1633bc25fa948efe66dd93bdde1e173357fc9"
FOME = "477f9e471aaf5e29180a70dbc7230d259199b40a"
SPEEDUINO_RELEASE = "202501.7"
SPEEDUINO_MASTER = "b59336df1fa80c29f6a08cd5376604744a275bce"
SPEEDUINO_MASTER_SHORT = SPEEDUINO_MASTER[:10]

START = "<!-- PINOUT:START -->"
END = "<!-- PINOUT:END -->"
PORT = re.compile(r"^P?([A-K])(\d{1,2})$", re.I)
GPIO_ASSIGN = re.compile(
    r"engineConfiguration->([A-Za-z0-9_\[\].]+)\s*=\s*Gpio::([A-Z]\d+)\s*;"
)
PAREN_PIN = re.compile(r"\(([A-K]\d{1,2})\)")


def norm_pin(token: str | None) -> str | None:
    if not token:
        return None
    m = PORT.fullmatch(token.strip())
    if not m:
        return None
    return "P%s%d" % (m.group(1).upper(), int(m.group(2)))


def boards() -> list[str]:
    names = []
    for p in sorted(CONFIG.iterdir()):
        if not p.is_dir() or p.name.startswith(".") or p.name == "opf33_fome":
            continue
        if (p / "connectors").is_dir() or (p / "board.mk").is_file():
            names.append(p.name)
    return names


def load_yaml_pins(board: str) -> list[dict]:
    conn = CONFIG / board / "connectors"
    rows = []
    if not conn.is_dir():
        return rows
    for path in sorted(conn.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        pins = data.get("pins") or []
        for index, pin in enumerate(pins, start=1):
            if not isinstance(pin, dict):
                rows.append({
                    "connector": path.stem,
                    "index": index,
                    "raw": {"value": str(pin)},
                    "mcu": [],
                    "note": "YAML entry is not a mapping",
                })
                continue
            raw = {}
            for k, v in pin.items():
                if isinstance(v, (str, int, float)):
                    raw[str(k)] = str(v)
                else:
                    raw[str(k)] = json.dumps(v, ensure_ascii=False)
            mcu = []
            for key in ("pin_name", "id"):
                n = norm_pin(raw.get(key))
                if n and n not in mcu:
                    mcu.append(n)
            ts = raw.get("ts_name") or ""
            for m in PAREN_PIN.finditer(ts):
                n = norm_pin(m.group(1))
                if n and n not in mcu:
                    mcu.append(n)
            rows.append({
                "connector": path.stem,
                "index": index,
                "raw": raw,
                "mcu": mcu,
            })
    return rows


def gpio_map(path: Path) -> dict[str, list[str]]:
    found: dict[str, list[str]] = {}
    if not path.is_file():
        return found
    text = path.read_text(encoding="utf-8", errors="replace")
    for field, pin in GPIO_ASSIGN.findall(text):
        n = norm_pin(pin)
        if not n:
            continue
        found.setdefault(n, [])
        if field not in found[n]:
            found[n].append(field)
    return found


def speeduino_map(board: str) -> tuple[dict[str, list[str]], dict]:
    path = OVERLAY / board / "board.json"
    meta = {}
    found: dict[str, list[str]] = {}
    if not path.is_file():
        return found, meta
    data = json.loads(path.read_text(encoding="utf-8"))
    meta = {
        "description": data.get("description") or "",
        "mcu_guard": data.get("mcu_guard") or "",
        "board_id": data.get("board_id"),
    }
    for func, pin in (data.get("pins") or {}).items():
        n = norm_pin(str(pin))
        if not n:
            continue
        found.setdefault(n, [])
        label = "%s=%s" % (func, pin)
        if label not in found[n]:
            found[n].append(label)
    return found, meta


def lookup(mcu: list[str], mapping: dict[str, list[str]]) -> str:
    if not mcu:
        return "unknown (no MCU pin in the connector YAML)"
    hits = []
    for pin in mcu:
        for item in mapping.get(pin, []):
            text = "%s: %s" % (pin, item)
            if text not in hits:
                hits.append(text)
    if not hits:
        return "unknown (not assigned in the firmware pin map)"
    return "; ".join(hits)


def firmware_sources(board: str) -> dict[str, Path]:
    rus = CONFIG / board / "board_configuration.cpp"
    if board == "opf33" and (CONFIG / "opf33_fome" / "board_configuration.cpp").is_file():
        fome = CONFIG / "opf33_fome" / "board_configuration.cpp"
    else:
        fome = rus
    return {"rusEFI": rus, "FOME": fome}


def section_md(board: str, connectors: list[str], meta: dict, pin_count: int) -> str:
    title = meta.get("description") or board
    mcu = meta.get("mcu_guard") or "unknown (not recorded in board.json or board.h)"
    conn = ", ".join("`%s`" % c for c in connectors) if connectors else "none in config/%s/connectors/" % board
    rusefi_tag = "rusefi-%s-%s" % (RUSEFI, board)
    fome_tag = "fome-%s-%s" % (FOME, board)
    spd_tag = "speeduino-%s-%s" % (SPEEDUINO_RELEASE, board)
    spd_master = "speeduino-master-%s-%s" % (SPEEDUINO_MASTER_SHORT, board)
    fome_note = ""
    if board == "opf33":
        fome_note = " FOME is built from `config/opf33_fome/` (same hardware, FOME overlay)."
    lines = [
        START,
        "## Pinout and firmware",
        "",
        "Generated by `scripts/docs/generate_pinout.py` from this board's connector YAMLs and the firmware pin maps in the repo. Fields that are not in those files are marked unknown.",
        "",
        "| | |",
        "| --- | --- |",
        "| Board | `%s` |" % board,
        "| Description | %s |" % title,
        "| MCU | `%s` |" % mcu,
        "| Connectors | %s |" % conn,
        "| Connector pins | %d |" % pin_count,
        "",
        "Interactive pinout: [docs/%s.html](../../docs/%s.html)." % (board, board),
        "",
        "Firmware variants built for this hardware (release asset name is `<tag>.bin` / `<tag>.ini` / `<tag>-base.msq`; this readme is copied into the release as `<tag>-manual.md`):",
        "",
        "| Firmware | Pinned ref | Release |",
        "| --- | --- | --- |",
        "| rusEFI | `%s` | [%s](../../../releases/tag/%s) |" % (RUSEFI, rusefi_tag, rusefi_tag),
        "| FOME | `%s` | [%s](../../../releases/tag/%s) |" % (FOME, fome_tag, fome_tag),
        "| Speeduino %s | `%s` | [%s](../../../releases/tag/%s) |" % (SPEEDUINO_RELEASE, SPEEDUINO_RELEASE, spd_tag, spd_tag),
        "| Speeduino master | `%s` | [%s](../../../releases/tag/%s) |" % (SPEEDUINO_MASTER, spd_master, spd_master),
        "",
        fome_note.strip(),
        END,
        "",
    ]
    return "\n".join(line for line in lines if line is not None)


def upsert_readme(board: str, section: str) -> str:
    path = CONFIG / board / "readme.md"
    if path.is_file():
        text = path.read_text(encoding="utf-8")
        block = section.strip() + "\n"
        if START in text and END in text:
            text = re.sub(re.escape(START) + r".*?" + re.escape(END), block.strip(), text, count=1, flags=re.S)
            if not text.endswith("\n"):
                text += "\n"
            path.write_text(text, encoding="utf-8")
            return "updated section"
        # Keep the existing manual. Place the generated block after the first heading.
        lines = text.splitlines(keepends=True)
        insert_at = 0
        for i, line in enumerate(lines):
            if line.startswith("# "):
                insert_at = i + 1
                break
        addition = "\n" + block + "\n"
        lines.insert(insert_at, addition)
        path.write_text("".join(lines), encoding="utf-8")
        return "inserted section"
    body = "# %s\n\n%s\n" % (board, section.strip())
    path.write_text(body, encoding="utf-8")
    return "created"


def render_html(board: str, rows: list[dict], meta: dict, sources: dict[str, str]) -> str:
    title = meta.get("description") or board
    mcu = meta.get("mcu_guard") or "unknown"
    payload = []
    for row in rows:
        raw = row["raw"]
        payload.append({
            "connector": row["connector"],
            "index": row["index"],
            "id": raw.get("id") or raw.get("pin") or "",
            "function": raw.get("function") or "",
            "type": raw.get("type") or "",
            "class": raw.get("class") or "",
            "ts_name": raw.get("ts_name") or "",
            "color": raw.get("color") or "",
            "mcu": row["mcu"],
            "rusefi": row["rusefi"],
            "fome": row["fome"],
            "speeduino": row["speeduino"],
            "extra": {k: v for k, v in raw.items() if k not in ("id", "pin", "function", "type", "class", "ts_name", "color")},
        })
    data = json.dumps({"board": board, "pins": payload}, ensure_ascii=False)
    source_lines = "".join("<li><code>%s</code>: <code>%s</code></li>" % (html.escape(k), html.escape(v)) for k, v in sources.items())
    return """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s pinout</title>
<style>
  :root { color-scheme: light dark; }
  body { font-family: Arial, Helvetica, sans-serif; margin: 1rem; line-height: 1.4; }
  h1 { font-size: 1.4rem; margin-bottom: 0.2rem; }
  .meta, .note { max-width: 70rem; }
  .toolbar { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.8rem 0; }
  input[type="search"] { min-width: 16rem; padding: 0.4rem 0.5rem; }
  button.filter { padding: 0.3rem 0.6rem; cursor: pointer; }
  button.filter.active { outline: 2px solid currentColor; }
  table { border-collapse: collapse; width: 100%%; max-width: 80rem; }
  th, td { border: 1px solid #888; padding: 0.35rem 0.45rem; text-align: left; vertical-align: top; }
  th { position: sticky; top: 0; background: #222; color: #fff; }
  tr.pin { cursor: pointer; }
  tr.pin:hover { background: rgba(80,140,220,0.15); }
  tr.detail { display: none; background: rgba(80,140,220,0.08); }
  tr.detail.open { display: table-row; }
  td.unknown { opacity: 0.75; }
  code { font-size: 0.92em; }
</style>
</head>
<body>
<p><a href="index.html">All boards</a> · <a href="../config/%(board)s/readme.md">config/%(board)s/readme.md</a></p>
<h1>%(title)s</h1>
<p class="meta">MCU: <code>%(mcu)s</code>. Interactive pinout generated from <code>config/%(board)s/connectors/*.yaml</code>. Firmware columns are filled only when that MCU pin is assigned in the repo's pin map.</p>
<p class="note">Sources:</p>
<ul>%(sources)s</ul>
<div class="toolbar">
  <input id="q" type="search" placeholder="Search pin, function, MCU, firmware" aria-label="Filter pins">
  <span id="filters"></span>
  <span id="count"></span>
</div>
<table>
  <thead>
    <tr>
      <th>Connector</th><th>Pin</th><th>Id</th><th>Function</th><th>Type</th><th>Class</th>
      <th>TunerStudio name</th><th>rusEFI</th><th>FOME</th><th>Speeduino</th>
    </tr>
  </thead>
  <tbody id="rows"></tbody>
</table>
<script id="pin-data" type="application/json">%(data)s</script>
<script>
const data = JSON.parse(document.getElementById("pin-data").textContent);
const tbody = document.getElementById("rows");
const q = document.getElementById("q");
const filters = document.getElementById("filters");
const count = document.getElementById("count");
const classes = Array.from(new Set(data.pins.map(p => p.class).filter(Boolean))).sort();
let active = "all";
function esc(s) {
  return String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&":"&amp;","<":"&lt;",">":"&gt;","\\"":"&quot;","'":"&#39;" }[c]));
}
function cell(text) {
  const unknown = !text || String(text).indexOf("unknown") === 0;
  return '<td class="' + (unknown ? "unknown" : "") + '">' + esc(text || "unknown") + "</td>";
}
function matches(p) {
  if (active !== "all" && p.class !== active) return false;
  const needle = q.value.trim().toLowerCase();
  if (!needle) return true;
  const blob = [p.connector, p.index, p.id, p.function, p.type, p.class, p.ts_name, p.color, (p.mcu || []).join(" "), p.rusefi, p.fome, p.speeduino, JSON.stringify(p.extra)].join(" ").toLowerCase();
  return blob.indexOf(needle) !== -1;
}
function render() {
  const pins = data.pins.filter(matches);
  tbody.innerHTML = pins.map((p, i) => {
    const id = "d" + i;
    const main = "<tr class=\\"pin\\" data-detail=\\"" + id + "\\">" +
      "<td>" + esc(p.connector) + "</td>" +
      "<td>" + esc(p.index) + "</td>" +
      cell(p.id) + cell(p.function) + cell(p.type) + cell(p.class) + cell(p.ts_name) +
      cell(p.rusefi) + cell(p.fome) + cell(p.speeduino) + "</tr>";
    const extra = Object.keys(p.extra).map(k => "<div><code>" + esc(k) + "</code>: " + esc(p.extra[k]) + "</div>").join("");
    const detail = "<tr class=\\"detail\\" id=\\"" + id + "\\"><td colspan=\\"10\\">" +
      "<div>MCU pin from YAML: <code>" + esc((p.mcu || []).join(", ") || "unknown") + "</code></div>" +
      "<div>Color: " + esc(p.color || "unknown") + "</div>" +
      extra +
      "<div>Click the row again to hide this detail.</div></td></tr>";
    return main + detail;
  }).join("");
  count.textContent = pins.length + " / " + data.pins.length + " pins";
  tbody.querySelectorAll("tr.pin").forEach(tr => {
    tr.addEventListener("click", () => {
      const row = document.getElementById(tr.dataset.detail);
      row.classList.toggle("open");
    });
  });
}
function setFilter(name, button) {
  active = name;
  filters.querySelectorAll("button").forEach(b => b.classList.toggle("active", b === button));
  render();
}
const allBtn = document.createElement("button");
allBtn.type = "button"; allBtn.className = "filter active"; allBtn.textContent = "all";
allBtn.addEventListener("click", () => setFilter("all", allBtn));
filters.appendChild(allBtn);
classes.forEach(name => {
  const b = document.createElement("button");
  b.type = "button"; b.className = "filter"; b.textContent = name;
  b.addEventListener("click", () => setFilter(name, b));
  filters.appendChild(b);
});
q.addEventListener("input", render);
render();
</script>
</body>
</html>
""" % {
        "title": html.escape(title),
        "board": html.escape(board),
        "mcu": html.escape(mcu),
        "sources": source_lines,
        "data": data.replace("</", "<\\/"),
    }


def render_index(entries: list[tuple[str, str]]) -> str:
    rows = []
    for board, desc in entries:
        rows.append(
            "<tr><td><code>%s</code></td><td>%s</td>"
            "<td><a href='%s.html'>pinout</a></td>"
            "<td><a href='../config/%s/readme.md'>readme</a></td></tr>"
            % (html.escape(board), html.escape(desc), html.escape(board), html.escape(board))
        )
    return """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>OPF ECU pinout and firmware</title>
<style>body{font-family:sans-serif;max-width:60rem;margin:2rem auto;padding:0 1rem}
table{border-collapse:collapse;width:100%%}td,th{border:1px solid #888;padding:.4rem .6rem;text-align:left}</style>
</head><body>
<h1>OPF ECU boards</h1>
<p>Pinout pages are generated from <code>config/&lt;board&gt;/connectors/*.yaml</code> by <code>scripts/docs/generate_pinout.py</code>. Firmware release tags are linked from each board readme. GitHub Pages serves this file only after it is on <code>main</code>.</p>
<table><thead><tr><th>Board</th><th>Description</th><th>Pinout</th><th>README</th></tr></thead>
<tbody>
%s
</tbody></table>
</body></html>
""" % "\n".join(rows)


def main() -> int:
    DOCS.mkdir(exist_ok=True)
    index_rows = []
    for board in boards():
        rows = load_yaml_pins(board)
        spd, meta = speeduino_map(board)
        sources = firmware_sources(board)
        maps = {
            "rusEFI": gpio_map(sources["rusEFI"]),
            "FOME": gpio_map(sources["FOME"]),
            "Speeduino": spd,
        }
        if not meta.get("mcu_guard"):
            header = CONFIG / board / "board.h"
            if header.is_file():
                m = re.search(r"#define\s+BOARD_NAME\s+\"([^\"]+)\"", header.read_text(encoding="utf-8", errors="replace"))
                if m:
                    meta["mcu_guard"] = "BOARD_NAME %s (MCU not named in board.h)" % m.group(1)
        for row in rows:
            row["rusefi"] = lookup(row["mcu"], maps["rusEFI"])
            row["fome"] = lookup(row["mcu"], maps["FOME"])
            row["speeduino"] = lookup(row["mcu"], maps["Speeduino"])
        rel_sources = {}
        for label, path in sources.items():
            rel_sources[label] = str(path.relative_to(ROOT)) if path.is_file() else "%s missing" % path.relative_to(ROOT)
        spd_path = OVERLAY / board / "board.json"
        rel_sources["Speeduino"] = str(spd_path.relative_to(ROOT)) if spd_path.is_file() else "no board.json"
        html_text = render_html(board, rows, meta, rel_sources)
        (DOCS / ("%s.html" % board)).write_text(html_text, encoding="utf-8")
        connectors = sorted({r["connector"] for r in rows})
        action = upsert_readme(board, section_md(board, connectors, meta, len(rows)))
        index_rows.append((board, meta.get("description") or board))
        print("%s: %d connector pins, readme %s" % (board, len(rows), action))
    (DOCS / "index.html").write_text(render_index(index_rows), encoding="utf-8")
    print("wrote docs/index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
