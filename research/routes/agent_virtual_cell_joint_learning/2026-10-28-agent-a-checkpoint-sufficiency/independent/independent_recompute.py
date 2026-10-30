"""Independent protocol-v2 numerical recomputation. No coordinator code imported/read.
Requested model: gpt-6.1-sol/high; effective model unknown.
"""
import os
for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
    os.environ[name] = '1'
import json, hashlib, time, ctypes
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.kernel_ridge import KernelRidge

ROOT = Path(__file__).resolve().parent.parent
OUT = Path(__file__).resolve().parent
SRC = ROOT.parent / '2026-10-28-agent-a-matched-signal-function' / 'sources'
STATIC = ROOT.parent / '2026-10-28-agent-a-mechanism-branches/static_substitution_metadata.json'
MODELS = ('scalar_ridge', 'full_ridge', 'full_rbf', 'partner_mean', 'source_copy')
ALPHAS = [10.0**k for k in range(-4,5)]
KERNEL_GRID = [{'ell': ell, 'lambda': lam} for ell in (0.3,1.,3.) for lam in (0.01,0.1,1.)]
EVENTS = []
FITS = {'loo': 0, 'final': 0}
START = time.perf_counter()

def stamp(event, **kw):
    EVENTS.append({'event': event, 'utc': datetime.now(timezone.utc).isoformat(), **kw})
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def save(name, obj):
    p = OUT / name
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    return sha(p)
def read_json(path):
    stamp('read_allowed_metadata', path=str(path))
    return json.loads(path.read_text(encoding='utf-8-sig'))
def peak_memory():
    from ctypes import wintypes
    class COUNTERS(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD), ('PeakWorkingSetSize', ctypes.c_size_t), ('WorkingSetSize', ctypes.c_size_t), ('QuotaPeakPagedPoolUsage', ctypes.c_size_t), ('QuotaPagedPoolUsage', ctypes.c_size_t), ('QuotaPeakNonPagedPoolUsage', ctypes.c_size_t), ('QuotaNonPagedPoolUsage', ctypes.c_size_t), ('PagefileUsage', ctypes.c_size_t), ('PeakPagefileUsage', ctypes.c_size_t)]
    c = COUNTERS(); c.cb = ctypes.sizeof(c)
    ctypes.windll.kernel32.GetCurrentProcess.restype = wintypes.HANDLE
    assert ctypes.windll.psapi.GetProcessMemoryInfo(ctypes.windll.kernel32.GetCurrentProcess(), ctypes.byref(c), c.cb)
    return int(c.PeakWorkingSetSize)

def normalize(train, target):
    mu = train.mean(axis=0); sd = train.std(axis=0, ddof=0)
    active = sd != 0
    a = np.zeros_like(train); b = np.zeros_like(target)
    a[:, active] = (train[:, active] - mu[active]) / sd[active]
    b[:, active] = (target[:, active] - mu[active]) / sd[active]
    constant = np.flatnonzero(~active).tolist()
    shifted = int(np.count_nonzero(target[:, ~active] != mu[~active]))
    return a, b, {'constant_columns_0based': constant, 'target_shifted_constant_cells': shifted}

def predict(train, delta, target, model, config, phase):
    a,b,diag = normalize(train,target)
    mean = float(delta.mean()); y = delta - mean
    if model in ('scalar_ridge','full_ridge'):
        learner = Ridge(alpha=config, fit_intercept=False, solver='svd')
        pred = learner.fit(a,y).predict(b)
    else:
        def kernel(x,z):
            squared = np.sum((x[:,None,:]-z[None,:,:])**2,axis=2)
            return np.exp(-squared/(2*82*config['ell']**2))
        learner = KernelRidge(alpha=config['lambda'], kernel='precomputed')
        pred = learner.fit(kernel(a,a),y).predict(kernel(b,a))
    FITS[phase] += 1
    return pred + mean, diag

def fit_group(XC, YC, XAC, YAC, XBC, scalar):
    # Only this role-restricted package is accepted. No target Y or global label dictionary.
    x = XAC-XC; target = XBC-XC; d = YAC-YC; n = len(d)
    predictions = {}; grids = {}; selected = {}; constants = {}
    for model in MODELS[:3]:
        cols = [scalar] if model == 'scalar_ridge' else list(range(82))
        tx=x[:,cols]; vx=target[:,cols]
        configs = KERNEL_GRID if model=='full_rbf' else ALPHAS
        entries=[]
        for cfg in configs:
            held=np.empty(n); diagnostics=[]
            for j in range(n):
                mask=np.arange(n)!=j
                p,diag=predict(tx[mask],d[mask],tx[j:j+1],model,cfg,'loo')
                held[j]=p[0]; diagnostics.append(diag)
            entries.append({'config': cfg, 'mse': float(np.mean((held-d)**2)), 'predicted_source_d': held.tolist(), 'fold_constants':diagnostics})
        pick=min(range(len(entries)), key=lambda j:entries[j]['mse'])
        cfg=configs[pick]
        p,diag=predict(tx,d,vx,model,cfg,'final')
        predictions[model]=(YC+p).tolist(); grids[model]=entries
        selected[model]={'grid_index':pick,'config':cfg}; constants[model]=diag
    predictions['partner_mean']=(YC+d.mean()).tolist()
    predictions['source_copy']=YAC.tolist()
    return {'predictions':predictions, 'source_loo':grids,'selected':selected,'final_constants':constants,'source_d_constant':bool(np.all(d==d[0]))}

