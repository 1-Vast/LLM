"""Independent saved-result arithmetic only; never imports training code or reads source labels."""
from pathlib import Path
import json, math, statistics
ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'log/20261022/naiad_direct_baseline'
p=json.loads((BASE/'PREDICTIONS.json').read_text())
c=json.loads((BASE/'COSTS.json').read_text())
h=json.loads((BASE/'INNER_HISTORIES.json').read_text())
assert len(p['pairs'])==1051 and len(set(p['pairs']))==1051
assert len(p['truth'])==1051 and len(p['records'])==18 and len(c)==36 and len(h)==18
key=lambda x:(x['budget'],x['model_type'],x['seed'])
hist={key(x):x['mse'] for x in h}
errors=[]
for r in p['records']:
 assert len(r['prediction'])==1051 and all(map(math.isfinite,r['prediction']))
 mse=math.fsum((a-b)**2 for a,b in zip(r['prediction'],p['truth']))/1051
 errors.append(abs(mse-r['development_mse']))
 history=hist[key(r)]
 assert len(history)==500 and all(map(math.isfinite,history))
 assert min(range(500),key=lambda i:history[i])+1==r['selected_epoch']
 assert min(history)==r['inner_validation_mse']
 stages={x['stage']:x for x in c if key(x)==key(r)}
 assert stages['inner']['train_count']==3*r['budget']//4
 assert stages['final']['train_count']==r['budget']
 assert stages['final']['epochs']==r['selected_epoch']
 for x in stages.values():
  assert x['optimizer_steps']==x['epochs']*math.ceil(x['train_count']/1024)
summary=[]
for b in [128,512,2048]:
 for model in ['pheno','both']:
  a=[r['development_mse'] for r in p['records'] if r['budget']==b and r['model_type']==model]
  summary.append({'budget':b,'model_type':model,'mean':statistics.mean(a),'seed_sd':statistics.stdev(a),'min':min(a),'max':max(a)})
out={'predictions_checked':18,'max_mse_error':max(errors),'checkpoint_histories_checked':18,'optimizer_steps':sum(x['optimizer_steps'] for x in c),'checkpoint_evaluations':sum(len(x['mse']) for x in h),'fit_seconds':sum(x['seconds'] for x in c),'summary':summary}
(BASE/'reviewer/SAVED_ARITHMETIC.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
