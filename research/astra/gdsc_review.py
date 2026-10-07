"""Independent, post-outcome audit of the pinned GDSC research branch.

No policy fitting, outcome clipping, subgroup selection or causal effect estimation.
The source branch is inspected in a separate snapshot; main is not merged.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

import numpy as np
import pandas as pd
from scipy.stats import t


COMMIT = "15fec7c53c5334ceca96832e8342ae2ebc1fde75"
ACTIONS = ["gdsc:1032:2uM", "gdsc:1036:10uM", "gdsc:1060:0.25uM"]
COMPARISONS = [("CS", "C", .025), ("CS", "fixed", .025), ("C", "fixed", .05), ("CS", "shuffle", .05)]


def sha(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def supplied_report_paths(root=Path(".")):
    """Use existing original input bytes when a duplicate narrative was retired."""
    directory = root / "research/astra"
    evidence = directory / "evidence/20261002_gdsc_inputs"
    receipt = None
    paths = []
    for name in ("GDSC_SCREEN.md", "MAESTRO_GDSC_RESEARCH_REPORT.md", "MAESTRO_GDSC_RESEARCH_REPORT.docx"):
        original = directory / name
        if original.is_file():
            paths.append(original)
            continue
        retained = evidence / (name + ".txt" if name.endswith(".md") else name)
        if not retained.is_file():
            raise ValueError(f"Retired GDSC source input {name}; restore registered original bytes from the source receipt.")
        if receipt is None:
            receipt = json.loads((evidence / "receipt.json").read_text(encoding="utf-8"))
        if sha(retained) != receipt[name]["sha256"]:
            raise ValueError(f"Registered GDSC source input changed: {name}")
        paths.append(retained)
    return paths


def save(path, payload):
    Path(path).write_text(json.dumps(payload, indent=2, allow_nan=False) + "\n", encoding="utf-8")


def unit_weights(frame):
    return 1. / frame.groupby("unit")["unit"].transform("size").to_numpy() / frame.unit.nunique()


def crossed_mean(frame, values, alpha):
    """Recalculate the reported fixed-policy interval, not assert coverage."""
    values = np.asarray(values, dtype=float)
    if len(values) != len(frame) or not np.isfinite(values).all():
        raise ValueError("complete finite paired observations required")
    w = unit_weights(frame)
    avg = float(w @ values)
    scores = pd.DataFrame({"unit": frame.unit.to_numpy(), "date": frame.date_cluster.to_numpy(),
                           "score": w * (values - avg)})
    variances = []
    for keys in (["unit"], ["date"], ["unit", "date"]):
        sums = scores.groupby(keys)["score"].sum().to_numpy()
        if len(sums) < 2:
            return dict(mean=avg, ci=None, reason="insufficient clusters")
        variances.append(float(len(sums) / (len(sums) - 1) * (sums @ sums)))
    vu, vd, vi = variances
    two = max(0., vu + vd - vi)
    se = float(np.sqrt(max(vu, vd, two)))
    df = min(frame.unit.nunique(), frame.date_cluster.nunique()) - 1
    half = float(t.ppf(1 - alpha / 2, df) * se)
    return dict(mean=avg, ci=[avg - half, avg + half], se=se, df=int(df),
                variance_patient=vu, variance_date=vd, variance_intersection=vi,
                variance_two_way=two, coverage="approximate conditional on original assumptions; not newly validated")


def contribution_table(frame):
    result = frame[["BARCODE", "unit", "date_cluster", "tissue", "growth", "medium", "log2_density"]].copy()
    result["unit_weight"] = unit_weights(frame)
    for arm in ("fixed", "C", "CS", "shuffle"):
        result[arm + "_action"] = frame[arm + "_action"].to_numpy()
        result[arm + "_utility"] = frame[arm + "_observed_utility"].to_numpy()
    for a, b, _ in COMPARISONS:
        delta = frame[a + "_observed_utility"].to_numpy() - frame[b + "_observed_utility"].to_numpy()
        result[a + "-" + b] = delta
        result[a + "-" + b + "_weighted_contribution"] = delta * result.unit_weight
        result[a + "-" + b + "_switched"] = frame[a + "_action"].to_numpy() != frame[b + "_action"].to_numpy()
        if np.any(delta[~result[a + "-" + b + "_switched"]] != 0):
            raise ValueError("unchanged action cannot change observed utility")
    return result


def grouped_contributions(table, field):
    rows = []
    for label, group in table.groupby(field, dropna=False, sort=True):
        record = dict(group=str(label), plates=len(group), units=group.unit.nunique(), weight=float(group.unit_weight.sum()))
        for a, b, _ in COMPARISONS:
            record[a + "-" + b + "_contribution_pp"] = float(group[a + "-" + b + "_weighted_contribution"].sum() * 100)
        rows.append(record)
    return rows


def run(snapshot, out, dependency_dir=None):
    start = time.perf_counter()
    out = out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    snapshot = snapshot.resolve()
    if dependency_dir:
        sys.path.insert(0, str(dependency_dir.resolve()))
    snapshot_receipt = json.loads((snapshot / "snapshot_manifest.json").read_text())
    if snapshot_receipt["commit"] != COMMIT:
        raise ValueError("fixed source commit required")
    for name, expected in snapshot_receipt["paths"].items():
        if sha(snapshot / name) != expected:
            raise ValueError(f"snapshot changed: {name}")
    astra = snapshot / "research/astra"
    results = astra / "results"
    sources = astra / "data/gdsc_screen_v1"
    freeze = results / "20261002_gdsc_freeze_v1"
    dev = results / "20261002_gdsc_development_v1"
    confirm = results / "20261002_gdsc_confirmation_v1"
    supplied = supplied_report_paths()
    input_hashes = {str(p.resolve()): sha(p) for p in supplied + [Path(__file__), snapshot / "snapshot_manifest.json"]}
    save(out / "freeze.json", dict(at_utc=datetime.now(timezone.utc).isoformat(), source_commit=COMMIT,
         inputs=input_hashes, snapshot_files=snapshot_receipt["paths"], analysis="post-outcome independent reproduction and finite sensitivity",
         diagnostics=["native source rows and normalization", "split and metadata", "reported intervals", "all-unit contributions",
                      "all date omissions", "denominator/control quality", "background annotation provenance"],
         no_refit=True, no_threshold_change=True, no_outcome_clipping=True, no_physical_experiment=True,
         uncertainty="original crossed-cluster calculation only; omissions descriptive; no new bootstrap coverage claim"))
    (out / "execution_source.py.txt").write_bytes(Path(__file__).read_bytes())
    spec = importlib.util.spec_from_file_location("pinned_gdsc_screen", astra / "gdsc_screen.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    error = None
    try:
        for directory in (freeze, dev, confirm):
            module.verify_manifest(directory)
        source_receipts = json.loads((sources / "SOURCES.json").read_text())
        for name, record in source_receipts["files"].items():
            if sha(sources / name) != record["sha256"]:
                raise ValueError("raw/annotation file changed")
        raw = module.read_raw(sources / "gdsc_example.rda")
        metadata = module.metadata(raw, sources / "Cell_Lines_Details.xlsx", sources / "model_list_latest.csv.gz")
        split, cutoff = module.assign_split(metadata)
        expected_split = pd.read_csv(freeze / "split.csv", dtype={"BARCODE": str})
        if split.BARCODE.tolist() != expected_split.BARCODE.tolist() or split.split.tolist() != expected_split.split.tolist():
            raise ValueError("split does not reproduce from source metadata")
        for key in ("unit", "tissue", "growth", "medium"):
            if split[key].fillna("missing").tolist() != expected_split[key].fillna("missing").tolist():
                raise ValueError(f"metadata discrepancy: {key}")
        reproduced = []
        for label, folder in (("development", dev), ("confirmation", confirm)):
            panel, observations, qc = module.normalize_panel(raw, split.loc[split.split == label].copy())
            expected = pd.read_csv(folder / (label + "_observations.csv"), dtype={"BARCODE": str})
            expected = expected.sort_values(["BARCODE", "action"]).reset_index(drop=True)
            actual = observations.sort_values(["BARCODE", "action"]).reset_index(drop=True)
            for key in ("BARCODE", "action", "source_row", "SCAN_ID", "POSITION"):
                if actual[key].tolist() != expected[key].tolist():
                    raise ValueError(f"native identity mismatch: {label}:{key}")
            maximum = float(np.max(np.abs(actual.utility.to_numpy() - expected.utility.to_numpy())))
            if maximum > 1e-12:
                raise ValueError("native normalization mismatch")
            reproduced.append(dict(split=label, plates=len(panel), action_rows=len(actual), max_utility_difference=maximum))
        policy = pd.read_csv(confirm / "policy_evaluation.csv", dtype={"BARCODE": str})
        native = panel.set_index("BARCODE").loc[policy.BARCODE, ACTIONS].to_numpy()
        if not np.allclose(native, policy[ACTIONS].to_numpy(), rtol=0, atol=1e-12):
            raise ValueError("policy evaluation outcomes differ from native normalized panel")
        sealed = pd.read_csv(dev / "sealed_confirmation_predictions.csv", dtype={"BARCODE": str})
        if policy.BARCODE.tolist() != sealed.BARCODE.tolist():
            raise ValueError("evaluation order differs from sealed predictions")
        for arm in ("fixed", "C", "CS", "shuffle"):
            if policy[arm + "_action"].tolist() != sealed[arm + "_action"].tolist():
                raise ValueError("actions changed after outcome opening")
            picked = policy[arm + "_action"].to_numpy(dtype=int)
            y = policy[ACTIONS].to_numpy()[np.arange(len(policy)), picked]
            if not np.allclose(y, policy[arm + "_observed_utility"], rtol=0, atol=1e-12):
                raise ValueError("policy outcome does not match selected action")
        published = json.loads((confirm / "summary.json").read_text())
        recomputed = {}
        for a, b, alpha in COMPARISONS:
            values = policy[a + "_observed_utility"] - policy[b + "_observed_utility"]
            calculated = crossed_mean(policy, values, alpha)
            recorded = published["comparisons"][a + "-" + b]
            if not np.allclose([calculated["mean"], *calculated["ci"], calculated["se"]],
                               [recorded["mean"], *recorded["ci"], recorded["se"]], rtol=0, atol=1e-12):
                raise ValueError("reported interval calculation does not reproduce")
            recomputed[a + "-" + b] = calculated
        save(out / "interval_reproduction.json", recomputed)
        table = contribution_table(policy)
        table.to_csv(out / "unit_contributions.csv", index=False)
        save(out / "group_contributions.json", {field: grouped_contributions(table, field)
             for field in ("C_action", "date_cluster", "tissue", "growth", "medium")})
        table.loc[table["CS-C_switched"]].to_csv(out / "density_switches.csv", index=False)
        omissions = []
        for date in sorted(policy.date_cluster.unique()):
            subset = policy.loc[policy.date_cluster != date]
            for a, b, alpha in COMPARISONS:
                record = crossed_mean(subset, subset[a + "_observed_utility"] - subset[b + "_observed_utility"], alpha)
                omissions.append(dict(omitted_date=date, comparison=a + "-" + b, retained_plates=len(subset),
                                      retained_units=subset.unit.nunique(), **record,
                                      status="post-hoc sensitivity; reweights retained units, not a new validation"))
        save(out / "date_omission.json", omissions)
        audit_controls = []
        lookup = raw.set_index("source_row")
        observed = pd.read_csv(confirm / "confirmation_observations.csv", dtype={"BARCODE": str})
        for barcode, group in observed.groupby("BARCODE", sort=False):
            r = group.iloc[0]
            nc = lookup.loc[list(map(int, r.control_source_rows_NC1.split(";"))), "INTENSITY"].to_numpy()
            blank = lookup.loc[list(map(int, r.control_source_rows_B.split(";"))), "INTENSITY"].to_numpy()
            if set(group.control_id) != {r.control_id}:
                raise ValueError("control sharing changed")
            denominator = float(nc.mean() - blank.mean())
            audit_controls.append(dict(BARCODE=barcode, denominator=denominator, nc_count=len(nc), blank_count=len(blank),
                  nc_sd=float(nc.std(ddof=1)), blank_sd=float(blank.std(ddof=1)), nc_cv=float(nc.std(ddof=1)/nc.mean()),
                  utility_outside_01=int(((group.utility < 0) | (group.utility > 1)).sum())))
        controls = pd.DataFrame(audit_controls)
        diagnostic = table.merge(controls, on="BARCODE", validate="one_to_one")
        diagnostic.to_csv(out / "denominator_diagnostics.csv", index=False)
        ranges = {comp: dict(mean_range_pp=[min(r["mean"] for r in omissions if r["comparison"] == comp)*100,
                                                    max(r["mean"] for r in omissions if r["comparison"] == comp)*100],
                                    interval_upper_range_pp=[min(r["ci"][1] for r in omissions if r["comparison"] == comp)*100,
                                                             max(r["ci"][1] for r in omissions if r["comparison"] == comp)*100])
                  for comp in recomputed}
        controls_summary = dict(denominator_min=float(controls.denominator.min()), denominator_median=float(controls.denominator.median()),
                  denominator_max=float(controls.denominator.max()), positive_denominators=bool((controls.denominator > 0).all()),
                  confirmation_outside_01=int(controls.utility_outside_01.sum()),
                  nc_cv_quantiles=controls.nc_cv.quantile([0,.5,.9,1]).to_dict(),
                  contribution_denominator_spearman={comp: float(diagnostic[comp + "_weighted_contribution"].corr(diagnostic.denominator, method="spearman"))
                                                    for comp in recomputed},
                  invalidation="no automatic exclusions/clipping; correlations are descriptive, not layout identification")
        save(out / "control_summary.json", controls_summary)
        dev_units = set(split.loc[split.split == "development", "unit"])
        test_units = set(split.loc[split.split == "confirmation", "unit"])
        if dev_units & test_units:
            raise ValueError("related unit crosses split")
        for name, expected in snapshot_receipt["paths"].items():
            if sha(snapshot / name) != expected:
                raise ValueError(f"snapshot changed during analysis: {name}")
        if any(sha(name) != value for name, value in input_hashes.items()):
            raise ValueError("source/input changed during analysis")
        receipt = dict(valid=True, source_commit=COMMIT, local_screen_report_matches_source=sha(supplied[0]) == sha(astra / "GDSC_SCREEN.md"),
                  raw_rows=len(raw), raw_plates=raw.BARCODE.nunique(), reproduced=reproduced, cutoff=cutoff,
                  patients=policy.unit.nunique(), dates=policy.date_cluster.nunique(), disjoint_unit_split=True,
                  cluster_size_counts=policy.groupby("unit").size().value_counts().sort_index().to_dict(),
                  cross_date_repeated_units=int((policy.groupby("unit").date_cluster.nunique() > 1).sum()),
                  intervals_reproduced=True, date_omission_ranges=ranges,
                  source_terms="GPL source package plus provider metadata terms; no new license certification",
                  no_new_model_fit=True, no_new_STATE_forward=True, physical_experiments=0,
                  original_findings="density increment negative, background auxiliary positive; causal/STATE/mechanism value uncertified",
                  elapsed_seconds=time.perf_counter()-start)
        save(out / "summary.json", receipt)
        print(json.dumps(receipt), flush=True)
    except Exception as exc:
        error = f"{type(exc).__name__}: {exc}"
        raise
    finally:
        save(out / "execution.json", dict(error=error, elapsed_seconds=time.perf_counter()-start))
        save(out / "manifest.json", {p.name: sha(p) for p in out.iterdir() if p.is_file() and p.name != "manifest.json"})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--dependency-dir", type=Path)
    args = parser.parse_args()
    run(args.snapshot, args.out, args.dependency_dir)
