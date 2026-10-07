"""Exploratory public dose-support correction; no production activation."""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import platform
import time
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

from research.astra.drylab_followup_20261007.reproduce import HERE, SOURCE, load_replay, preservation

ROOT = HERE.parents[2]
MONO = ROOT / "research/astra/mono_pretraining_20261005/results/mono_labels.csv.gz"
IDENTITY = ROOT / "research/astra/mono_pretraining_20261005/data_s0/drug_identity_map.csv"
DESIGN = ["log_library_top", "log_anchor_low", "log_anchor_high", "anchor_span", "log_seeding", "anchor_levels"]
QUALITY = [f"{role}_{name}" for role in ["anchor", "library"]
           for name in ["missing", "log_n", "range_transport", "tissue_transport"]]
FUNCTION = [f"{role}_{name}" for role in ["anchor", "library"]
            for name in ["dose_margin", "auc", "ic50_supported", "dose_supported", "log_range_span"]] + ["margin_product"]
ARMS = {"design_only": DESIGN, "missingness_only": DESIGN + QUALITY,
        "tier_a": DESIGN + QUALITY + FUNCTION, "tier_a_shuffled": DESIGN + QUALITY + FUNCTION}
GRID = [(0., 100.)] + [(a, l) for a in [.25, .5, 1.] for l in [100., 10., 1.]]


