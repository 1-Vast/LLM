"""Run G1: design-level identifiability chain, isolated replay on the legal menu, gate decisions."""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import idlib
import isolation
import logic
import records as rec

HERE = Path(__file__).resolve().parent
RES = HERE / "results"

VAULT = {
    "outcomes": {
        "A_JB211_VIAB": {"outcome": "no_loss", "source_records": ["S1-R30", "S1-R31"],
                         "strength": "absence of significance with n=3; effect size not extracted"},
        "A_T217D_RESCUE": {"outcome": "rescued", "source_records": ["S1-R29"],
                           "strength": "qualitative statement and figure bars; no source data"},
    },
    "canary": "CANARY-7f3a9c-DO-NOT-LEAK",
}


def jl(path, rows):
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8", newline="\n")


def replay(vault, scratch, unit, menu, ledger):
    """Isolated pre-purchase proposals, one legal release at a time. Returns the transcript."""
    views = scratch / "views"
    isolation.build_views(views, rec.RECORDS, menu, unit, ledger)
    ev = isolation.Evaluator(vault, ledger)
    observed, premises, transcript = {}, {}, []
    for step in range(len(menu) + 1):
        out = isolation.run_policy_isolated(scratch, views / "query", views / "source", observed, premises)
        prop = out["proposal"]
        transcript.append({"step": step, "observed_before": dict(observed), "stdout_sha256": out["stdout_sha256"], "proposal": prop,
                           "tree_files": out["tree_files"]})
        if not prop["decision"].startswith("measure("):
            break
        action = prop["decision"][len("measure("):-1]
        wells = next(a["wells_min"] for a in menu if a["action_id"] == action)
        got = ev.purchase(action, wells)
        observed[action] = got["outcome"]
    return transcript, ev


