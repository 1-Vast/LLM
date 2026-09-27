"""The protocol-v2 episode runner: truth-free execution on the public view, scoring joined afterwards.

File summary
- Path: research/protocol_v2/runner.py
- Purpose: run one arm on one (compound, contrast) under the shared rules and return a truth-free
  trace. The rules are protocol v1's `policies.run_matched` rules (menu, time order, measurement
  and assay-day budgets, QC-failure charge, stop on first elimination, registered validator and
  `EvidenceState`), with three changes.
- Core points:
  - The arm receives a `contracts.PublicContext`, not a sealed copy of the data.
  - The menu offers only conditions the design ran for the compound (`data.availability`), so a
    not-measured condition can no longer be bought and scored as a QC failure. Choosing one anyway
    raises `NotMeasured`.
  - The arm sees each executed step as (key, action, registered outcome, QC flag, eliminated,
    its own note). The validator's scores and template counts stay in the evaluation record.
  - No truth enters `run_episode`. `contracts.score` joins it afterwards.
- Interfaces: `run_episode`, `local_setting`, `audit_trace`
- Depends on: contracts.py, research/sequence_audit/policies.py, research/dynamic_world_model
"""
from __future__ import annotations

from dataclasses import replace

from . import contracts as K

P, C, E = K.T.P, K.T.C, K.T.E


def local_setting(setting, available):
    """The setting restricted to conditions the design ran for this compound (order preserved)."""
    return replace(setting, keys=tuple(k for k in setting.keys if tuple(k) in available))


def _public_step(step: dict) -> dict:
    return {k: step[k] for k in ("key", "action", "outcome", "qc", "eliminated", "note")}


def run_episode(arm_name: str, arm, view, real_ctx, compound, h1, h2, setting, *, execute=None) -> dict:
    """One episode; the trace carries no truth. `real_ctx` is used only by the executor."""
    execute = execute or E.execute
    available = view.data.availability.get(compound)
    if available is None:
        raise K.NotMeasured(f"no_design_metadata_for:{compound}")
    local = local_setting(setting, available)
    actions = {key: P.make_action(key, h1, h2, local) for key in local.keys}
    contrast = E.contrast_for(h1, h2, list(actions.values()) or [P.make_action(setting.keys[0], h1, h2, setting)])
    state = K.T.P.EvidenceState.open(contrast.hypotheses)
    steps, public, stop, offered = [], [], None, []
    while True:
        if state.eliminated:
            stop = "eliminated"
            break
        if len(steps) >= local.max_measurements:
            stop = "measurement_budget_spent"
            break
        remaining = local.budget_days - sum(local.days(tuple(s["key"])) for s in steps)
        menu = P.legal_menu(local, steps, remaining)
        if not menu:
            stop = "no_legal_action"
            break
        offered.append([C.action_id(k) for k in menu])
        key, note = arm(view, compound, h1, h2, [dict(s) for s in public], menu, remaining, local, state)
        if key is None:
            stop = (note or {}).get("reason") or "arm_stopped"
            break
        key = tuple(key)
        if key not in menu:
            if key in setting.keys and key not in local.keys:
                raise K.NotMeasured(f"{arm_name} chose {key} for {compound}, which the design did not run")
            raise ValueError(f"{arm_name} chose {key}, which is not in the legal menu")
        result = execute(real_ctx, compound, key, h1, h2)
        measured = K.measurement_state(result)
        if measured is K.MeasurementState.NOT_MEASURED:
            raise K.NotMeasured(f"availability metadata says {key} ran for {compound}, but no row exists")
        state, interpretation, outcome = C.evidence_update(
            state, contrast, actions[key], key, result, h1, h2, qc=result["qc"], agreement=result["agreement"],
            source=f"{setting.name}:{compound}")
        step = {"key": list(key), "action": C.action_id(key), "outcome": outcome, "qc": bool(result["qc"]),
                "state": measured.value, "outcome_class": interpretation.outcome_class.value,
                "eliminated": sorted(state.eliminated), "note": note or {},
                "validator": {k: result.get(k) for k in ("score_a", "score_b", "templates_a", "templates_b")
                              if k in result},
                "agreement": result.get("agreement")}
        steps.append(step)
        public.append(_public_step(step))
    keys = [tuple(s["key"]) for s in steps]
    return {"arm": arm_name, "compound": compound, "h1": h1, "h2": h2, "stop": stop, "steps": steps,
            "remaining": sorted(state.candidates), "measurements": len(steps),
            "days": float(sum(local.days(k) for k in keys)),
            "wells": 2 * len(keys) + 4 * len({(k[0], k[1]) for k in keys}),
            "offered": offered, "menu_size": len(local.keys), "unavailable_conditions": len(setting.keys) - len(local.keys)}


def audit_trace(trace: dict, setting) -> list[str]:
    """Shared-rule violations in one trace (protocol v1's `audit_record`, plus the state rules)."""
    problems = []
    steps = trace["steps"]
    if len(steps) > setting.max_measurements:
        problems.append("too_many_measurements")
    if trace["days"] > setting.budget_days + 1e-9:
        problems.append("over_budget")
    times = [s["key"][1] for s in steps]
    if times != sorted(times):
        problems.append("time_order")
    if len({s["action"] for s in steps}) != len(steps):
        problems.append("repeated_action")
    for i, s in enumerate(steps):
        if s["state"] == K.MeasurementState.NOT_MEASURED.value:
            problems.append("not_measured_condition_executed")
        if i < len(steps) - 1 and s["eliminated"]:
            problems.append("continued_after_elimination")
        before = steps[i - 1]["eliminated"] if i else []
        if s["state"] == K.MeasurementState.QUALITY_FAILED.value and s["eliminated"] != before:
            problems.append("qc_failure_changed_evidence")
        if s["state"] != K.MeasurementState.MEASURED_ELIMINATING.value and s["eliminated"] != before:
            problems.append("non_eliminating_state_changed_evidence")
    if "truth" in trace:
        problems.append("trace_carries_truth")
    return problems