stamp('script_start', script_sha256=sha(Path(__file__)))
freeze=read_json(ROOT/'input_freeze.json')
mapping=read_json(ROOT/'mapping.json')
static=read_json(STATIC)
allowed=[ROOT/'BRIEF.md',ROOT/'PROTOCOL_v2.md',ROOT/'mapping.json',STATIC,SRC/'q1_pertbio_exp_index.txt',SRC/'q1_pertbio_node_index.txt',SRC/'q1_pertbio_data.txt']
frozen={f['path']:f['sha256'] for f in freeze['files']}
input_hashes={str(p):sha(p) for p in allowed}
assert all(input_hashes[str(p)]==frozen[str(p)] for p in allowed)
labels=[s.split()[0] for s in (SRC/'q1_pertbio_exp_index.txt').read_text().splitlines() if s.strip()]
node_fields=[s.split() for s in (SRC/'q1_pertbio_node_index.txt').read_text().splitlines() if s.strip()]
nodes=[s[0] for s in node_fields]
assert len(labels)==len(set(labels))==89 and len(nodes)==len(set(nodes))==99
assert [i for i,s in enumerate(node_fields) if s[2]=='1']==list(range(82))
assert nodes.index('cellviab')==86
checkpoints=['AKTpS473','MAPKpT202','S6pS240','GSK3abpS21']
assert [nodes.index(s) for s in checkpoints]==[6,2,43,13]
tokens=[frozenset(tuple(part.split('|')) for part in label.split(',')) for label in labels]
assert len(set(tokens))==89
mapped={s['source_index']:s for s in mapping['condition_mapping']}
for row,s in mapped.items():
    assert s['author_label']==labels[row-1] and s['author_index_line_1based']==row
    assert frozenset((t['code'],t['dose_token']) for t in s['author_tokens'])==tokens[row-1]
code={s['S1C_label']:s['author_code'] for s in mapping['drug_code_and_token_mapping']}
roles=[]; source_rows=set(); target_rows=set(); single_rows=set(); pair_rows=set()
for g,checkpoint in zip(static['groups'],checkpoints):
    an,bn=g['implementations']; acode,bcode=code[an],code[bn]
    def candidates(drug, other):
        result={}
        for row in mapped:
            ts=tokens[row-1]
            if len(ts)!=2 or not any(t[0]==drug for t in ts) or any(t[0]==other for t in ts): continue
            partner=next(t for t in ts if t[0]!=drug)
            assert partner not in result
            result[partner]=row
        return result
    left=candidates(acode,bcode); right=candidates(bcode,acode)
    independently_common=set(left)&set(right)
    group=[]
    for c in g['contexts']:
        assert len(c['left_conditions'])==len(c['right_conditions'])==1
        la=c['left_conditions'][0]['source_index']; rb=c['right_conditions'][0]['source_index']
        common=tokens[la-1]&tokens[rb-1]; assert len(common)==1
        partner=next(iter(common)); assert left[partner]==la and right[partner]==rb
        assert partner[0]==code[c['partner']]
        single=tokens.index(frozenset([partner]))+1
        assert single in mapped
        group.append({'partner':c['partner'],'partner_token':list(partner),'C_row':single,'AC_row':la,'BC_row':rb,'C_label':labels[single-1],'AC_label':labels[la-1],'BC_label':labels[rb-1]})
        single_rows.add(single); pair_rows.update([la,rb]); source_rows.add(la); target_rows.add(rb)
    assert {tuple(c['partner_token']) for c in group}==independently_common
    roles.append({'implementations':[an,bn],'checkpoint':checkpoint,'checkpoint_column_0based':nodes.index(checkpoint),'contexts':group,'allowed_Y_rows': sorted({c[k] for c in group for k in ('C_row','AC_row')}),'withheld_Y_rows':[c['BC_row'] for c in group],'allowed_X_columns_0based':list(range(82))})
