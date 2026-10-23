"""Bind the pre-outcome protocol, implementation, tests and authenticated inputs."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/cdk_functional_increment'
assert not (OUT / 'FREEZE.json').exists()
assert not (OUT / 'RESULT.json').exists()
paths = [OUT / 'PROTOCOL.md', OUT / 'SYNTHETIC_TESTS.txt',
         ROOT / 'log/20261022/cdk_middle_feedback/PREPARATION.json',
         ROOT / 'log/20261022/cdk_middle_feedback/prepared.npz',
         ROOT / 'log/20261022/next_mechanism/source/cdk_review/table_s4.body']
paths += [Path(__file__).parent / name for name in ('run.py', 'test_run.py', 'freeze.py')]
review = ROOT / 'log/20261022/revision_value_operation'
paths += [review / 'frontier/CODE_REVIEW.md', review / 'biology/CODE_REVIEW.md']
paths += sorted((review / 'biology').glob('CODE_REVIEW*ADDENDUM*.md'))
paths += [review / 'biology/S4_PROTOCOL_REVIEW.md', review / 'skeptic/S4_PROTOCOL_REVIEW.md']
payload = {'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
           'files': {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
(OUT / 'FREEZE.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
print('Bound', len(paths), 'pre-outcome inputs; no biological labels decoded')
