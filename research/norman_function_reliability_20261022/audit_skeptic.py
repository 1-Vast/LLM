"""Independent saved-output arithmetic audit; no fitting or raw/protected reads."""
import hashlib
import json
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.stats import spearmanr
root = Path(__file__).resolve().parents[2]
p = root / 'log/20261022/norman_function_reliability'
d = pd.read_csv(p/'OOF_SOURCE.csv')
m = pd.read_csv(p/'MOMENTS.csv').set_index('model')
f = pd.read_csv(p/'FOLD_SCORES.csv')
s = json.loads((p/'SELECTIONS.json').read_text())
c = json.loads((p/'COSTS.json').read_text())
assert len(d)==d.pair.nunique()==3160
assert len(c)==90 and len(s)==20
assert all(int.from_bytes(hashlib.sha256(('MAESTRO_NORMAN_RELIABILITY_V1|'+x.pair).encode()).digest()[:8],'big')%5==x.fold for x in d.itertuples())
errors=[]
for name,row in m.iterrows():
    pred=d['prediction_'+name].to_numpy()
    e1=d.replicate1.to_numpy()-pred; e2=d.replicate2.to_numpy()-pred
    diff=d.replicate1.to_numpy()-d.replicate2.to_numpy()
    vals={'growth_mse':np.mean((d.growth-pred)**2),'replicate_mean_mse':np.mean(((d.replicate1+d.replicate2)/2-pred)**2),'residual_cross_product':np.mean(e1*e2),'replicate_difference_moment_div4':np.mean(diff**2)/4,'replicate1_residual_mean':e1.mean(),'replicate2_residual_mean':e2.mean(),'centered_residual_correlation':np.corrcoef(e1,e2)[0,1],'absolute_error_vs_absolute_disagreement_spearman':spearmanr(abs(d.growth-pred),abs(diff)).statistic}
    errors.extend(abs(float(row[k])-float(v)) for k,v in vals.items())
    assert abs(vals['replicate_mean_mse']-vals['residual_cross_product']-vals['replicate_difference_moment_div4'])<1e-14
    for _,fr in f[f.model.eq(name)].iterrows():
        mask=d.fold.eq(fr['fold'])
        errors.append(abs(np.mean((d.growth[mask]-pred[mask])**2)-fr.heldout_growth_mse))
for selection in s:
    train=set(selection['inner_train_pairs']); validation=set(selection['inner_validation_pairs'])
    held=set(d.loc[d.fold.eq(selection['fold']),'pair'])
    assert not train&validation and not (train|validation)&held
    assert train|validation==set(d.pair)-held
    assert len(selection['candidates'])==3
    assert selection['selected_parameter']==min(selection['candidates'],key=lambda x:x['mse'])['parameter']
    assert selection['outer_refit'].get('converged',True)
report={'status':'PASS_SAVED_OUTPUT_ARITHMETIC','rows':len(d),'fits':len(c),'selections':len(s),'max_absolute_recomputed_error':max(errors),'selected_nuclear_stop_unmet':sum(not x['outer_refit'].get('converged',True) for x in s),'scope':'Saved source OOF arithmetic and selection audit; no independent model refit or causal/noise identification'}
assert max(errors)<1e-12
(p/'skeptic/RESULT_AUDIT.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