def dump(path, obj):
    path.write_text(json.dumps(obj, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def dose_vectors(identity, value):
    components = identity.split("|")
    vectors = [tuple(float(x) for x in part.split("|")) for part in value.split(";")]
    if any(len(x) != len(components) or any(not math.isfinite(v) or v <= 0 for v in x) for x in vectors):
        raise ValueError("invalid_component_dose_vector")
    return components, vectors


def reference_groups(mono):
    # Enforced before any response aggregation; exclusion flag includes related identities.
    history = mono.loc[~mono.cell_excluded_from_mono].copy()
    assert not set(history.sidm) & set(mono.loc[mono.cell_excluded_from_mono, "sidm"])
    history["tissue"] = history.cmp_tissue.replace({"Large Intestine": "Colon"})
    groups = {}
    for (drug, top), group in history.groupby(["drug_id", "max_conc"]):
        groups[(str(drug), float(top), "GLOBAL")] = group
        for tissue, cells in group.groupby("tissue"):
            groups[(str(drug), float(top), tissue)] = cells
    return groups, history


def support(groups, drug, tissue, dose, require_exact=False):
    tops = sorted({top for d, top, t in groups if d == drug and t == "GLOBAL"})
    if not tops:
        return None
    exact = [top for top in tops if np.isclose(top, dose, rtol=1e-8, atol=0)]
    if require_exact and not exact:
        return None
    top = exact[0] if exact else min(tops, key=lambda x: (abs(math.log(x / dose)), x))
    local = groups.get((drug, top, tissue))
    transported = local is None or local.sidm.nunique() < 5
    group = groups[(drug, top, "GLOBAL")] if transported else local
    if group.sidm.nunique() < 5:
        return None
    finite = group[np.isfinite(group.ln_ic50) & np.isfinite(group.auc)]
    if finite.sidm.nunique() < 5:
        return None
    per_cell = finite.groupby("sidm").agg(ln_ic50=("ln_ic50", "median"), auc=("auc", "median"),
                                          low=("min_conc", "min"), high=("max_conc", "max"))
    median = float(per_cell.ln_ic50.median())
    return {"missing": 0., "log_n": math.log1p(len(per_cell)),
            "range_transport": float(not bool(exact)), "tissue_transport": float(transported),
            "dose_margin": float(np.clip((math.log(dose) - median) / math.log(2), -12, 12)),
            "auc": float(per_cell.auc.median()),
            "ic50_supported": float(((per_cell.ln_ic50 >= np.log(per_cell.low)) &
                                      (per_cell.ln_ic50 <= np.log(per_cell.high))).mean()),
            "dose_supported": float(((dose >= per_cell.low) & (dose <= per_cell.high)).mean()),
            "log_range_span": float(np.log2(per_cell.high / per_cell.low).median()),
            "reference_top_uM": top, "n_reference_cells": len(per_cell),
            "reference_tissue": "GLOBAL" if transported else tissue}


def build_features(menu, mono, identity):
    groups, history = reference_groups(mono)
    assert not set(menu.SIDM) & set(history.sidm), "target_mono_not_excluded"
    mapped = set(identity.loc[identity.status.eq("mapped"), "jaaks_id"].astype(str))
    cache, rows = {}, []
    for row in menu.itertuples(index=False):
        components, vectors = dose_vectors(row.ANCHOR_ID, str(row.anchor_set))
        # Source composite-library top is one scalar; do not invent component doses.
        lib_components = row.LIBRARY_ID.split("|")
        low, high = min(x[0] for x in vectors), max(x[0] for x in vectors)
        library_top = float(row.LIBRARY_CONC)
        if not math.isfinite(library_top) or library_top <= 0:
            raise ValueError("invalid_library_curve_top")
        record = {"log_library_top": math.log2(library_top), "log_anchor_low": math.log2(low),
                  "log_anchor_high": math.log2(high), "anchor_span": math.log2(high / low),
                  "log_seeding": math.log2(float(row.SEEDING_DENSITY)), "anchor_levels": len(vectors)}
        compatible = len(components) == len(lib_components) == 1
        for role, drug, dose in [("anchor", row.ANCHOR_ID, high), ("library", row.LIBRARY_ID, library_top)]:
            key = (drug, row.Tissue, dose, role, compatible)
            if key not in cache:
                cache[key] = support(groups, drug, row.Tissue, dose, role == "library") if drug in mapped and compatible else None
            values = cache[key]
            for name in ["missing", "log_n", "range_transport", "tissue_transport", "dose_margin", "auc",
                         "ic50_supported", "dose_supported", "log_range_span"]:
                record[f"{role}_{name}"] = values[name] if values else (1. if name == "missing" else np.nan)
            for name in ["reference_top_uM", "n_reference_cells", "reference_tissue"]:
                record[f"{role}_{name}"] = values[name] if values else None
        record["eligible"] = compatible and not bool(record["anchor_missing"] or record["library_missing"])
        record["margin_product"] = record["anchor_dose_margin"] * record["library_dose_margin"]
        record["composite"] = not compatible
        rows.append(record)
    features = pd.DataFrame(rows, index=menu.index)
    meta = {"source_rows": len(mono), "reference_rows": len(history),
            "reference_cells": int(history.sidm.nunique()), "excluded_cells": int(mono.loc[mono.cell_excluded_from_mono, "sidm"].nunique()),
            "target_own_mono_excluded": True, "eligible_rows": int(features.eligible.sum()),
            "fallback_rows": int((~features.eligible).sum()), "composite_rows": int(features.composite.sum()),
            "unresolved_composite_library_doses": int(menu.LIBRARY_ID.str.contains("|", regex=False).sum()),
            "functional_fields_not_released": ["slope", "Emax"],
            "shared_nlme_fit_not_refit": True,
            "licence_notice": "Sanger internal research/education; no resale/commercial services without consent. https://depmap.sanger.ac.uk/documentation/data-usage-policy/"}
    return features, meta


def shuffled_features(menu, features):
    result = features.copy()
    rng = np.random.default_rng(20261007)
    moved = 0
    keys = menu[["Tissue", "LIBRARY_CONC", "anchor_set"]].copy()
    keys["eligible"] = features.eligible
    for _, indices in keys.groupby(list(keys.columns)).groups.items():
        ids = np.asarray(list(indices))
        if len(ids) > 1 and bool(features.loc[ids[0], "eligible"]):
            perm = rng.permutation(ids)
            result.loc[ids, FUNCTION] = features.loc[perm, FUNCTION].to_numpy()
            moved += int((ids != perm).sum())
    return result, moved


def ridge_scores(train, test, features, columns, lam, label):
    fit = features.loc[train].eligible.to_numpy(bool)
    ids = np.asarray(train)[fit]
    if not len(ids):
        return np.zeros(len(test))
    X = features.loc[ids, columns].to_numpy(float)
    keys = label.loc[ids, ["SIDM", "role"]]
    sizes = keys.groupby(["SIDM", "role"]).SIDM.transform("size").to_numpy()
    weight = 1. / sizes
    weight /= weight.sum()
    # Weighted training-only fill and scaling. No target statistics or labels.
    valid = np.isfinite(X)
    center = np.sum(np.where(valid, X, 0) * weight[:, None], axis=0) / np.maximum(np.sum(valid * weight[:, None], axis=0), 1e-12)
    X = np.where(valid, X, center)
    scale = np.sqrt(np.sum((X - center) ** 2 * weight[:, None], axis=0))
    scale[scale < 1e-8] = 1.
    X = (X - center) / scale
    y = (label.loc[ids, "joint"].to_numpy(float) - label.loc[ids, "prior_control_score"].to_numpy(float))
    beta = np.linalg.solve(X.T @ (weight[:, None] * X) + lam * np.eye(len(columns)), X.T @ (weight * y))
    Z = features.loc[test, columns].to_numpy(float)
    Z = (np.where(np.isfinite(Z), Z, center) - center) / scale
    delta = Z @ beta
    delta[~features.loc[test].eligible.to_numpy(bool)] = 0.
    return delta


def evaluate(replay, truth, scores):
    menu = truth[replay.PUBLIC].copy()
    lab = replay.ReplayLab(truth.reset_index(drop=True), 2)
    lab.screen(replay.ordering(menu, scores)[:math.floor(.7 * lab.budget)].tolist())
    # Confirmation order is fixed even when screening is corrected.
    return replay.finish(lab, menu, menu.prior_control_score)


def select(replay, train, labels, features, columns):
    cells = sorted(labels.loc[train].SIDM.unique())
    totals = {z: 0 for z in GRID}
    for heldout in cells:
        is_validation = labels.loc[train, "SIDM"].eq(heldout).to_numpy()
        validation = np.asarray(train)[is_validation]
        fit = np.asarray(train)[~is_validation]
        for lam in [100., 10., 1.]:
            delta = pd.Series(ridge_scores(fit, validation, features, columns, lam, labels), index=validation)
            for _, g in labels.loc[validation].groupby("role"):
                base = g.prior_control_score.to_numpy(float)
                for alpha in [0., .25, .5, 1.]:
                    if alpha == 0. and lam != 100.:
                        continue
                    totals[(alpha, lam)] += evaluate(replay, g, base + alpha * delta.loc[g.index].to_numpy())["confirmations"]
    best = max(GRID, key=lambda z: totals[z])
    return best, totals[best], cells


def dependence_summary(records, swaps):
    totals = pd.DataFrame(records)
    b = totals[totals.arm.eq("frozen_static")].set_index(["SIDM", "role"])
    out = {}
    for arm in ARMS:
        x = totals[totals.arm.eq(arm)].set_index(["SIDM", "role"])
        delta = (x.confirmations - b.confirmations).groupby("SIDM").sum()
        rng = np.random.default_rng(20261007)
        boot = delta.to_numpy()[rng.integers(len(delta), size=(2000, len(delta)))].sum(axis=1)
        entries = pd.DataFrame([z for z in swaps if z["arm"] == arm])
        pair_ci = [0., 0.]
        if len(entries):
            pivot = entries.pivot_table(index="SIDM", columns="unordered_pair", values="joint_contribution", aggfunc="sum", fill_value=0)
            a = pivot.to_numpy(float)
            # Independent multinomial resampling weights for crossed cell and pair units.
            cw = rng.multinomial(len(pivot), np.ones(len(pivot)) / len(pivot), size=2000)
            pw = rng.multinomial(len(pivot.columns), np.ones(len(pivot.columns)) / len(pivot.columns), size=2000)
            cross = np.einsum("bi,ij,bj->b", cw, a, pw)
            pair_ci = np.quantile(cross, [.025, .975]).tolist()
        out[arm] = {"confirmation_delta": int(delta.sum()), "cell_bootstrap_delta_ci95": np.quantile(boot, [.025, .975]).tolist(),
                    "crossed_cell_pair_boundary_delta_ci95": pair_ci,
                    "crossed_interval_scope": "Changed-screen joint-label contributions only, not complete confirmation policy refits",
                    "swapped_in": int(sum(z["direction"] == "in" for z in swaps if z["arm"] == arm)),
                    "net_joint_boundary_contribution": int(sum(z["joint_contribution"] for z in swaps if z["arm"] == arm))}
    return out


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "results")
    args = parser.parse_args()
    args.output.mkdir(exist_ok=False)
    start = time.perf_counter()
    preservation()
    freeze = json.loads((HERE / "PROTOCOL_FREEZE.json").read_text())
    assert digest(HERE / "PROTOCOL.json") == freeze["sha256"]
    replay = load_replay()
    full, _, menu = replay.load_data()
    # Feature builder only receives allowlisted design columns and external reference.
    mono = pd.read_csv(MONO, dtype={"sidm": str, "drug_id": str})
    identity = pd.read_csv(IDENTITY, dtype={"jaaks_id": str})
    features, qualification = build_features(menu, mono, identity)
    shuffled, moved = shuffled_features(menu, features)
    qualification["shuffle_rows_reassigned"] = moved
    joined = pd.concat([menu[replay.KEY + ["role", "pair"]], features], axis=1)
    joined.to_csv(args.output / "public_features.csv.gz", index=False)
    audit = identity[identity.jaaks_id.isin(pd.read_csv(SOURCE / "data/drug.csv", dtype=str).drug_id)]
    audit.to_csv(args.output / "drug_qualification.csv", index=False)
    qualification["drug_identities"] = len(audit)
    qualification["mapped_drug_identities"] = int(audit.status.eq("mapped").sum())
    qualification["coverage_by_tissue"] = joined.groupby("Tissue").eligible.agg(["sum", "count"]).reset_index().to_dict("records")
    labels = full.copy()
    labels["joint"] = labels.hit1 & labels.hit2
    results, choices, swaps, traces = [], [], [], []
    with threadpool_limits(limits=1):
        for cell in sorted(labels.SIDM.unique()):
            train = labels.index[labels.SIDM.ne(cell)].to_numpy()
            test = labels.index[labels.SIDM.eq(cell)].to_numpy()
            scores = {"frozen_static": labels.loc[test, "prior_control_score"].to_numpy(float)}
            for arm, cols in ARMS.items():
                F = shuffled if arm == "tier_a_shuffled" else features
                (alpha, lam), quality, history = select(replay, train, labels, F, cols)
                assert cell not in history
                choices.append({"heldout_cell": cell, "arm": arm, "alpha": alpha, "lambda": lam,
                                "inner_confirmations": quality, "training_cells": history})
                scores[arm] = scores["frozen_static"] + alpha * ridge_scores(train, test, F, cols, lam, labels)
            scores = {a: pd.Series(v, index=test) for a, v in scores.items()}
            for role, g in labels.loc[test].groupby("role"):
                outputs = {a: evaluate(replay, g, v.loc[g.index].to_numpy()) for a, v in scores.items()}
                base_ids = set(outputs["frozen_static"]["screen_ids"])
                for arm, res in outputs.items():
                    results.append({"SIDM": cell, "role": role, "arm": arm,
                                    **{k: v for k, v in res.items() if k not in ["screen_ids", "confirmed_ids", "trace"]},
                                    "covered_confirmations": int(features.loc[g.iloc[res["confirmed_ids"]].index, "eligible"].sum())})
                    traces.extend(dict(SIDM=cell, role=role, arm=arm, **z) for z in res["trace"])
                    selected = set(res["screen_ids"])
                    for direction, ids in [("in", selected - base_ids), ("out", base_ids - selected)]:
                        for i in sorted(ids):
                            row = g.iloc[i]
                            unordered = "::".join(sorted([row.ANCHOR_ID, row.LIBRARY_ID]))
                            swaps.append({"SIDM": cell, "role": role, "arm": arm, "direction": direction,
                                          "pair": row.pair, "unordered_pair": unordered,
                                          **{k: getattr(row, k) for k in replay.KEY if k not in ["SIDM"]},
                                          "joint_contribution": int(row.joint) * (1 if direction == "in" else -1),
                                          "confirmed_by_policy": i in res["confirmed_ids"], "eligible": bool(features.loc[g.index[i], "eligible"])})
    frame = pd.DataFrame(results)
    frame.to_csv(args.output / "campaigns.csv", index=False)
    summary = frame.groupby("arm")[["confirmations", "spent", "budget", "unused", "screened", "verified", "covered_confirmations"]].sum()
    summary.to_csv(args.output / "summary.csv")
    pd.DataFrame(choices).to_json(args.output / "fold_choices.json", orient="records", indent=2)
    pd.DataFrame(swaps).to_csv(args.output / "boundary_swaps.csv", index=False)
    with (args.output / "purchase_traces.jsonl").open("w", encoding="utf-8") as stream:
        for trace in traces:
            stream.write(json.dumps(trace, allow_nan=False) + "\n")
    dump(args.output / "qualification.json", qualification)
    dump(args.output / "contrasts.json", dependence_summary(results, swaps))
    assert summary.loc["frozen_static", "confirmations"] == 92
    assert summary.loc["frozen_static", "spent"] == 762
    assert frame.budget.sum() == 915 * 5
    preservation()
    dump(args.output / "manifest.json", {"status": "Exploratory only; no production promotion",
         "protocol_sha256": freeze["sha256"], "script_sha256": digest(Path(__file__)),
         "sources": {str(p.relative_to(ROOT)): digest(p) for p in [MONO, IDENTITY, SOURCE / "data/predictions.csv.gz"]},
         "python": platform.python_version(), "wall_seconds": time.perf_counter() - start,
         "network_calls": 0, "llm_calls": 0, "gpu_training": False})
    print(summary.to_string())


if __name__ == "__main__":
    main()
