#!/usr/bin/env python3
"""Adapt an ECU_Build core48/core8 board_configuration.cpp to the current rusEFI board API.

Idempotent; only rewrites the old-API patterns it finds:
  * global setBoardConfigOverrides()/setBoardDefaultConfiguration() -> static functions
    registered via setup_custom_board_overrides() (hw_layer/board_overrides.h)
  * strncpy(config->luaScript, R"(...)", efi::size(config->luaScript)) -> setLuaScript(R"(...)")
  * adds the includes those need
"""
import re
import sys


def fix(src: str) -> str:
    if "setup_custom_board_overrides" in src:
        return src
    out = src
    hooks = []
    if re.search(r"^void\s+setBoardConfigOverrides\s*\(\s*(void)?\s*\)", out, re.M):
        out = re.sub(r"^void\s+setBoardConfigOverrides\s*\(\s*(void)?\s*\)",
                     "static void opf_boardConfigOverrides()", out, flags=re.M)
        hooks.append("\tcustom_board_ConfigOverrides = opf_boardConfigOverrides;")
    if re.search(r"^void\s+setBoardDefaultConfiguration\s*\(\s*(void)?\s*\)", out, re.M):
        out = re.sub(r"^void\s+setBoardDefaultConfiguration\s*\(\s*(void)?\s*\)",
                     "static void opf_boardDefaultConfiguration()", out, flags=re.M)
        hooks.append("\tcustom_board_DefaultConfiguration = opf_boardDefaultConfiguration;")
    out = re.sub(r"strncpy\(\s*config->luaScript\s*,\s*R\"\(", 'setLuaScript(R"(', out)
    out = re.sub(r"\)\"\s*,\s*efi::size\(\s*config->luaScript\s*\)\s*\)", ')")', out)
    includes = '#include "settings.h"\n#include "board_overrides.h"\n'
    if '#include "pch.h"' in out:
        out = out.replace('#include "pch.h"\n', '#include "pch.h"\n' + includes, 1)
    else:
        out = includes + out
    if hooks:
        out = out.rstrip() + "\n\n// added by OPF_ECU scripts/rusefi/rusefi_board_fixups.py\n" \
              "void setup_custom_board_overrides() {\n" + "\n".join(hooks) + "\n}\n"
    return out


def main() -> int:
    for path in sys.argv[1:]:
        with open(path, encoding="utf-8") as f:
            src = f.read()
        new = fix(src)
        if new != src:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new)
            print(f"fixed {path}")
        else:
            print(f"unchanged {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
