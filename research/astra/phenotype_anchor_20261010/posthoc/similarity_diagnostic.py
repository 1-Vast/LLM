"""POST-HOC, unregistered: does STATE place a held-out line near the right reference lines?

Compares, per held-out line, its similarity vector to the 40 reference lines computed from
(a) basal profiles, (b) observed response profiles, (c) STATE-predicted response profiles.
Descriptive only; written after RESULTS.json was seen.
"""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE))
import analysis as A, gate as G, evaluate as E

ref = G.load_reference()
_, info = A.qualified_reference()
table, names = dict(info["table"]), dict(info["names"])
ht, hn = A.P.load_counts(E.HELDOUT); table.update(ht); names.update(hn)
held = E.heldout_panel(ref, table, names)
labels5 = json.loads((HERE / "MENU.json").read_text())["labels_5uM"]
c5 = np.array([ref.labels.index(l) for l in labels5])
panel_delta = np.nanmean(ref.delta, axis=0)
refp = np.stack([A.response_profile(ref.delta[i, c5], panel_delta[c5]) for i in range(len(ref.files))])
def sims(v, M):
    c = M.mean(0); a = v - c; B = M - c
    return (B @ a) / (np.linalg.norm(B, axis=1) * np.linalg.norm(a))
out = {}
for j, f in enumerate(E.HELDOUT):
    sd, _ = E.state_delta(f, ref.labels)
    s_basal = sims(held.basal[j], ref.basal)
    s_obs = sims(A.response_profile(held.delta[j, c5], panel_delta[c5]), refp)
    s_state = sims(A.response_profile(sd[c5], panel_delta[c5]), refp)
    top = lambda s: [ref.names[ref.files[i]] for i in np.argsort(-s)[:3]]
    out[names[f]] = {"r_basal_vs_observed": float(np.corrcoef(s_basal, s_obs)[0, 1]),
                     "r_state_vs_observed": float(np.corrcoef(s_state, s_obs)[0, 1]),
                     "r_state_vs_basal": float(np.corrcoef(s_state, s_basal)[0, 1]),
                     "top3_basal": top(s_basal), "top3_observed": top(s_obs), "top3_state": top(s_state),
                     "state_similarity_range": [float(s_state.min()), float(s_state.max())],
                     "observed_similarity_range": [float(s_obs.min()), float(s_obs.max())]}
(HERE / "posthoc" / "similarity_diagnostic.json").write_text(json.dumps(out, indent=1))
for k, v in out.items():
    print(k, {kk: (round(vv, 3) if isinstance(vv, float) else vv) for kk, vv in v.items() if not kk.endswith("range")})
