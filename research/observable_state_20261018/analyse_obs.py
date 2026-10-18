"""Analyse RECORDS.json: confirmation rates, paired contrasts (family-cluster bootstrap), withdrawal rules. Writes RESULTS_OBS.json.

Rate per (arm, family) = confirmed (0/1; no edit or untestable -> 0); Zero = mean over its 20 draws. Contrasts are paired by family.
Bootstrap: 4,000 draws, seed 20261018; one-sided 95% bounds are the 5th / 95th percentiles; one-sided family sign-flip p (20,000 flips);
Holm over the three withdrawal comparisons (P1 a3-a2, K a3-a2k, Z a3-zero). Sensitivity: clusters by the family's top PRISM target gene.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
SEED, B, FLIPS = 20261018, 4000, 20000
ARMS = ["zero", "a2", "a2k", "a3", "a3_blind"]


def table(recs, fams):
    t = {a: np.zeros(len(fams)) for a in ARMS}
    cnt = {a: np.zeros(len(fams)) for a in ARMS}
    unt = {a: 0 for a in ARMS}
    ix = {f: i for i, f in enumerate(fams)}
    for r in recs:
        i = ix[r["family"]]
        cnt[r["arm"]][i] += 1
        t[r["arm"]][i] += float(r["confirmed"])
        unt[r["arm"]] += int(not r["testable"])
    for a in ARMS:
        t[a] = np.where(cnt[a] > 0, t[a] / np.maximum(cnt[a], 1), 0.0)
    return t, cnt, unt


def boot(d, clusters, rng):
    u = sorted(set(clusters))
    groups = [np.where(np.array(clusters) == c)[0] for c in u]
    m = np.empty(B)
    for b in range(B):
        pick = rng.integers(0, len(u), len(u))
        m[b] = np.concatenate([d[groups[k]] for k in pick]).mean()
    return m


def contrast(d, clusters, rng):
    m = boot(d, clusters, rng)
    flips = rng.choice([-1, 1], size=(FLIPS, len(d)))
    p = float(((flips * d).mean(1) >= d.mean() - 1e-12).mean())
    return {"mean": float(d.mean()), "ci95": [float(np.quantile(m, .025)), float(np.quantile(m, .975))],
            "lower95_one_sided": float(np.quantile(m, .05)), "upper95_one_sided": float(np.quantile(m, .95)), "p_one_sided": p}


def main():
    import obs_core as O

    recs = json.loads((HERE / "RECORDS.json").read_text(encoding="utf-8"))
    info = json.loads((HERE / "STAGE0.json").read_text(encoding="utf-8"))
    fams = [r["family"] for r in info["families"] if r["eligible"]]
    edits = json.loads((HERE / "EDITS.json").read_text(encoding="utf-8"))
    tg = O.target_genes_by_core()
    T = O.bench.load_tables()
    cores = T["cores"].astype(str)
    top = {}
    for f in fams:
        cnt = {}
        for c in cores[T["family"] == f]:
            for g in tg.get(c, ()):
                cnt[g] = cnt.get(g, 0) + 1
        top[f] = max(cnt, key=lambda g: (cnt[g], g)) if cnt else f
    t, cnt, unt = table(recs, fams)
    rng = np.random.default_rng(SEED)
    fam_c, tgt_c = list(fams), [top[f] for f in fams]
    pairs = {"P1_a3_minus_a2": ("a3", "a2"), "K_a3_minus_a2k": ("a3", "a2k"), "Z_a3_minus_zero": ("a3", "zero"),
             "B_a3_minus_a3blind": ("a3", "a3_blind"), "a2_minus_zero": ("a2", "zero"), "a2k_minus_zero": ("a2k", "zero")}
    res = {k: {"family_cluster": contrast(t[a] - t[b], fam_c, rng), "target_cluster": contrast(t[a] - t[b], tgt_c, rng)} for k, (a, b) in pairs.items()}
    ps = sorted((res[k]["family_cluster"]["p_one_sided"], k) for k in ("P1_a3_minus_a2", "K_a3_minus_a2k", "Z_a3_minus_zero"))
    holm, run = {}, 0.0
    for i, (p, k) in enumerate(ps):
        run = max(run, min(1.0, (3 - i) * p))
        holm[k] = run
    brier = {}
    for arm in ("a2", "a3", "a3_blind"):
        by = {r["family"]: r for r in recs if r["arm"] == arm}
        pp = np.array([by[f]["p"] for f in fams if f in by])
        cc = np.array([float(by[f]["confirmed"]) for f in fams if f in by])
        brier[arm] = {"n": int(len(pp)), "brier": float(np.mean((pp - cc) ** 2)), "mean_stated_p": float(pp.mean()), "confirmed_rate": float(cc.mean())}
    withdraw = {
        "agent_vs_enumerator": bool(res["P1_a3_minus_a2"]["family_cluster"]["upper95_one_sided"] < 0.10),
        "agent_vs_knowledge_rule": bool(res["K_a3_minus_a2k"]["family_cluster"]["lower95_one_sided"] <= 0),
        "agent_vs_zero": bool(res["Z_a3_minus_zero"]["family_cluster"]["lower95_one_sided"] <= 0),
    }
    withdraw["AGENT_CLAIM_WITHDRAWN"] = bool(any(withdraw.values()))
    withdraw["TYPED_EDIT_THESIS_WITHDRAWN"] = bool(max(t["a2"].mean() - t["zero"].mean(), t["a3"].mean() - t["zero"].mean()) <= 0.10)
    out = {"scope": "internal development assessment on exposed PRISM 19Q4; not independent confirmation", "episodes": len(fams),
           "rates": {a: float(t[a].mean()) for a in ARMS}, "families_with_edit": {a: int((cnt[a] > 0).sum()) for a in ARMS},
           "untestable_edits": unt, "contrasts": res, "holm_adjusted_p": holm, "brier": brier, "withdrawal": withdraw,
           "edits_per_arm": {a: sum(1 for e in edits["edits"] if e["arm"] == a) for a in ARMS},
           "no_edit": {a: sum(1 for e in edits["no_edit"] if e["arm"] == a) for a in ARMS}}
    (HERE / "RESULTS_OBS.json").write_bytes((json.dumps(out, indent=1) + "\n").encode())
    print(json.dumps({k: out[k] for k in ("rates", "withdrawal", "holm_adjusted_p", "brier")}, indent=1))
    for k, v in res.items():
        print(k, {a: (round(b, 3) if isinstance(b, float) else [round(x, 3) for x in b]) for a, b in v["family_cluster"].items()})


if __name__ == "__main__":
    main()
