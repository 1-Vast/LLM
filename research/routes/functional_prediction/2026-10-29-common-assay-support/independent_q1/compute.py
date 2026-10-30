import collections
import hashlib
import json
import math
import os
from pathlib import Path
import platform
import sys
import time
import traceback
import warnings

HERE = Path(__file__).resolve().parent
# The parent guard assigns the process to its hard resource job before releasing it.
while not (HERE / 'execution_gate').exists():
    time.sleep(0.01)

START_CPU = time.process_time()
import numpy as np
import scipy
from scipy.integrate import quad, IntegrationWarning
from scipy.special import log_ndtr, logsumexp

COUNTS = collections.Counter()
LN2 = math.log(2.0)
NEG_INF = -math.inf


def write_json(name, obj):
    data = json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False).encode('utf-8')
    existing = sum(p.stat().st_size for p in HERE.iterdir() if p.is_file())
    if existing + len(data) > 50000000:
        raise RuntimeError('output_budget_exceeded')
    (HERE / name).write_bytes(data)


def edge(x):
    return x if math.isfinite(x) else ('-inf' if x < 0 else '+inf')


def merge(model):
    grouped = collections.defaultdict(list)
    for weight, mu, var in model:
        grouped[(mu, var)].append(weight)
    return [(math.fsum(grouped[key]), *key) for key in sorted(grouped)]


def normal_logpdf(y, mu, var):
    COUNTS['gaussian_log_density_scalar'] += 1
    return -0.5 * (math.log(2 * math.pi * var) + (y - mu) ** 2 / var)


def lcdf(t):
    COUNTS['special_logcdf_scalar'] += 1
    return float(log_ndtr(t))


def lsf(t):
    COUNTS['special_logsf_scalar'] += 1
    return float(log_ndtr(-t))


def logdiff(large, small):
    if small == NEG_INF:
        return large
    if not small < large:
        raise ArithmeticError('nonpositive_CDF_difference')
    return large + math.log(-math.expm1(small - large))


def gaussian_mass(a, b, mu, var):
    sd = math.sqrt(var)
    lo, hi = (a - mu) / sd, (b - mu) / sd
    if lo == NEG_INF:
        return lcdf(hi)
    if hi == math.inf:
        return lsf(lo)
    if lo + hi >= 0:
        return logdiff(lsf(lo), lsf(hi))
    return logdiff(lcdf(hi), lcdf(lo))


def mixmass(a, b, model):
    answer = float(logsumexp([math.log(w) + gaussian_mass(a, b, mu, var)
                              for w, mu, var in model]))
    if not math.isfinite(answer) or math.exp(answer) == 0:
        raise ArithmeticError('nonempty_interval_mass_zero_or_nonfinite')
    return answer


def mixpdf(y, model):
    return float(logsumexp([math.log(w) + normal_logpdf(y, mu, var)
                            for w, mu, var in model]))


def envelope(a, b, model):
    lower, upper = [], []
    for w, mu, var in model:
        nearest = min(max(mu, a), b)
        upper.append(math.log(w) + normal_logpdf(nearest, mu, var))
        if not math.isfinite(a) or not math.isfinite(b):
            lower.append(NEG_INF)
        else:
            lower.append(math.log(w) + min(normal_logpdf(a, mu, var),
                                          normal_logpdf(b, mu, var)))
    return float(logsumexp(lower)), float(logsumexp(upper))


def leaf(a, b, models, trace):
    COUNTS['computed_leaf'] += 1
    logs = [mixmass(a, b, model) for model in models]
    marginal = float(logsumexp(logs)) - LN2
    logq = [value - LN2 - marginal for value in logs]
    bounds = [envelope(a, b, model) for model in models]
    logr = [bounds[z][1] - float(logsumexp([bounds[z][1], bounds[1-z][0]]))
            for z in range(2)]
    if any(math.exp(logq[z]) - math.exp(logr[z]) > 1e-12 for z in range(2)):
        raise ArithmeticError('posterior_mean_above_envelope')
    hq = math.fsum(-math.exp(v) * v for v in logq)
    gamma = max(logr[z] - logq[z] for z in range(2))
    d = math.exp(marginal) * min(hq, gamma)
    l = math.fsum(0.5 * math.exp(value) * (value - marginal) for value in logs)
    if not all(math.isfinite(v) for v in (l, d, hq, gamma)) or d < 0:
        raise ArithmeticError('negative_d_or_nonfinite_leaf')
    row = dict(a=edge(a), b=edge(b), log_model_mass=logs, log_marginal_mass=marginal,
               log_q=logq, log_r=logr,
               log_density_envelopes=[[edge(v) for v in pair] for pair in bounds],
               Hq=hq, gamma=gamma, L=l, d=d)
    trace.append(row)
    return dict(a=a, b=b, L=l, d=d, trace_index=len(trace)-1)


