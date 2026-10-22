"""Recover only independently CRC-verified complete members in a bounded ZIP prefix."""
import hashlib
import json
import struct
import zlib
from pathlib import Path

root = Path(__file__).resolve().parents[2] / 'log/20261022/biological_decision_scout/sources'
data = (root / 'mse_europepmc_supplements.body').read_bytes()
outdir = root / 'complete_members'
outdir.mkdir(exist_ok=True)
pos = 0
manifest = []
while pos + 30 <= len(data) and data[pos:pos + 4] == b'PK\x03\x04':
    _, version, flags, method, tm, dt, crc, compressed, size, nlen, xlen = struct.unpack_from('<IHHHHHIIIHH', data, pos)
    name = data[pos + 30:pos + 30 + nlen].decode('utf-8')
    start = pos + 30 + nlen + xlen
    if method != 8 or not flags & 8:
        raise ValueError('Unexpected ZIP encoding; do not guess')
    inflater = zlib.decompressobj(-15)
    body = inflater.decompress(data[start:])
    if not inflater.eof:
        manifest.append({'name': name, 'complete': False, 'retained': False})
        break
    end = len(data) - len(inflater.unused_data)
    if data[end:end + 4] != b'PK\x07\x08':
        raise ValueError('Missing explicit data descriptor')
    expected_crc, compressed, size = struct.unpack_from('<III', data, end + 4)
    if size != len(body) or compressed != end - start or expected_crc != zlib.crc32(body):
        raise ValueError('ZIP member integrity failure')
    wanted = name.endswith('.xlsx') or name.endswith('MOESM3_ESM.pdf')
    manifest.append({'name': name, 'complete': True, 'retained': wanted, 'size': len(body),
                     'compressed_size': compressed, 'crc32': expected_crc,
                     'sha256': hashlib.sha256(body).hexdigest(), 'offset': pos})
    if wanted:
        p = outdir / Path(name).name
        if p.exists():
            raise FileExistsError(p)
        p.write_bytes(body)
    pos = end + 16
(root / 'mse_prefix_member_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
print(json.dumps(manifest, indent=2))
