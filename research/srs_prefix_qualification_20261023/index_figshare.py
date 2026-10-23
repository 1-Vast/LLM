"""Public metadata index; do not cast assay or trajectory fields."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/srs_prefix_qualification/root'
data = json.loads((OUT/'figshare_lookup.json').read_text())
assert isinstance(data, list)
rows = [{key: row.get(key) for key in ['id', 'title', 'doi', 'url', 'url_public_html', 'published_date']}
        for row in data]
(OUT/'FIGSHARE_INDEX.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
print(json.dumps(rows, indent=2))
