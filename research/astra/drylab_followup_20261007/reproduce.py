"""Replay the supplied experiment without overwriting its evidence."""
from __future__ import annotations

import contextlib
import argparse
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "drylab_solution_20261007"


def load_replay():
    spec = importlib.util.spec_from_file_location("supplied_drylab", SOURCE / "run_simulation.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def preservation():
    receipt = json.loads((HERE / "import_receipt.json").read_text(encoding="utf-8"))
    root = HERE.parents[2]
    checked = []
    for item in receipt["files"]:
        actual = hashlib.sha256((root / item["local_path"]).read_bytes()).hexdigest()
        assert actual == item["sha256"], item["local_path"]
        checked.append(item["local_path"])
    return checked


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "reproduction")
    args = parser.parse_args()
    checked = preservation()
    module = load_replay()
    dest = args.output
    dest.mkdir(exist_ok=False)
    module.RESULTS = dest
    with (dest / "stdout.txt").open("w", encoding="utf-8") as stream:
        with contextlib.redirect_stdout(stream):
            module.main()
    matched = []
    for filename in ["summary.csv", "campaigns.csv", "fold_choices.csv", "sensitivity_grid.csv"]:
        pd.testing.assert_frame_equal(pd.read_csv(dest / filename), pd.read_csv(SOURCE / "results" / filename))
        matched.append(filename)
    def traces(path):
        return [json.loads(line) for line in path.read_text().splitlines()]
    assert traces(dest / "purchase_traces.jsonl") == traces(SOURCE / "results/purchase_traces.jsonl")
    matched.append("purchase_traces.jsonl")
    old = json.loads((SOURCE / "results/diagnostics.json").read_text())
    new = json.loads((dest / "diagnostics.json").read_text())
    old.pop("wall_seconds"); new.pop("wall_seconds")
    assert old == new
    report = {"preserved_files": len(checked), "matched_outputs": matched,
              "trace_bytes_equal": (dest / "purchase_traces.jsonl").read_bytes() == (SOURCE / "results/purchase_traces.jsonl").read_bytes(),
              "comparison": "Parsed CSV/JSON records; native writer line endings may differ",
              "diagnostics_match_except_runtime": True, "checks": new["tests"]}
    preservation()
    (dest / "verification.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
