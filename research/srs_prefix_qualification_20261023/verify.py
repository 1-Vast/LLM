"""Local source binding checks; not biological or predictive validation."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'log/20261023/srs_prefix_qualification'
checks = []


def check(name, passed):
    checks.append({'name': name, 'passed': bool(passed)})


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


previous = ROOT / 'log/20261023/grounded_feedback_renewal/VERIFICATION.json'
for relative, sha in json.loads(previous.read_text(encoding='utf-8'))['files'].items():
    path = ROOT / relative
    check('predecessor:' + relative, path.exists() and digest(path) == sha)

receipts = sorted((BASE / 'root').glob('*.receipt.json'))
check('13 logical GET receipts', len(receipts) == 13)
for path in receipts:
    rec = json.loads(path.read_text(encoding='utf-8'))
    body = path.with_name(path.name.removesuffix('.receipt.json'))
    check('receipt:' + body.name, body.exists() and digest(body) == rec['sha256']
          and body.stat().st_size == rec['bytes'])

pdf = BASE / 'root/publisher_supplement.pdf'
check('publisher PDF SHA', digest(pdf) == '0026fbdb7be9d6a00e8d90c9ac78e6c9703ed7a7fd70e1319830f82096ac2dc1')
check('publisher MD5', hashlib.md5(pdf.read_bytes()).hexdigest() == '89ea396e82f21d29f79f3e82eede99cf')
reader = PdfReader(pdf)
check('ten pages and no attachments', len(reader.pages) == 10 and not reader.attachments)
for n in range(1, 11):
    page = BASE / f'root/render/page-{n:02d}.png'
    check(f'page {n} rendered', page.exists() and page.read_bytes().startswith(b'\x89PNG'))

inventory = json.loads((BASE / 'root/FILE_INVENTORY.json').read_text(encoding='utf-8'))
check('inventory one PDF eight movies', inventory['file_count'] == 9 and inventory['pdfs'] == 1 and inventory['mp4s'] == 8)
for item in inventory['files']:
    detail = json.loads((BASE / f"root/figshare_{item['article_id']}.json").read_text(encoding='utf-8'))
    check(f"parent DOI {item['article_id']}", detail['resource_doi'] == '10.1021/acs.analchem.5c04806')

for role in ['constructive', 'critic']:
    for path in (BASE / role).glob('*SEAL.json'):
        seal = json.loads(path.read_text(encoding='utf-8'))
        if 'path' in seal and 'sha256' in seal:
            target = Path(seal['path'])
            check('seal:' + str(path.relative_to(BASE)), target.exists() and digest(target) == seal['sha256'])

files = sorted(p for directory in [BASE, ROOT / 'research/srs_prefix_qualification_20261023']
               for p in directory.rglob('*') if p.is_file() and p.name != 'VERIFICATION.json'
               and '__pycache__' not in p.parts)
report = {'utc': datetime.now(timezone.utc).isoformat(),
          'scope': 'Local source/file consistency only; not scientific validity, blindness or model performance',
          'checks': checks, 'failures': sum(not x['passed'] for x in checks),
          'files': {str(p.relative_to(ROOT)): digest(p) for p in files}}
(BASE / 'VERIFICATION.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps({'checks': len(checks), 'failures': report['failures'], 'files': len(files)}))
raise SystemExit(bool(report['failures']))
