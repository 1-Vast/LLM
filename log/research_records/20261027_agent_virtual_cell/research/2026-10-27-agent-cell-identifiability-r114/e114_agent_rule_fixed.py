"""E113: can the agent USE the conditional rule online?

R112 established that personalisation pays only when the prior is weak (below about 9-11%). An
agent could try to apply that rule by measuring a small probe, estimating the prior's accuracy
from it, and then deciding whether to personalise. This tests that decision end to end against
two fixed strategies.

Pre-registered in PROTOCOL_E109.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r114"
LAMBDA = 1.0
K = 20
PROBE = 100
THRESHOLD = 0.095
REPS = 3
N_BOOT = 2000
SEED = 20261027
PRIORS = {"weak": 0.10, "strong": 1.00}
USE = ["CELL_LINE_NAME", "Tissue", "ANCHOR_NAME", "LIBRARY_NAME",
       "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "Synergy"]


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def paired(a, b, off):
    j = pd.concat([a.rename("a"), b.rename("b")], axis=1).dropna()
    if len(j) < 3:
        return None
    dif = (j["a"] - j["b"]).to_numpy(float)
    rng = np.random.default_rng(SEED + off)
    boots = [float(np.mean(rng.choice(dif, size=len(dif), replace=True))) for _ in range(N_BOOT)]
    return {"n": int(len(dif)), "mean_diff": float(dif.mean()),
            "ci95": [float(np.quantile(boots, 0.025)), float(np.quantile(boots, 0.975))]}


def onehot(vals, levels):
    idx = {v: j for j, v in enumerate(levels)}
    Mt = np.zeros((len(vals), len(levels)))
    for t, v in enumerate(vals):
        j = idx.get(v)
        if j is not None:
            Mt[t, j] = 1.0
    return Mt


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    d = pd.read_csv(ORIG, low_memory=False, usecols=USE)
    d["cell"] = d["CELL_LINE_NAME"].astype(str)
    d["combo"] = d["ANCHOR_NAME"].astype(str) + " + " + d["LIBRARY_NAME"].astype(str)
    d["key"] = d["cell"] + "|" + d["combo"]
    d["syn"] = d["Synergy"].astype(str).str.lower().isin(["true", "1"])
    g = d.groupby("key", as_index=False).agg(
        cell=("CELL_LINE_NAME", "first"), a=("ANCHOR_NAME", "first"), b=("LIBRARY_NAME", "first"),
        ap=("ANCHOR_PATHWAY", "first"), lp=("LIBRARY_PATHWAY", "first"),
        tissue=("Tissue", "first"), syn=("syn", "mean"))
    g["syn"] = g["syn"] > 0.5
    for c in ("cell", "a", "b", "ap", "lp", "tissue"):
        g[c] = g[c].astype(str).fillna("NA")

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); CELL = g["cell"].to_numpy()
    drugs = sorted(set(A) | set(B)); cells = sorted(set(CELL))
    Xid = np.hstack([onehot(A, drugs), onehot(B, drugs)])
    Xpa = np.hstack([onehot(g["ap"].to_numpy(), sorted(g["ap"].unique())),
                     onehot(g["lp"].to_numpy(), sorted(g["lp"].unique())),
                     onehot(g["tissue"].to_numpy(), sorted(g["tissue"].unique()))])
    Xcombo = np.hstack([Xid, Xpa])
    y = g["syn"].to_numpy(bool)

    rng = np.random.default_rng(SEED)
    rows = []
    sanity = {"checked": 0, "differed": 0}
    for held in cells:
        po = np.where(CELL == held)[0]
        other = [c for c in cells if c != held]
        if len(po) < 200 + 2 * K or len(other) < 20:
            continue
        for pname, frac in PRIORS.items():
            keep = max(10, int(round(frac * len(other))))
            chosen = rng.choice(other, size=min(keep, len(other)), replace=False)
            tr = np.where(np.isin(CELL, chosen))[0]
            if len(tr) < 1000:
                continue
            ytr = y[tr].astype(float)
            Xt = Xcombo[tr]
            mu, sd = Xt.mean(axis=0), Xt.std(axis=0); sd[sd == 0] = 1.0
            Z = (Xt - mu) / sd
            w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
            base = ytr.mean() + ((Xcombo[po] - mu) / sd) @ w
            pos = {v: j for j, v in enumerate(po)}
            for _ in range(REPS):
                perm = rng.permutation(len(po))
                probe = po[perm[:PROBE]]
                meas = po[perm[PROBE:PROBE + 200]]
                rest = po[perm[PROBE + 200:]]
                if len(rest) < 2 * K:
                    continue
                # probe: the agent measures 20 keys and sees the flags
                probe_flags = y[probe].astype(float)
                probe_score = np.array([base[pos[i]] for i in probe])
                est_prior = float(probe_flags[np.argsort(-probe_score)[:K]].mean()) if len(probe) >= K else float("nan")
                decide = bool(np.isfinite(est_prior) and est_prior < THRESHOLD)
                # personalisation residuals from the measured 200
                res_meas = np.array([y[i] - base[pos[i]] for i in meas])
                acc = {}
                for i, rr in zip(meas, res_meas):
                    acc.setdefault(A[i], []).append(rr)
                    acc.setdefault(B[i], []).append(rr)
                reff = {k: float(np.mean(v)) for k, v in acc.items()}
                sc_base = np.array([base[pos[i]] for i in rest])
                sc_pers = np.array([base[pos[i]] + 0.5 * (reff.get(A[i], 0.0) + reff.get(B[i], 0.0))
                                    for i in rest])
                sanity["checked"] += 1
                if not np.array_equal(np.argsort(-sc_base)[:K], np.argsort(-sc_pers)[:K]):
                    sanity["differed"] += 1
                hit = y[rest].astype(float)
                rows.append({"cell": held, "prior": pname, "est_prior": est_prior,
                             "decided_personalise": decide,
                             "never": float(hit[np.argsort(-sc_base)[:K]].mean()),
                             "always": float(hit[np.argsort(-sc_pers)[:K]].mean()),
                             "adaptive": float(hit[np.argsort(-(sc_pers if decide else sc_base))[:K]].mean())})

    r = pd.DataFrame(rows)
    res = {"kind": "can_the_agent_apply_the_conditional_rule_online_with_an_identifiable_probe",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "probe": PROBE, "threshold": THRESHOLD, "reps": REPS,
                        "priors": PRIORS, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "cells_used": int(r["cell"].nunique()) if len(r) else 0,
                     "units": int(len(r)), "sanity_checks": sanity["checked"],
                     "top_k_changed": sanity["differed"],
                     "sanity_passed": bool(sanity["checked"] > 0
                                           and sanity["differed"] / max(sanity["checked"], 1) > 0.5)},
           "by_prior": {}, "files": {}}

    for pname in PRIORS:
        sub = r[r.prior == pname]
        if len(sub) < 5:
            continue
        res["by_prior"][pname] = {
            "n": int(len(sub)),
            "mean_estimated_prior": float(sub["est_prior"].mean()),
            "frac_decided_personalise": float(sub["decided_personalise"].mean()),
            "never": float(sub["never"].mean()),
            "always": float(sub["always"].mean()),
            "adaptive": float(sub["adaptive"].mean()),
            "adaptive_minus_never": paired(sub["adaptive"], sub["never"], 44001 + len(pname)),
            "adaptive_minus_always": paired(sub["adaptive"], sub["always"], 44101 + len(pname))}

    # pooled comparison across both prior strengths
    res["pooled"] = {
        "n": int(len(r)),
        "never": float(r["never"].mean()), "always": float(r["always"].mean()),
        "adaptive": float(r["adaptive"].mean()),
        "adaptive_minus_never": paired(r["adaptive"], r["never"], 44201),
        "adaptive_minus_always": paired(r["adaptive"], r["always"], 44301),
        "oracle": float(r.apply(lambda x: max(x["never"], x["always"]), axis=1).mean())}

    p = res["pooled"]
    h286 = bool(p["adaptive_minus_never"]["ci95"][0] > 0 and p["adaptive_minus_always"]["ci95"][0] > 0)
    h287 = bool(p["adaptive_minus_never"]["ci95"][0] <= 0 or p["adaptive_minus_always"]["ci95"][0] <= 0)
    est_mean = float(r["est_prior"].mean())
    ident_ok = bool(np.isfinite(est_mean) and est_mean > 0.03)
    res["identifiability_check"] = {"mean_estimated_prior": est_mean, "passed": ident_ok}
    res["decisions"] = {"sanity_passed": res["audit"]["sanity_passed"],
                        "identifiability_passed": ident_ok,
                        "H286_adaptive_beats_both_fixed": h286,
                        "H287_adaptive_fails_to_beat_both": h287,
                        "oracle_gap": float(p["oracle"] - p["adaptive"])}
    res["decisions"]["verdict"] = (
        "INVALID_sanity_failed" if not res["audit"]["sanity_passed"] else
        "INVALID_estimator_still_degenerate" if not ident_ok else
        "agent_can_apply_the_rule_online" if h286 else
        "rule_is_real_but_the_agent_cannot_apply_it_cheaply")
    res["limits"] = [
        "A 20-key probe gives an extremely noisy estimate of the prior's accuracy.",
        "The two prior strengths bracket the threshold but do not sample it continuously.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r113/PROTOCOL_E109.md",
                "research/2026-10-27-agent-cell-identifiability-r113/e114_agent_rule_fixed.py"):
        pth = ROOT / rel
        if pth.exists():
            res["files"][rel] = sha256(pth)
    (OUT / "E114_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E114_rows.csv", index=False)

    print("cells=%d units=%d sanity %d/%d passed=%s" % (
        res["audit"]["cells_used"], len(r), sanity["differed"], sanity["checked"],
        res["audit"]["sanity_passed"]))
    for pname, e in res["by_prior"].items():
        print("  [%-6s] est_prior %.4f decide %.2f | never %.4f always %.4f adaptive %.4f" % (
            pname, e["mean_estimated_prior"], e["frac_decided_personalise"],
            e["never"], e["always"], e["adaptive"]))
    print("  pooled: never %.4f always %.4f adaptive %.4f oracle %.4f" % (
        p["never"], p["always"], p["adaptive"], p["oracle"]))
    a = p["adaptive_minus_never"]; b = p["adaptive_minus_always"]
    print("  adaptive-never %+.4f [%+.4f,%+.4f] | adaptive-always %+.4f [%+.4f,%+.4f]" % (
        a["mean_diff"], a["ci95"][0], a["ci95"][1], b["mean_diff"], b["ci95"][0], b["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
