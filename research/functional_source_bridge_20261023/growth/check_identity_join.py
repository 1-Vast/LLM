"""Independent identifier audit; no author or root processing code imported."""
import csv
import hashlib
import io
import json
from pathlib import Path
import struct
import zipfile
import zlib

root = Path('log/20261023/functional_source_bridge/root')
out = root.parent / 'growth'
manifest = json.loads((root / 'figshare_data_manifest.body').read_text())
metadata_info = next(f for f in manifest['files'] if f['name'] == 'metadata.zip')
metadata = (root / 'metadata.zip.body').read_bytes()
assert hashlib.md5(metadata).hexdigest() == metadata_info['computed_md5']
assert len(metadata) == metadata_info['size']
with zipfile.ZipFile(io.BytesIO(metadata)) as archive:
    metadata_rows = list(csv.DictReader(io.StringIO(
        archive.read('metadata/cell_line_metadata.csv').decode())))
design = {r['cell_line'] for r in metadata_rows}
assert len(metadata_rows) == len(design) == 16


def local_payload(raw):
    fields = struct.unpack_from('<IHHHHHIIIHH', raw)
    assert fields[0] == 0x04034B50 and fields[3] == 8
    offset = 30 + fields[-2] + fields[-1]
    name = raw[30:30 + fields[-2]].decode()
    stream = zlib.decompressobj(-15)
    return name, stream.decompress(raw[offset:]), stream.eof


name, prefix, eof = local_payload((root / 'pseudobulk_prefix.body').read_bytes())
assert name == 'processed/pseudobulk_sum_by_ko.csv' and not eof
# Decompression physically materializes some subsequent bytes, but only the
# first two newline-terminated CSV header records are decoded or interpreted.
headers = prefix.split(b'\n', 2)[:2]
header_rows = [next(csv.reader([h.decode().rstrip('\r')])) for h in headers]
assert len(header_rows[0]) == len(header_rows[1])
state = list(zip(header_rows[0][1:], header_rows[1][1:]))

function = (root / 'crispr_table.csv').read_bytes()
function_ids = []
function_header = function.split(b'\n', 1)[0].decode().rstrip('\r')
assert function_header.startswith('cell_line,guide,')
for row in function.splitlines()[1:]:
    # The first two fields are simple author-produced unquoted identifiers.
    pair = row.split(b',', 2)[:2]
    assert len(pair) == 2 and all(b'"' not in part for part in pair)
    function_ids.append(tuple(part.decode() for part in pair))

central = (root / 'processed.zip.directory.body').read_bytes()
position = 0
crc_match = None
while True:
    position = central.find(b'PK\x01\x02', position)
    if position < 0:
        break
    fields = struct.unpack_from('<I6H3I5H2I', central, position)
    name_length, extra_length, comment_length = fields[10:13]
    filename = central[position + 46:position + 46 + name_length].decode()
    if filename == 'processed/crispr_table.csv':
        crc_match = {'crc32': fields[7], 'uncompressed_size': fields[9]}
    position += 46 + name_length + extra_length + comment_length
assert crc_match is not None
assert crc_match['crc32'] == zlib.crc32(function)
assert crc_match['uncompressed_size'] == len(function)
function_name, function_unpacked, function_eof = local_payload(
    (root / 'crispr_table.body').read_bytes())
assert function_name == 'processed/crispr_table.csv'
assert function_eof and function_unpacked == function

ss, fs = set(state), set(function_ids)
result = {
    'metadata_full_md5_verified': True,
    'processed_archive_full_md5_verified': False,
    'function_member_crc_size_and_local_stream_verified': True,
    'pseudobulk_prefix_only': True,
    'state_columns': len(state), 'state_unique': len(ss),
    'function_rows': len(function_ids), 'function_unique': len(fs),
    'matched': len(ss & fs), 'state_only': sorted(ss - fs),
    'function_only': sorted(fs - ss), 'design_lines': sorted(design),
    'function_header': function_header,
    'label_finiteness_checked': False, 'response_values_cast': False,
    'state_header_lines_only_interpreted': True,
}
assert {x[0] for x in ss} == {x[0] for x in fs} == design
expected = json.loads((root / 'IDENTITY_JOIN.json').read_text())
keys = ['state_columns', 'state_unique', 'function_rows', 'function_unique', 'matched']
assert all(result[k] == expected[k] for k in keys)
assert result['state_only'] == expected['state_only']
assert [list(p) for p in result['function_only']] == expected['function_only']
result['root_count_and_missing_identity_comparison'] = 'PASS'
(out / 'IDENTITY_JOIN_INDEPENDENT.json').write_text(
    json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps({k: result[k] for k in keys}))
