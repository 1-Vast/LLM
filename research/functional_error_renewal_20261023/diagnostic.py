"""Source-only cohort RNA stratification; never load compressed full X or Y."""
import csv
import hashlib
import json
from pathlib import Path
import platform
import sys
import time

import numpy as np
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'log/20261023/functional_error_renewal/diagnostic'
RAW = ROOT/'data/external/beataml2_20261017'
CACHE = ROOT/'tmp/context_transfer_20261017/beataml_domain.npz'
GENE = 'ENSG00000170458'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def hashed(text):
    return int(hashlib.sha256(text.encode()).hexdigest(), 16)


def selected_auc(rows, selected, drugs):
    sums = np.zeros((len(selected), len(drugs)))
    counts = np.zeros_like(sums, dtype=int)
    positions = {context: i for i, context in enumerate(selected)}
    columns = {drug: j for j, drug in enumerate(drugs)}
    decoded = 0
    for row in rows:
        context = row['dbgap_rnaseq_sample']
        if context not in positions or row['paper_inclusion'].upper() != 'TRUE':
            continue
        if row['inhibitor'] not in columns:
            raise ValueError('Unexpected selected-source drug')
        if row['dbgap_subject_id'] != selected[context]:
            raise ValueError('Patient mapping disagreement')
        raw_value = row['auc'].strip()
        if raw_value.lower() in {'', 'na', 'nan', 'n/a'}:
            continue
        value = float(raw_value)
        if not np.isfinite(value):
            raise ValueError('Nonfinite nonmissing AUC')
        i, j = positions[context], columns[row['inhibitor']]
        sums[i, j] += value
        counts[i, j] += 1
        decoded += 1
    result = np.full_like(sums, np.nan)
    np.divide(sums, counts, out=result, where=counts > 0)
    return result, counts, decoded


def prepare():
    if (OUT/'SOURCE.npz').exists():
        raise FileExistsError('SOURCE already exists')
    with np.load(CACHE, allow_pickle=False) as cache:
        groups = cache['groups'].astype(str)
        contexts = cache['contexts'].astype(str)
        drugs = cache['items'].astype(str)
        expected = cache['input_sha256'].astype(str)
    probit = RAW/'beataml_probit_curve_fits_v4_dbgap.txt'
    expression = RAW/'beataml_waves1to4_norm_exp_dbgap.txt'
    actual = [sha(probit), sha(expression)]
    if actual != expected.tolist():
        raise ValueError('Raw source bytes differ from original cache inputs')
    choices = {}
    for patient, context in zip(groups, contexts):
        if hashed('context-transfer-subject:'+patient) % 5 != 0:
            choices[patient] = min(context, choices.get(patient, context))
    selected = {choices[p]: p for p in sorted(choices)}
    patients = np.array(list(selected.values()))
    names = np.array(list(selected))
    discovery = np.array([hashed('functional-error-cd14-discovery:'+p) % 2 == 0
                          for p in patients])
    marker = None
    matches = 0
    with expression.open(encoding='utf-8', newline='') as handle:
        reader = csv.reader(handle, delimiter='\t')
        header = next(reader)
        if len(set(header)) != len(header):
            raise ValueError('Duplicate expression header')
        indices = [header.index(context) for context in names]
        for row in reader:
            if row[0] == GENE:
                matches += 1
                if row[header.index('display_label')] != 'CD14':
                    raise ValueError('Raw marker symbol disagreement')
                marker = np.array([float(row[index]) for index in indices])
    if matches != 1 or marker is None or not np.isfinite(marker).all():
        raise ValueError('Marker identity or numeric failure')
    threshold = float(np.median(marker[discovery]))
    high = marker > threshold
    with probit.open(encoding='utf-8', newline='') as handle:
        y, counts, decoded = selected_auc(csv.DictReader(handle, delimiter='\t'),
                                         selected, drugs)
    OUT.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(OUT/'SOURCE.npz', y=y, counts=counts, patients=patients,
                        contexts=names, drugs=drugs, marker=marker,
                        discovery=discovery, high=high)
    info = dict(patients=len(patients), discovery=int(discovery.sum()),
                replication=int((~discovery).sum()), drugs=len(drugs),
                marker=GENE, threshold=threshold, input_sha256=actual,
                selected_auc_strings_decoded=decoded,
                finite_source_cells=int(np.isfinite(y).sum()),
                duplicate_assay_cells=int((counts > 1).sum()),
                nonselected_auc_numerically_decoded=0,
                nonselected_expression_numerically_decoded=0,
                source_npz_sha256=sha(OUT/'SOURCE.npz'))
    (OUT/'PREPARATION.json').write_text(json.dumps(info, indent=2), encoding='utf-8')
    return info


