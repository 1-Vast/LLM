"""Reproducible mutation checks. Each mutation states its expected behaviour before it is applied.

Run: python mutation.py   (writes MUTATION_RESULTS.json; exit code 1 when any expectation fails).
A failed expectation is a finding about the package, not something to hide: it is recorded as such.
"""
import copy
import json
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import audit_logic as al  # noqa: E402  (also puts the v1 directory on sys.path)

import idlib  # noqa: E402
import isolation  # noqa: E402
import logic  # noqa: E402
import records as rec  # noqa: E402
import run_g1  # noqa: E402

LEGAL = [a for a in rec.ACTIONS if a["outcome_in_records"]]
U1 = rec.UNITS[0]


def _classify(records, unit=U1):
    return idlib.classify_unit(unit, records)


def _vault(jb, t17):
    return {"outcomes": {"A_JB211_VIAB": {"outcome": jb}, "A_T217D_RESCUE": {"outcome": t17}}, "canary": "CANARY-MUT"}


def m01_hidden_outcomes():
    out = {}
    for tag, (jb, t) in {"published": ("no_loss", "rescued"), "flipped": ("loss", "not_rescued")}.items():
        with tempfile.TemporaryDirectory(prefix="idv1a_") as tmp:
            tr, _ = run_g1.replay(_vault(jb, t), Path(tmp), U1, LEGAL, isolation.AccessLedger())
        out[tag] = tr
    step0_same = out["published"][0]["stdout_sha256"] == out["flipped"][0]["stdout_sha256"]
    final_differs = out["published"][-1]["proposal"]["decision"] != out["flipped"][-1]["proposal"]["decision"]
    return {"expected": "pre-purchase (step 0) proposal byte-identical; behaviour differs only after a legal release",
            "observed": {"step0_identical": step0_same, "post_release_final_differs": final_differs,
                         "final_published": out["published"][-1]["proposal"]["decision"], "final_flipped": out["flipped"][-1]["proposal"]["decision"]},
            "passed": step0_same and final_differs}


def m02_condition_identity():
    by = {r["id"]: r for r in rec.RECORDS}
    base = idlib.bind_conditions(by["S1-R31"], by["S1-R32"])
    res = {"baseline": base["mode"]}
    ok = base["mode"] == "strict"
    for field, val, want in (("cell", "MV4-11", "refused"), ("time_h", 48, "refused"), ("readout", "other readout", "refused"), ("dose_uM", "0.25;0.5", "descriptive"),
                             ("genotype", "AURKA_T217D_Dox", "refused")):
        mut = dict(by["S1-R32"]); mut[field] = val
        got = idlib.bind_conditions(by["S1-R31"], mut)
        res[field] = got["mode"]
        ok &= got["mode"] == want
    recs = [dict(r, cell="MV4-11") if r["id"] == "S1-R32" else r for r in rec.RECORDS]
    cl = _classify(recs)
    base_cl = _classify(rec.RECORDS)
    res["unit_level_after_cell_change"] = cl["level"]
    ok &= cl["level"] <= base_cl["level"] and len(cl["terminal_pairs"]) < len(base_cl["terminal_pairs"])
    return {"expected": "mismatched cell, time, readout or genotype refused; dose difference descriptive only; unit never rises", "observed": res, "passed": bool(ok)}


def m03_relabel_jb211():
    comp = copy.deepcopy(rec.COMPOUNDS)
    base = al.validate_compound_labels(comp)
    comp["JB211"]["mode"] = "inactive_control"
    comp["JB211"]["note"] = "inactive control"
    v1 = al.validate_compound_labels(comp)
    comp2 = copy.deepcopy(rec.COMPOUNDS)
    comp2["JB211"]["catalytic_inhibition_assumed"] = True
    v2 = al.validate_compound_labels(comp2)
    return {"expected": "validator clean for the real labels; violations when JB211 is called inactive or assumed to inhibit",
            "observed": {"baseline_violations": base, "relabelled_violations": v1, "assumed_inhibition_violations": v2},
            "passed": base == [] and len(v1) >= 1 and len(v2) == 1}


