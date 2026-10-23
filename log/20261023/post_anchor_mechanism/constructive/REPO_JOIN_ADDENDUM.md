# Official AML repository join qualification

2026-10-23. Additional local read of parent-acquired official repository files only; no HTTP, labels, matrices or fitting. Repository commit: `3d5ef9070a259fb902feccbc5948f10e6a9d44ae`. Evidence files: `root_sources/aml_tree.body`, `aml_readme.body`, `aml_lineage.body`, `aml_gex.body`. These supplement, without modifying, the sealed independent report and source addendum.

## Concrete evidence

The README identifies GSE289459 as DNA sequencing and describes SingleCellLineage, preprocessing, tag clustering, trees, then Seurat integration. A complete nontruncated tree contains scripts and Newick trees but does not instantiate the processed metadata join needed for a prospective functional task.

`single_cell_lineage_analysis.R` lines20–30 reads the lab-local `rs22_rs28_combined_cells_founder_and_casclone_annotation.csv`. Its `GEX_bc` key supplies Seurat barcode rows; columns3 and6 supply founder and cas_clone respectively. This exact named artifact is absent from the acquired complete tree. The code establishes the intended interface, not that the public expression matrix can currently be joined to a verified public functional label table.

The C1498 analysis assumes pre-existing `group` metadata with Control/Persistent/Resistant identities. Its founder/clone tables count sequenced cells then normalize to proportions. Such proportions do not equal absolute viable-cell growth or drug-specific outgrowth; cell sampling, missing founders and compositional changes need an explicit observation model.

The HL60 section assumes an already-existing `strict_founder_hl60s` object. It uses `Pre_exp_pool` at day0, A/B midpoint at day36, Control_midpoint at day43, and A/B/Control endpoint at day89. The source does not instantiate GSM/MULTIseq barcode→sample/flask/timepoint→founder joins. Day36 treatment and day43 control cannot be directly subtracted as a same-time matched causal response. Day89 is a potentially aligned endpoint, conditional on a valid culture and founder join.

`single_cell_GEX_initial_processing.R` starts from hardcoded lab CellRanger/MULTIseq paths, demultiplexes and removes doublets/negatives, and uses an already-existing lane_b. It does not supply the exact MULTIseq tag→group/flask/time mapping needed here. Do not execute these incomplete scripts as an authenticated reconstruction.

## Decision and bounded next contract

**NO_NUMERICAL_GO; metadata-join qualification only.** Missing pieces are now concrete rather than a general assertion that data are unavailable: barcode→founder/clone annotation, baseline/end sample and culture mapping, treatment/control timing, and independently quantified functional counts/curves joined to those entities. Paper-listed workbooks and raw lineage archives may contain enough information, but they have not been inspected in this pass. Do not claim global source unavailability or that reconstruction is impossible.

Before labels/fitting, qualify those artifacts and freeze the prospective feature cutoff. Endpoint-derived trees/modules cannot become baseline predictors. Whole founders and cultures, not same-ancestor cells, define uncertainty and partition units. Start with untreated fitness/count/history-only and strong direct treatment-interaction controls. Two cell systems and one drug cannot establish broad inheritable research improvement. This is a source-conditioned diagnostic opportunity, not a newly nominated update mechanism.
