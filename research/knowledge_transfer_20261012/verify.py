"""Recompute every registered verdict of block Q from the saved rows and compare with RESULTS.json.

Checks: the freeze still matches; the prediction and campaign statistics recomputed from
``results/prediction_rows.parquet`` and ``results/campaign_rows.json`` equal the raw results; the
verdicts equal ``RESULTS.json``; every campaign arm spent exactly its budget. Prints VERIFIED or
the first discrepancy.
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import pandas as pd

import confirm
import verify_freeze

HERE = Path(__file__).resolve().parent


def close(a, b, tol=1e-9) -> bool:
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(close(a[k], b[k], tol) for k in a)
    if isinstance(a, (list, tuple)) and isinstance(b, (list, tuple)):
        return len(a) == len(b) and all(close(x, y, tol) for x, y in zip(a, b))
    if isinstance(a, float) or isinstance(b, float):
        if a is None or b is None:
            return a is b
        return (math.isnan(a) and math.isnan(b)) or abs(a - b) <= tol * max(1.0, abs(a))
    return a == b


def main(results_dir: Path = HERE / "results", raw_path: Path | None = None, dry: bool = False) -> int:
    if not dry:
        verify_freeze.check()
    raw = json.loads((raw_path or results_dir / "raw_results.json").read_text(encoding="utf-8"))
    pred = pd.read_parquet(results_dir / "prediction_rows.parquet")
    camp = pd.read_json(results_dir / "campaign_rows.json", orient="records")
    problems = []
    p = json.loads(json.dumps(confirm.prediction_hypotheses(pred), default=str))
    if not close(p, raw["prediction"], 1e-6):
        problems.append("prediction statistics differ from raw_results")
    c = json.loads(json.dumps(confirm.campaign_hypotheses(camp), default=str))
    if not close(c["contrasts"], raw["campaigns"]["contrasts"], 1e-6):
        problems.append("campaign contrasts differ from raw_results")
    expected = camp.W.where(~camp.arm.isin(["zero", "generic", "vc_only"]), 0)
    over = camp[camp.wells != expected]
    if len(over):
        problems.append(f"{len(over)} arm runs did not spend exactly their budget")
    protocol = json.loads((HERE / "PROTOCOL.json").read_text(encoding="utf-8"))
    v = json.loads(json.dumps(confirm.verdicts(raw, protocol), default=str))
    stored = raw["verdicts_dry"] if dry else json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))["verdicts"]
    if not close(v, stored, 1e-9):
        problems.append("verdicts differ from RESULTS.json")
    print("VERIFIED" if not problems else "DISCREPANCY: " + "; ".join(problems))
    return 0 if not problems else 1


if __name__ == "__main__":
    if "--dry" in sys.argv:  # python verify.py --dry <dryrun name>: checks a dry run's rows against its record
        name = sys.argv[-1]
        sys.exit(main(HERE / "cache" / f"dryrun_{name}", HERE / "cache" / f"dryrun_{name}.json", dry=True))
    sys.exit(main())
