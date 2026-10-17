"""Post-hoc diagnostic (after the one-shot confirmation): is the lookahead loss on Beat AML a wasted-well effect?

File summary
- Path: research/context_transfer_20261017/posthoc_availability.py
- Purpose: explain, without changing any confirmatory result, why the lookahead bridge (the PRISM
  development winner) lost to exploit-first bridging on Beat AML. In the confirmation only 29% of
  lookahead bridge wells landed on a measured sample-inhibitor pair. This script asks whether the
  loss remains when no well can be spent on an unmeasured pair.
- Status: exploratory and post hoc. It reads Beat AML outcomes, which the confirmation has already
  opened, so nothing here is confirmatory. RESULTS.json is not read for outcomes and not changed.
- Core points:
  - Uses the frozen per-fold rank from RESULTS.json and the frozen budget (16) and bridge (4).
  - "standard": vc0, b_exploit and b_lookahead exactly as in the replay; these must reproduce the
    confirmation records (checked, reported as `reproduces_confirmation`).
  - "known availability": the model's per-item measurement rate is replaced, for each target, by
    that target's measured-pair indicator. This uses which pairs exist, never their values, and is
    the replay analogue of a laboratory where every chosen inhibitor can be plated. It breaks the
    protocol rule that candidates never depend on the target's availability, which is why it is a
    diagnostic only.
  - Bridge-item diagnostics per rule: source measurement rate of the chosen items and the share
    measured in the target.
  - Writes POSTHOC_AVAILABILITY.json.
- Interfaces: `python -B posthoc_availability.py` (maestro environment, Python 3.11).
"""
from __future__ import annotations

import json

import numpy as np

import data_beataml
from agent import choose_bridge, nominate
from common import CACHE, HERE, folds, paired, tie_order, write_json
from vc import ContextModel

BUDGET, K_BRIDGE, IMPUTE_ITERS, FOLD_SALT = 16, 4, 15, "context-transfer-subject"
ARMS = ("vc0", "b_exploit", "b_lookahead")
CONTRASTS = (("b_exploit", "vc0"), ("b_lookahead", "vc0"), ("b_lookahead", "b_exploit"))


def campaign(model, st0, yc, truth, arm, order):
    if arm == "vc0":
        wells = nominate(model.expected_hit(st0), BUDGET, [], order)
        bridge = np.array([], int)
    else:
        bridge = choose_bridge(arm[2:], model, st0, K_BRIDGE, BUDGET, order)
        st1 = model.posterior(st0, bridge, yc[bridge])
        final = nominate(model.expected_hit(st1), BUDGET - K_BRIDGE, bridge, order)
        wells = np.concatenate([bridge, final])
    return {"hits": int(truth[wells].sum()), "wasted": int((~np.isfinite(yc[wells])).sum()),
            "bridge": bridge}


def main():
    res = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
    ranks = {int(k): int(v["rank"]) for k, v in res["choices"].items()}
    confirm = {r["context"]: r for r in
               json.loads((CACHE / "confirm_records.json").read_text(encoding="utf-8"))}
    d = data_beataml.load()
    Y, X, ev = d["Y"], d["X"], d["events"]
    fid = folds(d["groups"], FOLD_SALT)
    order = tie_order(d["items"], "tie")
    recs, bridge_q, bridge_measured = [], {m: {a: [] for a in ARMS[1:]} for m in ("standard", "known")}, \
        {m: {a: [] for a in ARMS[1:]} for m in ("standard", "known")}
    for k in range(5):
        src, tgt = np.flatnonzero(fid != k), np.flatnonzero(fid == k)
        model = ContextModel(rank=ranks[k], abs_gate=None, min_measured=data_beataml.MIN_MEASURED,
                             impute_iters=IMPUTE_ITERS).fit(Y[src], X[src])
        q_source = model.measured_rate.copy()
        for c in tgt:
            x = X[c] if np.isfinite(X[c]).all() else None
            st0 = model.prior(x)
            yc, truth = Y[c], ev[c]
            rec = {"context": str(d["contexts"][c]), "group": str(d["groups"][c]), "fold": k}
            for mode in ("standard", "known"):
                model.measured_rate = q_source if mode == "standard" else np.isfinite(yc).astype(float)
                for arm in ARMS:
                    out = campaign(model, st0, yc, truth, arm, order)
                    rec[f"{mode}:{arm}"], rec[f"{mode}:{arm}_wasted"] = out["hits"], out["wasted"]
                    if arm != "vc0":
                        bridge_q[mode][arm].extend(q_source[out["bridge"]].tolist())
                        bridge_measured[mode][arm].extend(np.isfinite(yc[out["bridge"]]).tolist())
            model.measured_rate = q_source
            recs.append(rec)
        print("fold", k, "rank", ranks[k], "contexts", len(tgt), flush=True)
    groups = [r["group"] for r in recs]
    reproduces = all(r[f"standard:{a}"] == confirm[r["context"]][a] for r in recs for a in ARMS)
    out = {"status": "POST_HOC_EXPLORATORY", "reproduces_confirmation": bool(reproduces),
           "ranks": ranks, "contexts": len(recs), "clusters": len(set(groups)), "modes": {}}
    for mode in ("standard", "known"):
        m = {"mean_hits": {a: float(np.mean([r[f"{mode}:{a}"] for r in recs])) for a in ARMS},
             "wasted_wells_per_context": {a: float(np.mean([r[f"{mode}:{a}_wasted"] for r in recs])) for a in ARMS},
             "bridge_item_source_rate": {a: float(np.mean(v)) for a, v in bridge_q[mode].items()},
             "bridge_wells_measured": {a: float(np.mean(v)) for a, v in bridge_measured[mode].items()},
             "contrasts": {}}
        for a, b in CONTRASTS:
            st = paired(np.array([r[f"{mode}:{a}"] - r[f"{mode}:{b}"] for r in recs], float), groups)
            m["contrasts"][f"{a}-{b}"] = {"mean": st["mean"], "ci95": st["ci95"], "p_one_sided": st["p_one_sided"]}
        out["modes"][mode] = m
    out["library_source_rate_mean"] = float(np.mean(np.isfinite(Y).mean(0)))
    write_json(HERE / "POSTHOC_AVAILABILITY.json", out)
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
