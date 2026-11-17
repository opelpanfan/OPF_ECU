#!/usr/bin/env python3
"""Convert a raw TunerStudio page image (bytes read from the ECU/simulator) into a .msq tune,
using the [Constants] definitions of the matching FOME TunerStudio ini.

usage: ini2msq.py <ini> <page.bin> <out.msq> [--comment TEXT] [--setting LAMBDA ...]
       ini2msq.py --verify <ini> <page.bin> <out.msq>   # re-encode msq -> bytes and compare

Only nPages=1 inis (FOME/rusEFI) are supported. '#if X' blocks take the '#else' branch unless X
is passed with --setting (TunerStudio's default when the setting group option is off).
"""
import re, struct, sys, argparse, datetime, os


def _stamp():
    # honour SOURCE_DATE_EPOCH so the .msq is byte-reproducible
    sde = os.environ.get('SOURCE_DATE_EPOCH')
    if sde:
        return datetime.datetime.fromtimestamp(int(sde), datetime.timezone.utc)
    return datetime.datetime.now(datetime.timezone.utc)
from xml.sax.saxutils import escape

TYPES = {'U08': 'B', 'S08': 'b', 'U16': 'H', 'S16': 'h', 'U32': 'I', 'S32': 'i', 'F32': 'f', 'F64': 'd'}

def split_csv(s):
    out, cur, q = [], '', False
    for ch in s:
        if ch == '"': q = not q; cur += ch
        elif ch == ',' and not q: out.append(cur.strip()); cur = ''
        else: cur += ch
    if cur.strip(): out.append(cur.strip())
    return out

def num(s):
    s = s.strip()
    try: return float(s)
    except ValueError: return None

def parse_ini(path, settings):
    lines = open(path, encoding='latin-1').read().splitlines()
    sect = None; consts = []; stack = []; sig = None; page_size = None; in_page = False; defines = {}
    def expand(items):
        out = []
        for o in items:
            if o.startswith('$') and o[1:] in defines: out += expand(defines[o[1:]])
            else: out.append(o)
        return out
    for raw in lines:
        line = raw.split(';', 1)[0].rstrip() if not raw.lstrip().startswith(';') else ''
        st = line.strip()
        if not st: continue
        if st.startswith('#if'):
            sym = st.split()[1]; stack.append(sym in settings); continue
        if st.startswith('#else'): stack[-1] = not stack[-1]; continue
        if st.startswith('#endif'): stack.pop(); continue
        if not all(stack): continue
        if st.startswith('['): sect = st; continue
        m = re.match(r'#define\s+(\w+)\s*=\s*(.*)$', st)
        if m: defines[m.group(1)] = split_csv(m.group(2)); continue
        if sect == '[MegaTune]' and sig is None and st.startswith('signature'):
            sig = st.split('=', 1)[1].strip().strip('"')
        if sect == '[TunerStudio]' and sig is None and st.startswith('signature'):
            sig = st.split('=', 1)[1].strip().strip('"')
        if sect != '[Constants]' or '=' not in st: continue
        name, val = [x.strip() for x in st.split('=', 1)]
        if name == 'pageSize': page_size = int(split_csv(val)[0]); continue
        if name == 'page': in_page = True; continue
        f = split_csv(val)
        if not in_page or not f or f[0] not in ('scalar', 'array', 'bits', 'string'): continue
        kind, typ, off = f[0], f[1], int(f[2])
        c = {'name': name, 'kind': kind, 'type': typ, 'off': off}
        if kind == 'scalar':
            c.update(units=f[3].strip('"'), scale=num(f[4]) or 1.0, trans=num(f[5]) or 0.0,
                     digits=int(num(f[8]) or 0) if len(f) > 8 else 0)
        elif kind == 'array':
            shape = [int(x) for x in re.findall(r'\d+', f[3])]
            cols, rows = (shape[0], shape[1]) if len(shape) == 2 else (1, shape[0])
            c.update(cols=cols, rows=rows, units=f[4].strip('"'), scale=num(f[5]) or 1.0,
                     trans=num(f[6]) or 0.0, digits=int(num(f[9]) or 0) if len(f) > 9 else 0)
        elif kind == 'bits':
            lo, hi = [int(x) for x in re.findall(r'\d+', f[3])[:2]]
            opts = {}
            idx = 0
            for o in expand(f[4:]):
                m = re.match(r'^(\d+)\s*=\s*"(.*)"$', o)
                if m: opts[int(m.group(1))] = m.group(2)
                elif o.startswith('"'): opts[idx] = o.strip('"'); idx += 1
            c.update(lo=lo, hi=hi, opts=opts)
        elif kind == 'string':
            c.update(length=int(f[3]))
        consts.append(c)
    return sig, page_size, consts

def fmt(v):
    if v == int(v) and abs(v) < 1e15: return '%.1f' % v
    return repr(float(v))

def decode(c, data):
    t = c['type']
    if c['kind'] == 'string':
        return data[c['off']:c['off'] + c['length']].split(b'\0', 1)[0].decode('latin-1')
    code = TYPES[t]; sz = struct.calcsize(code)
    if c['kind'] == 'bits':
        raw = struct.unpack_from('<' + code.upper() if code in 'bhi' else '<' + code, data, c['off'])[0]
        v = (raw >> c['lo']) & ((1 << (c['hi'] - c['lo'] + 1)) - 1)
        return c['opts'].get(v, str(v))
    n = 1 if c['kind'] == 'scalar' else c['rows'] * c['cols']
    raws = struct.unpack_from('<%d%s' % (n, code), data, c['off'])
    vals = [(r + c['trans']) * c['scale'] for r in raws]
    if t == 'F32':
        def short(v):
            for n in range(6, 10):
                x = float('%.*g' % (n, v))
                if struct.pack('<f', x) == struct.pack('<f', v): return x
            return v
        vals = [short(v) for v in vals]
    return vals

