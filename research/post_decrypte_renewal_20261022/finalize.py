"""Scoped source/design verification and evidence bindings for this renewal."""
import json
import hashlib
from pathlib import Path
from datetime import datetime,timezone

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/post_decrypte_renewal'


def sha(path):
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        while block := handle.read(1024*1024):
            digest.update(block)
    return digest.hexdigest()


def main():
    assert not (OUT/'FINAL_BINDINGS.json').exists()
    archive = OUT/'root/almanac_archive'
    receipts = json.loads((archive/'RECEIPTS.json').read_text(encoding='utf-8'))
    assert len(receipts)==2 and all(r['status']==200 and not r.get('error') for r in receipts)
    assert sha(archive/'archive.zip') == receipts[1]['sha256']
    design = json.loads((archive/'DESIGN.json').read_text(encoding='utf-8'))
    assert not set(design['selected_columns']) & set(design['forbidden_columns'])
    assert design['rows']==3686475 and design['cell_count']==60
    join = json.loads((archive/'JOIN.json').read_text(encoding='utf-8'))
    assert join['categories']['all_solos_unique']==300091
    rows = json.loads((archive/'ELIGIBLE_DESIGN_ROWS.json').read_text(encoding='utf-8'))
    assert len(rows)==300091
    for row in rows:
        assert len(row['combination_rows'])==len(set(row['combination_rows']))==9
        assert len(row['single_agent_rows'])==len(set(row['single_agent_rows']))==6
        assert not set(row['combination_rows']) & set(row['single_agent_rows'])
        assert all(2<=i<=3686476 for i in row['combination_rows']+row['single_agent_rows'])
    overlap = json.loads((archive/'LAB_PAIR_OVERLAP.json').read_text(encoding='utf-8'))
    assert overlap['nsc_pair_overlap_FF_FG']==overlap['sample_pair_overlap_FF_FG']==0
    for name in ('root/INDEPENDENT.md','skeptic/INDEPENDENT.md','assay/INDEPENDENT.md',
                 'skeptic/CROSS.md','assay/CROSS.md','assay/ALMANAC_SCOPE.md','assay/ALMANAC_SCOPE_ADDENDUM.md'):
        assert (OUT/name).exists()
    verification = {'utc':datetime.now(timezone.utc).isoformat(),'status':'PASS',
        'archive_sha256_verified':True,'all300091design_row_sets_valid':True,
        'scope':'Scoped receipt/hash/design consistency, not independent raw row reconstruction or response evaluation',
        'objective':'ACTIVE_NOT_ACHIEVED'}
    (OUT/'VERIFICATION.json').write_text(json.dumps(verification,indent=2),encoding='utf-8')
    paths = [p for p in OUT.rglob('*') if p.is_file()]
    paths += list((ROOT/'research/post_decrypte_renewal_20261022').glob('*.py'))
    paths += list((ROOT/'research/post_decrypte_renewal_assay_20261022').glob('*.py'))
    paths += list((ROOT/'research/post_decrypte_renewal_skeptic_20261022').glob('*.py'))
    final = {'utc':verification['utc'],'scope':verification['scope'],
             'files':{p.relative_to(ROOT).as_posix():sha(p) for p in sorted(set(paths))}}
    (OUT/'FINAL_BINDINGS.json').write_text(json.dumps(final,indent=2),encoding='utf-8')
    assert all(sha(ROOT/p)==h for p,h in final['files'].items())
    print(json.dumps({'bound_files':len(final['files']),'verification':'PASS'}))


if __name__ == '__main__':
    main()
