# MAESTRO Research Report

## Scope and claim boundary

MAESTRO connects an evidence-gathering agent, a scientific decision layer and a virtual-cell predictor. This release preserves the three active STATE/decision studies and their tracked packet inputs. Generated results are local ignored outputs, not part of a clean checkout. `python -m tools.research_validation --verify` checks frozen inputs and outputs before invoking a study verifier; it reports `BLOCKED/ASSET_MISSING` when any are absent or mismatched.

The 2026-10-10 phenotype-anchored study evaluated Tahoe relative-survival selectivity and phase
shift on five checkpoint-held-out lines, using phenotypes measured in the same spheroids as RNA.
For survival selectivity, basal-similarity transfer beat STATE (delta r -0.23); a perfect RNA
oracle added only 0.003 r over the prior on reference lines, below the registered 0.05 minimum
useful benefit. The gate refused STATE for this endpoint, and held-out oracle results supported
that refusal. STATE's distinct held-out signal was predicted-cell G1 composition (+0.25 r on E2).
This scoped result does not establish apoptosis, mechanism or general decision value. See the
[canonical evidence](EVIDENCE.md#phenotype-anchored-dual-core--2026-10-10) and
[study packet](astra/phenotype_anchor_20261010/README.md).

A forecast may influence endpoint selection only after a same-unit readout-to-endpoint bridge
(same culture unit, dose and time) and a reference ceiling pass: substitute observed responses
for forecasts, score leave-one-context-out, and beat the best cheap prior by the declared minimum
useful benefit. Passing admits evaluation; it does not certify the forecast. Unsupported
cross-assay, cross-dose or cross-time bridges and undercounted contexts are refused.

The current endpoint is a signed 39-gene RNA response. It does not establish functional phenotype, protein activity, causal mechanism, clinical efficacy or the value of an experiment. Five target cell backgrounds in the current STATE studies were previously exposed, and reference contexts overlap STATE pretraining.

## Established results

- Engineering closure is verified: condition-bound requests, bounded execution, persistence, feedback and restart contracts operate across the agent, decision and virtual-cell layers.
- The original held-out-context STATE study has a recorded result of about 41% lower depth-corrected RNA error than its empirical baseline on three checkpoint-held-out contexts. This historical result is not rerun by the default test suite.
- The STATE readout repair has a recorded development result: RNA MSE falls 2.17% on reference folds and 7.84% on five previously exposed targets. Clean-checkout replay is blocked by missing Tahoe feature-name metadata.
- The joint-feedback repair has a recorded development result and matched-information posterior prediction improvement. Its frozen source hashes are checked by the preflight; full numerical verification still depends on generated outputs.
- The recorded MAP audit strictly loaded the released checkpoint hierarchy and executed a native forward. A fresh released-weight replay is blocked by external checkpoint, source, compatibility and Tahoe metadata assets. Output gene order and training-time semantics remain unauthenticated.

## Not established / blocked

Independent decision benefit is not established. The STATE readout repair does not change final equal-budget selections; joint-feedback acquisition loses utility on the five exposed target contexts; the recorded strict decision-value LOO finds joint KG only 0.0000544 above no-screen while using eight extra measurements. Clean-checkout reruns need ignored generated outputs. The registered risk-calibration study certifies no conditional-risk threshold and achieves only 2.6% to 3.4% marginal evaluation coverage; its prepared pack is not tracked.

No LLM advantage, functional phenotype gain or mechanism causality is established. Functional bridges, independent qualified evaluation units, a calibrated model-risk contract, utility-unit prices, failure/latency costs and the MAP decoder output map remain unavailable or unqualified. Some local generated outputs exist in this working copy, but they are not a reproducible clean-checkout input. Missing inputs must block with `ASSET_MISSING`; they are not replaced with zero-valued outcomes.

## Next decisive experiment

The [MAP module experiments](EVIDENCE.md#map-module-replacement-and-hard-task-tests--2026-10-09)
now include genuine released protein and relation encoders, matched-information
STATE feedback, scarce-history repeats and bounded-source agent API tests.
Original name-anchor relation composition retains substantial known-graph
content, but the primary molecule/protein direction does not beat structural
votes or popularity. Scarce-history knowledge feedback mainly prevents noisy
updates; it does not reliably beat structure, shuffled knowledge or no-screen.
Hard source-selection trials expose prototype schema and routing failures;
source-typed context alone does not fix them. Neither world-model nor agent
replacement meets its declared evidence requirements. Native MAP RNA output
order and training-time semantics remain unauthenticated.

Use qualified, previously unused biological units and a frozen complete-menu protocol to compare no-screen, strong deterministic acquisition and STATE-informed acquisition under identical information, measurement budgets and authenticated functional outcomes. Pre-register model-risk, cost, latency and failure handling. In parallel, authenticate the MAP training-time forward and output gene order before any native-response claim. Promotion requires independent prediction and decision results; another model expansion is not justified by the current evidence.
