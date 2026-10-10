"""Stage 5: one-time held-out evaluation of the frozen arms (PROTOCOL sections 4-6).

Inputs, all produced after FREEZE.json: held-out obs (phenotypes), held-out expression (oracle and
basal profile), STATE forecasts (target and context-permuted), LLM answers. Hyperparameters come
from GATE.json; nothing is chosen here. Writes RESULTS.json and PREDICTIONS.npz.
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
import gate as G  # noqa: E402

HELDOUT = list(A.P.HELDOUT)
PERMUTED_BASAL = {f: HELDOUT[(i + 1) % len(HELDOUT)] for i, f in enumerate(HELDOUT)}
BOOTSTRAP, SEED = 2000, 20261010
SCREEN, COMMIT = 8, 5


def zscore(v):
    s = np.nanstd(v)
    return (v - np.nanmean(v)) / s if s > 0 else np.zeros_like(v)


def heldout_panel(ref, table, names):
    hp = A.phenotype_panel(HELDOUT, ref.files, table, names)
    index = [hp.labels.index(l) if l in hp.labels else None for l in ref.labels]
    surv = np.array([[hp.survival[i, j] if j is not None else np.nan for j in index] for i in range(len(HELDOUT))])
    g1 = np.array([[hp.g1[i, j] if j is not None else np.nan for j in index] for i in range(len(HELDOUT))])
    out = A.Panel(files=HELDOUT, names={f: names[f] for f in HELDOUT}, labels=ref.labels, survival=surv, g1=g1)
    return A.attach_expression(out)


def state_delta(tag, labels):
    """Plate-mean paired STATE delta and predicted G1 log-odds shift per label (NaN if refused)."""
    z = np.load(A.CACHE / "state_forecasts" / f"{tag}.npz")
    li = {l: i for i, l in enumerate(labels)}
    acc, g1 = {}, {}
    gi = list(z["phases"]).index("G1")
    for lab, d, p, p0 in zip(z["label"], z["paired_delta"], z["phase_prob"], z["dmso_phase_prob"]):
        if lab in li:
            acc.setdefault(lab, []).append(d)
            lo = np.log(p[gi] / (1 - p[gi])) - np.log(p0[gi] / (1 - p0[gi]))
            g1.setdefault(lab, []).append(lo)
    delta = np.full((len(labels), 2000), np.nan, np.float32)
    shift = np.full(len(labels), np.nan)
    for lab, rows in acc.items():
        delta[li[lab]] = np.mean(rows, axis=0)
        shift[li[lab]] = np.mean(g1[lab])
    return delta, shift


def fit_bridge(ref, T, cols, config):
    n_pc, alpha, doses = config
    use = cols if doses == "5uM" else np.arange(len(ref.labels))
    panel_delta = np.nanmean(ref.delta, axis=0)
    X, y = A.bridge_rows(ref.delta, T, np.arange(len(ref.files)), use, panel_delta)
    return A.Bridge(n_pc, alpha).fit(X, y), panel_delta


def llm_prediction(f, labels5):
    path = HERE / "llm" / f"{f}.json"
    rec = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"status": "missing"}
    pred = np.zeros(len(labels5))
    if rec.get("status") == "ok":
        pos = {A.drug_of(l): i for i, l in enumerate(labels5)}
        for rank, name in enumerate(rec["ranked"]):
            pred[pos[name]] = -(A.TOP_K * 3 - rank)
    return pred, rec.get("status"), rec.get("reason")


def cluster_bootstrap(stat_fn, clusters, rng):
    uniq = np.unique(clusters)
    members = {c: np.flatnonzero(clusters == c) for c in uniq}
    draws = []
    for _ in range(BOOTSTRAP):
        pick = rng.choice(uniq, len(uniq), replace=True)
        draws.append(stat_fn(np.concatenate([members[c] for c in pick])))
    return np.percentile(draws, [2.5, 97.5]).tolist()


def compare(pred_a, pred_b, obs, generic, clusters, metric, rng):
    """Mean over lines of metric(a) - metric(b), drug-cluster bootstrap CI, lines with a > b."""
    def stat(idx):
        out = []
        for j in range(len(obs)):
            if metric == "r":
                out.append(A.within_r(pred_a[j][idx], obs[j][idx]) - A.within_r(pred_b[j][idx], obs[j][idx]))
            else:
                out.append(A.topk_utility(pred_a[j][idx], obs[j][idx], generic[j][idx]) - A.topk_utility(pred_b[j][idx], obs[j][idx], generic[j][idx]))
        return float(np.nanmean(out))
    full = np.arange(obs.shape[1])
    per_line = []
    for j in range(len(obs)):
        if metric == "r":
            per_line.append(A.within_r(pred_a[j], obs[j]) - A.within_r(pred_b[j], obs[j]))
        else:
            per_line.append(A.topk_utility(pred_a[j], obs[j], generic[j]) - A.topk_utility(pred_b[j], obs[j], generic[j]))
    ci = cluster_bootstrap(stat, clusters, rng)
    wins = int(np.sum(np.array(per_line) > 0))
    return {"mean_difference": stat(full), "ci95": ci, "per_line": per_line, "lines_better": wins,
            "success": bool(ci[0] > 0 and wins >= 4)}


def screening(prior, A_obs, B_obs, generic):
    """D2: no-screen top-5 by prior, and fixed top-8 screen then commit the best 5 observed A; score on B."""
    ok = np.flatnonzero(~np.isnan(A_obs) & ~np.isnan(B_obs))
    order = ok[np.lexsort((generic[ok], prior[ok]))]
    no_screen = float(-np.mean(B_obs[order[:COMMIT]]))
    screened = order[:SCREEN]
    commit = screened[np.argsort(A_obs[screened])[:COMMIT]]
    return {"no_screen": no_screen, "screen": float(-np.mean(B_obs[commit])), "credits_no_screen": COMMIT,
            "credits_screen": SCREEN + COMMIT, "menu": int(len(ok))}


def main(out_dir: Path = HERE, poison_seed: int | None = None):
    """Evaluate once. ``poison_seed`` replaces held-out phenotypes with noise (verification only)."""
    started = time.perf_counter()
    if not (HERE / "FREEZE.json").exists():
        raise SystemExit("evaluation requires FREEZE.json")
    gate = json.loads((HERE / "GATE.json").read_text(encoding="utf-8"))
    menu = json.loads((HERE / "MENU.json").read_text(encoding="utf-8"))
    ref = G.load_reference()
    _, info = A.qualified_reference()
    table, names = dict(info["table"]), dict(info["names"])
    held_table, held_names = A.P.load_counts(HELDOUT)
    table.update(held_table)
    names.update(held_names)
    held = heldout_panel(ref, table, names)
    if poison_seed is not None:
        noise = np.random.RandomState(poison_seed)
        held.survival = noise.normal(size=held.survival.shape)
        held.g1 = noise.normal(size=held.g1.shape)
        table = {k: ({**v, "n": int(noise.randint(1, 5000))} if k[0] in HELDOUT else v) for k, v in table.items()}
    labels5 = menu["labels_5uM"]
    c5 = np.array([ref.labels.index(l) for l in labels5])
    all_rows = np.arange(len(ref.files))
    drugs = pd.read_parquet(A.CACHE / "metadata/tahoe_drugs.parquet")
    moa = {A.norm(r.drug): str(r["moa-fine"]) for _, r in drugs.iterrows()}
    clusters = np.array([moa.get(A.norm(A.drug_of(l)), "unknown") for l in labels5])
    cells = pd.read_parquet(A.CACHE / "metadata/tahoe_cells.parquet")
    organ = {A.norm(r.cell_name): r.Organ for _, r in cells.iterrows()}
    drivers = {}
    for _, r in cells.iterrows():
        if r.Driver_Mech_InferDM == "GoF" or r.Driver_GeneType_DM == "Oncogene":
            drivers.setdefault(A.norm(r.cell_name), set()).add(str(r.Driver_Gene_Symbol))

    results = {"protocol": "PROTOCOL.md", "gate": gate["gate"], "menu_size": len(labels5), "lines": {}}
    endpoints = {}
    for endpoint, values_ref, values_held in (("E1_survival", ref.survival, held.survival), ("E2_g1", ref.g1, held.g1)):
        T_ref = A.selectivity(values_ref, all_rows)
        ref_mean = np.nanmean(values_ref, axis=0)
        obs = values_held[:, c5] - ref_mean[c5]
        generic = np.tile(ref_mean[c5], (len(HELDOUT), 1))
        key = "survival" if endpoint == "E1_survival" else "g1"
        cfg = gate[key]
        bridge, panel_delta = fit_bridge(ref, T_ref, c5, tuple(cfg["R"]["config"]))
        tau_b, m_b = cfg["B"]["config"]
        tau_k, m_k = cfg["RK"]["config"]
        ref_profiles = np.stack([A.response_profile(ref.delta[i, c5], panel_delta[c5]) for i in all_rows])
        preds = {k: np.zeros((len(HELDOUT), len(c5))) for k in ("Z", "O", "K", "B", "S_bridge", "S_kernel", "Sperm_bridge", "Sperm_kernel", "R_bridge", "R_kernel", "L", "S_cells")}
        refusals = {}
        for j, f in enumerate(HELDOUT):
            nm = A.norm(names[f])
            preds["O"][j], why = A.organ_prior(organ.get(nm), ref.meta["organ"], T_ref[:, c5])
            if why:
                refusals.setdefault(f, []).append(why)
            preds["K"][j] = A.knowledge_prior(drivers.get(nm, set()), labels5, ref.meta["targets"])
            preds["B"][j] = A.kernel_prior(held.basal[j], ref.basal, T_ref[:, c5], tau_b, m_b)
            obs_dev = held.delta[j, c5] - panel_delta[c5]
            preds["R_bridge"][j] = bridge.predict(np.nan_to_num(obs_dev))
            preds["R_kernel"][j] = A.kernel_prior(A.response_profile(held.delta[j, c5], panel_delta[c5]), ref_profiles, T_ref[:, c5], tau_k, m_k)
            for tag, prefix in ((f, "S"), (f"{f}__basal_{PERMUTED_BASAL[f]}", "Sperm")):
                sdelta, sshift = state_delta(tag, ref.labels)
                dev = sdelta[c5] - panel_delta[c5]
                preds[f"{prefix}_bridge"][j] = bridge.predict(np.nan_to_num(dev))
                preds[f"{prefix}_kernel"][j] = A.kernel_prior(A.response_profile(sdelta[c5], panel_delta[c5]), ref_profiles, T_ref[:, c5], tau_k, m_k)
                if prefix == "S":
                    preds["S_cells"][j] = zscore(sshift[c5]) - zscore(ref_mean[c5])
            preds["L"][j], status, reason = llm_prediction(f, labels5)
            if status != "ok":
                refusals.setdefault(f, []).append(reason or "LLM_MISSING")
        primary = "S_kernel" if gate["gate"]["primary_state_readout"] == "kernel" else "S_bridge"
        preds["S"] = preds[primary]
        preds["Sperm"] = preds["Sperm_kernel" if primary == "S_kernel" else "Sperm_bridge"]
        preds["SB"] = np.stack([zscore(preds["S"][j]) + zscore(preds["B"][j]) for j in range(len(HELDOUT))]) / 2
        rng = np.random.RandomState(SEED)
        summary = {"primary_state_readout": primary, "refusals": refusals, "arms": {}}
        for name, pred in preds.items():
            r = [A.within_r(pred[j], obs[j]) for j in range(len(HELDOUT))]
            u = [A.topk_utility(pred[j], obs[j], generic[j]) for j in range(len(HELDOUT))]
            summary["arms"][name] = {"r": r, "mean_r": float(np.nanmean(r)), "top10_utility": u, "mean_top10_utility": float(np.mean(u))}
        summary["outcome_oracle_top10_utility"] = float(np.mean([A.topk_utility(obs[j], obs[j], generic[j]) for j in range(len(HELDOUT))]))
        tests = {}
        if endpoint == "E1_survival":
            tests["H1_S_vs_B_r"] = compare(preds["S"], preds["B"], obs, generic, clusters, "r", rng)
            tests["H2_S_vs_B_top10"] = compare(preds["S"], preds["B"], obs, generic, clusters, "u", rng)
            tests["H2_S_vs_Z_top10"] = compare(preds["S"], preds["Z"], obs, generic, clusters, "u", rng)
            tests["H3_SB_vs_B_r"] = compare(preds["SB"], preds["B"], obs, generic, clusters, "r", rng)
            tests["H3_SB_vs_B_top10"] = compare(preds["SB"], preds["B"], obs, generic, clusters, "u", rng)
            tests["H3_SB_vs_S_r"] = compare(preds["SB"], preds["S"], obs, generic, clusters, "r", rng)
            tests["H3_SB_vs_S_top10"] = compare(preds["SB"], preds["S"], obs, generic, clusters, "u", rng)
            tests["H5_L_vs_K_r"] = compare(preds["L"], preds["K"], obs, generic, clusters, "r", rng)
            tests["H5_L_vs_O_r"] = compare(preds["L"], preds["O"], obs, generic, clusters, "r", rng)
            tests["S_vs_Sperm_r"] = compare(preds["S"], preds["Sperm"], obs, generic, clusters, "r", rng)
            tests["S_vs_O_r"] = compare(preds["S"], preds["O"], obs, generic, clusters, "r", rng)
            tests["H5_L_vs_K_top10"] = compare(preds["L"], preds["K"], obs, generic, clusters, "u", rng)
            tests["H5_L_vs_O_top10"] = compare(preds["L"], preds["O"], obs, generic, clusters, "u", rng)
            tests["B_vs_Z_top10"] = compare(preds["B"], preds["Z"], obs, generic, clusters, "u", rng)
            tests["gate_check_Roracle_vs_B_r"] = compare(preds["R_kernel" if primary == "S_kernel" else "R_bridge"], preds["B"], obs, generic, clusters, "r", rng)
            # D2 screening on two-plate 5 uM labels
            d2 = {}
            for j, f in enumerate(HELDOUT):
                frame = A.P.phenotype_frame(table, [f], ref.files)
                plates = {}
                for (ff, lab, pl), rec in frame.items():
                    if lab in labels5:
                        plates.setdefault(lab, []).append((pl, rec["survival"]))
                Aobs = np.full(len(labels5), np.nan)
                Bobs = np.full(len(labels5), np.nan)
                for i, l in enumerate(labels5):
                    if len(plates.get(l, [])) == 2:
                        (pa, va), (pb, vb) = sorted(plates[l])
                        Aobs[i], Bobs[i] = va - ref_mean[c5][i], vb - ref_mean[c5][i]
                d2[f] = {arm: screening(preds[arm][j], Aobs, Bobs, generic[j]) for arm in ("Z", "O", "B", "S", "SB")}
            summary["D2"] = d2
        else:
            tests["H4_Scells_vs_B_r"] = compare(preds["S_cells"], preds["B"], obs, generic, clusters, "r", rng)
            tests["Scells_vs_Z_r_note"] = "Z is constant; r undefined"
        summary["tests"] = tests
        results["lines"] = {f: names[f] for f in HELDOUT}
        endpoints[endpoint] = summary
        np.savez(Path(out_dir) / f"PREDICTIONS_{endpoint}.npz", obs=obs, generic=generic, labels=np.array(labels5), **preds)
    results["endpoints"] = endpoints
    results["seconds"] = round(time.perf_counter() - started, 1)
    (Path(out_dir) / "RESULTS.json").write_text(json.dumps(results, indent=1, default=float), encoding="utf-8")
    print(json.dumps({e: {k: (v["mean_difference"], v["ci95"], v["lines_better"], v["success"]) for k, v in s["tests"].items() if isinstance(v, dict)}
                      for e, s in endpoints.items()}, indent=1))


if __name__ == "__main__":
    main()
