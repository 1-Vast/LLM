"""The frozen baseline ladder: every arm chooses from the same legal menu through one runner.

File summary
- Path: research/external_validation/arms.py
- Purpose: the fourteen registered rungs (`protocol.json`) plus the shipped default and the latest
  research candidate, each as an arm `arm(ctx, compound, h1, h2, executed, menu, remaining, setting,
  state) -> (key | None, note)` for `sequence_audit.policies.run_matched`.
- Core points:
  - Arms receive the sealed policy view (`firewall.seal`). The only arm that reads hidden results
    is the oracle, which is built with the real context and flagged `reads_hidden_outcomes`.
  - Existing policies are reused unchanged: fixed, production and the sparse-value planner are
    imported, and `maestro` is `sequence_audit.policies.discrimination` with the virtual-cell
    channel made explicit (masked, on, or permuted to another held-out compound).
  - Every note that carries a forecast records it per hypothesis as `prediction_by_hypothesis`
    with `p_correct` and `p_wrong`, so calibration reads all arms the same way, and `used_vc`
    says whether virtual-cell output reached the choice.
  - Forecasts only choose actions. No arm touches `EvidenceState`.
- Depends on: research/sequence_audit/policies.py, research/sparse_value/{policy,model}.py,
  maestro.acquisition, maestro.selection, rdkit, scikit-learn
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "sequence_audit"))
sys.path.insert(0, str(ROOT / "research" / "sparse_value"))

import policies as P  # noqa: E402
import policy as SV  # noqa: E402

from . import firewall as F  # noqa: E402
from model import LABELS, Branch, Forecast, SparseReferenceModel  # noqa: E402

from maestro.acquisition import (  # noqa: E402
    outcome_consequences,
    select_decision_sensitive_action,
    select_discriminating_action,
)
from maestro.selection import BudgetedEvidenceSelector  # noqa: E402

C, E, V = P.C, P.E, P.V
PRICE = 0.02
SEED = 20260927
RETRIEVAL_NEIGHBOURS = 5
RIDGE_ALPHAS = (0.1, 1.0, 10.0, 100.0, 1000.0)


# ------------------------------------------------------------------------------ virtual cell
class StructureVC:
    """The frozen structure-kNN virtual cell (`episodes.Magnitude`) with its predicted profile exposed.

    `predict` returns exactly what `Magnitude.predict` returns; a compound without a parsable
    structure gets no prediction instead of an error.
    """

    def __init__(self, data, detected=None):
        from rdkit import Chem, RDLogger
        from rdkit.Chem import rdFingerprintGenerator
        RDLogger.DisableLog("rdApp.*")
        gen = rdFingerprintGenerator.GetMorganGenerator(radius=2, fpSize=2048)
        comp = data.compounds.drop_duplicates("compound")
        self.names = list(comp.compound)
        self.fold = dict(zip(comp.compound, comp.fold))
        fps, self.has_structure = [], {}
        for name, smiles in zip(comp.compound, comp.smiles):
            mol = Chem.MolFromSmiles(smiles) if isinstance(smiles, str) and smiles else None
            self.has_structure[name] = mol is not None
            fps.append(gen.GetFingerprintAsNumPy(mol).astype(np.float32) if mol is not None else np.zeros(2048, np.float32))
        self.fp = np.asarray(fps)
        self.pos = {c: i for i, c in enumerate(self.names)}
        self.data = data
        self._cache = {}

    def profile(self, compound: str, key):
        if key[1] != 24.0 or not self.has_structure.get(compound, False):
            return None                                   # the served rung refuses time_not_supported
        query = (compound, tuple(key))
        if query in self._cache:
            return self._cache[query]
        x = self.fp[self.pos[compound]]
        inter = self.fp @ x
        union = self.fp.sum(1) + x.sum() - inter
        sim = np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)
        fold = self.fold[compound]
        vectors, weights = [], []
        for j in np.argsort(-sim):
            other = self.names[j]
            if self.fold[other] == fold or not self.has_structure.get(other, False):
                continue
            row = self.data.index.get(key, {}).get(other)
            if row is None or not C.qc_passed(self.data, row):
                continue
            vectors.append(self.data.shift[row])
            weights.append(max(float(sim[j]), 1e-6))
            if len(vectors) == 5:
                break
        out = None
        if vectors:
            w = np.asarray(weights) / np.sum(weights)
            out = np.tensordot(w, np.asarray(vectors), axes=1)
        self._cache[query] = out
        return out

    def predict(self, compound: str, key) -> float | None:
        vector = self.profile(compound, key)
        return None if vector is None else float(np.linalg.norm(vector))

    def max_similarity(self, compound: str) -> float:
        """Nearest training neighbour's Tanimoto similarity (scaffold-novelty stratum)."""
        if not self.has_structure.get(compound, False):
            return float("nan")
        x = self.fp[self.pos[compound]]
        inter = self.fp @ x
        union = self.fp.sum(1) + x.sum() - inter
        sim = np.where(union > 0, inter / np.maximum(union, 1e-9), 0.0)
        fold = self.fold[compound]
        mask = np.array([self.fold[n] != fold and self.has_structure[n] for n in self.names])
        return float(sim[mask].max()) if mask.any() else float("nan")


