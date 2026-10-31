"""One staged, research-local comparison. Importing does not access response data."""
import csv
import gzip
import hashlib
import json
from pathlib import Path
import pickle
import sys

import numpy as np
from scipy.special import boxcox, inv_boxcox
from scipy.stats import spearmanr
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge

EP = Path(__file__).resolve().parent
ROOT = EP.parents[3]
COUNTS = ROOT/'data/external/conditional_interventions_20261030/egi/15_GI_expt2_counts.txt.gz'
GUIDES = EP.parent/'2026-10-31-regulatory-functional-dynamics/egi_admission/guide_identity.tsv'
COUNT_SHA = 'f9f5c85fc81e366709fd5d42f1c3c85388f00ab19624e14ebede53f72e09080b'
GUIDE_SHA = '9adbe2671aa6d422f394016677b4f944c9347eacfb8bc6acb07a2b0ba184ea78'
GRID = np.round(np.arange(41)/20, 2)
PS = [1., .5, 2.]
MODELS = ['coordinate', 'zero', 'source_mean', 'ridge', 'boosting']
EXPECTED_HEADER = ['double','t0_r1','t0_r2','dmso_r1','dmso_r2','etop_r1','etop_r2','keto_r1','keto_r2']


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def fold(a, b):
    a, b = sorted((a, b))
    return int(hashlib.sha256(f'MAESTRO-I054-v1|{a}|{b}'.encode()).hexdigest()[:8], 16) % 10


def transform(y, lam):
    y = np.asarray(y, dtype=float)
    return np.where(y >= 0, boxcox(1+np.maximum(y, 0), lam),
                    -boxcox(1+np.maximum(-y, 0), 2-lam))


def inverse(z, lam):
    z = np.asarray(z, dtype=float)
    return np.where(z >= 0, inv_boxcox(np.maximum(z, 0), lam)-1,
                    1-inv_boxcox(np.maximum(-z, 0), 2-lam))


def count_value(text):
    if text.strip()=='':
        return np.nan
    value = float(text)
    assert np.isfinite(value) and value>=0 and value.is_integer()
    return value


def read_counts(scoring=False):
    assert sha(COUNTS) == COUNT_SHA and sha(GUIDES) == GUIDE_SHA
    rows = list(csv.DictReader(GUIDES.open(encoding='utf-8'), delimiter='\t'))
    names = [r['guide_identity'] for r in rows]
    lookup = {name:i for i,name in enumerate(names)}
    ntc = np.array([i for i,r in enumerate(rows) if r['is_ntc'] == 'True'])
    assert len(names) == 638 and len(ntc) == 13
    c = np.full((2,4,len(names),len(names)), np.nan)
    decoded = np.zeros(c.shape,dtype=bool)
    # Forbidden endpoint strings are tokenized by CSV but never converted, displayed or used.
    with gzip.open(COUNTS, 'rt', encoding='utf-8', newline='') as stream:
        reader = csv.reader(stream)
        assert next(reader) == EXPECTED_HEADER
        seen = set()
        for fields in reader:
            first, second = fields[0].split(':')
            a,b = lookup[first],lookup[second]
            assert (a,b) not in seen
            seen.add((a,b))
            single = a in ntc or b in ntc
            ga,gb = rows[a]['analysis_gene_label'],rows[b]['analysis_gene_label']
            source_allowed = single or (ga != gb and fold(ga,gb) <= 7)
            for r in range(2):
                c[r,0,a,b] = count_value(fields[1+r])
                c[r,1,a,b] = count_value(fields[3+r])
                decoded[r,:2,a,b] = True
                if scoring or source_allowed:
                    c[r,2,a,b] = count_value(fields[5+r])
                    decoded[r,2,a,b] = True
                if scoring or single:
                    c[r,3,a,b] = count_value(fields[7+r])
                    decoded[r,3,a,b] = True
        assert len(seen) == len(names)**2
    finite = c[decoded]
    assert np.isfinite(finite[~np.isnan(finite)]).all()
    finite = finite[~np.isnan(finite)]
    assert (finite >= 0).all() and np.equal(finite,np.floor(finite)).all()
    return c, rows, ntc


