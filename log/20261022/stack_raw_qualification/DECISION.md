# STACK v1: raw objects and paired exported-row schema qualified

2026-10-22. **Decision: MANIFEST_AND_EXPORTED_ROW_SCHEMA_QUALIFIED; RESPONSE_NUMERICS_NOT_OPENED.** The bounded source task made concrete progress: four exact version-bound XLSX objects were acquired and their metadata qualify a limited joint-marker forecast. This is not a performance, new-world-model, agent, inheritance or RSI result. The full research goal remains ACTIVE / NOT_ACHIEVED.

## Authenticated assets and identities

The [source-derived route](ROUTE_DERIVATION.md) resolves the deferred file list for DOI10.17632/3pnv5wh5jm.1. The landing-linked client was inspected as text, not executed. Each exact manifest endpoint returned302; one explicitly validated HTTPS hop per file returned200. [Final acquisition](RAW_ACQUISITION_FINAL.json) verifies every advertised size and SHA256. Total acquired workbook content:11,559,238bytes.

| Exact deposited file | Bytes | Qualified full-table schema |
| --- | ---: | --- |
| Bioactive Compound Library.xlsx | 366,902 | 1,833 unique recorded names, with catalog/layout/CAS/target/SMILES metadata |
| T98G^N + DMSO + 1,833 compounds.xlsx | 2,630,241 | SG+ / NLS blocks,25 matching times0:4:96h |
| T98G^N + TMZ + 1,833 compounds.xlsx | 2,767,016 | SG+ / mKate2+ blocks,25 matching times0:4:96h |
| U2OS^N + 1,833 compounds.xlsx | 5,795,079 | SG+ / mKate2+ blocks,60 matching times0:2:118h |

Each full result table has1,920 identity-bearing rows:1,833 unique named entries, all exact one-to-one matches to the library, plus87 Compound cells of Excel error type e / literal #N/A at A601:A687. The same1,833 names occur in all three screens. None of the87 errors is authenticated as DMSO; the matching T98G control count is insufficient, and the primary reports79 retained U2OS controls. These remain unidentified exported rows. Identity-defined named entries are not an author-QC-passing cohort.

Two marker blocks share one Compound row and matching time coordinates. This qualifies a **paired exported-row bundle**, resolving the previous many-to-many matching concern at this level. It does not reconstruct original wells, unaveraged replicates, independent biological starts or mutually exclusive cell compartments. The exact T98G+DMSO file description says live(mKate2+)/dead(SG+) and agrees with the primary's nuclear-mKate2 assay; this supports an operational live-reporter interpretation of its NLS block. Preserve raw_label=NLS and that inference chain. Exact exporter-key synonymy and calibration across screens remain unverified.

Catalog and nonempty CAS literals are unique in the projected library. Exact SMILES has one conflicting duplicate spanning Doxycycline Hyclate(row574) andE-64(row587). This is annotation ambiguity, not evidence that the entries are aliases. No chemical repair/merge/canonicalization was performed. Distinct names/CAS do not establish1,833 verified unique chemical entities or a valid novel-scaffold split. The [collision report](METADATA_COLLISIONS.json) preserves exact source metadata.

The TMZ full sheet also has side headers AUC/Norm.AUC/Compound/Targets/Pathway/Plate/AverageAUC; its data cells remained closed because their ordering/selection/alignment may depend on outcomes. That Plate header and the library Plate/Position do not establish raw-series plate or run identity. Sheet dimensions are not replicate counts.

## Primary evidence, opposing reviews and unresolved limitations

Forcina et al., Cell Systems2017, DOI10.1016/j.cels.2017.05.002, PMC5509363, provides actual5micromolar multi-compound interventions in U2OS and T98G±400micromolarTMZ. Primary paragraph locations and original formula are retained in [the source audit](data_auditor/INDEPENDENT.md) and [exact evidence projection](data_auditor/SCREEN_AND_FORMULA_EVIDENCE.json). Marker outputs are objects/mm². SG can disappear from old corpses; red/SG double positives can persist; segmentation differs by cell line. Stock differences/running maxima are not authenticated death or birth events. LF's maximum uses only times up to the time scored, never later values in a prefix.

The primary's P055 global three-biological-replicate statement is positive but unmapped. Do not label the three screens as the three replicates, independent research domains, or established single runs. Raw-file run/well/plate mapping, possible averaging and pre/post-censor status remain unknown. Primary >10-fold temporal censoring, initial signal/density QC, future LFmax lethality selection and LED-fit qualification are different response-dependent operations. Current projections did not read QC membership or use future-selected lists.

