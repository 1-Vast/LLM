"""Workstream C, task 1: independent recomputation of the primary contrast.

Written by the verifier from the stated definitions only. It imports nothing
from the study package; it reads plans, rows.npy, slots.npz,
treated_summaries.npz and the STATE forecast npz files directly.

Definitions implemented (as given in the verification brief):
  observed(g, ctx)  = mean over FULL-QC treated rows of g
                      - mean over FULL-QC 'reference' DMSO rows of the same plate
  noise(g, ctx)     = mean_j var_T,j / n_T + mean_j var_C,j / n_C   (ddof = 1)
  M0                = sum_l w_l observed(g, l) over the 45 training contexts with
                      n_T(l) >= 8 for the (label, plate) key; w_l ~ 1/noise_l, sum w = 1
  devS(L, g)        = paired_delta(L, g) - simple mean over training contexts with a
                      forecast for the key of paired_delta(l, g)
  M2                = M0 + 0.5 * devS
  corrected SE      = mean_j (forecast - observed)^2 - sum_l w_l^2 noise_l - noise_L
  eligible          = n_T >= 50, n_C(reference, plate) >= 100, panel contexts >= 30, not DMSO

Usage: python task1_recompute.py <out_json> <heldout_file> [<heldout_file> ...]
"""
import json
import os
import sys
import time

import numpy as np

S = r"D:\MAESTRO\research\astra\zeroshot_context_20261007"
C = r"D:\MAESTRO\data\external\tahoe_zeroshot_20261007"
SCRATCH = os.environ.get("VERIFY_SCRATCH", "")
DMSO = "[('DMSO_TF', 0.0, 'uM')]"
GAMMA_S = 0.5
MIN_PANEL_CELLS = 8
MIN_TREATED = 50
MIN_REFERENCE = 100
MIN_PANEL_CONTEXTS = 30


def load_plan(f):
    with open(os.path.join(C, "extract", "plans", f + ".plan.json"), encoding="utf-8") as fh:
        return json.load(fh)


def load_slots(f):
    z = np.load(os.path.join(C, "extract", f, "slots.npz"))
    return {int(g): int(s) for g, s in zip(z["group"], z["start"])}


def open_rows(f):
    return np.load(os.path.join(C, "extract", f, "rows.npy"), mmap_mode="r")


def group_block(rows, slots, g):
    start = slots[g["group"]]
    n = len(g["rows"])
    block = np.asarray(rows[start:start + n], dtype=np.float64)
    assert block.shape == (n, 2000), block.shape
    return block


def reference_dmso(plan, slots, rows):
    """Per plate: mean, var (ddof=1), n of FULL-QC reference DMSO rows; also basal count."""
    out = {}
    for g in plan["groups"]:
        if not g["control"]:
            continue
        if g["label"] != DMSO:
            raise RuntimeError("control group with non-DMSO label: %r" % g["label"])
        if g["plate"] in out:
            raise RuntimeError("two control groups on plate %s" % g["plate"])
        full = np.asarray(g["full"], dtype=bool)
        role = np.asarray(g["control_role"])
        ref = full & (role == "reference")
        bas = full & (role == "basal")
        X = group_block(rows, slots, g)[ref]
        out[g["plate"]] = {
            "mean": X.mean(axis=0),
            "var": X.var(axis=0, ddof=1),
            "n": int(ref.sum()),
            "n_basal_full": int(bas.sum()),
            "group": g["group"],
        }
    return out


def build_panel(train_files):
    """Stream over training contexts; accumulate per (label, plate) key."""
    panel = {}   # key -> {"inv": [1/noise_l], "noise": [noise_l], "sy": sum y_l/noise_l, "ctx": [...]}
    pd_sum = {}  # key -> sum paired_delta over training contexts with a forecast
    pd_cnt = {}
    audit = {"train_files": len(train_files), "min_reference_n": None, "summary_n_mismatch": 0,
             "plates_missing_reference": 0}
    min_ref = None
    for f in train_files:
        t0 = time.time()
        plan = load_plan(f)
        slots = load_slots(f)
        rows = open_rows(f)
        ref = reference_dmso(plan, slots, rows)
        for st in ref.values():
            min_ref = st["n"] if min_ref is None else min(min_ref, st["n"])
        gm = {g["group"]: g for g in plan["groups"]}
        ts = np.load(os.path.join(C, "extract", f, "treated_summaries.npz"))
        groups, ns, means, vars_ = ts["group"], ts["n"], ts["mean"], ts["var"]
        for i in range(len(groups)):
            g = gm[int(groups[i])]
            if g["control"]:
                raise RuntimeError("summary for a control group")
            n = int(ns[i])
            if n != int(np.sum(g["full"])):
                audit["summary_n_mismatch"] += 1
            if n < MIN_PANEL_CELLS:
                continue
            if g["plate"] not in ref:
                audit["plates_missing_reference"] += 1
                continue
            r = ref[g["plate"]]
            y = means[i].astype(np.float64) - r["mean"]
            noise = float(vars_[i].astype(np.float64).mean()) / n + float(r["var"].mean()) / r["n"]
            key = (g["label"], g["plate"])
            e = panel.get(key)
            if e is None:
                e = panel[key] = {"inv": [], "noise": [], "sy": np.zeros(2000), "ctx": []}
            e["inv"].append(1.0 / noise)
            e["noise"].append(noise)
            e["sy"] += y / noise
            e["ctx"].append(f)
        sf = np.load(os.path.join(C, "state_forecasts", f + ".npz"))
        for lab, pl, pdv in zip(sf["label"].tolist(), sf["plate"].tolist(), sf["paired_delta"]):
            key = (lab, pl)
            if key not in pd_sum:
                pd_sum[key] = np.zeros(2000)
                pd_cnt[key] = 0
            pd_sum[key] += pdv.astype(np.float64)
            pd_cnt[key] += 1
        print("panel %s %.1fs keys=%d" % (f, time.time() - t0, len(panel)), flush=True)
    audit["min_reference_n"] = min_ref
    return panel, pd_sum, pd_cnt, audit


