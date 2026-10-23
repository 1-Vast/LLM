"""Verify prior and new local seals; record actual calls and fixed experiment costs."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/reusable_error_mechanism'
check = runpy.run_path(str(ROOT / 'research/post_anchor_mechanism_20261023/checkpoint.py'))['check']


def main():
    paths = [ROOT / 'log/20261023/mechanism_reentry/VERIFICATION.json',
             ROOT / 'log/20261023/mixed_feedback_estimator/VERIFICATION.json']
    paths.extend(p for p in OUT.rglob('*.json') if 'seal' in p.name.lower())
    paths.extend([OUT / 'OVERLAP_FREEZE.json', OUT / 'ATTENUATION_FREEZE.json'])
    checks = {str(p.relative_to(ROOT)): check(p) for p in sorted(set(paths))}
    margin = json.loads((OUT / 'MARGIN_CHECK_FREEZE.json').read_text(encoding='utf-8'))
    checks['MARGIN_CHECK_FREEZE'] = dict(files=len(margin), drift=[name for name, digest in margin.items()
               if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest])
    assert all(not row['drift'] for row in checks.values()), checks
    receipts = []
    for p in sorted(OUT.rglob('*.receipt.json')):
        row = json.loads(p.read_text(encoding='utf-8'))
        receipts.append(dict(path=str(p.relative_to(ROOT)), status=row.get('status', row.get('error'))))
    experiment = {name: json.loads((OUT / (name + '_RESULT.json')).read_text(encoding='utf-8'))
                  for name in ['OVERLAP', 'ATTENUATION']}
    api = json.loads((OUT / 'api/RECEIPT.json').read_text(encoding='utf-8'))
    assert api['status'] == 'RESPONSE_RETAINED'
    ledger = dict(public_logical_requests=len(receipts),
                  status_counts=dict(Counter(str(row['status']) for row in receipts)), public_receipts=receipts,
                  deepseek=api, fixed_state_scalar_fits=sum(r['fit_calls'] for r in experiment.values()),
                  summed_recorded_experiment_seconds=sum(r['seconds'] for r in experiment.values()),
                  independent_audit_work='Separate reconstructions; not biological replications or new model trials',
                  raw_matrix_reads=0, functional_label_reads=0, protected_outcomes_read=0,
                  wet_experiments=0, gpu_fits=0, native_model_tokens_currency='NOT_EXPOSED',
                  currency_and_transport_attempt_cost='NOT_EXPOSED', python=sys.version, interpreter=sys.executable,
                  scope='Script intervals omit source/review/API/audit costs. No equal-total-cost superiority.')
    (OUT / 'COST_LEDGER.json').write_text(json.dumps(ledger, indent=2), encoding='utf-8')
    files = sorted(p for base in [OUT, ROOT / 'research/reusable_error_mechanism_20261023']
                   for p in base.rglob('*') if p.is_file() and p != OUT / 'VERIFICATION.json')
    result = dict(utc=datetime.now(timezone.utc).isoformat(), goal='ACTIVE / NOT_ACHIEVED',
                  phase='PROGRESS / STOP_OVERLAP_SPECIFIC_ADVANTAGE / NO_NEW_CORE_GO', checks=checks,
                  files={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                  provenance='Local continuity only; historical global provenance drift unresolved.')
    (OUT / 'VERIFICATION.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(dict(files=len(files), seals=len(checks), drift=0,
                         public_logical_requests=len(receipts), statuses=ledger['status_counts'],
                         fixed_state_scalar_fits=ledger['fixed_state_scalar_fits'],
                         deepseek_tokens=api['provider_usage']['total_tokens']), indent=2))


if __name__ == '__main__':
    main()
