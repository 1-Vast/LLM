"""Audit already acquired design columns; never select response or raw-count columns."""
from pathlib import Path
import hashlib
import json
import re
import xml.etree.ElementTree as ET
import pandas as pd

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / '2026-10-26-agent-cell-evidence'
ROOT = HERE.parents[1]
COLS = ['Well', 'Cell line', 'Drug 1', 'Drug 2', 'Conc 1 (uM)', 'Conc 2 (uM)',
        'Failed QC', 'Iteration', 'file', 'Plate']
PAIR = ROOT / 'research/eight_directions_20261026/evidence_audit/raw/PAIR_SCREEN.csv'
assert not any(x in str(PAIR).lower() for x in ('sealed', 'holdout', 'reserve', 'vault'))
df = pd.read_csv(PAIR, usecols=COLS, dtype=str, keep_default_na=False)
overlap = pd.read_csv(PREVIOUS / 'independent_overlap_mapping.csv', dtype=str, keep_default_na=False)
keycols = ['Cell line','Drug 1','Drug 2','Conc 1 (uM)','Conc 2 (uM)']
out = {'python': __import__('sys').executable, 'response_columns_loaded': False,
       'selected_columns': COLS, 'overlap_rows':len(overlap),
       'overlap_stage_counts':overlap.groupby('Iteration').size().to_dict(),
       'overlap_files':overlap[['Iteration','file','Plate']].drop_duplicates().to_dict('records')}
overlap.to_csv(HERE / 'overlap_metadata_reused.csv', index=False)
ax = df[(df['Drug 1']=='Axitinib') | (df['Drug 2']=='Axitinib')].copy()
ax['Axitinib_role'] = ax['Drug 1'].eq('Axitinib').map({True:'Drug1',False:'Drug2'})
ax['row'] = ax.Well.str.extract(r'^([A-P])', expand=False)
ax['column'] = ax.Well.str.extract(r'([0-9]+)$', expand=False)
layout = ax.groupby(['Iteration','Cell line','file','Plate','Axitinib_role']).agg(
    rows=('row',lambda x: ','.join(sorted(set(x)))),
    columns=('column',lambda x: ','.join(sorted(set(x),key=int))),
    wells=('Well','size'), QC_labels=('Failed QC',lambda x: ','.join(sorted(set(x)))))
layout.reset_index().to_csv(HERE / 'axitinib_design_locations.csv', index=False)
out['axitinib_design_groups']=len(layout)
out['overlap_metadata_sha256']=hashlib.sha256((HERE/'overlap_metadata_reused.csv').read_bytes()).hexdigest()
(HERE/'mapping_summary.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
root = ET.parse(PREVIOUS / 'sources/PMC11696745.xml').getroot()
notes=[]
for sec in root.iter('sec'):
    title=sec.findtext('title','')
    for p in sec.findall('p'):
        text=''.join(p.itertext())
        if any(x in text.lower() for x in ['four of the drugs duplicated','independent duplicates','72','randomly selected combination plates','in rounds 1','cell viability','optimized seeding']):
            notes.append({'section':title,'paragraph':text})
(HERE/'sources/xml_design_passages.json').write_text(json.dumps(notes,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
print(layout.loc[layout.index.get_level_values('Cell line') == 'MSKEWS-33838'].to_string())
