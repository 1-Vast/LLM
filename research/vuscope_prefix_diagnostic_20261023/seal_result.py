"""Seal completed original results before independent arithmetic audits."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/vuscope_prefix_diagnostic'

if __name__ == '__main__':
    target = OUT/'RESULT_SEAL.json'
    assert not target.exists()
    paths = [p for p in (OUT/'pilot').rglob('*') if p.is_file()]
    paths += [OUT/'FREEZE.json', OUT/'EXECUTION.json', OUT/'pilot_console.txt', OUT/'POST_RESULT_SUMMARY.json']
    record = dict(utc=datetime.now(timezone.utc).isoformat(),
                  files={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)})
    target.write_text(json.dumps(record, indent=2), encoding='utf-8')
    print(json.dumps(dict(files=len(paths), result_seal=str(target))))
