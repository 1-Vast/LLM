"""Compare root frozen membership with the prior independent identity audit."""
import csv
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'log/20261023/distribution_health_qualification'
DATA_SOURCE = ROOT / 'data/external/research_sources/20261023/distribution_health_qualification/source'
AUDIT = json.loads((PHASE / 'biology/IDENTITY_AUDIT.json').read_text(encoding='utf-8'))

def read(name):
    with (PHASE / name).open(encoding='utf-8-sig', newline='') as handle:
        return list(csv.DictReader(handle, delimiter='\t'))

with (DATA_SOURCE / 'all_metadata.body').open(encoding='utf-8-sig', newline='') as handle:
    conditions = {(r['Metadata_pert_name'], r['Metadata_cell_line']) for r in csv.DictReader(handle, delimiter='\t')}
with (DATA_SOURCE / 'idr_target_metadata.body').open(encoding='utf-8-sig', newline='') as handle:
    pairs = {(r['Reagent Identifier'], r['Gene Identifier']) for r in csv.DictReader(handle) if r['Gene Identifier']}
known = dict(pairs)
controls = set(AUDIT['source_control_guides']) | {'EMPTY'}
unknown = set(AUDIT['source_unresolved_noncontrol_guides'])
expected_e = {(g, line, known[g]) for g, line in conditions if g not in controls | unknown}
expected_x = {(g, line, 'reference_control' if g in controls else 'missing_or_conflicting_target_id') for g, line in conditions if g in controls | unknown}
erows, xrows = read('ELIGIBILITY.tsv'), read('EXCLUSIONS.tsv')
actual_e = {(r['guide'], r['cell_line'], r['canonical_target_id']) for r in erows}
actual_x = {(r['guide'], r['cell_line'], r['reason']) for r in xrows}
record = json.loads((PHASE / 'ELIGIBILITY_RECORD.json').read_text(encoding='utf-8'))
checks = {
    'exact_eligible_membership_and_ids': actual_e == expected_e,
    'exact_excluded_membership_and_reasons': actual_x == expected_x,
    'no_eligible_duplicate_rows': len(erows) == len(actual_e),
    'no_excluded_duplicate_rows': len(xrows) == len(actual_x),
    'complete_disjoint_condition_coverage': ({r[:2] for r in actual_e} | {r[:2] for r in actual_x}) == conditions and not ({r[:2] for r in actual_e} & {r[:2] for r in actual_x}),
    'braf_both_guides_all_lines_one_id': {(g, line, 'ENSG00000157764') for g in ['BRAF1-1', 'BRAF-2'] for line in ['A549', 'ES2', 'HCC44']} <= actual_e,
    'source_hashes_match_prior_audit': all(hashlib.sha256((DATA_SOURCE / n).read_bytes()).hexdigest() == h for n, h in AUDIT['source_sha256'].items()),
    'frozen_table_hashes_match_root_record': all(hashlib.sha256((PHASE / n).read_bytes()).hexdigest() == h for n, h in record['sha256'].items()),
}
result = {'checks': checks, 'pass': all(checks.values()), 'eligible_conditions': len(actual_e), 'eligible_guides': len({r[0] for r in actual_e}), 'canonical_ids': len({r[2] for r in actual_e}), 'exclusion_reason_counts': dict(Counter(r[2] for r in actual_x)), 'scope': 'metadata membership only; no predictive split or label values audited'}
(PHASE / 'biology/ELIGIBILITY_REVIEW.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(json.dumps(result, indent=2))
assert result['pass']
