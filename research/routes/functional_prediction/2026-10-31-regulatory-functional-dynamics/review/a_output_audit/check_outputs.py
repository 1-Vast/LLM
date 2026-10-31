"""Independent frozen output arithmetic audit; imports no experiment code."""
import argparse
import csv
from datetime import datetime, timezone
import gzip
import hashlib
import json
import math
from pathlib import Path
from statistics import median

OUT = Path(__file__).parent
EPISODE = OUT.parents[1]
DATA = EPISODE.parents[3] / 'data/external/conditional_interventions_20261030/egi'
COUNT_SHA = '105353899a4b91bc5446bfacc20ee91a13ff6bf17f8d53805fc8bb543f2a1403'
RULES = json.loads((OUT / 'expectations.json').read_text())
METHODS = RULES['methods']


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1048576), b''):
            h.update(chunk)
    return h.hexdigest()


def write(name, obj):
    (OUT / name).write_text(json.dumps(obj, indent=2, allow_nan=True) + '\n')


def read_table(path):
    with path.open(encoding='utf-8', newline='') as stream:
        return list(csv.DictReader(stream, delimiter='\t'))


def sign(x):
    return (x > 0) - (x < 0)


def hit(prediction, target):
    return abs(target) >= 1 and prediction != 0 and sign(prediction) == sign(target)


def near(actual, expected):
    assert (math.isnan(actual) and math.isnan(expected)) or math.isclose(actual, expected, rel_tol=1e-10, abs_tol=1e-10), (actual, expected)


def fold(pair):
    a, b = sorted(pair)
    return int(hashlib.sha256(f'MAESTRO-EGI-A1|{a}|{b}'.encode()).hexdigest()[:8], 16) % 10


def ranks(values):
    order = sorted(range(len(values)), key=lambda i: values[i])
    result, start = [0.] * len(values), 0
    while start < len(order):
        end = start + 1
        while end < len(order) and values[order[end]] == values[order[start]]:
            end += 1
        for i in order[start:end]:
            result[i] = (start + end - 1) / 2 + 1
        start = end
    return result


def corr(x, y):
    a, b = math.fsum(x) / len(x), math.fsum(y) / len(y)
    xx, yy = [v-a for v in x], [v-b for v in y]
    denominator = math.sqrt(math.fsum(v*v for v in xx) * math.fsum(v*v for v in yy))
    return math.fsum(v*w for v, w in zip(xx, yy)) / denominator if denominator else float('nan')


def self_test():
    q = RULES['synthetic_Q']
    assert q['double'] - q['row_control'] - q['column_control'] + q['NTC_control'] == q['expected']
    f = RULES['synthetic_target_hit']
    assert sum(hit(p, t) for p, t in zip(f['prediction'], f['target'])) == f['primary']
    assert sum(hit(p, t) and hit(p, s) for p, t, s in zip(f['prediction'], f['target'], f['source'])) == f['joint']
    assert 4 / 8 >= 0.5 and not 3 / 8 >= 0.5
    assert fold(('A', 'B')) == 1 and fold(('A', 'C')) == 9 and fold(('B', 'C')) == 4


def freeze():
    self_test()
    names = ['review/a_output_audit/check_outputs.py', 'review/a_output_audit/expectations.json',
             'a_protocol_v2.md', 'a_freeze_corrected.json', 'a_experiment_corrected.py',
             'egi_admission/guide_identity.tsv']
    assert not (OUT / 'checker_freeze.json').exists()
    write('checker_freeze.json', {'created_utc': datetime.now(timezone.utc).isoformat(),
          'status': 'FROZEN_BEFORE_GENERATED_NUMERICAL_ACCESS',
          'files': {n: sha(EPISODE / n) for n in names}, 'source_count_sha256': COUNT_SHA,
          'generated_numerical_files_read': False, 'synthetic_expectations': 'PASS'})


