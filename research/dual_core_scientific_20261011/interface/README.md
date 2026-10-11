# Frozen observation distribution to terminal decision value

This interface prototype reuses `maestro.acquisition.expected_terminal_decision_value`.
The hypothesis-conditioned observation likelihood is a planning input; it cannot create a
measurement, remove a hypothesis, or license a mechanism verdict. A useful observation can
change the terminal Bayes decision. A large response that cannot change that decision has
zero information value.

The opt-in runtime contract requires a SHA256-pinned external evaluation receipt, an explicit
terminal-loss policy, a utility-scale price for every admitted measurement, independent
reference-unit counts, and exact model, calibration, source and action-condition binding.
Experimental budget units remain separate. A refused value calculation executes no action;
the agent or repair planner cannot replace it with a coverage-based purchase.

Receipt authentication establishes file identity and binding only. The evaluator supplying
`admission_status=admitted` and `calibration_status=calibrated` must have independently tested
the outcome distribution and readout-to-endpoint transport. These flags are not model
self-certification, and synthetic contract checks are not biological validation.

`prototype.py` checks the decision-value trap before promoting the interface. The production
contract is `maestro.decision_value_policy.FrozenDecisionValuePolicy.from_receipt` and the
runtime opt-in is `MAESTROOrchestrator(selection_strategy="decision_value", ...)`.

The minimal receipt schema and synthetic fixture are in `tests/test_terminal_value_policy.py`.
The receipt's global `hypotheses_sha256` binds the complete, identifier-sorted registered
`MechanismHypothesis` records, including description, causal factor and proposed development
action; matching labels cannot borrow calibration for a different scientific question.
Every direct policy selection must supply those hypotheses. Runtime checks the actual contrast
before forecasting. Supplying `expected_hypotheses` to `run` or `run_case_loop` makes the
registered objects authoritative: the existing compiler restores those definitions from an
LLM proposal, and the proposal text cannot alter their meaning. Without registered objects,
the generated full definitions must still exactly match the frozen semantic hash.

The global `interpretation_sha256` is `decision_interpretation_binding(rules,
time_tolerance_hours=1.0, require_context_match=True)`. It fixes the complete registered
`OutcomeRule` records, including thresholds, typed premises, scope, conditions and independent
unit requirements, together with the interpretation table's time tolerance and context check.
Rule order and set insertion order do not affect identity. Runtime validates this binding
before calling the forecaster. Direct `policy.select` calls must pass `interpretation_rules`
and the same table settings; supplied consequences must equal `outcome_consequences(rules)`.
A new reading definition needs a newly evaluated receipt, even when its label is unchanged.

Each admission includes the endpoint, readout, context, model version, reference-unit count,
calibration ID and revision, source revision, complete action-binding hash, domain membership
and shift flags. Dose, assay, platform and time must be explicit. Calibration and source
revisions must match the forecaster's provenance. `decision_action_binding` includes every
registered action field plus the operating mode, dose, time and context. Revising a protocol
requires a separately evaluated, newly pinned receipt.

```python
from maestro.decision_value_policy import FrozenDecisionValuePolicy

policy = FrozenDecisionValuePolicy.from_receipt(receipt_path, expected_sha256)
controller = MAESTROOrchestrator.from_workspace(
    workspace,
    selection_strategy="decision_value",
    outcome_forecaster=independently_evaluated_forecaster,
    decision_value_policy=policy,
)
```

Receipt loading snapshots immutable policy data. `decision_value_selection_computed` records
gross and net value, terminal loss, wrong-decision probability, prices and named rejection
reasons; `decision_value_execution_gate` records the final action authority. Both independent
reference units and branch support have explicit minimums. The gate filters rejected and
unaffordable actions before invoking the forecaster. Repair may not change an approved action,
its conditions, its hypothesis definitions or its bundle multiplicity.

This is a myopic Bayes hypothesis-decision loss, not a validated development-action utility.
The existing measured-evidence decision engine still owns biological verdicts. Positive model
value is engineering eligibility for a new experiment, not proof of scientific or agent gain.
