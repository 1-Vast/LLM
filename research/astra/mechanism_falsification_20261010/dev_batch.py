"""Batch confound check: does the class signal partly come from shared compound plates?

LINCS phase 1 profiled compounds in plate collections (the sig_id prefix, e.g. CPC006); Level 5
MODZ z-scores are normalised within plates, so drugs sharing a collection share plate artefacts.
Drugs of one mechanism class are often in the same collection. For each development query of a
referenced class:

* shares_batch: some reference drug of its class has a signature from one of its collections;
* batch_only scorer: rank classes by the share of their reference drugs that share a collection
  with the query (no expression used);
* the world model's full-profile rank (development/ceiling.json is recomputed here per query).
Reports ranks by shares_batch x activity, and the batch_only ranking itself.
Writes development/batch.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

import dev_ceiling as DC
import dev_programs as DP
import falsify as F
import study as S

HERE = Path(__file__).resolve().parent


def batches(split: dict) -> dict[str, set]:
    return {d: {s.split("_")[0] for s in v["sig_ids"]} for d, v in split["drugs"].items()}


def main() -> dict:
    data = S.load_tier("open")
    split = data["split"]
    bt = batches(split)
    X, moa, role, drug = data["x"], data["moa"], data["role"], data["drug"]
    ref = role == "reference"
    act = DP.drug_activity(X, ref)
    b = S.build(data, S.Config(score="relative", kcal="all"))
    fz = S.falsifier(b)
    lib = np.array([i for i, m in enumerate(b.models) if m.kind != "knowledge"])
    names = np.array([b.models[i].name for i in lib])
    pos = {n: i for i, n in enumerate(names)}
    members = {c: [str(drug[j]) for j in np.where(ref & (moa == c))[0]] for c in names}
    q = np.array([i for i in np.where(role == "development")[0] if moa[i] in pos])
    rows = []
    for qi in q:
        d = str(drug[qi])
        ti = pos[moa[qi]]
        share = np.array([np.mean([len(bt[m] & bt[d]) > 0 for m in members[c]]) for c in names])
        avail = S.available(data, qi)
        Qs, bs, As = fz.stats(b.Z_open[qi], avail, lib)
        nll, _ = F.score_from_stats(Qs, bs, As, fz.noise.tau2, len(avail))
        rows.append({"drug": d, "act": float(act[qi]), "shares_batch": bool(share[ti] > 0),
                     "rank_model": DC.rank_of(nll, ti, False), "rank_batch_only": DC.rank_of(share, ti, True),
                     "n_batches": len(bt[d])})
    res = {"n": len(rows), "share_with_class_batch": float(np.mean([r["shares_batch"] for r in rows]))}
    for lab, f in (("all", lambda r: True), ("act<0.5", lambda r: r["act"] < 0.5), ("act>=0.75", lambda r: r["act"] >= 0.75)):
        for sb in (True, False):
            rs = [r for r in rows if f(r) and r["shares_batch"] == sb]
            if rs:
                res[f"{lab}|shares={sb}"] = {"n": len(rs), "median_rank_model": float(np.median([r["rank_model"] for r in rs])),
                                             "top5_model": float(np.mean([r["rank_model"] <= 5 for r in rs])),
                                             "median_rank_batch_only": float(np.median([r["rank_batch_only"] for r in rs]))}
    rb = np.array([r["rank_batch_only"] for r in rows])
    res["batch_only_all"] = {"median_rank": float(np.median(rb)), "top5": float(np.mean(rb <= 5)), "top20": float(np.mean(rb <= 20))}
    res["rows"] = rows
    (HERE / "development" / "batch.json").write_text(json.dumps(res, indent=1), encoding="utf-8")
    return res


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: v for k, v in r.items() if k != "rows"}, indent=1))
