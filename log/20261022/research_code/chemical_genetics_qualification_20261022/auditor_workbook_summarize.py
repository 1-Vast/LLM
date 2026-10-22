"""Post-freeze helper: inspect only the approved JSON projection and hashes."""
from collections import Counter
import json

import auditor_workbook_identity as worker


def main():
    out = worker.OUT
    records = json.loads((out / 'STRUCTURE_AND_LABELS.json').read_text(encoding='utf-8'))
    summary = []
    checks = []
    frozen = json.loads((out / 'FREEZE.json').read_text(encoding='utf-8-sig'))
    for entry in frozen['files']:
        checks.append({'path': entry['path'], 'sha256_unchanged': worker.sha(entry['path']) == entry['sha256']})
    extracted = json.loads((out / 'EXTRACTED_WORKBOOKS.json').read_text(encoding='utf-8'))
    checks.append({'check': 'exact_extracted_whitelist',
                   'passed': sorted(worker.Path(e['path']).name for e in extracted) == sorted(worker.TARGETS)})
    for entry in extracted:
        checks.append({'path': entry['path'], 'sha256_unchanged': worker.sha(entry['path']) == entry['sha256']})
    for record in records:
        check_source = worker.sha(record['source_path']) == record['source_sha256'] == record['source_sha256_after']
        checks.append({'path': record['source_path'], 'projection_source_hash_unchanged': check_source})
        book = {'workbook': worker.Path(record['source_path']).name, 'sheets': []}
        for sheet in record['sheets']:
            labels = sheet['first_30_row_string_labels']
            assert all(1 <= int(worker.re.search(r'\d+$', c['coordinate'])[0]) <= 30 for c in labels)
            approved = [c for c in labels if 'label' in c]
            assert all(worker.filter_label(c['label']) == (c['label'], None) for c in approved)
            book['sheets'].append({k: sheet[k] for k in ['sheet_name', 'sheet_state', 'declared_dimension', 'merged_ranges', 'cell_type_counts']})
            book['sheets'][-1].update({'approved_header_or_identity_labels': approved,
                'withholding_counts': dict(Counter(c['withheld'] for c in labels if 'withheld' in c))})
        summary.append(book)
    passed = all(all(v for k, v in c.items() if k not in {'path', 'check'}) for c in checks)
    worker.write_json(out / 'CANDIDATE_IDENTITY_COORDINATES.json', summary)
    worker.write_json(out / 'VERIFICATION.json', {'utc': worker.utc(), 'all_passed': passed, 'checks': checks,
        'helper_scope': 'Post-freeze local helper; reads approved projection and hashes only. Not part of original frozen projector.'})
    print(json.dumps({'verification_passed': passed, 'summaries': summary}, ensure_ascii=False))
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
