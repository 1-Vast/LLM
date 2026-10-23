"""Static, primary-source-only FM03 contract qualification; no count decoding."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import requests
from html.parser import HTMLParser
import zipfile
import xml.etree.ElementTree as ET
import re
import subprocess
import platform

ROOT = Path('D:/MAESTRO')
OUT = ROOT / 'log/20261022/next_mechanism/source'
OLD = ROOT / 'log/20261022/mechanism_gap'

def digest(body):
    return hashlib.sha256(body).hexdigest()

class TextBlocks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.blocks, self.links, self.stack = [], [], []
    def handle_starttag(self, tag, attrs):
        if tag in ['p', 'figcaption', 'a']:
            self.stack.append([tag, dict(attrs), []])
    def handle_data(self, data):
        for block in self.stack:
            block[2].append(data)
    def handle_endtag(self, tag):
        for i in range(len(self.stack)-1, -1, -1):
            if self.stack[i][0] == tag:
                name, attrs, parts = self.stack.pop(i)
                value = {'tag': name, 'id': attrs.get('id'), 'text': ' '.join(' '.join(parts).split())}
                if tag == 'a':
                    value['href'] = attrs.get('href', '')
                    self.links.append(value)
                else:
                    self.blocks.append(value)
                break

def extract_existing():
    path = OLD / 'functional/PMC10628994.pmc.html'
    body = path.read_bytes()
    parser = TextBlocks()
    parser.feed(body.decode('utf-8'))
    matches = [b for b in parser.blocks if any(term in b['text'].lower() for term in ['fm03', 'pinometostat', 'spike-in', 'fraction of', 'dot1l'])]
    links = [a for a in parser.links if any(t in (a['href'] + a['text']).lower() for t in ['supplement', 'moesm', '06342'])]
    metadata = json.loads((OLD/'functional/figshare_22806494.metadata.json').read_text())
    result = {'source': str(path), 'bytes': len(body), 'sha256': digest(body), 'matches': matches, 'links': links, 'figshare_metadata': metadata}
    (OUT/'EXISTING_PRIMARY_EXTRACT.json').write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding='utf-8')
    print(json.dumps({'matches': matches, 'links': links, 'figshare_description': metadata.get('description'), 'figshare_files': metadata.get('files')}, ensure_ascii=False, indent=2))

def fetch(url, stem):
    start = datetime.now(timezone.utc).isoformat()
    try:
        response = requests.get(url, timeout=60)
        body = response.content
        (OUT/(stem+'.body')).write_bytes(body)
        receipt = {'url': url, 'final_url': response.url, 'started_utc': start, 'status': response.status_code,
                   'body_bytes': len(body), 'sha256': digest(body), 'headers': dict(response.headers)}
    except Exception as exc:
        receipt = {'url': url, 'started_utc': start, 'error': repr(exc)}
    (OUT/(stem+'.receipt.json')).write_text(json.dumps(receipt, indent=2), encoding='utf-8')
    print(json.dumps(receipt, indent=2))

def extract_docx(stem):
    path = OUT/(stem+'.body')
    ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    with zipfile.ZipFile(path) as archive:
        xml = archive.read('word/document.xml')
        tree = ET.fromstring(xml)
        paragraphs = [''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in tree.findall('.//w:p',ns)]
        members = [{'name': i.filename, 'bytes':i.file_size} for i in archive.infolist()]
    result = {'file_sha256': digest(path.read_bytes()), 'xml_bytes':len(xml), 'members':members, 'paragraphs':paragraphs}
    (OUT/(stem+'.extract.json')).write_text(json.dumps(result, indent=2,ensure_ascii=False),encoding='utf-8')
    for i,p in enumerate(paragraphs):
        if any(t in p.lower() for t in ['fm03','spike','pinometostat','dot1','fraction','pretreat','pre-treat','gdna']):
            print(json.dumps({'paragraph':i,'previous':paragraphs[max(0,i-1)],'text':p,'next':paragraphs[min(len(paragraphs)-1,i+1)]}, ensure_ascii=False))

def extract_pdf(stem):
    from pypdf import PdfReader
    path = OUT/(stem+'.body')
    reader = PdfReader(path)
    pages = [{'page':i+1,'text':p.extract_text()} for i,p in enumerate(reader.pages)]
    (OUT/(stem+'.extract.json')).write_text(json.dumps({'sha256':digest(path.read_bytes()),'pages':pages},indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps({'pages':len(pages),'first_text':pages[0]['text'][:1800]},ensure_ascii=False))
    for page in pages:
        if any(t in page['text'].lower() for t in ['fm03','spike','pinometostat','dot1','fraction','pretreat','pre-treat','gdna']):
            print(json.dumps(page,ensure_ascii=False))

def inspect_table_metadata():
    path = OUT/'nature_supp_tables.body'
    ns = {'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(path) as archive:
        workbook = ET.fromstring(archive.read('xl/workbook.xml'))
        sheets = [s.attrib for s in workbook.findall('.//s:sheet',ns)]
        strings_xml = ET.fromstring(archive.read('xl/sharedStrings.xml'))
        strings = [''.join(x.text or '' for x in si.findall('.//s:t',ns)) for si in strings_xml.findall('s:si',ns)]
        matches = [{'index':i,'text':s} for i,s in enumerate(strings) if any(t in s.lower() for t in ['fm03','spike','dot1','fraction','pretreat','pre-treat','standard','naive','barcode'])]
        rel_ns = {'r':'http://schemas.openxmlformats.org/package/2006/relationships'}
        rels = ET.fromstring(archive.read('xl/_rels/workbook.xml.rels'))
        targets = {r.attrib['Id']:r.attrib['Target'] for r in rels.findall('r:Relationship',rel_ns)}
        selected = []
        for sheet in sheets:
            if sheet['name'] not in ['7_BarcodeClones','11_BarcodeCounts']:
                continue
            target = targets[sheet['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id']]
            sheet_xml = ET.fromstring(archive.read('xl/'+target))
            text_cells=[]
            for cell in sheet_xml.findall('.//s:c',ns):
                if cell.attrib.get('t') == 's':
                    text_cells.append({'cell':cell.attrib['r'],'text':strings[int(cell.find('s:v',ns).text)]})
            selected.append({'sheet':sheet['name'],'text_cells_only':text_cells})
        result = {'sha256':digest(path.read_bytes()),'sheets':sheets,'matching_text_only':matches,'selected':selected,
                  'scope':'Workbook structure and matched text, plus text cells in Table 7 standards and Table 11 sample annotations. Numeric cells were not decoded.'}
    (OUT/'TABLE_METADATA.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
    print(json.dumps(result,indent=2,ensure_ascii=False))

def verify_standard_identity():
    metadata = json.loads((OUT/'TABLE_METADATA.json').read_text(encoding='utf-8'))
    cells = {c['cell']:c['text'] for c in metadata['selected'][0]['text_cells_only']}
    code_path = OLD/'root/source_completion/pretreatment_code.body'
    code = code_path.read_text(encoding='utf-8')
    code_barcodes = {k:v for k,v in re.findall(r'(spikeBC[12])\s*=\s*"([ACGT]+)"',code)}
    complement = str.maketrans('ACGT','TGCA')
    checks = []
    for variable, row in [('spikeBC1','3'),('spikeBC2','4')]:
        sequence = cells['B'+row]
        checks.append({'variable':variable,'table_label':cells['A'+row], 'length':len(sequence),
                       'matches_reverse_complement':code_barcodes[variable] == sequence.translate(complement)[::-1]})
    result = {'table_sha256':metadata['sha256'],'code_sha256':digest(code_path.read_bytes()),'checks':checks,
              'scope':'Sequence identity only. No counts or calibration fitting.'}
    assert all(c['matches_reverse_complement'] for c in checks)
    (OUT/'STANDARD_IDENTITY.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))

def seal():
    paths = sorted(p for p in OUT.iterdir() if p.is_file() and p.name != 'INDEPENDENT_SEAL.json')
    paths.append(Path(__file__).resolve())
    result = {'created_utc':datetime.now(timezone.utc).isoformat(),
              'git_head':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
              'python':platform.python_version(),'decision':'STOP scoped longitudinal FM03 numerical route; full goal active',
              'files':[{'path':str(p.relative_to(ROOT)),'bytes':p.stat().st_size,'sha256':digest(p.read_bytes())} for p in paths]}
    (OUT/'INDEPENDENT_SEAL.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'files':len(paths),'git_head':result['git_head'],'report_sha256':digest((OUT/'INDEPENDENT.md').read_bytes())},indent=2))

if __name__ == '__main__':
    import sys
    if len(sys.argv) == 1:
        extract_existing()
    elif sys.argv[1] == 'docx':
        extract_docx(sys.argv[2])
    elif sys.argv[1] == 'pdf':
        extract_pdf(sys.argv[2])
    elif sys.argv[1] == 'tables':
        inspect_table_metadata()
    elif sys.argv[1] == 'standards':
        verify_standard_identity()
    elif sys.argv[1] == 'seal':
        seal()
    else:
        fetch(sys.argv[1], sys.argv[2])
