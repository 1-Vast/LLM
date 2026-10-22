"""Read authentic supplement text and sample-table headers; no assay conversion."""
import hashlib,io,json,re,zipfile
from pathlib import Path
import xml.etree.ElementTree as ET
import openpyxl
from fetch_primary import P

def main():
    raw=(P/'caf_rest_supplementary_bundle.body').read_bytes()
    assert zipfile.is_zipfile(io.BytesIO(raw))
    with zipfile.ZipFile(io.BytesIO(raw)) as bundle:
        names=bundle.namelist();inventory=[dict(name=z.filename,bytes=z.file_size,compressed=z.compress_size) for z in bundle.infolist()]
        docname=next(n for n in names if n.endswith('41392_2026_2965_MOESM1_ESM.docx'))
        tabname=next(n for n in names if n.endswith('41392_2026_2965_MOESM2_ESM.xlsx'))
        docraw=bundle.read(docname);tabraw=bundle.read(tabname)
    with zipfile.ZipFile(io.BytesIO(docraw)) as doc:
        tree=ET.fromstring(doc.read('word/document.xml'))
    ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    paragraphs=[''.join(p.itertext()).strip() for p in tree.findall('.//w:p',ns)]
    # itertext includes only actual textual OOXML content; retain full text for audit.
    text='\n'.join(p for p in paragraphs if p)
    with (P/'caf_supplement_document_text.txt').open('x',encoding='utf-8',newline='\n') as f:f.write(text)
    wb=openpyxl.load_workbook(io.BytesIO(tabraw),read_only=True,data_only=False)
    sheets=[]
    for ws in wb:
        heads=[list(row) for row in ws.iter_rows(min_row=1,max_row=3,values_only=True)]
        sheets.append(dict(sheet=ws.title,rows=ws.max_row,columns=ws.max_column,first_three_rows=heads))
    wb.close()
    terms={term:[dict(paragraph=i,text=p) for i,p in enumerate(paragraphs) if re.search(term,p,re.I)] for term in ['wash','pre.?treat','sequen','IFN','TGF','migration','proliferat','donor','patient','supplementary methods','accession']}
    result=dict(bundle_sha256=hashlib.sha256(raw).hexdigest(),inventory=inventory,document=dict(member=docname,sha256=hashlib.sha256(docraw).hexdigest(),paragraphs=len(paragraphs)),sample_table=dict(member=tabname,sha256=hashlib.sha256(tabraw).hexdigest(),sheets=sheets),document_matches=terms,other_workbook_numeric_contents_not_parsed=True)
    with (P/'CAF_SUPPLEMENT_INITIAL_INSPECTION.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2,default=str)
    print(json.dumps(dict(inventory=inventory,sheets=sheets,matches={k:len(v) for k,v in terms.items()}),ensure_ascii=False,default=str))

if __name__=='__main__':main()
