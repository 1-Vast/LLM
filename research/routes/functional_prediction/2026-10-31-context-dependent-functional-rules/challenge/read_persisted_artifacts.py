"""Read-only arithmetic review of completed arrays; never imports experiment code."""
from pathlib import Path
import hashlib
import json
import numpy as np

EP = Path(__file__).resolve().parent.parent
RUN = EP/'run_repaired'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
manifest = json.loads((RUN/'prediction_manifest.json').read_text())
freeze = json.loads((EP/'numeric_freeze_v5.json').read_text())
assert sha(EP/'numeric_freeze_v5.json') == '2b86e5d5d1b10a244fd84b202ee839ae7440810cfc0add0fc7c39faff26dac52'
assert manifest['experiment_sha256'] == sha(EP/'experiment_v5.py') == freeze['files'][str(EP/'experiment_v5.py')]['sha256']
assert manifest['protocol_sha256'] == sha(EP/'protocol_v5.md') == freeze['files'][str(EP/'protocol_v5.md')]['sha256']
for name, value in manifest['files'].items():
    assert sha(RUN/name) == value
p = np.load(RUN/'predictions.npz', allow_pickle=False)
l = np.load(RUN/'scored_labels.npz', allow_pickle=False)
pred, y, observed = p['predictions'], l['labels'], l['matched_observed']
assert pred.shape[:4] == (3,2,2,5) and y.shape == pred.shape[:3]+pred.shape[4:]
assert observed.shape == (3,2,pred.shape[-1])
assert np.array_equal(observed, np.isfinite(y).all(axis=2))
assert np.allclose(l['paired_squared_losses'], (pred-y[:,:,:,None,:])**2, equal_nan=True)
assert np.isfinite(pred).all()
test = p['folds'] >= 8
models = ['coordinate','zero','source_mean','ridge','boosting']
out = {'scope':'Post-failure descriptive arithmetic from existing frozen artifacts; pipeline failed',
       'manifest_files_verified':True,'shapes':{k:list(v.shape) for k,v in [('predictions',pred),('labels',y),('matched_observed',observed),('paired_squared_losses',l['paired_squared_losses'])]},
       'test_pairs':int(test.sum()),'scored_labels_sha256':sha(RUN/'scored_labels.npz'),'analyses':[], 'constant_correlation_cases':[]}
out['weak_profile_fraction'] = float(np.mean(p['compatible_spread'][:,test].mean(0)>.5))
for pi, pseudo in enumerate([1.,.5,2.]):
    for ci, condition in enumerate(['etoposide','glucose_deprivation']):
        all_y = y[pi,ci][:,test]
        all_pred = pred[pi,ci][:,:,test]
        available = observed[pi,ci,test]
        yy, pp = all_y[:,available], all_pred[:,:,available]
        full_support = p['supported'][pi,ci][:,test].all(0)
        a = {'p':pseudo,'condition':condition,'matched_pairs':int(available.sum()),'unassessable_pairs':int((~available).sum()),
             'label_coverage':float(available.mean()),'support_fraction':float(full_support.mean()),
             'target_pair_variation':float(np.var(yy,axis=1).mean()),'culture_disagreement':float(np.mean((yy[0]-yy[1])**2)/2),'models':{}}
        strong = (np.abs(all_y)>=1).all(0) & (np.sign(all_y[0])==np.sign(all_y[1])) & available
        for mi, model in enumerate(models):
            loss = (pp[:,mi]-yy)**2
            values = all_pred[:,mi]
            order = np.argsort(-np.abs(values.mean(0)),kind='stable')[:100]
            hit = strong[order] & (np.sign(values.mean(0)[order])==np.sign(all_y[0,order]))
            a['models'][model] = {'mse':float(loss.mean()),'culture_mse':loss.mean(axis=1).tolist(),
                'signed_strong_hits_at100':int(hit.sum()),'assessed_nonhits_at100':int((available[order]&~hit).sum()),
                'unassessable_at100':int((~available[order]).sum()),'observed_label_hit_ceiling':int(min(100,strong.sum()))}
            if pi==0 and (full_support & available).any():
                take = full_support[available]
                a['models'][model]['supported_mse'] = float(loss[:,take].mean())
            for ri in range(2):
                v = pp[ri,mi]
                if np.ptp(v)==0 and np.std(v)>0:
                    out['constant_correlation_cases'].append({'p':pseudo,'condition':condition,'model':model,'culture':ri,'ptp':0.,'std':float(np.std(v))})
            flat = pp[:,mi].ravel()
            if np.ptp(flat)==0 and np.std(flat)>0:
                out['constant_correlation_cases'].append({'p':pseudo,'condition':condition,'model':model,'culture':'pooled','ptp':0.,'std':float(np.std(flat))})
        out['analyses'].append(a)
(EP/'challenge/persisted_artifact_arithmetic.json').write_text(json.dumps(out,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps(out,indent=2,allow_nan=False))
