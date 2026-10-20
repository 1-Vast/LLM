"""Amendment-layer logic for the post-G1 audit. It imports the frozen v1 modules unchanged and adds:

* evidence grades: an observation may update the compatible set only if its grade supports the
  reading (a negative reading such as "no loss" needs an equivalence margin or detection limit);
* separate JB211 variables (CRBN recruitment, occupancy, exposure, catalytic activity, abundance,
  terminal phenotype) so that a binary 'engaged' never implies catalytic inhibition;
* an `OPEN_OR_UNMODELED_EXPLANATION` member that finite observations cannot refute;
* the section 4 discriminative-assay criteria (differing predictions, legal conditions, declared
  uncertainty model or measurement limit, terminal-decision consequence).

The v1 decision rules are not edited; v1 results stay in research/implementation_identifiability_v1/.
"""
from __future__ import annotations

import sys
from itertools import combinations
from pathlib import Path

V1 = Path(__file__).resolve().parent.parent / "implementation_identifiability_v1"
if str(V1) not in sys.path:
    sys.path.insert(0, str(V1))

import logic as v1_logic  # noqa: E402  (frozen v1 module, unchanged)
import records as v1_records  # noqa: E402

RULE_VERSION = "audit1-rules-1"
SCHEMA_VERSION = "audit1-schema-1"

OPEN = "OPEN_OR_UNMODELED_EXPLANATION"
NONE = v1_logic.NONE
UNKNOWN = "unknown"
INDISTINGUISHABLE = v1_logic.INDISTINGUISHABLE

GRADES = ("not_read", "not_reported", "reported_qualitatively", "numeric_without_uncertainty", "numeric_with_uncertainty")
UNCERTAINTY_MODELS = ("none", "test_only", "interval", "equivalence_margin", "detection_limit")

# Variables that must stay separate for JB211 (and any CRBN-null analogue).
JB211_VARIABLES = ("crbn_recruitment", "aurka_occupancy_or_binding", "intracellular_exposure", "catalytic_activity",
                   "protein_abundance", "terminal_phenotype")
JB211_WORDING = ("CRBN-null close analog; AURKA binding is asserted in the source, but direct intracellular engagement "
                 "and catalytic inhibition remain unresolved in the extracted evidence.")


def can_update(grade: str, outcome_is_negative: bool, uncertainty_model: str) -> bool:
    """Whether an observation of this grade may refute explanations.

    A positive reading (an effect is seen) needs numeric values with uncertainty. A negative reading
    ("no significant effect") additionally needs an equivalence margin, interval or detection limit:
    absence of significance is not evidence of absence.
    """

    if grade != "numeric_with_uncertainty":
        return False
    if outcome_is_negative:
        return uncertainty_model in ("equivalence_margin", "interval", "detection_limit")
    return uncertainty_model != "none"


def aurora_model_v2() -> v1_logic.Model:
    """v1 model plus the open explanation and split premises (v1 model object is not modified)."""
    m1 = v1_logic.aurora_model()
    expl = list(m1.explanations) + [OPEN]
    # JB211 viability is read under the catalytic-activity premise only; occupancy or exposure do not resolve it.
    assays = {k: v for k, v in m1.assays.items() if k not in ("A_JB211_ENGAGE",)}
    assays["A_JB211_VIAB"] = {"premise": "P_catalytic_inhibition_by_JB211", "pred": {
        v1_logic.EX_DEG: {True: {"no_loss"}, False: {"no_loss"}},
        v1_logic.EX_CAT: {True: {"loss"}, False: {"no_loss"}},
        v1_logic.EX_CRBN: {True: {"no_loss"}, False: {"no_loss"}},
        v1_logic.EX_BIND: {True: {"loss"}, False: {"loss"}},
    }}
    assays["A_JB211_OCCUPANCY"] = {"resolves": "P_occupancy_by_JB211", "outcomes": {"occupied": True, "not_occupied": False}}
    assays["A_JB211_EXPOSURE"] = {"resolves": "P_exposure_of_JB211", "outcomes": {"exposed": True, "not_exposed": False}}
    assays["A_JB211_ACTIVITY"] = {"resolves": "P_catalytic_inhibition_by_JB211", "outcomes": {"inhibited": True, "not_inhibited": False}}
    outcomes = {k: v for k, v in m1.outcomes.items() if k != "A_JB211_ENGAGE"}
    outcomes.update({"A_JB211_OCCUPANCY": ["occupied", "not_occupied"], "A_JB211_EXPOSURE": ["exposed", "not_exposed"],
                     "A_JB211_ACTIVITY": ["inhibited", "not_inhibited"]})

    def terminal(S):
        s = set(S) - {OPEN}
        if not s:
            return UNKNOWN
        return v1_logic.aurora_terminal(frozenset(s))

    return v1_logic.Model(expl, assays, outcomes, terminal)


