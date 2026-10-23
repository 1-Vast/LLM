"""Verify phase receipts and pre-access stop without reading response values."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/intervention_constraint'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    count, statuses = 0, {}
    manifests = [('constructive', 'SEARCH_RECEIPTS.json'), ('constructive', 'PRIMARY_RECEIPTS.json'),
                 ('biology', 'RECEIPTS.json'), ('biology', 'METHOD_RECEIPTS.json')]
    for folder, filename in manifests:
        for row in json.loads((OUT / folder / filename).read_text()):
            name = row.get('name')
            if name is None:
                name = 'author_' + row['path'].replace('/', '_')
            body = OUT / folder / (name + '.body')
            assert body.stat().st_size == row['bytes'] and digest(body) == row['sha256'], body
            count += 1
            key = str(row['status'])
            statuses[key] = statuses.get(key, 0) + 1
    for folder, filename, pathkey, peerkey in [
        ('constructive', 'INDEPENDENT.seal.json', 'path', 'peer_reports_read'),
        ('biology', 'INDEPENDENT_SEAL.json', 'file', 'peer_reports_read_before_seal')]:
        seal = json.loads((OUT / folder / filename).read_text())
        assert digest(ROOT / seal[pathkey]) == seal['sha256'] and not seal[peerkey]
        for name in ['CROSS.md', 'FINAL_REVIEW.md']:
            assert (OUT / folder / name).is_file()
    receipt = json.loads((OUT / 'api/RECEIPT.json').read_text())
    assert receipt['status'] == 'RESPONSE_RETAINED' and receipt['finish_reason'] == 'stop'
    # API receipt hashes the request string, before Windows write_text CRLF translation.
    prompt_text = (OUT / 'api/PROMPT.md').read_text(encoding='utf-8')
    assert hashlib.sha256(prompt_text.encode()).hexdigest() == receipt['prompt_sha256']
    assert receipt['provider_usage']['total_tokens'] == receipt['provider_usage']['prompt_tokens'] + receipt['provider_usage']['completion_tokens']
    identity = json.loads((OUT / 'RECIPROCITY_IDENTITY.json').read_text())
    assert identity['status'] == 'STOP_IDENTITY' and identity['response_values_loaded'] == 0
    duplicate = {g: indices for g, indices in identity['feature_indices'].items() if len(indices) != 1}
    assert duplicate == {'RHOXF2B': [14109, 14112]}
    assert not (OUT / 'RECIPROCITY_RESULT.json').exists()
    assert not (OUT / 'RECIPROCITY_MATRIX.npz').exists()
    synthetic = json.loads((OUT / 'RECIPROCITY_TEST.json').read_text())
    assert synthetic['status'] == 'PASS_SYNTHETIC' and len(synthetic['cases']) == 5
    previous = json.loads((ROOT / 'log/20261023/function_update_renewal/VERIFICATION.json').read_text())
    drift = [name for name, expected in previous['files'].items() if not (ROOT / name).is_file() or digest(ROOT / name) != expected]
    assert not drift, drift
    report = {'status': 'PASS_LOCAL', 'receipt_bodies_checked': count, 'receipt_status_counts': statuses,
              'independent_seals_checked': 2, 'synthetic_cases': 5,
              'real_endpoint_gate': 'NOT_RUN_IDENTITY_STOP', 'deepseek_provider_usage': receipt['provider_usage'],
              'predecessor_files_checked': len(previous['files']), 'predecessor_drift': drift,
              'scope': 'Saved receipt/seal/code-path evidence; not biological validation, exhaustive novelty or global provenance repair'}
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