def m04_remove_catalytic_evidence():
    m = al.aurora_model_v2()

    def run(with_activity):
        g = al.GradedState(m)
        g.observe("A_T217D_RESCUE", "rescued", "numeric_with_uncertainty", "interval")
        if with_activity:
            g.observe("A_JB211_ACTIVITY", "inhibited", "numeric_with_uncertainty", "interval")
        g.observe("A_JB211_VIAB", "no_loss", "numeric_with_uncertainty", "equivalence_margin", negative=True)
        return sorted(g.compatible())

    with_ev, without_ev = run(True), run(False)
    return {"expected": "with catalytic-activity evidence EX_CATALYTIC_INHIBITION is refuted by JB211 no_loss; without it, it stays compatible",
            "observed": {"with_activity_evidence": with_ev, "without_activity_evidence": without_ev},
            "passed": logic.EX_CAT not in with_ev and logic.EX_CAT in without_ev}


def m05_duplicate_wells():
    recs = copy.deepcopy(rec.RECORDS)
    dups = [dict(r, id=r["id"] + "-dup", n=(r["n"] or 1) * 10) for r in rec.RECORDS if r["id"] in U1["record_ids"]]
    unit = dict(U1, record_ids=U1["record_ids"] + [d["id"] for d in dups])
    allrecs = recs + dups
    base_cl, mut_cl = _classify(rec.RECORDS), idlib.classify_unit(unit, allrecs)
    base_cnt = idlib.effective_counts(rec.UNITS, [idlib.classify_unit(u, rec.RECORDS) for u in rec.UNITS], rec.COMPOUNDS, rec.RECORDS)
    mut_units = [unit] + rec.UNITS[1:]
    mut_cnt = idlib.effective_counts(mut_units, [idlib.classify_unit(u, allrecs) for u in mut_units], rec.COMPOUNDS, allrecs)
    keys = ("targets", "target_families", "implementations_with_terminal_records", "modes_of_action_with_terminal_records",
            "cell_backgrounds_with_terminal_records", "independent_source_families", "level3_or_higher_units")
    counts_same = all(base_cnt[k] == mut_cnt[k] for k in keys)
    v1_double = idlib.cost_total(rec.ACTIONS, ["A_T217D_RESCUE", "A_T217D_RESCUE"])["wells"]
    unique = al.cost_total_unique(rec.ACTIONS, ["A_T217D_RESCUE", "A_T217D_RESCUE"])["wells"]
    return {"expected": "level and effective counts unchanged; a duplicated bundle is costed once",
            "observed": {"level_same": base_cl["level"] == mut_cl["level"], "effective_counts_same": counts_same,
                         "v1_idlib_cost_total_wells_for_duplicate_bundle": v1_double, "audit_cost_total_unique_wells": unique,
                         "finding": "v1 idlib.cost_total double counts a duplicated bundle id; the Evaluator refuses repeat purchases so replay is unaffected; the audit uses cost_total_unique"},
            "passed": base_cl["level"] == mut_cl["level"] and counts_same and unique == 18 and v1_double == 36}


def m06_remove_proximal():
    drop = {r["id"] for r in rec.RECORDS if r["id"] in U1["record_ids"] and r["level"] == "proximal"}
    recs = [r for r in rec.RECORDS if r["id"] not in drop]
    unit = dict(U1, record_ids=[i for i in U1["record_ids"] if i not in drop])
    try:
        idlib.classify_unit(U1, recs)
        dangling = "accepted"
    except KeyError:
        dangling = "refused (fail-closed)"
    cl, base = _classify(recs, unit), _classify(rec.RECORDS)
    return {"expected": "L3b fails (it already passes at baseline) and the level cannot rise",
            "observed": {"baseline_L3b": base["criteria"]["L3b_all_implementations_share_strict_proximal_readout"],
                         "mutated_L3b": cl["criteria"]["L3b_all_implementations_share_strict_proximal_readout"], "level": cl["level"],
                         "dangling_reference_to_removed_records": dangling},
            "passed": base["criteria"]["L3b_all_implementations_share_strict_proximal_readout"] and not cl["criteria"]["L3b_all_implementations_share_strict_proximal_readout"] and cl["level"] <= base["level"] and dangling.startswith("refused")}


