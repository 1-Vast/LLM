# Convergence: one execution path, explicit research and reproduction boundaries

This iteration narrows maintenance to two scientific questions and extracts cohesive
production responsibilities. It does not qualify a new biological task, checkpoint,
mechanism model or policy benefit. Predictions remain planning inputs; qualified
measurements retain their own evidence-admission requirements.

The implementation starts at `3b7935f`; execution changes are in `0b6fe51`, and the
asset-dependent test-scope correction is in `d116eda`. The machine receipt and
per-stage failures are under [results/20261003_convergence_v1](results/20261003_convergence_v1).
Counts from overlapping scopes must not be added. The dated log is navigation;
this report owns the interpretation and reproduction details.

## Responsibility and state ownership

| Responsibility | Single maintained owner | Boundary |
|---|---|---|
| Query construction, request binding, safe inference, raw cache and prediction logging | `src/agent/prediction.py:PredictionCoordinator` | No action selection, measurement interpretation or mechanism mutation |
| Plans, original plan versions, execution receipts, results, declared budget use and prediction/result ownership | `src/agent/case_store.py:CaseStore` | SQLite facts; no second execution ledger |
| Evidence admission, mechanism compatibility, budget/coverage/discrimination algorithms | Existing `src/maestro/` functions | Original scientific meanings and refusal rules retained |
| Candidate-to-plan selection | `MAESTROOrchestrator._select_budgeted_actions` | One named policy chooses among existing algorithms; final execution constraints still apply |
| Text memories, reflections, original round views and run-summary reconstruction | `src/agent/memory.py` | Derived context/audit only; never a replacement for CaseStore facts |

Historical `agent.memory` imports of CaseStore and its four associated types remain
aliases to the extracted implementation. Production consumers import from
`agent.case_store`. The shared SQLite transaction helper moved with the fact store;
it was not copied into another utility framework. The coordinator owns its cache
and parallelism validation; no controller-side duplicate prediction cache remains.

The existing main path remains: inspect case state, produce candidates, filter
execution prerequisites and budget, obtain bound predictions, select, perform
final constraints, commit the versioned plan, import results through the existing
importer, and update only admissible scientific state. A waiting case still skips
planning and model calls. A failed arm does not prevent receipt of committed
sibling results. Refusal reasons and actual result ownership are preserved.

`selection_strategy` is one of `budgeted_coverage`, `expected_coverage`, or
`discrimination`. The constructor defaults to budgeted coverage; the workspace
factory retains its previous expected-coverage default. The old constructor flags
translate once to a policy for compatibility; legacy discrimination takes precedence
when both old flags are true, as before. A named policy combined with enabled legacy
flags is rejected. Discrimination still requires an outcome forecaster. Coverage,
expected coverage and mechanism discrimination keep separate algorithms and units;
no heuristic is renamed information gain or combined into a new weighted score.
Outcome forecasts remain shadow diagnostics unless discrimination is selected.

AST-based checks confirm that all eight extracted prediction methods, all 23
existing CaseStore methods and its three transaction/refusal helpers preserve their
bodies after the declared prediction ownership/name changes. Behavioral tests verify
actions, query/cache identity, plan versions, budget, result ownership and refusals;
AST equality alone is not the acceptance criterion. Named and legacy policies are
also compared on the same synthetic conditions, including forecaster disagreement.

## Restart: receiving facts versus rebuilding an old interpretation

`CaseStore.pending_actions(case_id)` returns original plan/action identity, pending
status, declared cost, context, time, expected conditions and available execution
attempt/source fields. These are stored receipt fields, not a reconstructed complete
EvidenceAction, permission to execute again, or a monetary invoice. No new action
envelope or transaction schema was needed just to receive outstanding results.

The existing `MAESTROOrchestrator.import_measurement` remains the result entrance.
Two separate Python processes receive the original failed and valid sibling results
using empty planner stubs. Tests check that the old version remains one, an exact
retry is not charged again, the sibling remains pending after the first receipt,
and both attempts' declared use remains visible. A changed result must still pass
the original identity and condition checks; restarting does not assign it to the
latest similarly named action.

