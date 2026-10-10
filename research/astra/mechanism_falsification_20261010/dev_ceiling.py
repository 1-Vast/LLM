"""How well can any scorer rank the true class from a development drug's full profile? (ceiling)

All of a query's available options are used (no budget). Referenced classes only (the ranking is
over the 212 classes with reference drugs, true class among them). Scorers:

* nll_relative: the world model's profile NLL (potency-coupled, prototypes, basis), as used by the
  falsifier;
* proto_cosine: mean over shared options of cosine(query, class prototype) in the basis;
* member_mean_cosine: mean over reference members and shared options of cosine in gene space;
* nearest_member: max over reference members of the option-averaged gene-space cosine (kNN-1);
* shuffled: nll_relative with class labels of reference drugs permuted (control).
Reports the true class's rank (1 = best; ties mid-ranked), top-1/5/20 rates and the median rank,
for all queries and by activity bin. Writes development/ceiling.json.
"""
from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import numpy as np

import dev_programs as DP
import falsify as F
import study as S

HERE = Path(__file__).resolve().parent


def rank_of(scores: np.ndarray, true_i: int, larger_better: bool) -> float:
    s = scores if larger_better else -scores
    t = s[true_i]
    ok = np.isfinite(s)
    return float(np.sum(s[ok] > t) + (np.sum(s[ok] == t) + 1) / 2)


def unit(x: np.ndarray) -> np.ndarray:
    n = np.linalg.norm(x, axis=-1, keepdims=True)
    return x / np.where(n > 0, n, 1)


def main() -> dict:
    data = S.load_tier("open")
    X, moa, role = data["x"], data["moa"], data["role"]
    ref = role == "reference"
    act = DP.drug_activity(X, ref)
    out = {}
    builds = {"nll_relative": S.build(data, S.Config(score="relative", kcal="all")),
              "shuffled": S.build(data, S.Config(score="relative", kcal="all", permute_classes=True))}
    b = builds["nll_relative"]
    lib = np.array([i for i, m in enumerate(b.models) if m.kind != "knowledge"])
    names = np.array([b.models[i].name for i in lib])
    pos = {n: i for i, n in enumerate(names)}
    q = np.array([i for i in np.where(role == "development")[0] if moa[i] in pos])
    Xu = unit(np.nan_to_num(X))
    members = {c: np.where(ref & (moa == c))[0] for c in names}
    ranks = {k: [] for k in ("nll_relative", "shuffled", "proto_cosine", "member_mean_cosine", "nearest_member")}
    for qi in q:
        avail = S.available(data, qi)
        ti = pos[moa[qi]]
        for key in ("nll_relative", "shuffled"):
            bb = builds[key]
            fz = S.falsifier(bb)
            Qs, bs, As = fz.stats(bb.Z_open[qi], avail, lib)
            nll, _ = F.score_from_stats(Qs, bs, As, fz.noise.tau2, len(avail))
            ranks[key].append(rank_of(nll, ti, False))
        z = b.Z_open[qi][avail]  # (S, K)
        P = b.models[0].proto  # placeholder for shape
        pc = []
        for c in names:
            proto = b.models[b.model_index[c]].proto[avail]
            pc.append(float(np.mean(np.sum(unit(z) * unit(proto), axis=1))))
        ranks["proto_cosine"].append(rank_of(np.array(pc), ti, True))
        mm, nn = [], []
        for c in names:
            m = members[c]
            sims = []
            for j in m:
                shared = [o for o in avail if not np.isnan(X[j, o, 0])]
                if shared:
                    sims.append(float(np.mean(np.sum(Xu[qi, shared] * Xu[j, shared], axis=1))))
            mm.append(np.mean(sims) if sims else np.nan)
            nn.append(np.max(sims) if sims else np.nan)
        ranks["member_mean_cosine"].append(rank_of(np.array(mm), ti, True))
        ranks["nearest_member"].append(rank_of(np.array(nn), ti, True))
    a = act[q]
    for k, r in ranks.items():
        r = np.array(r)
        res = {}
        for lab, m in (("all", np.ones(len(r), bool)), ("act<0.5", a < 0.5), ("act0.5-0.75", (a >= 0.5) & (a < 0.75)), ("act>=0.75", a >= 0.75)):
            res[lab] = {"n": int(m.sum()), "median_rank": float(np.median(r[m])), "top1": float(np.mean(r[m] <= 1)),
                        "top5": float(np.mean(r[m] <= 5)), "top20": float(np.mean(r[m] <= 20))}
        out[k] = res
    out["n_classes"] = int(len(names))
    (HERE / "development" / "ceiling.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    return out


if __name__ == "__main__":
    r = main()
    for k, v in r.items():
        if k == "n_classes":
            print("classes", v)
            continue
        print(k, "  ".join(f"{lab}: n={x['n']} med={x['median_rank']:.0f} t1={x['top1']:.2f} t5={x['top5']:.2f} t20={x['top20']:.2f}" for lab, x in v.items()))