assert [len(g['contexts']) for g in roles]==[10,9,10,10]
assert len(pair_rows)==54 and len(single_rows)==12
assert sorted(source_rows&target_rows)==[6,7,10,18,19,20,38,47,51,69,83,88]
save('roles_reconstructed.json',{'groups':roles,'unique_paired_rows':sorted(pair_rows),'unique_single_rows':sorted(single_rows),'cross_group_source_target_rows':sorted(source_rows&target_rows),'indexing':'conditional positional assumption, not certified'})
# Tokenize only; numeric access happens exclusively below through per-group whitelists.
raw=[s.split() for s in (SRC/'q1_pertbio_data.txt').read_text().splitlines() if s.strip()]
assert len(raw)==89 and all(len(row)==99 for row in raw)
stamp('raw_matrix_tokenized_without_numeric_conversion', shape=[89,99])
all_predictions=[]
for gi,g in enumerate(roles):
    xrows={c[k] for c in g['contexts'] for k in ('C_row','AC_row','BC_row')}
    yrows=set(g['allowed_Y_rows'])
    def x_read(row):
        assert row in xrows
        a=np.array([float(v) for v in raw[row-1][:82]])
        assert np.isfinite(a).all()
        stamp('group_X_read', group=gi+1,row=row,columns='1..82')
        return a
    def y_read(row):
        assert row in yrows
        y=float(raw[row-1][86]); assert np.isfinite(y)
        stamp('group_source_Y_read',group=gi+1,row=row,column=87)
        return y
    cs=g['contexts']
    XC=np.array([x_read(c['C_row']) for c in cs]); XAC=np.array([x_read(c['AC_row']) for c in cs]); XBC=np.array([x_read(c['BC_row']) for c in cs])
    YC=np.array([y_read(c['C_row']) for c in cs]); YAC=np.array([y_read(c['AC_row']) for c in cs])
    fitted=fit_group(XC,YC,XAC,YAC,XBC,g['checkpoint_column_0based'])
    all_predictions.append({'group':gi+1,**fitted})
assert FITS=={'loo':1053,'final':12}
prediction_sha=save('independent_predictions.json',{'groups':all_predictions,'fit_counts':FITS,'script_sha256':sha(Path(__file__)),'input_sha256':input_hashes})
stamp('all_group_predictions_saved',sha256=prediction_sha,path=str(OUT/'independent_predictions.json'))
save('prediction_save_receipt.json',{'prediction_sha256':prediction_sha,'saved_utc':EVENTS[-1]['utc'],'script_sha256':sha(Path(__file__)),'coordinator_files_read':[]})
# First within-group target Y conversion starts only after all predictions and their SHA are saved.
results=[]
for gi,(g,p) in enumerate(zip(roles,all_predictions)):
    truth=[]
    for c in g['contexts']:
        row=c['BC_row']; y=float(raw[row-1][86]); assert np.isfinite(y)
        stamp('group_target_Y_evaluation_read',group=gi+1,row=row,column=87)
        truth.append(y)
    truth=np.array(truth)
    scores={}
    for m,pv in p['predictions'].items():
        residual=np.array(pv)-truth
        scores[m]={'mse':float(np.mean(residual**2)),'mae':float(np.mean(np.abs(residual))),'residual_prediction_minus_truth':residual.tolist()}
    s=scores['scalar_ridge']['mse']; a=min(scores[m]['mse'] for m in ('partner_mean','source_copy')); f=min(scores[m]['mse'] for m in ('full_ridge','full_rbf'))
    decision='scalar_strict_best' if all(s<scores[m]['mse'] for m in MODELS[1:]) else ('dominated_by_simple_and_full' if s>=a and s>=f else 'mixed_or_tied')
    results.append({'group':gi+1,'truth':truth.tolist(),'scores':scores,'decision':decision,'source_d_constant':p['source_d_constant'],'target_Y_constant':bool(np.all(truth==truth[0]))})
decisions=[r['decision'] for r in results]
if all(d=='scalar_strict_best' for d in decisions) and not any(r['source_d_constant'] or r['target_Y_constant'] for r in results): overall='retain_configuration_for_independent_test'
elif all(d=='dominated_by_simple_and_full' for d in decisions): overall='stop_this_configuration_on_this_panel'
else: overall='mixed_or_inconclusive'
summary={which:{m:{metric:float(np.mean([results[j]['scores'][m][metric] for j in ids])) for metric in ('mse','mae')} for m in MODELS} for which,ids in [('macro',[0,1,2,3]),('exact_name_groups_1_3',[0,2])]}
stamp('evaluation_completed')
save('independent_results.json',{'groups':results,**summary,'decision':overall,'biological_ci':None,'p_values':None,'prediction_sha256':prediction_sha,'fit_counts':FITS,'elapsed_seconds':time.perf_counter()-START,'peak_working_set_bytes':peak_memory(),'requested_model':'gpt-6.1-sol/high','effective_model':'unknown'})
save('access_log.json',EVENTS)
print(json.dumps({'decision':overall,'group_decisions':decisions,'prediction_sha256':prediction_sha,'fits':FITS,'elapsed_seconds':time.perf_counter()-START,'peak_working_set_MiB':peak_memory()/2**20}))
