#!/usr/bin/env python3
"""Apply a committed list of TunerStudio setting overrides (board pinout, trigger, engine basics) to a FOME
configuration page image, or to a live ECU over the TunerStudio protocol.

Overrides file: one `name = value` per line ('#' comments). `name` is a [Constants] field of the FOME ini;
`value` is the exact enum label for bits fields (e.g. `Low Side 12 (G3)`) or a number (TunerStudio units)
for scalars. Every name/label is validated against the ini; a pin used by two fields is an error.
A leading `?` (`?cylindersCount = 4`) makes a field optional: skipped when this FOME ini has no such field.

usage:
  apply_tune_overrides.py <ini> <overrides.txt> --page IN.bin --out OUT.bin     # offline (build: base tune)
  apply_tune_overrides.py <ini> <overrides.txt> --ecu /dev/ttyACM0 [--backup DIR] [--dry-run]
      live ECU: read page (CRC-checked), apply, write only changed bytes, burn, reconnect, re-read and
      verify every override field + CRC. Close TunerStudio first (it holds the serial port).
"""
import argparse, os, re, struct, sys, time, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ini2msq as m

PIN_LABEL = re.compile(r'(^P[A-I]\d{1,2}$)|\(([A-I]\d{1,2})( [A-Z]+)?\)$')

def load_overrides(path):
    out = []
    for n, raw in enumerate(open(path, encoding='utf-8'), 1):
        line = raw.split('#', 1)[0].strip()
        if not line: continue
        if '=' not in line: sys.exit('%s:%d: expected name = value' % (path, n))
        k, v = [x.strip() for x in line.split('=', 1)]
        out.append((k, v, n))
    return out

def encode(c, value, where):
    """-> list of (offset, mask_bytes, value_bytes) or raise"""
    code = m.TYPES[c['type']]; sz = struct.calcsize(code)
    if c['kind'] == 'bits':
        labels = list(c['opts'].values())
        if value not in labels: raise ValueError('%s: "%s" is not an option of %s' % (where, value, c['name']))
        if labels.count(value) > 1: raise ValueError('%s: label "%s" is ambiguous in %s' % (where, value, c['name']))
        raw = {v: k for k, v in c['opts'].items()}[value]
        return ('bits', raw)
    if c['kind'] == 'scalar':
        x = float(value); r = x / c['scale'] - c['trans']
        return ('scalar', r if c['type'] in ('F32', 'F64') else int(round(r)))
    raise ValueError('%s: %s (%s) is not supported in overrides' % (where, c['name'], c['kind']))

def apply(consts_by_name, page, overrides):
    buf = bytearray(page); changes = []
    for name, value, n in overrides:
        optional = name.startswith('?'); name = name.lstrip('?')
        c = consts_by_name.get(name)
        if c is None and optional:
            print('  %-28s not in this ini, skipped (optional)' % name); continue
        if c is None: raise ValueError('line %d: unknown ini field %s' % (n, name))
        kind, raw = encode(c, value, 'line %d' % n)
        old = m.decode(c, bytes(buf))
        code = m.TYPES[c['type']]
        if kind == 'bits':
            u = '<' + code.upper(); mask = ((1 << (c['hi'] - c['lo'] + 1)) - 1) << c['lo']
            cur = struct.unpack_from(u, buf, c['off'])[0]
            struct.pack_into(u, buf, c['off'], (cur & ~mask) | ((raw << c['lo']) & mask))
        else:
            struct.pack_into('<' + code, buf, c['off'], raw)
        new = m.decode(c, bytes(buf))
        changes.append((name, old, new))
    return bytes(buf), changes

def pin_fields(consts):
    for c in consts:
        if c['kind'] != 'bits' or c['type'] != 'U16': continue
        if sum(1 for v in c['opts'].values() if PIN_LABEL.search(v)) >= 4: yield c

def adc_fields(consts):
    for c in consts:
        if c['kind'] == 'bits' and c['type'] == 'U08' and any(v.startswith('Analog Inputs') for v in c['opts'].values()):
            yield c

def _raw(c, page):
    code = '<' + m.TYPES[c['type']].upper()
    return (struct.unpack_from(code, page, c['off'])[0] >> c['lo']) & ((1 << (c['hi'] - c['lo'] + 1)) - 1)

def _mcu_pin(label):
    mm = PIN_LABEL.search(label)
    return None if not mm else ('P' + mm.group(2) if mm.group(2) else mm.group(1))

def pin_conflicts(consts, page, names):
    """MCU pins used by more than one field (digital pin fields and ADC channels), where at least one
    of the fields is in `names`"""
    users = {}
    for c in list(pin_fields(consts)) + list(adc_fields(consts)):
        raw = _raw(c, page)
        if not raw: continue
        label = c['opts'].get(raw, str(raw)); pin = _mcu_pin(label) or '%s#%d' % (c['type'], raw)
        users.setdefault(pin, []).append(c['name'])
    return {p: u for p, u in users.items() if len(u) > 1 and any(x in names for x in u)}

