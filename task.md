# Scientific operating and evaluation contract

This document defines MAESTRO's supported boundaries and success criteria. The
agent and virtual-cell world model are separate cores; neither component can
upgrade the evidence origin of the other. Current results are in
[the research report](research/REPORT.md), with exact studies and commands in
[the evidence register](research/EVIDENCE.md).

## Objective and responsibilities

Given a biological question, legal candidate menu, available evidence, budget
and deadline, choose the next admissible intervention or observation, explain
what it can resolve and state what would falsify the current interpretation.

| Owner | Responsibility |
|---|---|
| Agent / decision core | Objectives, candidate hypotheses, evidence acquisition, admissible selection, workflow repair and stopping |
| Virtual cell | Condition-bound response prediction, applicability, refusal, model/source identity and uncertainty |
| CaseStore | Authoritative plans, attempts, execution statuses, results, reservations and actual spending |
| Tools and knowledge | Acquisition, normalization, source tracing and structured lookup; references remain references |
| Research | Experimental methods, protocols and scientifically scoped evaluation; not a competing production controller |

The world-model foundation is official pretrained STATE `final.ckpt`. Keep exact
checkpoint and feature-axis identity. Different backends or weights do not count
as STATE validation. Predictions do not certify target engagement, protein
activity, causality, intervention equivalence or mechanistic probability.

Genetic-pharmacological discordance is a mechanistic task family. The present
cheap public-data work instead evaluates a bounded native-RNA selection task;
RNA proxy gains cannot validate the broader mechanism claim.

## Input and prediction contract

- Normalize compound/component identity, intervention mode, dose/unit, time,
  cell background and required readouts; preserve original identifiers.
- Bind prediction to its complete request, action, case/contrast/plan and model
  version. Cache reuse requires matching conditions and source/feature identity.
- A required input that is missing triggers refusal or an explicitly supported
  backend switch. Public basal reference data is not the target culture's measured
  decision-time state.
- Distinguish an outcome conditional on a valid experiment from the full outcome
  of attempting it. Failure, nondetection, QC failure and uninterpretable outcomes
  retain their probabilities. Never redistribute missing mass to success.
- Record when each input became available. Targets and derived labels cannot
  enter a decision before the corresponding authorized purchase/reveal.
- Research entry points explicitly record strategy/parameters, whether predictions
  affect selection, rule/model versions, menu, budget and stopping conditions.
  Predictor-dependent selection cannot silently become a different fallback policy.

## Evidence and execution contract

Model predictions, literature references, derived analyses and real measurements
retain distinct origins through context, memory, tools and reports. A source
record repeated across files, articles or databases does not become independent
support. Scope and provenance belong to every projected result.

A scientific update requires qualified observation, matching conditions,
interpretable readout, adequate source support and the named interpretation
prerequisites. RNA change is not protein activity; binding is not sufficient
functional inhibition. Unconfirmed prerequisites preserve the observation but
cannot upgrade the conclusion. If all current hypotheses conflict with accepted
evidence, mark the hypothesis set invalid and propose a new analysis.

Plans have an explicit version; actions, attempts, predictions and results have
stable identities. Ambiguous repeated actions require the original plan identity.
Idempotent result retries do not charge twice and may repair missing derived
projections. One action's QC failure does not discard other already-produced
results in its batch. Separate planned, started, completed, QC-failed and cancelled
states; failed attempts retain actual cost.

Reopening a case can recover execution facts and receive original results. It
cannot silently resume scientific selection from an empty evidence state when
historical exclusions/reliability have not been restored. Block that continuation
or explicitly establish a new analysis; do not reinterpret old judgments with a
new rule version without declaring the change.

## Acceptance gates

| Gate | Evidence required |
|---|---|
| Engineering correctness | Identity/refusal/condition/budget tests, idempotency, concurrency, restart and audit lineage |
| Predictive validity | Declared endpoint and supported conditions, independent units, error/calibration/refusal and distribution-shift evaluation |
| Decision value | Same legal inputs, menu, cost and deadline; independently observed final value against strong simple/deterministic policies |
| Agent-specific contribution | Same tools/information, actual semantic choices, provider cost/latency and invalid-action accounting |
| Mechanistic conclusion | Qualified intervention-realisation and proximal/phenotypic evidence; transcript forecasts alone are insufficient |

Software tests do not establish biological validity. Development selection,
post-hoc rescue, different seeds and swapped repeat roles do not create untouched
confirmation. Group complete cells, directions/repeats and source units according
to the task; report drug-pair dependence and concentrated gains.

The latest comparison-based acquisition study preserves all 146 candidates,
commits all five final B selections before reveal and prices A/B profiles equally.
Its five target contexts were already exposed. Future reference rollouts need
source qualification: 43 of the 45 backgrounds cover the full menu; missing-source
outcomes are not zeros or experimentally observed failures.

## Current bounded research

Test whether frozen STATE forecasts and purchased feedback improve candidate-pair
or selected-set loss prediction and reduce the information cost of a decision.
Learn a small strongly shrunk correction on nested reference episodes; retain
empirical-only, STATE KG, fixed and condition-permuted controls. Price and utility
must stay separate without an externally justified conversion. A small Gaussian
crossing score is not a calibrated multistep value or stopping guarantee.

Keep new fitting and policies in `research`. Promote reusable contracts only
after behavioral verification; promote scientific policies only within a task
scope supported by decision-value evidence. Dataset acquisition is metadata-first,
selective and provenance preserving. Existing exposed packets support inexpensive
replay; confirmation requires qualified independent public units.
