"""Outcome-blind sample and condition identity audit for exact S8/S7 members."""
from pathlib import Path
from io import BytesIO
from collections import Counter, defaultdict
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path('D:/MAESTRO')
OUT = ROOT / 'log/20261022/generative_repair_renewal/source/archive_followup'
NS = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
TAG = '{'+NS['s']+'}'

def workbook(member):
    with zipfile.ZipFile(OUT/'archive.body') as archive:
        return zipfile.ZipFile(BytesIO(archive.read(member)))

def config(archive):
    strings = ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('s:si',NS) if 'xl/sharedStrings.xml' in archive.namelist() else []
    rels = {item.attrib['Id']:item.attrib['Target'] for item in ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))}
    sheets = {}
    for item in ET.fromstring(archive.read('xl/workbook.xml')).findall('.//s:sheet',NS):
        target = rels[item.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
        sheets[item.attrib['name']] = target.lstrip('/') if target.startswith('/') else 'xl/'+target
    return strings, sheets

def value(cell,strings):
    assert cell.find('s:f',NS) is None, 'Unexpected metadata formula'
    if cell.attrib.get('t') == 's':
        return ''.join(item.text or '' for item in strings[int(cell.find('s:v',NS).text)].findall('.//s:t',NS))
    if cell.attrib.get('t') == 'inlineStr':
        return ''.join(item.text or '' for item in cell.findall('.//s:t',NS))
    node = cell.find('s:v',NS)
    return node.text if node is not None else ''

def identities(archive,sheet,allowed):
    strings,sheets = config(archive)
    rows = ET.fromstring(archive.read(sheets[sheet])).findall('.//s:row',NS)
    headers = {re.match(r'[A-Z]+',cell.attrib['r'])[0]:value(cell,strings) for cell in rows[0]}
    selected = {column:header for column,header in headers.items() if header in allowed}
    assert set(selected.values()) == set(allowed)
    result = []
    for row in rows[1:]:
        record = dict.fromkeys(allowed,'')
        for cell in row:
            column = re.match(r'[A-Z]+',cell.attrib['r'])[0]
            if column in selected:
                record[selected[column]] = value(cell,strings)
        if any(record.values()):
            result.append(record)
    return headers,result

with workbook('TableS8_PTPC_info_0703.xlsx') as archive:
    headers,rows = identities(archive,'A_metadata',['Sample_ID','Cell_line','Cell_plate','Pert_ID','Compound_name','Pert_time_(hrs)','Rep'])
    strings,sheets = config(archive)
    matrix_ids = []
    matrix_header = None
    with archive.open(sheets['C_protein_Matrix']) as stream:
        for event,row in ET.iterparse(stream,events=['end']):
            if row.tag != TAG+'row':
                continue
            first = next((cell for cell in row if re.match(r'[A-Z]+',cell.attrib.get('r',''))[0] == 'A'),None)
            if first is not None:
                identity = value(first,strings)
                if matrix_header is None:
                    matrix_header = identity
                elif identity:
                    matrix_ids.append(identity)
            row.clear()

with workbook('TableS7_PTNC-20260703final.xlsx') as archive:
    s7headers,s7rows = identities(archive,'B',['Cell_line','Pert_ID'])
    _,s7drugs = identities(archive,'A',['Pert_ID','Compound_name'])

old_source = ROOT/'research/dual_core_innovation_validation_20261021/CENSUS.json'
old_lineages = sorted(json.loads(old_source.read_text(encoding='utf-8'))['partition'])
normalize = lambda text: re.sub(r'[^A-Z0-9]','',text.upper())
new_lines = sorted(set(row['Cell_line'] for row in rows))
conditions = Counter((row['Cell_line'],row['Pert_ID'],row['Pert_time_(hrs)']) for row in rows)
sample_ids = [row['Sample_ID'] for row in rows]
by_line = {}
for line in new_lines:
    subset = [row for row in rows if row['Cell_line']==line]
    by_line[line] = dict(rows=len(subset),times=sorted(set(row['Pert_time_(hrs)'] for row in subset)),
                         rep_annotations=dict(Counter(row['Rep'] for row in subset)),
                         plate_ids=sorted(set(row['Cell_plate'] for row in subset)),
                         distinct_perturbation_ids=len(set(row['Pert_ID'] for row in subset)))
result = dict(scope='No Efficacy cells decoded, counted or compared; no protein abundance read',
              S8_headers=headers,S8_rows=len(rows),S8_cell_lines=new_lines,S8_by_line=by_line,
              S8_rep_annotations=dict(Counter(row['Rep'] for row in rows)),
              S8_duplicate_sample_ids=[key for key,count in Counter(sample_ids).items() if count>1],
              S8_repeated_line_pert_time_groups=sum(count>1 for count in conditions.values()),
              S8_matrix_first_column_header=matrix_header,S8_matrix_sample_ids=len(matrix_ids),
              S8_metadata_ids_equal_matrix_ids=set(sample_ids)==set(matrix_ids),
              S8_metadata_id_order_equal_matrix_order=sample_ids==matrix_ids,
              S7_B_headers=s7headers,S7_B_identity_rows=len(s7rows),
              S7_cell_lines=sorted(set(row['Cell_line'] for row in s7rows)),
              old_lineage_keys=old_lineages,old_identity_source=str(old_source.relative_to(ROOT)),
              old_identity_source_sha256=hashlib.sha256(old_source.read_bytes()).hexdigest(),
              S8_old_lineage_name_overlap=sorted(set(normalize(item) for item in new_lines)&set(normalize(item) for item in old_lineages)),
              S7_S8_cell_name_overlap=sorted(set(normalize(row['Cell_line']) for row in s7rows)&set(normalize(item) for item in new_lines)),
              paper_alias_mapping={'Panc 10.05':'Panc1005'})
(OUT/'S8_IDENTITY_ROWS.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'S7_IDENTITY_ROWS.json').write_text(json.dumps(dict(rows=s7rows,compounds=s7drugs),ensure_ascii=False,indent=2),encoding='utf-8')
(OUT/'IDENTITY_RESULT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
