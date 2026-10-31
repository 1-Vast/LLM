# Virtual-cell core innovation checkpoint: task-sufficient transfer

Date: 2026-10-31 (Asia/Shanghai). Study: `task_sufficient_transfer_mvp_20261101`.

**Current design precedence:** [NEXT_ROUND_DESIGN.md](NEXT_ROUND_DESIGN.md) supersedes the broader future-action/Agent sketches below; they remain historical proposals, not admitted work.

## Scientific decision

The current work does **not** establish a high-value Virtual Cell core innovation. The GAT component remains a useful, independently verified input representation correction, and the new pilot shows that the full GAT residual retrieval carries a small exploratory advantage on the exposed development pool. The pilot does not show that a compact state is sufficient for a future intervention or that the result improves an independently held-out drug-discovery decision. No change is admitted to `src/` or `tools/`, and no AIVO or Agent implementation is authorized by this checkpoint.

The surviving research question is narrower and more testable:

> Given a baseline and an early perturbation observation that are already measured, can a compact, support-aware state preserve later functional and cell-selection decisions for intervention classes held out by mechanism or chemotype, including different future doses, times, combinations or washout actions?

This is a predictive sufficiency question under a declared measurement contract. It is not a causal, mechanistic or biologically sufficient cell-state claim.

## Evidence reviewed

- GAT protocol, run, deviations and independent 139/139 verification: [`2026-10-31-generic-axis-transfer/REPORT.md`](../2026-10-31-generic-axis-transfer/REPORT.md).
- Current exploratory protocol and freeze: [`PROTOCOL.md`](PROTOCOL.md), [`FREEZE.json`](FREEZE.json).
- Exploratory output: [`RUN/RESULTS.json`](RUN/RESULTS.json), [`RUN/per_query_metrics.csv`](RUN/per_query_metrics.csv).
- Independent numerical check: [`VERIFY_61_REPORT.md`](VERIFY_61_REPORT.md), [`VERIFY_61.json`](VERIFY_61.json).
- Full all-arm independent replay: [`VERIFY_FULL_61/VERIFY_FULL_61_REPORT.md`](VERIFY_FULL_61/VERIFY_FULL_61_REPORT.md), [`VERIFY_FULL_61/VERDICT.json`](VERIFY_FULL_61/VERDICT.json).
- Frozen-arm numbering clarification: [`POSTRUN_CLARIFICATION.md`](POSTRUN_CLARIFICATION.md).
- Independent closest-prior review: [`CORE_INNOVATION_CLOSEST_PRIOR_REVIEW.md`](../2026-10-31-generic-axis-transfer/CORE_INNOVATION_CLOSEST_PRIOR_REVIEW.md).
- Conditional AIVO boundary: [`AIVO_CONDITIONAL_BOUNDARY_20261031.md`](../2026-10-31-generic-axis-transfer/AIVO_CONDITIONAL_BOUNDARY_20261031.md).
- Independent AIVO/Agent challenge and corrected next-round design: [`AIVO_AGENT_CHALLENGE_61.md`](AIVO_AGENT_CHALLENGE_61.md), [`NEXT_ROUND_DESIGN.md`](NEXT_ROUND_DESIGN.md).

The study was deliberately restricted to the exposed `dev_pool.npz` (1,403 compounds, 18 L1000 condition slots, 978 genes and 578 PRISM 19Q4 lines). NCI-60 and PRISM 24Q2 outcomes were not read in this pilot. The information contract has no matched untreated baseline, dose series, single-cell composition, spatial variables, extracellular matrix or longitudinal state-to-function join.

## What the exploratory pilot found

Five grouped folds were fixed from the InChIKey connectivity block (`[272, 274, 280, 294, 283]` queries). The run used 348 exploratory-active compounds. All transformations were specified as reference-fold fits. The primary ranking endpoint was residualized top-10% cell-line hit precision; selection regret is the observed sensitivity gap between the predicted top set and the oracle top set. These are retrospective development-pool observations, not confirmation results.

