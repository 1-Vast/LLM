"""WS3 deterministic rerun of the frozen replay with purchase capture (exploratory, read-only on frozen code).

File summary
- Path: research/astra/feedback_validation_20261003/workstreams/ws3_certification_costs/rerun_capture.py
- Purpose: the frozen receipts record counts only (no purchased ids, no shortlist scores), so the
  cost of the certify branch and the design-based FDR given each real shortlist cannot be
  computed from them. This script reruns the FROZEN replay code (research.certified_discovery,
  digests checked against protocol/freeze.json first) with in-process wrappers that record,
  for every campaign: the shared purchases, the exploit pick, the shortlist, its scores and
  labels, and each audit draw. It then checks that the rerun reproduces every frozen receipt.
- Core points:
  - Wrappers only observe: `agent._top`, `MenuRandomArm.choose` and `cert.certify` are wrapped
    and return exactly what the originals return. No frozen file is edited.
  - ALMANAC outcomes were opened once at 17:58:48; this rerun is exposed, exploratory analysis.
  - Output: capture_<screen>.npz/.json next to this file (never inside research/certified_discovery).
- Run: D:/anaconda/envs/maestro/python.exe research/astra/feedback_validation_20261003/workstreams/ws3_certification_costs/rerun_capture.py
"""
from __future__ import annotations

import hashlib
import json
import os
import pickle
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict
from pathlib import Path

for _v in ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS"):
    os.environ.setdefault(_v, "1")

import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
sys.path.insert(0, str(ROOT))

from research.certified_discovery import agent, replay  # noqa: E402
from research.certified_discovery import certify as cert  # noqa: E402
from research.certified_discovery.screens import CACHE, load_library  # noqa: E402

FROZEN = ROOT / "research/certified_discovery"
SCREENS = {
    "oneil": {"library": CACHE / "oneil_v1.npz", "receipts": [FROZEN / "results/dev_20261003_v2/campaigns.jsonl"],
              "spec": {"kappa": 2}},
    "almanac": {"library": CACHE / "almanac_v1.npz", "receipts": [FROZEN / "results/confirm_almanac_20261003/replay/campaigns.jsonl"],
                "spec": {"budget_fraction": 0.1, "rounds": 4, "kappa": 2, "alpha": 0.2, "delta": 0.1,
                         "audit_seeds": 20, "wells_per_point": 1}},
}


def check_freeze() -> list[str]:
    freeze = json.loads((FROZEN / "protocol/freeze.json").read_text(encoding="utf-8"))
    bad = []
    for name, digest in freeze["files"].items():
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != digest:
            bad.append(name)
    return bad


_CAPTURE: dict | None = None
_orig_top = agent._top
_orig_choose = agent.MenuRandomArm.choose
_orig_run = agent.run_campaign


def _top(scores, available, k, rng):
    out = _orig_top(scores, available, k, rng)
    if _CAPTURE is not None:
        _CAPTURE["top"].append(np.asarray(out).copy())
    return out


def _choose(self, available, measured, values, k):
    out = _orig_choose(self, available, measured, values, k)
    if _CAPTURE is not None:
        _CAPTURE["choose"].append(np.asarray(out).copy())
    return out


class _CertProxy:
    draw_audit = staticmethod(cert.draw_audit)

    @staticmethod
    def certify(shortlist, scores, audit, audit_hits, *, alpha, delta):
        out = cert.certify(shortlist, scores, audit, audit_hits, alpha=alpha, delta=delta)
        if _CAPTURE is not None:
            if _CAPTURE.get("shortlist") is None:
                _CAPTURE["shortlist"] = np.asarray(shortlist).copy()
                _CAPTURE["scores"] = np.asarray(scores, float).copy()
            _CAPTURE["audits"].append(np.asarray(audit).copy())
            _CAPTURE["nominated"].append(np.asarray(out.nominated).copy())
        return out

    def __getattr__(self, name):
        return getattr(cert, name)


