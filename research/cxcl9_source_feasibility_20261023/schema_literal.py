"""Resolve literal 'None' labels without treating them as missing data."""
import json
import pandas as pd
from schema import FILES
from source import OUT

if __name__ == '__main__':
    results = []
    for name in FILES:
        frame = pd.read_csv(OUT/'raw'/f'00_Raw_Data_{name}.csv', keep_default_na=False)
        keys = ['Cell line', 'Condition', 'Cytokines', 'Inhibitors']
        counts = frame.groupby(keys).size()
        sample_map = frame.groupby(['Condition', 'Cytokines', 'Inhibitors'])['Sample'].nunique()
        results.append({'file': name, 'rows': len(frame),
                        'categories': {col: sorted(frame[col].unique().tolist()) for col in keys},
                        'groups': len(counts), 'min_beads_per_group': int(counts.min()),
                        'max_beads_per_group': int(counts.max()),
                        'sample_id_count': int(frame['Sample'].nunique()),
                        'max_sample_ids_per_group': int(sample_map.max()),
                        'concentrations': {col: sorted(frame[col].unique().tolist()) for col in
                            ['Cytokine concentration (ng/mL)', 'Inhibitor concentration (uM)']},
                        'blank_counts_by_condition': frame[
                            (frame['Cytokines'] == 'None') & (frame['Inhibitors'] == 'None')
                        ].groupby('Condition').size().to_dict()})
    target = OUT/'SCHEMA_LITERAL.json'
    assert not target.exists()
    target.write_text(json.dumps(results, indent=2), encoding='utf-8')
    print(json.dumps(results, indent=2))
