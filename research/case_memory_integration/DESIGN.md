# Design: evidence-grounded case memory, production integration

> **File summary**
> - **Path**: `research/case_memory_integration/DESIGN.md`
> - **Purpose**: the design record of the case-memory production integration: the episode schema,
>   the directional features, the adaptive retrieval, the hypothesis graph, the conditional
>   virtual-cell forecast, the decision-value action selection and the gated production call path.
> - **Depends on**: `PROTOCOL.md` (frozen evaluation), `src/maestro/case_memory.py` and siblings.

## 1. Schema (scm-2)

`src/maestro/case_memory.py` defines the production scientific episode: immutable, append-only,
digest-addressed, versioned (`supersedes` chains), with the six-state measurement model
(`ScientificMeasurementStatus`), seven case kinds (canonical, contrastive, failure, negative,
adaptation, bridge, real-user-episode) and seven evidence classes (measured fact, qualified
experimental evidence, model prediction, historical analogy, mechanistic inference, curated
annotation, speculation). A failure or negative case is stored, never discarded. A forecast is a
model prediction by construction and cannot carry measurement status; qualified evidence requires
a qualified measurement. Provenance declares `data_origin` (real / synthetic / mixed) and source
hashes. `ScientificMeasurementStatus` is deliberately named apart from
`maestro.models.MeasurementStatus` (measured/estimated/unknown): the two contracts differ and
must never be conflated.

Compound-level mechanism-class cases (the development benchmark and the LINCS 2020 reference
episodes built by `tools/case_memory/build_cases.py`) are retained as **proxy** cases; their
mechanism labels are `curated_annotation`, stated in `provenance.label_kind`, never biological
ground truth. Real user episodes use the same schema with `case_kind = real_user_episode` and the
full episode content (user data references, quality diagnosis, initial hypotheses, retrieved
cases, adaptation map, virtual-cell forecasts, actions, real outcomes, qualified evidence,
hypothesis updates, next actions, branching interpretation plan).

## 2. Directional features

`src/maestro/directional.py`: signed feature deltas, ranked up/down features, signed pathway
projection (gene-set mean scaled by the square root of member count), population shift, replicate
statistics, typed context features, and a realisation record that keeps nominal dose apart from
realised dose (unknown = status, never the nominal relabelled, never zero). The four registered
feature arms (scalar, signed direction, pathway direction, combined) select the feature vector on
identical data; cosine is the frozen similarity. Directional features enter retrieval (stage 3),
forecast weighting and action ranking - verified by the ablation tests and the external replay.

## 3. Adaptive retrieval

`src/maestro/adaptive_retrieval.py`: four stages. Stage 1 hard compatibility (biological system,
assay, measurement type, control design, intervention type, quality, cell line, time and dose
scale) with named exclusion reasons. Stage 2 mechanism: a precedent supports the hypothesis its
reading licensed. Stage 3 directional state similarity uses only a single compatible condition
whose observations are marked `pre_action`. Outcome-only signatures cannot become query features.
A state-free problem (or the scalar arm) may retrieve outcome-only references for frequency
estimation, with no claimed directional match. Stage 4 the nine-term adaptation-aware score with per-case component reports,
adaptation operations and cost basis (transfer history or declared prior). A retrieved set with
fewer than two Kish-effective precedents is reported as not usable. Production retrieval requires
the feature flag; evaluation passes `research_mode=True` explicitly.

## 4. Hypothesis and evidence graph

`src/maestro/hypothesis_graph.py`: typed nodes (intervention, target, engagement, proximal
function, pathway, cell state, phenotype, observable, assay, context, time, dose), typed edges
(relation, direction, context, time, assay, evidence class, source, confidence, uncertainty,
contradictory evidence) and hyperedges for higher-order claims that are never flattened into
pairwise links. Only `qualified_experimental_evidence` is promotable to an evidence state; the
graph assigns no probabilities and grants no evidence.

## 5. Conditional virtual-cell forecast

