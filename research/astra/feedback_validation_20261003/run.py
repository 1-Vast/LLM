"""Run the feedback-validation study stages and write receipts.

File summary
- Path: research/astra/feedback_validation_20261003/run.py
- Purpose: one entry point per stage:
  - `dry`: synthetic Jaaks-format release (no real data), full pipeline, for the pre-freeze check;
  - `oneil_parity`: development data (exposed O'Neil), validation call = screen call, to check
    parity of the shared arms with frozen receipts;
  - `jaaks`: the registered primary analysis; opens the vault once against the frozen protocol;
  - `almanac`: the registered exploratory re-scoring of exposed ALMANAC (second vault entry).
- Core points:
  - Outputs go to a new directory and are never overwritten (refusal if it exists).
  - Lines run in parallel worker processes; each worker receives the panels once.
  - Every stage writes lines.jsonl, manifest.json (environment, versions, hashes, seeds, timing)
    and run_log.json; the verdict is computed by the frozen `verdict.py`.
- Interfaces: `python -m research.astra.feedback_validation_20261003.run --stage S --out DIR`.
- Depends on: numpy, pandas, scikit-learn, scipy; study modules; tools.datasets.combination_screens
  (vault); research.certified_discovery (frozen).
"""
from __future__ import annotations

import argparse
import json
import os
import platform
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np

from research.certified_discovery.screens import CACHE, load_library, sha256

from . import verdict
from .study import Budget, Panel, run_line

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
PROTOCOL = HERE / "protocol"
FREEZE = PROTOCOL / "freeze.json"
VAULT_LOG = PROTOCOL / "vault_log.jsonl"
BUDGETS = {"primary": Budget(0.20, 4), "budget10": Budget(0.10, 4)}
PROTOCOL_FILE = PROTOCOL / "protocol.json"

_PANELS: dict[str, Panel] = {}


def _init(panels: dict[str, Panel]) -> None:
    global _PANELS
    _PANELS = panels


def _task(args: tuple[str, int, tuple[str, ...]]) -> dict:
    name, line, budget_names = args
    return run_line(_PANELS[name], line, {b: BUDGETS[b] for b in budget_names})


def run_panels(panels: dict[str, Panel], budget_names: tuple[str, ...], workers: int) -> list[dict]:
    tasks = [(name, line, budget_names) for name, p in panels.items() for line in range(len(p.library.lines))]
    with ProcessPoolExecutor(max_workers=workers, initializer=_init, initargs=(panels,)) as pool:
        return list(pool.map(_task, tasks))


def _environment() -> dict:
    import pandas
    import scipy
    import sklearn

    return {"python": sys.version.split()[0], "executable": sys.executable, "platform": platform.platform(),
            "numpy": np.__version__, "scipy": scipy.__version__, "sklearn": sklearn.__version__,
            "pandas": pandas.__version__}


def _write(out: Path, lines: list[dict], manifest: dict, log: list[dict]) -> None:
    with open(out / "lines.jsonl", "w", encoding="utf-8", newline="\n") as handle:
        for record in lines:
            handle.write(json.dumps(record) + "\n")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1, default=str), encoding="utf-8")
    (out / "run_log.json").write_text(json.dumps(log, indent=1), encoding="utf-8")


def _step(log: list[dict], name: str) -> dict:
    entry = {"step": name, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "status": "running"}
    log.append(entry)
    return entry


def _done(entry: dict) -> None:
    entry.update(status="done", ended=time.strftime("%Y-%m-%dT%H:%M:%S%z"))


def stage_dry(out: Path, workers: int) -> dict:
    from .jaaks import build_panels, synthetic_release

    release = synthetic_release(out / "synthetic_release.csv", seed=7)
    ticket = {"freeze_sha256": "DRY_RUN_SYNTHETIC", "data_sha256": sha256(release)}
    panels, report, candidates = build_panels(ticket, release)
    lines = run_panels(panels, tuple(BUDGETS), workers)
    return {"lines": lines, "report": report, "candidates": candidates}


def stage_oneil(out: Path, workers: int) -> dict:
    lib = load_library(CACHE / "oneil_v1.npz")
    hits = lib.y > lib.threshold
    panel = Panel("oneil2016_parity", "ONEIL", lib, hits, hits.copy(), lib.y.copy(), np.zeros(len(lib), bool),
                  np.zeros(len(lib), bool))
    lines = run_panels({"oneil": panel}, ("primary", "budget10"), workers)
    return {"lines": lines, "report": {"note": "development parity: validation call := screen call"}}


def stage_jaaks(out: Path, workers: int) -> dict:
    from tools.datasets.combination_screens import open_vault

    from .jaaks import RELEASE, RESCREEN, build_panels, rescreen_calls

    registered = json.loads(PROTOCOL_FILE.read_text(encoding="utf-8"))["registered_sha256"]
    ticket = open_vault(FREEZE, VAULT_LOG, purpose="primary: Jaaks 2022 plate-disjoint orientation-split validation",
                        source=RELEASE, root=ROOT)
    if ticket["data_sha256"] != registered["jaaks_original"]:
        raise SystemExit("DATA_MISMATCH: release digest differs from the registered digest")
    panels, report, candidates = build_panels(ticket, RELEASE)
    lines = run_panels(panels, tuple(BUDGETS), workers)
    ticket2 = open_vault(FREEZE, VAULT_LOG, purpose="secondary S11: Jaaks 2022 authors' validation rescreen",
                         source=RESCREEN, root=ROOT)
    if ticket2["data_sha256"] != registered["jaaks_rescreen"]:
        raise SystemExit("DATA_MISMATCH: rescreen digest differs from the registered digest")
    calls = rescreen_calls(ticket2, RESCREEN)
    rescreen = {(t, lo, hi, sidm): bool(h) for t, lo, hi, sidm, h in
                zip(calls["Tissue"], calls["lo"], calls["hi"], calls["SIDM"], calls["hit"])}
    return {"lines": lines, "report": report, "candidates": candidates, "tickets": [ticket, ticket2],
            "rescreen": _rescreen_summary(lines, panels, candidates, rescreen)}