def reconstruct(top_pairs, supports):
    """Only selected double/control count tokens are converted; no model call."""
    meta = read_table(EPISODE / 'egi_admission/guide_identity.tsv')
    ntc = [r['guide_identity'] for r in meta if r['is_ntc'] == 'True']
    groups = {}
    for r in meta:
        if r['is_ntc'] == 'False':
            groups.setdefault(r['source_gene_label'], []).append(r['guide_identity'])
    assert len(ntc) == 13
    constructs = {pair: [(a,b) for g,h in [pair, pair[::-1]] for a in groups[g] for b in groups[h]] for pair in top_pairs}
    assert all(len(c) == 8 for c in constructs.values())
    targets = {g for pair in top_pairs for gene in pair for g in groups[gene]}
    needed = {c for cs in constructs.values() for c in cs}
    needed |= {(g,n) for g in targets for n in ntc} | {(n,g) for g in targets for n in ntc} | {(n,m) for n in ntc for m in ntc}
    path = DATA / '14_GI_expt1_counts.txt.gz'
    assert sha(path) == COUNT_SHA
    counts = {}
    labels = [f'Rep{r}_{c}' for r in [1,2] for c in ['T0','UT','DRUG']]
    with gzip.open(path, 'rt', encoding='utf-8') as stream:
        header = stream.readline().rstrip('\r\n').split('\t')
        positions = [header.index(label)-1 for label in labels]
        for line in stream:
            identity, rest = line.split('\t', 1)
            pair = tuple(identity.split(':'))
            if pair in needed:
                fields = rest.rstrip('\r\n').split('\t')
                values = [float(fields[i]) for i in positions]
                assert all(math.isfinite(x) and x >= 0 and x.is_integer() for x in values)
                assert pair not in counts
                counts[pair] = values
    assert counts.keys() == needed
    eligible = {c for c, x in counts.items() if x[0] >= 30 and x[3] >= 30}
    nn = [(n,m) for n in ntc for m in ntc if (n,m) in eligible]
    assert len(nn) >= 25
    row = {g: [(g,n) for n in ntc if (g,n) in eligible] for g in targets}
    col = {g: [(n,g) for n in ntc if (n,g) in eligible] for g in targets}
    assert all(len(v) >= 5 for v in [*row.values(), *col.values()])

    def response(r, p, numerator, denominator):
        lr = {c: math.log2((x[r*3+numerator]+p)/(x[r*3+denominator]+p)) for c,x in counts.items()}
        center = median(lr[c] for c in nn)
        rm, cm = {g: median(lr[c] for c in row[g]) for g in targets}, {g: median(lr[c] for c in col[g]) for g in targets}
        return {pair: median(lr[a,b]-rm[a]-cm[b]+center for a,b in cs if (a,b) in eligible) for pair,cs in constructs.items()}

    responses = {p: [response(r,p,2,1) for r in [0,1]] for p in RULES['pseudocounts']}
    baseline = [response(r,1,1,0) for r in [0,1]]
    support_columns = ['r1_t0','r1_ut','r1_drug','r2_t0','r2_ut','r2_drug']
    for target, records in supports.items():
        for rec in records:
            c = rec['guide_a'], rec['guide_b']
            assert [float(rec[k]) for k in support_columns] == counts[c]
            assert (rec['retained'] == 'True') == (c in eligible)
            assert int(rec['eligible_a_ntc']) == len(row[c[0]])
            assert int(rec['eligible_ntc_b']) == len(col[c[1]])
            assert int(rec['eligible_ntc_ntc']) == len(nn)
    floor = {r: {pair: sum(counts[c][r*3+1]<10 or counts[c][r*3+2]<10 for c in cs if c in eligible) / sum(c in eligible for c in cs) >= .5 for pair,cs in constructs.items()} for r in [0,1]}
    return responses, baseline, floor, constructs, len(needed)