def moments(y, weights=None):
    mask = np.isfinite(y).astype(float)
    values = np.where(mask, y, 0.)
    weights = np.ones(len(y)) if weights is None else weights
    n = mask.T @ (weights[:, None]*mask)
    sums = values.T @ (weights[:, None]*mask)
    squares = (values*values).T @ (weights[:, None]*mask)
    cross = values.T @ (weights[:, None]*values)
    safe_n = np.maximum(n, 1.)
    cov_sum = cross-sums*sums.T/safe_n
    var_sum = np.maximum(squares-sums*sums/safe_n, 0.)
    denominator = np.sqrt(var_sum*var_sum.T)
    corr = np.zeros_like(cross)
    np.divide(cov_sum, denominator, out=corr, where=denominator > 1e-12)
    corr = np.clip(corr, -1., 1.)
    covariance = cov_sum/np.maximum(n-1, 1.)
    slope = np.zeros_like(cross)
    np.divide(cov_sum, var_sum, out=slope, where=var_sum > 1e-12)
    return dict(n=n, corr=corr, covariance=covariance, slope=slope,
                constant=denominator <= 1e-12)


def run():
    if (OUT/'RESULT.json').exists():
        raise FileExistsError('RESULT already exists')
    start = time.perf_counter()
    with np.load(OUT/'SOURCE.npz', allow_pickle=False) as source:
        y = source['y']
        d, h = source['discovery'], source['high']
        drugs = source['drugs']
    cells = [(d & ~h), (d & h), (~d & ~h), (~d & h)]
    arrays = [y[cell] for cell in cells]
    if any(len(array) == 0 for array in arrays):
        raise ValueError('Empty prespecified stratum')
    estimates = [moments(array) for array in arrays]
    eligible = np.triu(np.ones((len(drugs), len(drugs)), dtype=bool), 1)
    for estimate in estimates:
        eligible &= estimate['n'] >= 25
    ii, jj = np.where(eligible)
    result = dict(python=platform.python_version(), numpy=np.__version__,
                  seed=20261023, bootstraps=2000, eligible_pairs=len(ii),
                  cell_sizes=[len(array) for array in arrays],
                  source_sha256=sha(OUT/'SOURCE.npz'),
                  method_fits=0, scope='SOURCE_ONLY_ASSOCIATION_NOT_RISK_OR_CAUSALITY')
    if len(ii) < 30:
        result.update(decision='INSUFFICIENT_COVERAGE_STOP')
    else:
        differences = [estimates[1]['corr']-estimates[0]['corr'],
                       estimates[3]['corr']-estimates[2]['corr']]
        delta_d, delta_r = [delta[ii, jj] for delta in differences]
        statistic = float(np.mean(delta_d*delta_r))
        rng = np.random.default_rng(20261023)
        boot = []
        for _ in range(2000):
            rs = []
            for array in arrays:
                weights = np.bincount(rng.integers(0, len(array), len(array)),
                                      minlength=len(array))
                rs.append(moments(array, weights)['corr'][ii, jj])
            boot.append(float(np.mean((rs[1]-rs[0])*(rs[3]-rs[2]))))
        np.save(OUT/'BOOTSTRAP.npy', np.array(boot))
        lower, middle_low, middle_high = np.quantile(boot, [.05, .025, .975])
        records = []
        for k, (i, j) in enumerate(zip(ii, jj)):
            records.append(dict(drug_i=str(drugs[i]), drug_j=str(drugs[j]),
                                delta_discovery=float(delta_d[k]),
                                delta_replication=float(delta_r[k]),
                                cells=[{key: (bool(value[i, j]) if key == 'constant'
                                              else float(value[i, j]))
                                        for key, value in estimate.items()}
                                       for estimate in estimates]))
        (OUT/'PAIRS.json').write_text(json.dumps(records, indent=2), encoding='utf-8')
        result.update(T=statistic, bootstrap_lower_one_sided95=float(lower),
                      bootstrap_central95=[float(middle_low), float(middle_high)],
                      contrast_direction_agreement=float(np.mean(delta_d*delta_r > 0)),
                      constant_pair_cell_count=sum(int(e['constant'][ii, jj].sum())
                                                   for e in estimates),
                      correlation_reversals_discovery=int(np.sum(
                          estimates[0]['corr'][ii, jj]*estimates[1]['corr'][ii, jj] < 0)),
                      correlation_reversals_replication=int(np.sum(
                          estimates[2]['corr'][ii, jj]*estimates[3]['corr'][ii, jj] < 0)),
                      correlation_reversals_both=int(np.sum(
                          (estimates[0]['corr'][ii, jj]*estimates[1]['corr'][ii, jj] < 0)
                          & (estimates[2]['corr'][ii, jj]*estimates[3]['corr'][ii, jj] < 0))),
                      decision=('CONTINUE_ASSOCIATION_INVESTIGATION_ONLY' if lower > .01
                                else 'STOP_THIS_CD14_STRATIFIED_SOURCE_RATIONALE'))
    result['elapsed_seconds'] = time.perf_counter()-start
    (OUT/'RESULT.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    with threadpool_limits(limits=1):
        print(json.dumps(prepare() if sys.argv[1] == 'prepare' else run(), indent=2))