def evaluate_line(f, panel, pd_sum, pd_cnt):
    t0 = time.time()
    plan = load_plan(f)
    slots = load_slots(f)
    rows = open_rows(f)
    ref = reference_dmso(plan, slots, rows)
    sf = np.load(os.path.join(C, "state_forecasts", f + ".npz"))
    fc = {(l, p): i for i, (l, p) in enumerate(zip(sf["label"].tolist(), sf["plate"].tolist()))}
    pdL = sf["paired_delta"]
    recs = []
    reasons = {"treated_lt_50": 0, "reference_lt_100": 0, "panel_lt_30": 0, "no_forecast": 0}
    for g in plan["groups"]:
        if g["control"]:
            continue
        key = (g["label"], g["plate"])
        full = np.asarray(g["full"], dtype=bool)
        nT = int(full.sum())
        r = ref.get(g["plate"])
        nC = r["n"] if r is not None else 0
        e = panel.get(key)
        nP = len(e["inv"]) if e is not None else 0
        bad = False
        if nT < MIN_TREATED:
            reasons["treated_lt_50"] += 1
            bad = True
        if nC < MIN_REFERENCE:
            reasons["reference_lt_100"] += 1
            bad = True
        if nP < MIN_PANEL_CONTEXTS:
            reasons["panel_lt_30"] += 1
            bad = True
        if key not in fc or key not in pd_sum:
            reasons["no_forecast"] += 1
            bad = True
        if bad:
            continue
        X = group_block(rows, slots, g)[full]
        muT = X.mean(axis=0)
        varT = X.var(axis=0, ddof=1)
        obs = muT - r["mean"]
        noiseL = float(varT.mean()) / nT + float(r["var"].mean()) / nC
        inv = np.asarray(e["inv"])
        noise_l = np.asarray(e["noise"])
        w = inv / inv.sum()
        m0 = e["sy"] / inv.sum()
        panel_noise = float(np.sum(w * w * noise_l))
        devS = pdL[fc[key]].astype(np.float64) - pd_sum[key] / pd_cnt[key]
        m2 = m0 + GAMMA_S * devS
        se0 = float(np.mean((m0 - obs) ** 2)) - panel_noise - noiseL
        se2 = float(np.mean((m2 - obs) ** 2)) - panel_noise - noiseL
        recs.append({
            "group": g["group"], "label": g["label"], "plate": g["plate"],
            "n_T": nT, "n_C": nC, "n_panel": nP, "n_forecast_train": pd_cnt[key],
            "noise_L": noiseL, "panel_noise": panel_noise,
            "obs_energy": float(np.mean(obs ** 2)),
            "se_M0": se0, "se_M2": se2,
        })
    se0 = np.array([x["se_M0"] for x in recs])
    se2 = np.array([x["se_M2"] for x in recs])
    out = {
        "file": f,
        "eligible_groups": len(recs),
        "treated_groups_in_plan": sum(1 for g in plan["groups"] if not g["control"]),
        "ineligible_reasons_nonexclusive": reasons,
        "reference_n_by_plate": {p: v["n"] for p, v in sorted(ref.items())},
        "basal_full_n_by_plate": {p: v["n_basal_full"] for p, v in sorted(ref.items())},
        "mean_se_M0": float(se0.mean()),
        "mean_se_M2": float(se2.mean()),
        "mean_M2_minus_M0": float((se2 - se0).mean()),
        "seconds": round(time.time() - t0, 1),
        "groups": recs,
    }
    print("line %s eligible=%d M0=%.6g M2=%.6g diff=%.6g (%.1fs)" % (
        f, len(recs), out["mean_se_M0"], out["mean_se_M2"], out["mean_M2_minus_M0"], out["seconds"]), flush=True)
    return out


def main():
    out_json = sys.argv[1]
    lines = sys.argv[2:]
    with open(os.path.join(S, "SPLIT.json"), encoding="utf-8") as fh:
        split = json.load(fh)
    heldout = set(split["files"].values())
    assert len(heldout) == 5
    train_files = [f"c{i}.h5ad" for i in range(50) if f"c{i}.h5ad" not in heldout]
    assert len(train_files) == 45
    t0 = time.time()
    panel, pd_sum, pd_cnt, audit = build_panel(train_files)
    audit["panel_keys"] = len(panel)
    audit["panel_keys_ge30"] = sum(1 for e in panel.values() if len(e["inv"]) >= MIN_PANEL_CONTEXTS)
    audit["forecast_keys"] = len(pd_sum)
    audit["panel_seconds"] = round(time.time() - t0, 1)
    result = {"audit": audit, "lines": {}}
    for f in lines:
        result["lines"][f] = evaluate_line(f, panel, pd_sum, pd_cnt)
        with open(out_json, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=1)
    print("done", round(time.time() - t0, 1), flush=True)


if __name__ == "__main__":
    main()