def design(c, rows, ntc):
    mask = (c[:,0] >= 30).all(axis=0) & np.isfinite(c[:,1]).all(axis=0)
    single_positions = np.isin(np.arange(len(rows)),ntc)[:,None] | np.isin(np.arange(len(rows)),ntc)[None,:]
    paid_control_complete = np.isfinite(c[:,1:]).all(axis=(0,1))
    mask &= (~single_positions) | paid_control_complete
    assert mask[np.ix_(ntc,ntc)].sum() >= 25
    good = (mask[:,ntc].sum(1) >= 5) & (mask[ntc,:].sum(0) >= 5)
    by_gene = {}
    for i,row in enumerate(rows):
        if i not in ntc:
            by_gene.setdefault(row['analysis_gene_label'],[]).append(i)
    genes = sorted(g for g,v in by_gene.items() if len(v)==2 and good[v].all())
    groups = [np.array(by_gene[g]) for g in genes]
    pairs, slots = [], np.full(mask.shape,-1,dtype=int)
    for i,a in enumerate(groups):
        for j in range(i+1,len(groups)):
            b = groups[j]
            if mask[np.ix_(a,b)].sum()+mask[np.ix_(b,a)].sum() < 4:
                continue
            if min(mask[np.ix_(a,b)].sum(),mask[np.ix_(b,a)].sum()) < 1:
                continue
            n = len(pairs)
            pairs.append((i,j))
            slots[np.ix_(a,b)] = slots[np.ix_(b,a)] = n
    pairs = np.array(pairs,dtype=int)
    folds = np.array([fold(genes[a],genes[b]) for a,b in pairs])
    active = mask & (slots >= 0)
    ids = slots[active]
    n_const = np.bincount(ids,minlength=len(pairs))
    assert len(pairs) >= 10000 and (folds >= 8).sum() >= 1000
    return mask, genes, groups, pairs, folds, slots, active, ids, n_const


def aggregate(matrix, active, ids, n_const):
    return np.bincount(ids,weights=matrix[active],minlength=len(n_const))/n_const


def controls(matrix, mask, ntc):
    z = np.where(mask,matrix,np.nan)
    return np.nanmean(z[:,ntc],axis=1),np.nanmean(z[ntc,:],axis=0),np.nanmean(z[np.ix_(ntc,ntc)])


def endpoint(c, condition, p, mask, ntc):
    lr = np.log2((c[condition]+p)/(c[0]+p))
    return lr-controls(lr,mask,ntc)[2]


def q_label(c, condition, p, mask, ntc):
    delta = np.log2((c[condition]+p)/(c[1]+p))
    a,b,n = controls(delta,mask,ntc)
    return delta-a[:,None]-b[None,:]+n


def predict_matrix(ut, target, lam, mask, ntc):
    a0,b0,n0 = controls(transform(ut,lam),mask,ntc)
    ae,be,ne = controls(transform(target,lam),mask,ntc)
    predicted = inverse(transform(ut,lam)+ae[:,None]-a0[:,None]+be[None,:]-b0[None,:]-ne+n0,lam)
    raw_a,raw_b,raw_n = controls(target-ut,mask,ntc)
    q = predicted-ut-raw_a[:,None]-raw_b[None,:]+raw_n
    return q,predicted


def stats(x):
    x = np.asarray(x)
    x = x[np.isfinite(x)]
    return np.r_[x.mean(),x.std(),np.quantile(x,[0,.25,.5,.75,1])]


def features(qgrid, ut, target, groups, pairs, mask, ntc, agg):
    gene = []
    for guides in groups:
        values = []
        for y in (ut,target):
            z = np.where(mask,y,np.nan)
            values.extend(stats(np.r_[z[np.ix_(guides,ntc)].ravel(),z[np.ix_(ntc,guides)].ravel()]))
        gene.append(values)
    gene = np.asarray(gene)
    a,b = gene[pairs[:,0]],gene[pairs[:,1]]
    context = np.r_[stats(np.where(mask,ut,np.nan)[np.ix_(ntc,ntc)]),
                    stats(np.where(mask,target,np.nan)[np.ix_(ntc,ntc)])]
    return np.column_stack([qgrid,agg(ut),a+b,np.abs(a-b),a*b,np.tile(context,(len(pairs),1))])


