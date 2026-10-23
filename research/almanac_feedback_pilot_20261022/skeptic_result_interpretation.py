"""Saved-summary interpretation only; no refit or raw-response access."""
from pathlib import Path
import json
ROOT=Path('log/20261022/almanac_feedback_pilot')
r=json.loads((ROOT/'root/RESULTS.json').read_text())
m=r['development_metrics']; a=m['B0-selected']; b=m['B1-selected']
out={}
for metric in ('mse','mae','mean_top10pct_regret'):
    out[metric]={'B0':a[metric],'B1':b[metric],'relative_gain':(a[metric]-b[metric])/a[metric]}
out['matched_method_mse_gain']={k[3:]:v['mse']-m['B1:'+k[3:]]['mse'] for k,v in m.items() if k.startswith('B0:')}
out['cell_relative_mse_gain']=[(x-y)/x for x,y in zip(a['cell_mse'],b['cell_mse'])]
out['ranking_cells_improved']=sum(x>y for x,y in zip(a['cell_top10pct_regret'],b['cell_top10pct_regret']))
out['dose_gains']=[x-y for x,y in zip(a['dose_mse'],b['dose_mse'])]
out['last_three_dose_share']=sum(out['dose_gains'][-3:])/sum(out['dose_gains'])
out['study_mse_cells_improved']=sum(x>y for x,y in zip(m['B0-study-exclusion']['cell_mse'],m['B1-study-exclusion']['cell_mse']))
out['study_ranking_cells_improved']=sum(x>y for x,y in zip(m['B0-study-exclusion']['cell_top10pct_regret'],m['B1-study-exclusion']['cell_top10pct_regret']))
with (ROOT/'skeptic/RESULT_DIAGNOSTICS.json').open('x',encoding='utf-8') as f: json.dump(out,f,indent=2)
print(json.dumps(out,indent=2))
