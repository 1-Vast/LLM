"""Project released action and generation fields, without reporting outcome values."""
import csv
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261023/organoid_schedule_qualification/root'

if __name__ == '__main__':
    tables = []
    with zipfile.ZipFile(OUT / 'zenodo_archive.body') as archive:
        for name in archive.namelist():
            if not name.endswith('.csv'):
                continue
            rows = list(csv.DictReader(io.StringIO(archive.read(name).decode('utf-8-sig'))))
            fields = ['seq', 't0', 't1'] if '/sequential/' in name else [x for x in rows[0] if x.startswith('conc') and x[-1].isdigit()]
            design = [{k: row[k] for k in fields + ['gen', 'number']} for row in rows]
            groups = defaultdict(list)
            for row in design:
                groups[tuple(row[k] for k in fields)].append(row['gen'])
            duplicates = [dict(action=dict(zip(fields, action)), generations=gens)
                          for action, gens in groups.items() if len(gens) > 1]
            tables.append(dict(name=name, action_fields=fields, design=design,
                               generation_counts=dict(Counter(row['gen'] for row in rows)),
                               distinct_actions=len(groups), repeated_actions=duplicates,
                               response_values_emitted=False))
    target = OUT / 'ACTION_DESIGN.json'
    assert not target.exists()
    target.write_text(json.dumps(tables, indent=2), encoding='utf-8')
    print(json.dumps([{k:v for k,v in table.items() if k != 'design'} for table in tables], indent=2))
