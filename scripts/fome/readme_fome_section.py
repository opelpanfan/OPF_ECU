#!/usr/bin/env python3
"""Maintain the FOME section of a board branch's readme.md, between <!-- FOME:START --> / <!-- FOME:END -->.

  readme_fome_section.py update <readme.md> <fome_dir> <owner/repo> <branch>
      rewrite only the marked section (badge links to fome/fome_firmware.bin, fome_tunerstudio.ini, fome_console.zip). The first time, the legacy
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
    """Same content/style as the original hand-written block: badge links to the firmware .bin and the ini,
    plus the console (upstream FOME still ships fome_console in its release bundles) when it was built."""
    raw = 'https://raw.githubusercontent.com/%s/%s/fome/' % (repo, branch)
    have = set(os.listdir(fome_dir))
    out = [START, '\n## FOME (RUSEFI fork) Firmware\n', "(Right click and 'Save link as...')\n"]
    for name, label, color, title in (('fome_firmware.bin', 'FOME%20Firmware', 'blue', 'FOME Firmware'),
                                      ('fome_tunerstudio.ini', 'FOME%20TunerStudio%20INI', 'green', 'FOME TunerStudio INI'),
                                      ('fome_console.zip', 'FOME%20Console', 'purple', 'FOME Console')):
        if name in have:
            out.append('\n' + BADGE.format(label=label, color=color, title=title, url=raw + name))
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
