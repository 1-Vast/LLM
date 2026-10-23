"""Diagnose syntax of exactly the stopped first record; export no record values."""
import hashlib
import json
from pathlib import Path
import re
import zlib

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/aml_identity_qualification'
OLD = ROOT/'log/20261023/post_anchor_mechanism/root_sources'
paths = [OUT/'IDENTITY_PROTOCOL.md', OUT/'IDENTITY_PROBE.json',
         ROOT/'research/aml_identity_qualification_20261023/identity_probe.py']
seal = dict(files={str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths})
target = OUT/'PROBE_SEAL.json'
if target.exists():
    assert json.loads(target.read_text(encoding='utf-8')) == seal
else:
    target.write_text(json.dumps(seal, indent=2), encoding='utf-8')
output = {}
for phase in ['pre', 'post']:
    decoder = zlib.decompressobj(16+zlib.MAX_WBITS)
    lines = decoder.decompress((OLD/f'lineage_{phase}.compressed_prefix').read_bytes(), 512*1024).split(b'\n')
    header = lines[0].decode().rstrip('\r').split('\t')
    fields = lines[1].decode().rstrip('\r').split('\t')
    parts = fields[header.index('readName')].split('_')
    output[phase] = dict(header_fields=len(header), row_fields=len(fields), underscore_fields=len(parts),
                         second_field_length=len(parts[1]),
                         second_field_uppercase_dna=bool(re.fullmatch('[ACGTN]+', parts[1])),
                         third_field_integer_syntax=bool(re.fullmatch('[0-9]+', parts[2])))
(OUT/'GRAMMAR_DIAGNOSTIC.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
print(json.dumps(output, indent=2))