def _run(lib, world, arm, spec, seed):
    global _CAPTURE
    _CAPTURE = {"top": [], "choose": [], "audits": [], "nominated": [], "shortlist": None}
    record = _orig_run(lib, world, arm, spec, seed)
    cap, _CAPTURE = _CAPTURE, None
    rows = world.rows
    planner = cap["choose"]
    if planner:
        shared, exploit = planner[: spec.rounds - 1], planner[spec.rounds - 1]
    else:
        shared, exploit = cap["top"][: spec.rounds - 1], cap["top"][spec.rounds - 1]
    measured = np.concatenate(shared) if shared else np.zeros(0, int)
    cost = lib.cost_points[rows].astype(np.int64)
    exploit = np.asarray(exploit, int)
    shortlist = cap["shortlist"].astype(int)
    audits = [np.asarray(a, int) for a in cap["audits"]]
    record["_ws3"] = {
        "shared_points": int(cost[measured].sum()), "shared_n": int(measured.size),
        "exploit_points": int(cost[exploit].sum()), "exploit_n": int(exploit.size),
        "audit_points": [int(cost[a].sum()) for a in audits], "audit_n": [int(a.size) for a in audits],
        "audit_exploit_overlap": [int(np.intersect1d(a, exploit).size) for a in audits],
        "exploit_in_shortlist": int(np.intersect1d(exploit, shortlist).size),
        "nominated_points": [int(cost[np.asarray(n, int)].sum()) for n in cap["nominated"]],
        "shortlist": shortlist.astype(np.int32), "scores": cap["scores"],
        "shortlist_hits": (lib.y[rows][shortlist] > lib.threshold),
        "audits": np.stack(audits).astype(np.int32),
        "score_ties_in_shortlist": int(shortlist.size - np.unique(cap["scores"]).size),
    }
    return record


def _install():
    agent._top = _top
    agent.MenuRandomArm.choose = _choose
    agent.cert = _CertProxy()
    agent.run_campaign = _run


def run_line(task):
    _install()
    return replay.run_line(task)


def key(record) -> tuple:
    return (record["arm"], record["line"], record["seed"])


def compare(rerun: list[dict], receipts: list[dict]) -> dict:
    frozen = {key(r): r for r in receipts}
    fields = ["nominated", "nominated_true", "yield_bound", "audit_hits", "remainder_hits", "hits", "refusal", "shortlist", "audit"]
    mismatched, missing = [], 0
    for r in rerun:
        f = frozen.get(key(r))
        if f is None:
            missing += 1
            continue
        same = (r["exploit"] == f["exploit"] and r["dose_points"] == f["dose_points"] and len(r["certify"]) == len(f["certify"])
                and all(a[k] == b[k] for a, b in zip(r["certify"], f["certify"]) for k in fields))
        if not same:
            mismatched.append(list(key(r)))
    return {"rerun_records": len(rerun), "frozen_records": len(frozen), "missing": missing,
            "mismatched": len(mismatched), "mismatched_examples": mismatched[:10]}


def main() -> int:
    bad = check_freeze()
    if bad:
        raise SystemExit(f"frozen digests changed: {bad}")
    summary = {"freeze_intact": True, "screens": {}}
    for screen, cfg in SCREENS.items():
        lib = load_library(cfg["library"])
        spec = agent.CampaignSpec(**cfg["spec"])
        tasks = [(str(cfg["library"]), line, asdict(spec), replay.ARMS, {}) for line in range(len(lib.lines))]
        started = time.time()
        with ProcessPoolExecutor(max_workers=20) as pool:
            records = [r for batch in pool.map(run_line, tasks) for r in batch]
        receipts = [json.loads(l) for path in cfg["receipts"] for l in open(path, encoding="utf-8")]
        check = compare(records, receipts)
        check["wall_seconds"] = round(time.time() - started, 1)
        summary["screens"][screen] = check
        with open(HERE / f"capture_{screen}.pkl", "wb") as handle:
            pickle.dump([{k: v for k, v in r.items() if k not in ("eb", "world")} for r in records], handle)
        print(screen, json.dumps(check), flush=True)
    (HERE / "rerun_capture.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
