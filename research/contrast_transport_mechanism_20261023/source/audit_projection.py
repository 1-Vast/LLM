"""Independent saved projection audit via least squares; no raw/count access."""
import os
os.environ['OPENBLAS_NUM_THREADS'] = '1'
os.environ['OMP_NUM_THREADS'] = '1'
from pathlib import Path
import hashlib
import json
import numpy as np
from threadpoolctl import threadpool_limits

root = Path(__file__).resolve().parents[3]
out = root/'log/20261023/contrast_transport_mechanism'
prior = root/'log/20261023/replicated_contrast'
report = json.loads((out/'PROJECTION_RESULT.json').read_text())
freeze = json.loads((out/'EXECUTION_FREEZE.json').read_text())
meta = json.loads((out/'source/SELECTED_CONSTRUCT_METADATA.json').read_text())
labels = json.loads((out/'source/IDENTITY_NUISANCE_LABELS.json').read_text())
pairs = json.loads((prior/'SELECTED_PAIR_IDS.json').read_text())
ids = json.loads((prior/'CONSTRUCT_IDS.json').read_text())
identity = np.load(out/'source/IDENTITY_NUISANCE_MATRICES.npz',allow_pickle=False)
arrays = np.load(out/'PROJECTION_ARRAYS.npz',allow_pickle=False)
with np.load(prior/'CONTRAST_ARRAYS.npz',allow_pickle=False) as old:
    values = old['delta']
checks, errors = [], {}
rtol = 256*np.finfo(float).eps

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def check(name, ok):
    checks.append(dict(name=name,passed=bool(ok)))
    if not ok:
        raise AssertionError(name)

def near(name, a, b):
    a,b = np.asarray(a),np.asarray(b)
    errors[name] = float(np.max(np.abs(a-b)))
    check(name,np.allclose(a,b,rtol=1e-10,atol=1e-10))

for rel,digest in freeze['files'].items():
    check('freeze:'+rel,sha(root/rel) == digest)
check('output_hash',sha(out/'PROJECTION_ARRAYS.npz') == report['arrays_sha256'])
check('metadata_order',[r['construct_id'] for r in meta] == ids)
check('metadata_unique',len(meta) == len({r['construct_id'] for r in meta}) == 9306)
check('pair_count',len(pairs) == 1024)
gi,hi = {g:i for i,g in enumerate(labels['role_gene'])},{h:i for i,h in enumerate(labels['role_guide'])}
gene = np.zeros((1024,len(gi)))
guide = np.zeros((1024,len(hi)))
sizes = np.zeros(1024,dtype=int)
parent = {}
for r in meta:
    i = r['pair_row']
    check('pair_row_'+r['construct_id'],0 <= i < 1024 and sorted([r['target_a_id'],r['target_b_id']]) == pairs[i])
    sizes[i] += 1
    for slot,g,h in [('L:',r['target_a_id'],r['probe_a_id']),('R:',r['target_b_id'],r['probe_b_id'])]:
        gene[i,gi[slot+g]] += 1
        guide[i,hi[slot+h]] += 1
        parent[slot+h] = slot+g
check('sizes9or18',np.isin(sizes,[9,18]).all())
check('sizes_saved',np.array_equal(sizes,identity['construct_sizes']))
gene /= sizes[:,None]
guide /= sizes[:,None]
near('role_gene_metadata',gene,identity['role_gene'])
near('role_guide_metadata',guide,identity['role_guide'])
check('guide_parent_metadata',parent == labels['guide_parent'])
for h,g in parent.items():
    near('balanced_'+h,3*guide[:,hi[h]],gene[:,gi[g]])
check('three_children',all(sum(p == g for p in parent.values()) == 3 for g in gi))
design = np.column_stack([np.ones(512),gene[0::2]-gene[1::2]])
near('design_metadata',design,arrays['design'])
near('delta_binding',values,arrays['delta'])
with threadpool_limits(limits=1):
    coefficients,_,rank,singular = np.linalg.lstsq(design,values,rcond=max(design.shape)*np.finfo(float).eps)
add = design@coefficients
res = values-add
near('lstsq_additive',add,arrays['additive'])
near('lstsq_residual',res,arrays['residual'])
near('singular_values',singular,arrays['singular_values'])
check('rank',int(rank) == report['rank'] == arrays['basis'].shape[1])
check('residual_dim',512-int(rank) == report['residual_dimension'])
check('design_columns',design.shape[1] == report['nuisance_columns'])
q = arrays['basis']
near('q_orthonormal',q.T@q,np.eye(q.shape[1]))
near('q_spans_design',q@(q.T@design),design)
near('q_residual_orthogonal',q.T@arrays['residual'],np.zeros((q.shape[1],2)))
near('residual_centered',res.mean(axis=0),report['residual_mean'])
centered = values-values.mean(axis=0)
ac = add-add.mean(axis=0)
total,additive,residual = (float(x[:,0]@x[:,1]) for x in [centered,ac,res])
for name,value in [('total_cross_product',total),('additive_cross_product',additive),('residual_cross_product',residual)]:
    near(name,value,report[name])
floor = rtol*max(float(np.linalg.norm(centered[:,0])*np.linalg.norm(centered[:,1])),np.finfo(float).tiny)
defined = abs(total) > floor
fractions = dict(additive_fraction=additive/total,residual_fraction=residual/total) if defined else dict(additive_fraction=None,residual_fraction=None)
for name,v in fractions.items():
    check(name+'_null',v is None and report[name] is None) if v is None else near(name,v,report[name])
correlations = {}
for name,x in [('original',values),('additive',add),('residual',res)]:
    xc = x-x.mean(axis=0)
    norms = np.linalg.norm(xc,axis=0)
    guard = rtol*np.maximum(np.linalg.norm(values,axis=0),np.finfo(float).tiny)
    correlation = None if np.any(norms <= guard) else float((xc[:,0]@xc[:,1])/(norms[0]*norms[1]))
    correlations[name] = correlation
    check(name+'_correlation_null',report[name+'_correlation'] is None) if correlation is None else near(name+'_correlation',correlation,report[name+'_correlation'])
    near(name+'_rms',np.sqrt((x*x).sum(axis=0)/len(x)),report[name+'_rms'])
screen = bool(total > floor and correlations['residual'] is not None and correlations['residual'] >= .5 and fractions['residual_fraction'] is not None and fractions['residual_fraction'] >= .25)
check('screen',screen == report['screen'])
summary = dict(checks=len(checks),failures=0,details=checks,numeric_errors=errors,
               maximum_numeric_discrepancy=max(errors.values()),rank=int(rank),residual_dimension=512-int(rank),
               additive_fraction=fractions['additive_fraction'],residual_fraction=fractions['residual_fraction'],
               residual_correlation=correlations['residual'],screen=screen,method='Independent np.linalg.lstsq on reconstructed identity-weighted design',
               code_sha256=sha(Path(__file__)),new_raw_count_access=False,predictive_model_fit=False,
               scope='Retained-input projection arithmetic and hashes, not raw extraction, causal attribution or heldout prediction')
(out/'source/ARRAY_AUDIT.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k not in ['details','numeric_errors']}))
