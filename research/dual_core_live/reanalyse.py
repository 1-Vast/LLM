"""Correct uncertainty reporting without changing frozen observations or estimates."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys


def correct_intervals(summary):
    corrected, changes = deepcopy(summary), []

    def visit(value, path):
        if isinstance(value, dict):
            if "units" in value and "ci" in value and value["ci"] is not None:
                if value["units"] < 2:
                    changes.append({"path": path + "/ci", "original": value["ci"], "replacement": None,
                                    "reason": "insufficient_independent_units"})
                    value["ci"] = None
                    value["uncertainty_status"] = "insufficient_independent_units"
                elif value["ci"][0] == value["ci"][1]:
                    value["uncertainty_status"] = "zero_observed_variance_conditional_bootstrap"
            for key, item in list(value.items()):
                visit(item, path + "/" + key)
        elif isinstance(value, list):
            for index, item in enumerate(value):
                visit(item, path + "/" + str(index))

    visit(corrected, "")
    corrected["uncertainty_correction"] = {
        "single_unit_intervals_removed": len(changes),
        "interpretation": "Conditional bootstrap intervals do not establish equivalence or future-population uncertainty; physical clusters remain separate.",
        "observations_estimates_and_policy_unchanged": True,
    }
    return corrected, changes


def run(input_path, out):
    original_bytes = input_path.read_bytes()
    corrected, changes = correct_intervals(json.loads(original_bytes))
    out.mkdir(parents=True, exist_ok=False)
    target = out / "corrected_summary.json"
    with target.open("x", encoding="utf-8") as handle:
        json.dump(corrected, handle, indent=2, allow_nan=False)
    receipt = {
        "command": [sys.executable, *sys.argv],
        "git_parent": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "environment": {"python": sys.version, "platform": platform.platform(), "interpreter": sys.executable},
        "input_path": str(input_path), "input_sha256": hashlib.sha256(original_bytes).hexdigest(),
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "output_sha256": hashlib.sha256(target.read_bytes()).hexdigest(), "changes": changes,
        "new_api_calls": 0, "fits": 0,
    }
    if input_path.read_bytes() != original_bytes:
        raise RuntimeError("frozen_summary_changed")
    with (out / "correction_receipt.json").open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2, allow_nan=False)
    print(json.dumps({"removed_single_unit_intervals": len(changes), "new_api_calls": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    run(args.input.resolve(), args.out.resolve())
