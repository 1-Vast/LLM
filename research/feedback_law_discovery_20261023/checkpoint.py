"""Verify sealed review/results, retain costs, and seal this completed bounded phase."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/feedback_law_discovery'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(path):
    payload = json.loads(path.read_text(encoding='utf-8'))
    entries = payload.get('files', payload.get('artifacts', {}))
    if isinstance(entries, dict):
        entries = [dict(path=k, sha256=v['sha256'] if isinstance(v, dict) else v) for k,v in entries.items()]
    if not entries and 'sha256' in payload:
        name = payload.get('file', payload.get('path', payload.get('artifact')))
        implicit = {
            OUT/'constructive/RESULT_CROSS.seal.json': OUT/'constructive/RESULT_CROSS.md',
            OUT/'constructive/SERIALIZATION_SCOPE_ADDENDUM.seal.json': OUT/'constructive/SERIALIZATION_SCOPE_ADDENDUM.md',
            OUT/'constructive/TITANS_PROVENANCE_CORRECTION.seal.json': OUT/'constructive/TITANS_PROVENANCE_CORRECTION.md',
        }
        if name is None and path in implicit:
            name = str(implicit[path])
        if name:
            entries = [dict(path=name, sha256=payload['sha256'])]
    if not entries:
        raise ValueError(f'Unknown seal format: {path}')
    drift = []
    for entry in entries:
        target = Path(entry.get('path', entry.get('file', entry.get('artifact'))))
        if not target.is_absolute():
            target = ROOT/target
        if not target.exists() or digest(target) != entry['sha256'].lower():
            drift.append(str(target))
    return dict(files=len(entries), drift=drift)


if __name__ == '__main__':
    receipts = []
    for path in sorted(OUT.rglob('*.receipt.json')):
        row = json.loads(path.read_text(encoding='utf-8'))
        error_status = re.search(r'HTTP Error (\d{3})', row.get('error', ''))
        status = row.get('status', int(error_status.group(1)) if error_status else 'UNEXPOSED')
        receipts.append(dict(path=str(path.relative_to(ROOT)), status=status,
                             status_source='status field' if 'status' in row else 'retained HTTPError string'))
    source_requests = [json.loads(line) for line in (OUT/'source/REQUESTS.jsonl').read_text(encoding='utf-8').splitlines() if line]
    summary = json.loads((OUT/'pilot/SUMMARY.json').read_text(encoding='utf-8'))
    ledger = dict(public_logical_requests=len(receipts)+len(source_requests),
        explicit_status_counts=dict(Counter(str(r['status']) for r in receipts+source_requests)),
        receipts=receipts, source_request_log='source/REQUESTS.jsonl',
        public_transport_attempts='UNEXPOSED', api=json.loads((OUT/'api/RECEIPT.json').read_text(encoding='utf-8')),
        native_model_tokens_currency='UNEXPOSED; no estimate',
        neural_functional_model_trainings=12, covariance_fits=1,
        source_mean_scale_fit='Shared source-only preprocessing, not12separate label acquisitions',
        new_dataset_downloads=0, new_wet_experiments=0, gpu_experiments=0,
        pilot_run=json.loads((OUT/'pilot/RUN_RECEIPT.json').read_text(encoding='utf-8')),
        replay_counts={k:summary[k] for k in ['context_episode_replays','context_view_evaluations','scalar_query_evaluations','fast_package_gradient_evaluations']},
        scope='Replayed computation units are not independent assays/tasks; historical assay costs unknown. Matching views does not match exact FLOPs.')
    (OUT/'COST_LEDGER.json').write_text(json.dumps(ledger, indent=2), encoding='utf-8')
    previous = [ROOT/'log/20261023/attenuation_identifiability/VERIFICATION.json',
                ROOT/'log/20261023/reusable_error_mechanism/VERIFICATION.json',
                ROOT/'log/20261023/functional_mechanism_frontier/VERIFICATION.json']
    seals = [p for p in OUT.rglob('*.json') if 'seal' in p.name.lower()]
    seals.extend([OUT/'API_CHECK_FREEZE.json', OUT/'PILOT_FREEZE.json'])
    checks = {str(p.relative_to(ROOT)):check(p) for p in sorted(previous+seals)}
    if any(c['drift'] for c in checks.values()):
        raise RuntimeError(json.dumps(checks, indent=2))
    files = sorted(p for base in [OUT, ROOT/'research/feedback_law_discovery_20261023']
                   for p in base.rglob('*') if p.is_file() and p != OUT/'VERIFICATION.json')
    payload = dict(utc=datetime.now(timezone.utc).isoformat(), goal='ACTIVE / NOT_ACHIEVED',
                   phase='PROGRESS / STOP_FIXED_CONSISTENCY_CONFIGURATION / NO_NEW_CORE_GO',
                   checks=checks, files={str(p.relative_to(ROOT)):digest(p) for p in files},
                   provenance='Local byte integrity only; no repair of historical global provenance drift.')
    (OUT/'VERIFICATION.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps(dict(sealed_files=len(files), checked_seals=len(checks), drift=0,
                         public_logical_requests=ledger['public_logical_requests'],
                         statuses=ledger['explicit_status_counts'], pilot=summary['status']), indent=2))
