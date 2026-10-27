# R198-A2v4 constructive simulator — FULL PIPELINE (IMMEDIATE IMPLEMENTATION; NOT RUN THIS ROUND)
# -------------------------------------------------------------------------------------------------
# Status: complete design-version implementation; NOT executed in R198 (forbidden: no simulator runs).
# The only execution gate is --confirm-run; without it the script prints the plan and exits.
# Metadata inputs only: folds.json, state_z.json, and GDSC identity/annotation/design columns.
# NEVER reads response columns (SYNERGY_DELTA_EMAX etc.); synthetic y only.
#
# Implements spec_v4 §4 / protocol_draft_v4 §3:
#   - world generator: b_cell + b_pair + b_dose + g_group + h_state*z + eps, injections I/II/III/null
#   - S batch allocation for k in {6,12,20,24,36} (structured 20-unit batch: 10 in/10 out, z 5/5)
#   - K_A2 classifier (rules 1-5: nuisance r_I, condition gap+>=5 flipped cell groups, residual
#     structure + <=6 candidate max-stat permutation identification, else unresolvable/null_ok)
#   - endpoints E1..E4 with pre-registered abstention accounting (null abstention option (a))
#   - MDE simulation plan (unverified runtime planning value)
#   - verdict: constructive_pass / partial / fail
# SHA256 of this file is recorded in record_v4.md §3 / usage_v4.json (file itself not run).
import argparse, json, os, sys
import numpy as np

BASE = os.path.dirname(os.path.abspath(__file__))
SEED_BASE = 20261027
SIGMAS = (0.5, 1.0, 2.0)
DELTAS = (1.0, 2.0)          # in units of sigma
K_GRID = (6, 12, 20, 24, 36)
CLASSES = ("I", "II", "III", "null")
N_WORLDS_PER_CLASS = 24
N_BATCHES_MDE = 1000
DELTA_MIN = {"E1": 0.30, "E2": 0.20, "E3": 0.05, "E4": 0.10}  # same-unit as MDE (accuracy/rate difference)
# E4b per-class resolved floor and null resolved gate (challenge A2v3 must-fix 3 -> option (a))
E4B_PER_CLASS_RESOLVED = 0.85
NULL_RESOLVED_GATE = 0.50     # null unresolvable rate must be <= 0.50, i.e. null resolved >= 0.50
RESPONSE_COLS = ["SYNERGY_DELTA_EMAX"]  # never read by this simulator

# ----------------------------------------------------------------------------- artifacts
def load_design(path=None):
    with open(path or os.path.join(BASE, "folds.json"), encoding="utf-8") as fh:
        folds = json.load(fh)
    with open(os.path.join(BASE, "state_z.json"), encoding="utf-8") as fh:
        sz = json.load(fh)
    return folds, sz

