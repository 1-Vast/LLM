"""G0/G1 engineering tests (software integrity level). They test behaviour, not report numbers."""
import copy
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE))

import build_g0  # noqa: E402
import idlib  # noqa: E402
import isolation  # noqa: E402
import logic  # noqa: E402
import records as rec  # noqa: E402
import run_g1  # noqa: E402

LEGAL = [a for a in rec.ACTIONS if a["outcome_in_records"]]
UNIT = rec.UNITS[0]


def _vault(jb211="no_loss", t217d="rescued", canary="CANARY-A"):
    return {"outcomes": {"A_JB211_VIAB": {"outcome": jb211, "source_records": ["S1-R30"]},
                         "A_T217D_RESCUE": {"outcome": t217d, "source_records": ["S1-R29"]}}, "canary": canary}


# ---- Test A: hidden-outcome isolation ----
def test_a_pre_purchase_decision_ignores_hidden_outcomes(tmp_path):
    transcripts = []
    for jb, t, can in (("no_loss", "rescued", "CANARY-A"), ("loss", "not_rescued", "CANARY-B")):
        led = isolation.AccessLedger()
        tr, _ = run_g1.replay(_vault(jb, t, can), tmp_path / can, UNIT, LEGAL, led)
        transcripts.append(tr)
        for step in tr:
            blob = json.dumps(step["proposal"])
            assert can not in blob
            assert not re.search(r"S1-R(29|30|31|32)", blob)
            assert not any("vault" in f or "evaluator" in f for f in step["tree_files"])
    assert transcripts[0][0]["stdout_sha256"] == transcripts[1][0]["stdout_sha256"], "step-0 proposal depends on hidden outcomes"


def test_a_views_contain_no_hidden_records_and_menu_is_stripped(tmp_path):
    q = isolation.build_views(tmp_path, rec.RECORDS, LEGAL, UNIT)
    src = json.loads((tmp_path / "source" / "records.json").read_text(encoding="utf-8"))
    assert not {r["id"] for r in src} & set(isolation.HIDDEN_RECORDS)
    assert all(not {"outcome_in_records", "record_ids"} & set(a) for a in q["menu"])
    for a in rec.ACTIONS:  # action identifiers must not encode outcomes
        assert not re.search(r"no_loss|rescued|loss$|engaged", a["action_id"].lower().replace("rescue", ""))


def test_a_release_is_one_observation_and_logged(tmp_path):
    led = isolation.AccessLedger()
    ev = isolation.Evaluator(_vault(), led)
    got = ev.purchase("A_T217D_RESCUE", 18)
    assert got == {"action_id": "A_T217D_RESCUE", "outcome": "rescued"}
    assert [e["event"] for e in led.events] == ["outcome_released"]
    with pytest.raises(ValueError):
        ev.purchase("A_T217D_RESCUE", 18)
    with pytest.raises(isolation.OutcomeUnavailable):
        ev.purchase("A_ALI_VIAB", 18)
    assert "A_JB211_VIAB" not in ev.released


# ---- Test B: condition binding ----
def _r(**kw):
    base = {"cell": "IMR5", "genotype": "WT", "time_h": 6, "readout": "x", "dose_uM": 1.0}
    base.update(kw)
    return base


@pytest.mark.parametrize("override", [{"cell": "MV4-11"}, {"genotype": "AURKA_T217D_Dox"}, {"time_h": 12}, {"readout": "y"}])
def test_b_mismatched_context_is_refused(override):
    assert not idlib.bind_conditions(_r(), _r(**override))["bound"]


def test_b_dose_mismatch_is_descriptive_only():
    b = idlib.bind_conditions(_r(), _r(dose_uM=0.5))
    assert b["bound"] and b["mode"] == "descriptive"
    assert idlib.bind_conditions(_r(), _r())["mode"] == "strict"
    assert idlib.bind_conditions(_r(dose_uM="series_not_extracted"), _r())["mode"] == "descriptive"


def test_b_real_records_are_not_silently_pooled():
    by = {r["id"]: r for r in rec.RECORDS}
    assert idlib.bind_conditions(by["S1-R20"], by["S1-R21"])["mode"] == "descriptive"      # 1 uM vs 0.5 uM
    assert not idlib.bind_conditions(by["S1-R27"], by["S2-R08"])["bound"]                   # viability vs GI50 readout
    assert not idlib.bind_conditions(by["S1-R22"], by["S1-R21"])["bound"]                   # 18 h vs 12 h


