"""FF design-only reconstruction. Never indexes or converts response columns."""
import csv
import hashlib
import io
import json
import platform
import subprocess
import time
import zipfile
from collections import Counter, defaultdict
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OLD = ROOT / 'log/20261022/post_decrypte_renewal/root/almanac_archive'
OUT = ROOT / 'log/20261022/almanac_feedback_pilot/root'
FIELDS = ('SCREENER', 'STUDY', 'PLATE', 'PANELNBR', 'CELLNBR', 'NSC1', 'SAMPLE1',
          'CONC1', 'CONCUNIT1', 'NSC2', 'SAMPLE2', 'CONC2', 'CONCUNIT2', 'VALID')


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    assert not (OUT / 'DESIGN_TASKS.json').exists()
    start = time.perf_counter()
    all_grids = json.loads((OLD / 'ELIGIBLE_DESIGN_ROWS.json').read_text())
    grids = [g for g in all_grids if g['context'][0] == 'FF']
    del all_grids
    combination = {}
    wanted_solo = set()
    plates = defaultdict(set)
    for i, g in enumerate(grids):
        assert g['single_agent_plates'] == [g['plate']]
        g['coordinates'] = []
        for line in g['combination_rows']:
            assert line not in combination
            combination[line] = i
        wanted_solo.update(g['single_agent_rows'])
        plates[tuple(g['context'][:2]) + (g['plate'],)].add(tuple(g['context'][2:]))
    solos = {}
    with zipfile.ZipFile(OLD / 'archive.zip') as z:
        with z.open('ComboDrugGrowth_Nov2017.csv') as f:
            reader = csv.reader(io.TextIOWrapper(f, encoding='utf-8-sig', newline=''))
            header = next(reader)
            pos = {k: header.index(k) for k in FIELDS}
            for line, row in enumerate(reader, 2):
                if line not in combination and line not in wanted_solo:
                    continue
                d = {k: row[v] for k, v in pos.items()}
                assert d['SCREENER'] == 'FF'
                a = (d['NSC1'], d['SAMPLE1'])
                if line in wanted_solo:
                    assert not d['NSC2']
                    solos[line] = (a, d['CONC1'], d['CONCUNIT1'], d['VALID'])
                if line in combination:
                    g = grids[combination[line]]
                    assert tuple(d[k] for k in ('SCREENER', 'STUDY', 'PANELNBR', 'CELLNBR')) == tuple(g['context'])
                    assert d['PLATE'] == g['plate']
                    b = (d['NSC2'], d['SAMPLE2'])
                    if a < b:
                        coord = (d['CONC1'], d['CONC2'])
                    else:
                        coord = (d['CONC2'], d['CONC1'])
                    assert d['CONCUNIT1'] == d['CONCUNIT2'] == 'M'
                    g['coordinates'].append((coord, line, d['VALID']))
    assert set(solos) == wanted_solo
    tasks = []
    valid = Counter()
    for g in grids:
        pair = tuple(sorted(tuple(x) for x in g['drug_samples']))
        coords = g.pop('coordinates')
        axes = [sorted({x[0][j] for x in coords}, key=Decimal) for j in range(2)]
        assert list(map(len, axes)) == [3, 3]
        mapping = {x[0]: x[1] for x in coords}
        assert len(mapping) == 9
        ordered_solos = []
        for drug, doses in zip(pair, axes):
            for dose in doses:
                hits = [line for line in g['single_agent_rows'] if solos[line][:3] == (drug, dose, 'M')]
                assert len(hits) == 1
                ordered_solos.append(hits[0])
        flags = [x[2] for x in coords] + [solos[line][3] for line in ordered_solos]
        valid.update(flags)
        tasks.append({'cell': g['context'][2:], 'study': g['context'][1], 'plate': g['plate'],
                      'pair': pair, 'doses': axes, 'combination_rows': [mapping[a, b] for a in axes[0] for b in axes[1]],
                      'single_agent_rows': ordered_solos, 'valid_flags': sorted(set(flags))})
    # Keep a single design occurrence; no value-based averaging or replicate choice.
    groups = defaultdict(list)
    for t in tasks:
        key = json.dumps([t['cell'], t['pair'], t['doses']], separators=(',', ':'))
        groups[key].append(t)
    chosen = []
    for key in sorted(groups):
        group = groups[key]
        t = min(group, key=lambda x: min(x['combination_rows']))
        t['other_occurrence_first_rows'] = sorted(min(x['combination_rows']) for x in group if x is not t)
        chosen.append(t)
    # Connected cell components expose shared physical plate dependencies.
    cells = sorted({tuple(t['cell']) for t in chosen})
    parent = {c: c for c in cells}
    def find(c):
        while parent[c] != c:
            c = parent[c]
        return c
    for members in plates.values():
        members = sorted(members)
        for c in members[1:]:
            parent[find(c)] = find(members[0])
    components = defaultdict(list)
    for c in cells:
        components[find(c)].append(c)
    ordered_components = sorted(components.values(), key=lambda c: hashlib.sha256(('ALMANAC-FF-cell-v1:' + json.dumps(sorted(c))).encode()).hexdigest())
    result = {'scope': 'DESIGN_ONLY; no response values semantically accessed',
              'git_head': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'python': platform.python_version(), 'eligible_ff_grids': len(grids), 'unique_cell_pair_dose_tasks': len(chosen),
              'duplicate_occurrence_histogram': dict(Counter(len(v) for v in groups.values())),
              'valid_flag_counts': dict(valid), 'unique_matched_solo_rows': len(solos),
              'plate_cell_histogram': dict(Counter(map(len, plates.values()))), 'cell_components': ordered_components,
              'component_size_histogram': dict(Counter(map(len, ordered_components))),
              'canonical_samplepairs': len({json.dumps(t['pair']) for t in chosen}),
              'canonical_pair_dose_designs': len({json.dumps([t['pair'], t['doses']]) for t in chosen}),
              'inputs': {name: digest(OLD / name) for name in ('archive.zip', 'ELIGIBLE_DESIGN_ROWS.json')},
              'code_sha256': digest(Path(__file__)), 'wall_s': time.perf_counter() - start}
    (OUT / 'DESIGN_TASKS.json').write_text(json.dumps(chosen), encoding='utf-8')
    (OUT / 'DESIGN_SUMMARY.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
