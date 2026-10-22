"""Offline string projection of retained client metadata routes; no JS execution."""
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261022/stack_raw_qualification'
text = (LOG / 'network/landing_client.body').read_text(encoding='utf-8')
snippets = []
for match in re.finditer(r'public-api|/datasets/|/files\?|file_download|download_url|downloadUrl|files\?folder', text):
    snippets.append({'offset': match.start(), 'snippet': text[max(0, match.start()-180):match.end()+360]})
with (LOG / 'CLIENT_ROUTE_PROJECTION.json').open('x', encoding='utf-8') as stream:
    json.dump({'snippets': snippets, 'executed_javascript': False}, stream, ensure_ascii=False, indent=2)
print(json.dumps(snippets, ensure_ascii=False))
