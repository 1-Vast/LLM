"""Verify release checksums and inspect textual schema without casting assay values."""
import hashlib,io,json,zipfile
import xml.etree.ElementTree as ET
from fetch_sources import P
NS={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}

def main():
    manifest=json.loads((P/'SMALL_ASSET_MANIFEST.json').read_text());rows=[]
    for source in manifest['files']:
        raw=(P/(source['name']+'.body')).read_bytes()
        checksum='md5:'+hashlib.md5(raw).hexdigest()
        assert len(raw)==source['size'] and checksum==source['checksum'],source['name']
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names=z.namelist();strings=[]
            if 'xl/sharedStrings.xml' in names:
                strings=[''.join(e.itertext()) for e in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('s:si',NS)]
            workbook=ET.fromstring(z.read('xl/workbook.xml'))
            sheets=[e.attrib for e in workbook.findall('s:sheets/s:sheet',NS)]
            tabs=[]
            for name in sorted(n for n in names if n.startswith('xl/worksheets/sheet') and n.endswith('.xml')):
                tree=ET.fromstring(z.read(name));labels=[];numeric_cells=0;formulas=0
                for cell in tree.findall('.//s:sheetData/s:row/s:c',NS):
                    kind=cell.attrib.get('t');value=cell.find('s:v',NS)
                    if kind=='s' and value is not None:labels.append(dict(cell=cell.attrib['r'],text=strings[int(value.text)]))
                    elif kind=='inlineStr':labels.append(dict(cell=cell.attrib['r'],text=''.join(cell.find('s:is',NS).itertext())))
                    elif value is not None:numeric_cells+=1
                    formulas+=cell.find('s:f',NS) is not None
                dimension=tree.find('s:dimension',NS)
                tabs.append(dict(member=name,dimension=dimension.attrib.get('ref') if dimension is not None else None,text_cells=labels,numeric_cell_tags_counted_not_values_cast=numeric_cells,formula_cells=formulas))
        rows.append(dict(name=source['name'],release_key=source['key'],bytes=len(raw),verified_checksum=checksum,sheets=sheets,tabs=tabs))
    result=dict(files=rows,assay_scalar_casts=0,normalization_values_not_inspected=True,raw_outcomes_downloaded_but_not_numerically_converted=True)
    with (P/'WORKBOOK_SCHEMA_AUDIT.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
