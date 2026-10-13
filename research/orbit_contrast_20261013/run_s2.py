"""Entry point for the single S2 validation run after deviation D4 (controls call-site defect).

File summary
- Path: research/orbit_contrast_20261013/run_s2.py
- Purpose: the frozen `run.py s2` computed the real and relabelled S2 results and then crashed in
  `run_controls` before writing anything. `stage` passed the dict of Task B pipelines where
  `run_controls` expects the non-trivial pipeline's result (`KeyError: 'scores'`). This file leaves
  the frozen bytes of run.py untouched and wraps `run_controls` so it receives `rb["nontrivial"]`,
  which is what the dev-fold smoke test passed. Nothing else changes: same folds, salts, arms,
  populations, relabel count and output format.
- Core points:
  - Refuses unless FREEZE.json authenticates and RESULTS.json does not exist (as run.py does).
  - `--path-check` runs the same code path on the development fold 0 with controls and no
    relabelling, writing only to tmp/, so the wrapped path is shown crash-free before S2.
- Commands (study folder): `python run_s2.py --path-check`, then `python run_s2.py`.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import freeze  # noqa: E402
import run  # noqa: E402

_frozen_run_controls = run.run_controls


def _run_controls(W, ra, pa, rb, pb, outer):
    return _frozen_run_controls(W, ra, pa, rb["nontrivial"], pb, outer)


run.run_controls = _run_controls


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path-check", action="store_true")
    args = ap.parse_args()
    freeze.require_freeze()
    if args.path_check:
        out = run.stage([0], "S1 path check", controls=True, n_relabel=0)
        target = HERE.parents[1] / "tmp" / "orbit_contrast_20261013" / "s2_path_check.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(run.jsonable(out), indent=1) + "\n", encoding="utf-8", newline="\n")
        print(f"path check written: {target}")
        return 0
    target = HERE / "RESULTS.json"
    if target.exists():
        raise SystemExit("RESULTS_ALREADY_WRITTEN: S2 is write-once")
    out = run.stage([1, 2, 3, 4], "S2 validation", controls=True, n_relabel=run.N_RELABEL)
    out["entry"] = "run_s2.py (deviation D4)"
    target.write_text(json.dumps(run.jsonable(out), indent=1) + "\n", encoding="utf-8", newline="\n")
    print("S2 written")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
