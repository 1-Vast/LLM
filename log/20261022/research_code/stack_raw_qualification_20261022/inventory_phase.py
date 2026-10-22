"""Inventory the completed bounded phase without reading response cells."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/stack_raw_qualification'
CODE = ROOT / 'research/stack_raw_qualification_20261022'
target = LOG / 'FINAL_FILE_INVENTORY.json'
verification = json.loads((LOG / 'VERIFICATION.json').read_text(encoding='utf-8'))
assert verification['all_pass']
files = [{'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
          'sha256': hashlib.sha256(path.read_bytes()).hexdigest()}
         for folder in [LOG, CODE] for path in sorted(folder.rglob('*'))
         if path.is_file() and path != target]
with target.open('x', encoding='utf-8') as stream:
    json.dump({'utc': datetime.now(timezone.utc).isoformat(), 'files': files,
               'excluded': ['this inventory', 'mutable navigation indexes']},
              stream, ensure_ascii=False, indent=2)
    stream.write('\n')
print(json.dumps({'inventoried_files': len(files), 'bytes': sum(item['bytes'] for item in files),
                  'prior_preserved_files': verification['preserved_prior_files'],
                  'goal_status': 'ACTIVE_NOT_ACHIEVED'}))
