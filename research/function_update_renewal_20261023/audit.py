"""Verify source bytes, independent seals and finite-check arithmetic, without refits."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/function_update_renewal'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipts_checked = 0
    statuses = {}
    for receipt_file in OUT.rglob('*.receipt.json'):
        receipt = json.loads(receipt_file.read_text(encoding='utf-8'))
        body = receipt_file.with_name(receipt_file.name.removesuffix('.receipt.json') + '.body')
        assert body.is_file(), body
        assert body.stat().st_size == receipt['bytes'] and digest(body) == receipt['sha256']
        status = str(receipt['status'])
        statuses[status] = statuses.get(status, 0) + 1
        receipts_checked += 1
    for name, suffix, key in [('constructive', 'INDEPENDENT.seal.json', 'path'), ('skeptic', 'INDEPENDENT_SEAL.json', 'file')]:
        seal = json.loads((OUT / name / suffix).read_text())
        assert digest(ROOT / seal[key]) == seal['sha256']
        assert not seal['peer_reports_read']
    skeptic = OUT / 'skeptic'
    for filename, extension, key in [('SEARCH_RECEIPTS.json', '.xml', 'name'), ('FULLTEXT_RECEIPTS.json', '.html', 'id')]:
        for receipt in json.loads((skeptic / filename).read_text()):
            body = skeptic / (receipt[key] + extension)
            assert body.stat().st_size == receipt['bytes'] and digest(body) == receipt['sha256']
            receipts_checked += 1
    weight = json.loads((OUT / 'WEIGHT_CHECK.json').read_text())
    assert weight['true_optimal_first'] in ['B', 'C'] and weight['weighted_optimal_first'] == 'A'
    assert abs(weight['true_expected_hit_gap'] - .05) < 1e-12
    operator = json.loads((OUT / 'constructive/OPERATOR_CHECK.json').read_text())
    assert max(operator['effective_head_update_max_errors']) < 1e-12
    assert operator['functional_nullspace_max_error'] < 1e-12
    assert operator['functional_nullspace_state_change_norm'] > 1
    composition = json.loads((OUT / 'constructive/COMPOSITION_CHECK.json').read_text())
    assert abs(composition['two_operator_actual_minus_first_order'] - composition['exact_second_order_term']) < 1e-12
    assert abs(composition['exact_second_order_term']) > .01
    for name in ['constructive', 'skeptic']:
        assert (OUT / name / 'CROSS.md').is_file()
    previous = json.loads((ROOT / 'log/20261022/norman_matched_guide/VERIFICATION.json').read_text())
    drift = [name for name, expected in previous['files'].items() if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
    assert not drift, drift
    report = {'status': 'PASS_LOCAL', 'source_receipts_checked': receipts_checked,
              'individual_receipt_status_counts': statuses, 'independent_seals_checked': 2,
              'predecessor_files_checked': len(previous['files']), 'predecessor_drift': drift,
              'scope': 'Finite algebra, source bytes and local continuity; not biological performance, exhaustive novelty or global provenance repair'}
    (OUT / 'AUDIT.json').write_text(json.dumps(report, indent=2))
    files = {}
    for folder in [OUT, Path(__file__).resolve().parent]:
        for path in sorted(folder.rglob('*')):
            if path.is_file() and path.name != 'VERIFICATION.json':
                files[path.relative_to(ROOT).as_posix()] = digest(path)
    (OUT / 'VERIFICATION.json').write_text(json.dumps({**report, 'files': files}, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
