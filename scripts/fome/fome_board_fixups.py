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
c.write_text(s)

# rusEFI-only helper file
env = board / 'board.env'
if env.exists():
    env.unlink(); applied.append('removed rusEFI-only board.env')

print('fixups applied:' if applied else 'fixups: none needed')
for a in applied:
    print('  -', a)
