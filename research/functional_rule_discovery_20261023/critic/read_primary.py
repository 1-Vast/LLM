"""Extract retained official proceedings PDF for source review, no author execution."""
from pathlib import Path
from pypdf import PdfReader

out = Path(__file__).resolve().parents[3] / 'log/20261023/functional_rule_discovery/critic'
reader = PdfReader(out / 'primary2.body')
text = '\n\n'.join(f'PAGE {i+1}\n{page.extract_text()}' for i, page in enumerate(reader.pages))
text = text.encode('utf-8', errors='replace').decode('utf-8')
(out / 'PRIMARY_TEXT.txt').write_text(text, encoding='utf-8')
print(text)
