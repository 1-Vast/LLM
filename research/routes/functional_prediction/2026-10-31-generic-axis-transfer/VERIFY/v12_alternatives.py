"""Cheap tests of alternative readings of ambiguous protocol rules. Writes check_extra_alternatives.json.

(a) NCI-60 kill threshold 5.60 (literal) vs -log10(2.5e-6) = 5.60206; borderline means.
(b) 24Q2 activity denominator: all evaluated lines (literal; missing = not killed) vs lines with a value.
(c) 24Q2 line set: exact DepMap-ID match (literal, 568) vs suffix-stripped match (adds 19Q4 lines such as
    ACH-000010_FAILED_STR). Re-runs B0, B1, C1 with a fast vectorised similarity (checked against the saved
    predictions on the 568 lines). Uses only the 101 query rows already parsed by the run.
(e) Bound for the sealed compound that shares its connectivity block with a query (BRD-K57796080): how negative
    its per-compound difference would have to be to flip the sign of the 24Q2 H1/H3 point estimates.
"""
import json
import re
import sys
from collections import defaultdict

import numpy as np

ROOT = "D:/MAESTRO/"
VER = ROOT + "research/routes/functional_prediction/2026-10-31-generic-axis-transfer/VERIFY/"
STUDY = VER[: -len("VERIFY/")]
PROC = ROOT + "data/processed/generic_axis_transfer_20261031/"
MATRIX = ROOT + "data/external/prism_24q2_20261031/matrix/Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv"
CLIST = ROOT + "data/external/prism_24q2_20261031/meta/Repurposing_Public_24Q2_Extended_Primary_Compound_List.csv"
sys.path.insert(0, VER)
import vlib  # noqa: E402


def fast_sims(Q, R, D=None):
    """Mean cosine over shared options for all query x reference pairs; optional axis removal fitted on R."""
    Q = Q.astype(np.float64)
    R = R.astype(np.float64)
    nq, nr, O = Q.shape[0], R.shape[0], Q.shape[1]
    S = np.zeros((nq, nr))
    C = np.zeros((nq, nr))
    for o in range(O):
        qh = np.isfinite(Q[:, o, 0])
        rh = np.isfinite(R[:, o, 0])
        Qo, Ro = Q[qh, o], R[rh, o]
        if D is not None:
            mu = Ro.mean(axis=0)
            _, _, Vt = np.linalg.svd(Ro - mu, full_matrices=False)
            V = Vt[:D]
            Qo = (Qo - mu) - ((Qo - mu) @ V.T) @ V
            Ro = (Ro - mu) - ((Ro - mu) @ V.T) @ V
        qn = np.linalg.norm(Qo, axis=1)
        rn = np.linalg.norm(Ro, axis=1)
        num = Qo @ Ro.T
        den = qn[:, None] * rn[None, :]
        ok = den > 0
        cos = np.where(ok, num / np.where(ok, den, 1.0), 0.0)
        qi, ri = np.flatnonzero(qh), np.flatnonzero(rh)
        S[np.ix_(qi, ri)] += cos
        C[np.ix_(qi, ri)] += ok
    return np.where(C > 0, S / np.maximum(C, 1), np.nan)


