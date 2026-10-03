# Close verified feedback defects; freeze the main architecture

This iteration follows the review of `2a8091c98ec1d8bbb1f0b36ea86f61e26878e56a`.
The existing controller, PredictionCoordinator, CaseStore, evidence ledger and
selection algorithms retain their ownership. No new backend, agent, store,
controller or full scientific recovery framework is introduced. Subsequent
architecture changes should require a reproduced execution defect or a specific
frozen research need. Performance/inference batching is deferred.

## Verified defects and surgical fixes

Four new behavior tests were copied to a separate detached base worktree. All four
failed on the old source, independently of the new implementation:

| Boundary | Base reproduction | Current behavior |
|---|---|---|
| Two simultaneous sibling results | Two results exist, spent is 1 instead of 2, case remains awaiting | `BEGIN IMMEDIATE` precedes the first read; budget, action completion and case state commit together |
| Interrupted result projection, then retry | Same-case evidence remains absent | Retry rereads the immutable accepted CaseStore fact and idempotently projects case-scoped evidence without another charge |
| Two same-drug action doses | Both requests contain 10 nM instead of 10 and 1000 nM | Exact dose/unit/time conditions bind the action to its own query and cache identity |
| Interrupted score persistence | No interruption occurs because the runtime never invokes persistence | Accepted prediction/result pairs persist their score before changing planning reliability; retry repairs the score |

The [base receipt](results/20261003_feedback_closure_v1/base_reproduction.txt)
retains the expected failures. The concurrent test synchronizes entry, and on the
old implementation also forces unlocked first readers to see the same case state.
The fixed implementation locks before either first read. Additional tests cover
same-result concurrent retry, concurrent evidence projection, missing projection
repair, case isolation and next-round ContextBuilder visibility.

`ContextBuilder.record_result` now has an optional case binding. Case projections
require accepted result ID and plan version, use a stable evidence ID and preserve
structured context, time, conditions, metrics, QC, experimental units, limitations
and interpretation fields. EvidenceLedger's insert/check transaction is serialized
so two projection retries cannot race to insert the same ID. CaseStore remains
the authority; projection failure does not roll back an already accepted fact.
Repeating its accepted import repairs the view. Historical unscoped rows remain
unchanged; nothing relabels their origin or upgrades their scientific support.

`Intervention.for_action` is the shared binding/check used by per-action query
construction and ranking/scoring compatibility. It handles explicit drug identity,
mode, dose and unit, dose_nM/dose_uM aliases, time, context and readout. Dose strings
such as `10 nM` are parsed conservatively; unknown, ambiguous or inconsistent
units are rejected. Concentration units remain explicit: there is no guessed
conversion, assay equivalence or biological effect. Conditions the current
Intervention cannot express refuse a query with a named reason. A completely
refused per-action template never falls back to one shared prediction. An explicit
caller request must already match its action; it is not silently rewritten.
Opaque historical perturbation labels are not decoded into assumed doses.

## Recovery is a capability boundary

Saved scores use `runtime_prediction_score_v1` and the versioned deterministic
reliability policy, retaining original model/readout, source cluster, result,
conditions and plan pairing. Construction restores these scores in SQLite commit
order, validates original prediction/fact identities, and uses the existing source
deduplication and model-version boundaries. Three independent matching synthetic
interval misses remain revoked after rebuilding the controller, and an unchanged
new-case menu selects the same actions before and after rebuilding. A different
aggregation policy requires explicit migration and is rejected rather than
silently reinterpreting history. These saved scores affect planning influence;
they do not establish new calibration evidence or mechanism conclusions.

`recovery_capabilities(case_id)` distinguishes fact/result/budget access from
scientific continuation. After restart, a previously measured case cannot silently
start a new selection with an empty mechanism state. It returns the named
`scientific_state_not_restored` blocker without invoking the planner. Original
pending results can still be accepted and exact prediction pairs reconciled.
Historical audit reconstruction continues to read original saved interpretations.
Starting a second case-loop invocation after measured history is also blocked as
`scientific_loop_state_not_restored`: that invocation would otherwise lose local
premises, units, scope and repair trajectory even in the same process.

