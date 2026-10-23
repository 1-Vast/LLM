"""Check BioStudies' published file record via its file-serving route."""
from official_package import OUT, fetch
import json
import zipfile
from io import BytesIO
from xml.etree import ElementTree as ET

if __name__ == '__main__':
    record = json.loads((OUT/'biostudies_record.json').read_text())
    files = record['section']['files']
    assert any(x['path']=='mmc2.docx' for x in files)
    # Accession and filename are from the authenticated record, not a guessed CDN attachment.
    response = fetch('biostudies_mmc2.docx',
        'https://www.ebi.ac.uk/biostudies/files/S-EPMC12205652/mmc2.docx')
    result = dict(status=response.status_code, declared_files=files,
                  route='BioStudies file service using API record accession and listed path')
    if response.status_code == 200 and zipfile.is_zipfile(BytesIO(response.content)):
        with zipfile.ZipFile(BytesIO(response.content)) as archive:
            result['members'] = archive.namelist()
            tree = ET.fromstring(archive.read('word/document.xml'))
            ns = {'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            # Read only initial schema text, not assay responses.
            result['first_paragraphs'] = [''.join(p.itertext()) for p in tree.findall('.//w:p',ns)[:5]]
    (OUT/'BIOSTUDIES_SCHEMA.json').write_text(json.dumps(result, indent=2),encoding='utf-8')
    print(json.dumps(result, indent=2))
