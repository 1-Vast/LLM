"""Bounded, compound-held-out replay of measured LINCS population transitions.

Run in maestro: python research/acquisition_followup/lincs_flow.py
The protocol is saved before expression arrays are opened. This research-only
analysis does not change acquisition defaults or turn predictions into evidence.
"""
from __future__ import annotations

import hashlib
import json
import platform
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/external/lincs_l1000_phase1"
OUT = ROOT / "outputs/acquisition_followup/lincs"
SEED = 20260926


def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def write(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2, allow_nan=False), encoding="utf-8")


def key(value):
    return hashlib.sha256(f"{SEED}:{value}".encode()).hexdigest()


def annotation_map(pert):
    samples = pd.read_csv(ROOT / "data/raw/sciplex3/repurposing_samples_20200324.txt",
                          sep="\t", comment="!").fillna("")
    drugs = pd.read_csv(ROOT / "data/raw/sciplex3/repurposing_drugs_20200324.txt",
                        sep="\t", comment="!").fillna("")
    by_id, by_inchi = defaultdict(set), defaultdict(set)
    for row in samples.itertuples(index=False):
        by_id[str(row.broad_id).split("-", 2)[0] + "-" + str(row.broad_id).split("-")[1]].add(row.pert_iname)
        if row.InChIKey:
            by_inchi[row.InChIKey].add(row.pert_iname)
    by_name = {name: group for name, group in drugs.groupby("pert_iname")}
    result = {}
    for row in pert.itertuples(index=False):
        names, route = by_id.get(row.pert_id, set()), "exact_Broad_compound_ID"
        if not names:
            names, route = by_inchi.get(row.inchi_key, set()), "exact_full_InChIKey"
        records = [by_name[name] for name in names if name in by_name]
        moas = sorted({str(x) for frame in records for x in frame.moa if str(x)})
        targets = sorted({str(x) for frame in records for x in frame.target if str(x)})
        result[row.pert_id] = {"name": row.pert_iname, "annotation_route": route if records else None,
                               "moa": moas, "targets": targets,
                               "annotation_scope": "external compound annotation, not measured mechanism evidence"}
    return result


def cosine_rows(a, b):
    return np.sum(a * b, axis=1) / np.maximum(np.linalg.norm(a, axis=1) * np.linalg.norm(b, axis=1), 1e-12)


