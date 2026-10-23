# PTPC public supplement: five new backgrounds have a paired state / Efficacy schema

2026-10-22. Source qualification completed without reading other roles' new scientific drafts. The publisher ZIP was downloaded once and only table identities, metadata, headers and annotation text were inspected. **No Efficacy value was exposed or scored; no class prevalence/missingness/consistency, protein abundance, performance sheet, or new numerical outcome was inspected.** The bounded header script resolves text cells internally to replace literal outcome calls with a suppression marker before output; it does not preserve those calls in derived views. The full identity pass skips Efficacy cells without resolving them. Original primary9file seal remains unchanged.

**Decision: positive new-source qualification at the schema/identity level.** Actual TableS8 contains measured-proteome sample IDs and an `Efficacy` field on the same sample records for five backgrounds outside the old18stocks/17lineages. It is no longer correct to call this merely an unavailable abstract promise or a protein-only table. The source can justify freezing a narrow, outcome-unopened local PTPC task around the author's published Efficacy column. This does not yet authenticate its assay horizon/dose/cutoff, pretreatment trajectories, useful class variation, or a successful method. Unknown cutoff does not universally forbid predicting a published label; it limits the biological and decision interpretation of that target.

## Actual archive and selected tables

One GET of the exact saved publisher link returned HTTP200,126,369,414bytes, complete below256MiBcap; SHA256 `efdcbdab1f67d23e963208b3957164a95ff9a4485141b9e61aa852457a42e133`. Request lasted09:21:25–09:29:46UTC. It is terminal with no live process or repeat request. `ARCHIVE_MEMBERS.json` lists18workbooks. Only these selected workbooks were opened in memory:

- `TableS8_PTPC_info_0703.xlsx` (66,582,301bytes), sheets `Legend`, `A_metadata`, `B_drug_info`, `C_protein_Matrix`.
- `TableS7_PTNC-20260703final.xlsx` (34,077bytes), sheets `Legend`,`A`,`B`,`C`,`D`; only Acompound identities and Bfunctional-identity columns were read. C/Dperformance sheets were not opened.

No archive member was extracted as an executable or run. The whole archive is retained as an unopened outcome source for any later frozen experiment; receipt, directory and permitted views are separate evidence.

## Strong positive join actually verified

S8 `A_metadata` actual full header:

`Sample_ID | Cell_line | Cell_plate | Pert_ID | Compound_name | Pert_time_(hrs) | Efficacy | Rep`.

S8 `B_drug_info` has Pert_ID, catalog number, compound name, CAS, SMILES, formula, pathways, indication, solvent, target and compound-type descriptors. There is no dose column in either authenticated header. The Efficacy column is present on the same metadata records as state identities; its values remain unexamined. Thus this is a paired **state/author-Efficacy schema**, rather than borrowing condition-level labels from an unrelated table.

The complete identity-only pass found actual cell names `A375`, `HCT116`, `NCI-H1975`, `NCI-H2170`, `Panc1005`. The paper/workbook Legend spells the last `Panc10.05`/`Panc 10.05`; this is a recorded punctuation alias, not a sixth background. The other four match the paper names directly. All five are absent from the old18stock identifiers and normalized17lineage names.

The first column of S8 `C_protein_Matrix` is `Sample_ID`; its2,217identity entries match the2,217metadata entries **in exact row order**, not merely set membership. Only that column was read; no abundance cell was converted. This authenticates a usable state-table correspondence. Because Sample_ID is not unique, a generic many-to-many merge on that column would be wrong. Retain the authenticated row mapping and verify row/rep context in any numerical adapter.

## Counts and units are metadata, not thousands of independent tasks

| Actual background | Metadata rows | Blank Rep | techrep | biorep | Distinct Pert_IDs including controls |
|---|---:|---:|---:|---:|---:|
| A375 |216|198|11|7|103|
| HCT116 |1,289|1,204|47|38|603|
| NCI-H1975 |249|210|10|29|110|
| NCI-H2170 |255|217|10|28|112|
| Panc1005 |208|192|8|8|96|

Totals are2,217rows:2,021blank Rep,86`techrep`,110`biorep`. There are2,131distinct Sample_IDs and86duplicated IDs;80occur as blank-Rep+techrep and6as biorep+techrep. There are2,021distinct `(Cell_line,Pert_ID,Pert_time)` design groups. These structural counts agree with the legend's overall2,021plus196repeat accounting, but do not establish independent efficacy assays per row. Actual functionality, label variation and repeat agreement were deliberately not checked. A molecular timepoint or technical repeat must not create an extra functional measurement purchase or independent RSI task. Inference across new backgrounds has at most five line-level units under this asset, with heavily unequal coverage; HCT116has most records.

`S8_IDENTITY_ROWS.json`, `IDENTITY_RESULT.json` and `OLD_STOCK_AND_CONTROL_CHECK.json` preserve allowed identities and counts. They contain no response labels.

## Exact overlap with the old seven-file release

Only the first identity field of the original `allcelltype_drugpair_crossdrug_loo_label.csv` was read, never pheno.csv or expression data. The file has **no header**; its first row is the identity/time record `BT20_#10,24`. The retained loader's exact rule is stock=experiment prefix before the first underscore, lineage=stock with literal `(ATCC)` removed. Its hash `a790fd20a0b0b4d6327d8db94ec954e616482b6d44a977dfcbd75f52502bcadb` matches the original manifest.

