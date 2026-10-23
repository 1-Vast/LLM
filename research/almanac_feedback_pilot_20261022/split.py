"""Freeze response-independent, rectangular known-pair/new-cell pilot design."""
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/almanac_feedback_pilot/root'


def key(t):
    return json.dumps([t['pair'], t['doses']], separators=(',', ':'))


def main():
    assert not (OUT / 'SPLIT.json').exists()
    design = json.loads((OUT / 'DESIGN_SUMMARY.json').read_text())
    tasks = json.loads((OUT / 'DESIGN_TASKS.json').read_text())
    assert design['component_size_histogram'] == {'1': 60}
    cells = [x[0] for x in design['cell_components']]
    groups = {name: cells[a:b] for name, a, b in (
        ('fit', 0, 20), ('tune', 20, 30), ('development', 30, 40),
        ('selection_closed', 40, 50), ('later_closed', 50, 60))}
    opened_cells = {tuple(x) for x in cells[:40]}
    coverage = defaultdict(set)
    lookup = {}
    study_cells = defaultdict(set)
    for i, t in enumerate(tasks):
        coverage[key(t)].add(tuple(t['cell']))
        lookup[(key(t), tuple(t['cell']))] = i
        study_cells[t['study']].add(tuple(t['cell']))
    eligible = sorted(k for k, v in coverage.items() if opened_cells <= v)
    # One actual-dose design per sample pair; choose by design hash, never outcomes.
    by_pair = defaultdict(list)
    for k in eligible:
        by_pair[json.dumps(json.loads(k)[0])].append(k)
    chosen = sorted(min(v, key=lambda k: hashlib.sha256(('FF-dose-v1:' + k).encode()).hexdigest())
                    for v in by_pair.values())
    selected = [[lookup[(k, tuple(c))] for k in chosen] for c in cells[:40]]
    selected_tasks = [tasks[i] for row in selected for i in row]
    plates = {name: {('FF', t['study'], t['plate']) for t in selected_tasks if t['cell'] in cs}
              for name, cs in groups.items()}
    names = list(groups)
    assert all(not (plates[a] & plates[b]) for i, a in enumerate(names) for b in names[i + 1:])
    selected_studies = {name: {t['study'] for t in selected_tasks if t['cell'] in cs}
                        for name, cs in groups.items()}
    study_overlap = {a + '/' + b: len(selected_studies[a] & selected_studies[b])
                     for i, a in enumerate(names[:3]) for b in names[i + 1:3]}
    solo = {line for t in selected_tasks for line in t['single_agent_rows']}
    combo = {line for t in selected_tasks for line in t['combination_rows']}
    assert not solo & combo
    result = {'scope': 'metadata-only FF fixed catalog/new cell; source studies may overlap',
              'cell_groups': groups, 'ordered_cells': cells[:40], 'canonical_pair_dose_keys': chosen,
              'task_indices_by_cell_pair': selected, 'pair_count': len(chosen),
              'tasks_per_open_cell': len(chosen), 'selected_task_count': len(selected_tasks),
              'full40_coverage_pair_dose_designs': len(eligible),
              'excluded_pair_dose_designs_not_full40': len(coverage) - len(eligible),
              'multiple_full40_dose_designs_same_samplepair': sum(len(v) > 1 for v in by_pair.values()),
              'study_cell_count_histogram_all_ff': dict(Counter(map(len, study_cells.values()))),
              'study_overlap_between_open_partitions': study_overlap,
              'unique_solo_entries_open': len(solo), 'unique_combo_entries_open': len(combo),
              'source_and_target_plate_overlap': 0, 'anchor_index': 8, 'query_indices': list(range(8)),
              'design_tasks_sha256': hashlib.sha256((OUT / 'DESIGN_TASKS.json').read_bytes()).hexdigest(),
              'code_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    assert len(chosen) > 0
    (OUT / 'SPLIT.json').write_text(json.dumps(result), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('canonical_pair_dose_keys', 'task_indices_by_cell_pair')}, indent=2))


if __name__ == '__main__':
    main()
