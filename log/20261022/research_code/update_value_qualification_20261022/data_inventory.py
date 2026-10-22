"""Inventory only filenames and explicitly named PRISM treatment/cell metadata."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/update_value_qualification/data'
OUT.mkdir(parents=True, exist_ok=True)
roots = [ROOT / 'data/external/prism_19q4/raw',
         ROOT / 'data/external/gdsc_combinations/jaaks2022_figshare']
inventory = [{'source': str(root.relative_to(ROOT)),
              'files': [{'name': p.name, 'bytes': p.stat().st_size} for p in sorted(root.iterdir()) if p.is_file()]}
             for root in roots]
metadata = {}
for path in roots[0].glob('*info.csv'):
    with path.open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        rows = list(reader)
    metadata[path.name] = {'header': reader.fieldnames, 'rows': len(rows),
                           'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                           'examples': rows[:2]}
result = {'inventory': inventory, 'prism_metadata': metadata,
          'rdkit_available': importlib.util.find_spec('rdkit') is not None,
          'response_files_opened': False}
(OUT / 'LOCAL_INVENTORY.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, ensure_ascii=False, indent=2))
