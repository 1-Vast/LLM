"""Seal and verify the completed phase's code/evidence; no assay reads."""
import json
from pathlib import Path
from audit import ROOT, OUT, digest

if __name__ == '__main__':
    target = OUT / 'VERIFICATION.json'
    assert not target.exists(), 'Do not replace an existing final seal'
    roots = [OUT, ROOT / 'research/observation_law_search_20261023']
    paths = sorted(p for base in roots for p in base.rglob('*') if p.is_file() and p != target)
    files = {p.relative_to(ROOT).as_posix(): digest(p) for p in paths}
    target.write_text(json.dumps({'files': files, 'scope': 'This phase only; not global provenance repair'},
                                 indent=2), encoding='utf-8')
    for relative, expected in files.items():
        assert digest(ROOT / relative) == expected
    current = {p.relative_to(ROOT).as_posix() for base in roots for p in base.rglob('*')
               if p.is_file() and p != target}
    assert current == set(files)
    print(json.dumps({'status': 'SEALED_LOCAL', 'files': len(files), 'drift': 0, 'unsealed_files': 0}))
