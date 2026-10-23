"""Read the author's public UI layout for download links, without callback data."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/multi_context_state_function/root_sources'
assert not (OUT / 'layout.body').exists()
response = requests.get('https://gwps.wi.mit.edu/_dash-layout', timeout=45)
(OUT / 'layout.body').write_bytes(response.content)
(OUT / 'layout.receipt.json').write_text(json.dumps({
    'url': response.url, 'status': response.status_code, 'utc': datetime.now(timezone.utc).isoformat(),
    'bytes': len(response.content), 'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
links, text = [], []


def visit(node):
    if isinstance(node, dict):
        props = node.get('props', {})
        if 'href' in props:
            links.append({'href': props['href'], 'label': props.get('children')})
        for key, value in node.items():
            if key in ('figure', 'data'):
                continue
            visit(value)
    elif isinstance(node, list):
        for value in node:
            visit(value)
    elif isinstance(node, str) and len(node) > 10:
        text.append(node)


visit(response.json())
(OUT / 'BROWSER_LINKS.json').write_text(json.dumps(links, indent=2), encoding='utf-8')
(OUT / 'BROWSER_TEXT.json').write_text(json.dumps(text, indent=2), encoding='utf-8')
print(json.dumps({'links': links, 'text': text}, indent=2)[:18000])