def adaptive(models):
    models = [merge(model) for model in models]
    trace, iterations = [], []
    starts = [-math.inf, -8.0, 0.0, 8.0, math.inf]
    leaves = [leaf(a, b, models, trace) for a, b in zip(starts, starts[1:])]
    equal = models[0] == models[1]
    splits = 0
    while True:
        raw_l = math.fsum(item['L'] for item in leaves)
        width = math.fsum(item['d'] for item in leaves)
        if raw_l < -1e-12 or not all(math.isfinite(v) for v in (raw_l, width)):
            raise ArithmeticError('invalid_total_information')
        selected = max(range(len(leaves)), key=lambda i: leaves[i]['d'])
        current = leaves[selected]
        if equal:
            lower = upper = 0.0
            stop = 'exact_identical_model_guard_after_initial_leaf_checks'
        else:
            lower, upper = raw_l, raw_l + width
            stop = ('width_reached' if upper-lower <= 0.02 else
                    'leaf_limit' if len(leaves) >= 2048 else None)
        iterations.append(dict(leaf_count=len(leaves), L=lower, U=upper,
                               initial_or_unguarded_L=raw_l, unguarded_width=width,
                               selected=[edge(current['a']), edge(current['b'])],
                               selected_trace_index=current['trace_index'], stop=stop))
        if stop:
            break
        a, b = current['a'], current['b']
        midpoint = b-8.0 if a == NEG_INF else a+8.0 if b == math.inf else (a+b)/2
        children = [leaf(a, midpoint, models, trace), leaf(midpoint, b, models, trace)]
        leaves[selected:selected+1] = children
        splits += 1
        COUNTS['split'] += 1
    return dict(L=lower, U=upper, width=upper-lower, stop=stop, identical_guard=equal,
                leaf_count=len(leaves), computed_leaves=len(trace), splits=splits,
                computed_leaf_trace=trace, iterations=iterations,
                final_partition=[dict(a=edge(x['a']), b=edge(x['b']), L=x['L'], d=x['d'],
                                      trace_index=x['trace_index']) for x in leaves])


def mi_lb(models, merged):
    if merged:
        models = [merge(model) for model in models]
    marginal = [(w/2, mu, var) for model in models for w, mu, var in model]
    if merged:
        marginal = merge(marginal)
    hl = -math.fsum(w * float(logsumexp([
        math.log(wj) + normal_logpdf(mu, muj, var+varj)
        for wj, muj, varj in marginal])) for w, mu, var in marginal)
    hu = [math.fsum(w * (-math.log(w) + 0.5*math.log(2*math.pi*math.e*var))
                    for w, mu, var in model) for model in models]
    return dict(score=hl-math.fsum(0.5*x for x in hu), H_lower_marginal=hl,
                H_upper_models=hu)


def means_disagreement(models):
    means = [math.fsum(w*mu for w, mu, var in model) for model in models]
    mean = math.fsum(x/2 for x in means)
    return dict(model_means=means, score=math.fsum(0.5*(x-mean)**2 for x in means))


def threshold_bald(models):
    # Direct two-bin mutual information with no adaptive contribution.
    terms, probs = [], []
    for a, b in [(-math.inf, 0.5), (0.5, math.inf)]:
        logs = [mixmass(a,b,model) for model in models]
        marginal = float(logsumexp(logs))-LN2
        terms += [0.5*math.exp(v)*(v-marginal) for v in logs]
        probs.append([math.exp(v) for v in logs])
    return dict(tau=0.5, score=math.fsum(terms), bin_model_probabilities=probs)


def reference(models):
    models = [merge(model) for model in models]
    diagnostics = dict(negative_model_terms=0, largest_abs_model_term=0.0,
                       largest_sum_abs_terms=0.0)
    def integrand(y):
        COUNTS['quad_integrand'] += 1
        values = [mixpdf(y, model) for model in models]
        marginal = float(logsumexp(values))-LN2
        terms = [0.5*math.exp(v)*(v-marginal) for v in values]
        diagnostics['negative_model_terms'] += sum(v < 0 for v in terms)
        diagnostics['largest_abs_model_term'] = max(diagnostics['largest_abs_model_term'],
                                                    *(abs(v) for v in terms))
        diagnostics['largest_sum_abs_terms'] = max(diagnostics['largest_sum_abs_terms'],
                                                    math.fsum(abs(v) for v in terms))
        answer = math.fsum(terms)
        if not math.isfinite(answer):
            raise ArithmeticError('nonfinite_quad_integrand')
        return answer
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter('always')
        value, err = quad(integrand, -16.0, 16.0, epsabs=1e-12, epsrel=1e-12, limit=300)
    tails = [math.exp(mixmass(-math.inf,-16.0,model))+
             math.exp(mixmass(16.0,math.inf,model)) for model in models]
    tail_bound = LN2*math.fsum(v/2 for v in tails)
    total_error = err + tail_bound
    good = not caught and all(math.isfinite(v) for v in (value,err,total_error)) and total_error <= 1e-10
    return dict(value=value, quad_error=err, tail_upper_bound=tail_bound,
                total_error=total_error, error_range=[value-total_error,value+total_error],
                valid_for_containment=good, warnings=[str(w.message) for w in caught],
                cancellation_diagnostics=diagnostics,
                caution='Signed model terms can cancel; quad error is an estimate, not a formal enclosure.')


