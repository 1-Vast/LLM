"""Seal static review and verify only existing identity/HCT116 label evidence."""
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json

root = Path('D:/MAESTRO')
out = root/'log/20261022/ptpc_update_opportunity/source'
prior = root/'log/20261022/generative_repair_renewal/source/archive_followup'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
identities_path = prior/'S8_IDENTITY_ROWS.json'
prior_seal = json.loads((prior/'SEAL.json').read_text())
entry = next(v for v in prior_seal['files'] if v['path'].replace('\\', '/').endswith('/S8_IDENTITY_ROWS.json'))
assert sha(identities_path) == entry['sha256']
groups = json.loads((out/'HCT116_CONDITION_GROUPS.json').read_text())
eligible = {g['Pert_ID']: int(next(iter(g['labels']))) for g in groups
            if not g['control'] and g['strict_complete_candidate'] and '6' in g['times']}
assert len(eligible) == 601 and sum(eligible.values()) == 34
by_sample = defaultdict(list)
for row in json.loads(identities_path.read_text()):
    if row['Cell_line'] == 'HCT116' and row['Pert_time_(hrs)'] == '6' and row['Pert_ID'] in eligible:
        by_sample[row['Sample_ID']].append(row)
collisions = {k: sorted({(r['Cell_line'], r['Pert_ID'], r['Pert_time_(hrs)']) for r in v})
              for k, v in by_sample.items() if len({(r['Cell_line'], r['Pert_ID'], r['Pert_time_(hrs)']) for r in v}) != 1}
assert not collisions
assert {r['Pert_ID'] for values in by_sample.values() for r in values} == set(eligible)
check = dict(created_utc=datetime.now(timezone.utc).isoformat(), identities_sha256=sha(identities_path),
             eligible_conditions=len(eligible), positive_conditions=sum(eligible.values()),
             selected_rows=sum(len(v) for v in by_sample.values()), distinct_sample_ids=len(by_sample),
             context_collisions=collisions, protein_values_read=False, baseline_outputs_read=False)
check_path = out/'BASELINE_IDENTITY_CHECK.json'
assert not check_path.exists()
check_path.write_text(json.dumps(check, indent=2), encoding='utf-8')
paths = [out/'BASELINE_CODE_REVIEW.md', check_path, Path(__file__).resolve()]
seal = out/'BASELINE_CODE_REVIEW_SEAL.json'
assert not seal.exists()
seal.write_text(json.dumps(dict(created_utc=datetime.now(timezone.utc).isoformat(),
    tests='3 synthetic tests passed; no preparation/evaluation main executed by reviewer',
    files=[dict(path=str(p.relative_to(root)), sha256=sha(p)) for p in paths]), indent=2), encoding='utf-8')
print(json.dumps(dict(identity_check=check, report_sha256=sha(paths[0]), seal_sha256=sha(seal)), indent=2))
