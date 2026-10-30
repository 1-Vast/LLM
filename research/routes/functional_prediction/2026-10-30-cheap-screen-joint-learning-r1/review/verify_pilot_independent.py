"""Independent E001 arithmetic; no primary implementation or results are inputs."""
import csv
import hashlib
import itertools
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

START_WALL = time.perf_counter()
START_CPU = time.process_time()
ROOT = Path(__file__).resolve().parents[1]
STIM = {'None': '00', 'IFNG': '10', 'TNFA': '01', 'IFNG_TNFA': '11'}
DRUGS = ['Momelotinib', 'BMS-345541', 'Salirasib', 'Trametinib', 'Taselisib']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def difference(a, b):
    return [a[0] - b[1], a[1] - b[0]]


output = {
    'implementation': 'Independent csv grouping and NumPy linear-quantile arithmetic; primary code/result never read before freeze',
    'protocol_sha256': digest(ROOT / 'protocol_v1_1.md'),
    'source_sha256': {}, 'preparations': {},
    'residual_convention': '(prediction - observation)/S0',
    'limitations': ['Capture beads; PE-only export cannot verify original APC gating.',
                    'Technical envelopes are not CIs; no population, molecular, cell-causal or external-validation conclusion.',
                    'Local control calibration in every preparation; differing doses confound between-line interpretation.']}
for code in ['E3CA', 'E3CB', 'E3DA', 'E3DB']:
    path = ROOT / 'evidence' / f'cxcl9_raw_{code}.body'
    output['source_sha256'][path.name] = digest(path)
    grouped = defaultdict(list)
    identities = {}
    with path.open(newline='', encoding='utf-8-sig') as stream:
        for row in csv.DictReader(stream):
            key = (row['Inhibitors'], STIM[row['Cytokines']], row['Condition'])
            grouped[key].append(float(row['Fluorescent intensity (PE)']))
            identity = {k: v for k, v in row.items() if k != 'Fluorescent intensity (PE)'}
            assert key not in identities or identities[key] == identity
            identities[key] = identity
    assert len(grouped) == 48
    wells = {}
    for key, values in grouped.items():
        arr = np.asarray(values, dtype=float)
        q1, q3 = np.quantile(arr, [.25, .75], method='linear')
        low, high = q1 - 1.5 * (q3-q1), q3 + 1.5 * (q3-q1)
        kept = arr[(arr >= low) & (arr <= high)]
        wells['|'.join(key)] = dict(identity=identities[key], n_raw=len(arr), n_kept=len(kept),
                                    n_removed=len(arr)-len(kept), q1=float(q1), q3=float(q3),
                                    trim_bounds=[float(low), float(high)], mfi=float(np.mean(kept)))
    means, ranges = {}, {}
    for drug in ['None'] + DRUGS:
        means[drug], ranges[drug] = {}, {}
        for stimulus in ['00', '10', '01', '11']:
            pair = [wells['|'.join((drug, stimulus, well))]['mfi'] for well in ['Sample1', 'Sample2']]
            means[drug][stimulus] = sum(pair)/2
            ranges[drug][stimulus] = [min(pair), max(pair)]
    m = means['None']; cr = ranges['None']
    D0, N0, S0 = m['10']-m['00'], m['11']-m['01'], m['11']-m['00']
    Dinterval, Ninterval = difference(cr['10'], cr['00']), difference(cr['11'], cr['01'])
    eligible = Dinterval[0] > 0 and Ninterval[0] > 0 and S0 > 0
    control = dict(means=m, ranges=cr, D0=D0, N0=N0, S0=S0,
                   D_interval=Dinterval, N_interval=Ninterval, eligible=eligible)
    prep = dict(wells=wells, means=means, well_ranges=ranges, controls=control, targets={})
    output['preparations'][code] = prep
    if not eligible:
        continue
    kappa, interaction = N0/D0, N0-D0
    ratio_corners = [n/d for n, d in itertools.product(Ninterval, Dinterval) if d > 0]
    ki = [min(ratio_corners), max(ratio_corners)]
    control.update(kappa=kappa, I0=interaction, kappa_endpoint_ratios=ratio_corners, kappa_interval=ki)
    for drug in DRUGS:
        y = means[drug]; wr = ranges[drug]
        effect = y['10'] - y['00']
        predictions = {'H_gain': y['01'] + kappa*effect,
                       'B_add': y['10'] + y['01']-y['00'],
                       'B_const': y['10']+y['01']-y['00']+interaction,
                       'B_control': m['11']}
        delta = difference(wr['10'], wr['00'])
        products = [a*b for a, b in itertools.product(ki, delta)]
        interval = [wr['01'][0]+min(products), wr['01'][1]+max(products)]
        signed = {model: (p-y['11'])/S0 for model, p in predictions.items()}
        absolute = {model: abs(e) for model, e in signed.items()}
        prep['targets'][drug] = dict(calibration={s:y[s] for s in ['00','10','01']},
            observed=y['11'], observed_interval=wr['11'], predictions=predictions,
            signed_normalized_errors=signed, absolute_normalized_errors=absolute,
            D_drug_interval=delta, endpoint_products=products, gain_prediction_interval=interval,
            technical_overlap=interval[0] <= wr['11'][1] and wr['11'][0] <= interval[1],
            gain_minus_constant_prediction=predictions['H_gain']-predictions['B_const'],
            gain_minus_constant_formula=interaction*(effect/D0-1),
            gain_minus_comparator_absolute_errors={b:absolute['H_gain']-absolute[b] for b in ['B_add','B_const','B_control']})
    prep['MAE'] = {model: sum(t['absolute_normalized_errors'][model] for t in prep['targets'].values())/5
                   for model in ['H_gain','B_add','B_const','B_control']}
    prep['gain_minus_constant_MAE'] = prep['MAE']['H_gain']-prep['MAE']['B_const']
    prep['observed_inhibitor_order_low_to_high'] = sorted(DRUGS, key=lambda drug: means[drug]['11'])
    prep['predicted_inhibitor_orders_low_to_high'] = {
        model: sorted(DRUGS, key=lambda drug: prep['targets'][drug]['predictions'][model])
        for model in ['H_gain','B_add','B_const','B_control']}

output['usage'] = dict(wall_seconds=time.perf_counter()-START_WALL,
                       cpu_seconds=time.process_time()-START_CPU,
                       external_API_calls=0, network_calls=0, monetary_cost=0)
destination = ROOT / 'review' / 'independent_result.json'
destination.write_text(json.dumps(output, indent=2, ensure_ascii=False, allow_nan=False)+'\n', encoding='utf-8')
print(json.dumps({'frozen_result': str(destination), 'sha256': digest(destination),
                  'usage':output['usage'], 'MAE':{k:v.get('MAE') for k,v in output['preparations'].items()}}, indent=2))
