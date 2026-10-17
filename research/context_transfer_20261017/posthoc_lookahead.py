"""Post-hoc check (after the one-shot confirmation) of the corrected batch lookahead in the promoted source modules.

File summary
- Path: research/context_transfer_20261017/posthoc_lookahead.py
- Purpose: the confirmation's lookahead bridge (frozen as `agent.py`, kept in the source package as
  rule ``lookahead_v1``) used the prior hit chances as its baseline after the first greedy pick.
  Its value estimates for later picks were then biased low, and with heterogeneous measurement
  rates the bias favoured rarely measured items (`POSTHOC_AVAILABILITY.json`). The source package's
  rule ``lookahead`` re-scores the baseline under the shrunk covariance. This script measures what
  that correction changes, using the promoted modules only.
- Status: exploratory and post hoc. Beat AML outcomes were opened by the confirmation and PRISM 19Q4
  is a development asset, so nothing here is confirmatory, and nothing here changes RESULTS.json.
- Core points:
  - Domains: ``beataml`` (frozen per-fold ranks from RESULTS.json, W 16, k 4, patient folds),
    ``prism_line`` and ``prism_lineage`` (rank 40, W 32, k 8, the v2 development configurations).
  - Arms: ``vc0``, ``b_exploit``, ``b_lookahead_v1`` (frozen rule) and ``b_lookahead`` (corrected),
    each through `agent.bridge_design.run_campaign`.
  - Parity: ``vc0``, ``b_exploit`` and ``b_lookahead_v1`` must reproduce the study's cached records
    context by context (``reproduces_study_records``).
  - Bridge diagnostics: the source measurement rate of the chosen bridge items and the share of bridge
    wells that returned a readout.
  - Writes POSTHOC_LOOKAHEAD_<domain>.json.
- Interfaces: `python -B posthoc_lookahead.py beataml|prism_line|prism_lineage` (maestro environment).
"""
from __future__ import annotations

import importlib
import json
import sys

import numpy as np

from common import CACHE, HERE, ROOT, folds, paired, tie_order, write_json

sys.modules.pop("agent", None)
sys.path.insert(0, str(ROOT / "src"))
bt = importlib.import_module("virtual_cell.bridged_transfer")
bd = importlib.import_module("agent.bridge_design")

ARMS = {"vc0": None, "b_exploit": "exploit", "b_lookahead_v1": "lookahead_v1", "b_lookahead": "lookahead"}
STUDY_NAME = {"vc0": "vc0", "b_exploit": "b_exploit", "b_lookahead_v1": "b_lookahead"}
CONTRASTS = (("b_lookahead", "b_lookahead_v1"), ("b_lookahead", "b_exploit"), ("b_lookahead", "vc0"),
             ("b_exploit", "vc0"), ("b_lookahead_v1", "vc0"))


def setting(name):
    if name == "beataml":
        import data_beataml
        d = data_beataml.load()
        res = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
        ranks = {int(k): int(v["rank"]) for k, v in res["choices"].items()}
        cached = json.loads((CACHE / "confirm_records.json").read_text(encoding="utf-8"))
        return d, folds(d["groups"], "context-transfer-subject"), ranks, 16, 4, None, data_beataml.MIN_MEASURED, cached
    import data_prism
    d = data_prism.load()
    regime = name.split("_")[1]
    fid = folds(d["contexts"], "context-transfer") if regime == "line" else folds(d["groups"], "context-transfer-lineage")
    cached = json.loads((CACHE / "dev" / f"v2_{regime}_w32_b8_r40.json").read_text(encoding="utf-8"))["records"]
    return d, fid, {k: 40 for k in range(5)}, 32, 8, data_prism.ABS_GATE, data_prism.MIN_MEASURED, cached


def main():
    name = sys.argv[1]
    d, fid, ranks, budget, k_bridge, abs_gate, min_measured, cached = setting(name)
    cached = {r["context"]: r for r in cached}
    Y, X, ev = d["Y"], d["X"], d["events"]
    order = tie_order(d["items"], "tie")
    recs = []
    diag = {a: {"q": [], "measured": []} for a, rule in ARMS.items() if rule}
    for k in sorted(set(fid.tolist())):
        src, tgt = np.flatnonzero(fid != k), np.flatnonzero(fid == k)
        model = bt.BridgedTransferModel(rank=ranks[k], abs_gate=abs_gate, min_measured=min_measured,
                                        impute_iters=15).fit(Y[src], X[src])
        for c in tgt:
            x = X[c] if np.isfinite(X[c]).all() else None
            rec = {"context": str(d["contexts"][c]), "group": str(d["groups"][c]), "fold": int(k)}
            for arm, rule in ARMS.items():
                camp = bd.run_campaign(model, x, lambda idx: Y[c, idx], budget, k_bridge, rule, order)
                rec[arm] = int(ev[c][camp.wells].sum())
                rec[arm + "_wasted"] = camp.wasted
                if rule:
                    diag[arm]["q"].extend(model.measured_rate[camp.bridge].tolist())
                    diag[arm]["measured"].extend(np.isfinite(Y[c, camp.bridge]).tolist())
            recs.append(rec)
        print(name, "fold", k, "rank", ranks[k], "contexts", len(tgt), flush=True)
    groups = [r["group"] for r in recs]
    mismatch = {a: sum(r[a] != cached[r["context"]][s] for r in recs) for a, s in STUDY_NAME.items()}
    out = {"status": "POST_HOC_EXPLORATORY", "domain": name, "budget": budget, "k_bridge": k_bridge,
           "ranks": ranks, "contexts": len(recs), "clusters": len(set(groups)),
           "reproduces_study_records": all(v == 0 for v in mismatch.values()), "mismatched_contexts": mismatch,
           "mean_hits": {a: float(np.mean([r[a] for r in recs])) for a in ARMS},
           "wasted_wells_per_context": {a: float(np.mean([r[a + "_wasted"] for r in recs])) for a in ARMS},
           "bridge_item_source_rate": {a: float(np.mean(v["q"])) for a, v in diag.items()},
           "bridge_wells_measured": {a: float(np.mean(v["measured"])) for a, v in diag.items()},
           "library_source_rate_mean": float(np.mean(np.isfinite(Y).mean(0))), "contrasts": {}}
    for a, b in CONTRASTS:
        st = paired(np.array([r[a] - r[b] for r in recs], float), groups)
        out["contrasts"][f"{a}-{b}"] = {"mean": st["mean"], "ci95": st["ci95"], "p_one_sided": st["p_one_sided"]}
    write_json(HERE / f"POSTHOC_LOOKAHEAD_{name}.json", out)
    write_json(CACHE / f"posthoc_lookahead_{name}_records.json", recs)
    print(json.dumps({k: out[k] for k in ("reproduces_study_records", "mismatched_contexts", "mean_hits",
                                          "bridge_wells_measured", "contrasts")}, indent=1))


if __name__ == "__main__":
    main()
