"""Independent development-result reconstruction; no run imports or parquet decoding."""
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT/'log/20261023/emerald_functional_rule'
def read(name):
    return json.loads((OUT/name).read_text(encoding='utf8'))
plan, result, trials = read('IDENTITY_PLAN.json'), read('RESULT.json'), read('TRIALS.json')
data = np.load(OUT/'DEVELOPMENT.npz')
matrix = data['matrix']
truth = matrix[:,45:]
groups = np.array(plan['query_groups'])
freeze = read('FREEZE.json')
hashes = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==wanted
          for name,wanted in freeze['files'].items()}
assert all(hashes.values())
rows = read('DEVELOPMENT_ROWS.json')
receipt = read('EXPORT_RECEIPT.json')
assert hashlib.sha256((OUT/'DEVELOPMENT_ROWS.json').read_bytes()).hexdigest()==receipt['sha256']
allcells = plan['development']+plan['reserve']
expected = sorted(allcells, key=lambda c:(hashlib.sha256(('emerald-functional-rule-v1|'+c).encode()).hexdigest(),c))
assert expected[:36]==plan['development'] and expected[36:]==plan['reserve']
assert len(set(allcells))==52 and len(set(plan['conditions']))==60
assert len(rows)==2160 and matrix.shape==(36,60)
lookup = {(r['cell_line'],r['condition']):r['growth_rate'] for r in rows}
assert len(lookup)==2160
rebuilt = np.array([[lookup[c,t] for t in plan['conditions']] for c in plan['development']])
assert np.array_equal(rebuilt,matrix) and np.isfinite(matrix).all()
assert set(r['cell_line'] for r in rows)==set(plan['development'])
assert not (set(r['cell_line'] for r in rows)&set(plan['reserve']))
assert set(r['condition'] for r in rows)==set(plan['conditions'])

def metrics(pred):
    mse = np.empty((36,7))
    regret = np.empty((36,7))
    for i in range(36):
        for pair in range(7):
            ids = [j for j,g in enumerate(groups) if g==pair]
            mse[i,pair] = sum((truth[i,j]-pred[i,j])**2 for j in ids)/len(ids)
            chosen = min(ids,key=lambda j:(pred[i,j],j))
            regret[i,pair] = truth[i,chosen]-min(truth[i,j] for j in ids)
    return {'mse':float(mse.mean()), 'regret':float(regret.mean()),
            'per_pair_mse':mse.mean(axis=0).tolist(),'per_pair_regret':regret.mean(axis=0).tolist(),
            'per_context_mse':mse.mean(axis=1).tolist(),'per_context_regret':regret.mean(axis=1).tolist()}

errors = []
computed = {}
for arm in ['single_only','single_plus_anchor','source_mean']:
    computed[arm] = metrics(data[arm])
    for name,value in computed[arm].items():
        errors.append(float(np.max(np.abs(np.asarray(value)-np.asarray(result['metrics'][arm][name])))))
baseline = np.stack([np.mean(np.delete(truth,i,axis=0),axis=0) for i in range(36)])
baseline_error = float(np.max(np.abs(baseline-data['source_mean'])))
single, anchor = computed['single_only'], computed['single_plus_anchor']
wins = sum(b<a for a,b in zip(single['per_pair_mse'],anchor['per_pair_mse']))
gate = anchor['mse']<single['mse'] and anchor['regret']<single['regret'] and wins>=4
assert wins==result['pair_wins'] and gate==result['gate']
assert result['decision']==('ORDINARY_INFORMATION_SIGNAL' if gate else 'STOP_FIXED_SINGLE_PLUS_ONE_ANCHOR')
assert result['counters']=={'inner_program_fits':3240,'outer_fits':72}

