"""Independent raw-CSV reconstruction of the frozen exposed Jaaks diagnostic."""
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261023/evidence_portfolio_optimization'
DATA = ROOT / 'data/processed/evidence_portfolio_optimization_20261023'
SOURCE = ROOT / 'data/external/gdsc_combinations/jaaks2022_figshare'
ORIGINAL = SOURCE / 'Original screen_All tissues_fitted data.csv'
VALIDATION = SOURCE / 'Validation screen_All tissues_fitted data.csv'


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            h.update(block)
    return h.hexdigest()


def hkey(value):
    return hashlib.sha256(value.encode()).digest()


def identity(row):
    sidm, anchor, dose, library = (row[c].strip() for c in
                                  ('SIDM', 'ANCHOR_ID', 'ANCHOR_CONC', 'LIBRARY_ID'))
    if any(not x or '|' in x for x in (sidm, anchor, dose, library)):
        return None
    try:
        value = float(dose)
    except ValueError:
        return None
    return '|'.join((sidm, anchor, repr(value), library)) if math.isfinite(value) else None


def rows(path):
    with path.open(encoding='utf-8', newline='') as stream:
        yield from csv.DictReader(stream)


def selected_values(path, allowed):
    samples = defaultdict(list)
    conversions = 0
    for row in rows(path):
        k = identity(row), row['BARCODE'].strip()
        if k not in allowed:
            continue
        conversions += 1
        try:
            y = float(row['SYNERGY_DELTA_EMAX'])
        except ValueError:
            continue
        if math.isfinite(y):
            samples[k].append(y)
    return {k: math.fsum(v) / len(v) for k, v in samples.items()}, conversions


def descending(values, indices):
    return sorted(indices, key=lambda i: (not math.isfinite(values[i]),
                                         -values[i] if math.isfinite(values[i]) else 0, i))


def compare(actual, expected):
    if isinstance(expected, dict):
        assert set(actual) == set(expected), (set(actual), set(expected))
        for k in expected:
            compare(actual[k], expected[k])
    elif isinstance(expected, (list, tuple)):
        assert len(actual) == len(expected)
        for a, e in zip(actual, expected):
            compare(a, e)
    elif isinstance(expected, float):
        assert math.isclose(actual, expected, rel_tol=1e-12, abs_tol=1e-12), (actual, expected)
    else:
        assert actual == expected, (actual, expected)


