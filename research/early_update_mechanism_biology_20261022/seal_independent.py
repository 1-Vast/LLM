"""Seal independent biological mechanism hypothesis and literal primary evidence."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json

root=Path('D:/MAESTRO')
out=root/'log/20261022/early_update_mechanism/biology'
code=root/'research/early_update_mechanism_biology_20261022'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prose=json.loads((out/'decryptE_PROSE.json').read_text(encoding='utf-8'))
phrases=['treated for 18','only marginally affected','For determination of cell viability',
         'For confluency and metabolic activity evaluation','T Cell Activation Bioassay','MSV000093659',
         'strictly only considered sigmoidal','time, which might be different']
quotes=[]
for phrase in phrases:
    matches=[dict(paragraph_index=i,section=r['section'],text=r['text']) for i,r in enumerate(prose) if phrase in r['text']]
    assert matches, phrase
    quotes.append(dict(match=phrase,source='decryptE_PROSE.json',matches=matches))
state=json.loads((out/'state_epmc.body').read_text(encoding='utf-8'))['resultList']['result']
published=next(r for r in state if r.get('doi')=='10.1016/j.cell.2026.07.052')
quotes.append(dict(source='state_epmc.body',doi=published['doi'],first_publication=published['firstPublicationDate'],
                   access_boundary='Original published abstract/metadata only, full Methods not reviewed',text=published['abstractText']))
(out/'PRIMARY_QUOTES.json').write_text(json.dumps(quotes,ensure_ascii=False,indent=2),encoding='utf-8')
seal=out/'INDEPENDENT_SEAL.json'
assert not seal.exists()
paths=sorted(p for p in out.iterdir() if p.is_file() and p.name!=seal.name)+sorted(code.glob('*.py'))
record=dict(created_utc=datetime.now(timezone.utc).isoformat(),other_new_drafts_read=False,
            protected_biological_values_read=False, biological_data_downloads=0, experiment_run=False,
            publication_http_requests=4, original_draft=True,
            literature_boundary='decryptE OA primary prose; State2026 original abstract; decryptM2023 metadata background only',
            files=[dict(path=str(p.relative_to(root)),bytes=p.stat().st_size,sha256=sha(p)) for p in paths])
seal.write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(dict(files=len(paths),report_sha256=sha(out/'INDEPENDENT.md'),seal_sha256=sha(seal))))