# ------------------------------------------------------------------------------ helpers
def _prediction_note(forecasts_by_h: dict, **extra) -> dict:
    return {"evidence_kind": "model_prediction", "prediction_by_hypothesis": forecasts_by_h, **extra}


def _stop(reason: str, **extra):
    return None, {"reason": reason, **extra}


@F.fitting
def build_reference_model(ctx, *, pooling=True) -> SparseReferenceModel:
    comp = ctx.data.compounds.drop_duplicates("compound").set_index("compound")
    groups = comp["component" if "component" in comp.columns else "skeleton"].to_dict()
    return SparseReferenceModel(ctx.ft, ctx.params, groups, pooling=pooling)


def _model(ctx, *, pooling=True) -> SparseReferenceModel:
    """The sparse-value reference model; shares `make_policy`'s cache so every arm sees one model."""
    models = ctx.extra.setdefault("sparse_value_models", {})
    key = (pooling, False)
    if key not in models:
        models[key] = build_reference_model(ctx, pooling=pooling)
    return models[key]


def planning_state(model, executed, h1, h2):
    """Planning weights and conditioning source, exactly as `sparse_value.policy.choose` sets them."""
    weights = {h1: 0.5, h2: 0.5}
    if not (executed and executed[-1]["qc"]):
        return weights, None, None, None
    source = tuple(executed[-1]["key"])
    label = P.NEUTRAL.get(executed[-1]["outcome"])
    if label is None:
        return None, None, None, "result_not_a_neutral_planning_observation"
    initial = model.forecast(source, h1, h2)
    if initial.refusal:
        return None, None, None, "value_unknown:first_reading_likelihood_unavailable"
    likelihood = {h: initial.branches[h].probabilities[label] for h in weights}
    total = sum(likelihood.values())
    if total <= 0:
        return None, None, None, "value_unknown:observed_reading_outside_forecast"
    return {h: p / total for h, p in likelihood.items()}, source, label, None


def mutual_information(weights: dict, probabilities: dict) -> float:
    """I(H; Y) in bits for planning weights over H and reading distributions P(Y | H)."""
    joint = {h: np.asarray([probabilities[h][label] for label in LABELS]) * w for h, w in weights.items()}
    marginal = sum(joint.values())

    def entropy(p):
        p = p[p > 0]
        return float(-(p * np.log2(p)).sum())

    conditional = sum(w * entropy(np.asarray([probabilities[h][label] for label in LABELS])) for h, w in weights.items())
    return max(entropy(marginal) - conditional, 0.0)