def fmt(v): return v if isinstance(v, str) else ' '.join('%g' % x for x in v)

def check(consts, page, overrides, changes):
    names = {k.lstrip('?') for k, _, _ in overrides}
    bad = pin_conflicts(consts, page, names)
    for raw, u in bad.items(): print('PIN CONFLICT: %s used by %s' % (raw, ', '.join(u)), file=sys.stderr)
    if bad: sys.exit('refusing: duplicate pin assignment')
    for name, old, new in changes:
        print('  %-28s %s -> %s' % (name, fmt(old), fmt(new)) if old != new else '  %-28s %s (unchanged)' % (name, fmt(new)))

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('ini'); ap.add_argument('overrides')
    ap.add_argument('--page'); ap.add_argument('--out')
    ap.add_argument('--ecu'); ap.add_argument('--backup'); ap.add_argument('--dry-run', action='store_true')
    ap.add_argument('--chunk', type=int, default=256)
    a = ap.parse_args()
    sig, page_size, consts = m.parse_ini(a.ini, set())
    by = {c['name']: c for c in consts}
    ov = load_overrides(a.overrides)
    if a.page:
        page = open(a.page, 'rb').read()
        if len(page) != page_size: sys.exit('page is %d bytes, ini pageSize %d' % (len(page), page_size))
        new, ch = apply(by, page, ov); check(consts, new, ov, ch)
        open(a.out or a.page, 'wb').write(new)
        print('overrides: %d fields, page crc32 %08x -> %08x' % (len(ov), zlib.crc32(page), zlib.crc32(new))); return
    if not a.ecu: ap.error('--page or --ecu required')
    from ts_read_page import Link
    def read_all(link):
        s = link.cmd(b'S')[1:].rstrip(b'\0').decode('latin-1')
        if s != sig: sys.exit('signature mismatch: ECU "%s" != ini "%s"' % (s, sig))
        d = b''
        while len(d) < page_size:
            n = min(1024, page_size - len(d)); r = link.cmd(b'R' + struct.pack('<HH', len(d), n))
            if r[0] != 0 or len(r) - 1 != n: raise IOError('read failed at %d' % len(d))
            d += r[1:]
        e = struct.unpack('>I', link.cmd(b'k' + struct.pack('<HH', 0, page_size))[1:5])[0]
        if e != zlib.crc32(d): sys.exit('read CRC mismatch ecu %08x local %08x' % (e, zlib.crc32(d)))
        return d
    link = Link(a.ecu); cur = read_all(link)
    print('ECU signature ok, page crc32 %08x' % zlib.crc32(cur))
    if a.backup:
        os.makedirs(a.backup, exist_ok=True)
        open(os.path.join(a.backup, 'before.bin'), 'wb').write(cur)
        open(os.path.join(a.backup, 'before.msq'), 'w', encoding='latin-1').write(m.to_msq(sig, page_size, consts, cur, 'pre-change backup %s' % a.ecu))
    new, ch = apply(by, cur, ov); check(consts, new, ov, ch)
    diff = [i for i in range(page_size) if cur[i] != new[i]]
    print('%d byte(s) differ, target crc32 %08x' % (len(diff), zlib.crc32(new)))
    if a.dry_run or not diff:
        print('dry run, nothing written' if a.dry_run else 'ECU already matches'); return
    i = 0  # write contiguous changed runs, in chunks
    while i < len(diff):
        s = diff[i]; e = s
        while i + 1 < len(diff) and diff[i + 1] - e <= 8 and diff[i + 1] - s < a.chunk: i += 1; e = diff[i]
        r = link.cmd(b'C' + struct.pack('<HH', s, e - s + 1) + new[s:e + 1])
        if r[:1] != b'\0': sys.exit('write failed at %d: %s' % (s, r.hex()))
        i += 1
    e = struct.unpack('>I', link.cmd(b'k' + struct.pack('<HH', 0, page_size))[1:5])[0]
    if e != zlib.crc32(new): sys.exit('ECU RAM crc %08x != target %08x after write (not burned)' % (e, zlib.crc32(new)))
    r = link.cmd(b'B')
    if r[:1] not in (b'\0', b'\x04'): sys.exit('burn failed: %s' % r.hex())
    print('burned'); time.sleep(1.0)
    del link; time.sleep(0.5)
    back = read_all(Link(a.ecu))
    bad = [n for n, _, _ in ch if m.decode(by[n], back) != m.decode(by[n], new)]
    if bad or back != new: sys.exit('VERIFY FAILED after reconnect: %s, crc %08x' % (bad, zlib.crc32(back)))
    if a.backup:
        open(os.path.join(a.backup, 'after.bin'), 'wb').write(back)
    print('verified after reconnect: all %d override fields read back, page crc32 %08x' % (len(ch), zlib.crc32(back)))

if __name__ == '__main__':
    main()
