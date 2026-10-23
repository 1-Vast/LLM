# Cross-review: historical entry and PLK1 source qualification

2026-10-22. Both frontier independent originals and seals retained unchanged. Actually read biology/SOURCE_INDEPENDENT.md, skeptic/SOURCE_INDEPENDENT.md, ROOT_SOURCE_POSITION.md, root_sources/GEO203240_METADATA.json and geo203240.receipt.json. This review performed no new HTTP request, supplemental value/response-array read, model fit, or protected-data access.

## Evidence update after independent sealing

Root's GEO request returned HTTP 200, 3,383 bytes, SHA256 e0d86e9739e7fbc4e1971c24b169806be80c46249b869b390d3970ce183e6606. The authenticated GSE203240 metadata explicitly names [PooledCRISPR], design “Pooled in vivo CRISPR knock-out screen for synthetic dosage lethal hits of PLK1,” 18 GSM entries, and one listed supplementary `GSE203240_Raw_read_counts_matrix.txt.gz`. Thus this accession is positively identified as pooled in-vivo functional screening. The shared abstract's Perturb-seq mention cannot override the accession's design or turn its counts into RNA expression. The 18 samples are not automatically 18 independent cancer contexts; their exact control/replicate roles remain to be mapped.

This strengthens the independent source judgment from “generic CRISPR accession ambiguous” to “this authenticated series is pooled in-vivo.” It does not establish global absence of public MCF7 Perturb-seq data in another accession, an author repository, or supplementary resource. No file listing yet authenticates a joined state/function matrix.

Before sealing I also actually read the newly supplied GSE203242_METADATA.json and geo203242.receipt.json: HTTP 200, 2,470 bytes, SHA256 070d6c9bd9e874f4cdb64915ada0e4e29b1fccb4537a6e6499f413cb4472a09c. This SuperSeries lists only GSE203237 and GSE203240, 31 GSM records, and GSE203242_RAW.tar. The tar was not downloaded or inspected. These advertised resources still do not authenticate an MCF7 expression/guide payload; they do not prove global absence. Do not repeat this completed SuperSeries check as the next action.

## Actual challenges and responses

Skeptic challenged whether functional preselection invalidates every prediction task within the 65 targets. I agree that it does not. Conditioning on the fixed, author-selected population can support a prespecified continuous-outcome study; selection limits the estimand and generalization, rather than logically forcing all functional values to be equal. My independent source report already retained that possibility. Biology and root likewise allow the conditional question. Consequently do not make recovery of every excluded 105/960-gene outcome a universal prerequisite for a selected-65 estimand; do require honest selection, clone failure, perturbation failure, and missingness records for the analyzed population.

Biology reviewer challenged the acquisition budget: measured MCF7 query RNA is a paid perturbation assay, not free gene metadata. Accepted. Every state-using method must receive the same observed RNA at the same cost; prior-screen/annotation and ordinary direct predictors must be strong, and the state contribution contrast must not be confused with a favorable information-budget imbalance. Gene holdout in this panel does not establish inheritance across cell backgrounds or independent later research campaigns.

My challenge to biology and skeptic is the converse: do not demand independent later campaigns merely to allow a small state-feature contribution experiment. Multiple independent campaigns are required for inherited improvement claims, not as a universal prerequisite for this narrower conditional prediction study. If source identities and the target-level test contract qualify, ordinary models can test capability without a novel mathematical primitive. The same distinction applies to source/pathway grouping: a reasonable prespecified grouping can limit correlated target leakage, but no threshold/group definition should be selected for favorable outcome scores.

Both reviewers subsequently explicitly accepted this challenge in direct messages: the later-campaign requirement limits inheritance/improved-improver claims, not the selected-65 capability test; group definitions must precede outcome evaluation; complete 105/960-genome recovery is not a hard gate for the explicitly conditioned estimand. Thus there is no unresolved disagreement on these scope boundaries.

Skeptic accepted the historical scope correction: whole-feedback-compound to disjoint-audit-compound PRISM transfer was proposed but not executed; the later two-pool single-compound coverage test cannot be used to call that separate proposal already measured. We agree it remains NOT_RUN / UNQUALIFIED and cannot be rescued by using previously observed masks to choose new favorable pools or plates. Shared normalization prevents a claim of fresh independent biological replication, while not automatically prohibiting a disclosed conditional utility study.

Both peers' strongest simplicity concern is accepted: initially test whether state provides functional information over ordinary predictors and known selection features. Do not insert a reflector/editor/agent and call it ReTTT transfer before establishing that information opportunity. Conversely, an ordinary capability test may proceed once qualified; absence of an original primitive is not a stop rule for all numerical work.

## The remaining artifact gap, stated concretely

The authenticated paper and pooled-screen series do not yet provide a verified local set of:

1. MCF7 Perturb-seq gene-expression counts, feature/cell identifiers, guide-to-cell assignments, and sample/batch metadata, with perturbation and QC/missingness provenance.
2. Guide-to-target identities connecting the MCF7 library to HCI-010 assays, including constructs/perturbation differences and the six failed-expression knockouts.
3. Complete continuous HCI-010 functional outcomes for the declared common target universe, with controls, replicate/sample identities, assay scale, and a prespecified definition of the target outcome. GSE203240 raw-read-count file identity is useful, but values, full guide mapping and sample roles have not been audited. S6/S7 titles alone do not prove complete continuous or replicate coverage.
4. A resolved timing record for the two-versus-four-day MCF7 discrepancy and explicit temporal interpretation. If the narrow task does not require temporal forecasting, the discrepancy can be disclosed as a limitation rather than falsely resolved; it must not support an early-state/later-fitness claim.

A frozen split/common start and outcome-access ledger would follow successful artifact qualification. They should not be selected by peeking at functional values. Nothing here certifies a trained virtual cell world model, adaptive constructor, agent necessity, or RSI inheritance.

## Executable next step and decision

The next executable step, if this lead is retained, is one bounded **metadata-only source manifest check** of the remaining linked sample/study records and article resource descriptions for an explicit MCF7 expression-and-guide payload; map listed pooled-screen sample/control roles; identify the schema/coverage promised for S6/S7 and guide table S8 without evaluating response values. The SuperSeries and pooled-series metadata requests are already complete and must not be repeated. Exact file URLs/accessions, dimensions stated in metadata, assay contexts and join keys are the deliverable. No scoring, downloading large arrays/tar archives, training, new broad literature search, or contacting authors is implied. This review itself does not execute that next step.

If that bounded check authenticates the required payload, register one ordinary selected-population state-to-continuous-function test with strong same-information controls and assay costs. If it cannot authenticate the state payload or lawful functional join, record that specific access/contract blocker and stop this test's qualification rather than infer universal absence or biological failure. Do not indefinitely repeat metadata hunts.

Current decision: SOURCE_QUALIFICATION_PENDING / NO_READY_NUMERICAL_EXPERIMENT. This is an update to the source's availability evidence, not a new performance result. Historical scoped STOPs, independent originals, and the distinction between capability evidence and algorithmic novelty remain intact. The full project objective remains unachieved.
