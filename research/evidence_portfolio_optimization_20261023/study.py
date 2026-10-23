"""One exposed-data, paid-feedback feasibility diagnostic; never accesses AZ."""
import argparse
import csv
import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
LOG = ROOT / 'log/20261023/evidence_portfolio_optimization'
DATA = ROOT / 'data/processed/evidence_portfolio_optimization_20261023'
SOURCE = ROOT / 'data/external/gdsc_combinations/jaaks2022_figshare'
ORIGINAL = SOURCE / 'Original screen_All tissues_fitted data.csv'
VALIDATION = SOURCE / 'Validation screen_All tissues_fitted data.csv'
IDS = ['SIDM', 'ANCHOR_ID', 'ANCHOR_CONC', 'LIBRARY_ID', 'BARCODE']
VALUE = 'SYNERGY_DELTA_EMAX'


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1048576), b''):
            h.update(b)
    return h.hexdigest()


def save(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def hashed(s):
    return int(hashlib.sha256(s.encode()).hexdigest(), 16)


def key(row):
    fields = [row[c].strip() for c in ('SIDM', 'ANCHOR_ID', 'ANCHOR_CONC', 'LIBRARY_ID')]
    if any(not v or '|' in v for v in fields):
        return None  # Multi-anchor records are outside the single-anchor task.
    try:
        dose = float(fields[2])
    except ValueError:
        return None
    if not np.isfinite(dose):
        return None
    return '|'.join([fields[0], fields[1], repr(dose), fields[3]])


def freeze():
    if (LOG / 'FREEZE.json').exists():
        raise RuntimeError('Freeze already exists; do not overwrite')
    DATA.mkdir(parents=True, exist_ok=True)
    original = pd.read_csv(ORIGINAL, usecols=IDS, dtype=str, keep_default_na=False)
    val = pd.read_csv(VALIDATION, usecols=IDS, dtype=str, keep_default_na=False)
    assert not set(original.BARCODE) & set(val.BARCODE)
    assert val.groupby('BARCODE').SIDM.nunique().max() == 1
    ounits = {key(row) for row in original.to_dict('records')}
    ounits.discard(None)
    groups = defaultdict(lambda: [set(), set()])
    for row in val.to_dict('records'):
        u, b = key(row), row['BARCODE'].strip()
        if u is None:
            continue
        groups[u][hashed('portfolio-role-v1:' + b) % 2].add(b)
    records = []
    for u, roles in sorted(groups.items()):
        if u in ounits and all(roles):
            chosen = [min(bs, key=lambda b: hashed('portfolio-read-v1:' + u + '|' + b)) for bs in roles]
            records.append({'unit': u, 'sidm': u.split('|')[0], 'scout_plate': chosen[0], 'final_plate': chosen[1]})
    metadata = DATA / 'ELIGIBLE.json'
    save(metadata, records)
    files = sorted(Path(__file__).parent.glob('*.py')) + [LOG / 'PROTOCOL.md',
             LOG / 'PRE_FREEZE_REVISIONS.md', ORIGINAL, VALIDATION, metadata]
    save(LOG / 'FREEZE.json', {'created_utc': datetime.now(timezone.utc).isoformat(),
         'question': 'paid scout feasibility; exposed Jaaks only',
         'K': len(records), 'source_rows': {'original': len(original), 'validation': len(val)},
         'metadata_excluded_rows': {label: sum(key(r) is None for r in df.to_dict('records'))
                                    for label, df in (('original', original), ('validation', val))},
         'files': {str(p.relative_to(ROOT)).replace('\\', '/'): digest(p) for p in files}})
    print('Metadata-only freeze:', len(records), 'units', flush=True)


def values(path, allowed):
    """Convert response only for whitelisted (unit, plate) rows, never other responses."""
    out = defaultdict(list)
    with path.open(encoding='utf-8', newline='') as f:
        for row in csv.DictReader(f):
            k = (key(row), row['BARCODE'].strip())
            if k not in allowed:
                continue
            try:
                y = float(row[VALUE])
            except ValueError:
                continue
            if np.isfinite(y):
                out[k].append(y)
    return {k: float(np.mean(v)) for k, v in out.items()}


def rank(values_):
    # Sorted eligible unit order breaks ties without looking at any final response.
    return np.argsort(-np.nan_to_num(values_, nan=-np.inf), kind='stable')


def choose(p, scout, units):
    K = len(p)
    S, F = int(0.4 * K), int(0.2 * K)
    first = rank(p)[:S]
    order = rank(p[first])
    feedback = rank(scout[first])
    ordinal = np.empty((2, S))
    ordinal[0, order] = np.arange(S)
    ordinal[1, feedback] = np.arange(S)
    return first, {'fixed': first[order[:F]], 'feedback': first[feedback[:F]],
          'mix': first[np.argsort(ordinal.mean(0), kind='stable')[:F]],
          'random': np.array(sorted(first, key=lambda i: hashed('portfolio-random-v1:' + units[i]))[:F]),
          'direct': rank(p)[:(S + F) // 2]}


def run():
    frozen = json.loads((LOG / 'FREEZE.json').read_text(encoding='utf-8'))
    assert all(digest(ROOT / p) == h for p, h in frozen['files'].items()), 'Frozen content changed'
    meta = json.loads((DATA / 'ELIGIBLE.json').read_text(encoding='utf-8'))
    units = [r['unit'] for r in meta]
    selected = set(units)
    # Only original metadata is parsed here to construct a score whitelist.
    ids = pd.read_csv(ORIGINAL, usecols=IDS, dtype=str, keep_default_na=False)
    allowed = {(key(row), row['BARCODE'].strip()) for row in ids.to_dict('records') if key(row) in selected}
    by_unit = defaultdict(list)
    for (u, _), v in values(ORIGINAL, allowed).items():
        by_unit[u].append(v)
    p = np.array([np.mean(by_unit[u]) if by_unit[u] else np.nan for u in units])
    first = rank(p)[:int(0.4 * len(meta))]
    scout_values = values(VALIDATION, {(units[i], meta[i]['scout_plate']) for i in first})
    scout = np.array([scout_values.get((u, meta[i]['scout_plate']), np.nan) for i, u in enumerate(units)])
    first, choices = choose(p, scout, units)
    paid_scouts = {a: rank(p)[:len(idx) + (len(first) + len(choices['fixed'])) % 2]
                   if a == 'direct' else first for a, idx in choices.items()}
    choice_path = DATA / 'CHOICES.json'
    save(choice_path, {'scouts': first.tolist(), 'scouts_by_arm': {a: x.tolist() for a, x in paid_scouts.items()},
                      'finals': {a: x.tolist() for a, x in choices.items()}})
    save(LOG / 'CHOICES_FREEZE.json', {'created_utc': datetime.now(timezone.utc).isoformat(), 'sha256': digest(choice_path),
         'timing': 'Saved before converting final-role response fields', 'final_outcomes_used_for_choices': False})
    final_values = values(VALIDATION, {(units[i], meta[i]['final_plate']) for x in choices.values() for i in x})
    final = np.array([final_values.get((u, meta[i]['final_plate']), np.nan) for i, u in enumerate(units)])
    arrays = DATA / 'OBSERVED.npz'
    np.savez_compressed(arrays, p=p, scout=scout, final=final)
    lines = sorted({r['sidm'] for r in meta})
    line_index = np.array([lines.index(r['sidm']) for r in meta])
    boot = np.random.default_rng(20261023).integers(0, len(lines), (2000, len(lines)))
    planned_reads = len(first) + len(choices['fixed'])
    summary, cluster_counts = {}, {}
    for a, idx in choices.items():
        charged_scouts = len(paid_scouts[a])
        assert charged_scouts + len(idx) == planned_reads
        summary[a] = {'planned_reads': planned_reads, 'scout_reads': charged_scouts,
                      'final_reads': len(idx), 'missing_final_reads': int(np.isnan(final[idx]).sum()),
                      'missing_paired_scout_reads': int(np.isnan(scout[idx]).sum()),
                      'missing_paid_scout_reads': int(np.isnan(scout[paid_scouts[a]]).sum())}
        for threshold in (0.10, 0.0):
            k = str(threshold)
            positive = (final[idx] > threshold) & (scout[idx] > threshold)
            hits = int(positive.sum())
            cluster_counts[(a, k)] = np.bincount(line_index[idx], weights=positive, minlength=len(lines))
            summary[a][k] = {'repeat_positive': hits, 'per_1000_planned_wells': 1000 * hits / (7 * planned_reads),
                             'repeat_positive_fraction': hits / len(idx),
                             'positive_final_reads_secondary': int((final[idx] > threshold).sum())}
    differences = {}
    for a in ('fixed', 'direct', 'mix'):
        d = cluster_counts[('feedback', '0.1')] - cluster_counts[(a, '0.1')]
        differences[a] = {'positive_count_difference': int(d.sum()),
                           'sidm_bootstrap_95pct': np.quantile(d[boot].sum(1), [.025, .975]).tolist()}
    f, base, direct = [summary[a]['0.1']['repeat_positive'] for a in ('feedback', 'fixed', 'direct')]
    ratio = f / base if base else None
    passed = ratio is not None and ratio >= 1.2 and f > direct and all(differences[a]['sidm_bootstrap_95pct'][0] > 0 for a in ('fixed', 'direct'))
    result = {'K': len(meta), 'SIDM_clusters': len(lines), 'scout_count': len(first),
       'missing_scout_reads': int(np.isnan(scout[first]).sum()), 'summary': summary,
       'feedback_over_fixed_primary_ratio': ratio, 'primary_paired_differences': differences,
       'scout_final_count_upper_bound': len(choices['fixed']),
       'decision': 'DEVELOPMENT_FEASIBILITY_PASS' if passed else 'STOP_THIS_SCOUT_CONFIGURATION',
       'no_certification_or_world_agent_inheritance_RSI_claim': True,
       'artifact_hashes': {p.name: digest(p) for p in (DATA / 'ELIGIBLE.json', choice_path, arrays)}}
    save(LOG / 'RESULTS.json', result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('stage', choices=['freeze', 'run'])
    args = parser.parse_args()
    freeze() if args.stage == 'freeze' else run()
