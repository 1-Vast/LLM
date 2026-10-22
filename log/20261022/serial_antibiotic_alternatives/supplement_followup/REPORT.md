# Tripartite supplement: real public per-strain functional panels, not yet a full replay

2026-10-22. **The exact public supplement was obtained and all five complete
pages were rendered and visually reviewed with the PDF skill.** This materially
improves the source qualification: some individual-strain functional values are
publicly visible in figure tables. It is no longer accurate to describe this
asset as having only a genomic accession with no public individual function data.
There is still no authenticated complete molecular-state/action/function replay.

## Acquisition and exposure

One fixed official Europe PMC supplementary-files request returned HTTP200 ZIP,
1,448,783 bytes, SHA256 `60ea6240ce202307de22d8e498546d99c2882a657aed00552745c6116bbdac01`.
Its directory contains the exact `msaf115_supplementary_data.pdf` (888,413 bytes,
SHA256 `4dfc44aa78d1f176871c49abde5694fe3b46c97c68dfe6cae8c30ffcb8f80b4b`)
and main-paper figure JPG/GIF members. Only the PDF was extracted; the other
members remain unread inside the retained raw archive. No retry/redirect or
author contact occurred. This independent successful route does not erase the
metadata auditor's old-host404/new-host403 PMC OA API failures.

Pypdf extracted little text from page 1, so an initial heading-only inventory
could not establish its contents. After `VISUAL_SCOPE.md` registration, Poppler
rendered all five pages at 110dpi. Root inspected each complete page. **Published
MIC, extinction and AUC values visible in these pages are now designer-exposed
literature, not sealed evaluation outcomes.** They were not digitised, exported
as numerical arrays, fitted or used to choose a winning model. No claim of blind
confirmation on reused figure values is permissible.

## Page evidence

| PDF page / source label | Actual visible evidence | Remaining limitation |
|---|---|---|
| 1, Figure S1 A-E | Stage-wise alive/extinct counts, first/second attempt legend, MIC summary panels. Some continued GEN challenge is selected among previously resensitised strains. | Summary counts do not identify each failed/restarted culture or cost; selected continuation is not an unconditional policy test. |
| 2, Figure S1 F/G and full caption | Two 16-row strain-index heat tables for GEN→PIP→NIT and NIT→PIP→GEN; each has GEN, PIP and NIT MIC panels at three stages, plus WT. Explicit per-cell MIC numbers, crossed cells, and green/red circles on selected row indices. Caption says green/red mark sequenced GEN-resensitised/resistant strains. | Row indices are within a loop panel, not global sample accessions. The caption does not give a BioSample→row key or per-row first/second attempt identity. Crossed-cell meaning must be reconciled with actual extinction/missingness, not silently zero-filled. |
| 3, Figure S2 | AUC distributions for three loop orders; paired before/after plots stratified by endpoint resensitised/resistant status. | No global strain ID labels on the plotted points; AUC cannot be automatically joined to MIC rows or genomic samples. Raw absorbance/time-series table absent from these pages. |
| 4, Figure S3 | Uptake-assay summary and caption: supernatant inhibition-zone area after incubation, with the interpretation that lower uptake leaves more GEN in supernatant and a larger zone. Caption reports n=3; main methods mention six independent measurements per strain. | Preserve the n-description difference; do not invent whether n=3 is strains, group summaries or a protocol discrepancy. Uptake is a selected-source mechanism measurement, not every decision-prefix's free state. |
| 5, Figure S4 | Four clinical strain groups A-D, eight replicate row positions, PIT and GEN MIC panels and pre-SAGE adaptation row. Caption states NIT was omitted because these strains were already NIT-resistant; extinction counts cover (NIT)-PIT-GEN. | Do not call these measured NIT→PIP→GEN loops: PIT includes tazobactam and differs from PIP; initial NIT resistance is not a newly measured NIT evolution action. Only the displayed stage/action coverage is authenticated. |

There is no supplementary machine-readable CSV/XLSX or additional numbered table
in this exact downloaded archive. This statement is scoped to its full directory
and the five reviewed PDF pages, not every paper-associated source on the web.
The MIC heat tables are real public figure tables despite lacking a CSV. Visual
legibility supports later carefully checked digitisation if a useful task is
registered; a file format alone is not a reason to reject science.

## What is now usable, and what is not established

A bounded **designer-exposed phenotypic transition/MIC prediction diagnostic**
could in principle use row-linked MIC profiles across these stages, with culture
ancestry grouping and explicit extinction/missingness. It would have a narrow
application in bacterial resistance evolution and would need same-information
direct phenotype/history predictors, ordinary transition models and refitting.
It cannot be called a molecular-world-model contribution merely because MIC is
a multidimensional cell/population state.

This supplement alone does not authenticate matched early genomic state for all
lineages, genotyping before the outcome used for selection, lineage-specific
genotype/function joins, all actual alternative future actions from each state,
or enough genuinely independent transfer/meta-task backgrounds. A few fixed
orders are not a fully crossed action menu. Absence of within-culture adaptive
branching does not prohibit cross-experiment research-agent replay, but the
permitted experimental action and all attempted response units would still need
to be defined and complete for the chosen claim.

The independent metadata follow-up has now authenticated **BioProject1254677→21
unique BioSample Entrez IDs** (the same set repeated in three linkname groups).
This is not 21 donors, founders, strains, contexts or future RSI tasks. The
earlier zero from a BioSample search with an invalid field is explicitly
superseded as a counting method. BioSample identity-only attributes are being
qualified separately; source reports from earlier stages remain unchanged.

## Decision and stopping conditions

**PUBLIC_PER_STRAIN_FUNCTION_CONFIRMED / GENOMIC_PREFIX_JOIN_AND_FULL_REPLAY_NOT_ESTABLISHED.**
Do not download FASTQ or train anything until it is known whether the available
genomic samples are pre-decision or selected endpoints and whether they map to
the visible functional rows. No automatic extension of the stopped history-state
refinement candidate follows from finding real biological history effects.

If the 21 samples are only selected endpoints or cannot map to real prefixes,
stop the claim of a genome-conditioned early-state serial-decision benchmark on
this asset; preserve the phenotypic/source value. If relevant independent tasks
or measured action outcomes are absent, stop only that Agent/inheritance/RSI
claim. No generic theory or simulated missing result may serve as an evaluator.

All response-model, agent-selection, inheritance, joint and common-start RSI
improvement-strategy benefits remain NOT_TESTED. The stopped novelty candidate
has a separate decision at `../../antibiotic_state_refinement_review/DECISION.md`.

## Reproduction

The source/manifest receipt, PDF/text inventory, visual-scope amendment, five
PNG pages and Poppler command/PNG hashes are retained here. Source code is only
under `research/serial_antibiotic_alternatives_20261022/`. Existing maestro pypdf
and bundled Poppler sufficed; no install, PDF editing or artifact-authoring
operation was performed. `pdfplumber` and `pymupdf` were absent but unnecessary.
Render count=5 and source-signature/member/size/SHA checks pass; these verify
source handling, not experimental reliability or efficacy.
