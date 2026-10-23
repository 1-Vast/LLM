"""Bind the agreed diagnostic before any selected raw scalar decoding."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT/'log/20261023/functional_error_renewal'
CODE = ROOT/'research/functional_error_renewal_20261023'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    target = BASE/'FREEZE.json'
    if target.exists():
        raise FileExistsError(target)
    files = [BASE/'DIAGNOSTIC_PROTOCOL.md', BASE/'SYNTHETIC_CHECKS.json',
             CODE/'diagnostic.py', CODE/'test_diagnostic.py', Path(__file__),
             ROOT/'tmp/context_transfer_20261017/beataml_domain.npz']
    files += [BASE/role/name for role in ['constructive', 'critic']
              for name in ['INDEPENDENT.md', 'PREFLIGHT.md', 'CROSS.md']]
    files += [BASE/'frontier/INDEPENDENT.md', BASE/'frontier/DIAGNOSTIC_REVIEW.md',
              BASE/'root_sources/cd14_identity.body']
    bindings = {str(path.relative_to(ROOT)).replace('\\', '/'): digest(path)
                for path in files}
    manifest = dict(utc=datetime.now(timezone.utc).isoformat(),
                    git_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                      cwd=ROOT, text=True).strip(),
                    files=bindings, biological_numeric_access_before_freeze=False,
                    purpose='Source association diagnostic only; not clinical method validation')
    target.write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print(json.dumps(dict(bound_files=len(bindings), utc=manifest['utc'])))
