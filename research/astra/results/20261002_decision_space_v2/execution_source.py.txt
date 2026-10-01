"""Observed c39 RNA coverage audit; does not identify intervention utility.

Exact nonsolvate Trametinib labels only. Missing actions remain missing; cells,
sublibraries and native sample IDs are not authenticated physical replicates.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
from itertools import combinations
import json
from pathlib import Path

import anndata as ad
import h5py
import numpy as np
import pandas as pd

from tools.datasets.state_prospective_input import CONTROL, PERT, digest, write_json
from research.astra.zero_audit import choice, paired_contrasts


ACTIONS = [str([("Trametinib", dose, "uM")]) for dose in (.05, .5, 5.)]


def describe(values):
    values = np.asarray(values, dtype=float)
    if not len(values):
        return dict(cells=0, mean=None, minimum=None, maximum=None, nonzero=None)
    if not np.isfinite(values).all():
        raise ValueError("nonfinite observed RNA; no zero imputation")
    return dict(cells=len(values), mean=float(values.mean()), minimum=float(values.min()),
                maximum=float(values.max()), nonzero=int((values != 0).sum()))


def coverage_table(records, actions):
    """Count actual conditions within each plate; never substitute predictions."""
    if len(set(actions)) != len(actions) or CONTROL in actions or len(actions) < 2:
        raise ValueError("distinct noncontrol action menu required")
    result = []
    for plate, rows in records.groupby("plate", sort=True):
        counts = [int((rows[PERT] == action).sum()) for action in actions]
        control = int((rows[PERT] == CONTROL).sum())
        result.append(dict(plate=str(plate), measured_cell_counts=counts, control_cells=control,
                           measured_action_indices=[i for i, count in enumerate(counts) if count],
                           complete_menu_with_control=all(counts) and control > 0,
                           missing_action_indices=[i for i, count in enumerate(counts) if not count],
                           independent_parent_cultures=None))
    return result


def condition_table(records, actions):
    result = []
    for (plate, action), rows in records.groupby(["plate", PERT], sort=True):
        if action not in actions:
            continue
        controls = records[(records["plate"] == plate) & (records[PERT] == CONTROL)]
        treated, control = describe(rows["EGR1"]), describe(controls["EGR1"])
        result.append(dict(plate=str(plate), action=str(action), observed_EGR1=treated,
                           native_sample_ids=sorted(rows["sample"].astype(str).unique().tolist()),
                           observed_control_EGR1=control,
                           control_sample_ids=sorted(controls["sample"].astype(str).unique().tolist()),
                           filter_strata={str(k): describe(v["EGR1"]) for k, v in rows.groupby("pass_filter")},
                           control_filter_strata={str(k): describe(v["EGR1"]) for k, v in controls.groupby("pass_filter")},
                           matched_plate_difference=(treated["mean"] - control["mean"] if control["cells"] else None),
                           comparison_scope="same-plate descriptive RNA; parent/randomization/attempt QC unknown",
                           intervention_utility=None, physical_CI=None))
    return result


def prediction_agreement(conditions, prediction_summary):
    lookup = {(r["plate"], r["action"]): r for r in conditions}
    result = []
    for row in prediction_summary["rows"]:
        for action, predicted in zip(prediction_summary["action_labels"], row["endpoint_scores"]):
            observed = lookup.get((row["pool"], action))
            actual = observed["observed_EGR1"]["mean"] if observed else None
            result.append(dict(pool=row["pool"], seed=row["seed"], action=action,
                               predicted_mean=predicted, observed_mean=actual,
                               absolute_difference=abs(predicted - actual) if actual is not None else None,
                               observed_cells=observed["observed_EGR1"]["cells"] if observed else 0,
                               status="matched plate/action diagnostic; not held-out accuracy" if observed else "no measured action on this plate",
                               exposure="unknown", actual_state_gain=None))
    return result


def sampling_diagnostics(summary):
    """Leave-one-draw-out sensitivity, not an interval or adaptive seed selection."""
    results = []
    for pool in sorted({row["pool"] for row in summary["rows"]}):
        rows = [r for r in summary["rows"] if r["pool"] == pool]
        if len(rows) != 3 or {r["seed"] for r in rows} != {17, 42, 103}:
            raise ValueError("exact three frozen numeric draws required")
        utilities = -np.asarray([r["endpoint_scores"] for r in rows], dtype=float)
        for row in rows:
            calls = [c for c in row["trace"]["calls"] if c["paired"]]
            if len(calls) != 3 or len({c["basal_sha256"] for c in calls}) != 1:
                raise ValueError("actual within-request pairing required")
        omitted = [dict(omitted_seed=row["seed"], **choice(np.delete(utilities, i, axis=0).mean(axis=0)))
                   for i, row in enumerate(rows)]
        results.append(dict(pool=pool, uniform_K3=choice(utilities.mean(axis=0)),
                            leave_one_seed_out=omitted, contrasts=paired_contrasts(utilities, True),
                            diagnostic_scope="previously inspected K3 draws; numerical sensitivity only",
                            biological_variance=None, model_bias=None, domain_shift=None,
                            decision="do not increase K to claim physical benefit; validate readout and action panel first"))
    return results


def run(root, out):
    root, out = root.resolve(), out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    dataset = root / "data/external/arc_state/tahoe_metadata_source/c39.h5ad"
    identity = root / "research/astra/results/20261002_egr1_identity/receipt.json"
    grid = root / "research/astra/results/20261002_paired_matrix_v1/summary.json"
    zeros = root / "research/astra/results/20261002_zero_audit_v1/receipt.json"
    inputs = {str(p): digest(p) for p in (dataset, identity, grid, zeros, Path(__file__))}
    certified = json.loads(identity.read_text(encoding="utf-8"))
    if not certified["passed"] or certified["x_hvg_column"] != 546 or inputs[str(dataset)] != certified["files"]["dataset"]["sha256_before"]:
        raise ValueError("fixed EGR1 identity proof or dataset unavailable")
    write_json(out / "freeze.json", dict(frozen_at_utc=datetime.now(timezone.utc).isoformat(),
               inputs=inputs, actions=ACTIONS, context="NCI-H596", endpoint="observed log1p EGR1; no efficacy utility",
               filters="retain all published rows, report pass_filter strata separately; no new QC threshold",
               missing_actions="remain missing", replicate_level="unknown physical cultures; no physical CI",
               meaningful_delta=None, outcome_previously_inspected="metadata yes; descriptive development study",
               model_forwards=0, costs="unknown", decision_state_available="uncertified"))
    (out / "execution_source.py.txt").write_bytes(Path(__file__).read_bytes())
    with h5py.File(dataset, "r") as handle:
        obs = ad.io.read_elem(handle["obs"])
        values = handle["obsm/X_hvg"][:, 546]
    if not obs.index.is_unique or len(values) != len(obs) or set(obs["cell_name"].astype(str)) != {"NCI-H596"}:
        raise ValueError("native row identity or context changed")
    labels = obs[PERT].astype(str)
    selected = labels.isin(ACTIONS + [CONTROL])
    cols = ["sample", "plate", PERT, "cell_name", "pass_filter", "sublibrary"]
    records = obs.loc[selected, cols].copy().astype(str)
    records.insert(0, "native_observation_id", obs.index[selected].astype(str))
    records.insert(1, "source_row_zero_based", np.flatnonzero(selected))
    records["EGR1"] = values[selected]
    records["source_file_sha256"] = inputs[str(dataset)]
    records["EGR1_coordinate_zero_based"] = 546
    records.to_csv(out / "observed_rows.csv", index=False)
    coverage, conditions = coverage_table(records, ACTIONS), condition_table(records, ACTIONS)
    predicted = json.loads(grid.read_text(encoding="utf-8"))
    agreement = prediction_agreement(conditions, predicted)
    write_json(out / "coverage.json", coverage)
    write_json(out / "conditions.json", conditions)
    write_json(out / "prediction_agreement.json", agreement)
    write_json(out / "sampling_diagnostics.json", sampling_diagnostics(predicted))
    ranges = [r["observed_EGR1"]["mean"] for r in conditions]
    pair_support = {f"{a}:{b}": [r["plate"] for r in coverage if r["measured_cell_counts"][a] and r["measured_cell_counts"][b] and r["control_cells"]]
                    for a, b in combinations(range(3), 2)}
    matched = [r for r in agreement if r["observed_mean"] is not None]
    summary = dict(valid=True, source_cells=len(obs), retained_rows=len(records),
                   observed_treatment_conditions=len(conditions), observed_treated_cells=sum(r["observed_EGR1"]["cells"] for r in conditions),
                   observed_treated_nonzero_EGR1=sum(r["observed_EGR1"]["nonzero"] for r in conditions),
                   plates_with_complete_action_menu=sum(r["complete_menu_with_control"] for r in coverage),
                   same_plate_action_pair_support=pair_support,
                   global_observed_condition_mean_range=[min(ranges), max(ranges)],
                   matched_prediction_action_requests=len(matched), missing_prediction_action_requests=len(agreement) - len(matched),
                   zero_predictions_with_positive_observed_mean=sum(r["predicted_mean"] == 0 and r["observed_mean"] > 0 for r in matched),
                   response_readout_varies="yes, descriptively across dose/plate conditions",
                   independent_action_effect="not_identified; action/dose and plate confounded",
                   state_changes_observed_ranking="not_identified; no legal predecision state or within-unit action panel",
                   final_utility_headroom="unknown; observed endpoint is RNA, not validated utility",
                   QC_scope="pass_filter strata only; full attempted-experiment denominator unavailable",
                   physical_CI=None, model_forwards=0, physical_attempts=0, actual_cost=None)
    if any(digest(path) != value for path, value in inputs.items()):
        raise ValueError("audit input changed")
    write_json(out / "summary.json", summary)
    write_json(out / "manifest.json", {p.name: digest(p) for p in out.iterdir() if p.is_file()})
    print(json.dumps(summary), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.root, args.out)