This is deliberately conservative; complete scientific restart is **not**
implemented. An explicitly registered new analysis needs a new case/analysis ID,
declared hypotheses, original provenance and an independent evidence-admission
design. Renaming a case alone does not certify transferred scientific state.
The current controller does not reconstruct historical mechanism exclusions or
repairs by re-running newer rules or an LLM.

## State and selection contracts

`run` and `run_case_loop` accept the existing typed `UserStateContext`, including
the existing `user_state_from_compiled` output. Explicit state reaches the
OutcomeForecaster's extended protocol without replacing response-prediction
semantics. A mismatched cell context is rejected. Three-argument legacy forecasters
still run when no state is supplied; a state-aware call is never silently downgraded
to ignore supplied state. A fixed-menu test uses an intentionally separating
synthetic forecaster: changing only state changes the selected action and leaves
mechanism evidence unchanged. This proves interface wiring, **not STATE biological
gain or a validated mechanism probability mapping**. The caller still must certify
measurement chronology, lawful inputs and the chosen forecaster's domain.

Decision-mode forecast failures now stop acquisition by default. The explicit
`forecast_failure_policy="coverage"` option permits the historical coverage
fallback and logs that change; diagnostic/shadow failures retain coverage without
claiming forecast-driven choice. Response magnitude remains diagnostic on
expected coverage and at most a final tie-break on the existing applicable paths;
the prior negative keep rule is not relaxed. No RNA response is converted to a
mechanism-conditional outcome distribution.

Every actual planning run records its named strategy, fallback parameters,
prediction role, rule contract/table, action menu, original/remaining budget,
backend and supplied-state digest. The CLI exposes an explicit coverage strategy;
the maintained evaluation factory explicitly names `expected_coverage` rather
than depending on the workspace factory's compatibility default. Archived
research implementations and frozen historical scripts retain their original
configuration. The new scientific pilot uses a fully declared precommitted lookup,
not either orchestrator default. Future studies must register model/checkpoint,
query/preprocessing versions and stopping rules before outcomes are opened.

Default test membership is now checked before collection. Existing core files,
two distributed regression files, and maintained noncore tests have explicit
assignments in pyproject. A new file in `tests/` or the maintained ASTRA top level
must be registered even when a default run would not collect it. Overlapping
assignments fail. Archive directories stay outside this maintained check and the
existing explicit opt-in research runner continues to own their collection.
No missing-asset skip was added and the original core file list remains intact.

## Scientific delivery and genuine blockers

The new [sealed protocol](results/20261003_feedback_closure_v1/protocol/protocol.json)
and [readiness decision](results/20261003_feedback_closure_v1/protocol/readiness.json)
prioritize the **complete-menu cheap-background policy pilot**. The
[builder](feedback_protocol.py) verifies the original allocation manifest, refuses
already executed/measured rows, checks 12 lines/24 planned starts/480 wells and
seals a new design without changing the old allocation. No target outcomes are
read. The future primary comparison is the frozen roster recommendation versus
fixed Afatinib; other two fixed actions are prespecified secondary comparisons.
All three actions are measured, and paired action contrasts are reported per
culture with technical repeats and shared controls explicitly distinguished.

The proposed endpoint is blank-corrected ATP relative to matched terminal vehicle,
then `1 - normalized_ATP` without clipping. It is not cell death, GR, clinical
response or mechanism confirmation. The roster is enriched by old recommendation
strata, so the scope is this pilot population, not general policy value. Physical
units require verified independent culture starts; missing actions remain
unidentified without genuine predeclared outcome/cost bounds. Model predictions
cannot fill their outcomes. Prior historical GDSC outcomes were already examined
and are not represented as fresh held-out confirmation.

Execution is explicitly **blocked**, with **zero actual physical attempts** in
the supplied allocation. Missing original records include:

