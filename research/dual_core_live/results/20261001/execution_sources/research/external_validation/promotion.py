"""The hierarchical promotion rule: integrity, safety, effectiveness, benefit, replication, virtual cell.

File summary
- Path: research/external_validation/promotion.py
- Purpose: turn one tier's per-episode records into gate results and a status, exactly as
  `protocol.json` registers them, so no status can be raised by hand or by a secondary metric.
- Core points:
  - The comparator is chosen by `strongest_baseline` from the baseline pool only; MAESTRO arms, the
    permuted controls and the oracle can never be the comparator.
  - A gate either passes, rejects, or neither; the status is REJECTED on any reject condition,
    INCONCLUSIVE when a gate neither passes nor rejects, SHADOW when every development gate passes
    but external replication is unavailable, and DEFAULT_CANDIDATE only with external replication
    and the virtual-cell gate; prospective confirmation is always still required after that.
  - `overall` is the worst status across tiers.
- Depends on: statistics.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from . import statistics as S

HERE = Path(__file__).resolve().parent
SEVERITY = ("REJECTED", "INCONCLUSIVE", "SHADOW", "DEFAULT_CANDIDATE")


def protocol() -> dict:
    return json.loads((HERE / "protocol.json").read_text(encoding="utf-8"))


def arm_rates(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.groupby("policy")[["correct", "wrong", "measurements", "days"]].mean()


def strongest_baseline(frame: pd.DataFrame, spec: dict) -> str:
    """Highest correct rate under the wrong-risk cap; else highest correct - 2 wrong; ties by cost, name."""
    pool = spec["strongest_baseline_rule"]["pool"]
    rates = arm_rates(frame[frame.policy.isin(pool)])
    cap = spec["thresholds"]["wrong_risk_cap"]
    eligible = rates[rates.wrong <= cap + 1e-12]
    if len(eligible):
        ranked = sorted(eligible.itertuples(), key=lambda r: (-r.correct, r.measurements, r.Index))
    else:
        ranked = sorted(rates.itertuples(), key=lambda r: (-(r.correct - 2 * r.wrong), r.measurements, r.Index))
    return ranked[0].Index


def gates(frame: pd.DataFrame, candidate: str, comparator: str, unit: str, spec: dict, *, integrity: list,
          role: str = "development", level: float = 0.95) -> dict:
    t = spec["thresholds"]
    cap, dw, mpie, dc = t["wrong_risk_cap"], t["wrong_risk_noninferiority_margin"], t["correct_mpie"], \
        t["correct_noninferiority_margin"]
    cm, cd, cmpie = t["cost_noninferiority_margin"]["measurements"], t["cost_noninferiority_margin"]["assay_days"], \
        t["cost_mpie"]["measurements"]
    own = frame[frame.policy == candidate]
    wrong_rate = S.rate(own, "wrong", unit, level=level)
    d = {m: S.paired(frame, candidate, comparator, m, unit, level=level) for m in ("correct", "wrong", "measurements", "days")}
    out = {"candidate": candidate, "comparator": comparator, "level": level, "wrong_rate": wrong_rate, "differences": d}

    out["G1_integrity"] = {"pass": not integrity, "problems": integrity}
    out["G2_safety"] = {
        "pass": wrong_rate["ci"][1] <= cap and d["wrong"]["ci"][1] <= dw,
        "reject": wrong_rate["ci"][0] > cap or d["wrong"]["ci"][0] > dw}
    superior = d["correct"]["ci"][0] > 0 and d["correct"]["difference"] >= mpie
    noninferior = d["correct"]["ci"][0] > -dc
    out["G3_effectiveness"] = {"pass": noninferior, "superior": superior, "reject": d["correct"]["ci"][1] < -dc}
    cheaper = d["measurements"]["ci"][1] < 0 and d["measurements"]["difference"] <= -cmpie
    no_dearer = d["measurements"]["ci"][1] <= cm and d["days"]["ci"][1] <= cd
    out["G4_benefit"] = {"pass": (superior and no_dearer) or (cheaper and noninferior),
                         "route": "effectiveness" if superior and no_dearer else ("cost" if cheaper and noninferior else None)}
    out["G5_external_replication"] = {"pass": role == "external_test" and all(
        out[g]["pass"] for g in ("G1_integrity", "G2_safety", "G3_effectiveness", "G4_benefit")),
        "available": role == "external_test"}
    return out


def vc_gate(frame: pd.DataFrame, unit: str, spec: dict, *, level: float = 0.95) -> dict:
    dw = spec["thresholds"]["wrong_risk_noninferiority_margin"]
    out = {}
    for control in ("maestro_masked", "maestro_vc_permuted"):
        c = S.paired(frame, "maestro_vc", control, "correct", unit, level=level)
        w = S.paired(frame, "maestro_vc", control, "wrong", unit, level=level)
        out[control] = {"correct": c, "wrong": w, "pass": c["ci"][0] > 0 and w["ci"][1] <= dw}
    out["pass"] = all(out[c]["pass"] for c in ("maestro_masked", "maestro_vc_permuted"))
    return out


def status(result: dict, vc: dict | None = None) -> str:
    if not result["G1_integrity"]["pass"]:
        return "REJECTED"
    if result["G2_safety"]["reject"] or result["G3_effectiveness"]["reject"]:
        return "REJECTED"
    if not (result["G2_safety"]["pass"] and result["G3_effectiveness"]["pass"] and result["G4_benefit"]["pass"]):
        return "INCONCLUSIVE"
    if not result["G5_external_replication"]["pass"]:
        return "SHADOW"
    if vc is not None and not vc["pass"]:
        return "SHADOW"
    return "DEFAULT_CANDIDATE"


def overall(statuses) -> str:
    statuses = list(statuses)
    return min(statuses, key=SEVERITY.index) if statuses else "INCONCLUSIVE"