def _rescreen_summary(lines, panels, candidates, rescreen) -> dict:
    out: dict = {}
    for record in lines:
        tissue = record["stratum"]
        panel = panels[f"{tissue}_{record['replicate']}"]
        cand = candidates[tissue]
        for arm, value in record["budgets"]["primary"]["arms"].items():
            runs = value if isinstance(value, list) else [value]
            slot = out.setdefault(arm, {"purchased_in_rescreen": 0.0, "rescreen_synergistic": 0.0,
                                        "screen_hits_in_rescreen": 0.0, "screen_hits_rescreen_synergistic": 0.0})
            for run in runs:
                for local in sum(run["purchases"], []):
                    row = record["rows"][local]
                    lo, hi = sorted(cand["pairs_s_v"][row])
                    sidm = cand["line_sidm"][panel.library.c[row]]
                    call = rescreen.get((tissue, lo, hi, sidm))
                    if call is None:
                        continue
                    w = 1.0 / len(runs)
                    slot["purchased_in_rescreen"] += w
                    slot["rescreen_synergistic"] += w * call
                    if panel.screen_hit[row]:
                        slot["screen_hits_in_rescreen"] += w
                        slot["screen_hits_rescreen_synergistic"] += w * call
    return out


def stage_almanac(out: Path, workers: int) -> dict:
    from tools.datasets.combination_screens import open_vault

    from .almanac_reference import build_panel
    from .reference_design import ZIP

    registered = json.loads(PROTOCOL_FILE.read_text(encoding="utf-8"))["registered_sha256"]
    ticket = open_vault(FREEZE, VAULT_LOG, purpose="exploratory E1: ALMANAC off-date single-agent reference",
                        source=ZIP, root=ROOT)
    if ticket["data_sha256"] != registered["almanac"]:
        raise SystemExit("DATA_MISMATCH: ALMANAC digest differs from the registered digest")
    panel, report = build_panel(ticket)
    lines = run_panels({"almanac": panel}, ("primary",), workers)
    import numpy as _np

    diagnostics = {}
    for record in lines:
        rows = _np.asarray(record["rows"])
        for arm, value in record["budgets"]["primary"]["arms"].items():
            runs = value if isinstance(value, list) else [value]
            slot = diagnostics.setdefault(arm, {"gap_sum": 0.0, "gap_n": 0.0})
            for run in runs:
                picked = rows[sum(run["purchases"], [])]
                gap = panel.library.y[picked] - panel.valid_y[picked]
                gap = gap[_np.isfinite(gap)]
                slot["gap_sum"] += gap.sum() / len(runs)
                slot["gap_n"] += gap.size / len(runs)
    report["mean_screen_minus_reference_label_of_purchases"] = {
        arm: v["gap_sum"] / v["gap_n"] for arm, v in diagnostics.items() if v["gap_n"]}
    return {"lines": lines, "report": report, "tickets": [ticket]}


STAGES = {"dry": stage_dry, "oneil_parity": stage_oneil, "jaaks": stage_jaaks, "almanac": stage_almanac}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--stage", choices=sorted(STAGES), required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--workers", type=int, default=16)
    args = parser.parse_args(argv)
    out = Path(args.out)
    if not out.is_absolute():
        out = HERE / out
    if out.exists():
        raise SystemExit(f"refusing to overwrite {out}")
    out.mkdir(parents=True)
    log: list[dict] = []
    entry = _step(log, f"stage_{args.stage}")
    started = time.time()
    try:
        result = STAGES[args.stage](out, args.workers)
    except Exception as error:  # record the failure, then re-raise
        entry.update(status="failed", error=repr(error), ended=time.strftime("%Y-%m-%dT%H:%M:%S%z"))
        (out / "run_log.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
        raise
    _done(entry)
    manifest = {"stage": args.stage, "started": time.strftime("%Y-%m-%dT%H:%M:%S%z", time.localtime(started)),
                "wall_seconds": round(time.time() - started, 1), "workers": args.workers,
                "environment": _environment(), "budgets": {k: vars(v) for k, v in BUDGETS.items()},
                "freeze_sha256": sha256(FREEZE) if FREEZE.exists() else None,
                "code_sha256": {p.name: sha256(p) for p in sorted(HERE.glob("*.py"))},
                "frozen_imports_sha256": {n: sha256(ROOT / "research/certified_discovery" / n)
                                          for n in ("world.py", "agent.py", "screens.py")},
                "build_report": result.get("report"), "tickets": result.get("tickets")}
    _write(out, result["lines"], manifest, log)
    for key in ("candidates", "rescreen"):
        if key in result:
            (out / f"{key}.json").write_text(json.dumps(result[key], indent=1), encoding="utf-8")
    entry = _step(log, "verdict")
    verdict.main([str(out)])
    _done(entry)
    (out / "run_log.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
    print(json.dumps({"stage": args.stage, "lines": len(result["lines"]), "wall_seconds": manifest["wall_seconds"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
