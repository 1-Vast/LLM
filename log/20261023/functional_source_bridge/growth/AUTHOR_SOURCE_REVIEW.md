# Independent author-source review: 16-line DepMap Perturb-seq pilot

2026-10-23. Position: CONDITIONAL_SOURCE_OPPORTUNITY, NOT_METHOD_GO. Reviewed author source at commit ccb9ee5c37fb5a117cd76d8e9a5a5217ce12338d, without importing/executing it, loading datasets, network calls or model fitting. Before writing this review, I read only root/data_utils.body, root/author_tree.body and source files inside root/author_source.zip.body, not root's later conclusions. Native model identity/token cost are not attested.

## Actual endpoint and join

data_utils.py L50–59 calls the functional input `CRISPRGeneEffect`, downloaded from DepMap public-25q2-c5ef.114. generate.py L81–108 directly reindexes that matrix by cell-line `arxspan_id` and knockout gene symbol, melts it into `gene_effect`, and thresholds it into `dependency_strength_class` and `is_dependent`. figure1.py explicitly labels this Gene dependency (Chronos). This is an independently assayed historical DepMap functional endpoint, not a newly measured viability assay in the same Perturb-seq experiment. `lfc_matrix` belongs to differential-expression matrices with two-level headers; its name is not evidence of fitness LFC.

These source-level paths establish intended pairing keys, not actual downloaded identifier overlap, completeness, duplicate handling, timing or endpoint independence at every sample. No data payload is authenticated by this review. The README names a 16-cell-line pilot. This is different from the original 2022 Replogle dual-guide growth contract; that scoped acquisition STOP does not forbid this source or all DepMap labels.

## Selection and label-derived artifacts

The metadata carries target_class and the plotted classes include Common Essential, High Variance, Selective and Olfactory Control. This is strong evidence that dependency-related target categories are part of design/annotation; the checked code does not implement library selection or identify the exact historical release used to choose targets/cell lines. We cannot assert from these scripts that every targeted gene was selected using the exact held-out public-25q2 value. Target-class information is nevertheless privileged dependency metadata for predicting Chronos; exclude it from the primary label-blind feature set, and report the task as conditioned on the selected panel. It may be an explicitly declared equally available prior in a separate comparison, with its historical provenance established.

For a new held-out Chronos prediction protocol, forbid the following as ordinary state features:

- `gene_effect`, `dependency_strength_class`, `is_dependent` from crispr_table.
- generate_cell_depletion_table's `y_pred`: fitted OLS/LOWESS explicitly uses gene_effect as its x variable (L1372–1403). Its raw `depletion` is recovered pass-QC cell count relative to olfactory controls (L1341–1352), not independent longitudinal growth.
- `residual_depletion`, `expected_cells`, `observed_vs_expected_cell_ratio` and dependent-only cell-cycle summaries in mistimed/timepoint tables (L1914–1978): inherited label conditioning/fitted values.
- Published dependency top-DEG tables and dependency hallmark mean-z features: they select/aggregate lines using is_dependent or Chronos < -1 (L1710–1754, L1777–1838). Their full-panel response-gene rankings must not select prediction features.
- Target/arm dependency averages in arm-loss covariate tables. These need explicit allowlisting before any use; generate.py's arm summary uses CRISPRGeneEffect. Chronos predictability results similarly require treatment as a label-trained external prior, not expression features.

The entire `cell_quality_covariates` object is not automatically label-contaminated: generate.py L1413–1494 uses UMI counts, cell recovery, and self-downregulation from expression z/FDR. Its full-panel line-level aggregation is still a retrospective/transductive exposure if future target or line state measurements are unavailable at decision time. Such features are legitimate only under an explicit measured-state information budget and fair counts/QC-only competitors. Raw pseudobulk, lfc and zscore require their own assay/correction provenance and train-only learned transformations; direct CRISPRGeneEffect input is not evident in the inspected cell-quality function. The inspected SCEPTRE arm-loss thresholds use high-quality control-cell expression quantiles; this alone does not demonstrate that all upstream preprocessing is label-free.

These restrictions concern our prospective held-out evaluation, not an allegation that the authors' descriptive biological correlation plots are leaky prediction experiments. Their source explicitly joins gene_effect for association and visualization, which is appropriate for that purpose.

## Support, objections and unresolved facts

Support: an actual named historical functional assay can support a narrowly described retrospective selected-target cross-line study of whether *paid measured perturbation state* adds functional information. New same-assay wet experiments are not required for that limited study. DepMap is not intrinsically a forbidden proxy here; it is the declared endpoint. Grouping cell lines and target genes, allowing only explicitly costed support observations, can provide a meaningful new task if payload access succeeds.

Objections: interpreting pre-existing expression–Chronos correlations as a new world-model contribution would be weak. Selected targets/lines, recovery/survivor bias, distinct assays/times and target-class metadata can explain apparent performance. Same-(line,gene) Chronos values must never be both query labels and features, and label-conditioned published summaries would invalidate a label-blind claim. Static 16-line data alone establishes neither later-task inheritance nor adaptive chronology nor RSI.

Unresolved: legal public download and actual schema; label/state overlap; release chronology versus target selection; how raw/lfc/zscore files were corrected; exact perturbation times and screening repeats; whether the proposed future decision has access to measured query RNA; available old-release growth priors. A source-level name is not an authenticated full dataset.

Minimum informed controls before numerical promotion: target mean and line/target effects; historically legal prior Chronos/essentiality; basal RNA and lineage; recovered-cell/UMI/QC-only model; simple response magnitude; regularized perturbation-RNA direct models; simple same-information fusion; equal-compute nonlinear direct comparator; ordinary pooled refit/CL and fixed AL if feedback adaptation is tested. A public same-pair historical score may make a purported unknown-function discovery task trivial, so define the information restriction honestly. Useful-gain and STOP margins must be frozen before query values. If strong informed direct methods explain the RNA increment, preserve it as conventional capability and do not add agent/RSI modules to rename it.

## Local audit

One initial source keyword extraction printed 11,788 tokens and was truncated. It contained code only, not dataset values; then narrower source ranges were inspected. AUTHOR_SOURCE_EXCERPTS.json records reproducible source ranges and hashes using research/functional_source_bridge_20261023/growth/review_author_source.py. No notebook outputs were read. This review does not modify the prior growth DECISION.md or EVIDENCE.json.
