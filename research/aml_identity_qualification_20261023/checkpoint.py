"""Verify existing and current local seals, then inventory this qualification phase."""
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/aml_identity_qualification'
check = runpy.run_path(str(ROOT/'research/post_anchor_mechanism_20261023/checkpoint.py'))['check']
seals = [ROOT/'log/20261023/post_anchor_mechanism/VERIFICATION.json',
         ROOT/'log/20261023/emerald_functional_rule/VERIFICATION.json',
         ROOT/'log/20261023/dose_update_qualification/VERIFICATION.json']
seals.extend(path for path in OUT.rglob('*.json') if 'seal' in path.name.lower())
checks = {str(path.relative_to(ROOT)): check(path) for path in sorted(seals)}
assert all(not result['drift'] for result in checks.values()), checks
receipts = [dict(path=str(path.relative_to(ROOT)),
                 status=json.loads(path.read_text(encoding='utf-8')).get('status'))
            for path in sorted(OUT.rglob('*.receipt.json'))]
ledger = dict(public_logical_requests=len(receipts),
              status_counts=dict(Counter(str(row['status']) for row in receipts)), receipts=receipts,
              deepseek_calls=0, gpu_fits=0, new_biological_fits=0, wet_experiments=0,
              native_agent_model_usage_cost='NOT_EXPOSED',
              scope='Retained logical requests only; transport attempts, redirects/retries not fully attested.')
(OUT/'COST_LEDGER.json').write_text(json.dumps(ledger, indent=2), encoding='utf-8')
paths = sorted(path for base in [OUT, ROOT/'research/aml_identity_qualification_20261023']
               for path in base.rglob('*') if path.is_file() and path != OUT/'VERIFICATION.json')
verification = dict(utc=datetime.now(timezone.utc).isoformat(), checks=checks,
                    goal='ACTIVE / NOT_ACHIEVED', phase='PROGRESS / STOP_LOCAL_UNAUTHENTICATED_AML_FATE_TASK',
                    files={str(path.relative_to(ROOT)): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths},
                    provenance='Local byte integrity only; historical global drift unresolved.')
(OUT/'VERIFICATION.json').write_text(json.dumps(verification, indent=2), encoding='utf-8')
print(json.dumps(dict(files=len(paths), checks=checks, costs=ledger), indent=2))
