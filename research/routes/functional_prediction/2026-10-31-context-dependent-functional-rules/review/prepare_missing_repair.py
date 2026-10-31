"""One reviewed schema repair; preserve every failed/prelaunch frozen version."""
from pathlib import Path

EP = Path(__file__).resolve().parent.parent


def once(text,old,new):
    assert text.count(old)==1,old
    return text.replace(old,new)


code = (EP/'experiment_v2.py').read_text(encoding='utf-8')
code = code.replace("EP/'run'","EP/'run_repaired'").replace("EP/'protocol_v2.md'","EP/'protocol_v4.md'")
code = once(code,'def read_counts(scoring=False):',"def count_value(text):\n    return np.nan if text.strip()=='' else float(text)\n\n\ndef read_counts(scoring=False):")
for index in ('1+r','3+r','5+r','7+r'):
    code = code.replace(f'float(fields[{index}])',f'count_value(fields[{index}])')
code = once(code,'assert np.isfinite(finite).all()',"assert np.isfinite(finite[~np.isnan(finite)]).all()")
code = once(code,'assert (finite >= 0).all() and np.equal(finite,np.floor(finite)).all()',
    'finite = finite[~np.isnan(finite)]\n    assert (finite >= 0).all() and np.equal(finite,np.floor(finite)).all()')
code = once(code,'mask = (c[:,0] >= 30).all(axis=0)',
    "mask = (c[:,0] >= 30).all(axis=0) & np.isfinite(c[:,1]).all(axis=0)\n    single_positions = np.isin(np.arange(len(rows)),ntc)[:,None] | np.isin(np.arange(len(rows)),ntc)[None,:]\n    paid_control_complete = np.isfinite(c[:,1:]).all(axis=(0,1))\n    mask &= (~single_positions) | paid_control_complete")
code = once(code,'train,val,test = folds<=6,folds==7,folds>=8',
    "source_labels = np.array([agg(q_label(c[r],2,1.,mask,ntc)) for r in range(2)])\n    source_observed = np.isfinite(source_labels).all(0)\n    train,val,test = (folds<=6)&source_observed,(folds==7)&source_observed,folds>=8\n    assert train.any() and val.any()")
code = once(code,"culture_training='Both source ancestries; neither culture is an independent training holdout')",
    "culture_training='Both source ancestries; neither culture is an independent training holdout',\n                    source_train_unobservable=int(((folds<=6)&~source_observed).sum()),\n                    source_validation_unobservable=int(((folds==7)&~source_observed).sum()),\n                    original_input_support='Fixed T0/UT plus common available paid single-control inputs; target pair labels never select prediction mask')")