# ---- Test C: legal posterior updates ----
def test_c_observation_updates_state_without_touching_rules():
    m = logic.aurora_model()
    frozen = copy.deepcopy((m.assays, m.outcomes, m.explanations))
    s0 = logic.initial_state()
    s1 = m.apply(s0, "A_T217D_RESCUE", "rescued")
    assert s0["observed"] == {}                      # input state not mutated
    assert m.compatible(s0) == frozenset(logic.AURORA_EXPLANATIONS)
    assert m.compatible(s1) == {logic.EX_DEG, logic.EX_CAT}
    assert (m.assays, m.outcomes, m.explanations) == frozen


def test_c_premise_assay_changes_what_an_observation_means():
    m = logic.aurora_model()
    s = m.apply(logic.initial_state(), "A_T217D_RESCUE", "rescued")
    s = m.apply(s, "A_JB211_VIAB", "no_loss")
    assert m.compatible(s) == {logic.EX_DEG, logic.EX_CAT}            # premise unknown: catalytic stays
    engaged = m.apply(s, "A_JB211_ENGAGE", "engaged")
    not_engaged = m.apply(s, "A_JB211_ENGAGE", "not_engaged")
    assert m.compatible(engaged) == {logic.EX_DEG}
    assert m.compatible(not_engaged) == {logic.EX_DEG, logic.EX_CAT}


# ---- Test D: non-identifiability ----
def test_d_no_discriminating_assay_returns_unresolved_state():
    m = logic.Model(["X", "Y"], {"a": {"pred": {"X": {"o"}, "Y": {"o"}}}}, {"a": ["o"]}, lambda S: logic.UNRESOLVED if len(S) > 1 else "advance")
    prop = logic.propose(m, logic.initial_state(), [{"action_id": "a", "wells_min": 3}], set())
    assert prop["decision"] == logic.INDISTINGUISHABLE
    assert logic.identifiability_chain(m, logic.initial_state(), [{"action_id": "a"}])["chain_exists"] is False


def test_d_legal_menu_with_recorded_outcomes_stays_indistinguishable(tmp_path):
    led = isolation.AccessLedger()
    tr, ev = run_g1.replay(_vault(), tmp_path, UNIT, LEGAL, led)
    assert tr[-1]["proposal"]["decision"] == logic.INDISTINGUISHABLE
    assert set(tr[-1]["proposal"]["compatible"]) == {logic.EX_DEG, logic.EX_CAT}


def test_d_all_refuted_gives_none_state_not_a_forced_choice():
    m = logic.aurora_model()
    s = m.apply(logic.initial_state(), "A_T217D_RESCUE", "rescued")
    s = m.apply(s, "A_AURKA_KD_VIAB", "no_loss")           # off-target says no_loss, rescue says on-target
    assert logic.residual_none(m, s)
    assert logic.aurora_terminal(m.compatible(s)) == logic.NONE


def test_d_discriminating_but_decision_irrelevant_assay_is_flagged():
    term = lambda S: "same" if S else logic.NONE
    m = logic.Model(["X", "Y"], {"a": {"pred": {"X": {"hi"}, "Y": {"lo"}}}}, {"a": ["hi", "lo"]}, term)
    rep = logic.assay_report(m, logic.initial_state(), "a")
    assert rep["n_pairs_separated"] == 1 and rep["changes_terminal_decision"] is False
    assert logic.identifiability_chain(m, logic.initial_state(), [{"action_id": "a"}])["chain_exists"] is False


def test_d_synthetic_same_phenotype_different_proximal_effect_is_discriminable():
    """Engineering fixture only: two implementations with one phenotype, separated by a proximal assay."""
    term = lambda S: {"I1"}.__eq__(set(S)) and "advance(I1)" or ({"I2"}.__eq__(set(S)) and "advance(I2)" or logic.UNRESOLVED)
    m = logic.Model(["I1", "I2"], {"prox": {"pred": {"I1": {"degraded"}, "I2": {"intact"}}}, "pheno": {"pred": {"I1": {"loss"}, "I2": {"loss"}}}},
                    {"prox": ["degraded", "intact"], "pheno": ["loss"]}, term)
    s0 = logic.initial_state()
    assert logic.assay_report(m, s0, "pheno")["n_pairs_separated"] == 0
    assert logic.assay_report(m, s0, "prox")["changes_terminal_decision"] is True
    assert logic.propose(m, s0, [{"action_id": "prox", "wells_min": 1}, {"action_id": "pheno", "wells_min": 1}], set())["decision"] == "measure(prox)"


