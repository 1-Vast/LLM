"""Inspect ZIP filenames/header metadata without decoding non-S2 entries."""
import json
from pathlib import Path
import struct

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/az_chemical_identity'
raw = (OUT / 's2_attempt_04.body').read_bytes()
headers = []
position = 0
while True:
    position = raw.find(b'PK\x03\x04', position)
    if position < 0 or position + 30 > len(raw):
        break
    offset = position
    _, _, flags, method, _, _, crc, compressed, uncompressed, nlen, elen = struct.unpack_from('<4s5H3I2H', raw, offset)
    position += 4
    if not 0 < nlen < 512:
        continue
    name = raw[offset + 30:offset + 30 + nlen]
    if any(c < 32 or c > 126 for c in name):
        continue
    headers.append({'offset': offset, 'name': name.decode(), 'flags': flags,
                    'method': method, 'compressed_size': compressed,
                    'uncompressed_size': uncompressed})
result = {'body_is_partial': True, 'other_entries_decoded': False,
          'zip_local_header_metadata': headers,
          'exact_s2_name_in_retained_prefix': b'EMS194010-supplement-Table_S2.xlsx' in raw}
(OUT / 'ZIP_PREFIX_METADATA.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result))
