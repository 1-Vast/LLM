"""Inspect labels/options on the author's linked scatter UI; no graph callback."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

import requests

OUT = Path(__file__).resolve().parents[2] / 'log/20261022/replogle_growth_acquisition/root_sources'
assert not (OUT / 'scatter_page.body').exists()
request = {'output': 'page-content.children', 'outputs': {'id': 'page-content', 'property': 'children'},
           'inputs': [{'id': 'url', 'property': 'pathname', 'value': '/program_scatter'},
                      {'id': 'url', 'property': 'search', 'value': ''}],
           'state': [], 'changedPropIds': ['url.pathname']}
(OUT / 'scatter_page.request.json').write_text(json.dumps(request, indent=2), encoding='utf-8')
response = requests.post('https://gwps.wi.mit.edu/_dash-update-component', json=request, timeout=45)
(OUT / 'scatter_page.body').write_bytes(response.content)
(OUT / 'scatter_page.receipt.json').write_text(json.dumps({
    'url': response.url, 'method': 'POST read-only public navigation', 'status': response.status_code,
    'utc': datetime.now(timezone.utc).isoformat(), 'bytes': len(response.content),
    'sha256': hashlib.sha256(response.content).hexdigest()}, indent=2), encoding='utf-8')
response.raise_for_status()
options, links = {}, []


def visit(node):
    if isinstance(node, dict):
        props = node.get('props', {})
        if 'options' in props:
            options[str(props.get('id'))] = [item.get('label') if isinstance(item, dict) else item for item in props['options']]
        if 'href' in props:
            links.append(props['href'])
        for key, value in node.items():
            if key not in ('figure', 'data', 'options'):
                visit(value)
    elif isinstance(node, list):
        for value in node:
            visit(value)


visit(response.json())
result = {'option_labels': {key: value for key, value in options.items() if key != 'program_chosen_guide'},
          'links': links}
(OUT / 'SCATTER_UI_LABELS.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result, indent=2))
