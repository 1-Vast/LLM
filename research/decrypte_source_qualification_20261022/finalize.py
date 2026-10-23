"""Bind only this phase and its declared archived article, not global history."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/decrypte_source_qualification'
CODE = ROOT / 'research/decrypte_source_qualification_20261022'


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as source:
        while block := source.read(1024 * 1024):
            result.update(block)
    return result.hexdigest()


def main():
    checked = []
    for seal in sorted(OUT.rglob('*.json')):
        if 'seal' not in seal.name.lower():
            continue
        record = json.loads(seal.read_text(encoding='utf-8-sig'))
        path = record.get('path', record.get('file'))
        if isinstance(path, str) and isinstance(record.get('sha256'), str):
            actual = digest(ROOT / path)
            assert actual == record['sha256'], str(seal)
            checked.append(str(seal.relative_to(ROOT)))
    receipt = json.loads((OUT / 'SUPPLEMENT_MEDIA_LARGE_RECEIPT.json').read_text())
    assert digest(OUT / 'supplement.xlsx') == receipt['sha256']
    identities = json.loads((OUT / 'IDENTITIES.json').read_text(encoding='utf-8'))
    jurkat = [r for r in identities['rows'] if r['cell'] == 'Jurkat']
    assert len(jurkat) == 432
    by_drug = {}
    for row in jurkat:
        by_drug.setdefault(row['drug'], set()).add(row['assay'])
    assert len(by_drug) == 144
    assert all(a == {'Confluency', 'Cytotoxicity', 'Metabolic activity'} for a in by_drug.values())
    files = [p for directory in (OUT, CODE) for p in directory.rglob('*')
             if p.is_file() and p.name != 'FINAL_BINDINGS.json']
    files.append(ROOT / 'log/20261022/early_update_mechanism/biology/decryptE_fulltext.xml')
    bindings = {str(p.relative_to(ROOT)).replace('\\', '/'): {'bytes': p.stat().st_size, 'sha256': digest(p)} for p in sorted(files)}
    (OUT / 'FINAL_BINDINGS.json').write_text(json.dumps({'scope': 'This phase plus declared article only; no historical integrity claim',
        'verified_review_seals': checked, 'functional_numeric_analysis': False, 'files': bindings}, indent=2), encoding='utf-8')
    print(json.dumps({'bound_files': len(bindings), 'verified_review_seals': len(checked),
                      'jurkat_drugs_with_three_assays': len(by_drug), 'status': 'PASS'}))


if __name__ == '__main__':
    main()
