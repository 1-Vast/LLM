"""Reference-only leave-one-line-out: hyperparameter choice, arm ceilings and the WMVC gate.

Writes ``GATE.json`` and ``reference_loo.npz``. No held-out file is opened.
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import analysis as A  # noqa: E402

MUB = 0.05


def load_reference():
    keep, info = A.qualified_reference()
    panel = A.phenotype_panel(keep, keep, info["table"], info["names"])
    panel = A.attach_expression(panel)
    cm = pd.read_parquet(A.CACHE / "metadata/tahoe_cells.parquet")
    dm = pd.read_parquet(A.CACHE / "metadata/tahoe_drugs.parquet")
    organ = {A.norm(r.cell_name): r.Organ for _, r in cm.iterrows()}
    drivers = {}
    for _, r in cm.iterrows():
        if r.Driver_Mech_InferDM == "GoF" or r.Driver_GeneType_DM == "Oncogene":
            drivers.setdefault(A.norm(r.cell_name), set()).add(str(r.Driver_Gene_Symbol))
    targets = {A.norm(r.drug): {t.strip() for t in str(r.targets).split(",")} if r.targets else set() for _, r in dm.iterrows()}
    moa = {A.norm(r.drug): str(r["moa-fine"]) for _, r in dm.iterrows()}
    panel.meta = {"organ": [organ.get(A.norm(panel.names[f])) for f in panel.files],
                  "drivers": [drivers.get(A.norm(panel.names[f]), set()) for f in panel.files],
                  "targets": targets, "moa": moa, "refused": info["refused"], "medians": info["medians"]}
    return panel


def loo(panel, endpoint: str = "survival"):
    values = panel.survival if endpoint == "survival" else panel.g1
    labels = panel.labels
    doses = np.array([A.dose_of(l) for l in labels])
    c5 = np.flatnonzero(doses == 5.0)
    call = np.arange(len(labels))
    n = len(panel.files)
    preds = {"Z": np.zeros((n, len(c5))), "O": np.zeros((n, len(c5))), "K": np.zeros((n, len(c5)))}
    kern = {(t, m): np.zeros((n, len(c5))) for t in A.KERNEL_GRID["tau"] for m in A.KERNEL_GRID["top_m"]}
    rkern = {(t, m): np.zeros((n, len(c5))) for t in A.KERNEL_GRID["tau"] for m in A.KERNEL_GRID["top_m"]}
    bridge = {(p, a, d): np.zeros((n, len(c5))) for p in A.BRIDGE_GRID["n_pc"] for a in A.BRIDGE_GRID["alpha"] for d in A.BRIDGE_GRID["doses"]}
    obs = np.zeros((n, len(c5)))
    generic = np.zeros((n, len(c5)))
    for j in range(n):
        train = np.array([i for i in range(n) if i != j])
        T = A.selectivity(values, train)
        obs[j] = T[j, c5]
        generic[j] = np.nanmean(values[train][:, c5], axis=0)
        preds["O"][j], _ = A.organ_prior(panel.meta["organ"][j], [panel.meta["organ"][i] for i in train], T[train][:, c5])
        preds["K"][j] = A.knowledge_prior(panel.meta["drivers"][j], [labels[c] for c in c5], panel.meta["targets"])
        for (t, m) in kern:
            kern[(t, m)][j] = A.kernel_prior(panel.basal[j], panel.basal[train], T[train][:, c5], t, m)
        panel_delta = np.nanmean(panel.delta[train], axis=0)
        Xj = panel.delta[j, c5] - panel_delta[c5]
        prof_j = A.response_profile(panel.delta[j, c5], panel_delta[c5])
        prof_train = np.stack([A.response_profile(panel.delta[i, c5], panel_delta[c5]) for i in train])
        for (t, m) in rkern:
            rkern[(t, m)][j] = A.kernel_prior(prof_j, prof_train, T[train][:, c5], t, m)
        del prof_train
        for d in A.BRIDGE_GRID["doses"]:
            cols = c5 if d == "5uM" else call
            X, y = A.bridge_rows(panel.delta, T, train, cols, panel_delta)
            mu = X.mean(0)
            Xc = X - mu
            _, _, vt = np.linalg.svd(Xc[np.random.RandomState(0).permutation(len(Xc))[:20000]], full_matrices=False)
            for p in A.BRIDGE_GRID["n_pc"]:
                comp = vt[:p]
                Z = Xc @ comp.T
                Zj = np.nan_to_num(Xj - mu) @ comp.T
                for a in A.BRIDGE_GRID["alpha"]:
                    w = np.linalg.solve(Z.T @ Z + a * np.eye(p), Z.T @ (y - y.mean()))
                    bridge[(p, a, d)][j] = Zj @ w + y.mean()
        print(json.dumps({"endpoint": endpoint, "fold": j, "line": panel.names[panel.files[j]]}), flush=True)
    return {"obs": obs, "generic": generic, "preds": preds, "kern": kern, "rkern": rkern, "bridge": bridge, "c5": c5}


def score(pred, obs, generic):
    r = np.array([A.within_r(pred[j], obs[j]) for j in range(len(obs))])
    u = np.array([A.topk_utility(pred[j], obs[j], generic[j]) for j in range(len(obs))])
    return r, u


def summarize(res):
    out = {}
    obs, gen = res["obs"], res["generic"]
    for name, pred in res["preds"].items():
        r, u = score(pred, obs, gen)
        out[name] = {"mean_r": float(np.nanmean(r)), "mean_top10_utility": float(np.mean(u)), "r": r.tolist(), "u": u.tolist()}
    best = {name: max(res[table], key=lambda k: np.nanmean(score(res[table][k], obs, gen)[0]))
            for name, table in (("B", "kern"), ("R", "bridge"), ("RK", "rkern"))}
    for name, key, table in (("B", best["B"], res["kern"]), ("R", best["R"], res["bridge"]), ("RK", best["RK"], res["rkern"])):
        r, u = score(table[key], obs, gen)
        out[name] = {"config": list(key), "mean_r": float(np.nanmean(r)), "mean_top10_utility": float(np.mean(u)), "r": r.tolist(), "u": u.tolist()}
    out["grid_mean_r"] = {"B": {str(k): float(np.nanmean(score(v, obs, gen)[0])) for k, v in res["kern"].items()},
                          "R": {str(k): float(np.nanmean(score(v, obs, gen)[0])) for k, v in res["bridge"].items()},
                          "RK": {str(k): float(np.nanmean(score(v, obs, gen)[0])) for k, v in res["rkern"].items()}}
    # an oracle-of-the-outcome top-10 (inflated by noise) as a descriptive scale
    out["outcome_oracle_top10_utility"] = float(np.mean([A.topk_utility(obs[j], obs[j], gen[j]) for j in range(len(obs))]))
    return out


def write_menu(panel):
    """Fix the 5 uM menu: reference-measured labels that the checkpoint's one-hot map contains."""
    import torch
    sys.path.insert(0, str(A.ROOT / "src"))
    from virtual_cell.state_runner import _numpy_scalar_globals
    weights = A.ROOT / "data/external/arc_state/weights/zeroshot/state_generalization_zeroshot_X_hvg/pert_onehot_map.pt"
    with torch.serialization.safe_globals(list(_numpy_scalar_globals())):
        mapping = torch.load(weights, map_location="cpu", weights_only=True)
    five = [l for l in panel.labels if A.dose_of(l) == 5.0]
    menu = {"labels_5uM": [l for l in five if l in mapping],
            "refused": [{"label": l, "reason": "LABEL_NOT_IN_CHECKPOINT"} for l in five if l not in mapping],
            "all_labels_in_map": [l for l in panel.labels if l in mapping]}
    (HERE / "MENU.json").write_text(json.dumps(menu, indent=1), encoding="utf-8")
    return menu


