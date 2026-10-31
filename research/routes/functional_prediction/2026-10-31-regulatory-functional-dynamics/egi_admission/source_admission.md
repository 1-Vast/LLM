# K562 environmental interaction source admission

2026-10-31. Source/identity investigation only. **Raw count identity and experimental-design admission passes; processed matrix-to-environment admission remains partial. No numerical access, predictive experiment or scientific conclusion is admitted by this report.** A missing source binding is a data limitation, not a scientific negative. Overall research objective remains ACTIVE / NOT_ACHIEVED.

The original study is Herken et al., *Large-scale mapping of environmental-genetic interactions illustrates the dynamic nature of cell-cycle and DNA repair regulation*, DOI `10.1016/j.molcel.2026.01.025`, PMID 41720076, original manuscript `PMC13068139.1` / `NIHMS2148368`. This audit reuses the original XML, supplementary archive, author notebooks, GEO SOFT records, two count gzip files and aligned guide reference under `D:/MAESTRO/data/external/conditional_interventions_20261030/egi/`. `identity_design_projection.json` pins their exact bytes, SHA-256 hashes and identities. Source acquisition provenance remains in the prior original `request_receipts.jsonl`; this round's three new receipts are separate.

## Exact raw sample and condition support

`sample_binding.tsv` provides all 14 endpoint/T0 columns with GEO accessions, batch, biological replicate and matched reference. The binding uses original GEO titles/characteristics and original calling-notebook source cells 6-10, not notebook outputs.

| Experiment | Count-file columns | Exact source meaning |
|---|---|---|
| GI1, Rep1 | `Rep1_T0`, `Rep1_UT`, `Rep1_DRUG` | GSM9350639, GSM9350641, GSM9350643: initial, vehicle reference, AZD6738 ATR inhibition |
| GI1, Rep2 | `Rep2_T0`, `Rep2_UT`, `Rep2_DRUG` | GSM9350640, GSM9350642, GSM9350644: matching second replicate |
| GI2, Rep1 | `t0_r1`, `dmso_r1`, `etop_r1`, `keto_r1` | GSM9350645, GSM9350647, GSM9350649, GSM9350651: initial, vehicle reference, etoposide, glucose deprivation |
| GI2, Rep2 | `t0_r2`, `dmso_r2`, `etop_r2`, `keto_r2` | GSM9350646, GSM9350648, GSM9350650, GSM9350652: matching second replicate |

`14_GI_expt1_counts.txt.gz` is tab separated. `15_GI_expt2_counts.txt.gz` is comma separated despite its `.txt` stem. Header detection precedes identity projection. No count field was converted, retained, summarized or displayed.

These are K562 CRISPRi screens with stable dCas9-KRAB expression. GEO's generic genotype field says WT; it does not negate the engineered CRISPRi background stated in original Methods. `KETO` is explicitly GEO `Glucose Starve`, not a ketone treatment. Three intervention environments use two reference batches. Etoposide and glucose deprivation share GI2's reference and replicate-specific T0. Batch1-reference minus batch2-reference is not a fourth environmental treatment.

Methods S24.1 says transduction and passaging were performed in duplicate as independent biological replicates. GI-screen T0 is seven days after transduction. All three screens end nine days after T0. ATRi uses 1.25 uM AZD6738 on days 0 and 7. Etoposide uses 500 nM on day 0, medium replacement at 24 h, another dose on day 3 and subsequent daily splitting without washout. Glucose deprivation uses glucose-free RPMI throughout days 0-9. A day-0/day-9 endpoint supports differential enrichment; it does not identify continuous-time dynamics. The original source does not supply individual culture/transduction IDs beyond experiment/replicate labels or prove that arms sharing an initial culture are independently cultured experiments.

## Guide, control and orientation identity

An independent identity-only scan verifies 407,044 unique ordered construct identities in each count file. Both sets exactly equal the aligned reference and form the 638-by-638 guide identity grid. Every construct identity is exactly `name_a:name_b`; zero library identity/name disagreements were found. Identity presence does not establish a positive or sufficient count.

The reference has 625 targeting guides for 313 source target genes plus 13 NTC guides. 312 genes have two guide identities; CSRP2BP has one. `guide_identity.tsv` records exact guide, source gene, source sequence, analysis label and NTC indicator. All 13 `non-targeting_*` guides have source gene label `negative`; processed matrix control identity is `non-targeting`. The internal `REV3` to `REV3L` mapping is supported by those exact guides' `REV3L_*` names and matrix labels. It is not an independently authenticated universal synonym assertion.

Vector positions a/b distinguish AB and BA. Genomic `+`/`-` in a guide name is a different property. Guides, orientations, NTC partners and matrix triangles do not add biological cultures. For an unordered gene-pair split, keep every guide combination and both vector orientations together. The raw 313-gene identity universe contains 48,828 structurally indexed distinct pairs; the processed 303-gene universe contains 45,753. Neither is a count of valid numerical observations.

## Native processing and residual supplementary-file binding