Preserved primary discrepancies: T98G exclusions say Eight but list nine names; U2OS says seven with a missing separator; common lethal counts79versus80; starting1,833versus retained1,806/1,819; abstract version2versus availability version1. Neither prose nor row position was used to invent missing identities or a preferred mask. The old v2 soft404 does not negate the acquired v1.

Source auditor and scientific skeptic independently drafted before peer access, then conducted actual bidirectional questioning, follow-up challenges and a post-schema debate. Their final reviews are [auditor POST_SCHEMA](data_auditor/POST_SCHEMA.md) and [skeptic POST_SCHEMA](skeptic/POST_SCHEMA.md); actual exchanges are in [auditor CROSS](data_auditor/CROSS.md) and [skeptic CROSS](skeptic/CROSS.md). Root read the final replies. Both accept paired exported-row forecasting and source-supported NLS interpretation while rejecting fabricated well/run identities, unverified chemical aliases and vehicle assignment. No present stop/qualification disagreement remains; empirical measurement, chemical and run uncertainties remain open.

Missing run identities do not prohibit an explicitly limited within-screen development study. Conversely, three related screens and1,833 recorded entries cannot establish broad RSI generalization. Review consensus, manifest availability and synthetic scope checks do not certify biological performance or algorithmic novelty. The closest-method review in the [preceding phase](../dead_stock_information_gate/DECISION.md) remains relevant; no new algorithm or exhaustive novelty clearance was claimed here.

## Next falsifiable numerical task and stop boundary

The next application is early drug-response triage using the named deposited entries: ask whether the complete early SG history helps predict a fixed later exported live-reporter readout, conditional on identical live history/time/background. Source structure now supports that question at the exported-row level. It does not yet establish a valid numerical response panel.

Before opening those values, register exact prefix/target/transform, data-domain and missingness rules, named-entry eligibility, common grouped roles across all screens, information features, model/budget choices, useful-gain and stopping conditions. Use the full-table named panel with no future-QC/LED/lethality selection, or explicitly register a different conditional estimand. Keep all same-entry screens in the same role for unseen-entry evaluation; resolve or conservatively group known metadata conflicts without claiming chemical correction. Unknown controls cannot supply vehicle normalization. Nominal time is source-supported; precise per-plate dosing offsets remain unknown.

The smallest test compares live-only, D0, prefix-end D snapshot and full D history under equal strong-direct model/selection budgets. A history claim must beat both snapshots; a full-D advantage over a weaker arm does not establish a world model. Any world claim then needs same-information direct temporal models, ordinary kinetic/state-space fitting, full retraining, simple fixed/validated mixtures and equal-budget search. Stop mechanism expansion if the registered response domain fails, useful incremental gain fails, or conventional comparisons explain it. Preserve any narrower supported channel value without relabeling it an algorithm.

Agent, continual-learning/active-learning, weight/procedure inheritance and joint benefits require their own fixed-feedback/common-start/equal-budget comparisons on subsequent legitimate tasks. Genuine RSI additionally compares a fixed improver against its revised improvement strategy on later improvement effectiveness, with the same starting predictor and feedback; a selected hyperparameter or more training data is insufficient. None of those comparisons was run here, and no new core was promoted.

This phase stops its source expansion after the bounded successful acquisition/metadata work. It does not stop the overall research goal or request user permission for already authorized future research. The failed HCT116 target/transform gate stays stopped; its outputs were not repaired or rerun.

## Verification and records

[WORK_AND_FAILURES.md](WORK_AND_FAILURES.md) records all acquisition hops, intermediate redirects/exit1, exposure protocols, no-response projections, six passing scope canaries, spreadsheet read-only handling and preserved errors. Code/tests are confined to research/stack_raw_qualification_20261022; all records/data are here. No production or historical frozen file was edited.

VERIFICATION.json records receipt/data hashes, exact schema/identity invariants, closed-response scope-test evidence and preservation of124functional-dynamics plus86dead-stock-phase inventoried files. Final document hashes are in FINAL_FILE_INVENTORY.json, which excludes itself and mutable navigation indexes. New resources:12GETs, four raw workbooks, zero DeepSeek/API-provider calls, zero model fits, zero wet-lab experiments and zero external contact. No performance or RSI outcome exists. Overall goal remains active.
