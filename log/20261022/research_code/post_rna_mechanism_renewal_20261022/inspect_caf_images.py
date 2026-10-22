"""Inspect already acquired source images with OOXML/ZIP provenance."""
import hashlib,io,json,zipfile
import xml.etree.ElementTree as ET
from PIL import Image
from fetch_primary import P

def main():
    dest=P/'caf_figures';dest.mkdir(exist_ok=True)
    with zipfile.ZipFile(P/'caf_rest_supplementary_bundle.body') as bundle:
        docraw=bundle.read('41392_2026_2965_MOESM1_ESM.docx')
        mainraw=bundle.read('41392_2026_2965_Fig6_HTML.webp')
    with zipfile.ZipFile(io.BytesIO(docraw)) as doc:
        tree=ET.fromstring(doc.read('word/document.xml'));rels=ET.fromstring(doc.read('word/_rels/document.xml.rels'))
        rm={r.attrib['Id']:r.attrib['Target'] for r in rels}
        ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
        rows=[dict(paragraph=i,text=''.join(e.itertext()),images=[rm[b.attrib['{http://schemas.openxmlformats.org/officeDocument/2006/relationships}embed']] for b in e.findall('.//a:blip',ns)]) for i,e in enumerate(tree.findall('.//w:p',ns))]
        entries=[]
        for number in [9,11]:
            i=next(i for i,row in enumerate(rows) if row['text'].startswith('Supplementary Fig. '+str(number)+'.'))
            j=i-1
            while not rows[j]['images'] and not rows[j]['text'].strip():j-=1
            assert len(rows[j]['images'])==1
            member='word/'+rows[j]['images'][0];raw=doc.read(member)
            name='supplement_Fig'+str(number)+'.png';im=Image.open(io.BytesIO(raw));im.save(dest/name)
            entries.append(dict(output=name,source_member=member,source_sha256=hashlib.sha256(raw).hexdigest(),size=im.size,caption=rows[i]['text']))
    im=Image.open(io.BytesIO(mainraw));im.save(dest/'main_Fig6.png')
    entries.append(dict(output='main_Fig6.png',source_member='41392_2026_2965_Fig6_HTML.webp',source_sha256=hashlib.sha256(mainraw).hexdigest(),size=im.size))
    with (dest/'PROVENANCE.json').open('x',encoding='utf-8') as f:json.dump(dict(entries=entries,ooxml_image_and_caption_mapping=rows),f,ensure_ascii=False,indent=2)
    print(json.dumps(entries,ensure_ascii=False))

if __name__=='__main__':main()
