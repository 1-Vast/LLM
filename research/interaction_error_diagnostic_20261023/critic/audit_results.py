"""Audit retained development predictions; no workbook access and no fitting."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[3]
LOG = ROOT/'log/20261023/interaction_error_diagnostic'
OUT = LOG/'critic'
DEV = ['MCF7', 'MDAMB231', 'MCF10A', 'CAL27', 'CAL33']
EXPECTED = {
    'code_sha256': 'ad31d0d83df0262de45be328376d3cb2ecaef9b6a326532f9fe24d9c3a36fe11',
    'plan_sha256': '38aea4b6229b2db07439fc4fb2c66a6d94706548394363d77bb6ede5638d4b9f',
    'amendment_sha256': '89edf88d5e6c3b740f4c77ad845e0efdd5bb98d747883173bcdd533864b6e3ad',
}

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    report = json.loads((LOG/'RESULTS.json').read_text(encoding='utf-8'))
    pairs = json.loads((LOG/'PAIR_IDS.json').read_text(encoding='utf-8'))
    checks, differences = [], []
    def check(name, condition):
        checks.append({'check': name, 'pass': bool(condition)})
    def close(name, actual, expected):
        error = float(np.max(np.abs(np.asarray(actual)-np.asarray(expected))))
        differences.append(error)
        check(name, error <= 1e-12)

    for name, expected in EXPECTED.items():
        check(name, report[name] == expected)
    for key, file in [('prediction_sha256','PREDICTIONS.npz'), ('pair_ids_sha256','PAIR_IDS.json')]:
        check(key, report[key] == sha(LOG/file))
    with np.load(LOG/'PREDICTIONS.npz', allow_pickle=False) as arrays:
        y, z = arrays['development_scores'], arrays['gene_incidence']
        n = len(pairs)
        genes = sorted({g for pair in pairs for g in pair})
        positions = {g:i for i,g in enumerate(genes)}
        incidence = np.zeros((n,len(genes)))
        for i, (a,b) in enumerate(pairs):
            incidence[i,positions[a]] = incidence[i,positions[b]] = 1
        check('development_shape_and_only_columns', y.shape == (n,5) and report['data']['parsed_score_columns'] == DEV)
        check('no_lung_array_keys', not any('A549' in key or 'A427' in key for key in arrays.files))
        check('eligible_count', n == 11621 == report['data']['eligible'])
        check('gene_count', len(genes) == 225 == report['data']['genes'])
        check('unique_sorted_canonical_pairs', pairs == sorted(pairs) and len({tuple(p) for p in pairs}) == n and all(a < b for a,b in pairs))
        check('controls_excluded', not any(set(p)&{'AAVS','nontargeting'} for p in pairs))
        check('finite_dev', np.isfinite(y).all())
        close('gene_incidence_from_ids', z, incidence)
        check('record_keys_unique', len(report['records']) == 20 == len({(r['context'],r['salt'],r['budget']) for r in report['records']}))
        metric_values, cost_totals = {}, Counter()
        coverage = {}
        for record in report['records']:
            name, salt, budget = record['context'],record['salt'],record['budget']
            prefix = f'{name}_{salt}_{budget}'
            idx = np.array(sorted(range(n), key=lambda i: hashlib.sha256((str(salt)+'|'+'|'.join(pairs[i])).encode()).hexdigest()))
            support, train, valid, query = [arrays[prefix+'_'+kind] for kind in ['support','inner_train','inner_valid','query']]
            check(prefix+'_hash_support', record['support_hash'] == hashlib.sha256(support.tobytes()).hexdigest())
            check(prefix+'_hash_query', record['query_hash'] == hashlib.sha256(query.tobytes()).hexdigest())
            check(prefix+'_roles', np.array_equal(support,idx[:budget]) and np.array_equal(query,idx[512:]) and np.array_equal(train,support[:int(.8*budget)]) and np.array_equal(valid,support[int(.8*budget):]))
            check(prefix+'_disjoint', not set(query)&set(support) and not set(train)&set(valid))
            check(prefix+'_query_n', len(query) == record['query_n'] == n-512)
            other = f'{name}_{salt}_{512 if budget==128 else 128}'
            check(prefix+'_fixed_Q', np.array_equal(query,arrays[other+'_query']))
            check(prefix+'_nested_support', set(arrays[f'{name}_{salt}_128_support']) <= set(arrays[f'{name}_{salt}_512_support']))
            truth = arrays[prefix+'_truth']
            close(prefix+'_truth_column', truth, y[query,DEV.index(name)])
            source = np.delete(y,DEV.index(name),axis=1)
            close(prefix+'_source_mean_columns', arrays[prefix+'_source_mean'], source[query].mean(axis=1))
            close(prefix+'_support_mean', arrays[prefix+'_support_mean'], np.full(len(query),y[support,DEV.index(name)].mean()))
            seen = np.any(z[support] != 0,axis=0)
            unseen = float(np.mean(z[query][:,~seen].sum(axis=1)>0))
            close(prefix+'_coverage', unseen,record['endpoint_unseen_fraction'])
            coverage[(name,salt,budget)] = unseen
            for family, choice in record['chosen'].items():
                candidates = [v for v in record['validation'] if v['family']==family]
                selected = min(candidates,key=lambda c:c['mse'])
                check(prefix+'_selection_'+family, selected['spec'] == choice and len(candidates)==(11 if family=='score_direct' else 10))
            optimal = np.mean(np.sort(truth)[:20])
            metric_values[(name,salt,budget)] = {}
            for arm, saved in record['metrics'].items():
                pred = arrays[prefix+'_'+arm]
                nominated = np.argsort(pred,kind='stable')[:20]
                computed = {'mse': np.mean((pred-truth)**2), 'bottom20_mean': np.mean(truth[nominated]), 'bottom20_regret':np.mean(truth[nominated])-optimal}
                metric_values[(name,salt,budget)][arm] = computed
                for metric, value in computed.items():
                    close(prefix+'_'+arm+'_'+metric,value,saved[metric])
            calls = record['calls']
            check(prefix+'_pipeline_calls',len(calls)==26==record['pipeline_calls'])
            check(prefix+'_validation_call_specs', [c['spec'] for c in calls if c['stage']=='validation'] == [v['spec'] for v in record['validation']])
            check(prefix+'_stages',Counter(c['stage'] for c in calls)=={'validation':21,'final':4,'negative_control':1})
            for call in calls:
                kind = call['spec'][0]
                expected_fits = 2 if kind=='residual' else int(kind in ('ridge','trees','joint','calibration'))
                check(prefix+'_call_cost_'+str(len(checks)),call['estimator_fits']==expected_fits and call['linear_solves']==int(kind in ('rbf','jointkernel')) and call['seconds']>=0)
            check(prefix+'_estimator_total',record['estimator_fits']==sum(c['estimator_fits'] for c in calls))
            check(prefix+'_solve_total',record['kernel_linear_solves']==sum(c['linear_solves'] for c in calls))
            check(prefix+'_elapsed',record['seconds']>=sum(c['seconds'] for c in calls))
            cost_totals.update({'pipeline_calls':len(calls),'estimator_fits':record['estimator_fits'],'kernel_linear_solves':record['kernel_linear_solves']})
        summary = []
        for aggregate in report['aggregate']:
            budget, wins = aggregate['budget'],0
            for context in aggregate['contexts']:
                name = context['context']
                values = {arm:{metric:np.mean([metric_values[(name,s,budget)][arm][metric] for s in (0,1)]) for metric in ('mse','bottom20_regret')} for arm in record['metrics']}
                for metric, arms in context['comparison'].items():
                    for arm, saved in arms.items():
                        close(f'aggregate_{name}_{budget}_{arm}_{metric}',values[arm][metric],saved)
                win = all(values['identity_ordinary'][m]<values['score_direct'][m] for m in ('mse','bottom20_regret'))
                check(f'joint_win_{name}_{budget}',win == context['joint_win'])
                wins += win
                summary.append({'context':name,'budget':budget,'values':values,'unseen_query_endpoint_fraction':float(np.mean([coverage[(name,s,budget)] for s in (0,1)])),'joint_win':win})
            check('joint_wins_'+str(budget),wins==aggregate['joint_wins'])
        gate = all(a['joint_wins']>=4 for a in report['aggregate'])
        check('screening_gate',gate==report['screening_gate'])
    output = {'scope':'Retained development arrays only; no workbook, no fit, no regenerated validation losses','checks':len(checks),'failures':[c for c in checks if not c['pass']],'max_numeric_difference':max(differences),'metric_comparisons':len(differences),'cost_totals':dict(cost_totals),'screening_gate':gate,'summary':summary,'detail':checks,'audited_results_sha256':sha(LOG/'RESULTS.json'),'audit_code_sha256':sha(Path(__file__))}
    (OUT/'AUDIT.json').write_text(json.dumps(output,indent=2),encoding='utf-8')
    print(json.dumps({k:output[k] for k in ('checks','failures','max_numeric_difference','metric_comparisons','cost_totals','screening_gate')}))

if __name__=='__main__':
    main()