def timed(function, *args):
    before = COUNTS.copy()
    start = time.process_time()
    result = function(*args)
    return dict(result=result, cpu_seconds=time.process_time()-start,
                counts={k: COUNTS[k]-before[k] for k in COUNTS if COUNTS[k]-before[k]})


def main():
    root = HERE.parent
    frozen = json.loads((HERE/'preexecution_freeze.json').read_text(encoding='utf-8-sig'))
    for rel, expected in frozen['hashes'].items():
        path = HERE/rel if rel in ('compute.py','guard.py','input.json') else root/rel
        if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise RuntimeError('frozen_hash_mismatch:'+rel)
    inputs = json.loads((HERE/'input.json').read_text(encoding='utf-8'))
    all_results = {}
    for name, models in inputs.items():
        all_results[name] = dict(raw_mi_lb=timed(mi_lb,models,False),
                                 exact_merged_mi_lb=timed(mi_lb,models,True),
                                 mean_disagreement=timed(means_disagreement,models),
                                 tau_bald=timed(threshold_bald,models),
                                 q1=timed(adaptive,models),
                                 reference_mi=timed(reference,models))
        write_json('partial_results.json',all_results)
    a,b,bp = (all_results[k] for k in ('A','B','B_prime'))
    qa,qb,qp = (x['q1']['result'] for x in (a,b,bp))
    ra,rb = (x['reference_mi']['result'] for x in (a,b))
    contained = {}
    for name, item in all_results.items():
        q,r = item['q1']['result'],item['reference_mi']['result']
        contained[name] = r['valid_for_containment'] and r['error_range'][0]>=q['L']-1e-8 and r['error_range'][1]<=q['U']+1e-8
    h1 = a['raw_mi_lb']['result']['score'] > b['raw_mi_lb']['result']['score'] and qa['identical_guard'] and rb['value']-rb['total_error']>0
    h2 = all(q['leaf_count']<=2048 and q['width']<=0.02 for q in (qa,qb)) and qb['L']>qa['U']+1e-8 and contained['A'] and contained['B']
    changes = dict(L=abs(qb['L']-qp['L']), U=abs(qb['U']-qp['U']),
                   raw_mi_lb=abs(b['raw_mi_lb']['result']['score']-bp['raw_mi_lb']['result']['score']))
    h3 = changes['L']<=1e-10 and changes['U']<=1e-10 and changes['raw_mi_lb']>1e-6
    result = dict(state='local_H_supported' if h1 and h2 and h3 else 'H_not_supported',
                  H=dict(H1=h1,H2=h2,H3=h3), changes_B_to_Bprime=changes,
                  reference_containment=contained, candidates=all_results,
                  total_counts=dict(COUNTS), worker_cpu_seconds=time.process_time()-START_CPU,
                  versions=dict(python=platform.python_version(),numpy=np.__version__,scipy=scipy.__version__),
                  actions=dict(raw_MI_LB_ranking=sorted(all_results,key=lambda k:all_results[k]['raw_mi_lb']['result']['score'],reverse=True),
                               Q1_B_over_A=qb['L']>qa['U']+1e-8),
                  independence='Only frozen allowed inputs/source read; root implementation/numerics neither read nor run.',
                  limits=dict(cpu_seconds=120,ram_bytes=1073741824,output_bytes=50000000),
                  evidence_scope='synthetic local numerical property only; no novelty/drug/learning benefit established')
    write_json('result.json',result)


try:
    main()
except Exception as error:
    write_json('result.json',dict(state='numerical_or_execution_failure',error_type=type(error).__name__,
                                  error=str(error), traceback=traceback.format_exc(), counts=dict(COUNTS),
                                  worker_cpu_seconds=time.process_time()-START_CPU, retry=False))
    raise