Mean saved-run summaries on active compounds were:

All values below are exploratory saved-run outputs. The PCA, random-projection and ridge predictions were structurally checked but were not independently refit in the first verifier.

| Arm | Hit precision | Selection regret | Selective r | Raw MAE |
|---|---:|---:|---:|---:|
| Raw cosine, k=5 | 0.20396 | 1.02251 | 0.19547 | 0.87223 |
| Raw cosine, k=20 | 0.21203 | 0.99476 | 0.21732 | 0.84013 |
| Chemistry Tanimoto, k=20 | 0.17312 | 1.15308 | 0.12345 | 0.99127 |
| **GAT residual, k=20** | **0.21856** | **0.96667** | **0.23323** | **0.83588** |
| Full flattened residual, k=20 | 0.21681 | 0.97024 | 0.23132 | 0.83719 |
| PCA residual, K=2 | 0.13005 | 1.25893 | 0.05668 | 1.02265 |
| PCA residual, K=20 | 0.19868 | 1.03652 | 0.19752 | 0.90024 |
| PCA residual, K=100 | 0.21417 | 0.99201 | 0.21974 | 0.86872 |
| Random residual, K=100 | 0.17734 | 1.09659 | 0.14946 | 0.92134 |
| Ordinary ridge on raw signature | 0.19857 | 1.03248 | 0.19088 | 0.85227 |
| GAT target-permutation null | 0.10806 | 1.36362 | 0.00008 | 1.04487 |

The GAT versus raw-k20 differences are small but directionally favorable in this exposed pool: hit precision `+0.00653`, regret `-0.02809`, selective r `+0.01591` and raw MAE `-0.00425`. No inferential gate was pre-registered for this pilot. Chemistry had defined hit precision for 341/348 active queries because some fingerprints were unavailable.

Saved-run outputs suggest that PCA K=2–20 underperforms and K=100 approaches the full residual result; the saved random-projection outputs are lower in this run. Because these arms were not independently refit, this is an exploratory implementation observation, not a confirmed negative result. The `global_residual_diagnostic` exactly reassembles the GAT prediction, so global-plus-residual decomposition is an identity check rather than a new mechanism. The permutation null removes selective signal, which supports that the transfer is not arbitrary, but it does not identify a biological mechanism.

The independent verifier passed the pipeline and re-derived all 1,403 residualized primary metrics from the saved arrays. It independently recomputed representative raw, chemistry, GAT and full-flat predictions and checked the global identity. PCA, random and ridge predictions were not independently refit; their exploratory values therefore remain implementation outputs, not independently verified model results. A first schema comparison incorrectly treated three derived scalar metadata values as NPZ keys; the verifier corrected this and confirmed all seven array shape/dtype pairs.

The later full all-arm replay completed without reading the frozen runner. Fold assignments matched all 1,403 compounds, and `raw_k5`, `raw_k20` and `ridge_raw` reproduced the saved predictions to below `1.2e-14`. It did **not** pass the all-arm equality gate: chemistry had a zero-fingerprint singleton mask discrepancy, while the GAT/PCA/random/full-residual families had substantial prediction mismatches. The replay preserved these files as a traceability diagnostic (`COMPLETED_WITH_MISMATCH`); it is not an independent scientific PASS. A subsequent source inspection found that the replay implemented different transformations and primary metrics: flattened rather than per-option GAT, centered raw rather than GAT-residual compression inputs, reversed sensitivity ranking and a different hit definition, plus different zero-fingerprint handling. The earlier attribution solely to protocol underspecification was premature. These are engineering differences, not biological failures. No corrected all-arm replay has yet been completed; see the [source-level diagnosis](../2026-10-31-crossfield-state-learning/root_notes.md). No result from this replay is used as a biological or novelty claim.

## Why this is not yet the core innovation

