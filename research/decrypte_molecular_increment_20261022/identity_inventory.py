"""Metadata-only internal TSV identity inventory; never interprets response fields."""
from collections import Counter
from datetime import datetime, timezone
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_molecular_increment'
GOOD = {'downloaded_unparsed', 'reused_archived_unparsed'}


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        while block := f.read(1024 * 1024):
            h.update(block)
    return h.hexdigest()


def normalize(name):
    # Only the previously documented explicit TG spelling bridge and whitespace.
    name = name.strip()
    return {'TG100-115': 'TG-100-115'}.get(name, name)


def main():
    manifest_path = OUT / 'DOWNLOAD_MANIFEST.json'
    manifest_sha = sha256(manifest_path)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    partition = json.loads((ROOT / 'log/20261022/decrypte_feedback_pilot/PARTITIONS.json').read_text(encoding='utf-8'))
    allowed = set(partition['partitions']['development'])
    assert len(manifest['records']) == 48
    assert {r['drug'] for r in manifest['records']} == allowed
    results = []
    for item in manifest['records']:
        if item['status'] not in GOOD:
            continue
        assert item['partition'] == 'development' and item['drug'] in allowed
        path = ROOT / item['path']
        assert sha256(path) == item['sha256'], item['drug']
        names = Counter()
        identifiers = Counter()
        empty_identifiers = []
        rows = 0
        with path.open(encoding='utf-8-sig', newline='') as handle:
            reader = csv.reader(handle, delimiter='\t')
            header = next(reader)
            assert len(header) == len(set(header)), item['drug']
            id_col, drug_col = header.index('identifier'), header.index('drug')
            for number, row in enumerate(reader, 2):
                if not row:
                    continue
                assert len(row) == len(header), (item['drug'], number, 'column count')
                # All TSV fields are tokenized as strings; only these two fields are accessed.
                identifier, drug = row[id_col], row[drug_col]
                if not identifier:
                    empty_identifiers.append(number)
                identifiers[identifier] += 1
                names[drug] += 1
                rows += 1
        expected = item['repository_drug']
        duplicates = {key: count for key, count in identifiers.items() if count > 1}
        normalized_match = bool(names) and all(normalize(n) == normalize(expected) for n in names)
        results.append({'drug': item['drug'], 'repository_drug': expected,
                        'path': item['path'], 'sha256': item['sha256'], 'sha256_verified': True,
                        'row_count': rows, 'distinct_internal_drug_counts': dict(names),
                        'exact_internal_name_agreement': bool(names) and set(names) == {expected},
                        'strict_normalized_name_agreement': normalized_match,
                        'normalization': 'strip surrounding whitespace; existing explicit TG100-115/TG-100-115 spelling bridge only',
                        'duplicate_identifier_count': len(duplicates), 'duplicate_identifiers': duplicates,
                        'empty_identifier_rows': empty_identifiers,
                        'identity_disposition': 'unresolved_CHDI_author_file_assignment_only'
                        if item['drug'] == 'CHDI00465983' else 'names_agree' if normalized_match else 'unresolved_no_new_alias_authorized'})
    now = datetime.now(timezone.utc)
    output = {'time_utc': now.isoformat(), 'manifest_sha256_at_start': manifest_sha,
              'manifest_complete_flag': manifest.get('complete', False),
              'metadata_scope': ['identifier', 'drug'], 'numerical_values_interpreted': False,
              'successful_files_examined': len(results), 'unavailable_files_not_parsed': 48 - len(results),
              'mismatched_files': [r['drug'] for r in results if not r['strict_normalized_name_agreement']],
              'files_with_duplicate_identifiers': [r['drug'] for r in results if r['duplicate_identifier_count']],
              'records': results,
              'manifest_unchanged_during_run': sha256(manifest_path) == manifest_sha}
    body = json.dumps(output, ensure_ascii=False, indent=2)
    (OUT / 'IDENTITY_INVENTORY.json').write_text(body, encoding='utf-8')
    archive = OUT / 'review' / ('IDENTITY_INVENTORY_' + now.strftime('%Y%m%dT%H%M%S%fZ') + '.json')
    archive.write_text(body, encoding='utf-8')
    print(json.dumps({key: value for key, value in output.items() if key != 'records'}, indent=2))


if __name__ == '__main__':
    main()
