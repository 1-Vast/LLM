"""Final local continuity/cost inventory; no scientific success certification."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import subprocess
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/attenuation_identifiability'
check = runpy.run_path(str(ROOT / 'research/post_anchor_mechanism_20261023/checkpoint.py'))['check']


def main():
    seals = [ROOT / 'log/20261023/reusable_error_mechanism/VERIFICATION.json',
             ROOT / 'log/20261023/mixed_feedback_estimator/VERIFICATION.json', OUT / 'FREEZE.json']
    seals.extend(p for p in OUT.rglob('*.json') if 'seal' in p.name.lower())
    checks = {}
    for p in sorted(set(seals)):
        payload = json.loads(p.read_text(encoding='utf-8'))
        if 'artifact' in payload and 'sha256' in payload:
            target = Path(payload['artifact'])
            checks[str(p.relative_to(ROOT))] = dict(files=1, drift=[] if target.exists() and
                 hashlib.sha256(target.read_bytes()).hexdigest() == payload['sha256'] else [str(target)])
        else:
            checks[str(p.relative_to(ROOT))] = check(p)
    assert all(not item['drift'] for item in checks.values()), checks
    experiment = json.loads((OUT / 'RESULT.json').read_text(encoding='utf-8'))
    assert experiment['status'] == 'VERIFIED_ALGEBRA_ONLY_NO_CAUSAL_ATTRIBUTION'
    ledger = dict(public_logical_requests=0, deepseek_requests=0, model_fits=0,
                  actual_diagnostic_runs=1, diagnostic_recorded_seconds=experiment['seconds'],
                  independent_audits='Separate saved-array reconstruction, not raw extraction or new biological samples',
                  synthetic_witnesses='Root two-composition construction plus independently retained role analytic examples',
                  raw_matrix_reads=0, function_labels_read=0, protected_outcomes_read=0, wet_experiments=0, gpu_fits=0,
                  native_agent_exact_model_tokens_currency='NOT_EXPOSED',
                  total_research_cost='Not equal to diagnostic script interval; prior source/review/audit costs remain',
                  python=sys.version, interpreter=sys.executable, numpy=np.__version__, random_seed='NONE_DETERMINISTIC',
                  git_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
    (OUT / 'COST_LEDGER.json').write_text(json.dumps(ledger, indent=2), encoding='utf-8')
    files = sorted(p for base in [OUT, ROOT / 'research/attenuation_identifiability_20261023']
                   for p in base.rglob('*') if p.is_file() and p != OUT / 'VERIFICATION.json')
    inventory = dict(utc=datetime.now(timezone.utc).isoformat(), checks=checks,
                     goal='ACTIVE / NOT_ACHIEVED', phase='PROGRESS / NO_NEW_CORE_GO / STOP_CAUSAL_PROMOTION',
                     files={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in files},
                     provenance='Local byte continuity only; historical global provenance drift unresolved')
    (OUT / 'VERIFICATION.json').write_text(json.dumps(inventory, indent=2), encoding='utf-8')
    print(json.dumps(dict(files=len(files), seals=len(checks), drift=0, model_fits=0,
                         public_requests=0, deepseek_requests=0, status=experiment['status']), indent=2))


if __name__ == '__main__':
    main()
