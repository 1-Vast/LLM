"""Bind the review's existing evidence; no scientific experiments are run."""
import ast
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/rsi_external_proposal_review'
EXPECTED = {
    'PROPOSAL.txt': 'ba2c8b068c0786b9717c00ca6952f1528b5df8a4806c141919f0cb34d6986498',
    'DATA_REVIEW.md': 'c9e0d1fea3d2b4f0f52437b210450283c0618fe6556b7a54de0f3a1854e22f15',
    'NOVELTY_REVIEW.md': '5afb8a5d32ac7c642081e36bb0f3fc8a4b5f3db64b781f367fd091bff029e00b',
    'RECURSION_REVIEW.md': '8e2bfec984dd23517195afc3cd5aeb2e4b56615d580d211c7acfadc4bfe38b82',
}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    for name, expected in EXPECTED.items():
        assert sha(OUT / name) == expected, name
    receipts = json.loads((OUT / 'primary/RECEIPTS.json').read_text())
    assert len(receipts) == 2
    for row in receipts:
        path = OUT / 'primary' / (row['name'] + '.body')
        assert row['status'] == 200 and path.stat().st_size == row['bytes']
        assert sha(path) == row['sha256']
    for name in ('CROSS_NOVELTY.md', 'CROSS_RECURSION.md', 'DECISION.md'):
        assert (OUT / name).is_file(), name
    for path in Path(__file__).parent.glob('*.py'):
        ast.parse(path.read_text(encoding='utf-8'))
    files = [{'path': path.relative_to(ROOT).as_posix(), 'bytes': path.stat().st_size,
              'sha256': sha(path)} for folder in (OUT, Path(__file__).parent)
             for path in sorted(folder.rglob('*')) if path.is_file()]
    record = {'utc': datetime.now(timezone.utc).isoformat(), 'passed': True,
              'scope': 'Current review evidence bindings, not full predecessor preservation or scientific performance',
              'files': files, 'primary_http_requests': 2,
              'successful_body_bytes': sum(row['bytes'] for row in receipts),
              'new_direct_deepseek_calls': 0, 'biological_predictor_fits': 0,
              'new_biological_outcome_decodes': 0, 'scientific_experiments_rerun': 0,
              'native_usage_and_cost': 'NOT_EXPOSED', 'full_goal': 'ACTIVE / NOT_ACHIEVED'}
    with (OUT / 'FINAL_BINDINGS.json').open('x', encoding='utf-8') as handle:
        json.dump(record, handle, ensure_ascii=False, indent=2)
    print(json.dumps({'passed': True, 'files': len(files), 'scientific_success': False}))


if __name__ == '__main__':
    main()