def load_units(design, state_z):
    """Build unit universe (cell x directed pair) from GDSC metadata/annotation/design columns.
    Streams with pandas but selects ONLY identity/annotation/design columns; no response columns."""
    import pandas as pd
    p = r"D:\MAESTRO\data\external\gdsc_combinations\jaaks2022_figshare\Original screen_All tissues_fitted data.csv"
    cols = ["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME", "Tissue",
            "ANCHOR_PATHWAY", "LIBRARY_PATHWAY", "ANCHOR_DRUG_TYPE", "LIBRARY_DRUG_TYPE", "BARCODE"]
    d = pd.read_csv(p, usecols=cols, low_memory=False)
    cells = sorted(d.CELL_LINE_NAME.unique().tolist())
    cidx = {c: i for i, c in enumerate(cells)}
    cell_group = {c: f"G{i % 8}" for i, c in sorted(enumerate(cells), key=lambda x: (d.loc[d.CELL_LINE_NAME == x[1], "Tissue"].iloc[0], x[1]))}
    z = {}
    idx = state_z["unit_index"]
    for ci, ai, li, zz in state_z["units_z"]:
        z[(idx["cells"][ci], idx["anchors"][ai], idx["libraries"][li])] = int(zz)
    u = d.groupby(["CELL_LINE_NAME", "ANCHOR_NAME", "LIBRARY_NAME"], sort=True).first().reset_index()
    u["cell_idx"] = u.CELL_LINE_NAME.map(cidx)
    u["pair_idx"] = u.groupby(["ANCHOR_NAME", "LIBRARY_NAME"], sort=True).ngroup()
    u["group_idx"] = u.groupby(["ANCHOR_PATHWAY", "LIBRARY_PATHWAY"], sort=True).ngroup()
    u["cell_group"] = u.CELL_LINE_NAME.map(lambda c: cell_group.get(c, "G0"))
    u["cond_in"] = u.cell_group.isin(["G0", "G1", "G2", "G3", "G4"]).astype(int)  # pre-registered condition predicate
    u["z"] = [z[(r.CELL_LINE_NAME, r.ANCHOR_NAME, r.LIBRARY_NAME)] for r in u.itertuples()]
    u["dtype_same"] = (u.ANCHOR_DRUG_TYPE == u.LIBRARY_DRUG_TYPE).astype(int)
    u["tissue_code"] = pd.factorize(u.Tissue)[0]
    u["cell_first_barcode_parity"] = u.BARCODE.map(lambda b: int("".join(ch for ch in str(b) if ch.isdigit())) % 2)
    u["dose_level"] = (u.groupby("ANCHOR_NAME").BARCODE.transform(lambda s: s.astype(str).str.len() % 2)).astype(int)
    return {"units": u, "n_cells": int(len(cells)), "n_pairs": int(u.pair_idx.nunique()),
            "n_groups": int(u.group_idx.nunique()), "n_units": int(len(u)),
            "cell_group": cell_group, "pairs_per_cell_group": None}

# ----------------------------------------------------------------------------- world generator
def make_world(design, units_meta, cls, sigma, delta, seed):
    """Generate a synthetic world on the unit universe (y), with the pre-registered injection.
    y = b_cell + b_pair + b_dose + g_group + h_state*z + eps. NEVER reads real response values."""
    rng = np.random.default_rng(seed)
    u = units_meta["units"]
    n_cells = units_meta["n_cells"]
    n_pairs = units_meta["n_pairs"]
    n_groups = units_meta["n_groups"]
    b_cell = rng.normal(0, 0.5, n_cells)[u.cell_idx.to_numpy()]
    b_pair = rng.normal(0, 0.5, n_pairs)[u.pair_idx.to_numpy()]
    b_dose = rng.normal(0, 0.2, 2)[u.dose_level.to_numpy()]
    g = rng.choice([-1.0, 1.0], n_groups) * (0.5 * delta)
    g_eff = g[u.group_idx.to_numpy()]
    z = u.z.to_numpy()
    h_state = np.zeros_like(g_eff)
    if cls == "I":            # numeric: nuisance shifts only
        b_cell = b_cell + delta
        b_pair = b_pair + delta
        b_dose = b_dose + delta
    elif cls == "II":         # relation applicability failure: g flips sign in the 3 OUT-of-condition cell groups
        flip = (u.cond_in.to_numpy() == 0).astype(float) * -2.0
        g_eff = g_eff * (1.0 + flip)
    elif cls == "III":        # representation missing state: observable-but-unmodeled z effect
        h_state = delta * z
    elif cls == "null":
        pass
    else:
        raise ValueError(cls)
    eps = rng.normal(0, sigma, len(u))
    y = b_cell + b_pair + b_dose + g_eff + h_state + eps
    return {"class": cls, "sigma": sigma, "delta": delta, "seed": seed, "y": y,
            "truth": {"b_cell": b_cell, "b_pair": b_pair, "b_dose": b_dose,
                      "g": g, "g_eff": g_eff, "z": z},
            "units_meta": units_meta}

