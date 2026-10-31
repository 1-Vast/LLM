"""Project explicitly allowed DNA design cells; never convert response cells."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re
import xml.etree.ElementTree as X
from zipfile import ZipFile

E = Path(__file__).resolve().parent.parent
SOURCE = E/'investigator/sources/promoter_library.xlsx'
ALLOWED = ['library index','subset','gene name','exonlength','exonstart in sequence',
           'exonend in sequence','changes','combination','first_ss','second_ss',
           'firstss','secondss','first_SF','second_SF','sequence']
NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'


def strings(archive, wanted):
    found = {}
    with archive.open('xl/sharedStrings.xml') as stream:
        index = 0
        for _,node in X.iterparse(stream,events=('end',)):
            if node.tag==NS+'si':
                if index in wanted:
                    found[index] = ''.join(t.text or '' for t in node.iter(NS+'t'))
                index += 1
                node.clear()
    assert set(found)==wanted
    return found


def raw_cell(cell):
    kind = cell.get('t','n')
    if kind=='inlineStr':
        return kind, ''.join(t.text or '' for t in cell.iter(NS+'t'))
    value = cell.find(NS+'v')
    return kind, value.text if value is not None else ''


def decode(cell, pool):
    kind,value = cell
    return pool[int(value)] if kind=='s' and value else value


with ZipFile(SOURCE) as archive:
    # The authenticated source workbook has exactly one table sheet.
    sheets = [n for n in archive.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',n)]
    assert len(sheets)==1, sheets
    with archive.open(sheets[0]) as stream:
        for _,node in X.iterparse(stream,events=('end',)):
            if node.tag==NS+'row':
                assert node.get('r')=='1'
                header_raw = {re.match('[A-Z]+',c.get('r')).group():raw_cell(c) for c in node}
                break
    pool = strings(archive,{int(v) for t,v in header_raw.values() if t=='s' and v})
    header = {col:decode(cell,pool) for col,cell in header_raw.items()}
    columns = {col:name for col,name in header.items() if name in ALLOWED}
    assert set(columns.values())==set(ALLOWED)
    raw_rows, wanted = [], set()
    with archive.open(sheets[0]) as stream:
        for _,node in X.iterparse(stream,events=('end',)):
            if node.tag!=NS+'row':
                continue
            if node.get('r')!='1':
                row = {}
                for cell in node:
                    col = re.match('[A-Z]+',cell.get('r')).group()
                    if col in columns:
                        value = raw_cell(cell)
                        row[columns[col]] = value
                        if value[0]=='s' and value[1]:
                            wanted.add(int(value[1]))
                if row:
                    raw_rows.append(row)
            node.clear()
    pool = strings(archive,wanted)
    rows = [{k:decode(row.get(k,('n','')),pool) for k in ALLOWED} for row in raw_rows]

target = E/'root/promoter_design_identities.tsv'
assert not target.exists()
with target.open('w',encoding='utf-8',newline='') as stream:
    writer = csv.DictWriter(stream,fieldnames=ALLOWED,delimiter='\t')
    writer.writeheader()
    writer.writerows(rows)
counts = lambda key:dict(Counter(r[key] for r in rows))
ids = counts('library index')
census = {
    'scope':'Original DNA design identity/sequence only; no response projection or processed isoform access',
    'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'contract_sha256':hashlib.sha256((E/'root/design_projection_contract.md').read_bytes()).hexdigest(),
    'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    'rows':len(rows),'unique_library_ids':len(ids),
    'duplicate_library_ids':{k:v for k,v in ids.items() if v>1},
    'unique_gene_labels':len(counts('gene name')),
    'subset_counts':counts('subset'),'sequence_lengths':dict(Counter(len(r['sequence']) for r in rows)),
    'first_ss_counts':counts('first_ss'),'second_ss_counts':counts('second_ss'),
    'firstss_counts':counts('firstss'),'secondss_counts':counts('secondss'),
    'first_SF_counts':counts('first_SF'),'second_SF_counts':counts('second_SF'),
    'changes_first_25_labels':list(counts('changes').items())[:25],
    'projected_fields':ALLOWED,
    'withheld_response_headers':[v for v in header.values() if v not in ALLOWED],
    'output_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),
    'wild_type_pairing_qualified':False,'observed_support_qualified':False,
}
out = E/'root/promoter_design_census.json'
assert not out.exists()
out.write_text(json.dumps(census,indent=2)+'\n',encoding='utf-8')
print(json.dumps(census))
