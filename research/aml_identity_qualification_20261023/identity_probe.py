"""Frozen small library-identifier probe; never request expression matrices."""
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import gzip
import hashlib
import json
from pathlib import Path
import re
import zlib
import requests

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/aml_identity_qualification'
OLD = ROOT/'log/20261023/post_anchor_mechanism/root_sources'
CONTRACT = hashlib.sha256((OUT/'IDENTITY_PROTOCOL.md').read_bytes()).hexdigest()
BASE = 'https://ftp.ncbi.nlm.nih.gov/geo/series/GSE289nnn/GSE289454/suppl/'
ITEMS = [(phase, kind, f'GSE289454_sample{number}_scRNA_humanAML_lines_{label}.{kind}.tsv.gz')
         for phase, number, label in [('pre', 3, 'preAraC'), ('post', 4, 'postAraC')]
         for kind in ['features', 'barcodes']]


def fetch(item):
    phase, kind, name = item
    target = OUT/f'{phase}_{kind}'
    record = dict(url=BASE+name, utc=datetime.now(timezone.utc).isoformat(), contract_sha256=CONTRACT)
    body = bytearray()
    try:
        with requests.get(BASE+name, stream=True, timeout=40) as response:
            record['status'] = response.status_code
            for part in response.iter_content(65536):
                if len(body)+len(part) > 4*1024*1024:
                    record['stop'] = 'COMPRESSED_CAP'
                    break
                body.extend(part)
            else:
                record['stop'] = 'COMPLETE'
    except Exception as error:
        record.update(error_type=type(error).__name__, error=str(error))
    target.with_suffix('.body').write_bytes(body)
    record.update(bytes=len(body), sha256=hashlib.sha256(body).hexdigest())
    target.with_suffix('.receipt.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    return phase, kind, record


def parse_prefix(phase, gex):
    source = OLD/f'lineage_{phase}.compressed_prefix'
    decoder = zlib.decompressobj(16+zlib.MAX_WBITS)
    decoded = decoder.decompress(source.read_bytes(), 512*1024)
    complete = decoded.split(b'\n')[:-1]
    columns = complete[0].decode('utf-8').rstrip('\r').split('\t')
    index = columns.index('readName')
    rows = complete[1:101]
    identifiers = []
    result = dict(source=str(source.relative_to(ROOT)), prefix_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
                  complete_records_available=len(complete)-1, maximum_records=100, inspected=0,
                  status='GRAMMAR_PASS', scope='Nonrandom compressed prefix; identity candidate only.')
    for row in rows:
        result['inspected'] += 1
        fields = row.decode('utf-8').rstrip('\r').split('\t')
        parts = fields[index].split('_') if len(fields) == len(columns) else []
        if len(parts) != 7 or not re.fullmatch('[ACGTN]{28,}', parts[1]) or not re.fullmatch('[0-9]+', parts[2]):
            result.update(status='STOP_GRAMMAR_MISMATCH', failed_record=result['inspected'],
                          readname_field_count=len(parts), row_field_count=len(fields))
            break
        identifiers.append(parts[1][:16])
    distinct = set(identifiers)
    result.update(valid_records=len(identifiers), distinct_cell_barcodes=len(distinct))
    if gex is not None:
        matches = distinct.intersection(gex)
        result.update(direct_identity_matches=len(matches),
                      direct_identity_fraction=len(matches)/len(distinct) if distinct else None)
    else:
        result['direct_identity_matches'] = 'NOT_EVALUABLE_MISSING_GEX'
    return result


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        receipts = list(pool.map(fetch, ITEMS))
    output = dict(contract_sha256=CONTRACT, libraries={}, prefixes={})
    for phase in ['pre', 'post']:
        library = {}
        gex = None
        for _, kind, receipt in [row for row in receipts if row[0] == phase]:
            if receipt.get('status') != 200 or receipt.get('stop') != 'COMPLETE':
                library[kind] = dict(status='SOURCE_NOT_QUALIFIED')
                continue
            lines = gzip.decompress((OUT/f'{phase}_{kind}.body').read_bytes()).decode('utf-8').splitlines()
            if kind == 'features':
                fields = [line.split('\t') for line in lines]
                library[kind] = dict(rows=len(fields), field_counts=dict(Counter(len(row) for row in fields)),
                    feature_types=dict(Counter(row[2] if len(row) > 2 else 'UNDECLARED' for row in fields)),
                    non_gene_expression=[row for row in fields if len(row) > 2 and row[2] != 'Gene Expression'])
            else:
                normalized = [re.sub(r'-[0-9]+$', '', line) for line in lines]
                gex = set(normalized)
                library[kind] = dict(rows=len(lines), unique_full=len(set(lines)), unique_without_suffix=len(gex),
                    suffixes=dict(Counter(re.search(r'-[0-9]+$', line).group() if re.search(r'-[0-9]+$', line) else 'NONE'
                                          for line in lines)),
                    normalized_lengths=dict(Counter(map(len, normalized))))
        output['libraries'][phase] = library
        output['prefixes'][phase] = parse_prefix(phase, gex)
    (OUT/'IDENTITY_PROBE.json').write_text(json.dumps(output, indent=2), encoding='utf-8')
    print(json.dumps(output, indent=2))
