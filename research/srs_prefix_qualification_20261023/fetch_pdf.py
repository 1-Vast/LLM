"""Download only the single verified publisher-linked supplementary PDF."""
import hashlib
import json
from retrieve import OUT, get

files = json.loads((OUT/'FILE_INVENTORY.json').read_text())['files']
pdfs = [f for f in files if f['name'].endswith('.pdf')]
assert len(pdfs) == 1
selected = pdfs[0]
assert selected['size'] < 10_000_000
get('publisher_supplement.pdf', selected['download_url'])
path = OUT/'publisher_supplement.pdf'
receipt = json.loads((OUT/'publisher_supplement.pdf.receipt.json').read_text())
assert receipt['status'] == 200 and path.read_bytes().startswith(b'%PDF-')
assert path.stat().st_size == selected['size']
assert hashlib.md5(path.read_bytes()).hexdigest() == selected['computed_md5']
(OUT/'PDF_BINDING.json').write_text(json.dumps(dict(article_id=selected['article_id'],
    doi=selected['doi'], actual_bytes=path.stat().st_size, publisher_size_match=True,
    publisher_md5_match=True, pdf_magic=True, scope='Publisher identity/bytes, not biological validity'), indent=2), encoding='utf-8')
