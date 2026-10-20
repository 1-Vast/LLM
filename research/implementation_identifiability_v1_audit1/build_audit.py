"""Build the audit1 artefacts deterministically from audit_data.py, supplement_extracts.json, MUTATION_RESULTS.json and the v1 package.

No network. v1 files are only read. Run mutation.py first (build_audit embeds a digest of MUTATION_RESULTS.json).
"""
import copy
import hashlib
import json
import statistics
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import audit_data as ad  # noqa: E402
import audit_logic as al  # noqa: E402

import isolation  # noqa: E402  (v1, unchanged)
import logic  # noqa: E402
import records as rec  # noqa: E402
import run_g1  # noqa: E402

V1 = al.V1


def jw(path, obj):
    path.write_text(json.dumps(obj, sort_keys=True, indent=1) + "\n", encoding="utf-8", newline="\n")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def mean_sd(xs):
    return round(statistics.mean(xs), 4), round(statistics.stdev(xs), 4)


def build_records_v2(ext):
    ch = ext["values"]["S1_DS3_IMR5_TMT_AURKA_log2_reporter"]["channels"]
    arm = {"JB170": [ch[f"JB170_{i}"] for i in (1, 2, 3)], "JB211": [ch[f"JB211_{i}"] for i in (1, 2, 3)], "alisertib": [ch[f"Alisertib_{i}"] for i in (1, 2, 3, 4)]}
    kelly = {n: ext["values"][f"S2_Kelly_proteomics_AURKA_{n}"] for n in ("CCT400028", "JB170", "cmpd50")}
    out = []
    for r in rec.RECORDS:
        if r["evidence_type"] != rec.OBSERVED:
            continue
        v = copy.deepcopy(r)
        v["version"] = 2
        v["supersedes"] = r["id"]
        v["supersedes_digest"] = al.canonical_digest(r)
        v["pd_or_exposure_evidence"] = []
        v["uncertainty_model"] = "none"
        v["amendment"] = "carried over unchanged except for the added v2 fields"
        out.append(v)
    by = {r["id"]: r for r in out}
    for rid, compound in (("S1-R09", "JB170"), ("S1-R10", "JB211"), ("S1-R11", "alisertib")):
        m, s = mean_sd(arm[compound])
        by[rid].update(numeric_extracted=True, uncertainty_reported=True, uncertainty_model="test_only", evidence_grade="numeric_with_uncertainty",
                       values={"AURKA_log2_reporter_channels": arm[compound], "mean": m, "sd": s, "kind": "TMT channels in one batch, not independent biological replicates",
                               "vehicle_channel": "none in the dataset"},
                       amendment="v1 had no numbers; channel values read from SI Supp Data Set 3 (AURKA row); abundance only, says nothing about catalytic activity")
    for rid, compound in (("S2-R03", "CCT400028"), ("S2-R04", "JB170")):
        k = kelly[compound]
        by[rid].update(numeric_extracted=True, uncertainty_reported=True, uncertainty_model="test_only", evidence_grade="numeric_with_uncertainty",
                       values={"log2_channels": k["log2_channels"], "log2Ratio": k["log2Ratio"], "BH_adjusted_p": k["BH_adjusted_p"], "shared_DMSO_channels_across_three_sheets": True},
                       amendment="v1 had a direction only; channel values read from SI si_002.xlsx AURKA row; DMSO channels are shared with compound 50 and the other sheet")
    by["S2-R01"].update(uncertainty_reported=True, uncertainty_model="test_only", evidence_grade="numeric_with_uncertainty",
                        values={"pDC50_mean": 7.5, "pDC50_sem": 0.0, "Dmax_pct": 85, "Dmax_sem": 0.4, "n": 3}, amendment="SI Table S1 gives pDC50 +- SEM and n")
    by["S2-R02"].update(uncertainty_reported=True, uncertainty_model="test_only", evidence_grade="numeric_with_uncertainty",
                        values={"pDC50_mean": 7.4, "pDC50_sem": 0.2, "Dmax_pct": 69, "Dmax_sem": 2.3, "n": 5}, amendment="SI Table S1 gives pDC50 +- SEM and n=5")
    for rid in ("S1-R30", "S1-R31"):
        by[rid].update(uncertainty_model="test_only", evidence_grade="reported_qualitatively",
                       amendment="negative reading ('no significant') with t-test only; no equivalence margin, interval or detection limit, so it cannot be read as no effect")
    k = kelly["cmpd50"]
    x01 = {"id": "S2-X01", "source": "S2", "locator": "SI si_002.xlsx sheet 2, gene AURKA", "level": "proximal", "evidence_type": rec.OBSERVED, "compound": "cmpd50", "cell": "Kelly",
           "genotype": "WT", "dose_uM": 1.0, "time_h": 4, "readout": "proteomics AURKA, N-Myc, AURKB, CDK9, GSPT1", "result": {"direction": "AURKA depleted (Fig 8 text: slightly less than JB170)"},
           "n": 3, "n_kind": "independent_experiments", "numeric_extracted": True, "uncertainty_reported": True, "lineage": {"cell_stock": "not_reported", "batch": "not_reported", "plate": "not_reported"},
           "note": "new record from the SI workbook", "version": 2, "supersedes": None, "supersedes_digest": None, "pd_or_exposure_evidence": [], "uncertainty_model": "test_only",
           "evidence_grade": "numeric_with_uncertainty", "values": {"log2_channels": k["log2_channels"], "log2Ratio": k["log2Ratio"], "BH_adjusted_p": k["BH_adjusted_p"],
                                                                  "shared_DMSO_channels_across_three_sheets": True},
           "amendment": "new record; the v1 package had no compound 50 proteomics record"}
    out.append(x01)
    for r in out:
        r.setdefault("evidence_grade", al.grade_of(r))
    return out, arm


