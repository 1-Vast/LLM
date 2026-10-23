"""Repair numbered-field metadata projection locally, without another request."""
import json
from pathlib import Path

OUT=Path(__file__).resolve().parents[2]/'log/20261023/post_anchor_mechanism/root_sources'
samples=[]
for line in (OUT/'aml_samples.body').read_text(encoding='utf-8').splitlines():
    if line.startswith('^SAMPLE = '):samples.append(dict(id=line.split(' = ',1)[1],title=None,files=[]))
    elif samples and line.startswith('!Sample_title = '):samples[-1]['title']=line.split(' = ',1)[1]
    elif samples and line.startswith('!Sample_supplementary_file'):
        samples[-1]['files'].append(line.split(' = ',1)[1])
record=dict(samples=samples,scope='official sample identities and declared file URLs only; no payload request',
    correction='Initial projection matched unnumbered supplementary_file only; this includes numbered fields from existing body.')
(OUT/'AML_SAMPLE_INDEX.json').write_text(json.dumps(record,indent=2),encoding='utf-8')
print(json.dumps(record,indent=2))
