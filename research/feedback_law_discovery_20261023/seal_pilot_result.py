"""Bind the completed single pilot's outputs without changing its run artifacts."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/feedback_law_discovery'


if __name__ == '__main__':
    target = OUT/'PILOT_RESULT_SEAL.json'
    assert not target.exists(), 'Do not overwrite a prior result seal'
    receipt = json.loads((OUT/'pilot/RUN_RECEIPT.json').read_text(encoding='utf-8'))
    assert receipt['status']=='COMPLETED' and receipt['returncode']==0
    files = [p for p in (OUT/'pilot').rglob('*') if p.is_file()]
    files.extend([ROOT/'research/feedback_law_discovery_20261023/pilot_accounted.py',
                  ROOT/'research/feedback_law_discovery_20261023/summarize_pilot.py', OUT/'PILOT_FREEZE.json'])
    target.write_text(json.dumps(dict(utc=datetime.now(timezone.utc).isoformat(),
        files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}), indent=2), encoding='utf-8')
    print(json.dumps(dict(sealed_files=len(files)), indent=2))
