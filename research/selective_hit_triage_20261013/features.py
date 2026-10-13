"""Pair-level evidence for every eligible (compound, cell line), from screen and context inputs only.

File summary
- Path: research/selective_hit_triage_20261013/features.py
- Purpose: build the evidence each triage arm may use. Nothing here reads a CTRP response value.
- Core points:
  - Screen evidence (all arms): PRISM 19Q4 primary log2 fold change at 2.5 uM, its within-compound
    robust z, and a two-way residual z. The residual removes each line's general sensitivity, the
    median over all 4,532 PRISM compounds, and the compound's median residual.
  - Context and mechanism evidence (virtual-cell and MAESTRO arms):
    - `ctx_pred`: the compound's residual z in the 25 lines most similar to this line in CCLE
      expression, the line itself excluded.
    - `lineage_pred`: the mean residual z over other lines of the same lineage.
    - `tgt_mut` and `tgt_expr_z`: a protein-changing mutation in, or the expression of, an
      annotated target gene.
    - `biomarker_pred`: the target-expression regression of residual z, fitted without the line.
    - `vc_pred` and `vc_trust`: the transcriptional-transfer virtual cell. It predicts the residual
      profile from the PRISM profiles of the five drugs with the most similar L1000 responses, the
      query and its structure duplicates excluded.
  - Acquired evidence (closed-loop arms only, when a compound's dose-response is bought):
    - `sec_auc_z`: the within-compound z of the mean PRISM secondary LFC over doses.
    - `sec_slope`: the dose-response rank correlation.
- Output: features.npz (pair table) and compounds.json (per-compound facts).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from census import CCLE, HERE, LINCS, PRISM, ROOT, brd_core

sys.path.insert(0, str(ROOT / "src"))
from virtual_cell.transcriptional_transfer import transfer_profile  # noqa: E402

LFC_HIT = -1.0
K_CONTEXT = 25
K_VC = 5
PROTEIN_CHANGING = {"Missense_Mutation", "Nonsense_Mutation", "Frame_Shift_Del", "Frame_Shift_Ins", "Splice_Site",
                    "In_Frame_Del", "In_Frame_Ins", "Nonstop_Mutation", "Start_Codon_SNP", "Start_Codon_Del", "Start_Codon_Ins"}


def robust_z(x: np.ndarray, axis: int = -1) -> np.ndarray:
    med = np.nanmedian(x, axis=axis, keepdims=True)
    mad = 1.4826 * np.nanmedian(np.abs(x - med), axis=axis, keepdims=True)
    return (x - med) / np.maximum(mad, 1e-6)


def loo_slope_pred(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    """For each line l: slope of y on x fitted on all other lines, times x_l (centred). NaN-safe."""
    ok = np.isfinite(y) & np.isfinite(x)
    out = np.full(len(y), np.nan)
    n = ok.sum()
    if n < 20:
        return out
    yy, xx = np.where(ok, y, 0.0), np.where(ok, x, 0.0)
    Sx, Sy, Sxx, Sxy = xx.sum(), yy.sum(), (xx * xx).sum(), (xx * yy).sum()
    m = n - ok.astype(float)                                   # count without l (for lines in ok)
    sx, sy = Sx - np.where(ok, xx, 0), Sy - np.where(ok, yy, 0)
    sxx, sxy = Sxx - np.where(ok, xx * xx, 0), Sxy - np.where(ok, xx * yy, 0)
    mx, my = sx / m, sy / m
    var = sxx / m - mx ** 2
    beta = (sxy / m - mx * my) / np.maximum(var, 1e-9)
    pred = beta * (x - mx)
    return np.where(np.isfinite(x), pred, np.nan)


def main() -> None:
    census = json.loads((HERE / "CENSUS.json").read_text(encoding="utf-8"))
    split = json.loads((HERE / "SPLIT.json").read_text(encoding="utf-8"))
    rows = {r["core"]: r for r in census["compounds"]}
    role = {c: "development" for c in split["development"]} | {c: "test" for c in split["test"]}
    cores = sorted(role)

    # ---- PRISM primary: one column per compound core (HTS preferred), all compounds for line effects
    pinfo = pd.read_csv(PRISM / "primary-screen-replicate-collapsed-treatment-info.csv")
    lfc = pd.read_csv(PRISM / "primary-screen-replicate-collapsed-logfold-change.csv", index_col=0)
    pinfo = pinfo[pinfo["column_name"].isin(lfc.columns)].copy()
    pinfo["core"] = pinfo["broad_id"].map(brd_core)
    pinfo["rank"] = list(zip(pinfo["screen_id"].ne("HTS"), (pinfo["dose"] - 2.5).abs()))
    pinfo = pinfo.sort_values(["core", "rank"]).drop_duplicates("core")
    lines = np.array([str(x) for x in lfc.index], dtype=str)
    all_cols = list(pinfo["column_name"])
    M = lfc[all_cols].to_numpy(dtype=float)                    # lines x all compounds
    line_med = np.nanmedian(M, axis=1)                         # line general sensitivity
    R_all = M - line_med[:, None]
    R_all = R_all - np.nanmedian(R_all, axis=0, keepdims=True)
    line_noise = 1.4826 * np.nanmedian(np.abs(R_all - np.nanmedian(R_all, axis=1, keepdims=True)), axis=1)
    col_of = dict(zip(pinfo["core"], pinfo["column_name"]))
    name_of_core = dict(zip(pinfo["core"], pinfo["name"]))
    X = lfc[[col_of[c] for c in cores]].to_numpy(dtype=float).T  # eligible compounds x lines
    Zc = robust_z(X, axis=1)
    Rr = X - line_med[None, :]
    Rr = Rr - np.nanmedian(Rr, axis=1, keepdims=True)
    Zr = Rr / np.maximum(1.4826 * np.nanmedian(np.abs(Rr), axis=1, keepdims=True), 1e-6)
    promisc = np.nanmean(X <= LFC_HIT, axis=1)
    madc = 1.4826 * np.nanmedian(np.abs(X - np.nanmedian(X, axis=1, keepdims=True)), axis=1)
    rank = np.argsort(np.argsort(np.where(np.isfinite(Zr), Zr, np.inf), axis=1), axis=1) + 1

    # ---- CCLE context
    info = pd.read_csv(CCLE / "sample_info.csv").set_index("DepMap_ID")
    lineage = np.array([str(info["lineage"].get(l, "")) for l in lines])
    expr = pd.read_csv(CCLE / "CCLE_expression.csv", index_col=0)
    expr.columns = [c.split(" (")[0] for c in expr.columns]
    expr = expr.reindex(lines)
    have_expr = expr.notna().all(axis=1).to_numpy()
    var_genes = expr.loc[have_expr].var(axis=0).sort_values(ascending=False).index[:2000]
    E = expr[var_genes].to_numpy(dtype=float)
    E = (E - np.nanmean(E[have_expr], 0)) / np.maximum(np.nanstd(E[have_expr], 0), 1e-6)
    Ec = np.where(have_expr[:, None], E, 0.0)
    sim = (Ec @ Ec.T) / E.shape[1]
    sim[~have_expr] = -np.inf
    sim[:, ~have_expr] = -np.inf
    np.fill_diagonal(sim, -np.inf)
    neigh = np.argsort(-sim, axis=1)[:, :K_CONTEXT]
    muts = pd.read_csv(CCLE / "CCLE_mutations.csv", usecols=["Hugo_Symbol", "Variant_Classification", "DepMap_ID"])
    muts = muts[muts["Variant_Classification"].isin(PROTEIN_CHANGING)]
    mutated = set(zip(muts["DepMap_ID"], muts["Hugo_Symbol"]))

    # ---- transcriptional-transfer virtual cell (L1000 landmark responses; references = other PRISM drugs)
    lm = [np.load(LINCS / f"derived/block_m_landmark_{p}.npz", allow_pickle=True) for p in ("open", "sealed")]
    l_names = np.concatenate([z["drug"] for z in lm])
    l_x = np.concatenate([z["x"] for z in lm]).astype(np.float64)
    l_x = np.where(np.concatenate([z["n_sig"] for z in lm])[..., None] > 0, l_x, np.nan)
    prism_by_name: dict = {}
    for core, name in name_of_core.items():
        prism_by_name.setdefault(str(name).strip().lower(), core)
    ref_idx = [i for i, n in enumerate(l_names) if str(n).strip().lower() in prism_by_name]
    ref_core = [prism_by_name[str(l_names[i]).strip().lower()] for i in ref_idx]
    conn = {c: rows[c]["connectivity"] for c in cores}
    pconn = {}
    for c in ref_core:
        pconn[c] = rows[c]["connectivity"] if c in rows else None
    all_core_index = {c: k for k, c in enumerate(pinfo["core"])}
    ref_profiles = np.stack([R_all[:, all_core_index[c]] for c in ref_core])        # refs x lines residual LFC
    vc_pred = np.full(X.shape, np.nan)
    vc_trust = np.full(len(cores), np.nan)
    for i, c in enumerate(cores):
        q = [k for k, n in enumerate(l_names) if prism_by_name.get(str(n).strip().lower()) == c]
        if not q:
            continue
        keep = [j for j, rc in enumerate(ref_core) if rc != c and (conn[c] is None or pconn.get(rc) != conn[c])]
        tr = transfer_profile(l_x[q[0]], l_x[[ref_idx[j] for j in keep]], ref_profiles[keep], k=K_VC)
        if tr.values is None:
            continue
        v = tr.values - np.nanmedian(tr.values)
        vc_pred[i] = v / np.maximum(1.4826 * np.nanmedian(np.abs(v)), 1e-6)
        vc_trust[i] = tr.trust

    # ---- PRISM secondary dose-response (acquisition only)
    sinfo = pd.read_csv(PRISM / "secondary-screen-replicate-collapsed-treatment-info.csv")
    sinfo["core"] = sinfo["broad_id"].map(brd_core)
    sinfo = sinfo[sinfo["core"].isin(cores)]
    slfc = pd.read_csv(PRISM / "secondary-screen-replicate-collapsed-logfold-change.csv", index_col=0,
                       usecols=lambda col: col == "Unnamed: 0" or col in set(sinfo["column_name"]))
    slfc = slfc.reindex(lines)
    sec_auc_z = np.full(X.shape, np.nan)
    sec_slope = np.full(X.shape, np.nan)
    sec_screen = {}
    for i, c in enumerate(cores):
        sub = sinfo[sinfo["core"] == c]
        if sub.empty:
            continue
        best = max(sub.groupby("screen_id"), key=lambda g: (slfc[list(g[1]["column_name"])].notna().sum().sum(), g[0] == "HTS002"))
        g = best[1].sort_values("dose")
        S = slfc[list(g["column_name"])].to_numpy(dtype=float)  # lines x doses
        if S.shape[1] < 4:
            continue
        sec_screen[c] = best[0]
        auc = np.nanmean(S, axis=1)
        sec_auc_z[i] = robust_z(auc[None])[0]
        logd = np.log10(g["dose"].to_numpy(dtype=float))
        ranks_d = pd.Series(logd).rank().to_numpy()
        for l in range(len(lines)):
            ok = np.isfinite(S[l])
            if ok.sum() >= 4:
                rs = pd.Series(S[l][ok]).rank().to_numpy()
                rd = ranks_d[ok]
                sec_slope[i, l] = np.corrcoef(rd, rs)[0, 1] if np.std(rs) > 0 else 0.0

    # ---- pair table over census-eligible pairs with a finite primary value
    cp = np.load(HERE / "census_pairs.npz")
    line_pos = {l: k for k, l in enumerate(lines)}
    cpos = {c: k for k, c in enumerate(cores)}
    recs = []
    for core, line in zip(cp["core"], cp["line"]):
        core, line = str(core), str(line)
        if core not in cpos or line not in line_pos:
            continue
        i, l = cpos[core], line_pos[line]
        if not np.isfinite(X[i, l]):
            continue
        targets = rows[core]["targets"]
        ctx = Zr[i, neigh[l]] if have_expr[l] else np.array([np.nan])
        same = (lineage == lineage[l]) & (np.arange(len(lines)) != l)
        tmut = float(any((line, t) in mutated for t in targets)) if targets else 0.0
        texp = [t for t in targets if t in expr.columns]
        recs.append((i, l, tmut, texp, float(np.nanmean(ctx)) if np.isfinite(ctx).any() else np.nan,
                     float(np.nanmean(Zr[i, same])) if np.isfinite(Zr[i, same]).any() else np.nan))
    n = len(recs)
    ci = np.array([r[0] for r in recs])
    li = np.array([r[1] for r in recs])
    # target expression z and leave-line-out biomarker prediction
    tgt_expr_z = np.full(n, np.nan)
    biomarker_pred = np.full(n, np.nan)
    gene_z_cache: dict = {}
    by_cpd: dict = {}
    for k, r in enumerate(recs):
        by_cpd.setdefault(r[0], []).append(k)
    for i, ks in by_cpd.items():
        genes = recs[ks[0]][3]
        if not genes:
            continue
        preds, zs = [], []
        for g in genes:
            if g not in gene_z_cache:
                v = expr[g].to_numpy(dtype=float)
                gene_z_cache[g] = (v - np.nanmean(v)) / max(np.nanstd(v), 1e-6)
            gz = gene_z_cache[g]
            preds.append(loo_slope_pred(Zr[i], gz))
            zs.append(gz)
        P = np.nanmean(np.stack(preds), axis=0)
        Zg = np.nanmax(np.stack(zs), axis=0)
        for k in ks:
            biomarker_pred[k] = P[recs[k][1]]
            tgt_expr_z[k] = Zg[recs[k][1]]
    table = {
        "core": np.array([cores[i] for i in ci]), "line": lines[li], "role": np.array([role[cores[i]] for i in ci]),
        "lfc": X[ci, li], "z_c": Zc[ci, li], "z_r": Zr[ci, li], "line_med": line_med[li], "line_noise": line_noise[li],
        "promisc_c": promisc[ci], "mad_c": madc[ci], "rank_c": rank[ci, li].astype(float),
        "ctx_pred": np.array([r[4] for r in recs]), "lineage_pred": np.array([r[5] for r in recs]),
        "tgt_mut": np.array([r[2] for r in recs]), "tgt_expr_z": tgt_expr_z, "biomarker_pred": biomarker_pred,
        "vc_pred": vc_pred[ci, li], "vc_trust": vc_trust[ci],
        "sec_auc_z": sec_auc_z[ci, li], "sec_slope": sec_slope[ci, li], "lineage": lineage[li],
    }
    np.savez_compressed(HERE / "features.npz", **table)
    compounds = [{"core": c, "role": role[c], "family": split["family"][c], "name": rows[c]["name"], "phase": rows[c]["phase"],
                  "moas": rows[c]["moas"], "targets": rows[c]["targets"], "promiscuity": float(promisc[i]),
                  "l1000_vc": bool(np.isfinite(vc_trust[i])), "vc_trust": None if not np.isfinite(vc_trust[i]) else float(vc_trust[i]),
                  "secondary_screen": sec_screen.get(c), "pairs": int((ci == i).sum())} for i, c in enumerate(cores)]
    (HERE / "compounds.json").write_text(json.dumps(compounds, indent=1) + "\n", encoding="utf-8")
    cover = {k: float(np.isfinite(v).mean()) for k, v in table.items() if v.dtype.kind == "f"}
    print(json.dumps({"pairs": n, "compounds": len(cores), "with_vc": int(np.isfinite(vc_trust).sum()),
                      "with_secondary": len(sec_screen), "coverage": cover}, indent=1))


if __name__ == "__main__":
    main()
