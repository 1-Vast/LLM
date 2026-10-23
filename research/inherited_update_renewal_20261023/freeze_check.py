"""Seal the actual incomplete API artifact and root checks before their run."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/inherited_update_renewal'

if __name__ == '__main__':
    target = OUT/'API_CHECK_FREEZE.json'
    assert not target.exists() and not (OUT/'API_CHECK.json').exists()
    paths = [OUT/'API_CHECK_PROTOCOL.md', OUT/'api/PROMPT.md', OUT/'api/PROPOSAL.md', OUT/'api/RECEIPT.json',
             ROOT/'research/inherited_update_renewal_20261023/api_check.py', Path(__file__)]
    files = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in paths}
    target.write_text(json.dumps({'utc': datetime.now(timezone.utc).isoformat(), 'files': files}, indent=2),
                      encoding='utf-8')
    print(json.dumps({'frozen_files': len(files)}))
