#!/usr/bin/env python3
"""Maintain the rusEFI section of a board branch's top-level readme.md.

The section is the board branch's original hand-written "RUSEFI Firmware" block (download badges for
rusefi/rusefi_firmware.bin, rusefi/rusefi_tunerstudio.ini and rusefi/rusefi_console.zip, same badge
style as commit 5c21224), wrapped in <!-- RUSEFI:START --> / <!-- RUSEFI:END -->.

* markers present  -> only the text between them is rewritten
* markers missing, original block present verbatim -> the block is wrapped in the markers in place
* otherwise        -> the block is appended at the end
Text outside the markers (board description, FOME/SPEEDUINO sections) is never altered; CRLF kept.

  readme_section.py update README [BRANCH]   # BRANCH used in the raw download URLs (default core48_21)
  readme_section.py check OLD NEW            # exit 1 unless NEW == OLD apart from the RUSEFI section
"""
import sys

START = "<!-- RUSEFI:START -->"
END = "<!-- RUSEFI:END -->"
BADGE = ("[![Download zip](https://custom-icon-badges.demolab.com/badge/-{label}-{color}?style=for-the-badge"
         "&logo=download&logoColor=white \"Download {title}\")]"
         "(https://raw.githubusercontent.com/opelpanfan/OPF_ECU/{branch}/rusefi/{file})")
BUTTONS = [  # exactly the original three buttons
    ("RusEFI%20Firmware", "blue", "RusEFI Firmware", "rusefi_firmware.bin"),
    ("RusEFI%20TunerStudio%20INI", "green", "RusEFI TunerStudio INI", "rusefi_tunerstudio.ini"),
    ("RusEFI%20Console", "purple", "RusEFI Console", "rusefi_console.zip"),
]


def body(branch, nl):
    lines = ["## RUSEFI Firmware", "(Right click and 'Save link as...')"]
    for label, color, title, f in BUTTONS:
        lines += ["", "<!-- BEGIN LATEST DOWNLOAD BUTTON -->",
                  BADGE.format(label=label, color=color, title=title, branch=branch, file=f),
                  "<!-- END LATEST DOWNLOAD BUTTON -->"]
    return nl.join(lines)


def read(path):
    try:
        with open(path, encoding="utf-8", newline="") as f:
            return f.read()
    except FileNotFoundError:
        return ""


def split(text):
    s = text.find(START)
    e = text.find(END, s + 1) if s >= 0 else -1
    if s < 0 or e < 0:
        return None
    return text[:s], text[s + len(START):e], text[e + len(END):]


def update(readme, branch="core48_21"):
    old = read(readme)
    nl = "\r\n" if "\r\n" in old else "\n"
    b = body(branch, nl)
    block = START + nl + b + nl + END
    parts = split(old)
    if parts is not None:
        new = parts[0] + block + parts[2]
    elif b in old:                      # adopt the original hand-written block in place
        i = old.index(b)
        new = old[:i] + block + old[i + len(b):]
    else:
        sep = "" if old == "" else (nl if old.endswith("\n") else nl + nl)
        new = old + sep + block + nl
    with open(readme, "w", encoding="utf-8", newline="") as f:
        f.write(new)


def check(old_file, new_file):
    old, new = read(old_file), read(new_file)
    p = split(new)
    if p is None:
        sys.exit("readme.md: RUSEFI markers missing after update")
    before, inner, after = p
    po = split(old)
    if po is not None:
        ok = (po[0], po[2]) == (before, after)
    else:
        nl = "\r\n" if "\r\n" in new else "\n"
        inner_body = inner[len(nl):-len(nl)] if inner.startswith(nl) and inner.endswith(nl) else inner
        adopted = old == before + inner_body + after
        appended = after.strip() == "" and before.startswith(old) and before[len(old):].strip() == ""
        ok = adopted or appended
    if not ok:
        sys.exit("readme.md: text outside <!-- RUSEFI:START/END --> changed")
    print("readme.md: changes confined to the RUSEFI section")


if __name__ == "__main__":
    if len(sys.argv) in (3, 4) and sys.argv[1] == "update":
        update(*sys.argv[2:])
    elif len(sys.argv) == 4 and sys.argv[1] == "check":
        check(*sys.argv[2:])
    else:
        sys.exit(__doc__)