New RunLogger round receipts bind case and plan version. Plan and result views are
immutable: exact repeats are allowed, conflicting content cannot overwrite them.
`RunLogger.review_case(case_id, store)` authenticates the saved views against their
receipt hashes, case/result ownership and consistent original plan binding. It
deduplicates receipt retries, retains every result, and rebuilds the summary using
the already-recorded execution layers. Tests exercise both orders of a revised
and non-revised judgement in a new process, hash corruption, incomplete result
views, and old unbound views. Missing historical interpretation is a blocker; the
review does not call an LLM, infer missing outcomes, or run today's evidence rules.

This is not automatic recovery of all scientific state. Mechanism states, repair
ledgers and aggregate reliability weights remain process-local. Exact bound
prediction/result pairs and scores have their existing CaseStore persistence and
reconciliation tests. Facts imported without a saved result interpretation can
still be received, but cannot produce a claimed complete historical run review.
Old logs without case/plan bindings are not silently upgraded. A future scientific
restart needs explicit original rule/version replay or a separately registered
new interpretation, rather than treating an audit summary as evidence state.

Example read-only inspection after restart:

```python
from pathlib import Path
from agent.case_store import CaseStore
from agent.memory import RunLogger

runtime = Path("RUNTIME_DIRECTORY")
store = CaseStore(runtime / "cases.sqlite")
pending = store.pending_actions("EXACT_CASE_ID")
# Supply a real MeasurementResult, with its original plan_version, to the existing
# orchestrator.import_measurement entry. Do not rebuild or recommit the plan.
summary = RunLogger(runtime).review_case("EXACT_CASE_ID", store)
```

## Tools and experimental entries

| Previous tool component | Current disposition | Reason |
|---|---|---|
| `resistrace_retrospective` | Entire fixed Ridge/cohort/holdout experiment in `research/astra` | Changing the study changes its experimental contract |
| `state_evidence_followup` | Cycloop controller and original-log replay in ASTRA; design-specific `assess` and source hashing stay tools | Separate controller-specific reconstruction from scientific admission |
| `state_raw_reconstruction` | Fixed official-checkpoint experiment in ASTRA; `convert_counts` stays tools | Reusable strict ordered-axis/count conversion has separate input requirements |
| `state_prospective_certify` | ASTRA | Fixed technical forward/invariance experiment; source snapshot paths updated after migration |
| `state_prospective_review` | ASTRA | Fixed source review and Liveseq metadata experiment |
| `state_search_acquire` | Tools | Receipt-driven acquisition under an explicit input plan |
| `state_search_build` | Tools | Source-format parsers and five-table relationship construction; frozen source-review audit only, no fitting or efficacy estimation |
| `state_raw_review` | Tools | Source schema/locator reconstruction with pinned source-specific adapters, not an outcome-selection experiment |
| `state_prospective_input`, `state_remote_h5` | Tools | Ordered input, availability/leakage and range-reading contracts |
| `astra/reproducibility_audit` | Research | Deliberately bound to the existing frozen replay assets; no second reuse case warrants a generic recovery service |

The moving functions retain AST-equivalent experiment bodies. ReSisTrace source
bytes move unchanged. No new experiment was executed by migration; only imports,
help entry points, contracts and previously saved reconstruction checks ran.
Historical snapshots, failure receipts and commands remain at their pinned versions.
Current commands use `python -m research.astra.MODULE`; installed tools do not regain
a dependency on research. No entire experimental controller was promoted.

ASTRA DecisionPath stays research-owned. Its ScientificQuery/ExecutionBinding schema,
research raw cache, injected selector and reviewer/repair callbacks differ from the
production PredictionRequest/QueryAssessment coordinator, named acquisition entry,
repair contracts and evidence interpreter. Both use the same production CaseStore;
its facts were not merged with the scientific EpisodeStore. A research prediction
or custom selector still requires its own scientific evaluation before default use.

## Verification scopes and actual execution

