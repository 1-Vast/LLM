"""Verify local source/review checkpoints and record this bounded phase."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/mechanism_reentry'
check = runpy.run_path(str(ROOT/'research/post_anchor_mechanism_20261023/checkpoint.py'))['check']
seals = [ROOT/f'log/20261023/{name}/VERIFICATION.json' for name in
         ['aml_identity_qualification', 'post_anchor_mechanism', 'emerald_functional_rule', 'dose_update_qualification']]
seals.extend(path for path in OUT.rglob('*.json') if 'seal' in path.name.lower())
checks = {str(path.relative_to(ROOT)): check(path) for path in sorted(seals)}
assert all(not row['drift'] for row in checks.values()), checks
receipts = [dict(path=str(path.relative_to(ROOT)),
                 status=json.loads(path.read_text(encoding='utf-8')).get('status'))
            for path in sorted(OUT.rglob('*.receipt.json'))]
ledger = dict(public_logical_requests=len(receipts),
              status_counts=dict(Counter(str(row['status']) for row in receipts)), receipts=receipts,
              deepseek_calls=0, new_biological_fits=0, gpu_fits=0, wet_experiments=0,
              operation_checks='one critic analytic witness plus root independent rational reconstruction',
              interpreter=sys.executable, python=sys.version,
              native_agent_model_tokens_currency='NOT_EXPOSED',
              scope='Logical calls only; redirects/transport retries not fully attested.')
(OUT/'COST_LEDGER.json').write_text(json.dumps(ledger, indent=2), encoding='utf-8')
files = sorted(path for base in [OUT, ROOT/'research/mechanism_reentry_20261023']
               for path in base.rglob('*') if path.is_file() and path != OUT/'VERIFICATION.json')
verification = dict(utc=datetime.now(timezone.utc).isoformat(), checks=checks,
                    goal='ACTIVE / NOT_ACHIEVED', phase='PROGRESS / NO_NEW_CORE_GO',
                    files={str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in files},
                    provenance='Local byte continuity only; historical global provenance drift unresolved.')
(OUT/'VERIFICATION.json').write_text(json.dumps(verification, indent=2), encoding='utf-8')
print(json.dumps(dict(files=len(files), checks=checks,
                     public_logical_requests=len(receipts), status_counts=ledger['status_counts']), indent=2))