def supported(ut,target,predicted,bounds,mask,ntc,agg):
    lo,hi = bounds
    inside = lambda x: np.isfinite(x) & (x >= lo) & (x <= hi)
    good_row = ((~mask[:,ntc]) | (inside(ut[:,ntc]) & inside(target[:,ntc]))).all(1)
    good_col = ((~mask[ntc,:]) | (inside(ut[ntc,:]) & inside(target[ntc,:]))).all(0)
    good_ntc = ((~mask[np.ix_(ntc,ntc)]) | (inside(ut[np.ix_(ntc,ntc)]) & inside(target[np.ix_(ntc,ntc)]))).all()
    z = inside(ut) & inside(predicted) & good_row[:,None] & good_col[None,:] & good_ntc
    return agg(z.astype(float)) == 1


def save_json(path, value):
    Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def fit():
    out = EP/'run_repaired'
    out.mkdir(exist_ok=False)
    c,rows,ntc = read_counts()
    mask,genes,groups,pairs,folds,slots,active,ids,n_const = design(c,rows,ntc)
    agg = lambda x: aggregate(x,active,ids,n_const)
    source_labels = np.array([agg(q_label(c[r],2,1.,mask,ntc)) for r in range(2)])
    source_observed = np.isfinite(source_labels).all(0)
    train,val,test = (folds<=6)&source_observed,(folds==7)&source_observed,folds>=8
    assert train.any() and val.any()
    train_construct = active & np.isin(slots,np.flatnonzero(train))
    depth = np.mean([agg(c[r,0]) for r in range(2)],axis=0)
    depth_edges = np.quantile(depth[train],[.25,.5,.75])
    depth_strata = np.searchsorted(depth_edges,depth)
    prediction = np.empty((3,2,2,len(MODELS),len(pairs)))
    support = np.empty((3,2,2,len(pairs)),dtype=bool)
    compatible_spread = np.empty((2,len(pairs)))
    selected = {}
    for p_index,p in enumerate(PS):
        ys = np.array([[endpoint(c[r],j,p,mask,ntc) for j in (1,2,3)] for r in range(2)])
        qgrid = np.empty((2,2,len(pairs),len(GRID)))
        xs = [[None,None],[None,None]]
        source_y = np.array([agg(q_label(c[r],2,p,mask,ntc)) for r in range(2)])
        bounds,occupancy = [],[]
        for r in range(2):
            inputs = np.r_[ys[r,0][train_construct],ys[r,1][train_construct]]
            # Add every allowed single/control input used by the source mechanism.
            single_mask = mask & (np.isin(np.arange(mask.shape[0]),ntc)[:,None] | np.isin(np.arange(mask.shape[0]),ntc)[None,:])
            inputs = np.r_[inputs,ys[r,0][single_mask],ys[r,1][single_mask]]
            inputs = inputs[np.isfinite(inputs)]
            bounds.append([float(inputs.min()),float(inputs.max())])
            occupancy.append(np.quantile(inputs,[0,.01,.05,.25,.5,.75,.95,.99,1]).tolist())
            for condition in range(2):
                for l,lam in enumerate(GRID):
                    q,pred_y = predict_matrix(ys[r,0],ys[r,condition+1],lam,mask,ntc)
                    qgrid[condition,r,:,l] = agg(q)
                assert np.allclose(qgrid[condition,r,:,20],0,atol=1e-10)
                qgrid[condition,r,:,20] = 0
                xs[condition][r] = features(qgrid[condition,r],ys[r,0],ys[r,condition+1],groups,pairs,mask,ntc,agg)
        assert np.isfinite(qgrid).all()
        if p_index == 0:
            culture_profiles = np.mean((qgrid[0][:,val,:]-source_y[:,val][...,None])**2,axis=1)
            profile = culture_profiles.mean(axis=0)
            choice = min(range(len(GRID)),key=lambda k:(profile[k],abs(GRID[k]-1),GRID[k]))
            lam = float(GRID[choice])
            compatible = profile <= 1.01*profile.min()
            train_x = np.concatenate([xs[0][r][train] for r in range(2)])
            train_y = source_y[:,train].ravel()
            val_x = np.concatenate([xs[0][r][val] for r in range(2)])
            val_y = source_y[:,val].ravel()
            mean,sd = train_x.mean(0),train_x.std(0)
            sd = np.where(sd>0,sd,1)
            fitted = []
            for name,settings in [('ridge',[1,100,10000]),('boosting',[7,15])]:
                models,losses = [],[]
                for setting in settings:
                    if name == 'ridge':
                        model = Ridge(alpha=setting).fit((train_x-mean)/sd,train_y)
                        pred = model.predict((val_x-mean)/sd)
                    else:
                        model = HistGradientBoostingRegressor(max_leaf_nodes=setting,l2_regularization=10,
                            max_iter=150,learning_rate=.05,random_state=20261031,early_stopping=False).fit(train_x,train_y)
                        pred = model.predict(val_x)
                    models.append(model)
                    losses.append(float(np.mean((pred-val_y)**2)))
                best = int(np.argmin(losses))
                fitted.append(models[best])
                selected[name] = {'settings':settings,'validation_mse':losses,'selected':settings[best]}
            source_mean = float(train_y.mean())
            selected.update(lambda_selected=lam,lambda_profile=profile.tolist(),
                            lambda_compatible=GRID[compatible].tolist(),source_mean=source_mean,
                            lambda_culture_validation_profiles=culture_profiles.tolist())
            compatible_spread[:] = np.ptp(qgrid[1][:,:,compatible],axis=2)
        diagnostics = []
        for condition in range(2):
            for r in range(2):
                x = xs[condition][r]
                prediction[p_index,condition,r,0] = qgrid[condition,r,:,choice]
                prediction[p_index,condition,r,1] = 0
                prediction[p_index,condition,r,2] = source_mean
                prediction[p_index,condition,r,3] = fitted[0].predict((x-mean)/sd)
                prediction[p_index,condition,r,4] = fitted[1].predict(x)
                q,pred_y = predict_matrix(ys[r,0],ys[r,condition+1],lam,mask,ntc)
                support[p_index,condition,r] = supported(ys[r,0],ys[r,condition+1],pred_y,bounds[r],mask,ntc,agg)
                lo,hi = bounds[r]
                bins = np.unique(occupancy[r])
                v = pred_y[active]
                inverse_slope = np.where(v>=0,(1+np.maximum(v,0))**(1-lam),(1+np.maximum(-v,0))**(lam-1))
                diagnostics.append({'condition':condition,'culture':r,'range':bounds[r],
                    'source_quantiles':occupancy[r],'predicted_histogram':np.histogram(v,bins=bins)[0].tolist(),
                    'predicted_outside_range_fraction':float(np.mean((v<lo)|(v>hi))),
                    'allowed_input_histogram':np.histogram(np.r_[ys[r,0][active],ys[r,0][single_mask],ys[r,condition+1][single_mask]],bins=bins)[0].tolist(),
                    'allowed_input_outside_range_fraction':float(np.mean((np.r_[ys[r,0][active],ys[r,0][single_mask],ys[r,condition+1][single_mask]]<lo)|(np.r_[ys[r,0][active],ys[r,0][single_mask],ys[r,condition+1][single_mask]]>hi))),
                    'inverse_sensitivity_quantiles':np.quantile(inverse_slope,[0,.5,.9,.99,1]).tolist()})
        selected[f'p{p}_support_diagnostics'] = diagnostics
    assert np.isfinite(prediction).all()
    np.savez_compressed(out/'predictions.npz',predictions=prediction,supported=support,pairs=pairs,folds=folds,
                        genes=np.array(genes),depth_strata=depth_strata,compatible_spread=compatible_spread)
    t0_pass = (c[:,0]>=30).all(0)
    ut_complete = t0_pass & np.isfinite(c[:,1]).all(0)
    selected['input_mask_counts'] = {'t0_only':int(t0_pass.sum()),'after_UT_complete':int(ut_complete.sum()),
        'after_common_paid_controls':int(mask.sum()),'UT_missing_removed':int((t0_pass&~ut_complete).sum()),
        'paid_control_missing_removed':int((ut_complete&~mask).sum())}
    selected['source_development_unobservable_by_culture'] = [int(((folds<=7)&~np.isfinite(source_labels[r])).sum()) for r in range(2)]
    selected.update(genes=len(genes),pairs=len(pairs),train=int(train.sum()),validation=int(val.sum()),test=int(test.sum()),
                    retained_constructs=int(mask.sum()),depth_strata_boundaries=depth_edges.tolist(),
                    culture_training='Both source ancestries; neither culture is an independent training holdout',
                    source_train_unobservable=int(((folds<=6)&~source_observed).sum()),
                    source_validation_unobservable=int(((folds==7)&~source_observed).sum()),
                    original_input_support='Fixed T0/UT plus common available paid single-control inputs; target pair labels never select prediction mask')
    save_json(out/'source_fit.json',selected)
    (out/'fitted_models.pkl').write_bytes(pickle.dumps({'models':fitted,'feature_mean':mean,'feature_sd':sd}))
    save_json(out/'prediction_manifest.json',{'count_sha256':COUNT_SHA,'guide_sha256':GUIDE_SHA,
        'experiment_sha256':sha(__file__),'protocol_sha256':sha(EP/'protocol_v5.md'),
        'files':{name:sha(out/name) for name in ['predictions.npz','source_fit.json','fitted_models.pkl']},
        'access':'No glucose doubles or held ETOP doubles numerically decoded before this manifest'})
    print(json.dumps({'stage':'predictions_frozen','lambda':selected['lambda_selected'],'pairs':len(pairs)}),flush=True)


