"""Verify this phase's current frozen sources and bind its evidence, not old history."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/cdk_middle_feedback'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    target = OUT / 'FINAL_BINDINGS.json'
    assert not target.exists()
    freeze = json.loads((OUT / 'FREEZE_SPARSE_VALIDATED.json').read_text())
    checks = {name: sha(ROOT / name) == digest for name, digest in freeze['bindings'].items()}
    assert all(checks.values()), checks
    source = ROOT / 'log/20261022/next_mechanism/source/cdk_review/table_s3.body'
    assert sha(source) == '36903d770ff3bd3bc5fd62c6ee19d8106871c9735e8591c0e722da05cf146608'
    preparation = json.loads((OUT / 'PREPARATION.json').read_text())
    assert sha(OUT / 'prepared.npz') == preparation['prepared_sha256']
    paths = sorted(p for p in OUT.rglob('*') if p.is_file() and p != target)
    paths += sorted(p for p in Path(__file__).parent.rglob('*.py') if p.is_file())
    record = {'scope': 'Only this phase and explicitly verified S3/current source bindings; no global predecessor-preservation claim',
              'frozen_current_checks': checks, 'S3_source_sha256': sha(source),
              'prepared_hash_check': True,
              'bindings': {str(p.relative_to(ROOT)).replace('\\', '/'): sha(p) for p in paths}}
    target.write_text(json.dumps(record, indent=2), encoding='utf-8')
    print('Current frozen checks PASS:', len(checks), '; phase files bound:', len(paths))


if __name__ == '__main__':
    main()
