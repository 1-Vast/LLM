"""Bind this agent's source-qualification artifacts only."""
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'log/20261022/decrypte_feedback_pilot/molecular'
CODE=ROOT/'research/decrypte_molecular_source_20261022'
files=[]
for folder in (OUT,CODE):
    for path in sorted(folder.rglob('*')):
        if path.is_file() and path.name!='SEAL.json':
            raw=path.read_bytes()
            files.append({'path':path.relative_to(ROOT).as_posix(),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()})
(OUT/'SEAL.json').write_text(json.dumps({'scope':'molecular source qualification only, not global provenance','files':files},indent=2),encoding='utf-8')
print('Bound',len(files),'files')
