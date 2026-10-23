"""Freeze reviewed final accounting version and exposed cache before numerical use."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/feedback_law_discovery'


if __name__ == '__main__':
    target = OUT/'PILOT_FREEZE.json'
    assert not target.exists(), 'Never overwrite a prior freeze'
    assert not (OUT/'pilot/INITIATED.json').exists(), 'Freeze must precede label access'
    code = ROOT/'research/feedback_law_discovery_20261023'
    files = [OUT/'PILOT_PROTOCOL_ACCOUNTED.md', code/'pilot_accounted.py', code/'test_pilot.py',
             code/'run_pilot.py', OUT/'pilot/SYNTHETIC_CHECKS.json', ROOT/'tmp/context_transfer_20261017/beataml_domain.npz']
    files.extend(OUT.glob('*/PRE_EXECUTION_REVIEW.md'))
    files.extend(OUT.glob('*/PRE_EXECUTION_REVIEW*seal.json'))
    files.extend(OUT.glob('critic/ACCOUNTING_REVIEW*'))
    assert (OUT/'critic/ACCOUNTING_REVIEW.md').exists(), 'Wait for final accounting review'
    payload = dict(utc=datetime.now(timezone.utc).isoformat(),
                   head=subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
                   python=platform.python_version(), seeds=[0,1,2], device='CPU',
                   exposure='Previously exposed development, no new confirmation claim',
                   files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    target.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps(dict(status='FROZEN', files=len(files)), indent=2))