def _branch(hypothesis, alpha, correct, wrong, neighbours, basis):
    total = float(alpha.sum())
    probabilities = alpha / total
    weights = np.zeros(len(LABELS))
    weights[correct], weights[wrong] = 1.0, -2.0
    mean = float(probabilities @ weights)
    variance = float((probabilities @ (weights ** 2) - mean ** 2) / (total + 1.0))
    from scipy.stats import beta
    return Branch(hypothesis, dict(zip(LABELS, probabilities.tolist())), dict(zip(LABELS, alpha.tolist())),
                  float(probabilities[correct]), float(probabilities[wrong]), mean, variance,
                  float(beta.ppf(0.95, alpha[wrong], total - alpha[wrong])), tuple(neighbours), (), (), (),
                  len(neighbours), 0, basis, 0.0)


def retrieval_forecast(ctx, model, source, profile, target, h1, h2, k=RETRIEVAL_NEIGHBOURS) -> Forecast:
    """Similarity-weighted reading distributions from the training references nearest the measured profile."""
    table = ctx.ft.tables.get(source)
    if table is None or profile is None or not np.isfinite(profile).all():
        return model.forecast(target, h1, h2)
    y = np.asarray(profile, dtype=np.float64)
    norms = np.linalg.norm(table.Y, axis=1) * max(float(np.linalg.norm(y)), 1e-12)
    cosine = (table.Y @ y) / np.maximum(norms, 1e-12)
    similarity = dict(zip(table.names, cosine))
    unconditional = model.forecast(target, h1, h2)
    branches = {}
    for own, other in ((h1, h2), (h2, h1)):
        readings = model._readings(target, own, other, h1)
        if not readings:
            return Forecast({}, f"no_target_references:{own}")
        ranked = sorted(((similarity[c], c) for c in readings if c in similarity and similarity[c] > 0), reverse=True)[:k]
        correct, wrong = (0, 1) if own == h1 else (1, 0)
        if not ranked:
            if unconditional.refusal:
                return unconditional
            b = unconditional.branches[own]
            branches[own] = Branch(**{**b.__dict__, "basis": "retrieval_backoff_unconditional"})
            continue
        alpha = np.full(len(LABELS), 0.5)
        for weight, compound in ranked:
            alpha[LABELS.index(readings[compound])] += weight
        branches[own] = _branch(own, alpha, correct, wrong, [c for _, c in ranked], "profile_retrieval")
    return Forecast(branches)


def _sparse_note(forecast, weights, estimate, price, **plan):
    return SV.note(forecast, weights, estimate, price, **plan)


