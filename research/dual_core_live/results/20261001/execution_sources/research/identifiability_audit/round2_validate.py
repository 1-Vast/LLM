"""Independent artifact checks: cost/terminal recomputation, pairing, use and immutability."""
from __future__ import annotations

import gzip
import importlib.metadata
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from research.identifiability_audit import round2 as R


def run(out: Path):
    folder = out / "interventions"
    report = json.loads((folder / "task_summary.json").read_text())
    settings = json.loads((R.FROZEN / "manifest.json").read_text())["settings"]
    checks, counts = [], {}
    for dataset, tier in R.TASKS:
        task = dataset + "_" + tier
        rows = {(r["fold"], r["compound"], r["h1"], r["h2"]): r for r in R.tables(task)}
        columns = ["episode", "fold", "compound", "h1", "h2", "forecast", "policy", "independent_unit",
                   "sequence", "steps", "days", "measurements", "final", "utility", "correct", "wrong",
                   "undetermined", "deferred", "forecast_entered_selector", "forecast_entered_repair",
                   "forecast_entered_final_evidence", "decisions", "utility_lo", "utility_hi", "coverage"]
        frame = pd.read_csv(folder / (task + "_path_attribution.csv"), usecols=columns)
        assert len(frame) == len(rows) * len(R.CELLS)
        assert not frame.duplicated(["episode", "forecast", "policy"]).any()
        for (forecast, policy), cell in frame.groupby(["forecast", "policy"]):
            assert len(cell) == len(rows)
            if policy == "fixed":
                assert not cell.forecast_entered_selector.any()
            assert not cell.forecast_entered_final_evidence.any() and not cell.forecast_entered_repair.any()
        checked = 0
        for item in frame.to_dict("records"):
            row = rows[(item["fold"], item["compound"], item["h1"], item["h2"])]
            steps = json.loads(item["steps"])
            assert json.loads(item["sequence"]) == [s["action"] for s in steps]
            assert item["measurements"] == len(steps)
            assert abs(item["days"] - sum(settings[task]["days"][s["action"]] for s in steps)) < 1e-9
            assert item["days"] <= settings[task]["budget_days"] and len(steps) <= 2
            assert len({s["action"] for s in steps}) == len(steps)
            for i, step in enumerate(steps):
                entry = row["outcomes"][step["action"]]
                assert step["outcome"] == entry["outcome"]
                assert bool(step["qc"]) == (entry["lifecycle"] == "measured_valid")
                if not step["qc"]:
                    assert step["eliminated"] == (steps[i-1]["eliminated"] if i else [])
                if i < len(steps)-1:
                    assert not step["eliminated"]
            if not steps:
                terminal = "deferred"
            elif len(steps[-1]["eliminated"]) == 2:
                terminal = "exhausted"
            elif steps[-1]["eliminated"]:
                terminal = "wrong" if row["truth"] in steps[-1]["eliminated"] else "correct"
            else:
                terminal = "undetermined"
            assert item["final"] == terminal
            assert item["utility"] == {"correct": 1, "wrong": -2, "exhausted": -2}.get(terminal, 0)
            assert bool(item["forecast_entered_selector"]) == any(d["forecast_calls"] for d in json.loads(item["decisions"]))
            assert item["utility_lo"] <= item["utility"] <= item["utility_hi"]
            checked += 1
        for cell in report[task]["cells"]:
            sub = frame[(frame.forecast == cell["forecast"]) & (frame.policy == cell["policy"])]
            for metric in ("correct", "wrong", "undetermined", "deferred", "measurements", "days", "utility"):
                expected = float(sub.groupby("independent_unit")[metric].mean().mean())
                assert abs(expected - cell["metrics"][metric]["mean"]) < 1e-12
        # Deterministic sample of per-query hashes plus immutable full-file hashes below.
        # Receipt explicitly distinguishes this from verification of every query digest.
        sampled, forecast_rows = 0, 0
        with gzip.open(folder / (task + "_forecasts.jsonl.gz"), "rt", encoding="utf-8") as f:
            for i, line in enumerate(f):
                forecast_rows += 1
                if i % 1000:
                    continue
                entry = json.loads(line)
                query = {k: entry[k] for k in ("task_input", "forecast", "compound", "h1", "h2", "action", "history")}
                assert entry["input_sha256"] == R.digest(query)
                assert entry["output_sha256"] == R.digest(entry["content"])
                sampled += 1
        counts[task] = {"episode_cells": checked, "forecast_records": forecast_rows,
                        "query_hashes_checked": sampled, "query_sample_rule": "every 1000th record, beginning at zero",
                        "unresolved_source_selected_episode_cells": int((frame.coverage == "source_linkage_unresolved").sum())}
        checks.append(task + ":every terminal/cost/QC/path + summary arithmetic + sampled query digests")
    original = json.loads((out / "round1_input_hashes.json").read_text())
    for rel, expected in original.items():
        assert R.file_hash(R.ROOT / rel) == expected, "original artifact changed: " + rel
    checks.append("all original Round 1 artifacts, frozen replay and raw-source hashes unchanged")
    predeclared = json.loads((folder / "predeclared.json").read_text())
    for rel, expected in predeclared["inputs"].items():
        if rel.startswith("src/"):
            assert R.file_hash(R.ROOT / rel) == expected
    checks.append("all production src hashes unchanged")
    R.save(out / "result_validation.json", {"passed": True, "checks": checks, "counts": counts,
                                            "code_sha256": R.file_hash(Path(__file__)),
                                            "command": [sys.executable, *sys.argv]})
    # Include input dependencies missed by the inherited historical manifests explicitly.
    extra = [R.ROOT / "outputs/biological_depth_20260926/prepared/compounds.csv",
             R.ROOT / "data/external/lincs_l1000_phase1/GSE92742_Broad_LINCS_pert_info.txt.gz"]
    code = {p.relative_to(R.ROOT).as_posix(): R.file_hash(p) for p in
            (R.ROOT / "research/identifiability_audit").glob("*.py")}
    outputs = {p.relative_to(R.ROOT).as_posix(): R.file_hash(p) for p in out.rglob("*")
               if p.is_file() and not any("tmp" in part for part in p.relative_to(out).parts)}
    R.save(out / "artifact_ledger.json", {
        "git_commit": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=R.ROOT, text=True).strip(),
        "source_sha256": code, "initial_execution_source_sha256": predeclared["inputs"].get(
            "research/identifiability_audit/round2.py"),
        "original_and_frozen_inputs": original,
        "intervention_inputs": predeclared["inputs"],
        "additional_input_sha256": {p.relative_to(R.ROOT).as_posix(): R.file_hash(p) for p in extra},
        "outputs_sha256": outputs, "environment": {"python": sys.version, "interpreter": sys.executable,
            "packages": {p: importlib.metadata.version(p) for p in
                         ("numpy", "pandas", "scipy", "h5py", "anndata", "torch", "arc-state", "pytest")}},
        "command_receipts": ["recovery.json", "interventions/predeclared.json", "interventions/resume_receipt*.json",
                             "state/state_summary.json", "cached_world/summary.json", "result_validation.json"],
        "tests": {"initial_contracts": "13 passed", "planner_selector_state_scope": "50 passed",
                  "final_contract_and_log_layout": "9 passed; contracts.xml"},
        "limitations": "Per-query digest checks are sampled as specified; every output file has a full SHA-256. "
                       "Initial source hash precedes review-only helper repairs; final source is preserved below. "
                       "No model training or production modification. Existing frozen outcomes remain exposed development data."})
    snapshot = out / "execution_source"
    snapshot.mkdir(exist_ok=False)
    for p in (R.ROOT / "research/identifiability_audit").glob("round2*.py"):
        (snapshot / p.name).write_bytes(p.read_bytes())
    (snapshot / "state_round2.py").write_bytes((R.ROOT / "research/identifiability_audit/state_round2.py").read_bytes())
    print(json.dumps({"passed": True, "counts": counts}), flush=True)


if __name__ == "__main__":
    run(R.OUT)
