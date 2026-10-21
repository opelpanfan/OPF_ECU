#!/usr/bin/env python3
"""Read the TunerStudio signature + configuration page from a FOME ECU or the FOME simulator,
using the msEnvelope_1.0 binary protocol, and save the raw page image.

usage: ts_read_page.py <tcp:HOST:PORT | /dev/ttyACM0> <pageSize> <out.bin> [--expect-signature SIG]
"""
import argparse, socket, struct, sys, time, zlib

class Link:
    def __init__(self, target, timeout=5.0):
        if target.startswith('tcp:'):
            _, host, port = target.split(':')
            for i in range(60):
                try:
                    self.s = socket.create_connection((host, int(port)), timeout=timeout); break
                except OSError:
                    time.sleep(0.5)
            else:
                sys.exit('cannot connect to %s' % target)
            self.read = self._sock_read; self.write = self.s.sendall
        else:
            import serial
            self.p = serial.Serial(target, 115200, timeout=timeout); time.sleep(0.2); self.p.reset_input_buffer()
            self.read = self.p.read; self.write = self.p.write

    def _sock_read(self, n):
        b = b''
        while len(b) < n:
            c = self.s.recv(n - len(b))
            if not c: break
            b += c
        return b

    def cmd(self, payload):
        self.write(struct.pack('>H', len(payload)) + payload + struct.pack('>I', zlib.crc32(payload)))
        hdr = self.read(2)
        if len(hdr) < 2: raise IOError('timeout waiting for response')
        n = struct.unpack('>H', hdr)[0]; body = self.read(n); crc = self.read(4)
        if len(crc) < 4 or struct.unpack('>I', crc)[0] != zlib.crc32(body): raise IOError('bad CRC in response')
        return body

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('target'); ap.add_argument('size', type=int); ap.add_argument('out')
    ap.add_argument('--expect-signature'); ap.add_argument('--chunk', type=int, default=1024)
    a = ap.parse_args()
    l = Link(a.target)
    sig = l.cmd(b'S')[1:].rstrip(b'\0').decode('latin-1')
    print('signature:', sig)
    if a.expect_signature and sig != a.expect_signature:
        sys.exit('signature mismatch: ECU "%s" != ini "%s"' % (sig, a.expect_signature))
    data = b''
    while len(data) < a.size:
        c = min(a.chunk, a.size - len(data))
        r = l.cmd(b'R' + struct.pack('<HH', len(data), c))
        if r[0] != 0 or len(r) - 1 != c: raise IOError('read failed at %d (status %d, %d bytes)' % (len(data), r[0], len(r) - 1))
        data += r[1:]
    r = l.cmd(b'k' + struct.pack('<HH', 0, a.size))
    ecu = struct.unpack('>I', r[1:5])[0]; loc = zlib.crc32(data)
    if ecu != loc: sys.exit('CRC mismatch: ecu %08x local %08x' % (ecu, loc))
    open(a.out, 'wb').write(data)
    print('page: %d bytes, crc32 %08x (matches ECU)' % (len(data), loc))

if __name__ == '__main__':
    main()