The default pytest list is the explicit production contract subset in
`pyproject.toml`. Collection markers label `core`, `regression` and `research`;
they do not skip missing assets. Root conftest owns import paths and scope labels.
The test extra supplies pytest and NumPy: current adapter/artifact imports use
NumPy, so pytest alone is insufficient even without weights or biological data.
STATE inference's larger optional dependencies are not needed by this core subset.

The research runner defaults to ASTRA. Paused/historical directories require explicit
pytest paths; `--include-archives` retains explicit historical-tree collection.
No historical code was deleted or relabelled as scientifically valid. The package
dependent engagement lint test was moved intact to the existing engagement package
suite after clean Linux exposed its asset dependency; its checks were not removed.

| Executed scope | Result | Evidence boundary |
|---|---|---|
| Before-extraction critical behavior tests | 146 passed | Original Windows maestro, base `3b7935f` |
| Original full aggregate after execution changes | 1,980 passed; no failures/errors/skips | Existing Windows maestro and its existing optional assets; not a clean full-research reproduction |
| Final core | 311 passed in each of Windows and clean Linux; no failures/errors/skips | Explicit asset-free subset; scopes overlap the full aggregate |
| Scope-correction checks | 29 passed | Original Windows assets; verifies the relocated engagement test too |
| New-process result/review and research-scope checks | 9 passed | Software fixtures, not physical repeats |
| Linux published replay, before restoration | 7 passed, 1 failed, 4 errors | Missing arrays and original-byte mismatch are visible blockers |
| Linux published replay, after exact restoration | 12 passed | Only the already-published 392-member and 16-member archives; includes overlaps |

Linux is Ubuntu under WSL2, Python 3.12; Windows maestro is Python 3.11. The Linux
core starts from a new shallow source checkout with an empty Git status and its own
isolated environment. The replay step adds pandas, authenticates the two published
archives and every member before restoring exact bytes. The prepared replay checkout
then has four tracked original-byte overlays: pack JSON, pack manifest, saved replay
results and the historical freeze protocol. This is the documented raw-byte convention,
not a modified frozen expectation. No Windows original dataset cache, model weight,
PISA supplement or Level5 matrix was copied into this Linux checkout.

Earlier failure receipts are retained. An initial command named a nonexistent test
file and ran no tests; the corrected baseline passed. Extraction first omitted UUID
and then the coded refusal helper; the saved failing scopes precede their repairs.
The first minimal Linux attempt lacked NumPy and failed collection; declaring/installing
the actual test dependency fixed this. The first clean core also exposed one asset
dependent skip, which caused the explicit scope correction. These are engineering
failures, not biological negative observations or passed independent confirmations.

All 2,058 protected original Windows worktree hashes remain unchanged and the old
day-log prefix is preserved. The known historical Git-LF versus original-CRLF
distinction remains binding; source equivalence cannot replace a raw-asset digest.
The Linux full scientific suite, clean reconstruction of large sources, STATE
forwards, live model APIs, new model training, physical experiments, biological
state gain and agent/mechanism utility were not run this iteration.

## Reproduction

Run core contracts in a clean checkout and a new environment:

```bash
python -m pip install -e '.[test]'
python -m pytest
```

Restore the published small regression packages into a prepared checkout, keeping
the original raw-byte differences visible:

```bash
python -m pip install pandas
python -m research.astra.reproducibility_audit --restore-fixtures-from research/astra/results/20261003_prediction_audit_fix_v1/replay_fixture_bundle.zip --out NEW_OUTPUT/restored_first.json
python -m research.astra.reproducibility_audit --restore-fixtures-from research/astra/results/20261003_prediction_audit_fix_v1/legacy_fixtures_v3/replay_fixture_bundle.zip --out NEW_OUTPUT/restored_legacy.json
python -m pytest research/case_memory_integration/test_external_evaluation.py research/astra/test_reproducibility_audit.py -m regression
```

