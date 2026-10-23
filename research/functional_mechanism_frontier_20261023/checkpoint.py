"""Seal this bounded review and verify previous local evidence without reading labels."""
import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/functional_mechanism_frontier'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(path):
    payload = json.loads(path.read_text(encoding='utf-8'))
    entries = payload.get('files', payload.get('artifacts', {}))
    if isinstance(entries, dict):
        entries = [dict(path=k, sha256=v['sha256'] if isinstance(v, dict) else v)
                   for k, v in entries.items()]
    if not entries and 'sha256' in payload:
        name = payload.get('file', payload.get('path', payload.get('artifact')))
        if name:
            entries = [dict(path=name, sha256=payload['sha256'])]
    if not entries:
        raise ValueError(f'Unknown seal format: {path}')
    drift = []
    for item in entries:
        target = Path(item.get('path', item.get('file', item.get('artifact'))))
        if not target.is_absolute():
            target = ROOT / target
        if not target.exists() or digest(target) != item['sha256']:
            drift.append(str(target))
    return dict(files=len(entries), drift=drift)


def main():
    receipts = []
    for path in sorted(OUT.rglob('*.receipt.json')):
        row = json.loads(path.read_text(encoding='utf-8'))
        receipts.append(dict(path=str(path.relative_to(ROOT)), status=row.get('status', 'UNEXPOSED')))
    requests = [json.loads(line) for line in (OUT/'source/REQUESTS.jsonl').read_text(encoding='utf-8').splitlines() if line]
    ledger = dict(public_logical_requests=len(receipts)+len(requests),
                  explicit_receipt_status_counts=dict(Counter(str(r['status']) for r in receipts)),
                  receipts=receipts, requests_without_status=len(requests),
                  source_request_log='source/REQUESTS.jsonl; saved bodies do not attest HTTP status',
                  transport_attempts='UNEXPOSED', deepseek_calls=0, new_biological_fits=0,
                  new_dataset_downloads=0, gpu_experiments=0, wet_experiments=0,
                  native_model_tokens_currency='UNEXPOSED; no estimate')
    (OUT/'COST_LEDGER.json').write_text(json.dumps(ledger, indent=2), encoding='utf-8')
    prior = [ROOT/'log/20261023/attenuation_identifiability/VERIFICATION.json',
             ROOT/'log/20261023/reusable_error_mechanism/VERIFICATION.json']
    seals = [p for p in OUT.rglob('*.json') if 'seal' in p.name.lower()]
    seals.append(OUT/'OPERATION_FREEZE.json')
    checks = {str(p.relative_to(ROOT)): check(p) for p in sorted(prior+seals)}
    if any(c['drift'] for c in checks.values()):
        raise RuntimeError(json.dumps(checks, indent=2))
    files = sorted(p for base in [OUT, ROOT/'research/functional_mechanism_frontier_20261023']
                   for p in base.rglob('*') if p.is_file() and p != OUT/'VERIFICATION.json')
    result = dict(utc=datetime.now(timezone.utc).isoformat(), goal='ACTIVE / NOT_ACHIEVED',
                  phase='COMPLETE_BOUNDED_REVIEW / NONE / NO_NEW_CORE_GO', checks=checks,
                  files={str(p.relative_to(ROOT)): digest(p) for p in files},
                  provenance='Local byte integrity only; historical global drift remains unresolved.')
    (OUT/'VERIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(dict(sealed_files=len(files), checked_seals=len(checks), drift=0,
                          public_logical_requests=ledger['public_logical_requests'],
                          explicit_status=ledger['explicit_receipt_status_counts']), indent=2))


if __name__ == '__main__':
    main()
