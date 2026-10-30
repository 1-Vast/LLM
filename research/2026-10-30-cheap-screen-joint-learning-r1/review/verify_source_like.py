"""Post hoc source-like trimming diagnostic, independently implemented.

Uses only raw CXCL9 exports and the archived source preparation script. It does
not read pilot_result.json or independent_result.json.
"""
import csv, hashlib, itertools, json, time
from collections import defaultdict
from pathlib import Path
import numpy as np

T0, C0 = time.perf_counter(), time.process_time()
ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'sources' / 'cxcl9_prepare.body'
STIM = {'None':'00', 'IFNG':'10', 'TNFA':'01', 'IFNG_TNFA':'11'}
DRUGS = ['Momelotinib','BMS-345541','Salirasib','Trametinib','Taselisib']
PREPS = ['E3CA','E3CB','E3DA','E3DB']

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def envdiff(a,b): return [a[0]-b[1], a[1]-b[0]]

out = {
  'diagnostic': 'source-like pooled technical-well IQR sensitivity; post hoc robustness diagnostic',
  'method': 'Within each preparation×stimulus×drug, pool Sample1 and Sample2 events; NumPy linear quartiles; retain strict PE > Q1−1.5IQR and PE < Q3+1.5IQR; calculate each surviving well MFI then equal-average surviving wells.',
  'source_script_sha256': sha(SOURCE), 'source_sha256': {}, 'preparations': {},
  'limitations': ['Source-like sensitivity only; it does not revise the frozen primary protocol.',
                  'Capture-bead APC gating cannot be reconstructed from PE-only exports.',
                  'Technical envelopes are descriptive and no biological, molecular, external-validation, CI or p-value claim follows.']}

for code in PREPS:
  path = ROOT/'evidence'/f'cxcl9_raw_{code}.body'; out['source_sha256'][path.name] = sha(path)
  pooled, raw = defaultdict(list), defaultdict(list)
  identities = {}
  with path.open(newline='', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
      key=(row['Inhibitors'], STIM[row['Cytokines']])
      well=row['Condition']; val=float(row['Fluorescent intensity (PE)'])
      pooled[key].append(val); raw[(key,well)].append(val)
      identities[(key,well)]={k:v for k,v in row.items() if k!='Fluorescent intensity (PE)'}
  assert len(pooled)==24 and all(len(raw[(k,w)]) > 0 for k in pooled for w in ['Sample1','Sample2'])
  wells, groups = {}, {}
  for key, vals in pooled.items():
    a=np.asarray(vals,dtype=float); q1,q3=np.quantile(a,[.25,.75],method='linear'); iqr=q3-q1
    lo,hi=q1-1.5*iqr,q3+1.5*iqr
    groups['|'.join(key)] = {'n_pooled':len(a),'q1':float(q1),'q3':float(q3),'iqr':float(iqr),
      'trim_bounds':[float(lo),float(hi)],'strict_rule':'PE > lower and PE < upper'}
    for well in ['Sample1','Sample2']:
      ar=np.asarray(raw[(key,well)],dtype=float); keep=ar[(ar>lo)&(ar<hi)]
      wells['|'.join((key[0],key[1],well))]={'identity':identities[(key,well)],'n_raw':len(ar),
        'n_kept':len(keep),'n_removed':len(ar)-len(keep),'mfi':float(np.mean(keep)),
        'pooled_group':'|'.join(key),'pooled_q1':float(q1),'pooled_q3':float(q3),
        'pooled_trim_bounds':[float(lo),float(hi)]}
  means,ranges={},{}
  for drug in ['None']+DRUGS:
    means[drug],ranges[drug]={},{}
    for s in ['00','10','01','11']:
      pair=[wells['|'.join((drug,s,w))]['mfi'] for w in ['Sample1','Sample2']]
      means[drug][s]=sum(pair)/2; ranges[drug][s]=[min(pair),max(pair)]
  m,cr=means['None'],ranges['None']; D0=m['10']-m['00']; N0=m['11']-m['01']; S0=m['11']-m['00']
  di,ni=envdiff(cr['10'],cr['00']),envdiff(cr['11'],cr['01'])
  eligible=di[0]>0 and ni[0]>0 and S0>0
  control={'means':m,'ranges':cr,'D0':D0,'N0':N0,'S0':S0,'D_interval':di,'N_interval':ni,'eligible':eligible}
  prep={'pooled_groups':groups,'wells':wells,'means':means,'well_ranges':ranges,'controls':control,'targets':{}}
  out['preparations'][code]=prep
  if not eligible: continue
  kappa, I0=N0/D0, N0-D0
  ratios=[n/d for n,d in itertools.product(ni,di) if d>0]; ki=[min(ratios),max(ratios)]
  control.update(kappa=kappa,I0=I0,kappa_endpoint_ratios=ratios,kappa_interval=ki)
  for drug in DRUGS:
    y,wr=means[drug],ranges[drug]; effect=y['10']-y['00']
    pred={'H_gain':y['01']+kappa*effect,'B_add':y['10']+y['01']-y['00'],
          'B_const':y['10']+y['01']-y['00']+I0,'B_control':m['11']}
    delta=envdiff(wr['10'],wr['00']); products=[a*b for a,b in itertools.product(ki,delta)]
    interval=[wr['01'][0]+min(products),wr['01'][1]+max(products)]
    signed={k:(v-y['11'])/S0 for k,v in pred.items()}; absolute={k:abs(v) for k,v in signed.items()}
    prep['targets'][drug]={'calibration':{s:y[s] for s in ['00','10','01']},'observed':y['11'],
      'observed_interval':wr['11'],'predictions':pred,'signed_normalized_errors':signed,
      'absolute_normalized_errors':absolute,'D_drug_interval':delta,'endpoint_products':products,
      'gain_prediction_interval':interval,'technical_overlap':interval[0]<=wr['11'][1] and wr['11'][0]<=interval[1],
      'gain_minus_constant_prediction':pred['H_gain']-pred['B_const'],
      'gain_minus_constant_formula':I0*(effect/D0-1),
      'gain_minus_comparator_absolute_errors':{b:absolute['H_gain']-absolute[b] for b in ['B_add','B_const','B_control']}}
  prep['MAE']={k:sum(t['absolute_normalized_errors'][k] for t in prep['targets'].values())/5 for k in ['H_gain','B_add','B_const','B_control']}
  prep['gain_minus_constant_MAE']=prep['MAE']['H_gain']-prep['MAE']['B_const']
  prep['observed_inhibitor_order_low_to_high']=sorted(DRUGS,key=lambda d:means[d]['11'])
  prep['predicted_inhibitor_orders_low_to_high']={k:sorted(DRUGS,key=lambda d:prep['targets'][d]['predictions'][k]) for k in ['H_gain','B_add','B_const','B_control']}
out['usage']={'wall_seconds':time.perf_counter()-T0,'cpu_seconds':time.process_time()-C0,'network_calls':0,'external_API_calls':0,'monetary_cost':0}
dest=ROOT/'review'/'source_like_result.json'; dest.write_text(json.dumps(out,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({'frozen_result':str(dest),'sha256':sha(dest),'usage':out['usage'],'MAE':{k:v.get('MAE') for k,v in out['preparations'].items()}},indent=2))
