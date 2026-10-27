"""Bounded exploratory PRISM replay; never reads historical sealed responses."""
from pathlib import Path
import hashlib
import json
import os
import time

os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
os.environ.setdefault('OMP_NUM_THREADS', '1')
import numpy as np
import pandas as pd
from scipy import sparse
from scipy.special import ndtr
from sklearn.linear_model import Ridge

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
SEED = 20261026


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def dump(name, data):
    (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def order(names):
    return np.argsort([hashlib.sha256(f'{SEED}:{v}'.encode()).hexdigest() for v in names])


def interval(values):
    x = np.asarray(values, float)
    rng = np.random.default_rng(SEED)
    means = np.mean(x[rng.integers(len(x), size=(2000, len(x)))], axis=1)
    return {'mean': float(x.mean()), 'ci95_cells': np.quantile(means, [.025, .975]).tolist(), 'n_cells': len(x)}


def metrics(y, pred):
    chosen = np.argsort(-pred)[:min(3, len(y))]
    return {'mse': float(np.mean((y-pred)**2)), 'utility': float(y[chosen].mean())}


def main():
    started = time.time()
    files = [ROOT / 'data/external/prism_19q4/derived/block_n_prism_open.npz',
             ROOT / 'data/external/prism_19q4/raw/primary-screen-replicate-collapsed-treatment-info.csv',
             ROOT / 'data/external/prism_19q4/raw/primary-screen-cell-line-info.csv']
    dump('FREEZE.json', {'inputs': {str(p.relative_to(ROOT)).replace('\\','/'): sha(p) for p in files + [HERE/'PROTOCOL.md', HERE/'run.py']},
                         'seed': SEED, 'endpoint': '-primary log2 viability', 'independence': 'previously exposed open development data'})
    a = np.load(files[0], allow_pickle=False)
    meta = pd.read_csv(files[1])
    meta = meta[meta.name.isin(a['drug']) & np.isclose(meta.dose, 2.5) & (meta.screen_id == 'HTS') & meta.target.notna() & ~meta.target.str.contains(',', na=False)]
    meta = meta.drop_duplicates('name', keep=False)
    # Distinct chemical strings; no claim of scaffold independence.
    meta = meta.dropna(subset=['smiles']).drop_duplicates(['target', 'smiles'])
    sizes = meta.groupby('target').name.nunique()
    meta = meta[meta.target.isin(sizes[sizes >= 4].index)].sort_values(['target','name']).reset_index(drop=True)
    cm = pd.read_csv(files[2]).set_index('row_name')
    cm = cm[cm.passed_str_profiling.astype(str).str.lower().eq('true') & cm.primary_tissue.notna()]
    counts = cm.primary_tissue.value_counts()
    cm = cm[cm.primary_tissue.isin(counts[counts >= 20].index)]
    cells = [v for v in a['line'] if v in cm.index]
    drugs = meta.name.tolist()
    di = {v:i for i,v in enumerate(a['drug'])}; ci = {v:i for i,v in enumerate(a['line'])}
    Y = -a['primary'][np.ix_([di[v] for v in drugs], [ci[v] for v in cells])].astype(float)
    family, family_names = pd.factorize(meta.target, sort=True)
    tissue, tissue_names = pd.factorize(cm.loc[cells, 'primary_tissue'], sort=True)
    withheld = np.array([idx[order([drugs[j] for j in idx])[-1]] for f in np.unique(family) for idx in [np.flatnonzero(family == f)]])
    known = np.setdiff1d(np.arange(len(drugs)), withheld)
    co = order(cells); ns, nd = int(.6*len(cells)), int(.2*len(cells))
    source, dev, final = co[:ns], co[ns:ns+nd], co[ns+nd:]
    meta.assign(index=np.arange(len(drugs)), family_id=family, withheld=np.isin(np.arange(len(drugs)), withheld)).to_csv(HERE/'drugs.csv', index=False)
    dump('PARTITION.json', {'source_cells': [cells[i] for i in source], 'development_cells':[cells[i] for i in dev], 'evaluation_cells':[cells[i] for i in final],
                            'withheld_drugs':[drugs[i] for i in withheld], 'families':list(family_names), 'shape':list(Y.shape), 'observed':int(np.isfinite(Y).sum())})
    # P0: all observed same-family 2x2 rectangles on open data, functional only.
    census = []
    for f in np.unique(family):
        idx = np.flatnonzero(family == f); z = Y[idx]
        good = np.all(np.isfinite(z), axis=0)
        z = z[:, good]
        # Functional discordance at a pre-fixed 2-fold viability reduction.
        hit = z >= 1.
        mixed = np.any(hit, axis=0) & ~np.all(hit, axis=0)
        census.append({'family':str(family_names[f]), 'drugs':len(idx), 'complete_backgrounds':int(good.sum()),
                       'discordant_backgrounds':int(mixed.sum()), 'all_active':int(np.all(hit,axis=0).sum()), 'all_inactive':int((~np.any(hit,axis=0)).sum()),
                       'mechanism_reference':False})
    dump('P0.json', census)

    # Sparse conventional models with the identical permitted information.
    d, c = np.indices(Y.shape); d, c = d.ravel(), c.ravel()
    def onehot(v, n):
        return sparse.csr_matrix((np.ones(len(v)), (np.arange(len(v)), v)), shape=(len(v), n))
    nf, nt, nc, nk = len(family_names), len(tissue_names), len(cells), len(drugs)
    base = sparse.hstack([onehot(d,nk),onehot(c,nc),onehot(family[d],nf),onehot(tissue[c],nt)], format='csr')
    bg = onehot(family[d]*nc+c,nf*nc)
    compound = onehot(d*nt+tissue[c],nk*nt)
    X = {'refit':base, 'background':sparse.hstack([base,bg],format='csr'), 'compound':sparse.hstack([base,compound],format='csr'),
         'full':sparse.hstack([base,bg,compound],format='csr')}
    finite = np.isfinite(Y.ravel())
    source_mask = np.isin(c,source) & np.isin(d,known) & finite
    feedback = known[order([drugs[j] for j in known])[:8]]
    def fitstage(target_cells):
        train = source_mask | (np.isin(c,target_cells) & np.isin(d,feedback) & finite)
        preds = {}
        for name,x in X.items():
            model = Ridge(alpha=10., solver='lsqr', tol=1e-6, max_iter=1000).fit(x[train],Y.ravel()[train])
            preds[name] = model.predict(x).reshape(Y.shape)
        rows=[]
        for j in target_cells:
            test = withheld[np.isfinite(Y[withheld,j])]
            if len(test)<3: continue
            for name,pred in preds.items():
                rows.append({'cell':cells[j], 'method':name, **metrics(Y[test,j],pred[test,j])})
        return rows
    development = fitstage(dev)
    choice = min(['background','compound'], key=lambda m: np.mean([r['mse'] for r in development if r['method']==m]))
    dump('SELECTION.json', {'revision':choice, 'criterion':'development MSE', 'alpha':10.,'fixed_feedback_drugs':[drugs[j] for j in feedback]})
    rows = fitstage(final)
    pd.DataFrame(development+rows).assign().to_csv(HERE/'rule_metrics.csv',index=False)
    rb = {m:{r['cell']:r for r in rows if r['method']==m} for m in X}
    rule = {'chosen_revision':choice, 'contrasts':{}}
    for baseline in ['refit','full']:
        keys=sorted(set(rb[choice]) & set(rb[baseline]))
        rule['contrasts'][baseline] = {metric:interval([rb[choice][k][metric]-rb[baseline][k][metric] for k in keys]) for metric in ['mse','utility']}
    dump('DIRECTION1.json',rule)

    # Source-only pharmacological similarity kernel, common to every query strategy.
    baseline = np.nanmean(Y[:,source], axis=1)
    profiles = np.where(np.isfinite(Y[:,source]),Y[:,source],baseline[:,None])
    profiles = profiles-profiles.mean(axis=0,keepdims=True)
    dist = np.mean((profiles[:,None,:]-profiles[None,:,:])**2,axis=2)
    scale = max(float(np.median(dist[dist>0])),1e-6)
    kernel = np.exp(-dist/scale)
    noise = .25
    policies = ['random','uncertainty','exploit','counterexample','knowledge_gradient']
    replay=[]; gates=[]; correction=[]; traces=[]
    for phase, target in [('development',dev),('evaluation',final)]:
        for j in target:
            pool=known[np.isfinite(Y[known,j])]; test=withheld[np.isfinite(Y[withheld,j])]
            if len(pool)<8 or len(test)<3: continue
            fam_base=np.array([np.mean(baseline[family==f]) for f in family])
            # Source standard deviation is a fixed score, not a calibrated conditional risk.
            sd=np.nanstd(Y[:,source],axis=1)
            rank=test[np.argsort(sd[test])]; kept=rank[:max(1,len(rank)//2)]
            rng=np.random.default_rng(SEED+j)
            rand=rng.choice(test,len(kept),replace=False)
            for method,sub in [('uncertainty',kept),('random',rand)]:
                err=np.abs(Y[sub,j]-baseline[sub])
                gates.append({'phase':phase,'cell':cells[j],'method':method,'coverage':len(sub)/len(test),'mse':float(np.mean(err**2)),
                              'wrong_confident_fraction':float(np.mean(err>1.))})
            for policy in policies:
                mean=baseline.copy(); cov=kernel.copy(); queried=[]
                rng=np.random.default_rng(SEED+j)
                fixed=pool[order([drugs[k] for k in pool])[:8]]
                for step in range(8):
                    available=np.setdiff1d(pool,queried)
                    var=np.diag(cov)[available]+noise
                    if policy=='random': pick=int(rng.choice(available))
                    elif policy=='uncertainty': pick=int(available[np.argmax(var)])
                    elif policy=='exploit': pick=int(available[np.argmax(mean[available])])
                    elif policy=='counterexample': pick=int(available[np.argmax(np.abs(mean[available]-fam_base[available]))])
                    else:
                        # One-step MC knowledge gradient for best top3 final decision.
                        normals=np.random.default_rng(SEED+step).standard_normal(32)
                        gain=[]
                        for k in available:
                            possible=mean[test,None]+cov[test,k,None]/np.sqrt(cov[k,k]+noise)*normals
                            gain.append(float(np.mean(np.sort(possible,axis=0)[-3:])) )
                        pick=int(available[np.argmax(gain)])
                    traces.append({'phase':phase,'cell':cells[j],'policy':policy,'step':step,'drug':drugs[pick]})
                    v=cov[:,pick].copy(); denom=cov[pick,pick]+noise
                    mean=mean+v/denom*(Y[pick,j]-mean[pick]); cov=cov-np.outer(v,v)/denom
                    queried.append(pick)
                replay.append({'phase':phase,'cell':cells[j],'policy':policy,'queries':len(set(queried)),**metrics(Y[test,j],mean[test])})
                if policy=='random':
                    # Same actual random feedback, compare update mechanisms.
                    shift=float(np.mean(Y[queried,j]-baseline[queried]))
                    for name,pred in [('static',baseline[test]),('global_bias',baseline[test]+shift),('gp_update',mean[test])]:
                        correction.append({'phase':phase,'cell':cells[j],'method':name,**metrics(Y[test,j],pred)})
    pd.DataFrame(replay).to_csv(HERE/'replay_metrics.csv', index=False)
    pd.DataFrame(traces).to_csv(HERE/'query_trace.csv', index=False)
    pd.DataFrame(gates).to_csv(HERE/'gate_metrics.csv', index=False)
    pd.DataFrame(correction).to_csv(HERE/'correction_metrics.csv', index=False)
    def compare(records,field,ours,theirs,metric):
        l={r['cell']:r[metric] for r in records if r['phase']=='evaluation' and r[field]==ours}
        r={r['cell']:r[metric] for r in records if r['phase']=='evaluation' and r[field]==theirs}
        return interval([l[k]-r[k] for k in sorted(l.keys() & r.keys())])
    best=max(policies,key=lambda p:np.mean([r['utility'] for r in replay if r['phase']=='development' and r['policy']==p]))
    # Three generations examine the same fixed candidates. No evaluator mutation.
    generations=[]
    incumbent='random'
    for generation,candidates in enumerate([['random','uncertainty'],['exploit','counterexample'],['knowledge_gradient']],1):
        incumbent=max([incumbent]+candidates,key=lambda p:np.mean([r['utility'] for r in replay if r['phase']=='development' and r['policy']==p]))
        generations.append({'generation':generation,'incumbent':incumbent})
    dump('REPLAY_SUMMARY.json', {
        'direction2':{p:compare(replay,'policy','counterexample',p,'utility') for p in policies if p!='counterexample'},
        'direction3':{p:{m:compare(correction,'method','gp_update',p,m) for m in ['utility','mse']} for p in ['static','global_bias']},
        'direction6':{'selected_policy':best,'contrasts':{p:compare(replay,'policy',best,p,'utility') for p in policies if p!=best},'independent_mechanism_tasks':0},
        'direction7':{m:compare(gates,'method','uncertainty','random',m) for m in ['mse','wrong_confident_fraction','coverage']},
        'direction8':{'generations':generations,'one_shot_winner':best,'same_search_result':incumbent==best,'generated_new_programs':0,
                      'contrast_to_one_shot':compare(replay,'policy',incumbent,best,'utility')},
        'kernel':{'type':'RBF source response profiles','scale':scale,'observation_noise_variance':noise},
        'limits':['no molecular mechanism ground truth','no physical cost audit','no independent screen confirmation','no LLM execution','finite MC KG, not full BAX or DAD reproduction']})
    dump('RUN_RECEIPT.json',{'completed':True,'elapsed_seconds':time.time()-started,'n_drugs':len(drugs),'n_cells':len(cells),
                             'n_replay_rows':len(replay),'n_queries':len(traces),'source_hashes_after':{str(p.relative_to(ROOT)):sha(p) for p in files}})
    print(json.dumps({'completed':True,'drugs':len(drugs),'cells':len(cells),'replay_rows':len(replay),'seconds':time.time()-started}))


if __name__ == '__main__':
    main()
