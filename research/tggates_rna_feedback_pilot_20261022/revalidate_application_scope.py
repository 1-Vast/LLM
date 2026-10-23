"""Bind existing primary dose-selection evidence to this pilot without new endpoint access."""
import hashlib,json
from pathlib import Path
import xml.etree.ElementTree as ET
from datetime import datetime,timezone
ROOT=Path(__file__).resolve().parents[2];P=ROOT/'log/20261022/tggates_rna_feedback_pilot'
source=ROOT/'log/20261022/tggates_source_qualification/PAPER.xml'
raw=source.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='1eab7724c09d40734848e0474c1884571d809cc3d9ee3dc36a042bac14930e84'
root=ET.fromstring(raw)
doi=[node.text for node in root.findall('.//article-id') if node.get('pub-id-type')=='doi']
assert doi==['10.1093/nar/gku955']
paragraphs=[]
for index,p in enumerate(root.findall('.//body//p')):
    text=''.join(p.itertext())
    if any(term in text for term in ['80–90% relative survival','Six lots of human hepatocytes',
                                       'will not reflect actual fold-changes']):
        paragraphs.append(dict(body_paragraph_index=index,text=text))
assert len(paragraphs)==3
record=dict(utc=datetime.now(timezone.utc).isoformat(),status='PREVIOUS_PRIMARY_EVIDENCE_REVALIDATED',
    source=source.relative_to(ROOT).as_posix(),source_sha256=hashlib.sha256(raw).hexdigest(),
    doi=doi[0],paragraphs=paragraphs,
    previous_decision='log/20261022/tggates_functional_qualification/DOSE_LINEAGE_REPORT.md',
    new_discovery=False,new_http_requests=0,new_assay_or_rna_values_accessed=0,
    authenticated='In-vitro highest dose selected for80–90%relative survival or limited by solubility.',
    unknown=['Prescreen assay','Prescreen time','Prescreen/released assay independence','Sample-to-lot/donor map'],
    forbidden_inference='Do not assign everyHigh target85% or infer current range/noise floor solely from dose selection.',
    task_scope='Conditional confirmation within a pre-screened continuous-exposure menu; not de-novo safe-dose discovery, '
               'clinical liver injury, same-cell trajectories, or donor transfer.',
    frozen_experiment_changed=False)
with (P/'APPLICATION_SCOPE_REVALIDATION.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2,ensure_ascii=False)
print(json.dumps({k:v for k,v in record.items() if k!='paragraphs'},ensure_ascii=False,indent=2))