class GradedState:
    """Wraps a v1 state: an observation is stored, but only a sufficiently graded one updates compatibility."""

    def __init__(self, model):
        self.model = model
        self.state = v1_logic.initial_state()
        self.log = []

    def observe(self, assay, outcome, grade, uncertainty_model="none", negative=False):
        ok = can_update(grade, negative, uncertainty_model)
        self.log.append({"assay": assay, "outcome": outcome, "grade": grade, "uncertainty_model": uncertainty_model,
                         "negative_reading": negative, "updates_compatibility": ok})
        if "resolves" in self.model.assays[assay] and grade not in ("numeric_with_uncertainty", "numeric_without_uncertainty"):
            return False  # a premise is not resolved by a qualitative statement either
        if ok or "resolves" in self.model.assays[assay]:
            self.state = self.model.apply(self.state, assay, outcome)
        return ok

    def compatible(self):
        # OPEN is never refuted by finite observations
        return frozenset(self.model.compatible(self.state)) | {OPEN}


def assay_is_discriminative(model, state, assay_id, menu_entry: dict) -> dict:
    """Section 4 criteria. All four must hold; the failing ones are returned."""

    rep = v1_logic.assay_report(model, state, assay_id)
    legal = bool(menu_entry) and bool(menu_entry.get("conditions")) and bool(menu_entry.get("controls")) and menu_entry.get("replicates", 0) >= 1
    um = menu_entry.get("uncertainty_model", "none") if menu_entry else "none"
    crit = {
        "differing_observable_predictions": rep["n_pairs_separated"] > 0,
        "scientifically_legal_under_declared_conditions": legal,
        "uncertainty_model_or_measurement_limit_declared": um in ("interval", "equivalence_margin", "detection_limit"),
        "can_change_terminal_decision": rep["changes_terminal_decision"],
    }
    return {"assay": assay_id, "criteria": crit, "discriminative": all(crit.values()), "failed": sorted(k for k, v in crit.items() if not v)}


def propose_v2(model, state, menu_by_id: dict, spent: set) -> dict:
    """Pre-purchase proposal under the strict criteria; `unknown` / `still_indistinguishable` when nothing qualifies."""

    S = frozenset(model.compatible(state)) | {OPEN}
    label = model.terminal(S)
    if label not in (v1_logic.UNRESOLVED, UNKNOWN):
        return {"decision": label, "compatible": sorted(S), "open_explanation_not_excluded": True, "ranking": []}
    ranked = []
    for a, entry in menu_by_id.items():
        if a in spent:
            continue
        r = assay_is_discriminative(model, state, a, entry)
        if r["discriminative"]:
            rep = v1_logic.assay_report(model, state, a)
            ranked.append({"action_id": a, "n_pairs_separated": rep["n_pairs_separated"], "wells": entry["wells_min"]})
    ranked.sort(key=lambda r: (-r["n_pairs_separated"], r["wells"], r["action_id"]))
    if ranked:
        return {"decision": f"measure({ranked[0]['action_id']})", "compatible": sorted(S), "open_explanation_not_excluded": True, "ranking": ranked}
    all_refuted = not (set(S) - {OPEN})
    return {"decision": UNKNOWN if all_refuted else INDISTINGUISHABLE, "compatible": sorted(S), "open_explanation_not_excluded": True, "ranking": []}


def validate_compound_labels(compounds: dict) -> list[str]:
    """Violations of the JB211 wording rule and of the CRBN-null control rule."""
    v = []
    jb = compounds.get("JB211", {})
    if jb.get("mode") != "crbn_null_aurka_binder_control":
        v.append("JB211 mode must stay crbn_null_aurka_binder_control")
    note = jb.get("note", "")
    if "inactive" in note.lower() and "not a pharmacologically inactive" not in note.lower():
        v.append("JB211 note describes it as inactive")
    if jb.get("catalytic_inhibition_assumed"):
        v.append("catalytic inhibition may not be assumed for JB211")
    c57 = compounds.get("cmpd57", {})
    if c57.get("terminal_inactive_claimed"):
        v.append("compound 57 terminal inactivity may not be claimed without a terminal result")
    return v


def validate_source_flags(sources: dict) -> list[str]:
    """Published, designer-read sources can never be discovery eligible or level 4."""
    v = []
    for sid, s in sources.items():
        if s.get("read_by_designer") and s.get("status") != "KNOWN_CASE_LOGIC_ONLY":
            v.append(f"{sid}: designer-read source must be KNOWN_CASE_LOGIC_ONLY, found {s.get('status')}")
        if s.get("discovery_eligible"):
            v.append(f"{sid}: published case flagged discovery eligible")
    return v


# ---------------------------------------------------------------------------------------------
# digests, unique costing
# ---------------------------------------------------------------------------------------------
import hashlib  # noqa: E402
import json  # noqa: E402


def canonical_digest(obj) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def record_digests(records) -> dict:
    return {r["id"]: canonical_digest(r) for r in records}


