"""Read-only supplementary PDF extraction; artifacts stay in log/."""
import json
from pypdf import PdfReader
from retrieve import OUT

reader = PdfReader(OUT/'publisher_supplement.pdf')
pages = [page.extract_text() or '' for page in reader.pages]
text = '\n\n'.join(f'PAGE {i+1}\n{value}' for i, value in enumerate(pages))
(OUT/'PDF_TEXT.txt').write_text(text, encoding='utf-8')
report = dict(pages=len(pages), page_previews=[dict(page=i+1, text=t[:230]) for i, t in enumerate(pages)],
              attachments=list(reader.attachments), scope='Text/attachment inventory, not parsed experimental data')
(OUT/'PDF_STRUCTURE.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
print(json.dumps(report, indent=2))