def units_v2():
    us = copy.deepcopy(rec.UNITS)
    us[2]["record_ids"] = us[2]["record_ids"] + ["S2-X01"]
    c4 = {"unit_id": "C4_KELLY_PROTEOMICS_CCT400028_JB170_50", "implementations": ["CCT400028", "JB170", "cmpd50"], "primary_terminal_endpoint": {"readout": "none", "time_h": None},
          "record_ids": ["S2-R03", "S2-R04", "S2-X01"], "discriminating_control_records": [], "genetic_reference_records": [], "mechanism_contrasts": []}
    return us + [c4]


def main():
    ext = json.loads((HERE / "supplement_extracts.json").read_text(encoding="utf-8"))
    mut = json.loads((HERE / "MUTATION_RESULTS.json").read_text(encoding="utf-8"))
    recs2, arm = build_records_v2(ext)
    (HERE / "records_v2.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in recs2), encoding="utf-8", newline="\n")

    # ---- G0 requalification ----
    us = units_v2()
    unresolved = {"U1_IMR5_AURKA_JB170_JB211_alisertib": ["P_catalytic_inhibition_by_JB211"]}
    claims = {"U1_IMR5_AURKA_JB170_JB211_alisertib": True, "U2_MV411_AURKA_JB170_alisertib": True}
    reqs = [al.requalify(u, recs2, unresolved.get(u["unit_id"], []), claims.get(u["unit_id"], False)) for u in us]
    v1_elig = json.loads((V1 / "evidence" / "eligibility.json").read_text(encoding="utf-8"))
    v1_levels = {c["unit_id"]: c["level"] for c in v1_elig["unit_classification"]}
    counts = {f"level_{k}_units": sum(1 for r in reqs if r["level"] == k) for k in (1, 2, 3, 4)}
    g0 = {
        "g0_decision": "QUALIFIED_FOR_LOGIC_TEST" if counts["level_2_units"] and not counts["level_3_units"] else ("QUALIFIED_FOR_RESEARCH_PENDING_POWER" if counts["level_3_units"] else "ASSET_BLOCKED"),
        "research_level_status": "ASSET_BLOCKED" if not counts["level_3_units"] else "UNDERPOWERED",
        "unit_levels_audit1": {r["unit_id"]: r["level"] for r in reqs}, "unit_levels_v1": v1_levels,
        "changed_vs_v1": [u for u in v1_levels if v1_levels[u] != next(r["level"] for r in reqs if r["unit_id"] == u)],
        "counts": counts, "records_level_1_annotation": len([r for r in rec.RECORDS if r["evidence_type"] == rec.ANNOTATION]),
        "requalification": reqs,
        "one_target_family": "targets 1, target families 1: insufficient for a held-out generalisation or implementation model whatever the unit levels",
    }

    # ---- G1 audit ----
    v1_metrics = json.loads((V1 / "results" / "metrics.json").read_text(encoding="utf-8"))
    legal = [a for a in rec.ACTIONS if a["outcome_in_records"]]
    with tempfile.TemporaryDirectory(prefix="idv1a_b_") as tmp:
        tr, ev = run_g1.replay(run_g1.VAULT, Path(tmp), rec.UNITS[0], legal, isolation.AccessLedger())
    v1_same = [t["stdout_sha256"] for t in tr] == [t["stdout_sha256"] for t in v1_metrics["replay_transcript"]]
    model = al.aurora_model_v2()
    menu_as_extracted = {a["action_id"]: dict(a) for a in legal}
    s0 = logic.initial_state()
    crit0 = {a: al.assay_is_discriminative(model, s0, a, e) for a, e in menu_as_extracted.items()}
    prop_a = al.propose_v2(model, s0, menu_as_extracted, set())
    # sensitivity: pretend an equivalence margin were declared; published outcomes keep their (qualitative) grades
    menu_decl = {a: dict(e, uncertainty_model="equivalence_margin") for a, e in menu_as_extracted.items()}
    gs = al.GradedState(model)
    spent, steps = set(), []
    published = {"A_T217D_RESCUE": ("rescued", "reported_qualitatively", "test_only", False), "A_JB211_VIAB": ("no_loss", "reported_qualitatively", "test_only", True)}
    for _ in range(4):
        pr = al.propose_v2(model, gs.state, menu_decl, spent)
        steps.append({"decision": pr["decision"], "compatible": pr["compatible"]})
        if not pr["decision"].startswith("measure("):
            break
        a = pr["decision"][len("measure("):-1]
        out, grade, um, neg = published[a]
        updated = gs.observe(a, out, grade, um, neg)
        spent.add(a)
        steps[-1]["released"] = {a: out, "grade": grade, "updates_compatibility": updated}
    g1 = {
        "frozen_v1_rules_unchanged": True,
        "v1_replay_rerun_identical_to_stored_hashes": v1_same,
        "v1_replay_decisions": [t["proposal"]["decision"] for t in tr],
        "checks": {
            "initial_evidence_preserves_multiple_compatible_explanations": len(logic.AURORA_EXPLANATIONS) == len(tr[0]["proposal"]["compatible"]) == 4,
            "only_a_legally_released_observation_updates_state": all(not t["observed_before"] or set(t["observed_before"]) <= set(ev.released) for t in tr),
            "hidden_outcome_does_not_change_pre_purchase_proposal": "mutation M01 (see MUTATION_RESULTS.json)",
            "retrospective_limitation": "the legal replay menu is chosen partly by outcome availability; this is not prospective policy evidence",
        },
        "strict_criteria_as_extracted": {
            "menu_declares_uncertainty_model_or_measurement_limit": any(e.get("uncertainty_model") for e in menu_as_extracted.values()),
            "per_assay_failed_criteria": {a: c["failed"] for a, c in crit0.items()},
            "step0_decision": prop_a["decision"], "compatible": prop_a["compatible"]},
        "sensitivity_with_hypothetical_equivalence_margin": {"note": "the margin is hypothetical, declared only to see how the strict update gate behaves; it is not evidence", "steps": steps,
                                                             "final_compatible": steps[-1]["compatible"], "published_outcomes_graded": {k: v[1] for k, v in published.items()}},
        "g1_engineering": "ENGINEERING_LOGIC_PASS (v1 24 tests plus audit1 tests)",
        "g1_biological": "BIOLOGICAL_DISCRIMINATION_NOT_ESTABLISHED",
        "g1_biological_reason": "no level 3 unit; JB211 catalytic activity unresolved; qualitative negative readings cannot update the compatible set under the strict gate; every assay that could separate protein loss from catalytic inhibition still lacks an outcome",
        "g2_information_value_inferred": False,
    }
    jw(HERE / "GATE_DECISIONS_AUDIT1.json", {"audit": "implementation_identifiability_v1_audit1", "G0": g0, "G1": g1,
                                              "G2": "NOT_EXECUTED", "G3": "NOT_EXECUTED", "G4": "NOT_EXECUTED", "G5": "NOT_EXECUTED"})

    # ---- JB211 premise status ----
    jb = copy.deepcopy(ad.JB211_STATUS)
    jb["wording"] = al.JB211_WORDING
    m211, s211 = mean_sd(arm["JB211"]); m170, _ = mean_sd(arm["JB170"]); mali, _ = mean_sd(arm["alisertib"])
    jb["variables"]["protein_abundance"]["evidence"] = (f"IMR5, 1 uM, 6 h TMT (SI Supp Data Set 3): AURKA log2 reporter JB211 {m211} +- {s211} (n=3), JB170 {m170} (n=3), alisertib {mali} (n=4); "
                                                         "one TMT batch, no vehicle channel; MV4-11 immunoblot: JB211 and alisertib raise AURKA (qualitative). Abundance only: it is not evidence of catalytic inhibition")
    jb["label_validator"] = {"violations_for_current_labels": al.validate_compound_labels(rec.COMPOUNDS)}
    jw(HERE / "JB211_PREMISE_STATUS.json", jb)
    jw(HERE / "CCT57_TERMINAL_STATUS.json", ad.CCT57_STATUS)

    # ---- source completion audit ----
    extracts_digest = sha(HERE / "supplement_extracts.json")
    audit = {
        "audit": "implementation_identifiability_v1_audit1", "post_hoc_audit": True, "not_preregistered": True,
        "grades_vocabulary": list(al.GRADES), "material": ad.MATERIAL_READ, "S1_items": ad.S1_ITEMS, "S2_items": ad.S2_ITEMS,
        "supplement_extracts_sha256": extracts_digest,
        "candidate_units": [dict(c, requalified_level=next(r["level"] for r in reqs if r["unit_id"] == c["unit_id"]),
                                 failed_audit1_and_v1_criteria=(next(r for r in reqs if r["unit_id"] == c["unit_id"]).get("v1_rules") or {}).get("failed", []) +
                                 next(r for r in reqs if r["unit_id"] == c["unit_id"])["failed_audit1"]) for c in ad.CANDIDATES],
        "conclusion": {
            "condition_matched_quantitatively_interpretable_lineage_qualified_unit_exists": False,
            "reasons": ["no alisertib terminal arm at the primary endpoint in S1; S2 has no inhibitor or genetic terminal comparator",
                        "terminal values for JB170 vs JB211 are qualitative and the negative reading has no equivalence margin",
                        "lineage (stock, passage, plate) unreported in both papers",
                        "JB211 catalytic inhibition unresolved; compound 57 has no terminal result",
                        "one target family"],
            "status_kept": ["G0 QUALIFIED_FOR_LOGIC_TEST", "research level ASSET_BLOCKED", "G1 biological BIOLOGICAL_DISCRIMINATION_NOT_ESTABLISHED"],
            "s1_fully_extracted": False, "s2_fully_extracted": False,
            "why_not_fully_extracted": "S1 Supp Table 1, Supp Data Sets 1 and 4 and figure-image values were not read; S2 Figure S7B values and blot images were not digitised",
        },
    }
    jw(HERE / "SOURCE_COMPLETION_AUDIT.json", audit)

    # ---- missing evidence update ----
    v1_reg = json.loads((V1 / "evidence" / "missing_evidence_register.json").read_text(encoding="utf-8"))
    status = {"G01": ("open", "no alisertib 72 h arm in S1; S2 has none"), "G02": ("open_and_split", "occupancy, exposure and catalytic activity are three separate measurements, none in read material; Supp Table 1 may hold a JB211 BRET value"),
              "G03": ("open", "siRNA cell cycle only"), "G04": ("open", "no kinase-dead replacement phenotype; kinase-dead constructs were used only for degradation"),
              "G05": ("open", "SI Fig S10 is a depletion blot; confirmed no terminal result for 57"), "G06": ("partly_addressed", "proximal numbers recovered (TMT, Kelly proteomics, HiBiT SEM); terminal numbers still missing"),
              "G07": ("open", "TMT batch and shared DMSO controls recovered; stock, passage, plate still missing"), "G08": ("open", "unchanged"),
              "G09": ("open", "unchanged"), "G10": ("open", "H_E/H_M/H_C/H_O still undefined in the repository; not used")}
    items = [dict(i, audit1_status=status[i["id"]][0], audit1_note=status[i["id"]][1]) for i in v1_reg["items"]]
    new = [
        {"id": "N01", "category": "premise_resolution", "what": "separate JB211 measurements: AURKA occupancy in cells, intracellular exposure, catalytic activity (validated substrate readout; pT288 only as context-dependent proxy)", "needed_by": ["G1"]},
        {"id": "N02", "category": "measurement_limits", "what": "equivalence margin or detection limit for every negative terminal readout, fixed before the measurement", "needed_by": ["G1"]},
        {"id": "N03", "category": "missing_necessary_control", "what": "vehicle channel for the IMR5 TMT contrast, or a vehicle arm at 6 h next to JB170, JB211 and alisertib", "needed_by": ["G0"]},
        {"id": "N04", "category": "missing_terminal_endpoint", "what": "CCT400028 with a matched inhibitor and a genetic comparator on the MV4-11 72 h viability endpoint, plus compound 57 at that endpoint", "needed_by": ["G0", "G1"]},
        {"id": "N05", "category": "missing_exposure_evidence", "what": "exposure or pharmacodynamic evidence supporting dose matching (nominal equality is not equivalence)", "needed_by": ["G0"]},
        {"id": "N06", "category": "access", "what": "S1 Supp Table 1, Supp Data Set 1 and 4 (not served by the bundle; the PMC route is gated); S1 Fig 6a,d and ED7d numeric source values (no Source Data published)", "needed_by": ["G0"]},
        {"id": "N07", "category": "rescue_controls", "what": "expression level and localisation of HA-T217D relative to endogenous AURKA, and JB170 binding to T217D", "needed_by": ["G1"]},
    ]
    jw(HERE / "MISSING_EVIDENCE_UPDATE.json", {
        "v1_items_updated": items, "new_items": new,
        "next_permitted_action": ("A person with the right to ask (the user or the paper's authors) obtains S1 Supp Table 1, Supp Data Set 1/4 and the Fig 6a,d / ED7d numeric source values with lineage metadata; "
                                  "then this audit is re-run as audit2. No modelling, no G2-G5, no new data purchase, no wet-lab work before that."),
        "forbidden_until_then": ["G2", "G3", "G4", "G5", "new Virtual Cell or world model", "paid API calls", "wet-lab work", "autonomous-discovery claims", "reopening stopped branches"]})

    # ---- manifest ----
    files = ["records_v2.jsonl", "supplement_extracts.json", "SOURCE_COMPLETION_AUDIT.json", "JB211_PREMISE_STATUS.json", "CCT57_TERMINAL_STATUS.json",
             "MISSING_EVIDENCE_UPDATE.json", "GATE_DECISIONS_AUDIT1.json", "MUTATION_RESULTS.json", "audit_logic.py", "audit_data.py", "mutation.py", "build_audit.py", "extract_supplements.py"]
    jw(HERE / "AUDIT_MANIFEST.json", {
        "audit": "implementation_identifiability_v1_audit1", "head_at_audit_start": ad.HEAD_AT_AUDIT_START, "v1_base_commit": ad.V1_BASE_COMMIT,
        "audit_package_commit": "the commit that first contains this file; resolve with: git log --diff-filter=A -1 --format=%H -- research/implementation_identifiability_v1_audit1/AUDIT_MANIFEST.json",
        "schema_version": al.SCHEMA_VERSION, "rule_version": al.RULE_VERSION, "v1_rules": "implementation_identifiability_v1/PROTOCOL.md G0 levels 1-4 and G1 definition, unchanged",
        "source_hashes": {k: {"xml_sha256": v["xml_sha256"], "pmcid": v["pmcid"]} for k, v in rec.SOURCES.items()},
        "supplement_file_sha256": {k: v["sha256"] for k, v in ext["files"].items() if not k.endswith((".gif", ".jpg"))},
        "v1_artefact_sha256": {p: sha(V1 / p) for p in ("evidence/records.jsonl", "evidence/eligibility.json", "results/gate_decisions.json", "results/metrics.json", "PROTOCOL.md", "REPORT.md")},
        "file_sha256": {f: sha(HERE / f) for f in files},
        "test_commands": ["python research/implementation_identifiability_v1/verify.py",
                          "python -m pytest research/implementation_identifiability_v1/tests/test_g0_g1.py -q -p no:cacheprovider",
                          "python research/implementation_identifiability_v1_audit1/mutation.py",
                          "python -m pytest research/implementation_identifiability_v1_audit1/tests -q -p no:cacheprovider",
                          "python research/implementation_identifiability_v1_audit1/verify.py"],
        "sources_exposed": True, "post_hoc_audit": True, "not_preregistered": True, "independent_confirmation": False,
        "actual_expenditure": {"api_calls": 0, "usd": 0.0, "data_purchases": 0, "wet_lab": 0, "free_public_downloads": "Europe PMC full text and supplementary bundles for two open-access papers (about 76 MB in total, kept outside the repository)"},
        "mutation_summary": {r["id"]: r["passed"] for r in mut["results"]},
    })
    print(json.dumps({"G0": g0["g0_decision"], "counts": counts, "v1_same": v1_same, "step0": prop_a["decision"], "sens_final": g1["sensitivity_with_hypothetical_equivalence_margin"]["final_compatible"]}, indent=1))


if __name__ == "__main__":
    main()