GAT removes shared transcriptional directions before analogue retrieval. That operation is closely related to all-but-the-top, PCA or whitening in representation retrieval, and unwanted-variation correction in genomics. Its confirmed value is a task-specific incremental correction, not a new cell-state law. The current query already has an L1000 perturbation signature; only its viability profile is unmeasured. It is therefore not structure-only prediction of an unprofiled drug. A PCA projection of the same measured genes also compresses representation, not experimental measurement cost.

The closest-prior review found the following occupied or high-risk areas:

| Prior | What it makes unavailable as a standalone claim |
|---|---|
| Systema, *Nature Biotechnology* 2025, DOI `10.1038/s41587-025-02777-8` | A correlation gain after removing shared variation is not enough; perturbation-specific and magnitude-sensitive evaluation is required. |
| PrePR-CT, *Nature Machine Intelligence* 2026, DOI `10.1038/s42256-026-01202-2` | Graph/state-conditioned transfer to unseen cell types or compounds is already a demonstrated capability. |
| CRISP, *Nature Computational Science* 2025, DOI `10.1038/s43588-025-00887-6` | Unseen-context and cross-platform perturbation transfer is an existing target. |
| MAP, *Nature Machine Intelligence* 2026, DOI `10.1038/s42256-026-01286-w` | Mechanism knowledge and zero-shot unprofiled-drug transfer are already a strong prior. |
| UniPert-G2CP, *Cell* 2026, DOI `10.1016/j.cell.2026.06.005` | Broad genetic-to-chemical intervention transfer is already occupied. |
| PertReason, arXiv:2607.18777 (2026) | State-gated regulatory reasoning under OOD context/mechanism is a material preprint prior. |
| Predictive-state and action-abstraction work in robotics/RL, including arXiv:2606.25357 | “A state sufficient for future actions” is not a new general theory; the biological estimand and action interface must be explicit. |

The possible difference is therefore not a better embedding, graph, knowledge graph, contrastive loss or Agent. It is an operational object: a compact, measurable state whose future predictions remain equivalent under the allowed interventions and whose uncertainty can cause a principled refusal. This remains a hypothesis, not a novelty finding.

## Recommended core candidate

Use the plain name **action-conditioned decision-sufficient cell state**. Let `H_t` contain the baseline and early perturbation measurements, exposure and context, and let `z_t = f(H_t)` be the compact state. For every allowed future action `a` (dose, time extension, combination, washout or follow-up perturbation), test whether:

`P(Y_{t+Δ} | H_t, a, context) ≈ P(Y_{t+Δ} | z_t, a, context)`.

The candidate earns scientific value only if the compact state also improves a predeclared drug-discovery decision under a fixed assay budget, retains the overall-effect channel, and refuses unsupported transport. The claim must remain predictive. Causal mechanism requires separate intervention evidence.

## Next decisive validation round

### Data gate

Before modeling, audit a public resource that contains the complete join: baseline or early state, intervention identity, dose and time, later viability or function, preparation/replicate identity, and enough chemical or mechanism labels for whole-family holdouts. Existing longitudinal live-cell count files, perturbation-proteomics resources and single-cell perturbation resources are candidates for a data audit only; their presence in `data/external` does not establish a valid join. Do not merge GAT, NCI-60 and PRISM endpoints as if they measured the same quantity.

### Frozen comparison

Use scaffold/chemotype holdout first, whole target or mechanism-family holdout where an ontology is authenticated, and an independent assay/platform or dose/time regime. Random compound splits are diagnostics only. Fit all state maps, imputation, calibration and refusal thresholds on the reference side. Compare raw transfer, GAT, full ordinary ridge/PLS, global-plus-residual, a declared state-dimension/measurement curve, chemistry-only and a shuffled-target control.

### Action-conditioned challenge

Construct either matched early histories that receive the **same** future action but have different later outcomes, or a joint outcome vector over a fixed action menu for the same history or matched histories. Divergence after different actions is not by itself evidence of state insufficiency because the action is already a conditioning input. A state that merges histories which diverge under the same action is insufficient for that decision. A single held-out viability endpoint cannot establish this property.

### Gate metrics

