"""Local final bindings; source reviews and scientific claims have separate scope."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/grounded_feedback_renewal'
target = OUT/'VERIFICATION.json'
assert not target.exists()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


prior = ROOT/'log/20261023/contrast_transport_mechanism/VERIFICATION.json'
checks = [dict(file=name, matches=sha(ROOT/name)==expected)
          for name, expected in json.loads(prior.read_text())['files'].items()]
assert all(c['matches'] for c in checks)
audit = json.loads((OUT/'SOURCE_AUDIT.json').read_text())
assert audit['failures'] == 0 and audit['logical_gets'] == 16
for role in ['constructive', 'critic']:
    assert (OUT/role/'FINAL_REVIEW.md').exists()
assert (OUT/'DECISION.md').exists() and (OUT/'SOURCE_AGENT_FAILURE.md').exists()
files = sorted(p for p in OUT.rglob('*') if p.is_file())
files += sorted((ROOT/'research/grounded_feedback_renewal_20261023').rglob('*.py'))
files += [prior]
record = dict(utc=datetime.now(timezone.utc).isoformat(),
              files={str(p.relative_to(ROOT)): sha(p) for p in files},
              predecessor_checks=checks, failures=sum(not c['matches'] for c in checks),
              source_audit_checks=len(audit['checks']), source_audit_failures=audit['failures'],
              git_head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              python=platform.python_version(), scope='Local consistency; not scientific validation',
              goal='ACTIVE / NOT_ACHIEVED')
target.write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(dict(files=len(files), predecessor_checks=len(checks),
                     source_audit_checks=len(audit['checks']), failures=record['failures'])))