def main():
    RES.mkdir(exist_ok=True)
    model = logic.aurora_model()
    unit = rec.UNITS[0]
    full_menu = rec.ACTIONS
    legal_menu = [a for a in rec.ACTIONS if a["outcome_in_records"]]

    # 1. design level: explanations compatible with the initial evidence and chains that separate them
    s0 = logic.initial_state()
    design_chain = logic.identifiability_chain(model, s0, full_menu)
    legal_chain = logic.identifiability_chain(model, s0, legal_menu)
    reports = {a["action_id"]: logic.assay_report(model, s0, a["action_id"]) for a in full_menu}
    # the contrast that decides the implementation question: degradation vs catalytic inhibition, after the
    # on-target rescue has removed the off-target explanations
    s1 = model.apply(s0, "A_T217D_RESCUE", "rescued")
    design_chain_pair = logic.identifiability_chain(model, s1, [a for a in full_menu if a["action_id"] != "A_T217D_RESCUE"])
    legal_chain_pair = logic.identifiability_chain(model, s1, [a for a in legal_menu if a["action_id"] != "A_T217D_RESCUE"])

    # 2. replay on the legal menu with hidden published outcomes (isolated)
    ledger = isolation.AccessLedger()
    with tempfile.TemporaryDirectory(prefix="idv1_run_") as tmp:
        transcript, ev = replay(VAULT, Path(tmp), unit, legal_menu, ledger)
    final = transcript[-1]["proposal"]
    # the state reached after the legal purchases, evaluated on the full model for the missing-assay analysis
    st = logic.initial_state(ev.released)
    S_after = model.compatible(st)
    post = logic.propose(model, st, full_menu, set(ev.released))

    simulated = [{"ledger": "simulated_acquisition", "action_id": a, "wells": next(x["wells_min"] for x in legal_menu if x["action_id"] == a),
                  "status": "archived outcome released by evaluator; no wet-lab work done"} for a in ev.released]
    actual = [
        {"ledger": "actual_expenditure", "item": "europe_pmc_fulltext_xml_S1", "bytes": 195106, "usd": 0.0},
        {"ledger": "actual_expenditure", "item": "europe_pmc_fulltext_xml_S2", "bytes": 213356, "usd": 0.0},
        {"ledger": "actual_expenditure", "item": "llm_api_calls_in_study_code", "calls": 0, "usd": 0.0},
        {"ledger": "actual_expenditure", "item": "wet_lab_or_purchased_data", "usd": 0.0},
    ]
    jl(RES / "cost_ledger.jsonl", actual + simulated)
    jl(HERE / "evidence" / "replay_access_ledger.jsonl", ledger.events)

    l2 = json.loads((HERE / "evidence" / "eligibility.json").read_text(encoding="utf-8"))
    unit_level = next(c["level"] for c in l2["unit_classification"] if c["unit_id"] == unit["unit_id"])
    chain_ok = design_chain["chain_exists"] and design_chain_pair["chain_exists"]
    realised = len(S_after) == 1
    criterion_9_4 = chain_ok and unit_level >= 3 and realised

    proc = subprocess.run([sys.executable, "-m", "pytest", str(HERE / "tests"), "-q", "-p", "no:cacheprovider"], capture_output=True, text=True, cwd=HERE)
    eng = "ENGINEERING_LOGIC_PASS" if proc.returncode == 0 else "ENGINEERING_LOGIC_FAIL"
    g1 = {
        "engineering": eng,
        "engineering_tests_tail": proc.stdout.strip().splitlines()[-1] if proc.stdout.strip() else proc.stderr[-300:],
        "engineering_basis": "isolation, binding, premise handling, non-identifiability and ledger tests in tests/ (see verify.py level 1)",
        "biological": "BIOLOGICAL_DISCRIMINATION_NOT_ESTABLISHED",
        "biological_basis": [
            "design-level chain exists (T217D rescue and JB211 viability separate explanations that map to different decisions) but no Level 3 unit supports it",
            "with the legal replayable menu the compatible set stays {EX_PROTEIN_LOSS_SCAFFOLD, EX_CATALYTIC_INHIBITION}: JB211 cannot be read without a catalytic-engagement premise that no record resolves",
            "every assay that would separate degradation from catalytic inhibition (A_JB211_ENGAGE, A_KINASE_DEAD_REPLACE, A_ALI_VIAB) has no published outcome",
            "published JB211 and T217D results are qualitative (absence of significance, n=3); contrast against noise is not assessable",
            "known-case, designer-exposed and likely in pretrained memory; not independent confirmation",
        ],
        "section_9_4_criterion_met": criterion_9_4,
        "section_9_4_detail": {"design_level_chain_exists": chain_ok, "legal_menu_chain_exists_one_sided": legal_chain_pair["chain_exists"],
                               "legal_menu_resolves_degradation_vs_catalytic_with_recorded_outcomes": realised, "unit_level": unit_level,
                               "required_unit_level": 3},
        "partial_biological_findings": {
            "recorded_published_direction": {"A_T217D_RESCUE": "rescued", "A_JB211_VIAB": "no_loss"},
            "compatible_after_legal_purchases": sorted(S_after),
            "eliminated_by_recorded_results": sorted(set(model.explanations) - S_after),
            "interpretation": "recorded results are compatible with scaffold-type loss or with catalytic inhibition if JB211 does not inhibit; off-target explanations are refuted only at known-case qualitative level",
        },
    }
    decisions = {
        "reference_date": "2026-10-19",
        "G0": {"decision": l2["G0_decision"], "research_level": l2["research_level_assessment"], "counts": l2["effective_counts"]},
        "G1": g1,
        "G2": "NOT_EXECUTED", "G3": "NOT_EXECUTED", "G4": "NOT_EXECUTED", "G5": "NOT_EXECUTED_REQUIRES_SEPARATE_QUALIFICATION",
        "G1_does_not_imply_G2": True,
        "recommendation": "CONTINUE_ONLY_AT_KNOWN_CASE_LOGIC_LEVEL_AND_COLLECT_SPECIFIED_MISSING_EVIDENCE",
    }
    metrics = {
        "initial_compatible_explanations": design_chain["compatible"],
        "design_chain": design_chain["chains"],
        "legal_menu_chain": legal_chain["chains"],
        "pair_chain_after_rescue_design": design_chain_pair["chains"],
        "pair_chain_after_rescue_legal_menu": legal_chain_pair["chains"],
        "assay_reports_initial": {k: {"separated_pairs": v["separated_pairs"], "changes_terminal_decision": v["changes_terminal_decision"],
                                      "terminal_label_by_outcome": v["terminal_label_by_outcome"]} for k, v in reports.items()},
        "replay_transcript": [{"step": t["step"], "observed_before": t["observed_before"], "decision": t["proposal"]["decision"],
                               "compatible": t["proposal"]["compatible"], "stdout_sha256": t["stdout_sha256"]} for t in transcript],
        "replay_final": final,
        "after_legal_purchases_full_model_proposal": post,
        "simulated_wells_spent": sum(s["wells"] for s in simulated),
        "assay_noise_assessment": "not_assessable_from_records: no effect sizes or variances extracted for the JB211 or T217D panels",
        "probabilities": "none computed; the records support no outcome probabilities",
    }
    (RES / "gate_decisions.json").write_text(json.dumps(decisions, sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
    (RES / "metrics.json").write_text(json.dumps(metrics, sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"G0": decisions["G0"]["decision"], "G1_eng": g1["engineering"], "G1_bio": g1["biological"], "final": final["decision"],
                      "design_chains": [c["action_id"] for c in design_chain["chains"]], "legal_chains": [c["action_id"] for c in legal_chain["chains"]],
                      "S_after": sorted(S_after), "post": post["decision"]}, indent=1))


if __name__ == "__main__":
    main()
