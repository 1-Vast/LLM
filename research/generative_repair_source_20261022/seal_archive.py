"""Seal identity-only archive qualification and verify prior independent evidence."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root = Path('D:/MAESTRO')
source = root/'log/20261022/generative_repair_renewal/source'
out = source/'archive_followup'
digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
prior = json.loads((source/'INDEPENDENT_SEAL.json').read_text(encoding='utf-8'))
verification = [dict(path=item['path'],unchanged=digest(root/item['path'])==item['sha256']) for item in prior['files']]
assert len(verification)==9 and all(item['unchanged'] for item in verification)
prior_paths = {item['path'].replace('\\','/') for item in prior['files']}
paths = sorted(path for path in out.iterdir() if path.is_file() and path.name!='SEAL.json')
paths += [source/'INDEPENDENT_SEAL.json']
paths += [path for path in sorted((root/'research/generative_repair_source_20261022').glob('*.py'))
          if str(path.relative_to(root)).replace('\\','/') not in prior_paths]
record = dict(created_utc=datetime.now(timezone.utc).isoformat(),
              prior_verification=verification, numerical_outcomes_opened=False,
              scope='Metadata/header/identity-only new PTPC qualification; no phenotype or protein quantities',
              files=[dict(path=str(path.relative_to(root)),bytes=path.stat().st_size,sha256=digest(path)) for path in paths])
(out/'SEAL.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(dict(files=len(paths),prior_unchanged=len(verification),report_sha256=digest(out/'RESULT.md'))))