start = code.index('    assert np.isfinite(labels).all()',code.index('def score():'))
end = code.index("\n\nif __name__=='__main__':",start)
score_tail = '''    observed = np.isfinite(labels).all(axis=2)
    result = {'models':MODELS,'pseudocounts':PS,'pair_count':int(test.sum()),'analyses':[],
              'interpretation':'Observed-subset internal prediction only; missingness is not established random'}
    for pi,p in enumerate(PS):
        for condition,name in enumerate(['etoposide','glucose_deprivation']):
            all_y = labels[pi,condition][:,test]
            all_predictions = pred[pi,condition][:,:,test]
            available = observed[pi,condition,test]
            assert available.any()
            y = all_y[:,available]
            predictions = all_predictions[:,:,available]
            support_universe = support[pi,condition][:,test].all(0)
            supported_pair = support_universe[available]
            analysis = {'p':p,'condition':name,'supported_fraction':float(support_universe.mean()),
                        'matched_label_coverage':float(available.mean()),'matched_observable_pairs':int(available.sum()),
                        'unassessable_pairs':int((~available).sum()),'supported_observed_fraction':float(supported_pair.mean()),
                        'models':{},'culture_disagreement':float(np.mean((y[0]-y[1])**2)/2),
                        'cross_culture_spearman':float(spearmanr(y[0],y[1]).statistic)}
            strong = (np.abs(all_y)>=1).all(0) & (np.sign(all_y[0])==np.sign(all_y[1])) & available
            for m,model in enumerate(MODELS):
                values = predictions[:,m,:]
                all_values = all_predictions[:,m,:]
                order = np.argsort(-np.abs(all_values.mean(0)),kind='stable')[:100]
                hit = strong[order] & (np.sign(all_values.mean(0)[order])==np.sign(all_y[0,order]))
                entry = {'pooled':summary(y.ravel(),values.ravel()),
                         'cultures':[summary(y[r],values[r]) for r in range(2)],
                         'signed_strong_hits_at100':int(hit.sum()),
                         'assessed_nonhits_at100':int((available[order]&~hit).sum()),
                         'unassessable_at100':int((~available[order]).sum()),
                         'observed_label_hit_ceiling':int(min(100,strong.sum())),
                         'ceiling_scope':'Observed labels only, not the unknown full-universe optimum',
                         'depth_strata':[]}
                if supported_pair.any():
                    entry['supported'] = summary(y[:,supported_pair].ravel(),values[:,supported_pair].ravel())
                for stratum in range(4):
                    take = saved['depth_strata'][test][available]==stratum
                    entry['depth_strata'].append({'stratum':stratum,'pairs':int(take.sum()),
                        'mse':float(np.mean((y[:,take]-values[:,take])**2)) if take.any() else None})
                analysis['models'][model]=entry
            result['analyses'].append(analysis)
    available = observed[0,1,test]
    y = labels[0,1][:,test][:,available]
    predictions = pred[0,1][:,:,test][:,:,available]
    losses = np.mean((predictions-y[:,None,:])**2,axis=0)
    rng = np.random.default_rng(20261031)
    delta = []
    for _ in range(500):
        weight = rng.poisson(1,len(genes))
        w = weight[pairs[test,0][available]]*weight[pairs[test,1][available]]
        assert w.sum()>0
        delta.append(np.sum((losses[1:]-losses[0])*w,axis=1)/w.sum())
    result['gene_weighted_mse_improvement_intervals'] = {MODELS[m]:np.quantile(np.array(delta)[:,m-1],[.025,.5,.975]).tolist() for m in range(1,len(MODELS))}
    result['source_profile_weak_fraction'] = float(np.mean(saved['compatible_spread'][:,test].mean(0)>.5))
    glucose = next(x for x in result['analyses'] if x['p']==1 and x['condition']=='glucose_deprivation')
    source = next(x for x in result['analyses'] if x['p']==1 and x['condition']=='etoposide')
    mse = [glucose['models'][m]['pooled']['mse'] for m in MODELS]
    best = min(range(1,len(MODELS)),key=lambda m:mse[m])
    result['best_pooled_rival']=MODELS[best]
    lower = result['gene_weighted_mse_improvement_intervals'][MODELS[best]][0]
    per_culture = all(glucose['models']['coordinate']['cultures'][r]['mse'] < min(glucose['models'][m]['cultures'][r]['mse'] for m in MODELS[1:]) for r in range(2))
    gate = mse[0] <= .9*min(mse[1:]) and lower>0 and per_culture
    result['target_pair_variation'] = float(np.var(y,axis=1).mean())
    signal = result['target_pair_variation'] > glucose['culture_disagreement']
    identified = result['source_profile_weak_fraction'] <= .1
    coverage = glucose['supported_fraction'] >= .8
    label_coverage = min(glucose['matched_label_coverage'],source['matched_label_coverage']) >= .8
    source_ok = source['models']['coordinate']['pooled']['mse'] < source['models']['zero']['pooled']['mse']
    result['gates']={'advantage':bool(gate),'source_held_pair_gain':bool(source_ok),'signal':bool(signal),
                     'source_profile_diagnostic':bool(identified),'coverage':bool(coverage),'label_coverage':bool(label_coverage)}
    result['decision'] = 'INTERNAL_ADVANTAGE' if all(result['gates'].values()) else ('INCONCLUSIVE' if not (signal and identified and coverage and label_coverage) else 'NO_ADDITIONAL_USEFUL_CAPABILITY')
    low,latent = [],[]
    lam = json.loads((out/'source_fit.json').read_text())['lambda_selected']
    for ci,condition in enumerate((2,3)):
        by_culture,latent_cultures = [],[]
        take = test & observed[0,ci]
        for r in range(2):
            by_culture.append(float(np.mean(agg(((c[r,1]<10)|(c[r,condition]<10)).astype(float))[take]>=.5)))
            ut,target = [endpoint(c[r],j,1.,mask,ntc) for j in (1,condition)]
            a,b,n = controls(transform(target,lam)-transform(ut,lam),mask,ntc)
            residual = agg(transform(target,lam)-transform(ut,lam)-a[:,None]-b[None,:]+n)[take]
            latent_cultures.append(np.quantile(residual,[0,.01,.1,.5,.9,.99,1]).tolist())
        low.append(by_culture)
        latent.append(latent_cultures)
    result['half_constructs_below10_fraction']=low
    result['latent_residual_quantiles']=latent
    np.savez_compressed(out/'scored_labels.npz',labels=labels,matched_observed=observed,
                        paired_squared_losses=(pred-labels[:,:,:,None,:])**2)
    save_json(out/'results.json',result)
    print(json.dumps({'stage':'scored','decision':result['decision'],'gates':result['gates'],'glucose_pooled_mse':dict(zip(MODELS,mse))}),flush=True)
'''
code = code[:start]+score_tail+code[end:]
protocol = (EP/'protocol_v2.md').read_text(encoding='utf-8')
protocol += '''

## V4: the one schema repair after the preserved first launch failure

The admitted v3 run failed after5.594seconds in float('') before fitting or prediction. Original logs, v1-v3 freezes and the empty original run directory remain unchanged. No target double was decoded by this failure. Empty allowed count fields now remain NaN; they are never interpreted as observed zero. Nonempty counts must remain finite nonnegative integers.

Input availability adds finite UT in both cultures to the T0 construct mask. For single/NTC controls ONLY, use a common mask requiring finite paid UT/ETOP/glucose observations in both cultures, preserving identical control identities across the nonlinear and raw contrasts. Target/held-ETOP double missingness never changes this prediction mask. The same two-guide/pair/T0/control thresholds, pair hashes, transform family, primary margin and source-only hyperparameters remain fixed.

Only complete SOURCE-development whole-pair labels in both cultures enter fitting/validation; report unobservable source pairs. A whole-pair label is observable only when every retained construct needed for its fixed average is observed; endpoint-specific averaging is prohibited. Every prediction is still frozen before target double access. At scoring use the same matched observable pair set for every model, preserve all unavailable labels in saved arrays, and report original prediction universe, matched denominators and unassessable counts. Below80% matched-label coverage in source-held or target test forces an inconclusive interpretation. This is an operational coverage gate, not evidence that missingness is random. Any useful result is limited to the observed subset.

Ranking preserves the original100selectedpairs. Report confirmed signed strong hits, assessed nonhits and unassessable selections separately. Missing is not a biological nonhit. The strong-hit ceiling refers only to observed labels, not an unknown full-universe optimum. Count-floor and latent-residual diagnostics report their matched observed denominators. No new family, label imputation, target calibration, or target-based reselection is allowed.

Current executable files are experiment_v4.py/check_arithmetic_v4.py/launcher_v4.py with numeric_freeze_v4.json. This supersedes stale launcher notes above. Remaining aggregate numerical subprocess time is1794.4059999999881seconds (1800 minus the failed5.594seconds), with the same four-logical-CPU affinity and pool limits. This is the sole allowed implementation repair; another failure stops the matrix.
'''
launcher = (EP/'launcher_v3.py').read_text(encoding='utf-8')
launcher = launcher.replace('numeric_freeze_v3.json','numeric_freeze_v4.json').replace('experiment_v2.py','experiment_v4.py')
launcher = launcher.replace("EP/'launch_receipt.json'","EP/'launch_repair_receipt.json'")
launcher = launcher.replace("f'{stage}_stdout.txt'","f'{stage}_repair_stdout.txt'").replace("f'{stage}_stderr.txt'","f'{stage}_repair_stderr.txt'")
launcher = launcher.replace('1800','1794.4059999999881')
check = (EP/'check_arithmetic_v2.py').read_text(encoding='utf-8').replace('experiment_v2 as e','experiment_v4 as e')
check += "\nassert np.isnan(e.count_value('')) and e.count_value('0')==0\n"
freeze = (EP/'review/freeze_numeric_v3.py').read_text(encoding='utf-8').replace('numeric_freeze_v3.json','numeric_freeze_v4.json')
freeze = freeze.replace('protocol_v2.md','protocol_v4.md').replace('experiment_v2.py','experiment_v4.py').replace('check_arithmetic_v2.py','check_arithmetic_v4.py').replace('launcher_v3.py','launcher_v4.py')
for name,text in [('experiment_v4.py',code),('protocol_v4.md',protocol),('launcher_v4.py',launcher),
                  ('check_arithmetic_v4.py',check),('review/freeze_numeric_v4.py',freeze)]:
    path = EP/name
    assert not path.exists(),path
    path.write_text(text,encoding='utf-8')
print('One schema repair prepared; all original files and failed logs preserved.')