`src/virtual_cell/interface.py` gains four optional fields on `PredictionRequest` (hypotheses,
history, observation_context, forecast_mode); every pre-extension caller, payload and cache key
is unchanged (regression-pinned). Validation is conditional on the mode: `state` allows empty
hypotheses; `hypothesis_conditional` requires at least two; `history_aware` requires
structurally valid history; invalid combinations return named errors.
`src/virtual_cell/conditional_forecast.py` defines `ConditionalStatePrediction` (per-hypothesis
branches with readouts, directional effects, intervals, support, applicability, calibration
status, provenance and abstain reason) and the conditional cache identity, which includes
hypotheses, history, observation context and mode - the inputs the plain `PredictionCache`
deliberately strips. Abstentions contain no prediction and are never cached.

## 6. Case-memory outcome forecaster and action selection

`src/maestro/hypothesis_forecast.py` implements the existing
`maestro.acquisition.OutcomeForecaster` protocol over an `EpisodeStore`, so the orchestrator's
discrimination selection consumes memory forecasts with no change to evidence admission.
`UserStateContext` connects the compiled user state (directional state, pathway direction,
cell-state summaries, intervention identity, structure, cell context, time, dose, assay,
hypothesis graph, evidence history) to retrieval and to the cache identity; the same action under
two user states forecasts differently when the arm carries state (tested). Forecasts speak in the
action's declared outcome vocabulary when it has one. Retrieved realised outcomes are preferred
when a case contains explicitly conditioned `real_measurements`. Legacy cases without labelled
outcomes return `insufficient_outcome_support`; no probability is fabricated. Version 3 uses one
Dirichlet smoothing step over weighted frequencies with Kish effective support. A single
pseudocount may be fitted on separate development compounds; there is no fixed temperature.
The planner preserves the resulting mean and uses its concentration only for uncertainty.
The profile binds to assay, readout, cell, laboratory, time, dose, outcome mode, feature arm and
source snapshot. A development fit remains **uncalibrated** for external use; receipts distinguish
`development_only` from `not_fitted` and report provenance and the full distribution.
`valid_readout` predicts four conditional outcomes. Complete `attempted_experiment` forecasts
include QC failure and require records explicitly declaring `sampling_frame=all_attempts`.
Conditional forecasts cannot rank complete experiments without an experiment-validity model.
`src/maestro/case_update.py` ranks actions by expected terminal decision value (reusing
`maestro.acquisition`) with named terms, builds branching interpretation plans (decisive /
ambiguous / invalid readings), and ingests real results append-only, keeping qualified,
reliable-but-inconclusive, negative, unreliable and not-measured apart.

## 7. The gated production call path

`src/maestro/case_memory_pipeline.py` runs user data -> ProblemCompiler -> hypothesis graph ->
AdaptiveRetriever -> CaseMemoryOutcomeForecaster -> decision-value ranking -> branching plan.
Gates: feature flag on; forecast mode supported; minimum independent support (6); forecast not
abstaining; forecast marked `model_prediction`; evidence state byte-identical before and after
the forecast. `src/agent/case_memory_wiring.py` returns the forecaster only when
`MAESTRO_CASE_MEMORY_ENABLED` is set, so the default orchestrator is byte-for-byte the
pre-integration behaviour. `tools/case_memory/tool.py` exposes the same path with typed refusals
and an explicitly separate research mode (honoured only for evaluation payloads, stamped
`research_evaluation`).

## 8. External evaluation

Per the frozen `PROTOCOL.md`: LINCS 2020 Level 5 (untouched source), study-level split by
InChIKey connectivity block against GSE92742 + GSE70138, the four-code validator, the eight
frozen arms, forecast-level and decision-level metrics, unit-cluster bootstrap of the primary
endpoint. The frozen replay predates the support-aware production estimator, so its metrics remain
the registered baseline and must not be reported as post-fix calibration. The support-aware
estimator is evaluated separately before activation; the registered gates still remain required,
and the exploratory stratum cannot meet them.

## 9. Scientific correction

See `SCIENTIFIC_REPAIR_V3.md` for the current estimator, preprocessing contract, regression checks
and development calibration comparison. `SCIENTIFIC_FIX_AND_DATA_PLAN.md` and
`SHRINKAGE_DIAGNOSIS.md` preserve the earlier version-2 measurements. The current proxy case file
is `outputs/case_memory_integration/episodes/proxy_reference_cases_v3.jsonl.gz`; older archives and
the frozen external replay remain unchanged. The new development result is encouraging but
does not establish external generalisation, state information gain or action-selection value.
