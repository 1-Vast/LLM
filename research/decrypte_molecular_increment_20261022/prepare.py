"""Selective high-dose development extraction after pre-value protocol freeze."""
import csv
import hashlib
import json
from pathlib import Path
import time
import numpy as np
from freeze import verify

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_molecular_increment'
PREVIOUS = ROOT / 'log/20261022/decrypte_feedback_pilot'


def digest(path):
    sha = hashlib.sha256()
    with path.open('rb') as source:
        while block := source.read(1024 * 1024):
            sha.update(block)
    return sha.hexdigest()


def main():
    assert (OUT / 'FREEZE.json').exists(), 'No numerical response extraction before freeze'
    verify()
    assert not (OUT / 'matrix.npz').exists(), 'Do not overwrite extracted data'
    start = time.perf_counter()
    previous = json.loads((PREVIOUS / 'DEVELOPMENT_VALUES.json').read_text(encoding='utf-8'))
    partition = json.loads((PREVIOUS / 'PARTITIONS.json').read_text(encoding='utf-8'))
    manifest = json.loads((OUT / 'DOWNLOAD_MANIFEST.json').read_text(encoding='utf-8'))
    records = manifest['records']
    assert manifest.get('complete') and all(r['status'] in ('downloaded_unparsed', 'reused_archived_unparsed') for r in records), 'Incomplete downloads, not TSV input'
    assert len(records) == len({r['drug'] for r in records}) == 48
    assert set(r['drug'] for r in records) == set(previous['drugs']) == set(partition['partitions']['development'])
    rows_by_drug = {}
    scope = []
    payloads = {}
    policy = json.loads((OUT / 'IDENTITY_POLICY.json').read_text(encoding='utf-8'))
    aliases = policy['aliases']
    normalize = lambda s: aliases.get(s.strip(), s.strip())
    # Author file assignment only: this internal name is NOT an authenticated alias.
    uncertain_identity = policy['uncertain_file_labels']
    for item in sorted(records, key=lambda r: r['drug']):
        source = ROOT / item['path']
        assert digest(source) == item['sha256'], source
        entries = {}
        exact = []
        with source.open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.reader(handle, delimiter='\t')
            header = next(reader)
            assert len(header) == len(set(header)), 'Ambiguous duplicate header'
            positions = {n: header.index(n) for n in ('identifier', 'drug', 'Normalized_Intensity_10000')}
            for line, row in enumerate(reader, 2):
                if not row:
                    continue
                assert len(row) == len(header), (item['drug'], line, len(row), len(header))
                identifier = row[positions['identifier']]
                assert identifier and identifier not in entries, (item['drug'], line, 'empty/duplicate identifier')
                observed_drug = row[positions['drug']]
                expected = uncertain_identity.get(item['drug'], item['repository_drug'])
                assert normalize(observed_drug) == normalize(expected), (item['drug'], line, observed_drug)
                payload = row[positions['Normalized_Intensity_10000']]
                if payload.strip() in ('', 'NA', 'NaN', 'nan', '#N/A'):
                    value = np.nan
                else:
                    value = float(payload)
                    if not np.isfinite(value):
                        value = np.nan
                assert not np.isfinite(value) or value >= 0, (item['drug'], line, 'negative intensity')
                entries[identifier] = (value, line)
                exact.append((identifier, line, payload))
        rows_by_drug[item['drug']] = entries
        payloads[item['drug']] = exact
        scope.append({'drug': item['drug'], 'source': item['path'], 'sha256': item['sha256'],
                      'rows': len(entries), 'decoded_columns': list(positions),
                      'identity_contract': 'uncertain_author_file_assignment' if item['drug'] in uncertain_identity else 'matching_internal_name',
                      'missing_selected_dose': sum(not np.isfinite(v[0]) for v in entries.values())})
    identifiers = sorted(set().union(*(set(d) for d in rows_by_drug.values())))
    columns = {name: i for i, name in enumerate(identifiers)}
    x = np.full((48, len(identifiers)), np.nan)
    row_indices = np.zeros((48, len(identifiers)), dtype=np.int32)
    for i, drug in enumerate(previous['drugs']):
        for identifier, (value, row) in rows_by_drug[drug].items():
            j = columns[identifier]
            x[i, j] = value
            row_indices[i, j] = row
    np.savez_compressed(OUT / 'matrix.npz', intensity=x, row_indices=row_indices)
    (OUT / 'PAYLOADS.json').write_text(json.dumps(payloads, ensure_ascii=False), encoding='utf-8')
    result = {'drugs': previous['drugs'], 'groups': previous['groups'], 'identifiers': identifiers,
              'download_manifest_sha256': digest(OUT / 'DOWNLOAD_MANIFEST.json'),
              'scope': scope, 'source_functional_sha256': digest(PREVIOUS / 'DEVELOPMENT_VALUES.json'),
              'shape': list(x.shape), 'finite_entries': int(np.sum(np.isfinite(x))),
              'missing_entries': int(np.sum(~np.isfinite(x))), 'zero_entries': int(np.sum(x == 0)),
              'selected_dose': 10000, 'wall_s': time.perf_counter() - start,
              'uncertain_identity': uncertain_identity,
              'global_identifier_union_for_storage_only': True}
    (OUT / 'PREPARATION.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('shape', 'finite_entries', 'missing_entries', 'zero_entries', 'wall_s')}))


if __name__ == '__main__':
    main()
