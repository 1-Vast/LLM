"""Check local evidence seals and summarize receipts, without loading biological values."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/post_anchor_mechanism'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(path):
    payload = json.loads(path.read_text(encoding='utf-8'))
    files = payload.get('files', {})
    if isinstance(files, dict):
        entries = [{'path': name, 'sha256': value['sha256'] if isinstance(value, dict) else value}
                   for name, value in files.items()]
    else:
        entries = files
    if not entries and 'sha256' in payload and ('file' in payload or 'path' in payload):
        entries = [{'path': payload.get('file', payload.get('path')), 'sha256': payload['sha256']}]
    if not entries:
        raise ValueError(f'Unrecognized or empty seal: {path}')
    drift = []
    for entry in entries:
        target = Path(entry['path'])
        if not target.is_absolute():
            target = ROOT / target
        if not target.exists() or digest(target) != entry['sha256']:
            drift.append(entry['path'])
    return dict(files=len(entries), drift=drift)


if __name__ == '__main__':
    receipts = []
    for path in sorted(OUT.rglob('*.receipt.json')):
        item = json.loads(path.read_text(encoding='utf-8'))
        receipts.append(dict(path=str(path.relative_to(ROOT)),
                             status=item.get('status', item.get('error_type', 'UNSPECIFIED'))))
    ledger = dict(public_logical_requests=len(receipts),
                  status_counts=dict(Counter(str(row['status']) for row in receipts)),
                  receipts=receipts,
                  scope='One retained receipt per logical public request; redirects/transport attempts not attested.',
                  api=json.loads((OUT/'api/RECEIPT.json').read_text(encoding='utf-8')),
                  native_agent_usage='Exact model, tokens and currency not exposed.',
                  new_biological_fits=0, gpu_experiments=0, wet_experiments=0)
    (OUT/'COST_LEDGER.json').write_text(json.dumps(ledger, indent=2), encoding='utf-8')
    seals = [ROOT/'log/20261023/emerald_functional_rule/VERIFICATION.json',
             ROOT/'log/20261023/dose_update_qualification/VERIFICATION.json']
    seals.extend(path for path in OUT.rglob('*.json') if 'seal' in path.name.lower())
    checks = {str(path.relative_to(ROOT)): check(path) for path in sorted(seals)}
    files = sorted(path for base in [OUT, ROOT/'research/post_anchor_mechanism_20261023']
                   for path in base.rglob('*') if path.is_file() and path != OUT/'VERIFICATION.json')
    result = dict(utc=datetime.now(timezone.utc).isoformat(), checks=checks,
                  goal='ACTIVE / NOT_ACHIEVED',
                  phase='PROGRESS / GO_BOUNDED_AML_IDENTITY_QUALIFICATION; NO_NEW_CORE_GO',
                  files={str(path.relative_to(ROOT)): digest(path) for path in files},
                  provenance='Local byte integrity only; historical global provenance drift unresolved.')
    (OUT/'VERIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(dict(public_requests=len(receipts), status_counts=ledger['status_counts'],
                          sealed_files=len(files), checks=checks), indent=2))
