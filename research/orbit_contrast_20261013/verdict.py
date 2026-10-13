"""Apply PROTOCOL.md sections 7 and 9 mechanically to RESULTS.json (frozen before S2 runs).

File summary
- Path: research/orbit_contrast_20261013/verdict.py
- Purpose: turn the S2 result file into gate outcomes, the method verdict and the mechanism-class
  flag, with no discretion left after the outcomes are seen.
- Operational definitions fixed here before S2 (DEVIATIONS.json D3):
  - "significantly negative" = the 95% CI upper bound < 0;
  - V2 is applied to the hypothesis pipelines (A' and B non-trivial); B full is reported;
  - mechanism-class rule: Delta_id(F) > 0 with p < 0.025, F - F_-know >= 0.5 x Delta_id(F) with
    p < 0.05, and the CI lower bound of F - F_-genetic <= 0.
- Interface: `decide(results: dict, power: dict) -> dict`.
"""
from __future__ import annotations

ALPHA_H1, ALPHA_2, ALPHA_V1 = 0.025, 0.05, 0.001


def _c(block: dict, name: str) -> dict:
    return block.get("contrasts", {}).get(name) or block.get("ablations", {}).get(name) or {}


def _pass(c: dict, alpha: float) -> bool:
    return bool(c.get("difference", 0.0) > 0 and c.get("p_greater", 1.0) < alpha)


def _neg(c: dict) -> bool:
    return bool(c.get("ci95") and c["ci95"][1] < 0)


def decide(results: dict, power: dict) -> dict:
    A = results["A"]["primary_active"]
    Bn = results["B_nontrivial"]["primary_all"]
    lm = results["B_full"]["landmark"]
    sp = results["B_full"]["certificates"].get("self", {}).get("spearman_identity_gate", float("nan"))
    v1c = _c(lm, "F-(F-self)")
    v1 = _pass(v1c, ALPHA_V1) and sp > 0
    v2 = {}
    for task, block in (("A", A), ("B_nontrivial", Bn), ("B_full", results["B_full"]["primary_all"])):
        true = _c(block, "F-O").get("difference", 0.0)
        rel = results["relabel_delta_id_F"][task]
        mean_rel = sum(rel) / len(rel)
        ok = true > max(rel) and mean_rel < 0.5 * true
        v2[task] = {"true_delta_id_F": true, "relabel": rel, "pass": bool(ok), "applies": bool(true > 0) and task != "B_full"}
    h1 = {"A": _pass(_c(A, "F-O"), ALPHA_H1), "B": _pass(_c(Bn, "F-O"), ALPHA_H1)}
    h2a = {"A": _pass(_c(A, "F-R"), ALPHA_2), "B": _pass(_c(Bn, "F-R"), ALPHA_2)}
    h2b = {"A": _pass(_c(A, "F-Cp"), ALPHA_2), "B": _pass(_c(Bn, "F-Cp"), ALPHA_2)}
    neg = {"F-R": {"A": _neg(_c(A, "F-R")), "B": _neg(_c(Bn, "F-R"))},
           "F-Cp": {"A": _neg(_c(A, "F-Cp")), "B": _neg(_c(Bn, "F-Cp"))}}
    any_neg = any(v for d in neg.values() for v in d.values())
    h2_support = (any(h2a.values()) or any(h2b.values())) and not any_neg
    pw = {"A": power["A"].get("power_at_mei", 0.0), "B": power["B"].get("power_at_mei", 0.0)}
    if not v1:
        verdict = "NO_GO_INSENSITIVE"
    elif any(v["applies"] and not v["pass"] for v in v2.values()):
        verdict = "NO_GO_LEAKY"
    elif all(h1.values()) and h2_support:
        verdict = "METHOD_SUPPORTED"
    elif any(h1.values()) and not any(h2a.values()) and not any(h2b.values()):
        verdict = "IDENTITY_WITHOUT_METHOD"
    elif sum(h1.values()) == 1 and h2_support:
        verdict = "TASK_SPECIFIC"
    elif any(h1.values()):
        verdict = "IDENTITY_WITHOUT_METHOD"
    elif any(pw[t] < 0.8 for t in pw):
        verdict = "INSUFFICIENT_EVIDENCE"
    else:
        verdict = "NO_IDENTITY_VALUE"
    fo = _c(A, "F-O")
    know = _c(A, "F-(F-know)")
    gen = _c(A, "F-(F-genetic)")
    mech_only = bool(_pass(fo, ALPHA_H1) and know.get("difference", 0) >= 0.5 * fo.get("difference", 0)
                     and know.get("p_greater", 1) < ALPHA_2 and gen.get("ci95", [0, 0])[0] <= 0)
    return {"V1": {"pass": v1, "landmark_F_minus_F_without_self": v1c, "spearman_identity_gate_self": sp},
            "V2": v2, "H1": h1, "H2a": h2a, "H2b": h2b, "H2_significantly_negative": neg,
            "H3_strict_new_genetic": _c(results["A"]["strict_new_active"], "F-(F-genetic)"),
            "power_at_mei": pw, "verdict": verdict,
            "functional_genetic_claim": "MECHANISM_CLASS_ONLY" if mech_only else ("SUPPORTED" if gen.get("ci95", [0, 0])[0] > 0 else "NOT_SUPPORTED")}
