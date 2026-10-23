"""Bounded CDK primary metadata/header qualification, never response decoding."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import re
import requests
import zipfile
import xml.etree.ElementTree as ET

ROOT=Path('D:/MAESTRO')
OUT=ROOT/'log/20261022/next_mechanism/source/cdk_review'
def sha(b): return hashlib.sha256(b).hexdigest()
def safe_header(text):
    if re.fullmatch('[ACGTN]{20,}',text.strip()): return '[DNA barcode suppressed]'
    if re.fullmatch(r'[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][-+]?\d+)?',text.strip()): return '[numeric text suppressed]'
    return text
def fetch(kind):
    specs={'zenodo':('https://zenodo.org/api/records/20414461',2_000_000),
           'table_s3':('https://media.springernature.com/original/springer-static/esm/art%3A10.1186%2Fs13073-026-01690-2/MediaObjects/13073_2026_1690_MOESM4_ESM.xlsx',80_000_000)}
    url,limit=specs[kind]
    receipt={'url':url,'limit':limit,'started_utc':datetime.now(timezone.utc).isoformat()}
    chunks=[]
    try:
        with requests.get(url,timeout=90,stream=True) as response:
            receipt.update(status=response.status_code,final_url=response.url,headers=dict(response.headers))
            size=0
            for chunk in response.iter_content(1024*1024):
                size+=len(chunk)
                if size>limit: raise RuntimeError('Body bound exceeded')
                chunks.append(chunk)
        body=b''.join(chunks)
        (OUT/(kind+'.body')).write_bytes(body)
        receipt.update(bytes=len(body),sha256=sha(body))
        if kind=='zenodo' and receipt['status']==200:
            obj=json.loads(body)
            selected={key:obj.get(key) for key in ['id','doi','metadata','files','links']}
            (OUT/'ZENODO_METADATA.json').write_text(json.dumps(selected,indent=2),encoding='utf-8')
    except Exception as exc:
        receipt['error']=repr(exc)
    (OUT/(kind+'.receipt.json')).write_text(json.dumps(receipt,indent=2),encoding='utf-8')
    print(json.dumps(receipt,indent=2))

def headers():
    ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    main='{'+ns['s']+'}'
    with zipfile.ZipFile(OUT/'table_s3.body') as archive:
        wb=ET.fromstring(archive.read('xl/workbook.xml'))
        rels=ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets={r.attrib['Id']:r.attrib['Target'] for r in rels}
        sheets=[]
        wanted=set()
        for sheet in wb.findall('.//s:sheet',ns):
            target=targets[sheet.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            target=target.lstrip('/') if target.startswith('/') else 'xl/'+target
            info={'name':sheet.attrib['name'],'member':target,'header_cells':[]}
            rows=0
            with archive.open(target) as source:
                for event,node in ET.iterparse(source,events=('end',)):
                    if node.tag==main+'row':
                        rows+=1
                        for cell in list(node)[:100]:
                            entry={'row':node.attrib.get('r'),'cell':cell.attrib.get('r')}
                            if cell.attrib.get('t')=='s':
                                idx=int(cell.find('s:v',ns).text)
                                entry['shared_string_index']=idx
                                wanted.add(idx)
                            elif cell.attrib.get('t')=='inlineStr':
                                entry['text']=safe_header(''.join(t.text or '' for t in cell.findall('.//s:t',ns)))
                            else:
                                entry['numeric_or_other_suppressed']=True
                            info['header_cells'].append(entry)
                        node.clear()
                        if rows==2: break
            sheets.append(info)
        resolved={}
        with archive.open('xl/sharedStrings.xml') as source:
            index=0
            for event,node in ET.iterparse(source,events=('end',)):
                if node.tag==main+'si':
                    if index in wanted:
                        text=''.join(t.text or '' for t in node.findall('.//s:t',ns))
                        resolved[index]=safe_header(text)
                    node.clear()
                    index+=1
                    if len(resolved)==len(wanted): break
        for sheet in sheets:
            for cell in sheet['header_cells']:
                if 'shared_string_index' in cell:
                    cell['text']=resolved[cell['shared_string_index']]
        body=(OUT/'table_s3.body').read_bytes()
        result={'scope':'First two rows and at most 100 cells per row; numeric values never decoded.',
                'workbook_sha256':sha(body),'workbook_md5':hashlib.md5(body).hexdigest(),
                'matches_primary_declared_md5':hashlib.md5(body).hexdigest()=='8aa7941c019dde721b274146526b1a8c','sheets':sheets}
    (OUT/'TABLE_S3_HEADERS.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

def source_excerpts():
    path=ROOT/'log/20261022/next_mechanism/root/literature/cdk_epmc.xml'
    body=path.read_bytes()
    tree=ET.fromstring(body)
    titles=['Cell lines','Growth assays','Barcodes sequencing','Single cell-RNA sequencing (scRNA-seq)',
            'Cellular population-level analyses','Barcode-level analyses']
    sections=[]
    for section in tree.findall('.//sec'):
        title=section.find('title')
        name=''.join(title.itertext()) if title is not None else ''
        if name in titles:
            sections.append({'title':name,'id':section.attrib.get('id'),
                             'paragraphs':[{'id':p.attrib.get('id'),'text':''.join(p.itertext())} for p in section.findall('p')]})
    limitation=[{'id':p.attrib.get('id'),'text':''.join(p.itertext())} for p in tree.findall('.//p')
                if 'barcodes in the ClonTracer library are not expressed' in ''.join(p.itertext())]
    record={'source_path':str(path.relative_to(ROOT)),'source_bytes':len(body),'sha256':sha(body),
            'sections':sections,'nonexpressed_limitation':limitation}
    (OUT/'SOURCE_EXCERPTS.json').write_text(json.dumps(record,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'sections':[s['title'] for s in sections],'paragraph_ids':[p['id'] for s in sections for p in s['paragraphs']],
                      'limitation_ids':[p['id'] for p in limitation]},indent=2))

def sample_contract():
    headers=json.loads((OUT/'TABLE_S3_HEADERS.json').read_text())
    entries=[]
    for sheet in headers['sheets']:
        if sheet['name'] not in ['Barcodes_Palbo_study','Barcodes_Abema_study']: continue
        drug='Palbo' if 'Palbo_' in sheet['name'] else 'Abema'
        cells={c.get('text'):c['cell'] for c in sheet['header_cells'] if c['row']=='1' and 'text' in c}
        for genotype in ['WT','Mut']:
            for treatment in ['Veh',drug]:
                for stage in ['Early','Middle','Late' if treatment=='Veh' else 'Late_Resistant']:
                    for replicate in [1,2,3]:
                        sample=f'{genotype}_{treatment}_{stage}_{replicate}'
                        assert sample+'_Count' in cells and sample+'_Fraction' in cells, sample
                        entries.append({'sheet':sheet['name'],'selection_family':drug,'genotype_label':genotype,
                                        'treatment_label':treatment,'stage_label':stage,'evolutionary_replicate':replicate,
                                        'sample_label':sample,'count_column':cells[sample+'_Count'],'fraction_column':cells[sample+'_Fraction']})
    result={'scope':'Header-only sample bindings; no outcomes read.', 'matches_primary_declared_md5':headers['matches_primary_declared_md5'],
            'bindings':entries,'n_sample_bindings':len(entries),
            'notes':['Veh sample labels recur across the two study worksheets; worksheet/selection-family is part of the key.',
                     'Palbo parent headers specify passage_3 and Abema parent header passage_10; do not silently identify these samples.',
                     'Count fields are sequencing quantities, not authenticated absolute live-cell counts.']}
    (OUT/'SAMPLE_HEADER_CONTRACT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'sample_bindings':len(entries),'all_expected_labels_present':True,'md5_matches':headers['matches_primary_declared_md5']}))

if __name__=='__main__':
    import sys
    if sys.argv[1]=='headers': headers()
    elif sys.argv[1]=='source': source_excerpts()
    elif sys.argv[1]=='contract': sample_contract()
    else: fetch(sys.argv[1])