def summary(y,p):
    difference = p-y
    pearson = float(np.corrcoef(y,p)[0,1]) if np.std(p)>0 and np.std(y)>0 else None
    rho = float(spearmanr(y,p).statistic) if np.std(p)>0 and np.std(y)>0 else None
    return {'mse':float(np.mean(difference**2)),'mae':float(np.mean(np.abs(difference))),
            'pearson':pearson,'spearman':rho,'error_quantiles':np.quantile(difference,[0,.01,.1,.5,.9,.99,1]).tolist()}


def score():
    out = EP/'run_repaired'
    assert not (out/'results.json').exists()
    manifest = json.loads((out/'prediction_manifest.json').read_text())
    assert manifest['experiment_sha256']==sha(__file__) and manifest['protocol_sha256']==sha(EP/'protocol_v5.md')
    for name,value in manifest['files'].items():
        assert sha(out/name)==value
    saved = np.load(out/'predictions.npz',allow_pickle=False)
    pred,support,pairs,folds,genes = [saved[k] for k in ['predictions','supported','pairs','folds','genes']]
    test = folds>=8
    c,rows,ntc = read_counts(scoring=True)
    mask,current_genes,groups,current_pairs,current_folds,slots,active,ids,n_const = design(c,rows,ntc)
    assert np.array_equal(genes,current_genes) and np.array_equal(pairs,current_pairs) and np.array_equal(folds,current_folds)
    agg = lambda x: aggregate(x,active,ids,n_const)
    labels = np.array([[[agg(q_label(c[r],condition,p,mask,ntc)) for r in range(2)] for condition in (2,3)] for p in PS])
    observed = np.isfinite(labels).all(axis=2)
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


if __name__=='__main__':
    np.seterr(over='raise',invalid='raise',divide='raise')
    {'fit':fit,'score':score}[sys.argv[1]]()