def main():
    frozen, result = read_json(LOG / 'FREEZE.json'), read_json(LOG / 'RESULTS.json')
    checked = {name: sha(ROOT / name) == expected for name, expected in frozen['files'].items()}
    assert all(checked.values())
    eligible, reported_choices = read_json(DATA / 'ELIGIBLE.json'), read_json(DATA / 'CHOICES.json')
    choice_receipt = read_json(LOG / 'CHOICES_FREEZE.json')
    assert choice_receipt['sha256'] == sha(DATA / 'CHOICES.json')
    assert choice_receipt['final_outcomes_used_for_choices'] is False
    assert frozen['created_utc'] < choice_receipt['created_utc']
    assert all(sha(DATA / name) == expected for name, expected in result['artifact_hashes'].items())

    original_units, original_barcodes, original_pairs = set(), set(), set()
    row_counts, exclusions = {}, {}
    for label, path in (('original', ORIGINAL), ('validation', VALIDATION)):
        n = excluded = 0
        roles, plate_lines = defaultdict(lambda: [set(), set()]), defaultdict(set)
        for row in rows(path):
            n += 1
            u, barcode = identity(row), row['BARCODE'].strip()
            if label == 'original':
                original_barcodes.add(barcode)
                if u is not None:
                    original_units.add(u)
                    original_pairs.add((u, barcode))
            else:
                plate_lines[barcode].add(row['SIDM'])
                if u is not None:
                    role = int.from_bytes(hkey('portfolio-role-v1:' + barcode), 'big') % 2
                    roles[u][role].add(barcode)
            excluded += u is None
        row_counts[label], exclusions[label] = n, excluded
    assert not original_barcodes & set(plate_lines)
    assert max(map(len, plate_lines.values())) == 1
    expected_meta = []
    for u in sorted(roles):
        if u not in original_units or not all(roles[u]):
            continue
        selected = [min(group, key=lambda b: hkey('portfolio-read-v1:' + u + '|' + b)) for group in roles[u]]
        expected_meta.append(dict(unit=u, sidm=u.split('|')[0], scout_plate=selected[0], final_plate=selected[1]))
    assert eligible == expected_meta
    compare(frozen['source_rows'], row_counts)
    compare(frozen['metadata_excluded_rows'], exclusions)
    K = len(eligible)
    units = [r['unit'] for r in eligible]
    unit_set = set(units)
    original_values, n_original = selected_values(ORIGINAL, {pair for pair in original_pairs if pair[0] in unit_set})
    grouped = defaultdict(list)
    for (u, _), value in original_values.items():
        grouped[u].append(value)
    p = np.array([math.fsum(grouped[u]) / len(grouped[u]) if grouped[u] else np.nan for u in units])
    original_order = descending(p, range(K))
    S, F = int(.4 * K), int(.2 * K)
    scouts = original_order[:S]
    source_scout, n_scout = selected_values(VALIDATION, {(units[i], eligible[i]['scout_plate']) for i in scouts})
    scout = np.array([source_scout.get((u, eligible[i]['scout_plate']), np.nan) for i, u in enumerate(units)])
    feedback_order = descending(scout, scouts)
    original_ranks = {i: j for j, i in enumerate(scouts)}
    feedback_ranks = {i: j for j, i in enumerate(feedback_order)}
    choices = {
        'fixed': scouts[:F], 'feedback': feedback_order[:F],
        'mix': sorted(scouts, key=lambda i: (original_ranks[i] + feedback_ranks[i], original_ranks[i]))[:F],
        'random': sorted(scouts, key=lambda i: hkey('portfolio-random-v1:' + units[i]))[:F],
        'direct': original_order[:(S + F) // 2],
    }
    paid = {a: original_order[:len(idx) + (S + F) % 2] if a == 'direct' else scouts for a, idx in choices.items()}
    compare(reported_choices, dict(scouts=scouts, scouts_by_arm=paid, finals=choices))
    final_allowed = {(units[i], eligible[i]['final_plate']) for idx in choices.values() for i in idx}
    source_final, n_final = selected_values(VALIDATION, final_allowed)
    final = np.array([source_final.get((u, eligible[i]['final_plate']), np.nan) for i, u in enumerate(units)])
    with np.load(DATA / 'OBSERVED.npz', allow_pickle=False) as saved:
        for name, values in (('p', p), ('scout', scout), ('final', final)):
            np.testing.assert_allclose(values, saved[name], rtol=1e-12, atol=1e-12, equal_nan=True)

    lines = sorted({r['sidm'] for r in eligible})
    line_index = {line: j for j, line in enumerate(lines)}
    line = np.array([line_index[r['sidm']] for r in eligible])
    counts, summary = {}, {}
    for arm, selected in choices.items():
        idx = np.array(selected)
        summary[arm] = dict(planned_reads=S + F, scout_reads=len(paid[arm]), final_reads=len(idx),
                            missing_final_reads=int(np.isnan(final[idx]).sum()),
                            missing_paired_scout_reads=int(np.isnan(scout[idx]).sum()),
                            missing_paid_scout_reads=int(np.isnan(scout[paid[arm]]).sum()))
        assert len(paid[arm]) + len(selected) == S + F
        for threshold in (.1, .0):
            repeated = (scout[idx] > threshold) & (final[idx] > threshold)
            hits = int(repeated.sum())
            counts[arm, str(threshold)] = np.array([sum(bool(hit) for i, hit in zip(idx, repeated) if line[i] == j)
                                                   for j in range(len(lines))])
            summary[arm][str(threshold)] = dict(repeat_positive=hits,
                per_1000_planned_wells=1000 * hits / (7 * (S + F)), repeat_positive_fraction=hits / len(idx),
                positive_final_reads_secondary=int((final[idx] > threshold).sum()))
    compare(result['summary'], summary)
    boot = np.random.default_rng(20261023).integers(0, len(lines), (2000, len(lines)))
    differences = {}
    for arm in ('fixed', 'direct', 'mix'):
        delta = counts['feedback', '0.1'] - counts[arm, '0.1']
        differences[arm] = dict(positive_count_difference=int(delta.sum()),
                               sidm_bootstrap_95pct=np.quantile(delta[boot].sum(1), [.025, .975]).tolist())
    compare(result['primary_paired_differences'], differences)
    f, fixed, direct = (summary[a]['0.1']['repeat_positive'] for a in ('feedback', 'fixed', 'direct'))
    ratio = f / fixed if fixed else None
    compare(result['feedback_over_fixed_primary_ratio'], ratio)
    passed = ratio is not None and ratio >= 1.2 and f > direct and all(
        differences[a]['sidm_bootstrap_95pct'][0] > 0 for a in ('fixed', 'direct'))
    assert result['decision'] == ('DEVELOPMENT_FEASIBILITY_PASS' if passed else 'STOP_THIS_SCOUT_CONFIGURATION')
    assert result['K'] == K and result['SIDM_clusters'] == len(lines) and result['scout_count'] == S
    assert result['missing_scout_reads'] == int(np.isnan(scout[scouts]).sum())
    assert result['scout_final_count_upper_bound'] == F
    np.savez_compressed(DATA / 'AUDIT_RAW_RECONSTRUCTION.npz', p=p, scout=scout, final=final,
                        sidm=line, **{f'{a}_repeat_by_sidm': counts[a, '0.1'] for a in choices})
    supplementary = None
    if (LOG / 'SIMPLE_CONTROL_RESULTS.json').exists():
        simple = read_json(LOG / 'SIMPLE_CONTROL_RESULTS.json')
        simple_receipt = read_json(LOG / 'SIMPLE_CHOICES_RECEIPT.json')
        simple_choices = {
            'gate_original': sorted(scouts, key=lambda i: (not scout[i] > .1, original_ranks[i]))[:F],
            'gate_random': sorted(scouts, key=lambda i: (not scout[i] > .1,
                                      hkey('portfolio-gate-random-v1:' + units[i])))[:F],
        }
        compare(read_json(DATA / 'SIMPLE_CHOICES.json'), simple_choices)
        assert simple['post_result_descriptive_only'] is True
        assert simple_receipt['post_result'] is True
        assert simple['choice_sha256'] == simple_receipt['choice_sha256'] == sha(DATA / 'SIMPLE_CHOICES.json')
        assert simple_receipt['plan_sha256'] == sha(LOG / 'SIMPLE_CONTROL_PLAN.md')
        assert simple_receipt['code_sha256'] == sha(Path(__file__).with_name('simple_controls.py'))
        assert simple['observed_sha256'] == sha(DATA / 'SIMPLE_FINALS.npz')
        simple_allowed = {(units[i], eligible[i]['final_plate']) for idx in simple_choices.values() for i in idx}
        simple_values, n_simple = selected_values(VALIDATION, simple_allowed)
        simple_final = np.array([simple_values.get((u, eligible[i]['final_plate']), np.nan) for i, u in enumerate(units)])
        with np.load(DATA / 'SIMPLE_FINALS.npz', allow_pickle=False) as saved:
            np.testing.assert_allclose(simple_final, saved['final'], rtol=1e-12, atol=1e-12, equal_nan=True)
        overlap = np.isfinite(final) & np.isfinite(simple_final)
        np.testing.assert_array_equal(final[overlap], simple_final[overlap])
        simple_summary, simple_counts = {}, {}
        for arm, selected in simple_choices.items():
            idx = np.array(selected)
            simple_summary[arm] = dict(planned_reads=S + F, final_reads=F,
                                      missing_final_reads=int(np.isnan(simple_final[idx]).sum()))
            for threshold in (.1, .0):
                repeated = (scout[idx] > threshold) & (simple_final[idx] > threshold)
                cluster = np.bincount(line[idx], weights=repeated, minlength=len(lines))
                simple_counts[arm, str(threshold)] = cluster
                delta = cluster - counts['feedback', str(threshold)]
                simple_summary[arm][str(threshold)] = dict(repeat_positive=int(repeated.sum()),
                    positive_final_reads_secondary=int((simple_final[idx] > threshold).sum()),
                    difference_from_feedback=int(delta.sum()),
                    conditional_sidm_bootstrap_95pct_difference=np.quantile(delta[boot].sum(1), [.025, .975]).tolist())
        compare(simple['summary'], simple_summary)
        assert simple['scout_positive_candidates'] == int((scout[scouts] > .1).sum())
        np.savez_compressed(DATA / 'AUDIT_SIMPLE_RAW_RECONSTRUCTION.npz', final=simple_final)
        supplementary = dict(status='PASS', exploratory_post_result=True, raw_selected_rows_parsed=n_simple,
                             unchanged_overlap_observations=int(overlap.sum()),
                             summary=simple_summary, detail_sha256=sha(DATA / 'AUDIT_SIMPLE_RAW_RECONSTRUCTION.npz'))
        if (LOG / 'COST_SENSITIVITY.json').exists():
            reported_cost = read_json(LOG / 'COST_SENSITIVITY.json')
            assert reported_cost['post_result_descriptive_only'] is True
            assert reported_cost['positive_threshold'] == .1
            rates, points = {}, {}
            for arm, idx in {**choices, **simple_choices}.items():
                paid_idx = paid[arm] if arm in paid else scouts
                cluster_cost = np.array([sum(line[i] == j for i in idx) + sum(line[i] == j for i in paid_idx)
                                         for j in range(len(lines))])
                cluster_hits = counts[arm, '0.1'] if arm in choices else simple_counts[arm, '0.1']
                assert cluster_cost.sum() == S + F
                rates[arm] = 1000 * cluster_hits[boot].sum(1) / (7 * cluster_cost[boot].sum(1))
                points[arm] = 1000 * cluster_hits.sum() / (7 * cluster_cost.sum())
            cost_differences = {arm: dict(point=points['feedback'] - points[arm],
                conditional_sidm_bootstrap_95pct=np.quantile(rates['feedback'] - rates[arm], [.025, .975]).tolist())
                for arm in ('fixed', 'direct', 'mix', 'gate_original', 'gate_random')}
            compare(reported_cost['differences_feedback_minus_control_per_1000_wells'], cost_differences)
            supplementary['cost_aware_sensitivity'] = dict(status='PASS', differences=cost_differences,
                code_sha256=sha(Path(__file__).with_name('cost_sensitivity.py')),
                plan_sha256=sha(LOG / 'COST_SENSITIVITY_PLAN.md'))
    receipt = dict(status='PASS', protected_or_AZ_access=False, verifier_sha256=sha(Path(__file__)),
        frozen_files_checked=len(checked), frozen_files_unchanged=all(checked.values()),
        eligibility_rebuilt_from_source_metadata=True, choices_rebuilt_without_final_values=True,
        permitted_response_rows_parsed=dict(original=n_original, scouts=n_scout, finals=n_final),
        K=K, SIDM=len(lines), source_rows=row_counts, metadata_exclusions=exclusions,
        planned_reads_per_arm=S + F, planned_well_proxy_per_arm=7 * (S + F),
        primary_counts={a: summary[a]['0.1']['repeat_positive'] for a in choices},
        sensitivity_zero_counts={a: summary[a]['0.0']['repeat_positive'] for a in choices},
        primary_differences=differences, decision_reproduced=result['decision'],
        array_source_max_abs_error=float(max(np.nanmax(np.abs(p - np.load(DATA / 'OBSERVED.npz')['p'])), 0)),
        detail_sha256=sha(DATA / 'AUDIT_RAW_RECONSTRUCTION.npz'),
        post_result_simple_controls=supplementary,
        limitations='Exposed validation-selected pool, fixed choices and thresholds; source and SIDM dependence remain. '
                    'Hashes/local ordering authenticate these records only, not secure blinding, global provenance or biological validity.')
    (LOG / 'NUMERIC_EVIDENCE_AUDIT.json').write_text(json.dumps(receipt, indent=2, allow_nan=False) + '\n', encoding='utf-8')
    print(json.dumps(receipt, indent=2))


if __name__ == '__main__':
    main()
