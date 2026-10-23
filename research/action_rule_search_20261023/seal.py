"""Finalize immutable phase manifest after all reviews/audits are complete."""
import json
from audit import ROOT, OUT, digest

if __name__ == '__main__':
    target = OUT/'VERIFICATION.json'
    assert not target.exists(), 'Never replace finalized evidence'
    roots = [OUT, ROOT/'research/action_rule_search_20261023']
    paths = sorted(p for base in roots for p in base.rglob('*') if p.is_file() and p != target)
    files = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}
    target.write_text(json.dumps({'files': files, 'scope': 'Current phase only'}, indent=2), encoding='utf-8')
    assert all(digest(ROOT/p) == expected for p, expected in files.items())
    current = {p.relative_to(ROOT).as_posix() for base in roots for p in base.rglob('*')
               if p.is_file() and p != target}
    assert current == set(files)
    print(json.dumps({'status': 'SEALED_LOCAL', 'files': len(files), 'drift': 0, 'unsealed_files': 0}))
