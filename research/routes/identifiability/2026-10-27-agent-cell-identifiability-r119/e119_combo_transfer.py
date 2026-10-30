"""E119: can identity+pathway transfer to an unseen tissue?

C65 tested cross-tissue transfer for drug marginals only. The recommended model is
identity+pathway, and its transfer has never been tested - the last untested cell of the
transfer grid.

Pre-registered in PROTOCOL_E112.md.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(r"D:\MAESTRO")
ORIG = ROOT / "data" / "external" / "gdsc_combinations" / "jaaks2022_figshare" / "Original screen_All tissues_fitted data.csv"
OUT = ROOT / "research" / "2026-10-27-agent-cell-identifiability-r119"
LAMBDA = 1.0
K = 20
SUBSAMPLES = 60
SUB_SIZE = 2000
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

    A = g["a"].to_numpy(); B = g["b"].to_numpy(); T = g["tissue"].to_numpy()
    drugs = sorted(set(A) | set(B))
    tissues = sorted(set(T))
    y = g["syn"].to_numpy(bool)

    Xid = np.hstack([onehot(A, drugs), onehot(B, drugs)])
    ap_lv = sorted(g["ap"].unique()); lp_lv = sorted(g["lp"].unique()); ti_lv = sorted(g["tissue"].unique())
    Xpa = np.hstack([onehot(g["ap"].to_numpy(), ap_lv), onehot(g["lp"].to_numpy(), lp_lv),
                     onehot(g["tissue"].to_numpy(), ti_lv)])
    Xcombo = np.hstack([Xid, Xpa])

    rng = np.random.default_rng(SEED)
    rows = []
    for held in tissues:
        te = np.where(T == held)[0]
        tr = np.where(T != held)[0]
        if len(te) < 1000 or len(tr) < 5000:
            continue
        ytr = y[tr].astype(float)

        def fit(XX):
            Xt = XX[tr]
            mu, sd = Xt.mean(axis=0), Xt.std(axis=0); sd[sd == 0] = 1.0
            Z = (Xt - mu) / sd
            w = np.linalg.solve(Z.T @ Z + LAMBDA * np.eye(Z.shape[1]), Z.T @ (ytr - ytr.mean()))
            return lambda XXe: ytr.mean() + ((XXe - mu) / sd) @ w

        f_id = fit(Xid); f_cb = fit(Xcombo)
        grand = float(ytr.mean())
        dm = {}
        for i in tr:
            dm.setdefault(A[i], []).append(y[i])
            dm.setdefault(B[i], []).append(y[i])
        deff = {k: float(np.mean(v)) - grand for k, v in dm.items()}

        for _ in range(SUBSAMPLES):
            sub = rng.choice(te, size=min(SUB_SIZE, len(te)), replace=False)
            s_m = np.array([deff.get(A[i], 0.0) + deff.get(B[i], 0.0) + grand for i in sub])
            s_id = f_id(Xid[sub])
            s_cb = f_cb(Xcombo[sub])
            hit = y[sub].astype(float)
            rows.append({"held": held,
                         "marginal": float(hit[np.argsort(-s_m)[:K]].mean()),
                         "identity": float(hit[np.argsort(-s_id)[:K]].mean()),
                         "combo": float(hit[np.argsort(-s_cb)[:K]].mean()),
                         "random": float(hit[rng.choice(len(sub), size=K, replace=False)].mean()),
                         "base": float(hit.mean())})

    r = pd.DataFrame(rows)
    res = {"kind": "can_identity_plus_pathway_transfer_to_an_unseen_tissue",
           "input_sha256": sha256(ORIG),
           "settings": {"k": K, "subsamples": SUBSAMPLES, "lambda": LAMBDA,
                        "n_boot": N_BOOT, "seed": SEED},
           "audit": {"keys": int(len(g)), "units": int(len(r)), "tissues": tissues},
           "by_tissue": {}, "files": {}}

    for held in tissues:
        sub = r[r.held == held]
        if len(sub) < 5:
            continue
        res["by_tissue"][held] = {
            "n": int(len(sub)), "base": float(sub["base"].mean()),
            "marginal": float(sub["marginal"].mean()), "identity": float(sub["identity"].mean()),
            "combo": float(sub["combo"].mean()), "random": float(sub["random"].mean()),
            "combo_minus_random": paired(sub["combo"], sub["random"], 46001 + len(held)),
            "combo_minus_identity": paired(sub["combo"], sub["identity"], 46101 + len(held)),
            "combo_minus_marginal": paired(sub["combo"], sub["marginal"], 46201 + len(held))}

    def wins(key):
        return sum(1 for e in res["by_tissue"].values() if e[key]["ci95"][0] > 0)

    w_rand = wins("combo_minus_random"); w_id = wins("combo_minus_identity"); w_marg = wins("combo_minus_marginal")
    res["decisions"] = {"combo_beats_random_pools": w_rand, "combo_beats_identity_pools": w_id,
                        "combo_beats_marginal_pools": w_marg,
                        "H296_transfers_everywhere": w_rand == len(res["by_tissue"]),
                        "H297_annotation_increment_survives": w_id >= 2,
                        "H298_combo_beats_marginal_under_transfer": w_marg >= 2}
    res["decisions"]["verdict"] = (
        "recommended_model_transfers_and_beats_marginals" if res["decisions"]["H296_transfers_everywhere"]
        and res["decisions"]["H298_combo_beats_marginal_under_transfer"] else
        "recommended_model_transfers_but_not_clearly_better_than_marginals" if res["decisions"]["H296_transfers_everywhere"] else
        "recommended_model_does_not_transfer")
    res["limits"] = [
        "Only three tissues, so three folds.",
        "Tissue is one of the combo model's own features, so holding it out removes a feature it was trained to use.",
        "Retrospective; no mechanism, clinical or drug-choice claim; no meta-learning or RSI.",
    ]
    for rel in ("research/2026-10-27-agent-cell-identifiability-r119/PROTOCOL_E112.md",
                "research/2026-10-27-agent-cell-identifiability-r119/e119_combo_transfer.py"):
        p = ROOT / rel
        if p.exists():
            res["files"][rel] = sha256(p)
    (OUT / "E119_RESULTS.json").write_text(json.dumps(res, indent=2, ensure_ascii=False), encoding="utf-8")
    if len(r):
        r.to_csv(OUT / "E119_rows.csv", index=False)

    print("units=%d tissues=%s" % (len(r), tissues))
    for held, e in res["by_tissue"].items():
        a = e["combo_minus_random"]; b = e["combo_minus_identity"]; c = e["combo_minus_marginal"]
        print("  [%-9s] base %.4f marg %.4f id %.4f combo %.4f rand %.4f" % (
            held, e["base"], e["marginal"], e["identity"], e["combo"], e["random"]))
        print("      combo-rand %+.4f [%+.4f,%+.4f] | combo-id %+.4f [%+.4f,%+.4f] | combo-marg %+.4f [%+.4f,%+.4f]" % (
            a["mean_diff"], a["ci95"][0], a["ci95"][1], b["mean_diff"], b["ci95"][0], b["ci95"][1],
            c["mean_diff"], c["ci95"][0], c["ci95"][1]))
    print("DECISIONS:", json.dumps(res["decisions"], ensure_ascii=False))


if __name__ == "__main__":
    main()
