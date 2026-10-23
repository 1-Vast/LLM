"""Necessary pair-loss support check from already exposed saved outputs only."""
from collections import Counter, defaultdict
from fractions import Fraction
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'log/20261022/early_update_mechanism'
source = ROOT / 'log/20261022/ptpc_late_information/RESULT.json'
bindings = json.loads((source.parent / 'FINAL_BINDINGS.json').read_text('utf-8'))['files']
assert hashlib.sha256(source.read_bytes()).hexdigest() == bindings[source.relative_to(ROOT).as_posix()]
target = OUT / 'API_FALSIFIER_RESULT.json'
assert not target.exists()
rows = json.loads(source.read_text('utf-8'))['predictions']
groups = defaultdict(list)
for row in rows:
    groups[row['chemical_group']].append(row)
pair_count = sum(sum(r['label'] == 1 for r in values) * sum(r['label'] == 0 for r in values)
                 for values in groups.values())
duplicates = []
for key, values in groups.items():
    if len(values) > 1:
        duplicates.append({'chemical_group': key, 'pert_ids': [r['pert_id'] for r in values],
                           'labels': [r['label'] for r in values],
                           'chemical_raw_scores': [r['scores']['logistic']['Craw'] for r in values]})
checks = []
for numerator in range(-5, 6):
    s, z, a, b, shrink = Fraction(numerator, 3), Fraction(numerator, 7), Fraction(2, 5), Fraction(-3, 8), Fraction(4, 9)
    proposed = s + shrink * (a * z + b * z ** 3)
    ordinary = sum(x * beta for x, beta in zip((s, z, z ** 3), (1, shrink * a, shrink * b)))
    assert proposed == ordinary
    checks.append(str(proposed))
record = {'scope': 'Already exposed metadata/scores; zero new biological fits or outcome opens',
          'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
          'conditions': len(rows), 'groups': len(groups),
          'groups_by_size': dict(Counter(len(values) for values in groups.values())),
          'opposite_label_within_group_pairs': pair_count, 'duplicate_groups': duplicates,
          'pair_loss_has_no_data_term': pair_count == 0,
          'positive_L2_unique_zero_coefficients_if_no_pairs': pair_count == 0,
          'exact_polynomial_feature_equalities': len(checks),
          'RSI_role_claim': 'NOT_ESTABLISHED_G_IS_BASE_PREDICTOR_NOT_EDITOR'}
target.write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps({k: v for k, v in record.items() if k != 'duplicate_groups'}, indent=2))
