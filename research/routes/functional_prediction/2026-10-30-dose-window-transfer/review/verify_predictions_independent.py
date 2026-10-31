"""Independent arithmetic verification of the frozen C2 HTS001 predictions.

This file does not fit models, read their implementation, or audit fitting leakage.
Truth and evaluation rosters are reconstructed from the parent endpoint CSV.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
from pathlib import Path

import numpy as np
import pandas as pd


EPISODE = Path(__file__).resolve().parents[1]
EXPECTED_ENDPOINT_SHA256 = "9525bfafbfe0bd2c56d3a0f3831582f1ca598a9f9adac42f8464fbb72d9fb0ba"
METHODS = [
    "source_mean", "linear", "additive_shape", "candidate", "pooled_shape",
    "full_anchored_ridge", "joint_covariance", "smooth_gp", "hill_map",
    "profile_neighbor", "profile_tree", "wrong_shape",
]
ANCHORS = (1, 8)
QUERIES = tuple(range(2, 8))
CELLS = ("BR1", "DS3", "DS7", "DS8", "DS9", "PC9")
N_DRUGS, N_DOSES, MARGIN = 14, 10, 0.25
KEY = ["cell", "drug", "dose_index"]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def finite(frame, columns, name):
    for column in columns:
        frame[column] = pd.to_numeric(frame[column], errors="raise")
        require(np.isfinite(frame[column].to_numpy(dtype=float)).all(),
                f"{name}: nonfinite {column}")


def boolean_column(series, name):
    values = series.astype(str).str.strip().str.lower()
    require(values.isin(["true", "false", "1", "0"]).all(),
            f"invalid Boolean values in {name}")
    return values.isin(["true", "1"]).to_numpy()


def load_truth(path):
    require(sha256(path) == EXPECTED_ENDPOINT_SHA256, "frozen endpoint SHA256 differs")
    frame = pd.read_csv(path, dtype={"cell.line": str, "upid": str,
                                     "well": str, "drug1": str})
    columns = ["cell.line", "upid", "well", "drug1", "drug1.conc",
               "log2_growth", "relative_growth"]
    require(set(columns).issubset(frame.columns), "endpoint columns missing")
    require(not frame[columns].isna().any().any(), "endpoint contains missing values")
    finite(frame, ["drug1.conc", "log2_growth", "relative_growth"], "endpoint")
    require(not frame.duplicated(["upid", "well"]).any(), "duplicate physical endpoint well")
    require(tuple(sorted(frame["cell.line"].unique())) == CELLS,
            "unexpected background roster")
    require(frame.groupby("cell.line")["upid"].nunique().eq(1).all(),
            "each background must have one plate")
    require(frame.groupby("upid")["cell.line"].nunique().eq(1).all(),
            "plate shared between background labels")
    control = frame["drug1"].eq("control")
    require(frame.loc[control, "drug1.conc"].eq(0).all(), "nonzero vehicle dose")
    vehicle = frame.loc[control].groupby("upid")["log2_growth"].median()
    require(set(vehicle.index) == set(frame["upid"]), "missing vehicle controls")
    independent_y = frame["log2_growth"] - frame["upid"].map(vehicle)
    require(np.allclose(independent_y, frame["relative_growth"], atol=1e-10, rtol=1e-10),
            "cached relative growth differs from independently centered endpoint")
    frame["independent_y"] = independent_y
    treated = frame.loc[~control].copy()
    require(treated["drug1.conc"].gt(0).all(), "nonpositive treated dose")
    drugs = tuple(sorted(treated["drug1"].unique()))
    require(len(drugs) == N_DRUGS, "unexpected compound count")
    grids = {}
    records = []
    for cell in CELLS:
        subset = treated.loc[treated["cell.line"].eq(cell)]
        require(set(subset["drug1"]) == set(drugs), f"drug roster differs in {cell}")
        for drug in drugs:
            group = subset.loc[subset["drug1"].eq(drug)]
            doses = tuple(sorted(group["drug1.conc"].unique()))
            require(len(doses) == N_DOSES, f"wrong dose count: {cell}/{drug}")
            if drug in grids:
                require(doses == grids[drug], f"physical dose grid differs: {cell}/{drug}")
            else:
                grids[drug] = doses
            for index, dose in enumerate(doses):
                wells = group.loc[group["drug1.conc"].eq(dose)].sort_values("well")
                require(len(wells) == 2 and wells["well"].nunique() == 2,
                        f"condition lacks exactly two lexical wells: {cell}/{drug}/{dose}")
                y0, y1 = wells["independent_y"].to_numpy(dtype=float)
                records.append({"cell": cell, "drug": drug, "dose_index": index,
                                "dose_M": float(dose), "well0": wells.iloc[0]["well"],
                                "well1": wells.iloc[1]["well"], "y0": float(y0),
                                "y1": float(y1), "y": float((y0 + y1) / 2),
                                "is_anchor": index in ANCHORS,
                                "is_query": index in QUERIES})
    truth = pd.DataFrame.from_records(records)
    metadata = {
        "backgrounds": list(CELLS), "drugs": list(drugs),
        "dose_grids_M": {drug: list(grid) for drug, grid in grids.items()},
        "anchor_indices": list(ANCHORS), "query_indices": list(QUERIES),
        "endpoint_rows": int(len(frame)), "condition_rows": int(len(truth)),
        "vehicle_wells_by_plate": {str(k): int(v) for k, v in
                                   frame.loc[control].groupby("upid").size().items()},
        "calibration_conditions_per_background": N_DRUGS * len(ANCHORS),
        "calibration_conditions_total": len(CELLS) * N_DRUGS * len(ANCHORS),
        "query_conditions_per_background": N_DRUGS * len(QUERIES),
        "query_conditions_total": len(CELLS) * N_DRUGS * len(QUERIES),
        "technical_well_mapping": "ascending lexical well label within each condition",
        "outcome": "log2_growth minus plate vehicle median log2_growth",
    }
    return truth, metadata


def load_predictions(path, truth, methods):
    frame = pd.read_csv(path, dtype={"method": str, "cell": str, "drug": str})
    required = ["method", *KEY, "dose_M", "y0", "y1", "prediction", "is_anchor", "is_query"]
    require(set(required).issubset(frame.columns), "prediction columns missing")
    require(not frame[required].isna().any().any(), "predictions contain missing values")
    finite(frame, ["dose_index", "dose_M", "y0", "y1", "prediction"], "predictions")
    require(np.equal(frame["dose_index"], np.floor(frame["dose_index"])).all(),
            "noninteger dose_index")
    frame["dose_index"] = frame["dose_index"].astype(int)
    require(not frame.duplicated(["method", *KEY]).any(), "duplicate prediction condition")
    require(set(frame["method"]) == set(methods), "incomplete or unexpected method panel")
    require(len(frame) == len(methods) * len(truth), "wrong total prediction row count")
    for method in methods:
        got = frame.loc[frame["method"].eq(method), KEY]
        expected = truth[KEY]
        check = expected.merge(got, on=KEY, how="outer", indicator=True, validate="one_to_one")
        require(check["_merge"].eq("both").all(), f"roster differs for {method}")
    frame = frame.merge(truth, on=KEY, how="left", suffixes=("_supplied", ""),
                        validate="many_to_one")
    require(frame["dose_M"].notna().all(), "prediction outside metadata roster")
    for column in ("dose_M", "y0", "y1"):
        require(np.allclose(frame[f"{column}_supplied"], frame[column],
                            atol=0 if column == "dose_M" else 1e-10,
                            rtol=1e-12 if column == "dose_M" else 1e-10),
                f"supplied {column} differs from independently rebuilt truth")
    for column in ("is_anchor", "is_query"):
        require(np.array_equal(boolean_column(frame[f"{column}_supplied"], column),
                               frame[column].to_numpy(dtype=bool)),
                f"supplied {column} differs from metadata")
    return frame


def make_rosters(truth):
    query = truth.loc[truth["is_query"]]
    pairs, menus = [], []
    for cell in CELLS:
        cell_query = query.loc[query["cell"].eq(cell)]
        drugs = sorted(cell_query["drug"].unique())
        doses = {drug: set(cell_query.loc[cell_query["drug"].eq(drug), "dose_M"])
                 for drug in drugs}
        for first, second in itertools.combinations(drugs, 2):
            common = sorted(doses[first] & doses[second])
            if common:
                pairs.append({"cell": cell, "drug_a": first, "drug_b": second,
                              "dose_M": common})
        for dose, group in cell_query.groupby("dose_M", sort=True):
            members = sorted(group["drug"].unique())
            if len(members) >= 2:
                menus.append({"cell": cell, "dose_M": float(dose), "drugs": members})
    require(pairs and menus, "no eligible exact-physical-dose choices")
    return pairs, menus


def aggregate(frame, value, inner):
    require(np.isfinite(frame[value].to_numpy(dtype=float)).all(), f"nonfinite derived {value}")
    by_unit = frame.groupby(["cell", *inner], sort=True)[value].mean()
    per_background = by_unit.groupby("cell").mean().reindex(CELLS)
    require(per_background.notna().all(), f"missing background loss in {value}")
    return {"aggregate": float(per_background.mean()),
            "per_background": {cell: float(per_background.loc[cell]) for cell in CELLS}}


def flip_counts(records):
    observed = sum(row["observed_flip"] for row in records)
    predicted = sum(row["predicted_flip"] for row in records)
    tp = sum(row["observed_flip"] and row["predicted_flip"] for row in records)
    return {"pair_count": len(records), "observed": int(observed),
            "predicted": int(predicted), "true_positive": int(tp),
            "false_positive": int(predicted - tp), "false_negative": int(observed - tp),
            "sensitivity": float(tp / observed) if observed else None,
            "precision": float(tp / predicted) if predicted else None}


def score_methods(predictions, truth, methods, pairs, menus):
    methods_out, pair_rows, menu_rows, flip_rows = {}, [], [], []
    query = truth.loc[truth["is_query"]]
    truth_lookup = {(r.cell, r.drug, r.dose_M): r for r in query.itertuples(index=False)}
    for method in methods:
        values = predictions.loc[predictions["method"].eq(method) & predictions["is_query"]]
        pred = {(r.cell, r.drug, r.dose_M): float(r.prediction)
                for r in values.itertuples(index=False)}
        method_pairs, method_menus, method_flips = [], [], []
        for unit in pairs:
            cell, first, second = unit["cell"], unit["drug_a"], unit["drug_b"]
            differences, positive, negative = [], [], []
            for dose in unit["dose_M"]:
                a, b = truth_lookup[(cell, first, dose)], truth_lookup[(cell, second, dose)]
                delta = pred[(cell, first, dose)] - pred[(cell, second, dose)]
                require(np.isfinite(delta), f"nonfinite pair contrast: {method}/{cell}/{first}/{second}/{dose}")
                choose_first = delta <= 0  # first is lexicographically earlier
                chosen = a if choose_first else b
                row = {"method": method, "cell": cell, "drug_a": first, "drug_b": second,
                       "dose_M": dose, "chosen_drug": first if choose_first else second,
                       "predicted_difference": delta, "observed_difference": a.y - b.y,
                       "regret": float(chosen.y - min(a.y, b.y)),
                       "regret_y0": float(chosen.y0 - min(a.y0, b.y0)),
                       "regret_y1": float(chosen.y1 - min(a.y1, b.y1))}
                method_pairs.append(row)
                differences.append(delta)
                same0, same1 = a.y0 - b.y0, a.y1 - b.y1
                positive.append(same0 >= MARGIN and same1 >= MARGIN
                                and min(a.y0, a.y1) > max(b.y0, b.y1))
                negative.append(same0 <= -MARGIN and same1 <= -MARGIN
                                and max(a.y0, a.y1) < min(b.y0, b.y1))
            method_flips.append({"method": method, "cell": cell, "drug_a": first,
                                 "drug_b": second, "query_doses": len(differences),
                                 "observed_flip": bool(any(positive) and any(negative)),
                                 "predicted_flip": bool(max(differences) >= MARGIN
                                                        and min(differences) <= -MARGIN)})
        for menu in menus:
            cell, dose = menu["cell"], menu["dose_M"]
            members = menu["drugs"]
            chosen = min(members, key=lambda drug: (pred[(cell, drug, dose)], drug))
            best_y = min(truth_lookup[(cell, drug, dose)].y for drug in members)
            method_menus.append({"method": method, "cell": cell, "dose_M": dose,
                                 "menu_size": len(members), "chosen_drug": chosen,
                                 "regret": float(truth_lookup[(cell, chosen, dose)].y - best_y)})
        pair_frame, menu_frame = pd.DataFrame(method_pairs), pd.DataFrame(method_menus)
        mse = values[["cell", "drug", "dose_index"]].copy()
        mse["squared_error"] = (values["prediction"] - values["y"]) ** 2
        flips = flip_counts(method_flips)
        flips["per_background"] = {
            cell: flip_counts([row for row in method_flips if row["cell"] == cell])
            for cell in CELLS}
        methods_out[method] = {
            "primary": aggregate(pair_frame, "regret", ["drug_a", "drug_b"]),
            "technical_primary": {
                "well0": aggregate(pair_frame, "regret_y0", ["drug_a", "drug_b"]),
                "well1": aggregate(pair_frame, "regret_y1", ["drug_a", "drug_b"])},
            "best_drug": aggregate(menu_frame, "regret", ["dose_M"]),
            "mse": aggregate(mse, "squared_error", ["drug", "dose_index"]),
            "flips": flips,
            "denominators": {
                "full_prediction_conditions": int(predictions["method"].eq(method).sum()),
                "query_prediction_conditions": int(len(values)), "pair_dose_choices": len(method_pairs),
                "background_pairs": len(method_flips), "best_drug_menus": len(method_menus)}}
        pair_rows.extend(method_pairs)
        menu_rows.extend(method_menus)
        flip_rows.extend(method_flips)
    require(len({json.dumps(v["denominators"], sort_keys=True) for v in methods_out.values()}) == 1,
            "method scoring denominators differ")
    return methods_out, pair_rows, menu_rows, flip_rows


def continuation_gate(scores, methods, candidate, wrong_control):
    rivals = [method for method in methods if method not in (candidate, wrong_control)]
    # A tie between rival aggregate losses follows the fixed protocol panel order.
    rival = min(rivals, key=lambda method: scores[method]["primary"]["aggregate"])
    candidate_loss = scores[candidate]["primary"]["aggregate"]
    rival_loss = scores[rival]["primary"]["aggregate"]
    absolute = rival_loss - candidate_loss
    relative = absolute / rival_loss if rival_loss > 0 else None
    differences = np.array([scores[rival]["primary"]["per_background"][cell]
                            - scores[candidate]["primary"]["per_background"][cell]
                            for cell in CELLS], dtype=float)
    draws = np.random.default_rng(1031).integers(0, len(CELLS), size=(2000, len(CELLS)))
    bootstrapped = differences[draws].mean(axis=1)
    interval = np.quantile(bootstrapped, [0.025, 0.975], method="linear")
    comparator_gains = {method: scores[method]["primary"]["aggregate"] - candidate_loss
                        for method in ("linear", "pooled_shape", wrong_control)}
    technical_gains = {
        well: scores[rival]["technical_primary"][well]["aggregate"]
              - scores[candidate]["technical_primary"][well]["aggregate"]
        for well in ("well0", "well1")}
    menu_gain = scores[rival]["best_drug"]["aggregate"] - scores[candidate]["best_drug"]["aggregate"]
    criteria = {
        "full_prediction_matrix_complete": True,
        "absolute_reduction_at_least_0_05": bool(absolute >= 0.05),
        "relative_reduction_at_least_20_percent": bool(relative is not None and relative >= 0.20),
        "improved_in_at_least_four_backgrounds": bool(np.count_nonzero(differences > 0) >= 4),
        "paired_background_interval_entirely_above_zero": bool(interval[0] > 0),
        "beats_linear_by_at_least_0_01": bool(comparator_gains["linear"] >= 0.01),
        "beats_pooled_shape_by_at_least_0_01": bool(comparator_gains["pooled_shape"] >= 0.01),
        "beats_wrong_shape_by_at_least_0_01": bool(comparator_gains[wrong_control] >= 0.01),
        "best_drug_regret_no_worse_than_fixed_primary_rival": bool(menu_gain >= 0),
        "well0_primary_improvement_nonnegative": bool(technical_gains["well0"] >= 0),
        "well1_primary_improvement_nonnegative": bool(technical_gains["well1"] >= 0),
    }
    return {
        "candidate": candidate, "wrong_shape_control": wrong_control,
        "strongest_primary_rival": rival, "rival_tie_rule": "fixed protocol panel order",
        "candidate_primary_loss": candidate_loss, "rival_primary_loss": rival_loss,
        "rival_oracle_headroom": rival_loss,
        "absolute_margin_unattainable_with_nonnegative_loss_at_this_headroom": bool(rival_loss < 0.05),
        "absolute_improvement": absolute, "relative_improvement": relative,
        "background_improvements": {cell: float(value) for cell, value in zip(CELLS, differences)},
        "improved_background_count": int(np.count_nonzero(differences > 0)),
        "bootstrap": {"unit": "paired background", "seed": 1031,
                      "rng": "numpy.random.default_rng", "resamples": 2000,
                      "background_order": list(CELLS), "interval": interval.tolist(),
                      "quantile_method": "linear", "rival_reselected_in_draws": False},
        "comparator_primary_improvements": comparator_gains,
        "best_drug_improvement_against_primary_rival": float(menu_gain),
        "technical_primary_improvements_against_primary_rival": technical_gains,
        "criteria": criteria, "metric_gate_pass": bool(all(criteria.values())),
        "metric_decision": "CONTINUE_TO_SEPARATE_PROTOCOL_REVIEW" if all(criteria.values())
                           else "PARK_THIS_SHAPE_RESTRICTION",
        "scope": "Arithmetic only; fitting leakage and execution provenance are not audited.",
    }


def at_path(value, path):
    for part in path:
        value = value[part]
    return value


def compare_values(left, right, label):
    if isinstance(left, dict):
        require(isinstance(right, dict) and set(left) == set(right), f"{label}: dictionary keys differ")
        for key in left:
            compare_values(left[key], right[key], f"{label}/{key}")
    elif isinstance(left, list):
        require(isinstance(right, list) and len(left) == len(right), f"{label}: list shape differs")
        for i, (a, b) in enumerate(zip(left, right)):
            compare_values(a, b, f"{label}/{i}")
    elif isinstance(left, bool) or left is None or isinstance(left, str):
        require(type(left) is type(right) and left == right, f"{label}: values differ: {left!r}/{right!r}")
    else:
        require(isinstance(right, (int, float)) and not isinstance(right, bool), f"{label}: nonnumeric value")
        require(np.isfinite(right) and np.isclose(left, right, rtol=1e-10, atol=1e-10),
                f"{label}: values differ: {left!r}/{right!r}")


def compare_root_outputs(summary, decision, args):
    if not (args.root_summary or args.root_decision or args.comparison_map):
        return {"performed": False}
    require(args.root_summary and args.root_decision and args.comparison_map,
            "comparison needs --root-summary, --root-decision and --comparison-map")
    root = {"summary": json.loads(args.root_summary.read_text(encoding="utf-8-sig")),
            "decision": json.loads(args.root_decision.read_text(encoding="utf-8-sig"))}
    mapping = json.loads(args.comparison_map.read_text(encoding="utf-8-sig"))
    require(isinstance(mapping, list) and mapping, "comparison mapping must be a nonempty list")
    independent = {"summary": summary, "decision": decision}
    checked = []
    for item in mapping:
        label = item.get("label", "/".join(map(str, item["independent_path"])))
        actual = at_path(independent[item["independent_document"]], item["independent_path"])
        reported = at_path(root[item["root_document"]], item["root_path"])
        compare_values(actual, reported, label)
        checked.append(label)
    return {"performed": True, "checked_fields": checked,
            "root_summary_sha256": sha256(args.root_summary),
            "root_decision_sha256": sha256(args.root_decision),
            "comparison_map_sha256": sha256(args.comparison_map)}


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--endpoint", type=Path, default=EPISODE.parent /
                        "2026-10-30-virtual-cell-four-directions/census_c_wells.csv")
    parser.add_argument("--predictions", type=Path, default=Path(
        "D:/MAESTRO/data/processed/virtual_cell_dose_transfer_20261030/c2_hts001/predictions.csv"))
    parser.add_argument("--output-dir", type=Path, default=EPISODE / "review/independent_metrics")
    parser.add_argument("--candidate", default="candidate")
    parser.add_argument("--wrong-control", default="wrong_shape")
    parser.add_argument("--root-summary", type=Path)
    parser.add_argument("--root-decision", type=Path)
    parser.add_argument("--comparison-map", type=Path,
                        help="JSON field-path map; permits schema differences without editing this frozen verifier")
    args = parser.parse_args()
    methods = [args.candidate if method == "candidate" else
               args.wrong_control if method == "wrong_shape" else method for method in METHODS]
    require(len(set(methods)) == len(METHODS), "candidate/control aliases collide with method panel")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    try:
        truth, metadata = load_truth(args.endpoint)
        predictions = load_predictions(args.predictions, truth, methods)
        pairs, menus = make_rosters(truth)
        scores, pair_rows, menu_rows, flip_rows = score_methods(predictions, truth, methods, pairs, menus)
        decision = continuation_gate(scores, methods, args.candidate, args.wrong_control)
        metadata["pair_roster"] = pairs
        metadata["complete_best_drug_menus"] = menus
        metadata["pair_counts_by_background"] = {
            cell: sum(unit["cell"] == cell for unit in pairs) for cell in CELLS}
        metadata["pair_dose_counts_by_background"] = {
            cell: sum(len(unit["dose_M"]) for unit in pairs if unit["cell"] == cell) for cell in CELLS}
        metadata["menu_counts_by_background"] = {
            cell: sum(unit["cell"] == cell for unit in menus) for cell in CELLS}
        metadata["prediction_rows_by_method"] = {
            method: int(predictions["method"].eq(method).sum()) for method in methods}
        summary = {
            "schema": "c2_independent_output_metrics_v1", "status": "VALID_COMPLETE_MATRIX",
            "hashes": {"endpoint": sha256(args.endpoint), "predictions": sha256(args.predictions),
                       "verifier": sha256(__file__), "protocol": sha256(EPISODE / "protocol.md"),
                       "protocol_v1_1": sha256(EPISODE / "protocol_v1_1.md")},
            "metadata": metadata, "methods": scores, "gate": decision,
            "limitations": ["No model refitting or fitting-leakage audit was performed.",
                            "Six backgrounds have shared training and are not independent preparations.",
                            "HTS001 is exposed development evidence; no external validation is asserted."],
        }
        summary["root_comparison"] = {"performed": False}
        truth.to_csv(args.output_dir / "truth_independent.csv", index=False)
        pd.DataFrame(pair_rows).to_csv(args.output_dir / "pair_choices_independent.csv", index=False)
        pd.DataFrame(menu_rows).to_csv(args.output_dir / "menu_choices_independent.csv", index=False)
        pd.DataFrame(flip_rows).to_csv(args.output_dir / "flips_independent.csv", index=False)
        write_json(args.output_dir / "summary_independent.json", summary)
        write_json(args.output_dir / "decision_independent.json", decision)
        summary["root_comparison"] = compare_root_outputs(summary, decision, args)
        write_json(args.output_dir / "summary_independent.json", summary)
        print(json.dumps({"status": summary["status"], "metric_gate_pass": decision["metric_gate_pass"],
                          "strongest_primary_rival": decision["strongest_primary_rival"],
                          "output_dir": str(args.output_dir)}, ensure_ascii=False))
    except Exception as error:
        write_json(args.output_dir / "verification_failure.json",
                   {"status": "INCONCLUSIVE_OUTPUT_VERIFICATION_FAILURE",
                    "error_type": type(error).__name__, "error": str(error),
                    "fitting_leakage_audited": False})
        raise


if __name__ == "__main__":
    main()
