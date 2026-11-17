#!/usr/bin/env python3
"""List unique STM32F407 OPF hardware boards under config/.

Used by the rusEFI, FOME and Speeduino autobuild workflows so a new
config/<board> folder is picked up with no workflow edit.

opf33_fome is the FOME overlay for the opf33 board, not a second board.
Teensy folders (none expected) are skipped because this branch is F407 only.
Every other config/<board> is emitted. Missing firmware support is a porting
bug, not a default skip.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config"


def iter_config_dirs():
    if not CONFIG.is_dir():
        raise SystemExit(f"no config directory at {CONFIG}")
    for d in sorted(p for p in CONFIG.iterdir() if p.is_dir() and not p.name.startswith(".")):
        yield d


def classify(name: str) -> tuple[str, str] | None:
    """Return (status, reason) where status is 'board' or 'skip'."""
    lname = name.lower()
    if "teensy" in lname:
        return "skip", "Teensy is not built on this branch (STM32F407 only)"
    if name == "opf33_fome":
        return "skip", "FOME overlay for the opf33 board, not a separate hardware board"
    return "board", ""


def list_boards() -> tuple[list[str], list[tuple[str, str]]]:
    boards, skipped = [], []
    for d in iter_config_dirs():
        status, reason = classify(d.name)
        if status == "skip":
            skipped.append((d.name, reason))
        else:
            boards.append(d.name)
    return boards, skipped


def fome_overlay(board: str) -> str:
    """Directory CI should overlay into FOME for this board."""
    if board == "opf33":
        return "config/opf33_fome"
    return f"config/{board}"


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--json", action="store_true", help="print {boards,skipped,fome_overlay}")
    p.add_argument("--fome-overlay", metavar="BOARD", help="print the FOME overlay path for one board")
    args = p.parse_args()
    if args.fome_overlay:
        print(fome_overlay(args.fome_overlay))
        return 0
    boards, skipped = list_boards()
    if args.json:
        print(json.dumps({
            "boards": boards,
            "skipped": [{"name": n, "reason": r} for n, r in skipped],
            "fome_overlay": {b: fome_overlay(b) for b in boards},
        }))
        return 0
    for n, r in skipped:
        print(f"SKIP {n}: {r}", file=sys.stderr)
    for b in boards:
        print(b)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
