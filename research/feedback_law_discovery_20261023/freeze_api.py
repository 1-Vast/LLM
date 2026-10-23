"""Bind retained proposal and locally reviewed check before execution."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/feedback_law_discovery'


if __name__ == '__main__':
    target = OUT/'API_CHECK_FREEZE.json'
    assert not target.exists(), 'Do not overwrite a prior freeze'
    files = [OUT/'API_CHECK_PROTOCOL.md', OUT/'api/PROPOSAL.md', OUT/'api/PROMPT.md',
             OUT/'api/RECEIPT.json', ROOT/'research/feedback_law_discovery_20261023/check_api.py']
    payload = dict(utc=datetime.now(timezone.utc).isoformat(),
                   files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files})
    target.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps(dict(frozen_files=len(files)), indent=2))