Primary metrics are fixed-budget top-k cell-line or compound selection regret and hit enrichment. Secondary metrics are magnitude-sensitive viability error, calibrated rank/profile error, selective correlation, support-coverage risk and refusal utility. Report both an overall-effect endpoint (for example, viability or kill magnitude calibration) and the selective cell-line endpoint; improving one while damaging the other is not promotion. Freeze a minimum coverage floor and compare refusal with a same-coverage abstaining baseline across the full utility-versus-coverage curve. Record mechanism-label provenance. Define a minimum important decision difference before opening the external outcomes. Require a confidence interval excluding no benefit in at least two independent domains, no material deterioration of overall-effect calibration, stable state size across outer folds and a code-independent replay.

### Stop conditions

Park the candidate if only correlation improves, if the gain disappears under mechanism or chemotype holdout, if ordinary ridge/GAT reaches the same decision value, if the compact state needs nearly the full input, if action-conditioned equivalence fails, if refusal is uncalibrated, or if no auditable external domain remains. Do not rescue a failed state with a larger encoder or an Agent.

## Conditional path to a Virtual Organoid

The AIVO review (Bai and Su, DOI `10.1016/j.bioactmat.2025.12.030`) is an architecture reference rather than drug-discovery validation. Its useful boundary is that an organoid digital twin needs persistent state, longitudinal measurement updates, spatial or neighborhood structure, cell-cell and cell-matrix interactions, exposure/transport when task-relevant, virtual measurement instruments and uncertainty. The review should not be treated as evidence that an Agent supplies missing biology.

Only after the cell-state candidate passes the core gate should a small AIVO be built around one organ-specific task. Start with two or three cell types, one fixed co-culture or spatial condition, a measured baseline, drug/dose/time, a functional organoid readout and donor/batch holdout. Add cell-type omission/add-back, ligand blockade, ECM or controlled-flow interventions when claiming an interaction. Compare the interaction model with an additive mixture of independent virtual cells. Add transport and longitudinal assimilation only when they change the held-out decision.

## Conditional Agent design

A candidate Agent role to test after the core gate is **model-validity and discriminating-measurement control**. Given competing explanations such as intrinsic resistance, poor local exposure and intercellular protection, the Agent may choose a predefined dose, time, imaging, depletion/add-back or molecular readout that maximizes expected decision value minus assay cost. It must be compared with fixed panels, mutual-information design, ordinary Bayesian optimization/active learning and a human or deterministic planner under equal wells and days.

The Agent may maintain versions, quality-control measurements, choose among fixed actions, propagate uncertainty and abstain. It may not invent mechanisms, rewrite the validated transition model, inspect held-out outcomes, impute unobserved biology as fact or bypass refusal. It passes only if it lowers decision regret or assay count on a prospective or temporally held-out organoid task and reproduces across donors or batches.

## Operational limits and preserved failures

- The MVP is retrospective and non-confirmatory; it is not an external test, a causal test or a biological Virtual Cell validation.
- The independent numerical verifier did not refit the PCA, random-projection or ridge arms; their reported curves remain exploratory.
- The later full replay matched only raw kNN and ridge; chemistry and the GAT/PCA/random/full-residual families did not meet all-arm equality, so the saved exploratory arm table is not a code-independent all-arm result.
- NCI-60 has development-pool connectivity overlap and standardized GI50 z-scores; PRISM 24Q2 is a separate assay and was not opened here.
- Current data do not identify untreated baseline, dose response, spatial interaction, ECM, exposure transport or single-cell composition.
- The earlier GAT review recorded a binary-output accident while inspecting a protected NPZ; no values were read or used, and no file was changed. This remains an audit incident, not scientific evidence.
- No Agent module, AIVO simulator, external model bridge or core-code promotion was performed.

Current status is therefore **Virtual Cell core: NOT_ADMITTED; AIVO/Agent: DEFERRED**. The next useful action is a data-contract audit for an action-conditioned early-state/later-function resource, followed by a new frozen external validation only if that contract passes.
