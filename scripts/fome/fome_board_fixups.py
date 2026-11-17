#!/usr/bin/env python3
"""Adapt an ECU_Build-style board config (copied into FOME's config/boards/<board>/) to the
FOME source tree being built. Each fixup only applies when the target FOME no longer has the
feature, so the same board files build against both older and newer FOME releases.

usage: fome_board_fixups.py <fome_firmware_dir> <board_dir>
"""
import re, sys, pathlib

fw = pathlib.Path(sys.argv[1]); board = pathlib.Path(sys.argv[2])
cfg_txt = (fw / 'integration' / 'fome_config.txt').read_text(errors='ignore')
applied = []

def field_exists(name):
    return re.search(r'\b%s\b' % re.escape(name), cfg_txt) is not None

def fome_has_rusefi_hooks():
    return (fw / 'hw_layer' / 'board_overrides.h').exists()

def convert_lua_to_fome(s):
    """Current FOME still stores the default script in config->luaScript (no setLuaScript())."""
    if 'setLuaScript' not in s:
        return s
    s2, n = re.subn(
        r'setLuaScript\s*\(\s*(R"\([\s\S]*?\)")\s*\)',
        r'strncpy(config->luaScript, \1, efi::size(config->luaScript))',
        s,
    )
    return s2 if n else s


def flatten_legacy_fields(src):
    out = re.sub(
        r'engineConfiguration->specs\.(cylindersCount|firingOrder|displacement)\b',
        r'engineConfiguration->\1',
        src,
    )
    out = re.sub(
        r'setAlgorithm\(\s*LM_SPEED_DENSITY\s*\)',
        'setAlgorithm(engine_load_mode_e::LM_SPEED_DENSITY)',
        out,
    )
    out = re.sub(r'\bTT_MITSUBISHI\b', 'TT_MITSU_4G63_CAM', out)
    return out

def convert_rusefi_hooks_to_fome(s):
    """Inverse of rusefi_board_fixups.py when this FOME still uses weak setBoard* hooks."""
    s = s.replace('#include "board_overrides.h"\n', '')
    s = convert_lua_to_fome(s)
    m = re.search(r'void\s+setup_custom_board_overrides\s*\(\s*\)\s*\{([\s\S]*?)\n\}', s)
    if not m:
        return s
    body = m.group(1)
    md = re.search(r'custom_board_DefaultConfiguration\s*=\s*(\w+)', body)
    mo = re.search(r'custom_board_ConfigOverrides\s*=\s*(\w+)', body)
    if md:
        s = re.sub(
            r'(?:static\s+)?void\s+' + md.group(1) + r'\s*\(\s*\)',
            'void setBoardDefaultConfiguration()',
            s, count=1)
    if mo:
        s = re.sub(
            r'(?:static\s+)?void\s+' + mo.group(1) + r'\s*\(\s*\)',
            'void setBoardConfigOverrides()',
            s, count=1)
    s = re.sub(
        r'\n?(?://[^\n]*setup_custom_board_overrides[^\n]*\n)?void\s+setup_custom_board_overrides\s*\(\s*\)\s*\{[\s\S]*?\n\}\n?',
        '\n', s, count=1)
    return s

# FOME #730 (2026-02): all UART / bluetooth / serial-console code removed.
if not field_exists('binarySerialTxPin'):
    h = board / 'board.h'
    s = h.read_text()
    for m in ['STM32_SERIAL_USE_USART1', 'STM32_UART_USE_USART1', 'TS_PRIMARY_UxART_PORT', 'SERIAL_SPEED',
              'EFI_CONSOLE_TX_BRAIN_PIN', 'EFI_CONSOLE_RX_BRAIN_PIN', 'EFI_BLUETOOTH_SETUP_DEBUG',
              'EFI_BLUETOOTH_SETUP']:
        s = re.sub(r'#undef %s\n#define %s[^\n]*\n\n?' % (m, m), '', s)
    h.write_text(s)
    applied.append('board.h: dropped UART/bluetooth defines (removed upstream, FOME #730)')

c = board / 'board_configuration.cpp'
s = c.read_text()
for f in ['binarySerialTxPin', 'binarySerialRxPin', 'tunerStudioSerialSpeed', 'uartConsoleSerialSpeed']:
    if not field_exists(f):
        s2 = re.sub(r'\s*engineConfiguration->%s\s*=[^;]*;' % f, '', s)
        if s2 != s:
            applied.append('board_configuration.cpp: removed engineConfiguration->%s (field gone upstream)' % f)
        s = s2

# Status LEDs: current FOME uses get*LedPin() (same as rusEFI), not engineConfiguration fields.
LED_FUNCS = {
    'communicationLedPin': 'getCommsLedPin',
    'runningLedPin': 'getRunningLedPin',
    'warningLedPin': 'getWarningLedPin',
}
funcs = []
for field, fn in LED_FUNCS.items():
    if field_exists(field):
        continue
    m = re.search(r'engineConfiguration->%s\s*=\s*(Gpio::\w+)\s*;' % field, s)
    if not m:
        continue
    pin = m.group(1)
    s = re.sub(r'\s*engineConfiguration->%s\s*=\s*Gpio::\w+\s*;' % field, '', s)
    if re.search(r'\bGpio\s+%s\s*\(' % fn, s) is None:
        funcs.append('Gpio %s() {\n\treturn %s;\n}\n' % (fn, pin))
    applied.append('board_configuration.cpp: %s -> %s()' % (field, fn))
if funcs:
    s = s.rstrip() + '\n\n// LED pins: engineConfiguration fields removed upstream\n' + '\n'.join(funcs)
if not fome_has_rusefi_hooks():
    s2 = convert_rusefi_hooks_to_fome(s)
    if s2 != s:
        applied.append('board_configuration.cpp: rusEFI setup_custom_board_overrides/setLuaScript -> FOME setBoard* hooks')
        s = s2
s2 = flatten_legacy_fields(s)
if s2 != s:
    applied.append('board_configuration.cpp: flattened specs/TT_MITSUBISHI/setAlgorithm for current FOME')
    s = s2
c.write_text(s)

# FOME's Makefile requires SHORT_BOARD_NAME as a make variable. Older ECU_Build
# board.mk files only set it as -DSHORT_BOARD_NAME=... in DDEFS.
mkp = board / 'board.mk'
if mkp.exists():
    mk = mkp.read_text()
    if re.search(r'^SHORT_BOARD_NAME\s*[:?]?=', mk, re.M) is None:
        m = re.search(r'-DSHORT_BOARD_NAME=([A-Za-z0-9_]+)', mk)
        if m:
            mk = 'SHORT_BOARD_NAME = %s\n' % m.group(1) + mk
            mkp.write_text(mk)
            applied.append('board.mk: set SHORT_BOARD_NAME=%s (was only in DDEFS)' % m.group(1))

# rusEFI-only helper file
env = board / 'board.env'
if env.exists():
    env.unlink(); applied.append('removed rusEFI-only board.env')

print('fixups applied:' if applied else 'fixups: none needed')
for a in applied:
    print('  -', a)
