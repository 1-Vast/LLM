# PLK1 study: a new source lead, not yet a matched feedback arena

2026-10-22. Independent addendum; earlier INDEPENDENT.md remains unchanged. Read only root-provided primary text/XML and its receipt, DOI 10.1016/j.xgen.2025.100876, *Identification of targetable vulnerabilities of PLK1-overexpressing cancers by synthetic dosage lethality*. Official Europe PMC XML HTTP200, 290243 bytes, SHA256 a4fbd1b664f35f53a04ca5709332e1d109656664548e6afdc8ff883052e9c05e. No current peer source draft, supplemental table, numerical array, accession page, download or external request was opened by this reviewer.

## Positive scientific lead

This is a genuinely different study from the stopped PRISM/ALMANAC/CDK tasks. It combines genetic perturbation, single-cell state observations and real growth/dropout endpoints, with orthogonal follow-up of IGF2BP2 and a small-molecule inhibitor. It therefore motivates a concrete practical question: does measured perturbation-induced state add functional-target prioritization information beyond prior screen scores, gene identity/annotation and ordinary predictors? Original mathematical primitives are not required before a small properly qualified test of that question.

But the primary does not supply an already authenticated rectangular gene-by-context state/function benchmark or independent task sequence. Availability and matching must be established before declaring a numerical experiment executable. The issue is not algorithmic originality.

## Exact matching audit from the primary

| Measurement | Context / intervention | Scope and relation |
|---|---|---|
| Initial functional screen | HCT116 inducible PLK1-S137D, induced versus uninduced; shRNA | Approximately 18000 genes; 960 hits selected from differential dropout over days 0/8/16. This is not expression profiling of those perturbations. |
| Arrayed growth validation | HCI-010 PDX-derived cells with versus without Cas9; paired guides per target | 105 prioritized genes, 60 meeting reported confluency criterion; Tables S6. Different cell context and perturbation reagent from initial shRNA. |
| In-vivo functional validation | HCI-010 with versus without Cas9, pooled guides; mammary xenografts, three weeks | Same 105 targets, 15 significant hits; Table S7. Separate assay/animals from in-vitro growth, but not independent candidate selection. Their union has 65 hits, overlap 10. |
| Direct-capture Perturb-seq | MCF7-Cas9; 65 already validated genes, two guides each plus controls | 22041 sequenced cells, 7434 after filtering; transcriptomic states only for the validation-selected subset. Not HCI-010 state measurements for all 105. |
| Bulk RNA-seq | HCT116 wild type versus IGF2BP2 knockout in 2D/3D | One perturbation across two culture formats, Table S9; not a multi-target state panel. |
| Chemical viability | MCF7, MDA-MB-231, BT549; IGF2BP2 compounds, 72-hour resazurin | Orthogonal pharmacology for one selected target, not 65 matched genetic perturbations in multiple contexts. |

MCF7 transcriptomic effects cannot silently be called HCI-010 functional-state matching merely because gene symbols overlap. Guide sequences and sample constructs must be reconciled, not only gene names. Counts of cells/sgRNAs are not independent tasks or independent biological backgrounds. The primary reports transcript/protein context dependence: IGF2BP2 knockdown decreases PLK1 mRNA in MCF7/BT549 but increases it in MDA-MB-231/HCT116, while protein effects differ again. This makes cross-context transfer scientifically interesting and forbids assuming interchangeable states.

Timing needs clarification: results/figure describe four days after selection/culture, while STAR Perturb-seq methods say harvested two days after puromycin selection. Do not infer a clean early-state-to-later-function time series from these descriptions. Captured surviving-cell abundance or a PLK1-high cluster fraction is not automatically an independently measured viability endpoint; sgRNA assignment, capture and QC also affect it.

## Library construction is outcome-informed, not a blind whole-genome panel

The chain is explicit: 960 primary HCT116 hits; multiple TCGA expression/survival, CCLE expression, existing Marcotte/Achilles essentiality, chromosome-location and functional/targetability priorities yield 134 distinct genes; 29 failed cloning, leaving 105. HCI-010 in-vitro/in-vivo outcome validation selects a union of 65, and THAT union defines the Perturb-seq library. IGF2BP2 is subsequently selected using the convergent assays/Perturb-seq evidence.