# ----------------------------------------------------------------------------- batches
def k_allocation(k):
    """Explicit unit allocation + reuse rules (spec_v4 §4.5). state counts are TOTALS per level."""
    table = {
        6:  {"in": 3,  "out": 3,  "z_total": 3,  "reserve": 0,  "confirm": None},
        12: {"in": 6,  "out": 6,  "z_total": 6,  "reserve": 0,  "confirm": None},
        20: {"in": 10, "out": 10, "z_total": 10, "reserve": 0,  "confirm": None},
        24: {"in": 10, "out": 10, "z_total": 10, "reserve": 4,  "confirm": None},
        36: {"in": 10, "out": 10, "z_total": 10, "reserve": 0,  "confirm": {"in": 8, "out": 8, "z_total": 4}},
    }
    if k not in table:
        raise ValueError(k)
    return table[k]

def sample_batch(world, k, rng):
    """Response-blind S sampling with pre-registered condition/state balance."""
    u = world["units_meta"]["units"]
    alloc = k_allocation(k)
    idx = np.arange(len(u))
    in_idx = idx[u.cond_in.to_numpy() == 1]
    out_idx = idx[u.cond_in.to_numpy() == 0]
    z = u.z.to_numpy()
    chosen = []
    for stratum, n_total, z_total in (("in", alloc["in"], alloc["z_total"] // 2), ("out", alloc["out"], alloc["z_total"] - alloc["z_total"] // 2)):
        pool = in_idx if stratum == "in" else out_idx
        n0 = min(z_total, int((z[pool] == 0).sum()))
        n1 = min(n_total - n0, int((z[pool] == 1).sum()))
        if n0 + n1 < n_total:  # top-up deterministically if balance impossible (not expected)
            rest = [i for i in pool if i not in set(chosen)][: n_total - n0 - n1]
            chosen.extend(rest)
            continue
        p0 = pool[z[pool] == 0]
        p1 = pool[z[pool] == 1]
        chosen.extend(rng.choice(p0, size=n0, replace=False).tolist())
        chosen.extend(rng.choice(p1, size=n1, replace=False).tolist())
    chosen = list(dict.fromkeys(chosen))
    if k in (24, 36):
        reserve_pool = [i for i in idx if i not in set(chosen)]
        chosen.extend(rng.choice(reserve_pool, size=k - len(chosen), replace=False).tolist())
    return {"S": np.array(chosen, dtype=int), "allocation": alloc}

def make_reference(world, rng, n_ref=300):
    idx = np.arange(len(world["units_meta"]["units"]))
    return rng.choice(idx, size=min(n_ref, len(idx)), replace=False)

# ----------------------------------------------------------------------------- K_A2 classifier
def _nuisance_matrix(u, rows):
    """cell one-hot + pair one-hot + dose level (numpy). Small ridge-stabilized OLS via lstsq."""
    cells = u.cell_idx.to_numpy()[rows]
    pairs = u.pair_idx.to_numpy()[rows]
    dose = u.dose_level.to_numpy()[rows]
    n = len(rows)
    Xc = np.zeros((n, u.cell_idx.max() + 1)); Xc[np.arange(n), cells] = 1.0
    Xp = np.zeros((n, u.pair_idx.max() + 1)); Xp[np.arange(n), pairs] = 1.0
    return np.column_stack([Xc, Xp, dose.astype(float)])

def _fit_resid(X, y, ridge=1e-6):
    beta = np.linalg.lstsq(np.column_stack([np.ones(len(X)), X]), y, rcond=None)[0]
    pred = np.column_stack([np.ones(len(X)), X]) @ beta
    return y - pred, pred, beta

def _bic_two_component(resid):
    """1-D 2-component Gaussian mixture BIC difference (positive = 2 components better)."""
    r = np.asarray(resid, dtype=float)
    n = len(r)
    mu, var = r.mean(), r.var() + 1e-12
    ll1 = -0.5 * n * (np.log(2 * np.pi * var) + 1.0)
    c = np.percentile(r, [25, 75]); thr = c.mean()
    a, b = r[r <= thr], r[r > thr]
    if len(a) < 3 or len(b) < 3:
        return 0.0
    def gauss_ll(x):
        v = x.var() + 1e-12
        return -0.5 * len(x) * (np.log(2 * np.pi * v) + 1.0)
    ll2 = gauss_ll(a) + gauss_ll(b)
    k1, k2 = 2, 5
    return (ll2 - 0.5 * k2 * np.log(n)) - (ll1 - 0.5 * k1 * np.log(n))

def classify(batch, world, k, thresholds, rng):
    """K_A2 pre-registered classifier. Returns dict(decision, reason, scores, identified_state)."""
    u = world["units_meta"]["units"]
    y = world["y"]
    S = batch["S"]
    yS, XS = y[S], _nuisance_matrix(u, S)
    residS, _, _ = _fit_resid(XS, yS)
    ssr_model = float(np.sum(residS ** 2))
    ssr_null = float(np.sum((yS - yS.mean()) ** 2)) + 1e-12
    r_I = ssr_model / ssr_null
    # reference sample: independent units (not in S)
    ref_pool = np.array([i for i in range(len(u)) if i not in set(S.tolist())])
    ref = rng.choice(ref_pool, size=min(300, len(ref_pool)), replace=False)
    yR, XR = y[ref], _nuisance_matrix(u, ref)
    residR, _, _ = _fit_resid(XR, yR)
    g_idx = u.group_idx.to_numpy()
    ref_group_sign = {}
    for g in np.unique(g_idx[ref]):
        rr = residR[g_idx[ref] == g]
        if len(rr) >= 5:
            ref_group_sign[g] = np.sign(rr.mean()) or 1.0
    # condition gap + flipped cell groups
    gS = g_idx[S]
    signS = np.sign(residS); signS[signS == 0] = 1.0
    cond = u.cond_in.to_numpy()[S]
    cg = u.cell_group.to_numpy()[S]
    def agree(mask):
        gg = np.array([ref_group_sign.get(g, np.sign(residS[i])) for i, g in zip(np.where(mask)[0], gS[mask])])
        return float(np.mean(signS[mask] == gg)) if mask.sum() else np.nan
    a_in, a_out = agree(cond == 1), agree(cond == 0)
    gap = (a_in - a_out) if (a_in == a_in and a_out == a_out) else np.nan
    flips = 0
    for c in np.unique(cg):
        m = (cg == c) & (cond == 0)
        if m.sum() >= 2 and ref_group_sign.get(gS[m][0]) is not None:
            if np.sign(residS[m].mean()) != ref_group_sign[gS[m][0]]:
                flips += 1
    # residual structure + candidate-state max-stat identification
    cand = {
        "tissue": u.tissue_code.to_numpy()[S],
        "dtype": u.dtype_same.to_numpy()[S],
        "cell_group8": np.array([int(c[1:]) for c in cg]),
        "z": u.z.to_numpy()[S],
    }
    def eta2(labels):
        tot = float(np.sum(residS ** 2)) + 1e-12
        ss = 0.0
        for lab in np.unique(labels):
            rr = residS[labels == lab]
            ss += len(rr) * (rr.mean() ** 2)
        return ss / tot
    obs = {name: eta2(lab) for name, lab in cand.items()}
    perm = {name: np.empty(200) for name in cand}
    for name, lab in cand.items():
        for b in range(200):
            perm[name][b] = eta2(rng.permutation(lab))
    pvals = {name: float((np.sum(perm[name] >= obs[name]) + 1) / (200 + 1)) for name in cand}
    best = max(pvals, key=lambda n: obs[n])
    bic2 = _bic_two_component(residS)
    structure = (bic2 > thresholds.get("bic2", 6.0)) or (pvals[best] < 0.05)
    state_identified = structure and (pvals[best] < 0.05) and (obs[best] > thresholds.get("eta2_min", 0.05))
    # decisions (sequential, pre-registered order: II -> I -> III -> null_ok/unresolvable)
    if k >= 20 and gap == gap and gap >= 0.20 and flips >= 5 and a_out < 0.60:
        return {"decision": "II", "reason": "condition_gap>=0.20 and >=5 flipped cell groups", "identified_state": None,
                "scores": {"r_I": r_I, "gap": gap, "flips": flips, "bic2": bic2}}
    if r_I <= thresholds.get("rI_q10", 0.05) and (gap != gap or gap < 0.10) and not structure:
        return {"decision": "I", "reason": "nuisance refit explains S", "identified_state": None,
                "scores": {"r_I": r_I, "gap": gap, "flips": flips, "bic2": bic2}}
    if state_identified:
        return {"decision": "III", "reason": "residual structure + candidate state identified", "identified_state": best,
                "scores": {"r_I": r_I, "gap": gap, "flips": flips, "bic2": bic2, "pvals": pvals}}
    if not structure and r_I > thresholds.get("rI_q10", 0.05):
        return {"decision": "null_ok", "reason": "no violation/structure", "identified_state": None,
                "scores": {"r_I": r_I, "gap": gap, "flips": flips, "bic2": bic2}}
    return {"decision": "unresolvable", "reason": "no rule passed", "identified_state": None,
            "scores": {"r_I": r_I, "gap": gap, "flips": flips, "bic2": bic2, "pvals": pvals}}

def calibration_thresholds(worlds, rng):
    """Pre-compute null-world thresholds (rI_q10, bic2) from null worlds only."""
    rIs, bics = [], []
    for w in worlds:
        b = sample_batch(w, 20, rng)
        u = w["units_meta"]["units"]; S = b["S"]
        residS, _, _ = _fit_resid(_nuisance_matrix(u, S), w["y"][S])
        rIs.append(float(np.sum(residS ** 2) / (np.sum((w["y"][S] - w["y"][S].mean()) ** 2) + 1e-12)))
        bics.append(_bic_two_component(residS))
    return {"rI_q10": float(np.quantile(rIs, 0.10)), "bic2": float(np.quantile(bics, 0.90))}

# ----------------------------------------------------------------------------- endpoints / verdict
def endpoints(preds, truths, null_resolved_gate=NULL_RESOLVED_GATE):
    """E1..E4 with pre-registered abstention accounting.
    E1: balanced accuracy, class weights I=0.5, pooled{II,III}=0.5; denominator=all worlds, abstention=error.
    E2: balanced accuracy II vs III (0.5/0.5); abstention=error.
    E3: null false-class rate (decision in I/II/III); null-resolved gate (option (a)): null unresolvable<=0.50.
    E4: unresolvable rate over non-null worlds <=0.10; E4b: per-class (I/II/III) resolved rate >=0.85.
    """
    preds = np.array(preds, dtype=object); truths = np.array(truths, dtype=object)
    dec = np.array([p["decision"] for p in preds], dtype=object)
    is_abstain = (dec == "unresolvable")
    def acc(mask, target):
        m = mask
        if not m.any():
            return np.nan
        return float(np.mean(dec[m] == target))
    nonnull = truths != "null"
    accI = acc(truths == "I", "I")
    acc_pool = np.nanmean([acc(truths == "II", "II"), acc(truths == "III", "III")])
    E1 = 0.5 * accI + 0.5 * acc_pool
    E2 = 0.5 * (acc(truths == "II", "II") + acc(truths == "III", "III"))
    nullmask = truths == "null"
    E3 = float(np.mean(np.isin(dec[nullmask], ["I", "II", "III"]))) if nullmask.any() else np.nan
    null_unres = float(np.mean(is_abstain[nullmask])) if nullmask.any() else np.nan
    null_gate_ok = bool(null_unres <= null_resolved_gate)
    nonnull_abstain = float(np.mean(is_abstain[nonnull])) if nonnull.any() else np.nan
    E4 = nonnull_abstain
    per_class_resolved = {c: float(np.mean(~is_abstain[truths == c])) for c in ("I", "II", "III")}
    return {"E1": E1, "E2": E2, "E3": E3, "E4": E4, "E4b": per_class_resolved,
            "null_unresolvable": null_unres, "null_gate_ok": null_gate_ok}

def verdict(ep):
    """Pre-registered attribution of partial/fail (challenge A2v3 must-fix 4)."""
    e1_ok = ep["E1"] == ep["E1"] and ep["E1"] >= 0.80
    e2_ok = ep["E2"] == ep["E2"] and ep["E2"] >= 0.70
    e3_ok = ep["E3"] == ep["E3"] and ep["E3"] <= 0.10
    e4_ok = ep["E4"] <= 0.10
    e4b_ok = all(v >= E4B_PER_CLASS_RESOLVED for v in ep["E4b"].values())
    null_ok = bool(ep["null_gate_ok"])
    if not e1_ok:
        return "constructive_fail"
    if not e2_ok:
        return "constructive_partial"
    if not (e3_ok and e4_ok and e4b_ok and null_ok):
        return "constructive_fail"
    return "constructive_pass"

# ----------------------------------------------------------------------------- MDE plan / runner
def mde_plan():
    return {"worlds_per_class": N_WORLDS_PER_CLASS, "classes": list(CLASSES),
            "sigma_grid": list(SIGMAS), "delta_grid": list(DELTAS),
            "worlds_total": N_WORLDS_PER_CLASS * len(CLASSES), "k_grid": list(K_GRID),
            "batches_mde": N_BATCHES_MDE,
            "classifier_calls_estimate": N_BATCHES_MDE * len(K_GRID) * len(CLASSES),
            "estimated_runtime_min": "<=5 (UNVERIFIED PLANNING VALUE; not measured)",
            "required": "for each endpoint and k: MDE <= DELTA_MIN[endpoint]; else design_uninformative",
            "e3_rule": "option (a): null unresolvable rate <= 0.50 is a design-check gate; null abstention counts as no-false-class for E3",
            "e4b": "per-class resolved >= 0.85 for I/II/III (null excluded)",
            "e1_weights": "class-balanced: I=0.5, pooled{II,III}=0.5 (II,III equal within pool)",
            "k6_state_reading": "z totals 3/3 across 6 units (no per-stratum balance; III not judged at k=6)",
            "partial_fail": "E1 fail -> constructive_fail; E1 pass & E2 fail -> constructive_partial; E3/E4/E4b/null-gate fail -> constructive_fail"}

def run_pipeline():
    """FULL simulation (only reachable with --confirm-run; NOT RUN in R198)."""
    design, sz = load_design()
    units_meta = load_units(design, sz)
    rng0 = np.random.default_rng(SEED_BASE)
    worlds = []
    for cls in CLASSES:
        for si, sigma in enumerate(SIGMAS):
            for di, delta in enumerate(DELTAS):
                for w in range(N_WORLDS_PER_CLASS // (len(SIGMAS) * len(DELTAS))):
                    seed = SEED_BASE + 100000 * CLASSES.index(cls) + 1000 * si + 100 * di + w
                    worlds.append(make_world(design, units_meta, cls, sigma, delta, seed))
    null_worlds = [w for w in worlds if w["class"] == "null"]
    rng = np.random.default_rng(SEED_BASE + 7)
    thresholds = calibration_thresholds(null_worlds, rng)
    results = {}
    for k in K_GRID:
        preds, truths = [], []
        for w in worlds:
            b = sample_batch(w, k, rng)
            preds.append(classify(b, w, k, thresholds, rng)); truths.append(w["class"])
        ep = endpoints(preds, truths)
        results[k] = {"endpoints": ep, "verdict": verdict(ep), "MDE": "see mde_simulation()"}
    return {"thresholds": thresholds, "results": results, "mde_plan": mde_plan()}

def main(argv):
    ap = argparse.ArgumentParser(description="A2v4 constructive simulator (full pipeline; NOT RUN in R198)")
    ap.add_argument("--confirm-run", action="store_true", help="required to execute; forbidden in R198-A2v4")
    args = ap.parse_args(argv)
    if not args.confirm_run:
        print("REFUSING TO RUN: R198-A2v4 is design-only. Use --confirm-run only after protocol freeze.")
        print(json.dumps({"mde_plan": mde_plan(),
                          "k_allocation": {str(k): k_allocation(k) for k in K_GRID},
                          "delta_min": DELTA_MIN, "e4b": E4B_PER_CLASS_RESOLVED,
                          "null_resolved_gate": NULL_RESOLVED_GATE}, ensure_ascii=False, indent=1))
        return 0
    out = run_pipeline()
    print(json.dumps(out, ensure_ascii=False, indent=1, default=str))
    return 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
