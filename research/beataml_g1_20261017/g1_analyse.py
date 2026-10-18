"""Registered analysis of gate G1: per-sample totals -> RESULTS.json (pure; ``verify.py`` recomputes it).

File summary
- Path: research/beataml_g1_20261017/g1_analyse.py
- Purpose: every contrast, the gate decision and the model-versus-observation decomposition of PROTOCOL.md,
  computed from ``records/records.json`` only (no Beat AML data are read).
- Statistics: paired differences of per-sample total hits over the 16 queries; patient clusters (479
  patients, 520 samples); the frozen ``common.paired`` (cluster bootstrap 95% interval, one-sided
  sign-flip p).
- Gate (strict): ``lo - 0.05 * extra_rounds > 0.05`` for ``CAND - S_ridge`` with ``extra_rounds = 1``.
  The gross reading (``lo > 0.05``) and the net-positive reading (``lo - 0.05 * extra > 0``) are reported but
  do not decide.
- Interfaces: ``analyse(records_obj) -> dict``; ``python g1_analyse.py`` writes RESULTS.json once.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
FEEDBACK = HERE.parents[0] / "feedback_attribution_20261017"
if str(FEEDBACK) not in sys.path:
    sys.path.append(str(FEEDBACK))
from common import paired  # noqa: E402  (feedback_attribution; copied unchanged from the confirmation)

MIN_USEFUL = 0.05
ROUND_COST = 0.05
KS = (4, 8, 12)
ROUNDS = {"A_item": 1, "S_ridge": 1, "C0": 1, "RF": 2, "RF_s": 2, "E": 2, "CAND": 2,
          **{f"C_{k}": 2 for k in KS}, **{f"RF_{k}": 2 for k in KS}, **{f"RFs_{k}": 2 for k in KS}}
MAIN = ("A_item", "S_ridge", "C0", "RF", "E", "CAND")
# (name, a, b, role)
CONTRASTS = [
    ("model_without_observations", "C0", "S_ridge", "one round each"),
    ("observations_for_candidate", "CAND", "C0", "the probe round for the low-rank model"),
    ("observations_for_ridge", "RF", "S_ridge", "the same probe round for a ridge prior"),
    ("model_given_observations", "CAND", "RF", "equal two-round protocol"),
    ("candidate_vs_item_ranking", "CAND", "A_item", ""),
    ("candidate_vs_confirmed_engine", "CAND", "E", "coherent score and chosen k versus the confirmed engine"),
    ("engine_vs_ridge", "E", "S_ridge", ""),
    ("ridge_vs_item_ranking", "S_ridge", "A_item", ""),
    ("ridge_feedback_vs_item_ranking", "RF", "A_item", ""),
    ("coherent_prior_vs_item_ranking", "C0", "A_item", ""),
]


def totals(recs: list[dict], arm: str) -> np.ndarray:
    return np.array([r["t_" + arm] for r in recs], dtype=float)


def level(res: dict, extra_rounds: int) -> dict:
    lo, hi = res["ci95"]
    net_lo = lo - ROUND_COST * extra_rounds
    if lo > MIN_USEFUL:
        reading = "USEFUL_POSITIVE"
    elif lo > 0:
        reading = "POSITIVE"
    elif hi < 0:
        reading = "NEGATIVE"
    elif lo > -MIN_USEFUL and hi < MIN_USEFUL:
        reading = "WITHIN_MARGIN"
    else:
        reading = "NOT_DISTINGUISHABLE"
    return {**res, "extra_rounds": extra_rounds, "net_mean": res["mean"] - ROUND_COST * extra_rounds,
            "net_lower": net_lo, "net_lower_positive": bool(net_lo > 0), "net_lower_exceeds_min_useful": bool(net_lo > MIN_USEFUL),
            "reading": reading}


def contrast(recs: list[dict], a: str, b: str) -> dict:
    groups = [r["group"] for r in recs]
    res = paired(totals(recs, a) - totals(recs, b), groups)
    return level(res, ROUNDS[a] - ROUNDS[b])


def gate(recs: list[dict]) -> dict:
    g = contrast(recs, "CAND", "S_ridge")
    strict = bool(g["ci95"][0] - ROUND_COST * g["extra_rounds"] > MIN_USEFUL)
    return {**g, "strict_pass": strict, "gross_pass": bool(g["ci95"][0] > MIN_USEFUL), "net_positive_pass": g["net_lower_positive"],
            "rule": "lo - 0.05 * extra_rounds > 0.05 (registered, strict)",
            "decision": "G1_PASSED" if strict else "G1_FAILED_STOP_LOW_RANK_STATE_MODEL_BRANCH"}


def per_fold(recs: list[dict]) -> dict:
    out = {}
    for f in sorted({r["fold"] for r in recs}):
        sub = [r for r in recs if r["fold"] == f]
        diff = totals(sub, "CAND") - totals(sub, "S_ridge")
        out[str(f)] = {"samples": len(sub), "mean_CAND_minus_S_ridge": float(diff.mean()),
                       "k_candidate": sub[0]["k_candidate"], "k_ridge_feedback": sub[0]["k_ridge_feedback"]}
    return out


def means(recs: list[dict]) -> dict:
    arms = [a for a in ROUNDS if "t_" + a in recs[0]]
    out = {}
    for a in arms:
        row = {"mean_total_hits": float(totals(recs, a).mean()), "rounds": ROUNDS[a],
               "wasted_queries_per_sample": float(np.mean([r["w_" + a] for r in recs]))}
        if "r_" + a in recs[0]:
            k = int(a.split("_")[-1]) if a.split("_")[-1].isdigit() else None
            row["probe_readouts_returned_per_sample"] = float(np.mean([r["r_" + a] for r in recs]))
            if k:
                row["probe_return_share"] = row["probe_readouts_returned_per_sample"] / k
        out[a] = row
    return out


def classify(contrasts: dict, g: dict) -> dict:
    """Plain statements; the readings are the ones in ``level``."""

    c = contrasts
    strongest = max(("S_ridge", "C0", "A_item"), key=lambda a: c["_means"][a]["mean_total_hits"])
    feedback_arm = {"S_ridge": "observations_for_ridge", "C0": "observations_for_candidate"}.get(strongest)
    fb = c[feedback_arm] if feedback_arm else None
    out = {
        "gate": g["decision"],
        "model_without_observations": c["model_without_observations"]["reading"],
        "observations_for_candidate": c["observations_for_candidate"]["reading"],
        "observations_for_ridge": c["observations_for_ridge"]["reading"],
        "model_given_observations": c["model_given_observations"]["reading"],
        "strongest_one_round_prior": strongest,
    }
    if fb is not None:
        out["feedback_on_strongest_prior"] = ("FEEDBACK_PATTERN_RETAINED_NET_OF_ROUND" if fb["net_lower_positive"] else
                                              "NO_NET_FEEDBACK_GAIN_AT_THE_LOWER_BOUND")
    return out


def analyse(obj: dict) -> dict:
    recs = obj["records"]
    res = {"status": "DEVELOPMENT (Beat AML 2.0 is exposed; no confirmation claim)",
           "samples": len(recs), "patients": len({r["group"] for r in recs}), "constants": obj["meta"]["constants"],
           "parity": obj["meta"]["parity"], "choices": obj["meta"]["choices"]}
    res["means"] = means(recs)
    res["gate"] = gate(recs)
    contrasts = {name: {**contrast(recs, a, b), "contrast": f"{a} - {b}", "note": note} for name, a, b, note in CONTRASTS}
    res["contrasts"] = contrasts
    c0 = contrast(recs, "C0", "S_ridge")["mean"]
    c1 = contrast(recs, "CAND", "C0")["mean"]
    res["identity"] = {"CAND_minus_S_ridge": res["gate"]["mean"], "sum_of_parts": c0 + c1,
                       "holds": bool(abs(res["gate"]["mean"] - (c0 + c1)) < 1e-12)}
    res["sensitivity"] = {
        "fixed_k_against_S_ridge": {a: contrast(recs, a, "S_ridge") for a in [f"C_{k}" for k in KS] + [f"RF_{k}" for k in KS]},
        "fixed_k_candidate_minus_ridge_feedback": {str(k): contrast(recs, f"C_{k}", f"RF_{k}") for k in KS},
        "ridge_feedback_shrunk_RF_s_minus_S_ridge": contrast(recs, "RF_s", "S_ridge"),
        "candidate_minus_RF_s": contrast(recs, "CAND", "RF_s"),
        "per_fold": per_fold(recs),
        "chosen_k": {"candidate": {str(f): obj["meta"]["choices"][str(f)]["k_candidate"] for f in range(5)},
                     "ridge_feedback": {str(f): obj["meta"]["choices"][str(f)]["k_ridge_feedback"] for f in range(5)}}}
    tmp = {**contrasts, "_means": res["means"]}
    res["classification"] = classify(tmp, res["gate"])
    return res


def main() -> None:
    src = HERE / "records" / "records.json"
    out = HERE / "RESULTS.json"
    if out.exists():
        raise SystemExit("RESULTS.json exists; the registered analysis is write-once")
    obj = json.loads(src.read_text(encoding="utf-8"))
    res = analyse(obj)
    res["records_sha256"] = hashlib.sha256(src.read_bytes().replace(b"\r\n", b"\n")).hexdigest()
    out.write_bytes((json.dumps(res, indent=1, allow_nan=False) + "\n").encode("utf-8"))
    g = res["gate"]
    print(json.dumps({"CAND_minus_S_ridge": [round(g["mean"], 4), [round(x, 4) for x in g["ci95"]]],
                      "net_lower": round(g["net_lower"], 4), "decision": g["decision"]}))
    print(json.dumps(res["classification"]))


if __name__ == "__main__":
    main()
