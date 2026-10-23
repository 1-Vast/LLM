"""Bind the exact before-value design and executable implementation."""
import datetime as dt
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_feedback_pilot'
CODE = ROOT / 'research/decrypte_feedback_pilot_20261022'


def main():
    assert not (OUT / 'DEVELOPMENT_VALUES.json').exists()
    assert not (OUT / 'FREEZE.json').exists()
    paths = [OUT / n for n in ('START.md', 'PARTITIONS.json', 'NUMERICAL_PROTOCOL_DRAFT.md',
                              'PROTOCOL_AMENDMENT_BEFORE_VALUES.md', 'SYNTHETIC_CHECKS.json', 'review/INDEPENDENT.md')]
    paths.extend(CODE.glob('*.py'))
    result = {'time_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
              'numerical_values_unopened': True, 'scope': 'Before-development-values implementation and design',
              'files': {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
    (OUT / 'FREEZE.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'status': 'FROZEN', 'files': len(paths)}))


if __name__ == '__main__':
    main()