# ------------------------------------------------------------------------------ rungs 1-4
def defer_floor(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
    return _stop("defer_floor")


def random_legal(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
    rng = np.random.default_rng([SEED, E.stable("random_legal", compound, h1, h2, len(executed))])
    return menu[int(rng.integers(len(menu)))], {"seeded": True}


def fixed(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
    return P.fixed(ctx, compound, h1, h2, executed, menu, remaining, setting, state)


def _budgeted(ctx, h1, h2, menu, remaining, setting, priorities):
    actions = [P.make_action(k, h1, h2, setting) for k in menu]
    plan = BudgetedEvidenceSelector().select(frozenset({h1, h2}), actions, E.PROFILE,
                                             min(remaining, setting.step_budget), action_priorities=priorities)
    if not plan.actions:
        return _stop("selector_returned_empty")
    chosen = plan.actions[0].identifier
    return next(k for k in menu if C.action_id(k) == chosen), {"used_vc": bool(priorities)}


def cost_only(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
    return _budgeted(ctx, h1, h2, menu, remaining, setting, None)


# ------------------------------------------------------------------------------ rungs 5, 6, 9, 10
def marginal_only(price=PRICE):
    return SV.make_policy(price, marginal_only=True)


def sparse_two_step(price=PRICE):
    return SV.make_policy(price)


def _eliminates(ctx):
    return bool(ctx.params["eliminates"])


def myopic_edv(price=PRICE):
    def arm(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
        if not _eliminates(ctx):
            return _stop("registered_validator_cannot_eliminate")
        model = _model(ctx)
        weights, source, label, refusal = planning_state(model, executed, h1, h2)
        if refusal:
            return _stop(refusal)
        best, unknown = SV.best_single(menu, lambda a: model.forecast(a, h1, h2, source=source, observed_label=label),
                                       weights, price, setting.days)
        if best is None:
            return _stop("value_unknown" if unknown else "estimated_net_non_positive", unknown_forecasts=unknown)
        net, _, _, action, estimate, forecast = best
        return action, _sparse_note(forecast, weights, estimate, price, expected_net=net, expected_measurements=1.0,
                                    after=label or ("qc_failure" if executed else "start"))
    return arm


def decision_sensitive_edv(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
    """One-step EDV arm using terminal-decision sensitivity.

    Assay-days remain the hard legality/budget cost.  The registered utility
    price is supplied separately so a six-day assay is not compared directly
    with a unit terminal-loss value.
    """
    if not _eliminates(ctx):
        return _stop("registered_validator_cannot_eliminate", decision_sensitive=True)
    actions = [P.make_action(key, h1, h2, setting) for key in menu]
    policy_state = ctx.extra.get("policy_input")
    if policy_state is None:
        policy_state = F.project_policy_input(
            visible_evidence=(), legal_actions=tuple(actions), budget=float(remaining),
            provenance={"arm": "decision_sensitive_edv"},
        )
    F.assert_policy_input(policy_state)
    actions = list(policy_state.legal_actions)
    remaining = min(float(policy_state.budget), float(remaining))
    contrast = E.contrast_for(h1, h2, actions)
    forecaster = V.ReferenceCardForecaster(ctx.ft, ctx.params, minimum_references=1)
    forecasts = forecaster.forecast(contrast, actions, state)
    consequences = outcome_consequences(V.registered_rules(h1, h2))
    plan = select_decision_sensitive_action(
        frozenset({h1, h2}), actions, E.PROFILE, min(remaining, setting.step_budget), forecasts,
        consequences, measurement_costs={action.identifier: PRICE for action in actions},
    )
    if plan.chosen is None:
        return _stop(
            f"acquisition_{plan.status}", decision_sensitive=True,
            reason_detail=plan.reason,
            evaluations={item.action_identifier: item.payload() for item in plan.evaluations},
        )
    chosen = plan.chosen
    forecast = forecasts[chosen.action_identifier]
    return next(key for key in menu if C.action_id(key) == chosen.action_identifier), _prediction_note(
        _per_hypothesis(forecast, h1, h2), decision_sensitive=True,
        expected_value=chosen.expected_value, net_value=chosen.net_value,
        decision_sensitivity=chosen.decision_sensitivity,
        expected_wrong_decision=chosen.expected_wrong_decision,
        utility_cost=chosen.cost, selector="terminal_decision_value",
    )


def retrieval(price=PRICE):
    def arm(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
        if not _eliminates(ctx):
            return _stop("registered_validator_cannot_eliminate")
        model = _model(ctx)
        weights, source, label, refusal = planning_state(model, executed, h1, h2)
        if refusal:
            return _stop(refusal)
        profile = ctx.extra["visible"].profile(source) if source is not None else None
        if source is None or profile is None:
            forecast_for, basis = (lambda a: model.forecast(a, h1, h2)), "retrieval_no_profile_yet"
        else:
            forecast_for, basis = (lambda a: retrieval_forecast(ctx, model, source, profile, a, h1, h2)), "profile_retrieval"
        best, unknown = SV.best_single(menu, forecast_for, weights, price, setting.days)
        if best is None:
            return _stop("value_unknown" if unknown else "estimated_net_non_positive", unknown_forecasts=unknown)
        net, _, _, action, estimate, forecast = best
        return action, _sparse_note(forecast, weights, estimate, price, expected_net=net, retrieval_basis=basis,
                                    after=label or ("qc_failure" if executed else "start"))
    return arm


def info_gain(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
    if not _eliminates(ctx):
        return _stop("registered_validator_cannot_eliminate")
    model = _model(ctx)
    weights, source, label, refusal = planning_state(model, executed, h1, h2)
    if refusal:
        return _stop(refusal)
    scored, unknown = [], {}
    for action in menu:
        forecast = model.forecast(action, h1, h2, source=source, observed_label=label)
        if forecast.refusal:
            unknown[C.action_id(action)] = forecast.refusal
            continue
        probabilities = {h: forecast.branches[h].probabilities for h in weights}
        scored.append((mutual_information(weights, probabilities), setting.days(action), C.action_id(action), action, forecast))
    if not scored:
        return _stop("value_unknown", unknown_forecasts=unknown)
    information, _, _, action, forecast = min(scored, key=lambda row: (-row[0], row[1], row[2]))
    if information <= 1e-9:
        return _stop("no_expected_information")
    return action, _sparse_note(forecast, weights, SV.value(forecast, weights), 0.0, mutual_information_bits=information,
                                after=label or ("qc_failure" if executed else "start"))


# ------------------------------------------------------------------------------ rung 7: magnitude
def _vc_priorities(ctx, compound, menu, vc: str) -> dict | None:
    if vc == "masked" or ctx.magnitude is None:
        return None
    source = compound if vc == "on" else ctx.extra["vc_partner"][compound]
    return V.magnitude_priorities(ctx, source, menu)


def magnitude(vc="on"):
    def arm(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
        priorities = _vc_priorities(ctx, compound, menu, vc)
        key, note = _budgeted(ctx, h1, h2, menu, remaining, setting, priorities)
        return key, {**note, "vc_channel": vc}
    return arm


# ------------------------------------------------------------------------------ rung 8: ridge
class RidgeProfiles:
    """Structure-to-profile ridge per action, fitted on the fold's training references only."""

    def __init__(self, ctx, vc: StructureVC):
        from sklearn.linear_model import RidgeCV
        self.vc, self.models = vc, {}
        for key, table in ctx.ft.tables.items():
            rows = [i for i, c in enumerate(table.names) if vc.has_structure.get(c, False)]
            if len(rows) < 5:
                continue
            X = vc.fp[[vc.pos[table.names[i]] for i in rows]].astype(np.float64)
            model = RidgeCV(alphas=RIDGE_ALPHAS).fit(X, table.Y[rows])
            self.models[key] = model

    def predict(self, compound, key):
        model = self.models.get(key)
        if model is None or not self.vc.has_structure.get(compound, False):
            return None
        return model.predict(self.vc.fp[self.vc.pos[compound]][None, :].astype(np.float64))[0]


@F.fitting
def fit_ridge(ctx) -> RidgeProfiles:
    return RidgeProfiles(ctx, ctx.extra["structure_vc"])


def ridge_predictor(ctx) -> RidgeProfiles:
    if "ridge_profiles" not in ctx.extra:
        ctx.extra["ridge_profiles"] = fit_ridge(ctx)
    return ctx.extra["ridge_profiles"]


@F.fitting
def prepare(ctx) -> None:
    """Build every fitted component before any vault opens; afterwards arms only predict.

    `make_policy` builds its model lazily under the same cache key, so it is built here too.
    """
    _model(ctx)
    ridge_predictor(ctx)


def ridge(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
    if not _eliminates(ctx):
        return _stop("registered_validator_cannot_eliminate")
    predictor = ridge_predictor(ctx)
    decisive, unpredicted = [], []
    for key in menu:
        profile = predictor.predict(compound, key)
        if profile is None:
            unpredicted.append(C.action_id(key))
            continue
        reading = C.read_profile(ctx.ft, key, profile, True, h1, h2, ctx.params)
        if reading["outcome"] in ("eliminate_a", "eliminate_b"):
            decisive.append((abs(reading["score_a"] - reading["score_b"]), setting.days(key), C.action_id(key), key, reading))
    if not decisive:
        return _stop("ridge_predicts_no_decisive_reading", unpredicted=unpredicted)
    gap, _, _, key, reading = min(decisive, key=lambda row: (-row[0], row[1], row[2]))
    return key, {"evidence_kind": "model_prediction", "predicted_reading": reading["outcome"], "score_gap": gap,
                 "ridge_alpha": float(predictor.models[key].alpha_)}


# ------------------------------------------------------------------------------ rungs 11-13: MAESTRO
def _per_hypothesis(forecast, h1, h2) -> dict:
    consequences = outcome_consequences(V.registered_rules(h1, h2))
    out = {}
    for branch in forecast.branches:
        own = branch.hypothesis
        other = h2 if own == h1 else h1
        correct = sum(p for label, p in branch.probabilities.items() if consequences.get(label) == frozenset({other}))
        wrong = sum(p for label, p in branch.probabilities.items() if own in consequences.get(label, frozenset()))
        out[own] = {"probabilities": dict(branch.probabilities), "p_correct": correct, "p_wrong": wrong,
                    "local_support": branch.support, "basis": forecast.basis}
    return out


def maestro(vc="on"):
    """`sequence_audit.policies.discrimination` (conditioned) with the virtual-cell channel explicit."""

    def arm(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
        forecaster = V.ReferenceCardForecaster(ctx.ft, ctx.params, minimum_references=1)
        actions = [P.make_action(k, h1, h2, setting) for k in menu]
        contrast = E.contrast_for(h1, h2, actions)
        forecasts = forecaster.forecast(contrast, actions, state)
        priorities = _vc_priorities(ctx, compound, menu, vc)
        plan = select_discriminating_action(frozenset({h1, h2}), actions, E.PROFILE, min(remaining, setting.step_budget),
                                            forecasts, outcome_consequences(V.registered_rules(h1, h2)),
                                            action_priorities=priorities)
        if plan.chosen is None:
            return _stop(f"acquisition_{plan.status}", vc_channel=vc, used_vc=bool(priorities))
        chosen = plan.chosen
        forecast = forecasts[chosen.action_identifier]
        return next(k for k in menu if C.action_id(k) == chosen.action_identifier), _prediction_note(
            _per_hypothesis(forecast, h1, h2), vc_channel=vc, used_vc=bool(priorities), priority=chosen.priority,
            discrimination_lower=chosen.discrimination_lower, support=chosen.support)
    return arm


def jev_unavailable(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
    raise RuntimeError("maestro_vc_jev is registered, not executed: provider_arm_reserved_for_external_study")


# ------------------------------------------------------------------------------ rung 14: oracle
def oracle_plan(real_ctx, compound, truth, h1, h2, setting, execute) -> tuple:
    """Best terminal utility, then fewest assay-days, then fewest measurements; reads hidden results."""
    results = {key: execute(real_ctx, compound, key, h1, h2)["outcome"] for key in setting.keys}

    def value(outcome):
        eliminated = {"eliminate_b": h2, "eliminate_a": h1}.get(outcome)
        return 0 if eliminated is None else (1 if eliminated != truth else -2)

    best = (0, 0.0, 0, ())
    for k1 in setting.keys:
        if setting.days(k1) > setting.budget_days + 1e-9:
            continue
        options = [((k1,), value(results[k1]))]
        if value(results[k1]) == 0 and setting.max_measurements >= 2:
            options += [((k1, k2), value(results[k2])) for k2 in setting.keys
                        if k2 != k1 and k2[1] >= k1[1] and setting.days(k1) + setting.days(k2) <= setting.budget_days + 1e-9]
        for sequence, v in options:
            days = sum(setting.days(k) for k in sequence)
            candidate = (v, days, len(sequence), sequence)
            if (candidate[0], -candidate[1], -candidate[2]) > (best[0], -best[1], -best[2]):
                best = candidate
    return best[3]


def make_oracle(real_ctx, execute):
    truth_of = real_ctx.data.compounds.drop_duplicates("compound").set_index("compound").klass.to_dict()
    plans = {}

    def arm(ctx, compound, h1, h2, executed, menu, remaining, setting, state):
        episode = (compound, h1, h2)
        if episode not in plans:
            plans[episode] = oracle_plan(real_ctx, compound, truth_of[compound], h1, h2, setting, execute)
        plan = plans[episode]
        if len(executed) >= len(plan):
            return _stop("oracle_defers" if not plan else "oracle_plan_complete")
        key = plan[len(executed)]
        if key not in menu:
            raise AssertionError(f"oracle plan {key} left the legal menu")
        return key, {"reads_hidden_outcomes": True}
    return arm


# ------------------------------------------------------------------------------ registry
REGISTRY = {
    "defer_floor": {"rung": 1, "build": lambda: defer_floor},
    "random_legal": {"rung": 2, "build": lambda: random_legal},
    "fixed": {"rung": 3, "build": lambda: fixed},
    "cost_only": {"rung": 4, "build": lambda: cost_only},
    "marginal_only": {"rung": 5, "build": lambda: marginal_only()},
    "retrieval": {"rung": 6, "build": lambda: retrieval()},
    "magnitude": {"rung": 7, "build": lambda: magnitude("on"), "vc": "on"},
    "magnitude_permuted": {"rung": 7, "build": lambda: magnitude("permuted"), "vc": "permuted", "control": True},
    "ridge": {"rung": 8, "build": lambda: ridge},
    "info_gain": {"rung": 9, "build": lambda: info_gain},
    "myopic_edv": {"rung": 10, "build": lambda: myopic_edv()},
    "decision_sensitive_edv": {"rung": 10.1, "build": lambda: decision_sensitive_edv},
    "maestro_masked": {"rung": 11, "build": lambda: maestro("masked"), "vc": "masked"},
    "maestro_vc": {"rung": 12, "build": lambda: maestro("on"), "vc": "on", "primary_candidate": True},
    "maestro_vc_permuted": {"rung": 12, "build": lambda: maestro("permuted"), "vc": "permuted", "control": True},
    "maestro_vc_jev": {"rung": 13, "build": lambda: jev_unavailable, "vc": "on",
                       "status": "registered_not_executed", "reason": "provider_arm_reserved_for_external_study"},
    "oracle": {"rung": 14, "build": None, "reads_hidden_outcomes": True},
    "production_default": {"rung": "R", "build": lambda: P.production},
    "sparse_two_step": {"rung": "R", "build": lambda: sparse_two_step()},
}
SWEEP = {"myopic_edv": myopic_edv, "sparse_two_step": sparse_two_step}
SWEEP_PRICES = (0.0, 0.005, 0.01, 0.05, 0.1, 0.2)
BASELINE_POOL = ("defer_floor", "random_legal", "fixed", "cost_only", "marginal_only", "retrieval", "magnitude",
                 "ridge", "info_gain", "myopic_edv")
CANDIDATES = ("maestro_vc", "decision_sensitive_edv", "production_default", "maestro_masked", "sparse_two_step")


def executed_arms() -> list[str]:
    return [name for name, spec in REGISTRY.items() if spec.get("status") != "registered_not_executed"]


def build(real_ctx, execute) -> dict:
    """Every executed arm, the oracle bound to the real context, and the price sweep."""
    table = {}
    for name in executed_arms():
        spec = REGISTRY[name]
        table[name] = make_oracle(real_ctx, execute) if name == "oracle" else spec["build"]()
    for name, factory in SWEEP.items():
        for price in SWEEP_PRICES:
            table[f"{name}@{price:g}"] = factory(price)
    return table


def vc_partners(compounds: list, fold: int, tier: str) -> dict:
    """A seeded permutation of the fold's held-out compounds with no fixed points (when n > 1)."""
    names = sorted(compounds)
    if len(names) < 2:
        return {c: c for c in names}
    rng = np.random.default_rng([SEED, int(fold), E.stable("vc_partner", tier)])
    order = list(rng.permutation(len(names)))
    partner = {names[i]: names[j] for i, j in zip(range(len(names)), order)}
    for position, name in enumerate(names):
        if partner[name] == name:
            # A bijection maps nothing else to `name`, so the exchange leaves neither end fixed.
            swap = names[(position + 1) % len(names)]
            partner[name], partner[swap] = partner[swap], partner[name]
    return partner