Consequences: using the 65-gene state panel to claim unbiased recovery of HCI-010 SDL hits is circular at the library-selection level. Using Achilles or TCGA values as an untouched external validation set is also unsafe if they helped prioritize this library. Selection is not a proof that every conditional analysis is invalid: a fixed, explicitly selected 65-gene population may still have quantitative functional variation. A prespecified conditional prediction study could test that limited variation, provided complete values, mapping and fair selection-feature controls exist. It cannot extrapolate hit yield to all 18000 genes or treat the original hit counts as its own discovery.

The primary states that the 65 hits were not tested broadly in PLK1-low/nonmalignant controls at that stage. Cas9-minus controls in HCI-010 are not a PLK1-low condition. Therefore pan-library functional selectivity for PLK1-high versus PLK1-low is not established, although specific IGF2BP2 follow-ups support a narrower biological conclusion.

## Endpoint independence and task axes

Expression and HCI-010 functional screens are physically distinct assays, so this source is more than a transcript-only benchmark. They nevertheless differ in cell context, and functional outcomes selected which genes received transcript profiling. Separate modality does not imply independent evaluation selection. Multiple assay replicates and many cells help measurement, not the number of independent later research tasks.

An admissible first capability question could be restricted cross-gene prediction of HCI-010 quantitative function using MCF7 perturbational state, comparing with and without state under the same source labels. It would be cross-context feature transport on a selected population, not demonstrated state dynamics or a trained procedure transferring across multiple independent campaigns. At present that question is NOT_RUN / UNQUALIFIED: source artifacts, complete endpoint vectors and exact legal information are unknown. A prospective target query's measured RNA profile is a paid perturbation assay, not free metadata; all candidate/control methods must receive the same profiles and their costs. A program which observes every target gene's RNA before selection must disclose that acquisition budget.

Such a conventional test could establish a bounded state-feature contribution without inventing a primitive. It would not by itself establish improved updating, agent necessity, inheritance or RSI. To test support-feedback adaptation, a common pre-feedback model and fixed support/hidden-functional partition are also needed; to test inherited improvement strategy, genuinely separate earlier/later tasks and common fresh starts are needed. The currently described single MCF7 panel and HCI-010 campaign do not automatically provide that sequence.

## Accession and artifact availability: concrete but not yet verified

Data availability names SuperSeries GSE203242 with GSE203237 for raw shRNA microarray CEL files and GSE203240 for CRISPR deep-sequencing FASTQ. The paper does not separately identify a single-cell processed count/guide-assignment accession in this statement. It is not permissible to assume GSE203240 necessarily contains the complete MCF7 Perturb-seq expression and guide matrices rather than only pooled-screen sequencing. Conversely this reviewer has not checked its accession contents, so it would be premature to assert those files absent.

Tables S6/S7 are described as in-vitro/in-vivo validated-hit results, S8 as guide sequences, S9 as IGF2BP2 2D/3D differential expression. No table was opened, so full 105-gene quantitative coverage, replicate-level controls, gene IDs and target overlap are NOT_VERIFIED. Other data are available on request according to the primary, and no original code is reported. Article links authenticate a lead, not a verified locally runnable payload. No author contact is sent or authorized by this review.

## Decision and one bounded next evidence step

NEW_SOURCE_LEAD_SUPPORTED; NO_NUMERICAL_EXPERIMENT_YET. This is not a fourth stopped performance experiment and does not close the source. It supplies a real, previously unexecuted conditional state-to-function question, while the exact fair data contract remains unqualified.

The single next discriminator is an accession/artifact manifest and schema audit, WITHOUT response scoring: establish whether processed MCF7 gene-expression/guide data, complete HCI-010 quantitative outcomes for the common genes, controls/replicates, candidate-selection identities and timestamps are actually obtainable. Record exact contexts and availability rather than opening tables to optimize a favorable subset. If the paired payload exists, separately freeze one small ordinary state-feature/feedback test with strong same-information direct prediction and prior-screen controls. No original primitive should be demanded as its prerequisite. If only selected hit summaries exist, necessary state matrices are unavailable, or gene/context mapping cannot be resolved, stop THAT proposed paired test rather than infer general world-model/RSI impossibility. No such accession request or test is performed by this reviewer.

Read limitations/failures: first broad text searches exceeded output limits; focused paragraph reads recovered the relevant selection, assay, timing and availability claims. One grep of single-line XML again produced excessive output and was not used to infer missing data. All findings above are primary-text claims with the stated artifact verification limits, not new numerical evidence. This addendum is final for independent sealing.