def independent_fit(x,y,z,program):
    name,amount = program
    ym = np.mean(y,axis=0)
    if name=='mean': return np.repeat(ym[None,:],len(z),axis=0)
    xm = np.mean(x,axis=0)
    if name=='offset': return ym+amount*np.mean(z-xm,axis=1)[:,None]
    scale = np.std(x,axis=0)
    scale[scale==0]=1
    a,b = (x-xm)/scale,(z-xm)/scale
    if name=='linear':
        # Independent primal solve rather than production source-row dual solve.
        u,v = a/np.sqrt(a.shape[1]),b/np.sqrt(a.shape[1])
        coef = np.linalg.solve(u.T@u+amount*np.eye(u.shape[1]),u.T@(y-ym))
        return ym+v@coef
    # Independent explicit differences avoids production norm-expansion formula.
    k = np.exp(-np.mean((a[:,None,:]-a[None,:,:])**2,axis=2)/2)
    q = np.exp(-np.mean((b[:,None,:]-a[None,:,:])**2,axis=2)/2)
    return ym+q@np.linalg.solve(k+amount*np.eye(len(a)),y-ym)

score_error, prediction_error = 0.,0.
selected_counts = {}
outer_records = []
for entry in trials:
    arm = entry['arm']
    width = 44 if arm=='single_only' else 45
    held = plan['development'].index(entry['held_context'])
    src = np.array([j for j in range(36) if j!=held])
    scores = []
    for program in plan['programs']:
        total = 0.
        for fold in range(3):
            va = src[np.arange(35)%3==fold]
            tr = src[np.arange(35)%3!=fold]
            pred = independent_fit(matrix[tr,:width],truth[tr],matrix[va,:width],program)
            for pair in range(7):
                ids = np.flatnonzero(groups==pair)
                total += float(np.mean((truth[va][:,ids]-pred[:,ids])**2,axis=1).sum())/(35*7)
        scores.append(total)
    score_error = max(score_error,float(np.max(np.abs(np.array(scores)-entry['scores']))))
    selected = int(np.argmin(scores))
    assert int(np.argmin(entry['scores']))==entry['selected']==selected
    selected_counts[arm+':'+str(plan['programs'][selected])] = selected_counts.get(arm+':'+str(plan['programs'][selected]),0)+1
    # Audit all selected outer fits, not merely representative cases.
    pred = independent_fit(matrix[src,:width],truth[src],matrix[[held],:width],plan['programs'][selected])[0]
    error = float(np.max(np.abs(pred-data[arm][held])))
    prediction_error = max(prediction_error,error)
    outer_records.append({'arm':arm,'held_context':entry['held_context'],'program':plan['programs'][selected],'max_abs_error':error})
assert len(trials)==72 and max(errors)<1e-12 and baseline_error<1e-12
assert score_error<1e-10 and prediction_error<1e-10
audit = {'status':'PASS','scope':'development export only; no original parquet response decoding or reserve access',
         'freeze_hashes':hashes,'export_hash_valid':True,'export_rows':len(rows),'reserve_exported':False,
         'matrix_exactly_reconstructed':True,'all_metrics_max_abs_error':max(errors),
         'source_mean_max_abs_error':baseline_error,'all_72_selector_argmins_match':True,
         'all_inner_scores_max_abs_error':score_error,'all_selected_outer_predictions_max_abs_error':prediction_error,
         'linear_solver':'independent primal; RBF explicit difference kernel',
         'pair_wins':wins,'gate':gate,'decision':result['decision'],'selected_counts':selected_counts,
         'outer_records':outer_records,'reconstructed_metrics':computed,
         'limitations':['shared-rowgroup decoder guarantee remains logical export only',
                        'source parquet read as opaque bytes for freeze hashing only',
                        'cost counters are checked combinatorially, not independently timed',
                        'local hashes do not authenticate historical authorship or physical assay independence']}
(OUT/'RESULT_AUDIT.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
print(json.dumps({k:v for k,v in audit.items() if k not in ['outer_records','reconstructed_metrics','freeze_hashes']},indent=2))
