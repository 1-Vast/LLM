"""Extract exact supplement; locate concentration table and render its page."""
from discover import OUT
import hashlib
import importlib.util
import json
import zipfile

if __name__=='__main__':
    with zipfile.ZipFile(OUT/'cipa_supplement_europepmc.body') as archive:
        manifest=[{'name':i.filename,'bytes':i.file_size} for i in archive.infolist()]
        matches=[i for i in archive.infolist() if 'Supplemental_Figures_and_Tables' in i.filename and i.filename.endswith('.pdf')]
        assert len(matches)==1
        body=archive.read(matches[0])
    with (OUT/'cipa_supplement_tables.pdf').open('xb') as f:
        f.write(body)
    print(json.dumps({'manifest':manifest,'selected':matches[0].filename,'bytes':len(body),'sha256':hashlib.sha256(body).hexdigest(),'fitz_available':importlib.util.find_spec('fitz') is not None,'pypdf_available':importlib.util.find_spec('pypdf') is not None}))
    import fitz
    doc=fitz.open(OUT/'cipa_supplement_tables.pdf')
    texts=[page.get_text() for page in doc]
    with (OUT/'cipa_supplement_complete_text.txt').open('x',encoding='utf-8') as f:
        f.write('\n\f\n'.join(texts))
    locations=[]
    for index, txt in enumerate(texts):
        if 'Table S2.' in txt or 'Table S2:' in txt:
            page=doc[index]
            image=OUT/f'cipa_table_s2_page_{index+1}.png'
            page.get_pixmap(matrix=fitz.Matrix(1.5,1.5)).save(image)
            locations.append({'page':index+1,'image':str(image),'text':txt})
    result={'archive':manifest,'selected_name':matches[0].filename,'selected_sha256':hashlib.sha256(body).hexdigest(),'pages':len(texts),'table_s2_candidates':locations,'numeric_assay_casts':0,'exposure':'Complete supplemental text extracted to retained file; includes result tables/figures. Treat supplement as designer-exposed, not an untouched outcome reserve.'}
    (OUT/'CIPA_SUPPLEMENT_AUDIT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'pages':len(texts),'table_s2_candidates':locations}))
