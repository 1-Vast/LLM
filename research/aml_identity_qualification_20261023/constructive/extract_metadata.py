"""Local, metadata-only projection from already acquired official sources."""
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as ET

root = Path('D:/MAESTRO')
old = root / 'log/20261023/post_anchor_mechanism'
out = root / 'log/20261023/aml_identity_qualification/constructive'
out.mkdir(parents=True, exist_ok=True)
paths = [old/'root_sources/aml_samples.body', old/'constructive/hierarchical_primary.body',
         old/'root_sources/aml_gex.body', old/'root_sources/aml_lineage.body']
result = {'scope':'existing official sources; SOFT sample metadata only; Methods paragraphs only; no tables/matrix/function values',
          'sources':[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]}
samples=[]
current=None
for line_no,line in enumerate(paths[0].read_text(encoding='utf-8').splitlines(),1):
    if line.startswith('^SAMPLE = '):
        current={'gsm':line.split(' = ',1)[1], 'fields':[]}
        samples.append(current)
    if current and line.startswith(('!Sample_title =','!Sample_source_name_ch1 =','!Sample_characteristics_ch1 =',
                                    '!Sample_description =','!Sample_relation =','!Sample_supplementary_file')):
        current['fields'].append({'line':line_no,'text':line})
result['sample_fields']=samples
xml=ET.parse(paths[1]).getroot()
paras=[]
for sec in xml.findall('.//sec'):
    title=' '.join(sec.findtext('title','').split())
    if title.lower() not in ('methods','materials and methods'):
        continue
    for i,p in enumerate(sec.findall('.//p')):
        text=' '.join(''.join(p.itertext()).split())
        if re.search(r'MULTI.?seq|multiplex|demultiplex',text,re.I):
            paras.append({'method_paragraph_index':i,'text':text})
result['methods_multiplex_paragraphs']=paras
for p in paths[2:]:
    lines=p.read_text(encoding='utf-8').splitlines()
    result[p.name]=[{'line':i,'text':line} for i,line in enumerate(lines,1)
                    if re.search(r'MULTI|Antibody Capture|RS22|\$sample|names\(.*table\)|group.by.*flask',line)]
(out/'METADATA_EXTRACTION.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({'samples':len(samples),'methods_paragraphs':len(paras),'output':str(out/'METADATA_EXTRACTION.json')}))
