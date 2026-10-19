"""G1 logic: compatible explanations, discriminative assays, non-identifiability, decision consequence.

Explanations are sufficient-cause candidates that may coexist. The surviving set is the set that no
observation has refuted; it is not a probability distribution. A residual `NONE` flag records that
a finite set of observations cannot refute "none of these is sufficient" unless every listed
explanation has been refuted. No outcome probabilities are used anywhere: the records give none.
"""
from __future__ import annotations

from itertools import combinations

NONE = "NONE_OF_THE_CURRENT_EXPLANATIONS_IS_SUFFICIENT"
UNRESOLVED = "unresolved"
INDISTINGUISHABLE = "still_indistinguishable"


class Model:
    """Explanations, assays, premises and a terminal-decision map.

    `assays[a]` is either
      {"pred": {expl: outcomes}}                                         unconditional, or
      {"premise": P, "pred": {expl: {True: outcomes, False: outcomes}}}  conditional on premise P, or
      {"resolves": P, "outcomes": {outcome: bool}}                       premise-resolving assay.
    An explanation missing from `pred` is unconstrained (admits every outcome of the assay).
    """

    def __init__(self, explanations, assays, outcomes, terminal):
        self.explanations = list(explanations)
        self.assays = assays
        self.outcomes = outcomes  # assay -> list of possible outcomes
        self.terminal = terminal  # callable(frozenset) -> label or UNRESOLVED

    def admissible(self, assay, expl, premises):
        spec = self.assays[assay]
        if "pred" not in spec or expl not in spec["pred"]:
            return set(self.outcomes[assay])
        p = spec["pred"][expl]
        if "premise" in spec:
            state = premises.get(spec["premise"])
            if state is None:
                return set(p[True]) | set(p[False])
            return set(p[state])
        return set(p)

    def apply(self, state, assay, outcome):
        new = {"observed": dict(state["observed"]), "premises": dict(state["premises"])}
        spec = self.assays[assay]
        if "resolves" in spec:
            new["premises"][spec["resolves"]] = spec["outcomes"][outcome]
        new["observed"][assay] = outcome
        return new

    def compatible(self, state):
        keep = []
        for e in self.explanations:
            ok = True
            for a, o in state["observed"].items():
                if "resolves" in self.assays[a]:
                    continue
                if o not in self.admissible(a, e, state["premises"]):
                    ok = False
                    break
            if ok:
                keep.append(e)
        return frozenset(keep)


def initial_state(observed=None, premises=None):
    return {"observed": dict(observed or {}), "premises": dict(premises or {})}


def residual_none(model, state):
    """True when no listed explanation survives: the unresolved state of Rule 2."""
    return len(model.compatible(state)) == 0


def assay_report(model, state, assay):
    """What an assay can do from `state`: outcome -> surviving set, separated pairs, decision labels."""

    S = model.compatible(state)
    per_outcome = {}
    for o in model.outcomes[assay]:
        nxt = model.apply(state, assay, o)
        per_outcome[o] = model.compatible(nxt)
    pairs = []
    for e1, e2 in combinations(sorted(S), 2):
        if any((e1 in s) != (e2 in s) for s in per_outcome.values()):
            pairs.append((e1, e2))
    labels = {o: (model.terminal(s) if s else NONE) for o, s in per_outcome.items()}
    refutes = any(s != S for s in per_outcome.values())
    premise_only = "resolves" in model.assays[assay]
    # a premise assay is informative when it changes what later assays can separate
    if premise_only:
        refutes = refutes or any(model.compatible(model.apply(state, assay, o)) != S for o in model.outcomes[assay])
    return {
        "assay": assay,
        "surviving_by_outcome": {o: sorted(s) for o, s in per_outcome.items()},
        "separated_pairs": pairs,
        "n_pairs_separated": len(pairs),
        "informative_at_some_outcome": refutes,
        "terminal_label_by_outcome": labels,
        "changes_terminal_decision": len(set(labels.values())) > 1,
        "premise_resolving": premise_only,
    }


def premise_unlock(model, state, assay, menu_ids):
    """Pairs a premise assay would make separable by some other menu assay, counted after each outcome."""
    gained = 0
    S = model.compatible(state)
    base = sum(assay_report(model, state, other)["n_pairs_separated"] for other in menu_ids if other != assay and "resolves" not in model.assays[other])
    for o in model.outcomes[assay]:
        nxt = model.apply(state, assay, o)
        after = sum(assay_report(model, nxt, other)["n_pairs_separated"] for other in menu_ids if other != assay and "resolves" not in model.assays[other])
        gained = max(gained, after - base)
    return gained