def check_record_digests(expected: dict, records) -> list[str]:
    got = record_digests(records)
    return sorted(k for k in set(expected) | set(got) if expected.get(k) != got.get(k))


def check_source_hashes(expected: dict, sources: dict) -> list[str]:
    return sorted(k for k in set(expected) | set(sources) if expected.get(k) != sources.get(k, {}).get("xml_sha256"))


def cost_total_unique(actions: list[dict], selected: list[str]) -> dict:
    """Wells and days with each bundle counted once; missing prices stay missing."""
    by = {a["action_id"]: a for a in actions}
    uniq = sorted(set(selected))
    days = [by[s]["turnaround_days"] for s in uniq]
    cur = [by[s]["cost_currency"] for s in uniq]
    return {"bundles": uniq, "wells": sum(by[s]["wells_min"] for s in uniq),
            "days": None if any(d is None for d in days) else max(days),
            "currency": None if any(c is None for c in cur) else sum(cur),
            "missing_price_fields": sum(c is None for c in cur)}


# ---------------------------------------------------------------------------------------------
# G0 requalification layer (v1 rules applied unchanged, audit1 extras added; extras can only lower a level)
# ---------------------------------------------------------------------------------------------
import idlib as v1_idlib  # noqa: E402


def grade_of(record: dict) -> str:
    """Audit grade of a record from its numeric flags (v2 records carry explicit upgrades)."""
    if record.get("evidence_grade"):
        return record["evidence_grade"]
    if record.get("numeric_extracted") and record.get("uncertainty_reported"):
        return "numeric_with_uncertainty"
    if record.get("numeric_extracted"):
        return "numeric_without_uncertainty"
    return "reported_qualitatively"


def requalify(unit: dict, records: list[dict], premises_unresolved: list[str], claims_inhibition_contrast: bool) -> dict:
    """v1 classification on the supplied (v2) records plus the audit1 criteria E1-E6.

    E1 a terminal endpoint exists; E2 proximal and terminal records share cell and genotype for every implementation;
    E3 nominal-dose comparisons carry exposure or PD evidence; E4 negative terminal readings carry an equivalence margin,
    interval or detection limit; E5 no unresolved premise that a mechanism contrast depends on; E6 an inhibitor or genetic
    terminal comparator is present when the unit claims a degradation-versus-inhibition contrast.
    """
    by = {r["id"]: r for r in records}
    recs = [by[i] for i in unit["record_ids"]]
    obs = [r for r in recs if r["evidence_type"] == "OBSERVED_EXPERIMENTAL_RESULT"]
    term = [r for r in obs if r["level"] == "terminal" and r["compound"] in unit["implementations"]]
    prox = [r for r in obs if r["level"] == "proximal" and r["compound"] in unit["implementations"]]
    if not term:
        return {"unit_id": unit["unit_id"], "level": 1, "level_name": v1_idlib.LEVEL_NAMES[1], "v1_rules": None,
                "failed_audit1": ["E1_terminal_endpoint_present"], "reason": "no terminal endpoint: not a task unit", "can_exceed_v1_level": False}
    v1 = v1_idlib.classify_unit(unit, records)
    negative_terminal = [r for r in term if "no significant" in str(r.get("result", {}).get("direction", "")).lower()]
    ctx = {i: {(r["cell"], r["genotype"]) for r in prox if r["compound"] == i} & {(r["cell"], r["genotype"]) for r in term if r["compound"] == i}
           for i in unit["implementations"]}
    e = {
        "E1_terminal_endpoint_present": True,
        "E2_proximal_terminal_context_shared_for_every_implementation": all(ctx[i] for i in unit["implementations"]),
        "E3_exposure_or_pd_evidence_for_nominal_dose_comparisons": all(r.get("pd_or_exposure_evidence") for r in term) and bool(term),
        "E4_negative_terminal_readings_have_equivalence_or_limit": all(r.get("uncertainty_model") in ("equivalence_margin", "interval", "detection_limit") for r in negative_terminal),
        "E5_no_unresolved_premise_under_mechanism_contrast": not premises_unresolved,
        "E6_inhibitor_or_genetic_terminal_comparator_when_contrast_claimed": (not claims_inhibition_contrast) or any(
            v1_records.COMPOUNDS[r["compound"]]["mode"] == "atp_competitive_kinase_inhibition" and r["time_h"] == unit["primary_terminal_endpoint"]["time_h"] and
            unit["primary_terminal_endpoint"]["readout"].split(" ")[0] in r["readout"] for r in term),
    }
    level = 3 if (v1["level"] == 3 and all(e.values())) else (2 if v1["level"] >= 2 else 1)
    return {"unit_id": unit["unit_id"], "level": level, "level_name": v1_idlib.LEVEL_NAMES[level], "v1_rules": {"level": v1["level"], "failed": v1["failed"]},
            "audit1_criteria": e, "failed_audit1": sorted(k for k, v in e.items() if not v), "unresolved_premises": premises_unresolved,
            "can_exceed_v1_level": False}
