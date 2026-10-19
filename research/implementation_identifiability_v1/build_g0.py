"""Build the G0 artifacts from records.py by the frozen rules in idlib.py. No network, no outcomes."""
import json
from pathlib import Path

import idlib
import isolation
import records as rec

HERE = Path(__file__).resolve().parent
EV = HERE / "evidence"
RES = HERE / "results"


def jl(path, rows):
    path.write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in rows), encoding="utf-8", newline="\n")


def js(path, obj):
    path.write_text(json.dumps(obj, sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")


MISSING = [
    {"id": "G01", "category": "missing_target_implementation_evidence", "what": "alisertib viability and apoptosis in IMR5 at 0.5 and 1 uM for 72 h next to JB170/JB211",
     "why": "no cell context carries inhibitor, degrader and CRBN-null binder on one terminal endpoint", "needed_by": ["G1", "G2"], "bundle": "A_ALI_VIAB"},
    {"id": "G02", "category": "missing_proximal_measurement", "what": "JB211 AURKA target engagement and catalytic inhibition (pT288, NanoBRET) at assay doses",
     "why": "reading JB211 as 'binds but does not degrade' needs it to inhibit the kinase; the text asserts binding only", "needed_by": ["G1"], "bundle": "A_JB211_ENGAGE"},
    {"id": "G03", "category": "missing_terminal_endpoint", "what": "genetic AURKA loss on viability and apoptosis in IMR5 or MV4-11 (CRISPR or siRNA with two reagents)",
     "why": "the only genetic reference is cell cycle by siRNA (ED6f-h)", "needed_by": ["G0", "G1"], "bundle": "A_AURKA_KD_VIAB"},
    {"id": "G04", "category": "missing_necessary_control", "what": "AURKA knockdown rescued by wild-type vs kinase-dead AURKA",
     "why": "T217D rescue separates on-target from off-target but not degradation from catalytic inhibition", "needed_by": ["G1"], "bundle": "A_KINASE_DEAD_REPLACE"},
    {"id": "G05", "category": "missing_necessary_control", "what": "viability and apoptosis of S2 control 57 next to CCT400028 in MV4-11 or Kelly",
     "why": "57 was tested for AURKA depletion only", "needed_by": ["G0"], "bundle": None},
    {"id": "G06", "category": "missing_numeric_values", "what": "numeric values with uncertainty for ED7d/6d (JB170 vs JB211), Fig 5a, Fig S7 curves",
     "why": "no Source Data for ED7; terminal outcomes exist as figure bars and qualitative statements", "needed_by": ["G0"], "bundle": None},
    {"id": "G07", "category": "missing_lineage", "what": "cell stock, culture initiation, treatment batch and plate for every record except the S1 TMT batch",
     "why": "dependence structure cannot be reconstructed; technical vs biological replicates are unlabeled in places", "needed_by": ["G0"], "bundle": None},
    {"id": "G08", "category": "missing_independent_validation", "what": "a second target family with a matched inhibitor / degrader / CRBN-null control trio and a shared terminal endpoint",
     "why": "all evidence is one target in one field; published cases are known-case and designer-exposed", "needed_by": ["G2", "G5"], "bundle": None},
    {"id": "G09", "category": "missing_cost_information", "what": "price, turnaround and failure rate for every bundle in the menu",
     "why": "the papers give none; costs in wells and days can be derived from design, currency cannot", "needed_by": ["G2", "G4"], "bundle": None},
    {"id": "G10", "category": "unlabeled_scope", "what": "definitions of the hypothesis categories H_E, H_M, H_C and H_O",
     "why": "not found in the repository, README, research registry or logs; study-local explanation names are used instead and no mapping is claimed", "needed_by": ["G1"], "bundle": None},
]

MINIMAL_EXPERIMENT_PACKAGE = {
    "scope": "AURKA in IMR5 (and MV4-11 if available); one cell stock per arm, vehicle on every plate; not executed, not purchased",
    "bundles": ["A_ALI_VIAB", "A_JB211_ENGAGE", "A_AURKA_KD_VIAB", "A_KINASE_DEAD_REPLACE"],
    "wells_min": sum(a["wells_min"] for a in rec.ACTIONS if a["action_id"] in {"A_ALI_VIAB", "A_JB211_ENGAGE", "A_AURKA_KD_VIAB", "A_KINASE_DEAD_REPLACE"}),
    "price_and_turnaround": "unknown; wells are design-derived (arms x 3 replicates) and technical wells per arm are unreported",
    "claim_if_executed": "would complete one qualified AURKA unit for logic and development use only; it would add no second target family",
}


def main():
    EV.mkdir(exist_ok=True)
    RES.mkdir(exist_ok=True)
    classes = [idlib.classify_unit(u, rec.RECORDS) for u in rec.UNITS]
    levels = {c["unit_id"]: c["level"] for c in classes}
    counts = idlib.effective_counts(rec.UNITS, classes, rec.COMPOUNDS, rec.RECORDS)
    graph = idlib.dependence_graph(rec.RECORDS, rec.UNITS)

    manifest = [{"kind": "source", "id": k, **v} for k, v in rec.SOURCES.items()]
    manifest += [{"kind": "compound", "id": k, **v} for k, v in rec.COMPOUNDS.items()]
    jl(EV / "manifest.jsonl", manifest)
    jl(EV / "records.jsonl", [{**r, "access_role": "evaluator" if r["id"] in isolation.HIDDEN_RECORDS else "source"} for r in rec.RECORDS])
    jl(EV / "units.jsonl", [{**u, "eligibility": next(c for c in classes if c["unit_id"] == u["unit_id"])["level_name"]} for u in rec.UNITS])
    for a in rec.ACTIONS:
        a["menu_status"] = "legal_replayable" if a["outcome_in_records"] else "proposed_missing_evidence"
    jl(EV / "actions.jsonl", rec.ACTIONS)
    js(EV / "dependence_graph.json", graph)
    js(EV / "mismatch_register.json", rec.MISMATCHES)

    any_l2 = any(l >= 2 for l in levels.values())
    any_l3 = any(l >= 3 for l in levels.values())
    if any_l3:
        decision = "QUALIFIED_FOR_RESEARCH_PENDING_POWER"
    elif any_l2:
        decision = "QUALIFIED_FOR_LOGIC_TEST"
    else:
        decision = "ASSET_BLOCKED"
    elig = {
        "G0_decision": decision,
        "research_level_assessment": {"status": "ASSET_BLOCKED" if not any_l3 else "UNDERPOWERED",
                                      "reason": "no Level 3 unit: numeric values, lineage and matched terminal endpoints are missing; one target family cannot power a held-out evaluation"},
        "levels": {"1_ANNOTATION_ONLY": [r["id"] for r in rec.RECORDS if r["evidence_type"] == rec.ANNOTATION],
                   "2_PARTIAL_PAIRED_EVIDENCE": [u for u, l in levels.items() if l == 2],
                   "3_QUALIFIED_IMPLEMENTATION_UNIT": [u for u, l in levels.items() if l == 3],
                   "4_INDEPENDENT_CONFIRMATION_UNIT": []},
        "unit_classification": classes,
        "effective_counts": counts,
        "known_case_status": {"S1": "KNOWN_CASE_LOGIC_ONLY", "S2": "KNOWN_CASE_LOGIC_ONLY"},
        "scope_of_any_future_claim": "AURKA, IMR5 and MV4-11, alisertib-derived CRBN degraders; nothing broader",
    }
    js(EV / "eligibility.json", elig)
    js(EV / "missing_evidence_register.json", {"items": MISSING, "minimal_experiment_package": MINIMAL_EXPERIMENT_PACKAGE})
    js(EV / "candidate_split_manifest.json", {
        "status": "NO_SPLIT_AUTHORISED",
        "reason": "no Level 3 unit exists, every record has been read by the designer, and one target family cannot be split into held-out families",
        "units": {u["unit_id"]: {"level": levels[u["unit_id"]], "role": "known_case_logic_only", "development_exposed": True} for u in rec.UNITS},
        "if_level3_units_are_later_built": {
            "primary_scope": "previously unseen concrete implementations of an already observed intervention mode (leave-one-implementation-out inside AURKA)",
            "separately_reported_scopes": ["unseen target family", "unseen cell context", "unseen intervention mode", "independent batch"],
            "forbidden": ["splitting wells or replicates", "model seeds as independent samples", "reuse of S1/S2 records as untouched confirmation"]},
    })
    ledger = [
        {"seq": 1, "event": "source_retrieved", "actor": "designer", "subject": "S1", "detail": {"xml_sha256": rec.SOURCES["S1"]["xml_sha256"], "outcomes_read": True}},
        {"seq": 2, "event": "source_retrieved", "actor": "designer", "subject": "S2", "detail": {"xml_sha256": rec.SOURCES["S2"]["xml_sha256"], "outcomes_read": True}},
        {"seq": 3, "event": "exposure_declared", "actor": "designer", "subject": "S1,S2", "detail": {"consequence": "all published outcomes are exposed to the study design; no Level 4 assignment is possible"}},
        {"seq": 4, "event": "pretrained_memory_risk", "actor": "designer", "subject": "S1", "detail": {"note": "AURORA-A JB170/JB211/alisertib is a published case; no LLM was run in G0/G1, so no memory test was performed; any later LLM run must not be read as rediscovery"}},
    ]
    jl(EV / "access_ledger.jsonl", ledger)
    print(decision, {u: l for u, l in levels.items()})


if __name__ == "__main__":
    main()
