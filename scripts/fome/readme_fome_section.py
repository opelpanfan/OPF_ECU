#!/usr/bin/env python3
"""Maintain the FOME section of a board branch's readme.md, between <!-- FOME:START --> / <!-- FOME:END -->.

  readme_fome_section.py update <readme.md> <fome_dir> <owner/repo> <branch>
      rewrite only the marked section (links to the files present in fome/). The first time, the legacy
      unmarked "## FOME ..." block (up to the next "## " heading) is replaced by the marked section.
  readme_fome_section.py check <old_readme> <new_readme>
      exit 1 unless the two files are identical outside the FOME section.
Line endings of the existing file (CRLF on core48_21) are preserved.
"""
import os, re, sys

START, END = '<!-- FOME:START -->', '<!-- FOME:END -->'
LEGACY = re.compile(r'^## FOME\b.*$', re.M)
BADGE = ('<!-- BEGIN LATEST DOWNLOAD BUTTON -->\n[![Download zip](https://custom-icon-badges.demolab.com/badge/'
         '-{label}-{color}?style=for-the-badge&logo=download&logoColor=white "Download {title}")]({url})\n'
         '<!-- END LATEST DOWNLOAD BUTTON -->\n')
FILES = [  # name, description
    ('fome_firmware.bin', 'OpenBLT bootloader + FOME, flash at 0x08000000 via DFU (STM32CubeProgrammer / dfu-util)'),
    ('fome_firmware.srec', 'FOME only, update through the OpenBLT bootloader'),
    ('fome_firmware.hex', 'Intel HEX image'),
    ('fome_firmware.dfu', 'DFU image'),
    ('fome_tunerstudio.ini', 'TunerStudio project ini (must match the firmware signature)'),
    ('fome_base_tune.msq', 'base tune: FOME defaults for this board, open in TunerStudio as a starting point'),
    ('fome_console.zip', 'FOME console (java; upstream FOME releases still ship it in their bundles)'),
    ('SHA256SUMS', 'checksums of the files above'),
    ('fome_build_info.txt', 'FOME version/commit, TunerStudio signature, toolchain'),
]


def split(text):
    """-> (before, section_incl_markers, after) or None"""
    i, j = text.find(START), text.find(END)
    if i >= 0 and j > i:
        j += len(END)
        return text[:i], text[i:j], text[j:]
    m = LEGACY.search(text)
    if m:
        n = re.compile(r'^## ', re.M).search(text, m.end())
        k = n.start() if n else len(text)
        return text[:m.start()], text[m.start():k], text[k:]
    return None


def section(fome_dir, repo, branch):
    raw = 'https://raw.githubusercontent.com/%s/%s/fome/' % (repo, branch)
    info = {}
    p = os.path.join(fome_dir, 'fome_build_info.txt')
    if os.path.exists(p):
        for line in open(p):
            if '=' in line:
                k, v = line.rstrip('\n').split('=', 1); info[k] = v
    have = set(os.listdir(fome_dir))
    out = [START, '\n## FOME (RUSEFI fork) Firmware\n', "(Right click and 'Save link as...')\n\n"]
    for name, label, color, title in (('fome_firmware.bin', 'FOME%20Firmware', 'blue', 'FOME Firmware'),
                                      ('fome_tunerstudio.ini', 'FOME%20TunerStudio%20INI', 'green', 'FOME TunerStudio INI'),
                                      ('fome_base_tune.msq', 'FOME%20Base%20Tune', 'orange', 'FOME Base Tune'),
                                      ('fome_console.zip', 'FOME%20Console', 'purple', 'FOME Console')):
        if name in have:
            out.append(BADGE.format(label=label, color=color, title=title, url=raw + name) + '\n')
    if info:
        c = info.get('fome_commit', '')
        out.append('Built automatically from FOME `%s` ([`%s`](https://github.com/FOME-Tech/fome-fw/commit/%s)), '
                   'TunerStudio signature `%s`.\n\n' % (info.get('fome_ref', '?'), c[:10], c, info.get('signature', '?')))
    out.append('| File | |\n|---|---|\n')
    for name, desc in FILES:
        if name in have:
            out.append('| [%s](%s%s) | %s |\n' % (name, raw, name, desc))
    if 'fome_console.zip' not in have:
        out.append('\nNo FOME console in this build.\n')
    out.append('\nThe settings reset to defaults when coming from rusEFI or another FOME config layout - back up your tune first.\n')
    out.append(END)
    return ''.join(out)


def read(p):
    b = open(p, 'rb').read().decode('utf-8')
    return b.replace('\r\n', '\n'), '\r\n' in b


def main():
    if sys.argv[1] == 'update':
        readme, fome_dir, repo, branch = sys.argv[2:6]
        text, crlf = read(readme)
        new = section(fome_dir, repo, branch)
        parts = split(text)
        if parts:
            before, _, after = parts
            if not after.startswith('\n'):
                after = '\n\n' + after.lstrip('\n') if after.strip() else '\n'
            text = before + new + after
        else:
            m = re.compile(r'^## Firmware.*\n', re.M).search(text)
            text = (text[:m.end()] + '\n' + new + '\n' + text[m.end():]) if m else (text.rstrip('\n') + '\n\n' + new + '\n')
        if crlf:
            text = text.replace('\n', '\r\n')
        open(readme, 'wb').write(text.encode('utf-8'))
    elif sys.argv[1] == 'check':
        a, _ = read(sys.argv[2]); b, _ = read(sys.argv[3])
        pa, pb = split(a), split(b)
        strip = lambda p, t: (p[0].rstrip('\n'), p[2].lstrip('\n')) if p else (t, '')
        if strip(pa, a) != strip(pb, b):
            print('readme.md changed outside the FOME section', file=sys.stderr); sys.exit(1)
    else:
        sys.exit(__doc__)


if __name__ == '__main__':
    main()
