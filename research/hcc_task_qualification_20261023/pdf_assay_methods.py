"""Read drug-screen method paragraphs from supplement methods pages only."""
import json
import re
from pypdf import PdfReader
from attachment import OUT

if __name__ == '__main__':
    reader = PdfReader(OUT/'mmc1.pdf')
    matches = []
    for index in range(1, 9):
        text = reader.pages[index].extract_text()
        # Sentences can contain declared assay parameters, never response tables.
        paragraphs = re.split(r'\n\s*\n', text)
        for paragraph in paragraphs:
            if re.search(r'CellTiter|drug screen|dose.response|area under|normaliz|DMSO|100 compound', paragraph, re.I):
                matches.append({'page': index+1, 'method_text': paragraph})
    target = OUT/'PDF_ASSAY_METHODS.json'
    assert not target.exists()
    target.write_text(json.dumps(matches, indent=2), encoding='utf-8')
    print(json.dumps(matches, indent=2))