- Certified culture/parent/sister relationships and independent starts.
- Operator-approved assay handling, controls and independently justified numeric QC.
- Background available before decision, followed by actual allocation/execution/endpoint events.
- Complete attempts, failure/unused-action reasons and raw outcome/hash records.
- Credible prices, failure/refusal loss and a pre-outcome minimum meaningful net gain.
- Physical variance and a confirmation sample-size rationale.

The protocol freezes these missing fields as unknown; it does not fill them with
arbitrary values to claim an execution-ready confirmation study. Release requires
a separate immutable pre-outcome execution registration supplying them. The old
allocation is a feasible proposal, not evidence that the laboratory conditions,
resource bounds or scientific comparison have been certified.

Cheap-state comparisons have a separate next registration: full menu within
background, background vs background + predecision confluence/cell count, local
state permutation and a simple predictor with identical legal inputs/budgets.
Whole physical connected units enter one split. State collection/processing/waiting
and failed attempts enter deployment cost. If state only changes common response
magnitude, or simple/background models explain the effect, stop or narrow the
action-ordering/model claim. Agent supplementation/stop-policy evaluation waits
for a real evidence-action menu, outcomes and prices. Mechanism acquisition waits
for genetic/pharmacological comparisons, measured realisation, proximal function,
and validated competing predictions. The ATP pilot cannot substitute for them.

## Verification and reproduction

The [run receipt](results/20261003_feedback_closure_v1/receipt.json) owns exact
counts, environment, source and asset hashes, successful/failed runs and unrun work.
Execution code is `7c5c962`. Final maestro core passed **342**, the full registered
aggregate passed **2,013**, and a clean native Linux checkout with an isolated
declared-test environment passed **342** core tests. Each final run had zero
failures, errors and skips. Counts overlap and must not be summed. All **2,058**
protected historical hashes, the initial day-log prefix and the 19 artifacts in
the previous efficiency receipt remain unchanged. Clean Linux full-research and
asset-restored regression were not repeated in this iteration.
Intermediate failures are retained: result projection changed an old unscoped
retrieval expectation; a historical context refusal string was initially changed
then preserved; new logging exposed frozenset serialization; initial new fixtures
used conflicting legacy flags, an invalid request ID, a wrong test log path and a
missing empty-plan field. The first full aggregate exposed four manually allocated
anonymous scoring fixtures missing `_case_store`; those now explicitly declare
no persistent store. A protocol test edited the wrong occurrence of a CSV boolean;
it now edits the executed column structurally. None of these failures was skipped
or used to weaken scientific admission. All failure receipts remain available.

Run from `D:\MAESTRO` in maestro, always using new output paths:

```powershell
$py = 'D:/anaconda/envs/maestro/python.exe'
$env:PYTHONPATH = 'src'
& $py -m pytest -o addopts= -q --junitxml=NEW_OUTPUT/core.xml
& $py -m pytest tests research/astra research/scientific_optimization/test_population_flow.py research/scientific_optimization/test_response_training.py research/case_memory_integration/test_external_evaluation.py -o addopts= -q --junitxml=NEW_OUTPUT/full.xml
& $py research/astra/feedback_protocol.py --out NEW_OUTPUT/sealed_protocol
```

For base reproduction, use a detached `2a8091c` worktree and copy the current
`test_case_lifecycle.py`, `test_restart_contract.py`, and
`test_agent_world_model_integration.py` test files into that disposable worktree.
Run only `-k 'parallel_results_update_budget or result_retry_repairs_scoped or action_dose_is_preserved or reliability_survives_restart'`.
Four base failures are expected; the same cases pass on the execution revision.
This never edits historical source in the main checkout. Clean Linux verification
uses the existing exact environment recipe with a new native clone and environment;
the new receipt records the execution revision and that run's scope.

No new STATE forward, live model API/LLM experiment, training, cell experiment,
biological calibration, policy-value, state-gain or mechanism-benefit study ran.
No end-to-end STATE batch-inference benchmark ran. No unverified architecture or
scientific model was promoted. Software fixes close demonstrated feedback gaps;
the central scientific questions remain unanswered until the missing real records
and pre-outcome registration are supplied.
