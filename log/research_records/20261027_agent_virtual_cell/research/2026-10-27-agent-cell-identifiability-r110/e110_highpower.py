"""E109: does a stronger prior raise the personalisation bar? (corrected construction)

R108 was invalid because its personalisation arm added one constant, which cannot reorder. This
uses R76's proven per-drug residual construction, so the correction actually moves candidates,
and it asserts that the personalised scores differ from the prior before reporting anything.

Pre-registered in PROTOCOL_E105.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r110"
LAMBDA = 1.0
K = 20
MS = (10, 25, 50, 100, 200)
DRAWS = 120
N_BOOT = 2000
SEED = 20261027
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
    M = np.zeros((len(vals), len(levels)))
    for t, v in enumerate(vals):
        j = idx.get(v)
        if j is not None:
            M[t, j] = 1.0
    return M


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
    for _ in range(DRAWS):
        held = cells[int(rng.integers(0, len(cells)))]
        po = np.where(CELL == held)[0]
        tr = np.where(CELL != held)[0]
        if len(po) < 600 or len(tr) < 50000:
            continue
        ytr = y[tr].astype(float)
        grand = float(ytr.mean())
        dm = {}
        for i in tr:
            dm.setdefault(A[i], []).append(y[i])
            dm.setdefault(B[i], []).append(y[i])
        deff = {k: float(np.mean(v)) - grand for k, v in dm.items()}
        base_marg = np.array([deff.get(A[i], 0.0) + deff.get(B[i], 0.0) + grand for i in po])

        Xt = Xcombo[tr]
        mu, sd = Xt.mean(axis=0), Xt.std(axis=0); sd[sd == 0] = 1.0
        Z = (Xt - mu) / sd
        w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
        base_combo = ytr.mean() + ((Xcombo[po] - mu) / sd) @ w

        pos = {v: j for j, v in enumerate(po)}
        perm = rng.permutation(len(po))
        for m in MS:
            if m >= len(po) // 2:
                continue
            meas = po[perm[:m]]
            rest = po[perm[m:]]
            row = {"cell": held, "m": m}
            for nm, base in (("marginal", base_marg), ("combo", base_combo)):
                res_meas = np.array([y[i] - base[pos[i]] for i in meas])
                # per-drug residual effects from the m measured keys (R76's construction)
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
                row[nm + "_prior"] = float(y[rest][np.argsort(-sc_base)[:K]].mean())
                row[nm + "_pers"] = float(y[rest][np.argsort(-sc_pers)[:K]].mean())
            rows.append(row)

    r = pd.DataFrame(rows)
    res = {"kind": "higher_power_personalisation_penalty_on_a_strong_prior",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "ms": list(MS), "draws": DRAWS, "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "units": int(len(r)),
                     "sanity_checks": sanity["checked"],
                     "top_k_changed": sanity["differed"],
                     "sanity_passed": bool(sanity["checked"] > 0
                                           and sanity["differed"] / max(sanity["checked"], 1) > 0.5)},
           "by_m": {}, "files": {}}

    for m in MS:
        sub = r[r.m == m]
        if len(sub) < 5:
            continue
        res["by_m"][str(m)] = {
            "n": int(len(sub)),
            "marginal_prior": float(sub["marginal_prior"].mean()),
            "marginal_pers": float(sub["marginal_pers"].mean()),
            "combo_prior": float(sub["combo_prior"].mean()),
            "combo_pers": float(sub["combo_pers"].mean()),
            "marginal_gain": paired(sub["marginal_pers"], sub["marginal_prior"], 40001 + m),
            "combo_gain": paired(sub["combo_pers"], sub["combo_prior"], 40101 + m)}

    def first_sig(prefix, off0):
        for m in MS:
            sub = r[r.m == m]
            if len(sub) < 5:
                continue
            c = paired(sub[prefix + "_pers"], sub[prefix + "_prior"], off0 + m)
            if c and c["ci95"][0] > 0:
                return m
        return None

    fm = first_sig("marginal", 38001)
    fc = first_sig("combo", 39001)
    res["thresholds"] = {"marginal": fm, "combo": fc}
    res["decisions"] = {"sanity_passed": res["audit"]["sanity_passed"],
                        "H279_bar_raised": bool(fc is not None and fm is not None and fc > fm),
                        "H280_bar_lowered": bool(fc is not None and fm is not None and fc < fm),
                        "H281_same": bool(fc == fm)}
    res["decisions"]["verdict"] = (
        "INVALID_sanity_failed" if not res["audit"]["sanity_passed"] else
        "stronger_prior_raises_the_bar" if res["decisions"]["H279_bar_raised"] else
        "stronger_prior_lowers_the_bar" if res["decisions"]["H280_bar_lowered"] else
        "threshold_unchanged")
    res["limits"] = [
        "Per-drug residuals from m measured keys are noisy for small m.",
        "Only five m values and 30 draws, so thresholds are coarse and low-powered.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r109/PROTOCOL_E105.md",
                "research/2026-10-27-agent-cell-identifiability-r109/e110_highpower.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E110_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E110_rows.csv", index=False)

    print("units=%d sanity %d/%d top-k changed -> passed=%s" % (
        len(r), sanity["differed"], sanity["checked"], res["audit"]["sanity_passed"]))
    print("thresholds: marginal=%s combo=%s" % (fm, fc))
    for m in MS:
        e = res["by_m"].get(str(m))
        if not e:
            continue
        a = e["marginal_gain"]; b = e["combo_gain"]
        print("  m=%-4d marg %.4f->%.4f (%+.4f [%+.4f,%+.4f]) | combo %.4f->%.4f (%+.4f [%+.4f,%+.4f])" % (
            m, e["marginal_prior"], e["marginal_pers"], a["mean_diff"], a["ci95"][0], a["ci95"][1],
            e["combo_prior"], e["combo_pers"], b["mean_diff"], b["ci95"][0], b["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