Calling-notebook source cells 11-15 intersect passing constructs between biological replicates, then take their arithmetic mean **at the normalized phenotype stage**. Cells 16-19 generate phenotype matrices, average AB/BA, fit guide-specific quadratic relationships, standardize residuals by query NTC residual SD and aggregate guide combinations to genes. Thus native maps pool biological-replicate phenotypes before fitting; they are neither pooled raw reads nor means of two independently fitted GI maps. The native GI is a standardized fitted residual. Native differential GI subtracts separately fitted and separately standardized maps, not an algebraic double-minus-single count contrast.

Per-replicate source paths are present in cells 24-33 and imported by `replicate_quality_control.ipynb`. Rep1 phenotype generation and many output writes are commented in the deposited calling notebook. Their existence supports reconstruction in principle, not a certified clean end-to-end run. No author code was executed. `methods_variable_projection.json` retains source evidence without any notebook output; growthScores numerical values were excluded. The original code supplies all ten experiment/replicate/condition growthScores keys.

All eight original workbooks were independently reprojected using string row-1/column-A identities only. Each has 304 matching row/column identities: 303 targets and NTC, with the same axis order. No numerical cells, finite/missing masks, value symmetry, replicate correlations, headroom or published response distributions were inspected.

| Original member | Table / XML xref | Current binding |
|---|---|---|
| MMC4.xlsx | Table S3 / SD10 | Member of the reference1/ATR pair; exact member unresolved |
| MMC5.xlsx | Table S4 / SD12 | Member of the reference1/ATR pair; exact member unresolved |
| MMC6.xlsx | Table S5 / SD4 | **Exact: native ATR GI minus matched reference1 GI** |
| MMC7.xlsx | Table S6 / SD11 | Member of the reference2/etoposide/glucose group; exact member unresolved |
| MMC8.xlsx | Table S7 / SD9 | Same group; exact member unresolved |
| MMC9.xlsx | Table S8 / SD3 | Same group; exact member unresolved |
| MMC10.xlsx | Table S9 / SD5 | Member of the etoposide/glucose-minus-reference2 differential pair; exact member unresolved |
| MMC11.xlsx | Table S10 / SD6 | Same differential group; exact member unresolved |

Every member's full original name and SHA-256 is in `environment_binding.json` and its TSV projection. The Table S5 binding is independently reconfirmed from the original xref/file metadata and the already authenticated identification sentence. Other original xrefs give group-level statements, not a per-member title. Workbook properties contain no condition title. The 12-page supplementary PDF contains no extractable Table/Data caption-start catalogue. The public Elsevier API returned bibliographic metadata only; the ordinary ScienceDirect article page returned 403. No access workaround followed. Filename/list order and creation timestamps are not scientific identity evidence. The unresolved members must not be assigned by assumed order or by numerical response matching during source admission.

## Per-replicate raw endpoint feasibility and gates

The original count design supplies matched treated and reference endpoints, the same replicate's T0, all guide pairs, both vector orientations and exact NTC controls. It therefore supports defining a **new per-replicate environmental double-vs-single differential enrichment contrast** after a separate frozen numerical protocol. `replication_label_contract.json` gives the symbolic identity-level interface and all outstanding choices; its companion Markdown explains the dependence boundary.

A fixed algebraic local contrast can avoid the native query-wide baseline fit. Native `calculateInteractions` fits each query against every paired phenotype involving it; fitting it over held-out double outcomes can make development labels depend on held-out responses. Declaring published maps as a fixed derived measurement object is a narrower benchmark. A strict raw-phenotype holdout needs a local fixed algebraic label or a predeclared training-only label fit, with its changed estimand explicit. This report does not select a model, environment, split, pseudocount, count filter, noise threshold or numerical result.

The native screen panel was selected using ATR nominating-screen phenotypes plus DDR prior genes. The validation library was selected using discovery-map properties and uses a different treatment regimen; it is not an unbiased sealed confirmation panel. Two biological replicates and shared controls limit precision. Replicate agreement, sufficient depth, label availability, useful prioritization support and any test's headroom remain unknown. These require the coordinator's separately admitted numerical audit, with the same pair's guides/orientations kept in one split and no held-out counts used for feature, baseline, imputation, selection or tuning decisions.

## Access, exposure and completion

This round used 3 counted HTTP attempts and 857,673 completed decoded body bytes, including the 403 response. No redirect, retry, unknown partial traffic, broad count acquisition, downloaded-code execution, model fit, external message or access bypass occurred. Requests were sequential to three different origins. No original/prior frozen file or shared index/library was changed. 19 attempts and 47,142,327 bytes remain unspent; the coordinator requested no further network or reallocation. `usage.json`, `request_audit.json`, original receipts and `processing_receipts.json` preserve the accounting and hashes. Wire totals are not certified.

Reading was limited to source/methods/variables, sample/header/identity metadata and the stated supplementary search. One numeric-masked xref identification probe accidentally displayed two qualitative published gene/interaction-direction sentences. No numerical GI values, count values or headroom/distribution results were displayed or used. This source auditor must therefore not be presented as an outcome-unexposed independent challenger. The acquisition bodies were preserved opaque except the declared identity/source projections. No memory rollout was read. The deliverable is a source-supported raw endpoint interface and a precise partial native-binding limitation, not an experimental result.
