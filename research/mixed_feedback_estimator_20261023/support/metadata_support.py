"""Source-only double-RNA identity support; never open RNA matrix or outcomes."""
import csv
import gzip
import hashlib
import json
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / 'log/20261022/norman_functional_contract'
OUT = ROOT / 'log/20261023/mixed_feedback_estimator/support'
RENAMES = {'C3orf72': 'FOXL2NB', 'C19orf26': 'CBARP',
           'KIAA1804': 'RP5-862P8.2', 'RHOXF2': 'RHOXF2B'}
CONTROLS = {'NegCtrl0_NegCtrl0', 'NegCtrl10_NegCtrl0', 'NegCtrl11_NegCtrl0'}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inputs = [BASE / 'PAIR_SPLITS.csv', BASE / 'IDENTITY_JOIN.json',
              BASE / 'data/GSE133344_raw_cell_identities.csv.gz']
    panel = set(json.loads(inputs[1].read_text())['matched_single_genes']) - {'BAK1', 'BCL2L11'}
    with inputs[0].open(newline='') as stream:
        source = {r['pair']: r for r in csv.DictReader(stream)
                  if r['split'] == 'source' and {r['gene_a'], r['gene_b']} <= panel}
    pair_cells = Counter()
    pair_groups = defaultdict(Counter)
    guides = defaultdict(Counter)
    orientations = defaultdict(set)
    controls = Counter()
    singles = defaultdict(Counter)
    barcode_gem_mismatch = 0
    with gzip.open(inputs[2], 'rt', newline='') as stream:
        for r in csv.DictReader(stream):
            raw = r['guide_identity'].split('__')[0]
            parts = raw.split('_')
            if len(parts) != 2:
                continue
            a, b = [RENAMES.get(p, p) for p in parts]
            pair = '|'.join(sorted((a, b)))
            is_control = raw in CONTROLS
            is_single = ((a in panel and b == 'NegCtrl0') or
                         (b in panel and a == 'NegCtrl0'))
            if not (pair in source or is_control or is_single):
                continue
            if r['number_of_cells'] not in {'1', '1.0'} or r['good_coverage'].lower() != 'true':
                continue
            gem = r['cell_barcode'].rsplit('-', 1)[-1]
            # Only compare metadata; no raw RNA UMI threshold is asserted.
            barcode_gem_mismatch += str(r['gemgroup']).split('.')[0] != gem
            if is_control:
                controls[gem] += 1
            elif is_single:
                singles[a if a in panel else b][gem] += 1
            else:
                pair_cells[pair] += 1
                pair_groups[pair][gem] += 1
                guides[pair][r['guide_identity']] += 1
                orientations[pair].add(raw)
    records = []
    for pair, r in sorted(source.items()):
        a, b = r['gene_a'], r['gene_b']
        gems = sorted(pair_groups[pair])
        complete = [g for g in gems if controls[g] and singles[a][g] and singles[b][g]]
        records.append({'pair': pair, 'source_order': r['source_order'],
                        'identity_qc_cells': pair_cells[pair], 'gemgroups': ';'.join(gems),
                        'control_and_both_singles_gemgroups': ';'.join(complete),
                        'unique_guide_identities': len(guides[pair]),
                        'raw_orientations': ';'.join(sorted(orientations[pair]))})
    with (OUT / 'SOURCE_PAIR_METADATA.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)
    (OUT / 'SOURCE_GUIDE_LINKS.json').write_text(json.dumps({p: dict(v) for p, v in guides.items() if v}, indent=2))
    report = {'source_panel_pairs': len(source), 'source_pairs_with_identity_qc_double_cells': len(pair_cells),
              'identity_qc_source_double_cells': sum(pair_cells.values()),
              'source_supported_pair_cell_counts': sorted(pair_cells.values()),
              'all_source_pair_gemgroup_counts': dict(Counter(len(v) for v in pair_groups.values())),
              'supported_pair_guide_identity_counts': dict(Counter(len(v) for v in guides.values() if v)),
              'source_pairs_complete_local_control_and_singles': sum(bool(r['control_and_both_singles_gemgroups']) for r in records),
              'source_pairs_all_observed_gemgroups_complete': sum(bool(r['gemgroups']) and r['gemgroups'] == r['control_and_both_singles_gemgroups'] for r in records),
              'control_metadata_cells_by_gemgroup': dict(controls),
              'barcode_gemgroup_metadata_mismatches_in_allowed_cells': barcode_gem_mismatch,
              'raw_RNA_matrix_opened': False, 'function_outcomes_opened': False,
              'development_protected_coverage_computed': False, 'RNA_UMI_2000_QC_performed': False,
              'input_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}}
    (OUT / 'METADATA_REPORT.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