def to_msq(sig, page_size, consts, data, comment):
    out = ['<?xml version="1.0" encoding="ISO-8859-1"?>',
           '<msq xmlns="http://www.msefi.com/:msq">',
           '<bibliography author="OPF FOME autobuild (ini2msq.py)" tuneComment="%s" writeDate="%s"/>'
           % (escape(comment, {'"': '&quot;'}), _stamp().strftime('%a %b %d %H:%M:%S UTC %Y')),
           '<versionInfo fileFormat="5.0" firmwareInfo="" nPages="1" signature="%s"/>' % escape(sig),
           '<page>']
    for c in consts:
        v = decode(c, data); nm = escape(c['name'])
        if c['kind'] in ('bits', 'string'):
            out.append('<constant name="%s">"%s"</constant>' % (nm, escape(v)))
        elif c['kind'] == 'scalar':
            out.append('<constant digits="%d" name="%s" units="%s">%s</constant>'
                       % (c['digits'], nm, escape(c['units'], {'"': '&quot;'}), fmt(v[0])))
        else:
            rows = ['         ' + ' '.join(fmt(x) for x in v[r * c['cols']:(r + 1) * c['cols']]) + ' '
                    for r in range(c['rows'])]
            out.append('<constant cols="%d" digits="%d" name="%s" rows="%d" units="%s">\n%s\n      </constant>'
                       % (c['cols'], c['digits'], nm, c['rows'], escape(c['units'], {'"': '&quot;'}), '\n'.join(rows)))
    out += ['</page>', '</msq>', '']
    return '\n'.join(out)

def encode_back(consts, msq_text, page_size):
    """Re-encode msq values into a page image (bytes not covered by any constant stay 0)."""
    vals = {}
    for m in re.finditer(r'<constant[^>]*name="([^"]+)"[^>]*>(.*?)</constant>', msq_text, re.S):
        vals[m.group(1)] = m.group(2).strip()
    buf = bytearray(page_size); covered = bytearray(page_size)
    for c in consts:
        s = vals[c['name']]; off = c['off']
        if c['kind'] == 'string':
            b = s.strip('"').encode('latin-1')[:c['length']]
            buf[off:off + c['length']] = b.ljust(c['length'], b'\0'); covered[off:off + c['length']] = b'\1' * c['length']; continue
        code = TYPES[c['type']]; sz = struct.calcsize(code)
        if c['kind'] == 'bits':
            label = s.strip('"'); labels = list(c['opts'].values())
            if labels.count(label) > 1: continue   # ambiguous label (e.g. "INVALID"): not verifiable
            inv = {v: k for k, v in c['opts'].items()}
            v = inv[label] if label in inv else int(label)
            mask = ((1 << (c['hi'] - c['lo'] + 1)) - 1) << c['lo']
            ucode = code.upper()
            cur = struct.unpack_from('<' + ucode, buf, off)[0]
            struct.pack_into('<' + ucode, buf, off, (cur & ~mask) | ((v << c['lo']) & mask))
            cm = struct.unpack_from('<' + ucode, covered, off)[0] | mask
            struct.pack_into('<' + ucode, covered, off, cm); continue
        nums = [float(x) for x in s.split()]
        for i, x in enumerate(nums):
            r = x / c['scale'] - c['trans']
            if c['type'] in ('F32', 'F64'): struct.pack_into('<' + code, buf, off + i * sz, r)
            else: struct.pack_into('<' + code, buf, off + i * sz, int(round(r)))
            covered[off + i * sz: off + (i + 1) * sz] = b'\xff' * sz
    return bytes(buf), bytes(covered)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--verify', action='store_true')
    ap.add_argument('ini'); ap.add_argument('page'); ap.add_argument('msq')
    ap.add_argument('--comment', default='Base tune (FOME defaults)')
    ap.add_argument('--setting', action='append', default=[])
    a = ap.parse_args()
    sig, page_size, consts = parse_ini(a.ini, set(a.setting))
    data = open(a.page, 'rb').read()
    if len(data) != page_size: sys.exit('page image is %d bytes, ini pageSize is %d' % (len(data), page_size))
    if not a.verify:
        open(a.msq, 'w', encoding='latin-1').write(to_msq(sig, page_size, consts, data, a.comment))
        print('wrote %s: %d constants, signature "%s"' % (a.msq, len(consts), sig)); return
    buf, cov = encode_back(consts, open(a.msq, encoding='latin-1').read(), page_size)
    bad = [i for i in range(page_size) if cov[i] and (buf[i] & cov[i]) != (data[i] & cov[i])]
    pct = 100.0 * sum(1 for x in cov if x) / page_size
    if bad:
        names = sorted({c['name'] for c in consts for i in bad[:50] if c['off'] <= i < c['off'] + 64})[:10]
        sys.exit('VERIFY FAILED: %d byte(s) differ, first at offset %d (near %s)' % (len(bad), bad[0], names))
    print('verify OK: msq re-encodes to identical bytes for all defined fields (%.1f%% of page covered)' % pct)

if __name__ == '__main__':
    main()
