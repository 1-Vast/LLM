"""Check old seals, receipts and the limited identity conclusion; seal this phase."""
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/hcc_link_recovery'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_seal(path):
    obj = json.loads(path.read_text(encoding='utf-8'))
    if 'report' in obj:
        assert digest(Path(obj['report'])) == obj['sha256']
        return 1
    if 'correction_sha256' in obj:
        assert digest(path.parent/'INDEPENDENT.md') == obj['original_sha256']
        assert digest(path.parent/'CORRECTION.md') == obj['correction_sha256']
        return 2
    files = obj['files']
    if isinstance(files, list):
        files = {x['path']:x['sha256'] for x in files}
    for name, expected in files.items():
        p = Path(name)
        if not p.is_absolute():
            p = ROOT/p
        assert digest(p) == expected, str(p)
    return len(files)


if __name__ == '__main__':
    target = OUT/'VERIFICATION.json'
    assert not target.exists()
    seals = [ROOT/'log/20261023/hcc_task_qualification/VERIFICATION.json']
    seals += sorted(OUT.glob('agent/*SEAL.json'))
    seals += sorted(OUT.glob('opportunity/*SEAL.json'))
    assert (OUT/'opportunity/CORRECTION.md').exists()
    checked = [{'path':str(p.relative_to(ROOT)), 'files':verify_seal(p)} for p in seals]
    receipt_count = 0
    for p in OUT.rglob('*.receipt.json'):
        obj = json.loads(p.read_text(encoding='utf-8'))
        # Agent receipts may use their own body filename conventions.
        candidates = [p.with_name(p.name.replace('.receipt.json','')),
                      p.with_name(p.name.replace('.receipt.json','.body'))]
        body = next((x for x in candidates if x.exists()),None)
        assert body is not None, str(p)
        assert digest(body) == obj['sha256'], str(p)
        assert body.stat().st_size == obj['bytes'], str(p)
        receipt_count += 1
    assert receipt_count == 11, receipt_count
    record = json.loads((OUT/'biostudies_record.json').read_text())
    assert record['accno']=='S-EPMC12205652'
    assert len(record['section']['files']) == 4
    assert not any(x['path'].endswith(('.xlsx','.xls','.csv')) for x in record['section']['files'])
    with ZipFile(OUT/'biostudies_mmc2.docx') as z:
        t = ET.fromstring(z.read('word/document.xml'))
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
        first = ''.join(t.find('.//w:p',ns).itertext())
        assert first == 'Table S2. PRDEGs in the PPI network ranked with the MCC method'
    audit = dict(scope='local source identity and unchanged seals only', prior_seals=checked,
                 retained_http_bodies=receipt_count, biological_fits=0,
                 mismatch_independently_reproduced=True, goal='ACTIVE / NOT_ACHIEVED')
    (OUT/'AUDIT.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    bases = [OUT, ROOT/'research/hcc_link_recovery_20261023']
    files = {str(p.relative_to(ROOT)).replace('\\','/'):digest(p)
             for b in bases for p in sorted(b.rglob('*')) if p.is_file() and p!=target}
    target.write_text(json.dumps(dict(files=files,scope=audit['scope']),indent=2),encoding='utf-8')
    assert all(digest(ROOT/p)==h for p,h in files.items())
    print(json.dumps(dict(files=len(files),drift=0,retained_http_bodies=receipt_count)))
