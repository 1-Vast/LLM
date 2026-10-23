"""Initial raw files: expose categories/counts only, never fluorescence values."""
from concurrent.futures import ThreadPoolExecutor
from source import OUT, REPO, fetch
import json
import pandas as pd

FILES = ['E3CA', 'E3CB', 'E3DA', 'E3DB']

if __name__ == '__main__':
    sha = json.loads((OUT/'commit.json').read_text(encoding='utf-8'))['sha']

    def retrieve(name):
        file = f'00_Raw_Data_{name}.csv'
        fetch(f'https://raw.githubusercontent.com/{REPO}/{sha}/data/cxcl9_assay/{file}',
              'raw/'+file)
        frame = pd.read_csv(OUT/'raw'/file)
        categories = [col for col in frame.columns
                      if col.lower() in ['cytokines', 'inhibitors', 'condition']]
        return {'file': name, 'columns': list(frame.columns), 'rows': len(frame),
                'categories': {col: sorted(frame[col].dropna().astype(str).unique().tolist())
                               for col in categories},
                'missing_counts': {col: int(frame[col].isna().sum()) for col in frame.columns},
                'groups': frame.groupby(categories, dropna=False).size().rename('beads').reset_index().to_dict('records')}

    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(retrieve, FILES))
    target = OUT/'SCHEMA.json'
    assert not target.exists()
    target.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps([{k: v for k, v in row.items() if k != 'groups'} for row in results], indent=2))
