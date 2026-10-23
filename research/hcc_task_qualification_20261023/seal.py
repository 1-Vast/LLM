"""Verify source receipts, original supplement identity and review seals."""
from datetime import datetime, timezone
import hashlib
import json
import re
from pathlib import Path
import zipfile
from pypdf import PdfReader
from attachment import ROOT, OUT


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


if __name__ == '__main__':
    target = OUT/'VERIFICATION.json'
    assert not target.exists()
    assert (OUT/'method/FINAL_SEAL.json').exists(), 'Wait for independent completion'
    seals = [ROOT/'log/20261023/inherited_update_renewal/VERIFICATION.json']
    seals += sorted((OUT/'method').glob('*SEAL.json'))
    checked = []
    for path in seals:
        payload = json.loads(path.read_text(encoding='utf-8'))
        files = payload['files']
        if isinstance(files, list):
            files = {row['path']: row['sha256'] for row in files}
        assert isinstance(files, dict) and files
        for name, expected in files.items():
            bound = Path(name)
            if not bound.is_absolute():
                bound = (path.parent if len(bound.parts) == 1 else ROOT)/bound
            assert digest(bound) == expected, (path, bound)
        checked.append({'seal': path.relative_to(ROOT).as_posix(), 'files': len(files)})
    receipt_bindings = [('ATTACHMENT_RECEIPT.json','mmc2.docx'),
                        ('CANONICAL_RECEIPT.json','mmc2_canonical.docx'),
                        ('EPMC_SUPP_RECEIPT.json','epmc_supplements.zip'),
                        ('epmc_fulltext.receipt.json','epmc_fulltext.xml')]
    for receipt_name, body_name in receipt_bindings:
        receipt = json.loads((OUT/receipt_name).read_text(encoding='utf-8'))
        body = OUT/body_name
        assert body.stat().st_size == receipt['bytes'] and digest(body) == receipt['sha256']
    for receipt in json.loads((OUT/'PUBLISHER_RECEIPTS.json').read_text(encoding='utf-8')):
        assert digest(OUT/(receipt['name']+'.html')) == receipt['sha256']
    expected = {'mmc1.pdf':'f4996291804515f2b114db71fd220c99',
                'mmc2.docx':'31b73eb3fd2aa42c679bb87fbac135c0',
                'mmc3.pdf':'c2516ecfb96c26bd6507e92f0aeffea4',
                'mmc4.pdf':'57332dc38c9a90d2a58294bd0ba84851'}
    xml = (OUT/'epmc_fulltext.xml').read_text(encoding='utf-8')
    for name, md5 in expected.items():
        pattern = r'<\?suppdata-name '+re.escape(name)+r'\?>.*?<\?suppdata-md5 ([a-f0-9]{32})\?>'
        match = re.search(pattern, xml, re.S)
        assert match and match.group(1) == md5, name
    with zipfile.ZipFile(OUT/'epmc_supplements.zip') as archive:
        names = archive.namelist()
        assert len(names) == 18 and not any(name.lower().endswith(('.xlsx','.xls','.csv')) for name in names)
        for name, md5 in expected.items():
            assert hashlib.md5(archive.read(name)).hexdigest() == md5
    for name in ['mmc1.pdf','mmc3.pdf','mmc4.pdf']:
        assert not list(PdfReader(OUT/name).attachments)
    audit = {'status':'PASS_SOURCE_SCOPE_ONLY','utc':datetime.now(timezone.utc).isoformat(),
             'seals':checked,'http_bodies_verified':6,'supplement_md5_verified':4,
             'archive_members':18,'response_workbook_present':False,
             'experiment_fits':0,'scope':'Local source/structure, not global data unavailability or biological verification'}
    (OUT/'AUDIT.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
    paths = sorted(path for base in [OUT,ROOT/'research/hcc_task_qualification_20261023']
                   for path in base.rglob('*') if path.is_file() and path != target)
    files = {path.relative_to(ROOT).as_posix():digest(path) for path in paths}
    target.write_text(json.dumps({'files':files,'scope':'HCC source qualification only'},indent=2),encoding='utf-8')
    assert all(digest(ROOT/name)==expected for name,expected in files.items())
    current = {path.relative_to(ROOT).as_posix() for base in [OUT,ROOT/'research/hcc_task_qualification_20261023']
               for path in base.rglob('*') if path.is_file() and path != target}
    assert current==set(files)
    print(json.dumps({'status':'SEALED_LOCAL','files':len(files),'drift':0,'unsealed':0}))