def interval(values, groups):
    means = np.array([np.mean(values[groups == group]) for group in np.unique(groups)])
    rng = np.random.default_rng(SEED)
    boots = means[rng.integers(0, len(means), (2000, len(means)))].mean(axis=1)
    return {"mean": float(means.mean()), "ci95": np.quantile(boots, [.025, .975]).tolist()}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    protocol = {
        "study": "independent-platform, retrospective population-transition diagnostic",
        "seed": SEED, "cell_line": "A549", "dose_um": 10.0, "source_h": 6.0, "target_h": 24.0,
        "selection": "metadata-only QC: >=2 wells and >=2 plates at each time; first 1200 identity groups by SHA256(seed:group)",
        "identity_group": "exact full LINCS InChIKey; fall back to pert_id when absent",
        "split": "SHA256(seed:group) integer modulo 5 == 0 is test; all other groups train",
        "feature_qc": "all 978 cached IDs must be measured landmark genes; finite means/variances; nonnegative variances",
        "models": ["persistence", "training_target_mean", "global_scaled_persistence", "ridge_residual", "ridge_shuffled_test_source"],
        "ridge": "train-only standardized 6h input; centered 24h-minus-6h target; L2 penalty = number of training conditions; intercept unpenalized",
        "shuffle": "seeded permutation of held-out 6h source rows, with fixed fitted model and untouched 24h target rows",
        "metrics": ["per-profile landmark MSE", "profile cosine", "R2 against zero target profile"],
        "uncertainty": "2000 paired bootstrap resamples of test compound identity groups, percentile 95% intervals",
        "annotation": "Broad compound ID from sample ID prefix, else full InChIKey; exact sample name to drug record; no fuzzy join",
        "trace_selection": "first five test identity groups in frozen hash order; no selection on outcome",
        "promotion": "none; diagnostic only; no acquisition or biological mechanism efficacy claim",
    }
    protocol_path = OUT / "protocol.json"
    if protocol_path.exists():
        existing = json.loads(protocol_path.read_text(encoding="utf-8"))
        if existing["protocol"] != protocol:
            raise RuntimeError("Existing frozen protocol differs; use a separately named study.")
    else:
        write("protocol.json", {"frozen_at_utc": datetime.now(timezone.utc).isoformat(),
                                 "script_sha256": digest(Path(__file__)), "protocol": protocol})
    print("Protocol frozen:", digest(protocol_path), flush=True)

    conditions = json.loads((DATA / "subset48/conditions.json").read_text())
    pert_path = DATA / "GSE92742_Broad_LINCS_pert_info.txt.gz"
    pert = pd.read_csv(pert_path, sep="\t", dtype=str).fillna("")
    inchi = dict(zip(pert.pert_id, pert.inchi_key))
    grouped = defaultdict(dict)
    for i, row in enumerate(conditions):
        if row["cell_id"] == "A549" and row["dose_um"] == 10.0:
            time = float(row["time_h"])
            if time in (6.0, 24.0):
                if time in grouped[row["pert_id"]]:
                    raise ValueError("Duplicate exact condition")
                grouped[row["pert_id"]][time] = i
    candidates = []
    for pid, pair in grouped.items():
        if set(pair) != {6.0, 24.0}:
            continue
        if any(conditions[i]["n_wells"] < 2 or conditions[i]["n_plates"] < 2 for i in pair.values()):
            continue
        chemical = inchi.get(pid, "")
        group = chemical if chemical not in ("", "-666") else pid
        candidates.append((group, pid, pair[6.0], pair[24.0]))
    chosen = set(sorted({r[0] for r in candidates}, key=key)[:1200])
    selected = sorted([r for r in candidates if r[0] in chosen], key=lambda r: (key(r[0]), r[1]))
    indices = np.array([[r[2], r[3]] for r in selected])
    arrays = np.load(DATA / "subset48/conditions.npz", allow_pickle=False)
    genes = arrays["gene_id"].astype(str)
    gene_table = pd.read_csv(DATA / "GSE92742_Broad_LINCS_gene_info.txt.gz", sep="\t", dtype=str)
    landmarks = set(gene_table.loc[gene_table.pr_is_lm == "1", "pr_gene_id"])
    if len(genes) != 978 or len(set(genes)) != 978 or not set(genes).issubset(landmarks):
        raise ValueError("Cached feature identities are not 978 distinct measured landmarks")
    symbols = gene_table.set_index("pr_gene_id").pr_gene_symbol.loc[genes].tolist()
    mean = arrays["mean"][indices].astype(np.float64)
    variance = arrays["var"][indices]
    valid = np.isfinite(mean).all(axis=(1, 2)) & np.isfinite(variance).all(axis=(1, 2)) & (variance >= 0).all(axis=(1, 2))
    selected = [row for row, ok in zip(selected, valid) if ok]
    x, y = mean[valid, 0], mean[valid, 1]
    groups = np.array([row[0] for row in selected])
    test = np.array([int(key(group), 16) % 5 == 0 for group in groups])
    train = ~test
    assert not set(groups[train]) & set(groups[test])
    assert train.sum() >= 20 and test.sum() >= 20
    print(f"Scoring {train.sum()} training and {test.sum()} held-out conditions", flush=True)
    xmean, scale = x[train].mean(axis=0), x[train].std(axis=0)
    scale = np.maximum(scale, 1e-8)
    z = (x[train] - xmean) / scale
    delta = y[train] - x[train]
    intercept = delta.mean(axis=0)
    with threadpool_limits(limits=4):
        weight = np.linalg.solve(z.T @ z + train.sum() * np.eye(len(genes)), z.T @ (delta - intercept))
        def predict(source):
            return source + intercept + ((source - xmean) / scale) @ weight
        ridge = predict(x[test])
        shuffled = predict(x[test][np.random.default_rng(SEED).permutation(test.sum())])
    scalar = float(np.sum(x[train] * y[train]) / np.sum(x[train] ** 2))
    predictions = {"persistence": x[test], "training_target_mean": np.broadcast_to(y[train].mean(axis=0), y[test].shape),
                   "global_scaled_persistence": scalar * x[test], "ridge_residual": ridge,
                   "ridge_shuffled_test_source": shuffled}
    per_model, metrics = {}, {}
    for name, predicted in predictions.items():
        values = {"mse": np.mean((predicted - y[test]) ** 2, axis=1),
                  "cosine": cosine_rows(predicted, y[test]),
                  "r2_vs_zero": 1 - np.sum((predicted - y[test]) ** 2, axis=1) / np.maximum(np.sum(y[test] ** 2, axis=1), 1e-12)}
        per_model[name] = values
        metrics[name] = {metric: interval(value, groups[test]) for metric, value in values.items()}
    contrasts = {baseline: {"mse_improvement_ridge": interval(per_model[baseline]["mse"] - per_model["ridge_residual"]["mse"], groups[test]),
                            "cosine_improvement_ridge": interval(per_model["ridge_residual"]["cosine"] - per_model[baseline]["cosine"], groups[test])}
                 for baseline in predictions if baseline != "ridge_residual"}
    annotations = annotation_map(pert)
    joined = [annotations.get(row[1], {}) for row in selected]
    coverage = {"selected_compound_ids": len(selected), "matched_annotation_records": sum(bool(a.get("annotation_route")) for a in joined),
                "nonempty_moa": sum(bool(a.get("moa")) for a in joined), "ambiguous_multiple_moa_records": sum(len(a.get("moa", [])) > 1 for a in joined),
                "routes": dict(Counter(a.get("annotation_route") or "unmatched" for a in joined))}
    test_rows = [row for row, is_test in zip(selected, test) if is_test]
    traces, seen = [], set()
    for i, (group, pid, source, target) in enumerate(test_rows):
        if group in seen:
            continue
        seen.add(group)
        observed_delta = y[test][i] - x[test][i]
        top = np.argsort(-np.abs(observed_delta))[:8]
        traces.append({"pert_id": pid, "identity_group": group, "annotation": annotations.get(pid, {}),
                       "source": {"status": "measured", **conditions[source], "rna_norm": float(np.linalg.norm(x[test][i]))},
                       "forecast": {"status": "predicted", "model": "ridge_residual", "target_h": 24, "evidence_kind": "model_prediction", "planning_only": True},
                       "target": {"status": "measured", **conditions[target], "rna_norm": float(np.linalg.norm(y[test][i]))},
                       "largest_measured_changes": [{"gene_id": genes[j], "symbol": symbols[j], "source": float(x[test][i, j]),
                                                       "target": float(y[test][i, j]), "prediction": float(ridge[i, j]),
                                                       "population_change_per_hour": float(observed_delta[j] / 18)} for j in top],
                       "paired_by": "compound, cell line and dose; different endpoint populations, not single cells"})
        if len(traces) == 5:
            break
    write("flow_traces.json", traces)
    files = [Path(__file__), protocol_path, DATA / "subset48/conditions.json", DATA / "subset48/conditions.npz",
             DATA / "subset48/scale_receipt.json", DATA / "subset48/control_audit.json", pert_path,
             DATA / "GSE92742_Broad_LINCS_gene_info.txt.gz", ROOT / "data/raw/sciplex3/repurposing_samples_20200324.txt",
             ROOT / "data/raw/sciplex3/repurposing_drugs_20200324.txt"]
    provenance = {str(path.relative_to(ROOT)): {"sha256": digest(path), "bytes": path.stat().st_size} for path in files}
    summary = {"protocol_sha256": digest(protocol_path), "scored_at_utc": datetime.now(timezone.utc).isoformat(),
               "environment": {"python": sys.version, "executable": sys.executable, "platform": platform.platform(), "numpy": np.__version__, "pandas": pd.__version__},
               "source": "GSE92742 local subset48 derived condition cache; public LINCS L1000 measured landmarks",
               "normalization": json.loads((DATA / "subset48/scale_receipt.json").read_text()),
               "counts": {"eligible_conditions_before_cap": len(candidates), "selected_conditions": len(selected), "nonfinite_or_negative_variance_rejected": int((~valid).sum()),
                          "train_conditions": int(train.sum()), "test_conditions": int(test.sum()), "train_identity_groups": len(set(groups[train])), "test_identity_groups": len(set(groups[test])),
                          "identity_overlap": 0, "landmark_genes": len(genes)},
               "annotation_coverage": coverage, "fitted_global_scale": scalar, "metrics": metrics, "paired_contrasts": contrasts,
               "population_dynamics": {"source_target_cosine": interval(cosine_rows(x[test], y[test]), groups[test]),
                                       "change_rms_per_hour": interval(np.sqrt(np.mean((y[test] - x[test]) ** 2, axis=1)) / 18, groups[test])},
               "limitations": ["Two separate population endpoints, not single-cell trajectories or a continuous dynamical mechanism.",
                                "A549 at 10 uM only; no unseen-context, dose-transfer or mechanism-decision claim.",
                                "Cached plate-normalized expression; original preprocessing runner is unavailable, so provenance binds the supplied cache, not a newly reconstructed raw pipeline.",
                                "Metadata replicate QC and finite-value QC do not establish detection or target engagement.",
                                "Annotations are external compound labels, not biological evidence of engagement in these cells.",
                                "One frozen compound holdout and fixed hyperparameters; performance is diagnostic and does not promote a selector.",
                                "Compound bootstrap does not model dependence from shared assay plates; intervals are conditional on these measured plates."],
               "provenance": provenance}
    write("summary.json", summary)
    split = [{"pert_id": row[1], "identity_group": row[0], "source_row": row[2], "target_row": row[3], "split": "test" if hold else "train"} for row, hold in zip(selected, test)]
    write("split.json", split)
    records = [{"pert_id": row[1], "identity_group": row[0], **{f"{arm}:{metric}": float(values[i]) for arm, measures in per_model.items() for metric, values in measures.items()}} for i, row in enumerate(test_rows)]
    write("per_compound.json", records)
    report = ["# LINCS measured population-flow diagnostic", "", f"Frozen protocol: `{summary['protocol_sha256']}`.",
              f"A549, 10 uM, 6 h to 24 h; {train.sum()} training and {test.sum()} held-out conditions, 978 measured landmark genes, no identity-group overlap.", "",
              "The agent can use a measured early population state to request a forecast of a later measurement. Forecasts remain planning inputs; only the later actual measurement can be evidence.", "",
              "| Model | MSE (95% compound CI) | Cosine (95% compound CI) |", "|---|---:|---:|"]
    for arm, values in metrics.items():
        report.append("| " + arm + " | " + " | ".join(f"{values[m]['mean']:.4f} [{values[m]['ci95'][0]:.4f}, {values[m]['ci95'][1]:.4f}]" for m in ("mse", "cosine")) + " |")
    report.extend(["", "Positive paired improvements favor the learned transition:", ""])
    for baseline, values in contrasts.items():
        v = values["mse_improvement_ridge"]
        report.append(f"- Against {baseline}: MSE improvement {v['mean']:.4f} [{v['ci95'][0]:.4f}, {v['ci95'][1]:.4f}].")
    report.extend(["", f"Exact local Repurposing Hub join: {coverage['matched_annotation_records']}/{len(selected)} compound IDs; {coverage['nonempty_moa']} have nonempty mechanism annotations. No mechanism classifier or elimination rule is evaluated.", "",
                   "`flow_traces.json` contains five predetermined held-out flows, source/target replicate and plate provenance, forecast status and gene-level measured changes. `split.json` and `per_compound.json` support reproduction.", "", "Limits:", ""])
    report.extend("- " + item for item in summary["limitations"])
    (OUT / "report.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(json.dumps({"counts": summary["counts"], "annotation_coverage": coverage, "paired_contrasts": contrasts}, indent=2), flush=True)


if __name__ == "__main__":
    main()
