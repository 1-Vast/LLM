"""Inventory PDF attachment names and page top metadata only."""
import json
from pypdf import PdfReader
from attachment import OUT

if __name__ == '__main__':
    result = []
    for name in ['mmc1.pdf', 'mmc3.pdf', 'mmc4.pdf']:
        reader = PdfReader(OUT/name)
        result.append({'file': name, 'attachments': list(reader.attachments),
                       'page_sizes': [list(page.mediabox) for page in reader.pages[:2]],
                       'first_page_first_line': (reader.pages[0].extract_text().splitlines() or [''])[0][:160]})
    (OUT/'PDF_STRUCTURE.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
