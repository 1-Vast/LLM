"""Read the author's K562 dataset UI, recording links without plotting values."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/multi_context_state_function/root_sources'
page = sys.argv[1] if len(sys.argv) > 1 else 'k562'
pathname = {'k562': '/K562_gwps', 'home': '/'}[page]
stem = {'k562': 'dataset_page', 'home': 'homepage'}[page]
request = {'output': 'page-content.children', 'outputs': {'id': 'page-content', 'property': 'children'},
           'inputs': [{'id': 'url', 'property': 'pathname', 'value': pathname},
                      {'id': 'url', 'property': 'search', 'value': ''}],
           'state': [], 'changedPropIds': ['url.pathname']}
assert not (OUT / (stem + '.body')).exists()
(OUT / (stem + '.request.json')).write_text(json.dumps(request, indent=2), encoding='utf-8')
response = requests.post('https://gwps.wi.mit.edu/_dash-update-component', json=request, timeout=45)
(OUT / (stem + '.body')).write_bytes(response.content)
(OUT / (stem + '.receipt.json')).write_text(json.dumps({
    'url': response.url, 'method': 'POST (read-only public UI navigation)', 'status': response.status_code,
    'utc': datetime.now(timezone.utc).isoformat(), 'bytes': len(response.content),
    'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
links, texts, skipped = [], [], []


def visit(node):
    if isinstance(node, dict):
        props = node.get('props', {})
        if 'href' in props:
            links.append({'href': props['href'], 'label': props.get('children')})
        for key, value in node.items():
            if key in ('figure', 'data', 'options'):
                skipped.append(key)
                continue
            visit(value)
    elif isinstance(node, list):
        for value in node:
            visit(value)
    elif isinstance(node, str) and len(node) > 12:
        texts.append(node)


visit(response.json())
result = {'links': links, 'texts': texts, 'skipped_fields': skipped}
(OUT / (stem.upper() + '_MANIFEST.json')).write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2)[:23000])
