"""Post-failure read-only arithmetic of saved artifacts, never a model/score rerun."""
import hashlib
import json
from pathlib import Path
import numpy as np

EP = Path(__file__).resolve().parent.parent
RUN = EP/'run_repaired'
manifest = json.loads((RUN/'prediction_manifest.json').read_text())
for name,value in manifest['files'].items():
    assert hashlib.sha256((RUN/name).read_bytes()).hexdigest()==value
saved = np.load(RUN/'predictions.npz',allow_pickle=False)
scored = np.load(RUN/'scored_labels.npz',allow_pickle=False)
source = json.loads((RUN/'source_fit.json').read_text())
pred,label = saved['predictions'],scored['labels']
loss = scored['paired_squared_losses']
assert np.allclose(loss,(pred-label[:,:,:,None,:])**2,equal_nan=True)
assert np.array_equal(scored['matched_observed'],np.isfinite(label).all(axis=2))
test = saved['folds']>=8
models = ['coordinate','zero','source_mean','ridge','boosting']
result = {'original_pipeline_status':'FAILED_JSON_EXPORT_AFTER_SAVING_LABELS_AND_PAIRED_LOSSES',
          'original_pipeline_passed':False,'model_or_score_rerun':False,
          'scope':'Post-failure arithmetic from already frozen predictions and saved labels; observed-subset internal evidence only',
          'source_fit':source,'test_pairs':int(test.sum()),'analyses':[],
          'limitations':['Alternate-pseudocount support and inverse-sensitivity use stale lambda2; excluded from validated claims.',
                         'No refit, raw-count read, scorer rerun, new model selection, or completed original-pipeline claim.',
                         'Correlations, raw-count-floor and coordinate-residual diagnostics are not reproduced here.']}
assert np.isfinite(pred).all()
assert np.array_equal(loss,(pred-label[:,:,:,None,:])**2,equal_nan=True)
assert list(saved['genes']) == sorted(saved['genes'])
assert list(map(tuple,saved['pairs'])) == sorted(map(tuple,saved['pairs']))
for pi,p in enumerate([1,.5,2]):
    for ci,condition in enumerate(['etoposide','glucose_deprivation']):
        available = scored['matched_observed'][pi,ci,test]
        y = label[pi,ci][:,test][:,available]
        pp = pred[pi,ci][:,:,test][:,:,available]
        pair_loss = loss[pi,ci][:,:,test][:,:,available]
        a = {'p':p,'condition':condition,'matched_pairs':int(available.sum()),'label_coverage':float(available.mean()),
             'input_supported_fraction':float(saved['supported'][pi,ci][:,test].all(0).mean()) if pi==0 else None,
             'selected_coordinate_support_validated':pi==0,
             'unassessable_pairs':int((~available).sum()),
             'target_pair_variation':float(np.var(y,axis=1).mean()),'culture_disagreement':float(np.mean((y[0]-y[1])**2)/2),
             'models':{}}
        all_y = label[pi,ci][:,test]
        strong = (np.abs(all_y)>=1).all(0)&(np.sign(all_y[0])==np.sign(all_y[1]))&available
        for m,name in enumerate(models):
            all_p = pred[pi,ci][:,m,:][:,test]
            assert all_p.shape==all_y.shape
            order = np.argsort(-np.abs(all_p.mean(0)),kind='stable')[:100]
            hits = strong[order]&(np.sign(all_p.mean(0)[order])==np.sign(all_y[0,order]))
            a['models'][name]={'mse':float(pair_loss[:,m].mean()),'mse_by_culture':pair_loss[:,m].mean(1).tolist(),
                'mae':float(np.mean(np.abs(pp[:,m]-y))),'hits_at100':int(hits.sum()),
                'assessed_nonhits_at100':int((available[order]&~hits).sum()),'unassessable_at100':int((~available[order]).sum()),
                'observed_label_hit_ceiling':int(min(100,strong.sum()))}
        if pi==0:
            take = saved['supported'][pi,ci][:,test].all(0)[available]
            a['supported_matched_pairs'] = int(take.sum())
            a['supported_models_mse'] = {name:float(pair_loss[:,m,take].mean()) for m,name in enumerate(models)}
        result['analyses'].append(a)
g = next(a for a in result['analyses'] if a['p']==1 and a['condition']=='glucose_deprivation')
e = next(a for a in result['analyses'] if a['p']==1 and a['condition']=='etoposide')
best = min(models[1:],key=lambda n:g['models'][n]['mse'])
result['best_pooled_rival']=best
available = scored['matched_observed'][0,1,test]
target_loss = loss[0,1][:,:,test][:,:,available].mean(0)
pairs = saved['pairs'][test][available]
rng = np.random.default_rng(20261031)
deltas = []
for _ in range(500):
    node = rng.poisson(1,len(saved['genes']))
    weights = node[pairs[:,0]]*node[pairs[:,1]]
    deltas.append(((target_loss[1:]-target_loss[0])*weights).sum(1)/weights.sum())
result['gene_weighted_mse_improvement_intervals']={name:np.quantile(np.array(deltas)[:,i],[.025,.5,.975]).tolist() for i,name in enumerate(models[1:])}
weak = float((saved['compatible_spread'][:,test].mean(0)>.5).mean())
result['source_profile_weak_fraction']=weak
result['arithmetic_gates']={
 'advantage':bool(g['models']['coordinate']['mse']<=.9*min(g['models'][m]['mse'] for m in models[1:])
    and all(g['models']['coordinate']['mse_by_culture'][r]<min(g['models'][m]['mse_by_culture'][r] for m in models[1:]) for r in range(2))
    and result['gene_weighted_mse_improvement_intervals'][best][0]>0),
 'source_held_gain':bool(e['models']['coordinate']['mse']<e['models']['zero']['mse']),
 'signal':bool(g['target_pair_variation']>g['culture_disagreement']),
 'profile':bool(weak<=.1),'input_coverage':bool(g['input_supported_fraction']>=.8),
 'label_coverage':bool(min(g['label_coverage'],e['label_coverage'])>=.8)}
path = EP/'review/post_failure_arithmetic.json'
assert not path.exists()
path.write_text(json.dumps(result,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({'lambda':source['lambda_selected'],'genes':source['genes'],'pairs':source['pairs'],
    'test_pairs':int(test.sum()),'main_analyses':[a for a in result['analyses'] if a['p']==1],
    'best':best,'gates':result['arithmetic_gates'],'profile_weak_fraction':weak,
    'improvement_interval':result['gene_weighted_mse_improvement_intervals'][best]}))
