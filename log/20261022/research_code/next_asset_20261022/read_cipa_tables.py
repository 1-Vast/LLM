"""Resume read-only metadata extraction after optional renderer import failure."""
from discover import OUT
import hashlib
import json
import shutil
import subprocess
import zipfile
from pypdf import PdfReader

if __name__=='__main__':
    source=OUT/'cipa_supplement_tables.pdf'
    reader=PdfReader(source)
    texts=[page.extract_text() or '' for page in reader.pages]
    with (OUT/'cipa_supplement_complete_text.txt').open('x',encoding='utf-8') as f:
        f.write('\n\f\n'.join(texts))
    locations=[]
    for index,txt in enumerate(texts):
        if 'Table S2.' in txt or 'Table S2:' in txt:
            prefix=OUT/f'cipa_table_s2_page_{index+1}'
            subprocess.run([shutil.which('pdftoppm'),'-f',str(index+1),'-l',str(index+1),'-singlefile','-scale-to','1600','-png',str(source),str(prefix)],check=True,capture_output=True)
            locations.append({'page':index+1,'image':str(prefix)+'.png','text':txt})
    with zipfile.ZipFile(OUT/'cipa_supplement_europepmc.body') as archive:
        manifest=[{'name':i.filename,'bytes':i.file_size} for i in archive.infolist()]
    result={'archive':manifest,'selected_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'pages':len(texts),'table_s2_candidates':locations,'numeric_assay_casts':0,'exposure':'Complete supplemental text extracted to retained file; includes result tables/figures. Treat supplement as designer-exposed, not an untouched outcome reserve.'}
    (OUT/'CIPA_SUPPLEMENT_AUDIT.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'pages':len(texts),'table_s2_candidates':locations}))