# ---- Test E: cost accounting ----
def test_e_missing_prices_stay_missing_and_ledgers_are_separate(tmp_path):
    c = idlib.cost_total(rec.ACTIONS, ["A_JB211_VIAB", "A_T217D_RESCUE"])
    assert c["wells"] == 36 and c["currency"] is None and c["days"] is None and c["missing_price_fields"] == 2
    led = isolation.AccessLedger()
    _, ev = run_g1.replay(_vault(), tmp_path, UNIT, LEGAL, led)
    charged = [e["detail"]["simulated_wells_charged"] for e in led.events if e["event"] == "outcome_released"]
    assert sum(charged) == sum(a["wells_min"] for a in LEGAL if a["action_id"] in ev.released)   # no double counting
    assert len(charged) == len(ev.released)


def test_e_every_bundle_counts_controls_and_replicates():
    for a in rec.ACTIONS:
        assert a["controls"] and a["replicates"] >= 3 and a["wells_min"] == a["arms"] * a["replicates"]


# ---- Test F: evidence identity separation ----
def test_f_evidence_types_are_separate():
    types = {r["evidence_type"] for r in rec.RECORDS}
    assert types <= set(rec.EVIDENCE_TYPES)
    assert rec.PREDICTION not in types and rec.CONFIRMATION not in types
    for r in rec.RECORDS:
        if r["evidence_type"] == rec.ANNOTATION:
            assert "result" not in r
        if r["evidence_type"] == rec.OBSERVED:
            assert r["source"] in rec.SOURCES and r["locator"]


def test_f_jb211_is_never_labelled_inactive_control():
    assert rec.COMPOUNDS["JB211"]["mode"] == "crbn_null_aurka_binder_control"
    assert "NOT a pharmacologically inactive control" in rec.COMPOUNDS["JB211"]["note"]


# ---- Test G: experimental lineage ----
def test_g_shared_batch_and_repeats_are_dependent():
    g = idlib.dependence_graph(rec.RECORDS, rec.UNITS)
    batch_edges = [e for e in g["edges"] if e["type"] == "shares_batch_and_controls"]
    assert {e["from"] for e in batch_edges} == {"S1-R09", "S1-R10", "S1-R11"}
    assert any(e["type"] == "same_molecule_cross_source_bridge" for e in g["edges"])
    classes = [idlib.classify_unit(u, rec.RECORDS) for u in rec.UNITS]
    c = idlib.effective_counts(rec.UNITS, classes, rec.COMPOUNDS, rec.RECORDS)
    assert c["target_families"] == 1 and c["independent_source_families"] == 1 and c["level3_or_higher_units"] == 0


def test_g_no_unit_reaches_level_3_or_4_from_this_evidence():
    for u in rec.UNITS:
        cl = idlib.classify_unit(u, rec.RECORDS)
        assert cl["level"] == 2, (u["unit_id"], cl["failed"])
        assert "L3d_numeric_values_with_uncertainty_for_primary_and_proximal" in cl["failed"]


# ---- Test H: reproducibility ----
def _digest(p):
    return hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def test_h_builder_is_deterministic():
    names = ["manifest.jsonl", "records.jsonl", "units.jsonl", "actions.jsonl", "eligibility.json", "dependence_graph.json",
             "missing_evidence_register.json", "candidate_split_manifest.json", "access_ledger.jsonl"]
    build_g0.main()
    first = {n: _digest(HERE / "evidence" / n) for n in names}
    build_g0.main()
    assert first == {n: _digest(HERE / "evidence" / n) for n in names}


def test_h_study_code_has_no_network_llm_or_training():
    banned = re.compile(r"\b(requests|urllib|httpx|anthropic|openai|torch|sklearn)\b")
    for p in HERE.glob("*.py"):
        if p.name == "verify.py":
            continue
        assert not banned.search(p.read_text(encoding="utf-8")), p.name
