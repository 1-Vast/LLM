"""Read-only checks of the final replay evidence and information boundary."""
from pathlib import Path
import hashlib
import json
import numpy as np
import pandas as pd

P = Path(__file__).resolve().parent
ROOT = P.parents[1]
freeze = json.loads((P/'FREEZE.json').read_text(encoding='utf-8'))
for name, expected in freeze['inputs'].items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
part = json.loads((P/'PARTITION.json').read_text(encoding='utf-8'))
roles = [set(part[k]) for k in ['source_cells','development_cells','evaluation_cells']]
assert not (roles[0]&roles[1] or roles[1]&roles[2] or roles[0]&roles[2])
drugs = pd.read_csv(P/'drugs.csv')
known = drugs[~drugs.withheld].name.tolist()
ordered = sorted(known, key=lambda n: hashlib.sha256(f'20261026:{n}'.encode()).hexdigest())
pool, common_test = set(ordered[::2]), set(ordered[1::2]) | set(part['withheld_drugs'])
assert not pool & common_test
trace = pd.read_csv(P/'query_trace.csv')
assert set(trace.drug) <= pool
q = trace.groupby(['phase','cell','policy']).drug.agg(['size','nunique'])
assert (q['size']==8).all() and (q['nunique']==8).all()
assert len(q)==970
replay = pd.read_csv(P/'replay_metrics.csv')
assert len(replay)==2910 and set(replay.policy)=={'random','uncertainty','exploit','counterexample','knowledge_gradient'}
assert np.isfinite(replay[['mse','utility','oracle_regret']]).all().all()
assert replay.oracle_regret.min() >= -1e-10
assert all(set(s.split('|')) <= common_test for s in replay.selected)
gates = pd.read_csv(P/'gate_metrics.csv')
coverage = gates.pivot(index=['phase','cell'],columns='method',values='coverage')
assert np.allclose(coverage['random'],coverage['uncertainty'])
summary = json.loads((P/'REPLAY_SUMMARY.json').read_text(encoding='utf-8'))
ev = replay[(replay.phase=='evaluation') & (replay.stratum=='combined')].pivot(index='cell',columns='policy',values='utility')
for method, saved in summary['direction2'].items():
    assert np.isclose((ev.counterexample-ev[method]).mean(),saved['mean'])
for direction in [4,5]:
    result = json.loads((P/f'evidence_audit/direction{direction}_results.json').read_text(encoding='utf-8'))
    assert result.get('status')
print(json.dumps({'verified':True,'frozen_files':len(freeze['inputs']),'replay_scenarios':len(q),
                  'queries':len(trace),'evaluation_cells':len(ev),'directions_present':[1,2,3,4,5,6,7,8]}))
