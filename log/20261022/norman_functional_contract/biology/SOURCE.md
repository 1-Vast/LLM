# Independent source qualification: Norman functional calibration

2026-10-22. qualification_assay. Read root's primary_bioc.source.txt (PMC6746554), pinned prediction/comparison/population source, cell_population.body, RAW_SCHEMA, IDENTITY_JOIN and BASELINE_PROTOCOL_DRAFT. No HTTP, matrix entries, biological assay/cell values, current peer draft or fit. Initial large combined source output was truncated; focused reads recovered the relevant pipeline, exact QC and primary Fig6 text. All acquisition/schema results below were executed by root, not independently rerun here.

## Decision

**GO_FINISH_NUMERIC_QUALIFICATION_AND_BASELINE_CALIBRATION; NOVELTY_NO_GO_FOR_RENAMED_ORIGINAL_METHOD.** There are now actual functional tables and raw RNA resources; the former processed-label blocker does not apply to this distinct Norman contract. However single-RNA side information plus sparse growth feedback to predict remaining interactions is already the original paper's Fig6 approach, not an unexecuted novel mechanism. Do not stop a small ordinary calibration merely because a new operator has not yet been invented; equally do not promote that calibration into the full research contribution.

## Independent function and closest existing method

Primary text states K562 SunTag CRISPRa dual-guide abundance was compared at the start and after ten days of growth. Bulk growth and growth-derived GI are independently assayed relative to scRNA profiles; transcriptomic GI categories remain a different endpoint. Gene-average versus exact Perturb-seq chosen-guide scores are distinct and must not be pooled silently.

Original Fig6 already uses single-perturbation transcriptomic side information and limited measured functional interactions to infer the remaining growth/GI landscape with a recommender/matrix-completion approach. Author prediction source specifies: fit a quadratic double-growth expectation from observed pair labels plus single growth; subtract it; Maxide-complete residuals using RNA side information; add the expectation back. Thus RNA + feedback, side-information matrix completion, quadratic residualization and their ordinary learning curves cannot be named new world-model/RSI contributions. They are mandatory close baselines/carriers for a subsequent genuinely distinct update claim.

Static source also reveals zero sentinels: `y[y != 0]`, predicted/given selected from zero/nonzero, and Maxide indices via flatnonzero(delta). These can confuse real measured zeros with missing values. Correct observation masks are necessary validity engineering, not new mechanism. get_deltas touches full source residuals but the original pipeline subsequently masks them; this fact alone does not prove original training leakage. New implementation should keep protected values entirely out of training memory and transformations and document faithful versus corrected behavior.

## Actual available assets versus final eligibility

Root acquired four fitness/emap CSV objects. The identity-only join gives113×113 functional axes and105 raw single-target names shared with them;5460 is merely the combinatorial maximum of nonself unordered pairs. It is not a measured pair count, post-QC state count, source budget guarantee or functional completeness result. The earlier filtered-ID join's matrix-not-acquired flag is superseded by later RAW_SCHEMA, not secretly a contradiction.

RAW_SCHEMA authenticates a33694×5898240 raw matrix declaration and114870 unique identity barcodes, all contained in its barcode axis, with no duplicates; expression entries and numeric cell fields remain unopened and QC unapplied. Root's completed raw-file acquisition removes a speculative-download requirement. Filtered GEO identities cannot stand in for the author's raw workflow because Cell Ranger filtering may discard low-UMI perturbed cells.

## Exact source-supported QC and single-only legal preprocessing

population.source calls `CellPopulation.from_file(..., filtered=False, raw_umi_threshold=2000)`, then selects `single_cell`. cell_population.body defines raw threshold from **expression-matrix column sums >=2000**, not the guide-calling metadata's field with the same UMI name. It explicitly defines `single_cell = (number_of_cells == 1) & good_coverage & (guide_identity != '*')`. Do not infer this from number_of_cells alone or use Cell Ranger called status as a substitute.

Population source resolves aliases, handles control-guide pairs, normalizes relative to gemgroup controls and aggregates guide targets. Author singles selection explicitly excludes BAK1/BCL2L11 as failed/toxic and chooses particular single+NegCtrl orientations. Prediction/comparison also selects genes with single-state differential-expression signal. These are real scope decisions:105 matching IDs are not automatically the final eligible panel. A faithful-close baseline must document them; an all-eligible alternative is a declared protocol variant, not a silent original reproduction. Toxicity/survivor selection restricts biological inference.

For the proposed single-only capability contract, derive controls, RNA transforms/features and eligibility only from permitted controls/single states, never pair RNA or functional-map clusters. A normalization or gene-selection call inherited from an all-perturbation original notebook is not automatically legal just because the notebook is published. Resolve exact control membership, gemgroup normalization and single orientation/alias mapping before fitting. Pseudobulk is sufficient after these definitions; no need recreate unrelated author visualizations or transcriptomic double models.

## Assessment of prospective draft

Hash-split unordered pair grouping, mirrored-entry grouping, source-only quadratic fit, explicit protected audit and shared budget order are appropriate. Held-out pairs with seen genes are one selected K562 map, not independent contexts or research tasks. Future masking must separately represent observed/missing, train/dev/protected role and any real zero; finite eligibility and symmetry checks must not accidentally open protected labels. Source/dev missingness is reportable without claiming protected completeness.

The draft's conventional set is appropriate: constant, single-growth additive/quadratic, gene identity/low rank, regularized direct symmetric RNA pair regression/simple fusion and corrected-mask original RNA-Maxide residual procedure. All same-information rivals must receive legal single RNA and single growth. No-RNA arms are information ablations. Explicitly record preprocessing/tuning costs and gene dependence of uncertainty. The proposed MSE primary and gene-level GI secondary are acceptable only after confirming their exact label lineage and no protected-dependent recalculation of GI normalization.

Before numerical fit, finish a frozen QC/alias/control implementation, functional observation-mask and orientation/missingness rules, real-zero handling and budget feasibility under actual eligible source labels. Then run limited baseline calibration, not a new architecture or unrestricted program search. Stable residual error may inform a later candidate; it does not itself establish novelty, a simulator, agent necessity, inheritance, joint gain or improved-improver RSI. Original Fig6 capability must remain attributed to the authors.