def main():
    out = {}
    # ---------------------------------------------------------------- (a) NCI-60 threshold
    Dn = np.load(VER + "derived_nci.npz")
    keys = [str(k) for k in Dn["key"]]
    Z = np.load(VER + "cache_zscore.npz")
    Rw = np.load(VER + "cache_raw.npz")
    from rdkit import Chem, RDLogger
    RDLogger.DisableLog("rdApp.*")
    keyset = set(keys)
    nsc_by_key = defaultdict(list)
    for n, smi in zip(Z["nsc"], Z["smiles"]):
        smi = str(smi)
        if not smi or smi in ("-", "na"):
            continue
        m = Chem.MolFromSmiles(smi)
        if m is None:
            continue
        k = Chem.MolToInchiKey(m)[:14]
        if k in keyset:
            nsc_by_key[k].append(str(n))
    rows_by_nsc = defaultdict(list)
    for i, n in enumerate(Rw["nsc"]):
        rows_by_nsc[str(n)].append(i)
    good = np.array([str(f).strip() == "-" for f in Rw["fail"]])
    means = np.full((len(keys), 60), np.nan)
    for qi, k in enumerate(keys):
        rows = [r for n in nsc_by_key[k] for r in rows_by_nsc[n] if good[r]]
        with np.errstate(all="ignore"):
            means[qi] = np.nanmean(Rw["x"][rows], axis=0)
    k560 = (np.nan_to_num(means, nan=-1) >= 5.60).sum(axis=1)
    k5602 = (np.nan_to_num(means, nan=-1) >= -np.log10(2.5e-6)).sum(axis=1)
    border = np.isfinite(means) & (np.abs(means - 5.60) < 1e-9)
    out["a_nci_threshold"] = {
        "killed_lines_equal_npz_at_5.60": bool(np.array_equal(k560, Dn["killed_lines"])),
        "n_line_means_within_1e-9_of_5.60": int(border.sum()),
        "n_keys_active_change_at_5.60206": int(((k5602 >= 3) != (k560 >= 3)).sum()),
        "keys_active_change_at_5.60206": [keys[i] for i in np.flatnonzero((k5602 >= 3) != (k560 >= 3))],
        "n_killed_line_cells_change_at_5.60206": int((k5602 != k560).sum()),
    }

    # ---------------------------------------------------------------- (b) 24Q2 activity denominator
    Dp = np.load(VER + "derived_prism.npz")
    pk = [str(k) for k in Dp["key"]]
    act = Dp["active"].astype(bool)
    alt = Dp["active_finite_denominator"].astype(bool)
    st = json.load(open(VER + "check1_stats.json", encoding="utf-8"))
    P2 = np.load(STUDY + "RUN/predictions_prism24q2.npz")
    obs, gen = Dp["observed"], Dp["generic"]
    R = {a: np.nan_to_num(np.array([vlib.sel_r(P2[f"pred_{a}"][i], obs[i], gen, 50) for i in range(len(pk))]), nan=0.0)
         for a in vlib.ARMS}
    changed = [pk[i] for i in np.flatnonzero(act != alt)]
    nfin = np.isfinite(obs).sum(axis=1)
    out["b_prism_activity_denominator"] = {
        "compounds_changing": changed,
        "their_killed_lines": [int(Dp["killed_lines"][pk.index(c)]) for c in changed],
        "their_finite_lines": [int(nfin[pk.index(c)]) for c in changed],
        "n_active_literal": int(act.sum()), "n_active_alt": int(alt.sum()),
        "H1_alt": vlib.paired_one_sided(R["C1"][alt], R["B0"][alt]),
        "H3_alt": vlib.paired_one_sided(R["C1"][alt], R["B1"][alt]),
        "leakage_alt": vlib.one_sample_two_sided(R["L"][alt]),
    }

    # ---------------------------------------------------------------- (e) bound for BRD-K57796080
    d1 = R["C1"] - R["B0"]
    d3 = R["C1"] - R["B1"]
    na = int(act.sum())
    out["e_unqueried_enantiomer_bound"] = {
        "compound": "BRD-K57796080 (3,5-DHPG-(S)); shares connectivity block HOOWCUZPEFNHDT with query BRD-A20589515",
        "BRD-A20589515_active": bool(act[pk.index("BRD-A20589515")]),
        "BRD-A20589515_killed_lines": int(Dp["killed_lines"][pk.index("BRD-A20589515")]),
        "if_inactive": "active-population tests (H1, H3, leakage, verdicts, promotion) unchanged",
        "if_active_H1_point_estimate_turns_negative_when_d_below": float(-d1[act].sum()),
        "if_active_H3_point_estimate_turns_negative_when_d_below": float(-d3[act].sum()),
        "observed_range_of_d_H1_over_24q2_actives": [float(d1[act].min()), float(d1[act].max())],
        "observed_range_of_d_H3_over_24q2_actives": [float(d3[act].min()), float(d3[act].max())],
        "observed_range_of_d_H1_over_all_24q2": [float(d1.min()), float(d1.max())],
        "observed_range_of_d_H3_over_all_24q2": [float(d3.min()), float(d3.max())],
        "n_actives": na,
    }

    # ---------------------------------------------------------------- (c) 24Q2 line set with suffix-stripped IDs
    dev = np.load(PROC + "dev_pool.npz")
    dl = [str(x) for x in dev["line"]]
    with open(MATRIX, encoding="utf-8", newline="") as f:
        mlines = f.readline().rstrip("\r\n").split(",")[1:]
    mset = set(mlines)
    base = [x.split("_")[0] for x in dl]
    lines_alt = [x for x, b in zip(dl, base) if b in mset]
    extra = [x for x in lines_alt if x not in mset]
    out["c_line_set"] = {"n_lines_literal": len(Dp["line"]), "n_lines_alt": len(lines_alt), "extra_19q4_lines": extra}
    # query rows (the same REP.1M rows the run parsed)
    import csv
    want = {}
    for r in csv.DictReader(open(CLIST, encoding="utf-8", newline="")):
        if r["screen"] == "REP.1M":
            i = r["IDs"].strip()
            c = re.match(r"^BRD:(BRD-[A-Z]\d{8})", i).group(1)
            if c in set(pk):
                want[i] = c
    vals = defaultdict(list)
    col = {s: j for j, s in enumerate(mlines)}
    with open(MATRIX, encoding="utf-8", newline="") as f:
        f.readline()
        for line in f:
            rid, rest = line.split(",", 1)
            if rid in want:
                fields = rest.rstrip("\r\n").split(",")
                vals[want[rid]].append(np.array([float(v) if v.strip() else np.nan for v in fields]))
    out["c_line_set"]["rows_parsed"] = sum(len(v) for v in vals.values())
    idx = [col[x.split("_")[0]] for x in lines_alt]
    obs_alt = np.vstack([np.nanmean(np.vstack(vals[c])[:, idx], axis=0) for c in pk])
    Y_alt = dev["profile"][:, [dl.index(x) for x in lines_alt]]
    with np.errstate(all="ignore"):
        gen_alt = np.nanmean(Y_alt, axis=0)
    killed = (np.nan_to_num(obs_alt, nan=0.0) <= -1).sum(axis=1)
    act_alt = killed >= 0.05 * len(lines_alt)
    L2 = np.load(PROC + "l1000_24q2.npz", allow_pickle=True)
    l2 = [str(k) for k in L2["key"]]
    qsig = L2["x"][[l2.index(k) for k in pk]]
    Rsig = dev["signature"]
    s_raw = fast_sims(qsig, Rsig)
    s_c1 = fast_sims(qsig, Rsig, D=5)
    pred = {"B0": [], "B1": [], "C1": []}
    for i in range(len(pk)):
        pred["B0"].append(vlib.weighted_prediction(s_raw[i], Y_alt, 5)[0])
        pred["B1"].append(vlib.weighted_prediction(s_raw[i], Y_alt, 20)[0])
        pred["C1"].append(vlib.weighted_prediction(s_c1[i], Y_alt, 20)[0])
    pred = {a: np.vstack(v) for a, v in pred.items()}
    # sanity: on the literal 568 lines the fast path must equal the saved predictions
    lit_idx = [lines_alt.index(x) for x in [str(s) for s in Dp["line"]]]
    out["c_line_set"]["fast_path_max_abs_diff_vs_saved_on_568"] = {
        a: float(np.nanmax(np.abs(pred[a][:, lit_idx] - P2[f"pred_{a}"]))) for a in pred}
    Ra = {a: np.nan_to_num(np.array([vlib.sel_r(pred[a][i], obs_alt[i], gen_alt, 50) for i in range(len(pk))]), nan=0.0)
          for a in pred}
    out["c_line_set"]["n_active_alt"] = int(act_alt.sum())
    out["c_line_set"]["active_changes"] = [pk[i] for i in np.flatnonzero(act_alt != act)]
    out["c_line_set"]["H1_alt"] = vlib.paired_one_sided(Ra["C1"][act_alt], Ra["B0"][act_alt])
    out["c_line_set"]["H3_alt"] = vlib.paired_one_sided(Ra["C1"][act_alt], Ra["B1"][act_alt])
    out["c_line_set"]["means_alt_active"] = {a: float(Ra[a][act_alt].mean()) for a in Ra}

    json.dump(out, open(VER + "check_extra_alternatives.json", "w", encoding="utf-8", newline="\n"), indent=1, default=float)
    print(json.dumps(out, indent=1, default=float))


if __name__ == "__main__":
    main()
