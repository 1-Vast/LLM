"""Independent source raw-file reconstruction; no root imports or cache X/Y."""
import csv
import hashlib
import json
import math
from pathlib import Path
import time

import numpy as np

ROOT = Path('D:/MAESTRO')
BASE = ROOT/'log/20261023/functional_error_renewal'
RAW = ROOT/'data/external/beataml2_20261017'


def digest(path):
    obj = hashlib.sha256()
    with path.open('rb') as handle:
        for block in iter(lambda: handle.read(1048576), b''):
            obj.update(block)
    return obj.hexdigest()


def integer_hash(text):
    return int(hashlib.sha256(text.encode()).hexdigest(), 16)


start = time.perf_counter()
checks = []


def require(condition, name):
    if not condition:
        raise AssertionError(name)
    checks.append(name)


freeze = json.loads((BASE/'FREEZE.json').read_text())
for name, expected in freeze['files'].items():
    require(digest(ROOT/name) == expected, 'frozen:' + name)
with np.load(ROOT/'tmp/context_transfer_20261017/beataml_domain.npz', allow_pickle=False) as cache:
    groups = cache['groups'].astype(str)
    contexts = cache['contexts'].astype(str)
    drugs = cache['items'].astype(str)
    inputs = cache['input_sha256'].astype(str).tolist()

source_rows = [i for i, p in enumerate(groups)
               if integer_hash('context-transfer-subject:' + p) % 5 != 0]
dev_rows = set(range(len(groups))) - set(source_rows)
subjects = sorted(set(groups[source_rows]))
chosen = [min(contexts[i] for i in source_rows if groups[i] == p) for p in subjects]
selected = dict(zip(chosen, subjects))
expected_d = np.array([integer_hash('functional-error-cd14-discovery:' + p) % 2 == 0
                       for p in subjects])
require(not set(subjects) & set(groups[list(dev_rows)]), 'patient-source-development-disjoint')
require(not set(chosen) & set(contexts[list(dev_rows)]), 'context-source-development-disjoint')
require(len(chosen) == len(set(chosen)) == len(subjects), 'one-unique-context-per-subject')

with np.load(BASE/'diagnostic/SOURCE.npz', allow_pickle=False) as saved:
    actual = {key: saved[key] for key in saved.files}
require(np.array_equal(actual['patients'], subjects), 'all-selected-subject-identities-and-order')
require(np.array_equal(actual['contexts'], chosen), 'all-selected-context-identities-and-order')
require(np.array_equal(actual['drugs'], drugs), 'all-drug-identities-and-order')
require(np.array_equal(actual['discovery'], expected_d), 'all-discovery-split-identities')
require(actual['y'].shape == (len(subjects), len(drugs)), 'full-source-shape')

probit = RAW/'beataml_probit_curve_fits_v4_dbgap.txt'
expr = RAW/'beataml_waves1to4_norm_exp_dbgap.txt'
require([digest(probit), digest(expr)] == inputs, 'raw-input-bytes-match-cache-original-digests')
column = {drug: i for i, drug in enumerate(drugs)}
row_number = {context: i for i, context in enumerate(chosen)}
values = {}
decoded = 0
with probit.open(encoding='utf-8', newline='') as handle:
    for row in csv.DictReader(handle, delimiter='\t'):
        context = row['dbgap_rnaseq_sample']
        if context not in selected:
            continue
        if row['paper_inclusion'].upper() != 'TRUE':
            continue
        if row['dbgap_subject_id'] != selected[context]:
            raise AssertionError('Selected source patient mismatch before AUC parse')
        if row['inhibitor'] not in column:
            raise AssertionError('Unrecognized source drug before AUC parse')
        scalar = row['auc'].strip()
        if scalar.casefold() in ('', 'na', 'nan', 'n/a'):
            continue
        number = float(scalar)
        if not math.isfinite(number):
            raise AssertionError('Unexpected selected nonfinite AUC')
        key = row_number[context], column[row['inhibitor']]
        values.setdefault(key, []).append(number)
        decoded += 1
rebuilt = np.full((len(subjects), len(drugs)), np.nan)
counts = np.zeros(rebuilt.shape, dtype=int)
for key, observations in values.items():
    rebuilt[key] = math.fsum(observations) / len(observations)
    counts[key] = len(observations)
require(np.array_equal(np.isnan(rebuilt), np.isnan(actual['y'])), 'all-source-response-missingness')
require(np.array_equal(counts, actual['counts']), 'all-source-response-duplicate-counts')
finite = np.isfinite(rebuilt)
require(np.array_equal(rebuilt[finite], actual['y'][finite]), 'all-source-response-values-exact')

marker_rows = 0
with expr.open(encoding='utf-8', newline='') as handle:
    reader = csv.reader(handle, delimiter='\t')
    header = next(reader)
    require(len(header) == len(set(header)), 'unique-expression-column-identities')
    location = [header.index(name) for name in chosen]
    for row in reader:
        if row[0] != 'ENSG00000170458':
            continue
        marker_rows += 1
        require(row[header.index('display_label')] == 'CD14', 'raw-exact-CD14-gene-and-symbol')
        marker = np.array([float(row[index]) for index in location])
require(marker_rows == 1, 'unique-exact-CD14-row')
require(np.isfinite(marker).all(), 'all-source-marker-finite')
require(np.array_equal(marker, actual['marker']), 'all-source-marker-values-exact')
threshold = float(np.median(marker[expected_d]))
require(np.array_equal(marker > threshold, actual['high']), 'all-marker-strata-from-discovery-only-threshold')
preparation = json.loads((BASE/'diagnostic/PREPARATION.json').read_text())
require(threshold == preparation['threshold'], 'discovery-marker-median-exact')
require(decoded == preparation['selected_auc_strings_decoded'], 'source-scalar-decode-accounting')
require(int(finite.sum()) == preparation['finite_source_cells'], 'finite-source-cell-accounting')
require(digest(BASE/'diagnostic/SOURCE.npz') == preparation['source_npz_sha256'], 'separated-source-payload-hash')

receipt = dict(status='PASS', checks=checks, check_count=len(checks),
               frozen_files_checked=len(freeze['files']), patients=len(subjects),
               drug_columns=len(drugs), all_source_cells=int(rebuilt.size),
               finite_source_cells=int(finite.sum()), missing_source_cells=int((~finite).sum()),
               auc_strings_numerically_decoded=decoded,
               marker_values_numerically_decoded=len(marker),
               nonselected_auc_or_expression_numerically_decoded=0,
               cache_members_decoded=['groups', 'contexts', 'items', 'input_sha256'],
               cache_X_Y_events_G_decoded=False,
               elapsed_seconds=time.perf_counter()-start,
               scope='Raw-source reconstruction and frozen-file integrity only; no statistic/bootstrap rerun')
(BASE/'critic/SOURCE_AUDIT.json').write_text(json.dumps(receipt, indent=2), encoding='utf-8')
print(json.dumps(receipt, indent=2))
