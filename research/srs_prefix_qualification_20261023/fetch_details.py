"""Resolve the nine exact publisher supplement metadata records, not media."""
from concurrent.futures import ThreadPoolExecutor
import json
from retrieve import get, OUT

rows = json.loads((OUT/'FIGSHARE_INDEX.json').read_text())
assert len(rows) == 9 and all(r['doi'].startswith('10.1021/acs.analchem.5c04806.s') for r in rows)
with ThreadPoolExecutor(max_workers=4) as executor:
    list(executor.map(lambda row: get('figshare_'+str(row['id'])+'.json', row['url']), rows))
