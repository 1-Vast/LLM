"""Exact envelopes of recorded Q procedures; never retrain an old experiment."""
import csv
from datetime import datetime, timezone
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import subprocess
import time

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/repair_information_opportunity'
REPAIR = ('M1:none:0:0', 'M1:func:10:0.0001',
          'M1:mol:10:0.0001', 'M1:both:10:0.0001')
MARGIN = F(9, 100)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mean(values):
    values = list(values)
    return sum(values, F(0)) / len(values)


def grouped(values, lineage):
    return {lin: mean(value for cell, value in values.items() if lineage[cell] == lin)
            for lin in sorted(set(lineage.values()))}


def score(values, lineage):
    return mean(grouped(values, lineage).values())


def envelope(utilities, lineage, arms):
    arms = tuple(arms)
    best = {cell: max(row[arm] for arm in arms) for cell, row in utilities.items()}
    ties = {cell: [arm for arm in arms if row[arm] == best[cell]]
            for cell, row in utilities.items()}
    by_lineage = grouped(best, lineage)
    single_action = {lin: max(mean(row[arm] for cell, row in utilities.items()
                                  if lineage[cell] == lin) for arm in arms)
                     for lin in by_lineage}
    return best, ties, mean(by_lineage.values()), mean(single_action.values())


def ratio(value):
    return {'exact': str(value), 'decimal': float(value)}


def analyze(meta):
    path = ROOT / meta['path']
    assert sha(path) == meta['sha256'] and path.stat().st_size == meta['bytes']
    utilities, lineage, context = {}, {}, {}
    with path.open(encoding='utf-8-sig', newline='') as handle:
        for row in csv.DictReader(handle):
            cell, arm = row['cell'], row['arm']
            utilities.setdefault(cell, {})
            assert arm not in utilities[cell], (cell, arm)
            if cell in lineage:
                assert lineage[cell] == row['lineage']
            lineage[cell] = row['lineage']
            identity = (row['n'], row['n_support'], row['prev'])
            assert context.setdefault(cell, identity) == identity
            assert int(row['n_support']) == 3 and int(row['n']) >= 5
            raw = F(row['prec5'])
            hits = round(raw * 5)
            assert 0 <= hits <= 5 and abs(raw - F(hits, 5)) < F(1, 10**10)
            utilities[cell][arm] = F(hits, 5)
    arms = sorted(next(iter(utilities.values())))
    assert all(sorted(row) == arms for row in utilities.values())
    assert all(set(REPAIR) | {'B1:none', 'Cmol', 'B1:kernel2'} <= set(row)
               for row in utilities.values())
    fixed = {arm: score({cell: row[arm] for cell, row in utilities.items()}, lineage)
             for arm in arms}
    menus = {'repair_only': REPAIR,
             'repair_with_B1_fallback': REPAIR + ('B1:none',),
             'repair_with_B1_Cmol_fallback': REPAIR + ('B1:none', 'Cmol'),
             'all_saved_actions': arms}
    result = {'input': meta, 'lineages': len(set(lineage.values())), 'stocks': len(utilities),
              'fixed_scores': {arm: ratio(value) for arm, value in fixed.items()},
              'hindsight_best_fixed_arms': [arm for arm in arms if fixed[arm] == max(fixed.values())],
              'recorded_precision5': {cell: {arm: str(value) for arm, value in row.items()}
                                      for cell, row in utilities.items()},
              'lineage': lineage, 'context': context, 'menus': {}}
    upper_scores = []
    for name, candidates in menus.items():
        best, ties, upper, common_lineage = envelope(utilities, lineage, candidates)
        assert upper >= common_lineage
        assert all(upper >= fixed[arm] for arm in candidates)
        upper_scores.append(upper)
        result['menus'][name] = {
            'arms': list(candidates), 'optimistic_stock_aware_upper': ratio(upper),
            'single_action_per_lineage_upper': ratio(common_lineage),
            'stock_oracle': {cell: {'precision5': str(best[cell]), 'ties': ties[cell]}
                             for cell in best},
            'lineage_oracle_precision5': {lin: str(value) for lin, value in grouped(best, lineage).items()},
            'contrasts': {baseline: {'delta_precision5': ratio(upper - fixed[baseline]),
                                    'delta_hits': ratio(5 * (upper - fixed[baseline])),
                                    'can_reach_recorded_margin': upper - fixed[baseline] >= MARGIN}
                          for baseline in ('B1:none', 'Cmol', 'B1:kernel2')},
            'versus_hindsight_best_fixed': ratio(upper - max(fixed.values()))}
    assert upper_scores == sorted(upper_scores)
    return result


def main():
    started = time.perf_counter()
    cpu = time.process_time()
    freeze = json.loads((OUT / 'FREEZE.json').read_text())
    for row in freeze['files']:
        assert sha(ROOT / row['path']) == row['sha256'], row['path']
    metadata = json.loads((OUT / 'CACHED_TABLE_IDENTITIES.json').read_text())
    # Main final table first, other base-training regimes kept strictly separate.
    metadata.sort(key=lambda row: 0 if '/final_eval/' in row['path'] else 1)
    results = [analyze(row) for row in metadata]
    primary = results[0]
    assert primary['lineages'] == 7 and primary['stocks'] == 7
    fallback = primary['menus']['repair_with_B1_fallback']['contrasts']['B1:none']
    broad = primary['menus']['all_saved_actions']['contrasts']['B1:none']
    record = {'utc': datetime.now(timezone.utc).isoformat(),
              'head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'protocol_sha256': sha(OUT / 'UPPER_BOUND_PROTOCOL.md'),
              'code_sha256': sha(Path(__file__)), 'freeze_sha256': sha(OUT / 'FREEZE.json'),
              'margin_precision5': str(MARGIN), 'margin_hits5': str(5 * MARGIN),
              'primary_B1_fallback_room': fallback['can_reach_recorded_margin'],
              'primary_all_saved_room': broad['can_reach_recorded_margin'],
              'tables': results, 'wall_seconds': time.perf_counter() - started,
              'process_cpu_seconds': time.process_time() - cpu,
              'biological_predictor_fits': 0, 'old_updates_rerun': 0, 'router_fits': 0,
              'new_raw_biological_decodes': 0, 'direct_deepseek_calls': 0,
              'scope': 'Exact recorded exposed finite-menu bound, not population/general algorithm/RSI success'}
    with (OUT / 'UPPER_BOUND_RESULT.json').open('x', encoding='utf-8') as handle:
        json.dump(record, handle, indent=2)
    print(json.dumps({'primary_fallback': fallback, 'primary_all_saved': broad,
                      'wall_seconds': record['wall_seconds'], 'fits': 0}))


if __name__ == '__main__':
    main()
