# Feedback attribution, ownership and measured-realisation follow-up

Date: 2026-10-03. Starting main: `52715c310e40667bee419ac27e57a68375ef2d5c`.
Environment: `D:/anaconda/envs/maestro/python.exe`; existing dependencies retained.
The supplied review and local `research/data` inputs were inspected before editing.
This iteration verifies engineering responsibilities and prepares a concrete biological
development design. It does not establish a new model or policy benefit.

## Reproduced defects and corrected behaviour

The first regression run reproduced both reported faults: **100 passed, 11 failed**.
The failures include malformed plan-version cases and second-plan attribution, not
eleven independent biological defects. Original failure receipts are retained.

1. CLI `_results` preserves `plan_version` and accepts only a positive integer when
   supplied. Boolean, floating, string, zero and negative versions are rejected.
   An omitted version stays unknown; no automatic latest-plan assignment is added.
   A real CLI parser/CaseStore integration test imports repeated actions into plans
   1 and 2 and verifies the original result identities and budget charges.
2. The main loop processes all selected siblings in the committed bundle after a
   QC failure, retaining each independent result, reflection and declared budget charge.
   It does not start another planning round. An unavailable sibling leaves the case
   awaiting results, with the QC failure retained as the primary stop reason.
   For a fully received failed bundle, the existing diagnostic decision remains
   available without overwriting the persisted QC-failed state.
3. Pending results are checked before terminal decision persistence. A prediction
   rejected as a measurement cannot close or charge the pending physical plan.

The result provider remains a caller-owned intake boundary, not a newly implemented
laboratory execution service. It returns a result already produced for the committed
action, or `None`; the extra intake call does not authorize a new experiment.
Plan identity, measured conditions and QC still pass existing storage/admission rules.

## Verified responsibility migration

| Change | Authority and validation | Scientific/default boundary |
|---|---|---|
| Two promotion test modules moved into `tests/` | Default engineering regressions; shared synthetic fixtures in `tests/fixtures/` | No biological observations or scientific promotion |
| ASTRA runtime/scoring forwarding modules retired | Direct imports from `agent.orchestrator`, `virtual_cell.state_adapter`, `maestro.case_update` | Retired bytes preserved in a new inert archive |
| Duplicate LINCS pack implementation retired | One builder/loader in `tools/datasets/lincs_pack.py`; research callers use it | Historical selection rules and protocol deviation unchanged |
| LINCS replay/evaluation moved out of tools | Existing `research/case_memory_integration/external_replay.py` owns the scientific commands | No installed tool imports `research`; no new result computation |
| Transcript fitting and population experiments moved out of production | `research/scientific_optimization/response_training.py` and `population_model.py` | Experimental fitting stays opt-in; no activation of the population backend |
| Transcript inference retained | `DoseAnchoredNetwork`, `LearnedTranscriptWorldModel`, `transcript_readouts` and the inference-used `ResponseFit` holder remain production-owned | State-dict keys, checkpoint loading and prediction semantics preserved |
| Duplicate numeric parsing consolidated | Existing `engagement_sources._number` used by both construction paths | Same missingness/nonfinite interpretation |
| Dataset backend imports corrected | Live tools import `virtual_cell.state_runner`, not checkout-only `src.virtual_cell` | Frozen source snapshots untouched |
| Explicit pack workspace | Builder/loader accept `workspace`; installed pack CLI accepts `--workspace` | Source/graph workflow remains checkout-scoped; no automatic asset download |
| Routine research collection excludes source archives | Explicit default ignore rules; `--include-archives` for deliberate historical collection | Active legacy-defect tests can still load pinned source intentionally |

No production/tool Python file was added or deleted: **98 before, 98 after**.
The initial **1,791** protected files, including supplied review inputs, retain their
original SHA256 values. Retired active sources are preserved separately; historical
evidence and manifests were not rewritten. `research/data` stays byte-preserved as
reference copies and is excluded from routine research collection.

The installed wheel was built without dependency resolution, installed to an isolated
temporary target, and tested with Python `-I` outside the checkout. Module paths
resolve to the installed target; explicit workspace loading succeeds; production
inference/tool imports do not load research. This is an installation probe in the
existing maestro scientific environment, not a clean-environment dependency guarantee.
Ten constructed queries, spanning two baseline vectors and five registered doses,
produce exactly equal before/after predictions and model versions. Random fixture
weights are not STATE, measured cells or newly trained biological evidence.

## Measured-realisation development task

The [input audit and latest specification](results/20261003_feedback_boundary_v1/realisation_intake_v3/readiness.json)
identify five supplied files as code/report material. There is no new matched
training table in that supplied directory. Existing LINCS/GDSC evidence does not
acquire same-culture target/function measurements merely by combining its files
with engagement annotations or lysate assays.

The executable design emitter is [realisation_plan.py](realisation_plan.py).
Its candidate scope is one EGFR-mutant NSCLC background, PC9, with pharmacological
and genetic EGFR interventions. This is a proposed scope: local assay availability,
identity, doses, schedules and endpoint/QC settings remain unconfirmed. No culture
was started and no action was executed.

