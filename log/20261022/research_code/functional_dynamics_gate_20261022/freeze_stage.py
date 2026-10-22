"""Final immutable file inventory; no model fit or new response access."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT/'log/20261022/functional_dynamics_gate'
CODE = ROOT/'research/functional_dynamics_gate_20261022'


def main():
    target = LOG/'FINAL_FILE_INVENTORY.json'
    if target.exists():
        raise FileExistsError('final_inventory_already_exists')
    paths = sorted(p for base in [LOG, CODE] for p in base.rglob('*') if p.is_file())
    entries = [{'path': str(p.relative_to(ROOT)), 'bytes': p.stat().st_size,
                'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]
    record = {'utc': datetime.now(timezone.utc).isoformat(), 'files': entries,
              'file_count': len(entries), 'bytes': sum(e['bytes'] for e in entries),
              'self_excluded': str(target.relative_to(ROOT)),
              'mutable_navigation_indexes_excluded': ['research/REPORT.md', 'log/README.md'],
              'goal': 'ACTIVE_NOT_ACHIEVED', 'turn': 'PROGRESS',
              'scope': 'local byte inventory, not independent scientific replication'}
    with target.open('x', encoding='utf-8') as f:
        json.dump(record, f, indent=2, ensure_ascii=False)
        f.write('\n')
    print(json.dumps({'files': len(entries), 'bytes': record['bytes']}))


if __name__ == '__main__':
    main()