def propose(model, state, menu, spent):
    """Deterministic pre-purchase proposal: rank unspent legal bundles by decision relevance.

    Score: terminal-decision-changing first, then pairs separated (premise assays: pairs unlocked),
    then fewer wells, then id. No outcome is read. When the compatible set already maps to a
    terminal label the proposal is that label; when nothing left can separate the set it is
    `still_indistinguishable` with the blocking assays named.
    """

    S = model.compatible(state)
    label = model.terminal(S) if S else NONE
    ids = [a["action_id"] for a in menu]
    wells = {a["action_id"]: a["wells_min"] for a in menu}
    if label != UNRESOLVED:
        return {"decision": label, "compatible": sorted(S), "ranking": []}
    ranking = []
    for a in ids:
        if a in spent:
            continue
        rep = assay_report(model, state, a)
        unlock = premise_unlock(model, state, a, ids) if rep["premise_resolving"] else 0
        informative = rep["n_pairs_separated"] > 0 or unlock > 0
        if not informative:
            continue
        ranking.append({
            "action_id": a, "n_pairs_separated": rep["n_pairs_separated"], "pairs_unlocked": unlock,
            "changes_terminal_decision": rep["changes_terminal_decision"], "wells": wells[a],
            "terminal_label_by_outcome": rep["terminal_label_by_outcome"],
        })
    ranking.sort(key=lambda r: (not r["changes_terminal_decision"], -(r["n_pairs_separated"] + r["pairs_unlocked"]), r["wells"], r["action_id"]))
    if not ranking:
        return {"decision": INDISTINGUISHABLE, "compatible": sorted(S), "ranking": []}
    return {"decision": f"measure({ranking[0]['action_id']})", "compatible": sorted(S), "ranking": ranking}


def identifiability_chain(model, state, menu):
    """Section 9.4 chain at design level: two compatible explanations, a legal assay that separates
    them, and different terminal decisions on the two sides."""

    S = model.compatible(state)
    chains = []
    for a in menu:
        rep = assay_report(model, state, a["action_id"])
        if rep["n_pairs_separated"] and rep["changes_terminal_decision"]:
            chains.append({"action_id": a["action_id"], "pairs": rep["separated_pairs"], "labels": rep["terminal_label_by_outcome"]})
    return {"compatible": sorted(S), "n_compatible": len(S), "chains": chains, "chain_exists": len(S) >= 2 and bool(chains)}


# ----------------------------------------------------------------------------------------------
# The AURORA-A task model (study-local explanation names; the earlier H_E/H_M/H_C/H_O labels are not
# defined anywhere in the repository and are not used or redefined here).
# ----------------------------------------------------------------------------------------------
EX_DEG = "EX_PROTEIN_LOSS_SCAFFOLD"          # loss of AURKA protein (non-catalytic role) is needed
EX_CAT = "EX_CATALYTIC_INHIBITION"           # loss of AURKA catalytic activity is sufficient
EX_CRBN = "EX_CRBN_DEPENDENT_OFFTARGET"      # CRBN-dependent effect not routed through AURKA
EX_BIND = "EX_WARHEAD_OFFTARGET_BINDING"     # off-target kinase binding by the alisertib-derived warhead

AURORA_EXPLANATIONS = [EX_DEG, EX_CAT, EX_CRBN, EX_BIND]


def aurora_terminal(S: frozenset) -> str:
    s = set(S) - {NONE}
    if not s:
        return NONE
    if s == {EX_DEG}:
        return "advance(degrader)"
    if s == {EX_CAT}:
        return "switch(alisertib_class_inhibitor)"
    if s <= {EX_CRBN, EX_BIND}:
        return "stop"
    return UNRESOLVED


def aurora_model() -> Model:
    assays = {
        "A_JB211_VIAB": {"premise": "P1_JB211_inhibits_AURKA_catalytic_activity", "pred": {
            EX_DEG: {True: {"no_loss"}, False: {"no_loss"}},
            EX_CAT: {True: {"loss"}, False: {"no_loss"}},
            EX_CRBN: {True: {"no_loss"}, False: {"no_loss"}},
            EX_BIND: {True: {"loss"}, False: {"loss"}},
        }},
        "A_T217D_RESCUE": {"pred": {
            EX_DEG: {"rescued"}, EX_CAT: {"rescued"}, EX_CRBN: {"not_rescued"}, EX_BIND: {"not_rescued"},
        }},
        # alisertib viability: loss is admitted by every explanation, so only "no_loss" can refute (EX_CAT)
        "A_ALI_VIAB": {"pred": {EX_CAT: {"loss"}}},
        "A_JB211_ENGAGE": {"resolves": "P1_JB211_inhibits_AURKA_catalytic_activity", "outcomes": {"engaged": True, "not_engaged": False}},
        # knockdown removes the protein and its activity together: it separates on-target from off-target only
        "A_AURKA_KD_VIAB": {"pred": {EX_DEG: {"loss"}, EX_CAT: {"loss"}, EX_CRBN: {"no_loss"}, EX_BIND: {"no_loss"}}},
        # replacement with kinase-dead AURKA restores viability only if the catalytic role is not needed
        "A_KINASE_DEAD_REPLACE": {"pred": {EX_DEG: {"rescued_by_kinase_dead"}, EX_CAT: {"not_rescued_by_kinase_dead"}}},
    }
    outcomes = {
        "A_JB211_VIAB": ["loss", "no_loss"],
        "A_T217D_RESCUE": ["rescued", "not_rescued"],
        "A_ALI_VIAB": ["loss", "no_loss"],
        "A_JB211_ENGAGE": ["engaged", "not_engaged"],
        "A_AURKA_KD_VIAB": ["loss", "no_loss"],
        "A_KINASE_DEAD_REPLACE": ["rescued_by_kinase_dead", "not_rescued_by_kinase_dead"],
    }
    return Model(AURORA_EXPLANATIONS, assays, outcomes, aurora_terminal)