def m07_identical_predictions():
    m = al.aurora_model_v2()
    for a, spec in m.assays.items():
        if "pred" in spec:
            allowed = set(m.outcomes[a])
            spec["pred"] = {e: ({True: allowed, False: allowed} if "premise" in spec else allowed) for e in m.explanations}
    menu = {a["action_id"]: dict(a, uncertainty_model="equivalence_margin") for a in LEGAL}
    prop = al.propose_v2(m, logic.initial_state(), menu, set())
    return {"expected": "no assay separates anything; proposal is still_indistinguishable", "observed": prop["decision"],
            "passed": prop["decision"] == al.INDISTINGUISHABLE and prop["ranking"] == []}


def m08_no_decision_consequence():
    m = al.aurora_model_v2()
    m.terminal = lambda S: "same_decision"
    menu = {a["action_id"]: dict(a, uncertainty_model="equivalence_margin") for a in LEGAL}
    rep = {a: al.assay_is_discriminative(m, logic.initial_state(), a, menu[a]) for a in menu}
    prop = al.propose_v2(m, logic.initial_state(), menu, set())
    return {"expected": "every assay fails can_change_terminal_decision; chain does not exist; no purchase proposed",
            "observed": {"failed": {a: r["failed"] for a, r in rep.items()}, "decision": prop["decision"]},
            "passed": all("can_change_terminal_decision" in r["failed"] for r in rep.values()) and not prop["decision"].startswith("measure(")}


def m09_hash_and_identity():
    exp_src = {k: v["xml_sha256"] for k, v in rec.SOURCES.items()}
    exp_rec = al.record_digests(rec.RECORDS)
    base = (al.check_source_hashes(exp_src, rec.SOURCES), al.check_record_digests(exp_rec, rec.RECORDS))
    srcs = copy.deepcopy(rec.SOURCES); srcs["S1"]["xml_sha256"] = "0" * 64
    recs = copy.deepcopy(rec.RECORDS); recs[0]["cell"] = "IMR5"; recs[1]["dose_uM"] = 99
    mut = (al.check_source_hashes(exp_src, srcs), al.check_record_digests(exp_rec, recs))
    return {"expected": "no mismatch at baseline; the changed source hash and the two changed condition identities are named",
            "observed": {"baseline": base, "mutated_source": mut[0], "mutated_records": mut[1]},
            "passed": base == ([], []) and mut[0] == ["S1"] and mut[1] == sorted([rec.RECORDS[0]["id"], rec.RECORDS[1]["id"]])}


def m10_discovery_flag():
    base = al.validate_source_flags(rec.SOURCES)
    srcs = copy.deepcopy(rec.SOURCES)
    srcs["S1"]["status"] = "DISCOVERY_ELIGIBLE"
    srcs["S2"]["discovery_eligible"] = True
    mut = al.validate_source_flags(srcs)
    return {"expected": "clean at baseline; both flag changes are violations while read_by_designer is true",
            "observed": {"baseline": base, "mutated": mut}, "passed": base == [] and len(mut) == 2}


MUTATIONS = [("M01", "change hidden evaluator outcomes", m01_hidden_outcomes), ("M02", "change cell line, dose, time or readout", m02_condition_identity),
             ("M03", "relabel JB211 as a fully inactive control", m03_relabel_jb211), ("M04", "remove JB211 catalytic-engagement evidence", m04_remove_catalytic_evidence),
             ("M05", "duplicate wells or technical replicates", m05_duplicate_wells), ("M06", "remove proximal evidence", m06_remove_proximal),
             ("M07", "make all legal assay predictions identical", m07_identical_predictions), ("M08", "remove all decision consequences", m08_no_decision_consequence),
             ("M09", "change source hashes or condition identities", m09_hash_and_identity), ("M10", "change a published-case flag to discovery eligible", m10_discovery_flag)]


def run_all():
    results = []
    for mid, name, fn in MUTATIONS:
        r = fn()
        results.append({"id": mid, "mutation": name, **r})
    return results


def main():
    results = run_all()
    (HERE / "MUTATION_RESULTS.json").write_text(json.dumps({"rule_version": al.RULE_VERSION, "results": results}, sort_keys=True, indent=1) + "\n",
                                                encoding="utf-8", newline="\n")
    for r in results:
        print(("PASS " if r["passed"] else "FAIL ") + r["id"], r["mutation"])
    sys.exit(0 if all(r["passed"] for r in results) else 1)


if __name__ == "__main__":
    main()
