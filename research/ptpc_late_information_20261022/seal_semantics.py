"""Seal source-only PTPC definition review; do not open scientific values."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

root=Path('D:/MAESTRO')
out=root/'log/20261022/ptpc_late_information/source'
code=root/'research/ptpc_late_information_20261022'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
# Correct the extraction metadata's original heading/substr naming before seal.
evidence_path=out/'TEXT_EVIDENCE.json'
evidence=json.loads(evidence_path.read_text(encoding='utf-8'))
for item in evidence['evidence']:
    if 'contains_Methods_heading' in item:
        item['contains_literal_Methods_substring']=item.pop('contains_Methods_heading')
evidence_path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2),encoding='utf-8')
paths=sorted(p for p in out.iterdir() if p.is_file() and p.name!='SEAL.json')+sorted(code.glob('*.py'))
sources=[root/p for p in ('tmp/ptv1_src/si.txt','tmp/ptv1_src/art.txt','tmp/ptv1_src/art.html',
    'log/20261022/generative_repair_renewal/source/archive_followup/S8_ANNOTATION_METADATA.json',
    'log/20261022/generative_repair_renewal/source/archive_followup/S8_HEADERS.json',
    'log/20261022/generative_repair_renewal/source/archive_followup/SEAL.json')]
seal=out/'SEAL.json'
assert not seal.exists()
seal.write_text(json.dumps(dict(created_utc=datetime.now(timezone.utc).isoformat(),
    scope='Source-only S8/PTPC author-Efficacy experimental definition; no new outcomes or protein values',
    metadata_requests=2, public_fulltext_location_found=False,
    extraction_metadata_correction='Methods-heading Boolean renamed to literal substring presence; reference names are not a Methods section; no request repeated',
    files=[dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=sha(p)) for p in paths],
    original_sources=[dict(path=str(p.relative_to(root)),sha256=sha(p)) for p in sources]),indent=2),encoding='utf-8')
print(json.dumps(dict(files=len(paths),report_sha256=sha(out/'EFFICACY_DEFINITION_RESULT.md'),seal_sha256=sha(seal))))
