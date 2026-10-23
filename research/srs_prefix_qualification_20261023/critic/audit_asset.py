"""Check retained publisher provenance, without new network or values extraction."""
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[3]
source = root / 'log/20261023/srs_prefix_qualification/root'
out = root / 'log/20261023/srs_prefix_qualification/critic'
inventory = json.loads((source / 'FILE_INVENTORY.json').read_text())
raw = (source / 'publisher_supplement.pdf').read_bytes()
checks = []
for item in inventory['files']:
    record = json.loads((source / f"figshare_{item['article_id']}.json").read_text())
    checks.append(record['resource_doi'] == '10.1021/acs.analchem.5c04806')
    checks.append(any(x['identifier'] == record['resource_doi'] and x['relation'] == 'IsSupplementTo'
                      for x in record['related_materials']))
    checks.append(record['files'][0]['id'] == item['id'])
pdf = next(x for x in inventory['files'] if x['name'].endswith('.pdf'))
checks.extend([raw.startswith(b'%PDF'), len(raw) == pdf['size'],
               hashlib.md5(raw).hexdigest() == pdf['computed_md5']])
receipt = json.loads((source / 'publisher_supplement.pdf.receipt.json').read_text())
checks.append(hashlib.sha256(raw).hexdigest() == receipt['sha256'])
result = dict(checks=len(checks), passed=all(checks), pdf_bytes=len(raw),
              pdf_sha256=hashlib.sha256(raw).hexdigest(),
              metadata_records=len(inventory['files']), movies_downloaded=False,
              scope='Retained provenance identity checks only; no data qualification by checksum')
(out / 'ASSET_BINDING_AUDIT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
