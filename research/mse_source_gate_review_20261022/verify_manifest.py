"""Independent metadata-only checks of the proposed patient/menu manifest."""
from collections import Counter, defaultdict
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'log/20261022/mse_source_gate'
m = json.loads((BASE / 'PATIENT_MENU_MANIFEST.json').read_text(encoding='utf-8'))
rows = m['rows']
assert len(rows) == len({r['sample'] for r in rows}) == 135
membership = defaultdict(set)
for r in rows:
    membership[r['patient']].add(r['partition'])
assert len(membership) == 95 and all(len(p) == 1 for p in membership.values())
ranked = sorted(membership, key=lambda p: hashlib.sha256(
    ('MSE-source-gate-20261022-patient-v1\n' + p).encode('utf-8')).hexdigest())
for i, p in enumerate(ranked):
    expected = 'source' if i < 55 else ('development' if i < 75 else 'later')
    assert membership[p] == {expected}
drugs = m['drugs']
assert len(drugs) == len(set(drugs)) == 65
probes = sorted(drugs, key=lambda d: hashlib.sha256(
    ('MSE-source-gate-20261022-fixed-probe-v1\n' + d).encode('utf-8')).hexdigest())[:8]
terminal = m['terminal_drugs']
assert len(terminal) == len(set(terminal)) == 57
assert set(terminal) == set(drugs) - set(probes)
result = {'manifest_sha256': hashlib.sha256((BASE/'PATIENT_MENU_MANIFEST.json').read_bytes()).hexdigest(),
          'patient_counts': dict(Counter(next(iter(v)) for v in membership.values())),
          'sample_counts': dict(Counter(r['partition'] for r in rows)),
          'independently_reconstructed_probes': probes, 'menu_actions': 65,
          'terminal_actions': 57, 'biological_scalar_reads': 0}
out = ROOT/'log/20261022/mse_source_gate_review/MANIFEST_REVIEW.json'
out.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
print(json.dumps(result))