The actual Linux clone/install/restore/check commands and package versions are in
`results/20261003_convergence_v1/linux_verify.sh` and its new receipt directories.
That script accepts source repo, a new Linux checkout, an isolated Python environment
and a new receipt directory. Its unprepared regression failure is intentional and
recorded, not converted to a success. This Ubuntu installation lacked ensurepip;
the isolated environments were created with `python3 -m venv --without-pip`, then
bootstrapped using `https://bootstrap.pypa.io/get-pip.py` (downloaded SHA256
`fb24e693bab954209a063d90953621412ccad4a500905a726286e038f508ddf6`).
No system Python or Windows maestro dependency was changed. To run the original full aggregate with the
existing maestro dependencies and verified assets:

```bash
python -m pytest tests research/astra research/scientific_optimization/test_population_flow.py research/scientific_optimization/test_response_training.py research/case_memory_integration/test_external_evaluation.py -o addopts= -q
python -m research.astra.convergence_audit --out NEW_OUTPUT/convergence_parity.json
```

The parity audit needs the base Git revision (fetch it if the checkout is shallow).
The full aggregate's original caches and optional assets are documented in
[PREDICTION_AUDIT_FOLLOWUP.md](PREDICTION_AUDIT_FOLLOWUP.md). Missing large assets
remain unrun/blocked dependencies; neither the core nor the small replay proves
full scientific or biological portability.

## Two maintained scientific questions and their next discriminating work

| Main line | Existing evidence and uncertainty | Next experiment and continuation rule |
|---|---|---|
| Cheap predecision state changes action ordering beyond background | Historical sensitivity and retrospective response analyses do not establish prospective state gain. Culture independence, readable state time, complete executed menu and prices still need evidence. | Collect non-destructive cell count/confluence or a frozen small marker panel before decision; independently start cultures, randomize the full intervention menu and positions, match controls and seal whole cultures into splits. Compare fixed action, background-only, background + state, permuted state and a simple predictor under matched budgets. Continue only if held-out state-dependent action contrasts recur and a prespecified meaningful utility gain is supported. If state only predicts overall response magnitude, retain prediction research but stop claiming action-selection gain. If background/simple predictors explain the gain, modify the model claim. |
| Actual intervention realisation improves response-difference prediction and mechanism evidence acquisition | The measured-realisation intake remains incomplete; no trained contribution or two-round scientific benefit is demonstrated. STATE expression predictions are not calibrated mechanism-conditional observation probabilities. | Use a limited same-target pharmacological/genetic comparison with dose/time/context, actual engagement or knockdown, proximal function, matched phenotype, QC failures and attempt ledger. Train a direct baseline versus a model predicting realisation from legal inputs and constraining downstream response through that predicted quantity. Hold out interventions/conditions and entire physical cultures. Continue only if independent response-difference prediction and then equal-budget evidence acquisition improve; stop the claimed model contribution if the direct model is as good. Mechanism conclusions require declared competing predictions, valid measurement and original interpretation premises, including coexistence/unknown and hypothesis-set failure. |

The first line's informative quantity is the *relative* action contrast conditional
on state and background, rather than a larger average predicted response. Ranking
ties or an unchanged best action are legitimate negative outcomes. Missing actions
retain prespecified utility bounds; predicted responses never fill observation tables.
State processing/waiting and collection enter deployment costs, and technical
repeats do not become independent cultures or physical confidence intervals.

For the second line, future measured realisation is a training target or a newly
acquired first-round observation, not an input secretly available before the original
decision. A prospective model must predict realisation from legal information.
An analysis conditioning on actually measured future realisation is a separate
retrospective/upper-bound experiment. RNA, binding, proximal activity and phenotype
remain different evidence levels. A model-mediated predictive gain alone does not
identify a causal mediation effect.

Both lines need a concrete frozen endpoint, action menu, minimum meaningful gain,
prices, refusal costs and confirmation sample-size rationale before held-out outcomes
are examined. Those unknown quantities were not guessed here. The existing 480-well
GDSC pilot can test full-menu phenotype differences and variance if actually executed;
it does not supply the absent state chronology or pharmacological/genetic mechanism
records by itself. No additional research branch or default model was opened.