The actual18stocks are BT20,BT549,DU4475,HCC1143,HCC1187,HCC1395,HCC1806,HCC1937,HCC38,HCC70,HS578T,MCF7,MDA-MB-231,MDA-MB-436,MDA-MB-453,MDA-MB-453(ATCC),MDA-MB-468,T47D. These collapse to17lineages; none overlaps the five actual PTPC names after case/punctuation normalization. This is materially new relative to that old split. It is not a claim that every drug is new, that the public foundation checkpoint never saw PTPC, or that no other historical project ever exposed a PTPC label. Checkpoint training exposure remains unknown, so retrain admissible models from allowed source partitions for any strong transfer claim.

The oldsplit STOP stays valid; new PTPC identities do not convert oldfinal labels into a fresh blind set. This gate kept new Efficacy/proteome quantities unexamined, which supports a **local outcome-unopened** task candidate, not absolute public-data OOD or prospective discovery.

## Important time and baseline discrepancy

Every actual S8metadata row has molecular Pert_time6or24hours. This includes explicit `control` samples at6/24hours; there are **no0hmetadata rows**. Both saved SI and actual workbook Legend instead say “with control samples assigned a perturbation time of0h.” `S8_ANNOTATION_METADATA.json` preserves the literal DrawingML legend text; no images or outcome cells were read.

Preserve this discrepancy rather than recoding controls to0. Time-matched untreated/control samples may support a separately defined reference, but they are not authenticated pretreatment samples of the same culture. No measured0→6→24history, same-live-cell trajectory, historical assay turnaround, or pre-outcome timing contract is established here. An offline measured-state→published-label task does not need to claim those properties. A prospective early-state decision or baseline-conditioned dynamical task would require the corresponding source fact.

## Efficacy meaning: what S7 does and does not fix

S7B's exact header is `Cell_line | Pert_ID | Efficacy`. Its173identity rows concern only BT549,HCC1806,HS578T,MDA-MB-468, all in the old lineage universe and **none** in S8. PTNC S7and PTPC S8must not be joined merely by Pert_ID or treated as the same assay cohort.

Saved SI S7Bexplicitly describes24h cell viability, three biological replicates, resistantN/sensitiveY calls under main-Methods criteria, and removal of condition pairs with inconsistent repeated labels. Those statements apply to **PTNC**. S8's actual workbook Legend, matching saved SI S8, describes proteomic metadata, new backgrounds and matched abundance matrix but **does not define Efficacy**, its horizon, assay method, class coding, numerical threshold, or replicate-level functional normalization. S9describes PTPC classification evaluation at paper level, but no S9values were read and it cannot supply the missing assay contract. The original README describes efficacy/synergy probability globally, not PTPC-specific label provenance.

Accordingly, the narrow known target is the author's PTPC **Efficacy field**, a function-related classification annotation whose exact assay semantics remain partly unknown. Do not claim it is a24h fixed-dose viable-cell utility, calibrated IC50, or same-aliquot independent live-cell measurement merely because S7has24h calls. Predicting the released label can be a valid explicitly limited retrospective task once the frozen protocol specifies label decoding/coverage and grouping. Biological threshold interpretation and therapy-value claims require more evidence.

## Next frozen numerical qualification, if the mechanism merits it

This source supports a new candidate population—five non-breast backgrounds with matched state IDs and Efficacy schema—without reopening oldPTVconfig. Before values, specify the target as authorEfficacy prediction or a newly authenticated measured utility; distinguish molecular feedback at6/24from label acquisition and keep all repeated condition rows together. Define how to handle no0hbaseline, plate controls,86duplicate sampleIDs,Rep aggregation, unequal background/drug coverage, missing labels and class-degenerate groups; do not choose favorable groups after viewing prevalence. New background-level evaluation is limited to fiveunits and cannot support arbitrary deeprecursivegenerations as fiveindependenttrain/dev/testfamilies.

The immediate next action should be only a separately frozen **label-type/legal-missingness and condition-deduplication gate**, deciding in advance which partition's values may be inspected, which Efficacy encodings/missing tokens are valid, and how every culture/background×compound keeps all6/24h and Rep rows together to prevent leakage. Do not inspect labels now, fit models, select favorable classes or run searches. Later mechanism experiments would need their own same-information strong direct/refit/kernel/simpleblend comparisons and protected later evaluation. The present identity audit does not preregister such an experiment, prove positive benefit or authorize free repeated hidden-label selection. Unknown published-checkpoint exposure remains explicit. No new API agent search was run.

## Verification and stop boundary

The9originalprimaryfiles and sealed scripts are rehashed by this stage's seal. Exactly1newHTTPrequest occurred in this archive follow-up. All label values and abundance remain unopened. No application, email or external message was sent. No tests were added for the reversible source-extraction scripts; their substantive checks are exact metadata/matrix ID-order correspondence, source-hash match and old/newidentity disjointness. Stop here at positive schema/source qualification with unresolved functional and timing semantics; complete research goal remains unachieved.
