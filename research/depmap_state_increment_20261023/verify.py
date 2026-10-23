"""Verify the final bounded experiment's bytes and explicit independent audits."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'log/20261023/depmap_state_increment'


def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def verify_seal(p):
    obj=json.loads(p.read_text(encoding='utf-8'))
    if 'files' in obj:
        files=obj['files']
        if isinstance(files,dict):files=[dict(path=x,sha256=h) for x,h in files.items()]
    elif 'path' in obj and 'sha256' in obj:
        files=[dict(path=obj['path'],sha256=obj['sha256'])]
    else:
        raise ValueError(str(p))
    for row in files:
        file=Path(row['path'])
        if not file.is_absolute():
            file=(p.parent/file) if len(file.parts)==1 else ROOT/file
        assert digest(file)==row['sha256'],(str(p),str(file))
    return len(files)


if __name__=='__main__':
    target=OUT/'VERIFICATION.json';assert not target.exists()
    checked=[]
    prior=ROOT/'log/20261023/functional_source_bridge/VERIFICATION.json'
    for p in [prior,OUT/'FREEZE.json']:
        checked.append(dict(path=p.relative_to(ROOT).as_posix(),files=verify_seal(p)))
    for directory in ['methods','skeptic']:
        for p in sorted((OUT/directory).glob('*[Ss][Ee][Aa][Ll].json')):
            checked.append(dict(path=p.relative_to(ROOT).as_posix(),files=verify_seal(p)))
    assert (OUT/'RESULT.json').exists()
    result=json.loads((OUT/'RESULT.json').read_text())
    assert result['counters']['outer_fits']==22
    assert result['counters']['eigendecompositions']==528
    assert result['counters']['lambda_fits']==2640
    receipt=json.loads((OUT/'ACQUISITION_RECEIPT.json').read_text())
    assert digest(OUT/'pseudobulk.range')==receipt['sha256']
    identity=json.loads((OUT/'ACQUISITION.json').read_text())
    assert digest(OUT/'pseudobulk.csv')==identity['sha256']
    prep=json.loads((OUT/'methods/PREPARATION_AUDIT.json').read_text())
    numeric=json.loads((OUT/'skeptic/NUMERICAL_AUDIT.json').read_text())
    assert prep['status']=='PASS'
    assert numeric['status']=='PASS'
    files={p.relative_to(ROOT).as_posix():digest(p) for base in [OUT,ROOT/'research/depmap_state_increment_20261023']
           for p in sorted(base.rglob('*')) if p.is_file() and p!=target}
    target.write_text(json.dumps(dict(scope='fixed reconstruction experiment; not prospective efficacy or RSI',
        checked_seals=checked,files=files,decision=result['decision'],goal='ACTIVE / NOT_ACHIEVED'),indent=2),encoding='utf-8')
    assert all(digest(ROOT/p)==h for p,h in files.items())
    print(json.dumps(dict(files=len(files),drift=0,decision=result['decision'])))
