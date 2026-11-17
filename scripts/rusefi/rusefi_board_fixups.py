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


LED_FUNCS = {
    "communicationLedPin": "getCommsLedPin",
    "runningLedPin": "getRunningLedPin",
    "warningLedPin": "getWarningLedPin",
}

def convert_leds(src: str) -> str:
    """Current rusEFI/FOME expose status LEDs via get*LedPin(), not engineConfiguration fields."""
    out = src
    funcs = []
    for field, fn in LED_FUNCS.items():
        m = re.search(r"engineConfiguration->%s\s*=\s*(Gpio::\w+)\s*;" % field, out)
        if not m:
            continue
        pin = m.group(1)
        out = re.sub(r"\s*engineConfiguration->%s\s*=\s*Gpio::\w+\s*;" % field, "", out)
        if re.search(r"\bGpio\s+%s\s*\(" % fn, out) is None:
            funcs.append("Gpio %s() {\n\treturn %s;\n}\n" % (fn, pin))
    if funcs:
        out = out.rstrip() + "\n\n// LED pins: engineConfiguration fields removed upstream\n" + "\n".join(funcs)
    return out

def fix_vbatt(src: str) -> str:
    """Host gcc in the simulator is built without -fsingle-precision-constant."""
    return src.replace(
        "engineConfiguration->vbattDividerCoeff = (6.34 + 1) / 1",
        "engineConfiguration->vbattDividerCoeff = 7.34f",
    )

def flatten_legacy_fields(src: str) -> str:
    """engineConfiguration->specs and a few old names were flattened/renamed upstream."""
    out = re.sub(
        r"engineConfiguration->specs\.(cylindersCount|firingOrder|displacement)\b",
        r"engineConfiguration->\1",
        src,
    )
    out = re.sub(r"\s*engineConfiguration->vehicleWeight\s*=[^;]*;", "", out)
    out = re.sub(
        r"setAlgorithm\(\s*LM_SPEED_DENSITY\s*\)",
        "setAlgorithm(engine_load_mode_e::LM_SPEED_DENSITY)",
        out,
    )
    # 4G63 board used the old TT_MITSUBISHI alias; current rusEFI/FOME call it TT_MITSU_4G63_CAM.
    out = re.sub(r"\b(?:trigger_type_e::)?TT_MITSUBISHI\b", "trigger_type_e::TT_MITSU_4G63_CAM", out)
    return out

def fix(src: str) -> str:
    out = flatten_legacy_fields(fix_vbatt(convert_leds(src)))
    if "setup_custom_board_overrides" in out:
        return out
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