def audit():
    frozen = json.loads((OUT / 'checker_freeze.json').read_text())
    assert all(sha(EPISODE/n) == v for n,v in frozen['files'].items())
    launch = json.loads((EPISODE / 'a_launch_corrected_receipt.json').read_text())
    assert launch['status'] == 'COMPLETE' and launch['returncode'] == 0
    assert not (OUT / 'independent_output_audit.json').exists()
    self_test()
    directory = EPISODE / 'a_results_corrected'
    endpoint_rows = read_table(directory / 'endpoints.tsv')
    result = json.loads((directory / 'results.json').read_text())
    endpoints, ordered, fold_sets = {}, [], {i:set() for i in range(10)}
    for row in endpoint_rows:
        pair = row['gene_a'], row['gene_b']
        assert pair[0] < pair[1] and pair not in endpoints
        f = int(row['fold']); assert f == fold(pair)
        values = [float(row[c]) for c in ['baseline_r1','baseline_r2','response_r1','response_r2']]
        assert all(math.isfinite(x) for x in values)
        endpoints[pair] = values; ordered.append(pair); fold_sets[f].add(pair)
    assert ordered == sorted(ordered)
    assert sum(len(s) for s in fold_sets.values()) == len(set().union(*fold_sets.values())) == len(ordered)
    train = sorted(set().union(*(fold_sets[f] for f in range(7))))
    test = set().union(fold_sets[8], fold_sets[9])
    for key, n in [('pairs',len(ordered)),('train',len(train)),('validation',len(fold_sets[7])),('test',len(test))]: assert result['qc'][key] == n
    confirmed = lambda pair: abs(endpoints[pair][2])>=1 and abs(endpoints[pair][3])>=1 and sign(endpoints[pair][2])==sign(endpoints[pair][3])
    strong = sum(confirmed(pair) for pair in train)
    training_correlation = corr(ranks([endpoints[p][2] for p in train]), ranks([endpoints[p][3] for p in train]))
    near(training_correlation, result['qc']['train_cross_culture_spearman'])
    near(corr([endpoints[p][2] for p in ordered], [endpoints[p][3] for p in ordered]), result['qc']['all_cross_culture_pearson'])
    near(corr(ranks([endpoints[p][2] for p in ordered]), ranks([endpoints[p][3] for p in ordered])), result['qc']['all_cross_culture_spearman'])
    assert result['qc']['train_confirmed_strong_pairs'] == strong
    assert result['qc']['confirmed_strong_pairs'] == sum(confirmed(pair) for pair in ordered)
    detectable = len(ordered)>=10000 and len(test)>=1000 and strong>=500 and training_correlation>=.2
    if not detectable:
        assert result['status'] == 'DETECTABILITY_STOP' and result['directions'] == {}
        write('independent_output_audit.json', {'status':'PASS_DETECTABILITY_STOP','folds_disjoint':True,'pair_count':len(ordered),'model_fit_by_auditor':False})
        return
    predictions, top, support, computed = {}, {}, {}, {}
    index = {p:i for i,p in enumerate(ordered)}
    for source,target in [(0,1),(1,0)]:
        direction = f'culture{source+1}_to_culture{target+1}'
        rows = read_table(directory / f'{direction}_predictions.tsv')
        assert set(rows[0]) == {'gene_a','gene_b',*METHODS}
        pred = {}; predictions[direction] = pred
        for row in rows:
            pair = row['gene_a'],row['gene_b']; assert pair in test and pair not in pred
            pred[pair] = {m:float(row[m]) for m in METHODS}
            assert all(math.isfinite(x) for x in pred[pair].values())
        assert pred.keys() == test
        top[direction], computed[direction] = {}, {}
        for method in METHODS:
            ranked = sorted(test, key=lambda p:(-abs(pred[p][method]),*p))[:100]
            top[direction][method] = ranked
            hits = sum(hit(pred[p][method], endpoints[p][target+2]) for p in ranked)
            joint = sum(hit(pred[p][method],endpoints[p][2]) and hit(pred[p][method],endpoints[p][3]) for p in ranked)
            mse = math.fsum((pred[p][method]-endpoints[p][target+2])**2 for p in test)/len(test)
            mae = math.fsum(abs(pred[p][method]-endpoints[p][target+2]) for p in test)/len(test)
            actual = result['directions'][direction]['metrics'][method]
            assert actual['hits_at_100']==hits and actual['joint_confirmed_hits_descriptive']==joint
            assert actual['negative_hits']==sum(hit(pred[p][method],endpoints[p][target+2]) and pred[p][method]<0 for p in ranked)
            near(actual['precision_at_100'],hits/100); near(actual['mse'],mse); near(actual['mae'],mae)
            assert actual['top_indices']==[index[p] for p in ranked]
            computed[direction][method] = {'hits':hits,'joint':joint,'MSE':mse,'MAE':mae}
        support[target] = read_table(directory / f'{direction}_top100_support.tsv')
    union = {p for methods in top.values() for ps in methods.values() for p in ps}
    responses, baselines, floor, constructs, selected_count = reconstruct(union, support)
    for p in union:
        for r in [0,1]: near(endpoints[p][r],baselines[r][p]); near(endpoints[p][r+2],responses[1][r][p])
    passed = []
    for source,target in [(0,1),(1,0)]:
        direction = f'culture{source+1}_to_culture{target+1}'
        recorded = result['directions'][direction]
        grouped = {}
        for rec in support[target]: grouped.setdefault((rec['model'],int(rec['rank'])),[]).append(rec)
        assert len(grouped)==len(METHODS)*100
        for method in METHODS:
            for rank,p in enumerate(top[direction][method],1):
                rs=grouped[method,rank]
                assert all((r['gene_a'],r['gene_b'])==p for r in rs)
                assert len(rs)==8 and {(r['guide_a'],r['guide_b']) for r in rs}==set(constructs[p])
            n=sum(floor[target][p] for p in top[direction][method])
            assert n==recorded['metrics'][method]['target_floor_pairs_in_top100']
            computed[direction][method]['target_floor_pairs']=n
        primary = {m:computed[direction][m]['hits'] for m in METHODS}
        passes = primary['candidate']>=20 and all(primary['candidate']-primary[m]>=5 for m in METHODS if m!='candidate') and computed[direction]['candidate']['target_floor_pairs']<=20
        sensitivities={}
        for p in [.5,2]:
            h={m:sum(hit(predictions[direction][pair][m],responses[p][target][pair]) for pair in top[direction][m]) for m in METHODS}
            assert h==recorded['fixed_ranking_pseudocount_sensitivity'][str(p)]
            passes = passes and h['candidate']>=20 and all(h['candidate']-h[m]>=5 for m in METHODS if m!='candidate')
            sensitivities[str(p)]=h
        assert passes==recorded['practical_gate']; passed.append(passes)
        computed[direction]['gate']={'pass':passes,'candidate_hit_margins':{m:primary['candidate']-primary[m] for m in METHODS if m!='candidate'},'pseudocount_sensitivity_hits':sensitivities}
    assert result['status']==('PRACTICAL_GATE_PASS' if all(passed) else 'PRACTICAL_GATE_FAIL')
    write('independent_output_audit.json', {'status':'PASS_ARITHMETIC_VERIFICATION','reported_experiment_status':result['status'],'folds_disjoint':True,'pair_count':len(ordered),'test_pair_count':len(test),'Top100_union_pairs':len(union),'selected_double_and_control_constructs_reconstructed':selected_count,'directions':computed,'model_fit_or_refit_or_rerank_by_auditor':False,'raw_count_conversion_limited_to_Top100_union_and_needed_controls':True})


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); mode=parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--freeze',action='store_true'); mode.add_argument('--audit',action='store_true')
    args=parser.parse_args()
    freeze() if args.freeze else audit()
