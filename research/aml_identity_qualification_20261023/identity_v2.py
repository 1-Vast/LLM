"""Apply independently documented FWD grammar to the same retained tiny prefixes."""
import gzip
import hashlib
import json
from pathlib import Path
import re
import zlib

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/aml_identity_qualification'
OLD = ROOT/'log/20261023/post_anchor_mechanism/root_sources'
result = dict(contract_sha256=hashlib.sha256((OUT/'IDENTITY_V2_PROTOCOL.md').read_bytes()).hexdigest(),
              prefixes={}, scope='Source-backed nonrandom-prefix identity diagnostic only; no fits.')
for phase in ['pre', 'post']:
    receipt = json.loads((OUT/f'{phase}_barcodes.receipt.json').read_text(encoding='utf-8'))
    assert receipt['status'] == 200 and receipt['stop'] == 'COMPLETE'
    gex = {re.sub(r'-[0-9]+$', '', line) for line in
           gzip.decompress((OUT/f'{phase}_barcodes.body').read_bytes()).decode().splitlines()}
    prefix = (OLD/f'lineage_{phase}.compressed_prefix').read_bytes()
    decoder = zlib.decompressobj(16+zlib.MAX_WBITS)
    lines = decoder.decompress(prefix, 512*1024).split(b'\n')[:-1]
    header = lines[0].decode().rstrip('\r').split('\t')
    identifiers = []
    row_result = dict(inspected=0, status='GRAMMAR_PASS', complete_records_available=len(lines)-1)
    for row in lines[1:101]:
        row_result['inspected'] += 1
        fields = row.decode().rstrip('\r').split('\t')
        parts = fields[header.index('readName')].split('_') if len(fields) == len(header) else []
        if len(parts) != 7 or not re.fullmatch('[ACGTN]{28}FWD', parts[1]) or not re.fullmatch('[0-9]+', parts[2]):
            row_result.update(status='STOP_GRAMMAR_MISMATCH', failed_record=row_result['inspected'])
            break
        identifiers.append(parts[1][:16])
    distinct = set(identifiers)
    row_result.update(valid_records=len(identifiers), distinct_cell_barcodes=len(distinct),
                      direct_identity_matches=len(distinct & gex) if distinct else None,
                      direct_identity_fraction=len(distinct & gex)/len(distinct) if distinct else None)
    result['prefixes'][phase] = row_result
(OUT/'IDENTITY_V2.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
