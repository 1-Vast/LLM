"""Run bounded real-checkpoint tests on an explicitly nonprospective c39 fixture."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

import anndata as ad
import h5py
import numpy as np
import pandas as pd

from tools.datasets.state_prospective_input import (
    CONTROL, CONTEXT, KEY, PERT, build_requests, digest, load_contract,
    predict, preprocess_new_rna, validate_requests, write_json,
)
from src.virtual_cell.state_runner import _column


def prepare(root, out):
    contract = load_contract(root)
    write_json(out / "contract.json", contract)
    source = Path(contract["hashes"]["dataset"]["path"])
    with h5py.File(source, "r") as handle:
        obs = handle["obs"]
        labels, contexts, plates = [_column(obs, key) for key in (PERT, "cell_name", "plate")]
        control = (labels == CONTROL) & (contexts == CONTEXT)
        plate = sorted(set(plates[control]))[0]
        selected = np.flatnonzero(control & (plates == plate))[:32]
        if len(selected) < 16:
            raise ValueError("insufficient development fixture controls")
        ids = _column(obs, obs.attrs["_index"])[selected]
        values = np.asarray(handle["obsm"][KEY][selected], dtype=np.float32)
    frame = pd.DataFrame({PERT: CONTROL, "cell_name": CONTEXT, "plate": plate,
                          "role": "baseline_control"}, index=ids)
    baseline = ad.AnnData(obs=frame)
    baseline.obsm[KEY] = values
    baseline.uns["state_feature_axis"] = np.asarray(contract["axis"])
    baseline.uns["purpose"] = "existing_development_controls_technical_fixture_only"
    baseline.write_h5ad(out / "baseline.h5ad")
    write_json(out / "baseline_provenance.json", {
        "source": contract["hashes"]["dataset"], "source_rows_zero_based": selected.tolist(),
        "source_ids": ids.tolist(), "plate": plate, "selection": "first 32 controls of lexically first plate, no response read",
        "state_collected_before_decision": "unknown", "state_available_before_decision": "unknown",
        "independent_physical_batch": "unknown; plate is only an input matching label",
        "blind_reference": "same technical baseline, frozen here before forwards; NOT an independent biological reference",
        "prospective_biological_input": False,
    })
    return contract, baseline


def run(root, out):
    out.mkdir(parents=True, exist_ok=False)
    (out / ".gitattributes").write_text("* binary\n", encoding="utf-8")
    for name in ("state_prospective_input.py", "state_prospective_certify.py"):
        shutil.copyfile(Path(__file__).with_name(name), out / (name + ".txt"))
    write_json(out / "execution.json", {"argv": [sys.executable, *sys.argv], "python": sys.version,
               "started_at_utc": datetime.now(timezone.utc).isoformat(), "model_api_calls": 0,
               "biological_state_gain_experiment": False, "local_compute_cost": "unknown"})
    actions = ["[('Trametinib', 0.05, 'uM')]", "[('Trametinib', 0.5, 'uM')]"]
    count, seed, atol, rtol = 16, 42, 1e-6, 1e-5
    contract, baseline = prepare(root, out)
    plan = {"actions": actions, "query_count_per_action": count, "seed": seed, "atol": atol, "rtol": rtol,
            "controls": baseline.n_obs, "frozen_at_utc": datetime.now(timezone.utc).isoformat(),
            "baseline_sha256": digest(out / "baseline.h5ad"), "purpose": "technical_certification_not_efficacy",
            "selector": "none; no biological action or endpoint is scored", "new_rna_status": "must_refuse"}
    write_json(out / "freeze.json", plan)
    records, checks = {}, {}
    # These are unrelated sentinel outcomes, never measured biology or model inputs.
    future = out / "sealed_future_outcomes.npy"
    np.save(future, np.zeros((2, 3), dtype=np.float32))
    future_before = digest(future)
    variants = {"visible": 0.0, "blind_identical_baseline": 0.0, "query_placeholders_replaced": 123.0,
                "future_outcomes_replaced": 0.0}
    for name, placeholder in variants.items():
        if name == "future_outcomes_replaced":
            shutil.copyfile(future, out / "future_outcomes_before.npy")
            np.save(future, np.full((2, 3), -98765.0, dtype=np.float32))
        query = build_requests(baseline, actions, count, contract, placeholder)
        query_path = out / (name + ".h5ad")
        query.write_h5ad(query_path)
        records[name] = predict(query_path, out / name, contract, actions, count, seed, forbidden_outcome=future)
        print(name, records[name]["valid"], records[name].get("error", ""), flush=True)
    for name in list(variants)[1:]:
        base_ok = records["visible"]["valid"] and records[name]["valid"]
        if base_ok:
            a = np.load(out / "visible/request_predictions.npy")
            b = np.load(out / name / "request_predictions.npy")
            checks[name] = {"passed": bool(np.allclose(a, b, atol=atol, rtol=rtol)),
                            "max_abs_difference": float(np.max(np.abs(a - b))),
                            "bitwise_equal": bool(np.array_equal(a, b))}
        else:
            checks[name] = {"passed": False, "status": "blocked_by_forward_failure"}
    checks["future_file_actually_changed"] = {"passed": future_before != digest(future),
                                               "before": future_before, "after": digest(future)}
    checks["no_future_file_reads_in_workers"] = {
        "passed": all(r.get("trace", {}).get("outcome_guard") and not r["trace"]["outcome_access_attempts"]
                      for r in records.values()),
        "scope": "Python audit hook guards the separate sentinel; does not certify arbitrary untrusted native code",
    }
    query = build_requests(baseline, actions, count, contract)
    invalids = {}
    bad = query.copy()
    bad.uns["state_feature_axis"] = bad.uns["state_feature_axis"][::-1]
    invalids["feature_order"] = bad
    bad = query.copy()
    bad.obs[PERT] = bad.obs[PERT].astype(str)
    bad.obs.loc[bad.obs["role"] == "prediction_request", PERT] = "UNKNOWN_DRUG"
    invalids["unknown_action"] = bad
    invalids["missing_baseline"] = query[query.obs["role"] == "prediction_request"].copy()
    bad = query.copy()
    bad.obs["cell_name"] = "WRONG_CONTEXT"
    invalids["wrong_context"] = bad
    bad = query.copy()
    bad.obs["plate"] = bad.obs["plate"].astype(str)
    bad.obs.loc[bad.obs["role"] == "prediction_request", "plate"] = "UNMATCHED_PLATE"
    invalids["global_pool_fallback"] = bad
    bad = query.copy()
    bad.obs.loc[bad.obs["role"] == "prediction_request", "role"] = "observed_response"
    invalids["observed_outcome_in_query"] = bad
    for name, bad in invalids.items():
        bad.write_h5ad(out / ("invalid_" + name + ".h5ad"))
        try:
            validate_requests(bad, actions, count, contract)
            checks[name] = {"passed": False, "error": "invalid input accepted"}
        except (ValueError, KeyError) as exc:
            checks[name] = {"passed": True, "expected_rejection": f"{type(exc).__name__}: {exc}"}
    try:
        preprocess_new_rna(np.ones((1, 2000)), contract["axis"], contract)
        checks["new_rna_refused"] = {"passed": False}
    except ValueError as exc:
        checks["new_rna_refused"] = {"passed": True, "expected_rejection": str(exc)}
    # Actual failing subprocess, not a mocked success/failure flag.
    failed = predict(out / "visible.h5ad", out / "missing_checkpoint", contract, actions, count,
                     checkpoint=out / "nonexistent.ckpt")
    records["missing_checkpoint"] = failed
    checks["inference_failure_not_prediction"] = {"passed": not failed["valid"] and failed.get("returncode", 0) != 0,
                                                  "valid_experiment": failed["valid_experiment"]}
    summary = {"scope": "real STATE checkpoint / existing c39 controls / software certification only",
               "checks": checks, "all_checks_passed": all(item["passed"] for item in checks.values()),
               "successful_inference_requests": sum(r["valid"] for r in records.values()),
               "actual_forward_calls": sum(r.get("forward_calls", 0) for r in records.values()),
               "real_experimental_attempts": 0, "biological_prediction_error": "not_run",
               "state_action_gain": "not_run", "terminal_utility": "not_run", "deployment_net_value": "not_run",
               "new_rna_preprocessing": "uncertified; rejected", "blind_reference_biological_validity": "uncertified",
               "training_exposure": "unknown", "records": records}
    write_json(out / "summary.json", summary)
    write_json(out / "manifest.json", {p.relative_to(out).as_posix(): digest(p) for p in out.rglob("*") if p.is_file()})
    return summary


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    result = run(args.root.resolve(), args.out.resolve())
    print(json.dumps({k: v for k, v in result.items() if k != "records"}, indent=2))
    raise SystemExit(0 if result["all_checks_passed"] else 1)