Cheap decision inputs are authenticated background, intervention/dose/schedule,
and already available cell-count/growth markers. RNA is optional for a separately
certified backend; this proposal does not make costly RNA a universal requirement.
Actual realisation is measured through absolute phospho-EGFR against matched
vehicle/loading controls, with total EGFR retained separately. Phospho-ERK is a
proximal pathway proxy, and ATP plus cell-count controls supplies phenotype.
Binding, protein abundance, phosphorylation and phenotype are distinct quantities.
Genetic preparation and drug onset must be recorded; equal nominal time is not
assumed to mean equal effective exposure.

Compare a direct phenotype predictor to a two-stage predictor:

```
realisation_hat = f(cheap covariates, nominal intervention)
phenotype_hat = g(covariates, realisation_hat, modality)
```

Measured realisation supplies training supervision. Fit `g` using inner-batch
out-of-fold predictions from `f`; hold entire outer physical batches out of both
fitting and preprocessing. At decision time a future measured realisation value
cannot enter either predictor. After an authenticated feedback event, an available
measurement may inform the next decision under the same admission rules.
This predicts intervention differences; it does not establish causal mediation or
calibrated mechanism likelihoods.

The latest empty CSV tables record conditions/attempts, measurements/provenance,
and events/costs. They contain headers only. Missing unit prices and outcomes stay
missing. The existing CaseStore remains the evidence authority; these tables and
the emitter do not create another result store.

For two-round research, freeze a menu of intervention/readout/time bundles. Commit
the first selected bundle and predictions, import actual qualified results and
failure costs, then select orthogonal function/rescue evidence, more measurement,
or stopping. No mechanism Bayes factor or information-gain claim is authorized
until hypothesis-conditional observation probabilities are separately supported.
Freeze the four proposed agent/predictor combinations plus fixed-action, simple
prediction, state-permutation and modality/realisation ablations under matched
information and budgets. Report each component increment and the interaction.

Blocking unknowns remain explicit: matched measurements, complete attempt/failure
denominator, assay conditions/QC, prices, meaningful gain/refusal loss, physical
variance and confirmation power. Stop before training while those data contracts
are unmet; stop this decision task if development action gaps lack useful headroom;
modify a model that fails held-out contrast prediction; require unopened matched
confirmation before promoting scientific use.

## Validation and failure accounting

Machine-readable results, command output and source hashes are in
[the new receipts directory](results/20261003_feedback_boundary_v1/).
The corrected flow suite passes **128** tests, and the correction suite passes
**71**. The existing LINCS pack passes **8** integrity/split/schema contracts.
The final aggregate passes **1,949** tests with no failures, errors or skips;
`receipt.json` and the dated log record the exact scope. Budget charges in software
fixtures are declared resource units, not newly authenticated laboratory prices.
A final focused check after the latest intake/design and documentation changes
passes **59** tests.

An intermediate full run passed **1,936** and failed one old assertion requiring a
decision after rejecting a model prediction as measurement. The regression now
asserts waiting, no decision, no mechanism update and zero physical expenditure.
This strengthens the pending-result contract. Another earlier targeted failure
required retaining the diagnostic decision for a completed QC-failed bundle;
that behaviour was restored and revalidated. Two preliminary scoped invocations
named nonexistent test files and collected no tests; corrected invocations use the
actual lifecycle test file. None of these attempts is a biological experiment.

The research-wide collector was exercised separately; collecting a test is not
executing its data-dependent evaluation. Other research suites and historical
full replays are not claimed to pass. Full-size GCTX rebuilding was not repeated;
the builder was tested on a complete small constructed source and the existing
real pack was validated. Changing the constructed test-side vectors leaves fitted
reference centroids exactly unchanged.

Not run: new STATE inference, LLM API research, measured-realisation biological
training, real two-round experiments, four-arm biological comparison, causal
mechanism likelihood calibration or prospective deployment-value evaluation.
Synthetic training contracts did execute small constructed arrays. APIs remain
authorized, but cannot supply the absent physical measurement evidence.

## Reproduction

From the repository root, use a fresh output directory for each receipt:

```powershell
$py = 'D:/anaconda/envs/maestro/python.exe'
& $py -m pytest tests research/astra research/scientific_optimization/test_population_flow.py research/scientific_optimization/test_response_training.py research/case_memory_integration/test_external_evaluation.py -o addopts= -q --junitxml NEW_OUTPUT/final.xml
& $py -m tools.research_validation --collect-only -q
& $py -m research.astra.realisation_plan --inputs research/data --out NEW_OUTPUT/intake
& $py -m tools.case_memory.workflow pack --workspace DATA_WORKSPACE
& $py -m research.case_memory_integration.external_replay --help
```

The pack command rebuilds assets; do not use a frozen historical output workspace.
Research replay/evaluation retains its original output contract and opened-data
status; command availability does not make it independent confirmation. Exact
wheel-build/installation/probe commands are in `package_verification.json`.

The scientific conclusion is unchanged: attribution and ownership are more reliable;
no new evidence establishes STATE state gain, improved interventions, mechanism
identification, dual-core synergy or net biological value.
