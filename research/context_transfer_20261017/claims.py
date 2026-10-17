"""Scientific-claims layer for the frozen confirmation, kept separate from its protocol verdict.

File summary
- Path: research/context_transfer_20261017/claims.py
- Purpose: the frozen `confirm.py` maps P1-P6 onto claims C1-C4 and returns `CONFIRMED`. This
  amendment, written after the run, keeps that label as the record of protocol execution and states
  what each result does and does not establish scientifically. It changes no frozen file and no
  number: every value is read from RESULTS.json, the cached per-sample records,
  POSTHOC_LOOKAHEAD_beataml.json and DEVIATIONS.json.
- Core points:
  - Three evidence levels per contrast, so a significant effect is not read as a useful one:
    `positive` (interval lower bound > 0, and the frozen Holm verdict for P1-P6),
    `exceeds_min_useful` (lower bound > the frozen 0.05 hits per sample) and `net_of_costs`
    (not evaluable: the protocol declared no conversion of an extra assay round into hits).
  - The frozen claim mapping is audited: C3 is decided by P5 non-inferiority, and C4 passes if any
    of P1, P2 or P6 passes. Neither establishes adaptivity or superiority over fixed pipelines.
  - Contrasts against `b_lookahead` use the defective `lookahead_v1` rule and are flagged.
  - Units: a "well" in the frozen files is one archived AUC query (one 7-dose response profile).
- Interfaces: `python -B claims.py` writes CLAIMS.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from common import paired

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RECORDS = ROOT / "tmp" / "context_transfer_20261017" / "confirm_records.json"
MIN_USEFUL = 0.05  # frozen in confirm.FROZEN["min_useful"]
DOSES_PER_PROFILE = 7  # Tyner et al. 2018 methods; checked against the raw inhibitor file
DEFECTIVE = "b_lookahead"


def levels(stat: dict, frozen_verdict: str | None = None) -> dict:
    lo, hi = stat["ci95"]
    positive = lo > 0 if frozen_verdict is None else frozen_verdict == "SUPPORTED"
    return {"mean": stat["mean"], "ci95": [lo, hi],
            "positive": bool(positive),
            "exceeds_min_useful": bool(lo > MIN_USEFUL),
            "net_of_costs": "NOT_EVALUABLE: no pre-declared conversion of the extra assay round into hits"}


def main() -> None:
    res = json.loads((HERE / "RESULTS.json").read_text(encoding="utf-8"))
    post = json.loads((HERE / "POSTHOC_LOOKAHEAD_beataml.json").read_text(encoding="utf-8"))
    recs = json.loads(RECORDS.read_text(encoding="utf-8"))
    prim, sec = res["primary"], res["secondary"]

    contrasts = {}
    for hid in ("P1", "P2", "P3", "P4", "P6"):
        s = prim[hid]
        row = {"contrast": s["contrast"], "frozen_verdict": s["verdict"], "p_holm": s["p_holm"],
               **levels(s, s["verdict"])}
        if DEFECTIVE in s["contrast"].split("-"):
            row["comparator_defect"] = "lookahead_v1 baseline defect (REPORT.md s5)"
        contrasts[hid] = row
    p5 = prim["P5"]
    contrasts["P5"] = {"contrast": p5["contrast"], "frozen_verdict": p5["verdict"], "mean": p5["mean"],
                       "ci95": p5["ci95"],
                       "reading": "performance floor only: the selector chose the hindsight-best fixed "
                                  "procedure (b_exploit) in 5/5 folds, so the difference is identically 0"}
    for key in ("vc0-item", "llm-maestro", "llm-b_lookahead", "maestro-maestro_yshuffle", "vc0-vc0_xshuffle",
                "b_lookahead-vc0", "b_lookahead-b_exploit"):
        row = {"contrast": key, **levels(sec[key])}
        if DEFECTIVE in key.split("-"):
            row["comparator_defect"] = "lookahead_v1 baseline defect (REPORT.md s5)"
        contrasts[key] = row
    d_item = paired(np.array([r["maestro"] - r["item"] for r in recs], float), [r["group"] for r in recs])
    contrasts["maestro-item (post hoc)"] = {
        "contrast": "maestro-item", "status": "POST_HOC: not in the frozen family; needs independent confirmation",
        **levels(d_item)}
    for key in ("b_lookahead-b_exploit", "b_lookahead-vc0"):
        s = post["contrasts"][key]
        contrasts[f"corrected {key} (post hoc)"] = {
            "contrast": key.replace("b_lookahead", "b_lookahead_corrected"), "mean": s["mean"], "ci95": s["ci95"],
            "status": "DEVELOPMENT: corrected rule written after the confirmation; equal means are not "
                      "evidence of equivalence (interval half-width about 0.06)"}

    vc0 = np.array([r["vc0"] for r in recs])
    mae = np.array([r["maestro"] for r in recs])
    per_sample = {"samples": len(recs), "patients": len({r["group"] for r in recs}),
                  "vc0_total_hits": int(vc0.sum()), "maestro_total_hits": int(mae.sum()),
                  "net_additional_events": int(mae.sum() - vc0.sum()),
                  "additional_events_per_100_samples": float(100 * (mae.sum() - vc0.sum()) / len(recs)),
                  "samples_improved": int((mae > vc0).sum()), "samples_worsened": int((mae < vc0).sum()),
                  "samples_unchanged": int((mae == vc0).sum()),
                  "wording": "about 7.3 additional replay events per 100 samples under the frozen event "
                             "definition; not 7.3% of patients benefiting and not clinical benefit"}

    claim_audit = {
        "C1_virtual_cell_transfer": {
            "frozen_rule": "P4 (vc0 - knn) SUPPORTED", "frozen_value": res["claims"]["C1_virtual_cell_transfer"],
            "scientific_reading": "the basal-expression prior beats nearest-sample transfer, but not the "
                                  "population item prior (vc0 - item -0.008 [-0.063, +0.050]); the rule does "
                                  "not test the strong baseline",
            "status": "NARROW"},
        "C2_virtual_cell_beyond_pilot_matching": {
            "frozen_rule": "P3 (maestro - match_panel) SUPPORTED",
            "frozen_value": res["claims"]["C2_virtual_cell_beyond_pilot_matching"],
            "scientific_reading": "feedback re-ranking with the model beats correlation matching on a fixed "
                                  "panel; it does not isolate the cell-state prior",
            "status": "SUPPORTED_AS_STATED"},
        "C3_agent_adaptivity": {
            "frozen_rule": "P5 non-inferiority to the best fixed procedure in hindsight",
            "frozen_value": res["claims"]["C3_agent_adaptivity"],
            "scientific_reading": "a performance floor, not adaptivity: the selector picked exploit-first "
                                  "in every fold and matched it sample by sample (P2 = 0 exactly)",
            "status": "NOT_ESTABLISHED"},
        "C4_agent_beats_fixed_pipelines": {
            "frozen_rule": "any of P1, P2, P6 SUPPORTED",
            "frozen_value": res["claims"]["C4_agent_beats_fixed_pipelines"],
            "scientific_reading": "P1 shows that exploit-first feedback beats no feedback; P2 (against the "
                                  "fixed exploit pipeline) is 0; P6 beats a defective comparator, which "
                                  "documents defect detection and rejection, not a method advantage",
            "status": "NOT_ESTABLISHED"},
        "min_useful": {
            "frozen_rule": "verdict() returns SUPPORTED when Holm p < alpha and the lower bound > 0; "
                           "min_useful = 0.05 only separates NOT_SUPPORTED from INCONCLUSIVE",
            "consequence": "SUPPORTED means any positive gain; P1's lower bound (0.025) does not show a gain "
                           "above 0.05. Future protocols report the three levels separately."},
    }

    scientific_claims = {
        "protocol_execution": {"status": "CONFIRMED (historical label, retained)",
                               "meaning": "the frozen decision rules returned CONFIRMED on the one-shot run"},
        "functional_feedback_gain": {
            "status": "SUPPORTED_UNDER_REPLAY",
            "evidence": "P1 +0.073 [+0.025, +0.127]; readouts from another patient lose 0.104",
            "limits": "archive-query replay; positive, not shown above min_useful; no net-of-cost claim"},
        "cell_state_model_beyond_population_prior": {
            "status": "NOT_ESTABLISHED", "evidence": "vc0 - item -0.008 [-0.063, +0.050]"},
        "procedure_selection_gain": {
            "status": "NOT_ESTABLISHED", "evidence": "P2 = 0; P5 trivially non-inferior; same procedure in 5/5 folds"},
        "llm_gain": {"status": "NOT_ESTABLISHED",
                     "evidence": "llm - maestro -0.015 [-0.050, +0.010]; its registered criterion was met "
                                 "only against the defective lookahead_v1"},
        "repaired_planner": {"status": "DEVELOPMENT",
                             "evidence": "corrected lookahead - exploit 0.000 [-0.061, +0.064], post hoc on "
                                         "exposed data; does not inherit the confirmation"},
        "total_cost_advantage": {"status": "NOT_ESTABLISHED",
                                 "evidence": "equal query counts, but bridged arms need a second assay round "
                                             "(about 72 h more); see units"},
        "transfer_type": {"status": "WORKFLOW_TRANSFER",
                          "meaning": "every outer fold refits drug means, loadings, the expression map, "
                                     "thresholds, rank and procedure on Beat AML source patients; the "
                                     "result shows an algorithm developed on PRISM applied within Beat AML, "
                                     "not biological knowledge carried from PRISM"},
    }

    budget = res["frozen"]["budget"]
    units = {
        "frozen_term": "well",
        "meaning": "one archived probit AUC summary for a (sample, inhibitor) pair = one drug-response query",
        "queries_per_sample": budget,
        "physical_profile": f"{DOSES_PER_PROFILE}-point 3-fold dilution, one well per concentration, 72 h, MTS "
                            "(Tyner et al. 2018); controls (DMSO vehicle, positive-control combination) per plate",
        "treatment_wells_per_sample_if_replicated": budget * DOSES_PER_PROFILE,
        "treatment_wells_note": "16 profiles x 7 doses = 112 treatment wells before controls and replicates; "
                                "equal for every arm, so paired comparisons are unaffected",
        "assay_rounds": res["costs"]["assay_rounds"],
        "extra_round": "about 72 h of culture plus re-plating; the replay assumes the banked sample keeps the "
                       "same response state between rounds, which it cannot test",
        "rna_timing": "basal RNA is pre-treatment; the replay assumes it is analysed before the first selection",
        "api_usd": {"confirmation_llm_arm": res["llm_spend"]["usd_upper_bound"], "pilot": 0.0156},
        "wet_lab_wells_purchased": res["costs"]["wet_lab_wells_purchased"],
    }

    out = {"study": "context_transfer_20261017", "kind": "post-run scientific-claims amendment",
           "changes_frozen_results": False,
           "strongest_wording": ("Under the defined Beat AML replay endpoint and query budget, querying a small "
                                 "number of high-scoring inhibitors and using their measured responses to "
                                 "update a low-rank model improved subsequent candidate selection. The "
                                 "incremental value of the research-procedure selector and LLM has not been "
                                 "established."),
           "scientific_claims": scientific_claims, "claim_mapping_audit": claim_audit,
           "contrasts": contrasts, "per_sample": per_sample, "units": units,
           "process_report_deviation": "DEVIATIONS.json entry 2 (maestro wasted wells 4.81 -> 2.53)"}
    (HERE / "CLAIMS.json").write_bytes((json.dumps(out, indent=1) + "\n").encode("utf-8"))
    print(json.dumps({k: v["status"] for k, v in scientific_claims.items()}, indent=1))
    print(json.dumps(per_sample, indent=1))


if __name__ == "__main__":
    main()
