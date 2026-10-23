"""Freeze exact necessary-condition check before its first execution."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/update_strategy_renewal'

if __name__ == '__main__':
    target = OUT/'PAIRED_CREDIT_FREEZE.json'
    assert not target.exists()
    paths = [OUT/'PAIRED_CREDIT_PROTOCOL.md', Path(__file__).with_name('paired_credit_check.py'),
             OUT/'constructive/INDEPENDENT.md', OUT/'critic/INDEPENDENT.md', OUT/'source/INDEPENDENT.md']
    body = dict(utc=datetime.now(timezone.utc).isoformat(),
                files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
                opposing_review='Constructive accepted same-task antithetic stronger control; critic accepted with same-task access, legal symmetric actions, score-at-zero and equal2evaluation independent-noise assumptions; all explicit in protocol',
                boundary='Mathematical exact enumeration only; no generated code, fit or biology')
    target.write_text(json.dumps(body, indent=2), encoding='utf-8')
    print(json.dumps(dict(files=len(paths), frozen=True)))
