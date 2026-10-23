"""Audit exact condition identities only; never decode phenotype columns."""
import ast
from collections import Counter, defaultdict
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import pyarrow.parquet as pq

OUT = Path('log/20261023/emerald_functional_rule')
OUT.mkdir(parents=True, exist_ok=True)
SOURCE = Path('log/20261023/dose_update_qualification/summary_statistics.parquet')
rows = pq.read_table(SOURCE, columns=['cell_line', 'condition']).to_pylist()
raw = sorted({row['condition'] for row in rows})
def parse(condition):
    # Decimal textual dose extraction avoids float approximate comparisons.
    value = ast.literal_eval(condition)
    return tuple((str(d), str(Decimal(str(q)).normalize()), str(u)) for d, q, u in value)

conds = {condition: parse(condition) for condition in raw}
single = {parts[0]: condition for condition, parts in conds.items()
          if len(parts) == 1 and not parts[0][0].startswith('DMSO')}
combos = {condition: parts for condition, parts in conds.items() if len(parts) > 1}
cells = defaultdict(set)
for row in rows:
    cells[row['condition']].add(row['cell_line'])
drug_doses = defaultdict(set)
for drug, dose, unit in single:
    drug_doses[drug].add((dose, unit))
audit = []
for condition, parts in combos.items():
    exact = [part in single for part in parts]
    common_cells = set(cells[condition])
    for part in parts:
        common_cells &= cells[single[part]] if part in single else set()
    audit.append({'condition': condition, 'parts': parts,
                  'exact_single_support': exact,
                  'drugs_with_no_single_at_any_dose': [p[0] for p in parts if p[0] not in drug_doses],
                  'missing_exact_single_parts': [p for p in parts if p not in single],
                  'query_contexts': len(cells[condition]),
                  'contexts_with_all_exact_support': len(common_cells)})
by_pair = defaultdict(list)
for condition, parts in combos.items():
    by_pair[' + '.join(sorted(p[0] for p in parts))].append(condition)
result = {
    'scope': 'cell_line/condition only; no phenotype values decoded',
    'input_sha256': hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
    'raw_rows': len(rows), 'contexts': len({r['cell_line'] for r in rows}),
    'conditions': len(raw), 'single_noncontrol_conditions': len(single),
    'single_drugs': len(drug_doses), 'combination_conditions': len(combos),
    'combination_arity_histogram': dict(Counter(len(p) for p in combos.values())),
    'distinct_unordered_drug_sets': len(by_pair),
    'conditions_with_all_exact_support': sum(all(a['exact_single_support']) for a in audit),
    'conditions_missing_any_exact_support': sum(not all(a['exact_single_support']) for a in audit),
    'query_context_condition_pairs': sum(a['query_contexts'] for a in audit),
    'pairs_with_all_exact_support': sum(a['contexts_with_all_exact_support'] for a in audit),
    'single_dose_curves': {d: sorted(q) for d, q in sorted(drug_doses.items())},
    'combination_curves': dict(sorted(by_pair.items())), 'combination_audit': audit,
    'no_single_anydose_drugs': sorted({d for a in audit for d in a['drugs_with_no_single_at_any_dose']}),
}
(OUT/'SOURCE_IDENTITY.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ['single_dose_curves','combination_curves','combination_audit']}, ensure_ascii=False, indent=2))
