"""Verify archive PDFs and emit only anchored table/figure captions."""
import hashlib
import io
import json
import re
import zipfile
from pypdf import PdfReader
from attachment import OUT

MD5 = {'mmc1.pdf': 'f4996291804515f2b114db71fd220c99',
       'mmc3.pdf': 'c2516ecfb96c26bd6507e92f0aeffea4',
       'mmc4.pdf': '57332dc38c9a90d2a58294bd0ba84851'}

if __name__ == '__main__':
    target = OUT/'PDF_CAPTIONS.json'
    assert not target.exists()
    result = []
    with zipfile.ZipFile(OUT/'epmc_supplements.zip') as archive:
        for name, expected in MD5.items():
            body = archive.read(name)
            assert hashlib.md5(body).hexdigest() == expected
            (OUT/name).write_bytes(body)
            document = PdfReader(io.BytesIO(body))
            matches = []
            for index, page in enumerate(document.pages):
                text = page.extract_text()
                lines = [line.strip() for line in text.splitlines()]
                for line in lines:
                    if re.match(r'^(Table\s*S?\d|Supplementary\s+Table|Fig(?:ure)?\.?\s*S?\d)', line, re.I):
                        matches.append({'page': index+1, 'caption': line[:500]})
            result.append({'file': name, 'pages': len(document.pages), 'md5_matches': True, 'captions': matches})
    target.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
