"""Assemble the dated execution receipt from machine records (no number is typed by hand)."""
from __future__ import annotations

import glob
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "log/20261010/PHENOTYPE_ANCHOR.json"


def load(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def main():
    results, gate, freeze, verified = load("RESULTS.json"), load("GATE.json"), load("FREEZE.json"), load("VERIFIED.json")
    expr = [json.loads(Path(p).read_text(encoding="utf-8")) for p in glob.glob(str(HERE / "expression/*.json"))]
    obs = [json.loads(Path(p).read_text(encoding="utf-8")) for p in glob.glob(str(HERE / "obs/*.json"))]
    state = [json.loads(Path(p).read_text(encoding="utf-8")) for p in glob.glob(str(HERE / "state_forecasts/*.json"))]
    spend_path = ROOT / "tmp/phenotype_anchor_20261010_spend.json"
    spend = json.loads(spend_path.read_text(encoding="utf-8")) if spend_path.exists() else None
    llm = [json.loads(Path(p).read_text(encoding="utf-8")) for p in glob.glob(str(HERE / "llm/*.json"))]
    e1 = results["endpoints"]["E1_survival"]
    e2 = results["endpoints"]["E2_g1"]
    body = {
        "study": "research/astra/phenotype_anchor_20261010",
        "protocol_sha256": freeze["files"]["PROTOCOL.md"],
        "frozen_utc": freeze["frozen_utc"],
        "dataset": "arcinstitute/State-Tahoe-Filtered@fdf87abece385feea6fa5e9944ab46e173b6af50",
        "checkpoint": json.loads((HERE / "STATE_STAGING.json").read_text(encoding="utf-8")),
        "reference_lines": gate["reference_lines"],
        "refused_reference_lines": gate["refused"],
        "gate": gate["gate"],
        "reference_loo_mean_r": {e: {k: v["mean_r"] for k, v in gate[e].items() if isinstance(v, dict) and "mean_r" in v} for e in ("survival", "g1")},
        "heldout_mean_r": {e: {k: v["mean_r"] for k, v in s["arms"].items()} for e, s in (("E1", e1), ("E2", e2))},
        "heldout_mean_top10_utility": {k: v["mean_top10_utility"] for k, v in e1["arms"].items()},
        "outcome_oracle_top10_utility": e1["outcome_oracle_top10_utility"],
        "tests": {e: {k: {kk: v[kk] for kk in ("mean_difference", "ci95", "lines_better", "success")} for k, v in s["tests"].items() if isinstance(v, dict)}
                  for e, s in (("E1", e1), ("E2", e2))},
        "D2": e1.get("D2"),
        "refusals": {"E1": e1["refusals"], "E2": e2["refusals"]},
        "verification": {c["check"]: c["passed"] for c in verified["checks"]},
        "resources": {
            "remote_bytes": sum(x["remote_bytes"] for x in expr) + sum(x["remote_bytes"] for x in obs),
            "remote_requests": sum(x["remote_requests"] for x in expr) + sum(x["remote_requests"] for x in obs),
            "state_forward_sets": sum(x["forward_sets"] for x in state),
            "state_seconds": sum(x["seconds"] for x in state),
            "llm_calls": len([x for x in llm if x.get("status") == "ok"]),
            "llm_usd": spend and round(sum((e.get("charged_usd") if e.get("charged_usd") is not None else e.get("reserved_usd", 0)) for e in spend.get("entries", [])), 6),
            "laboratory_credits": "simulated replay of public wells; see D2 credits per policy",
        },
        "results_sha256": hashlib.sha256((HERE / "RESULTS.json").read_bytes()).hexdigest(),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(body, indent=1, default=float), encoding="utf-8")
    print(OUT)


if __name__ == "__main__":
    main()