def main():
    started = time.perf_counter()
    panel = load_reference()
    menu = write_menu(panel)
    if len(menu["labels_5uM"]) != len([l for l in panel.labels if A.dose_of(l) == 5.0]):
        raise SystemExit("5 uM labels missing from the checkpoint map; menu must be re-declared")
    result = {"reference_lines": [panel.names[f] for f in panel.files], "refused": panel.meta["refused"], "mub": MUB}
    arrays = {}
    for endpoint in ("survival", "g1"):
        res = loo(panel, endpoint)
        summary = summarize(res)
        result[endpoint] = summary
        arrays[f"{endpoint}_obs"] = res["obs"]
        arrays[f"{endpoint}_R"] = res["bridge"][tuple(summary["R"]["config"])]
        arrays[f"{endpoint}_B"] = res["kern"][tuple(summary["B"]["config"])]
        arrays[f"{endpoint}_RK"] = res["rkern"][tuple(summary["RK"]["config"])]
    s = result["survival"]
    readout = "kernel" if s["RK"]["mean_r"] > s["R"]["mean_r"] else "bridge"
    ceiling = max(s["R"]["mean_r"], s["RK"]["mean_r"])
    margin = ceiling - max(s["B"]["mean_r"], s["O"]["mean_r"])
    result["gate"] = {"endpoint": "E1 survival selectivity at 5 uM", "r_R_bridge": s["R"]["mean_r"], "r_RK_kernel": s["RK"]["mean_r"],
                      "r_B": s["B"]["mean_r"], "r_O": s["O"]["mean_r"], "primary_state_readout": readout,
                      "margin": margin, "passes": bool(margin >= MUB),
                      "decision": "evaluate S as decision input" if margin >= MUB else "WM_CEILING_BELOW_MUB"}
    result["seconds"] = round(time.perf_counter() - started, 1)
    np.savez(HERE / "reference_loo.npz", **arrays)
    result["reference_loo_sha256"] = hashlib.sha256((HERE / "reference_loo.npz").read_bytes()).hexdigest()
    (HERE / "GATE.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("gate", "seconds")}, indent=1))
    for e in ("survival", "g1"):
        print(e, {k: (round(v["mean_r"], 3), round(v["mean_top10_utility"], 3), v.get("config")) for k, v in result[e].items() if isinstance(v, dict) and "mean_r" in v})


if __name__ == "__main__":
    main()
