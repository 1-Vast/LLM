# Tripartite BioSample identity-only follow-up

2026-10-22. **All 21 officially linked BioSample records were returned and their accessions/sample-name aliases are authenticated. The aliases suggest structured experimental labels, but their loop/stage/figure-row semantics are not documented in the exported attributes.** This does not yet certify pre-decision genomic states or a complete genotype→functional-row replay. It is not evidence that public function data are absent: root's separately completed `../supplement_followup/REPORT.md` already authenticates real per-strain MIC panels in the public supplement.

## One exact source and restricted projection

After `PROTOCOL.md`, six meaningful synthetic tests and a six-artifact pre-request freeze, a separate worker made exactly one official Entrez BioSample efetch for the already authenticated 21 Entrez IDs. HTTP200, **42,136 consumed response-body bytes**, no truncation, no retry. All 21 requested IDs returned exactly once, with 21 unique SAMN accessions and no missing/unexpected record. URL, headers/status/UTC/bytes/SHA256 and raw XML are retained in `NETWORK.json` and `sealed_source/BIOSAMPLE.xml`; no researcher opened excluded raw fields.

The worker exported only approved identity fields, taxonomy/owner/date and attribute names. All source titles triggered the predeclared phenotype-word guard and were withheld in full; **titles are present but not exported**, not missing. The preserved `Sample name` IDs remain available independently. Attribute values other than `strain`, `isolate` and collection date did not leave the worker. No MIC, fitness, mutation/variation, phenotype measurement, full description or contact-person fields were exported; no numeric endpoint casting or sequence analysis occurred. This is a process/data-flow contract, not OS file-permission isolation.

## Actual identity mapping

Every record reports taxonomy `562 / Escherichia coli`, strain `K-12`, owner `Concordia University`, and collection_date `2024-04-23`. Isolate labels are merely `Laboratory strain 1` through `Laboratory strain 21`; those sequential labels do **not** establish 21 founders/backgrounds. The metadata does not refine K-12 to the BW25113 substrain named in the paper methods; no mismatch is silently repaired. Collection date is the same for all records and is not a recovered per-stage culture timeline. Submission/publication/update timestamps are separately retained as registry metadata.

| Entrez / SAMN accession | Literal sample-name ID | Isolate label number |
|---|---|---:|
| 48118416 / SAMN48118416 | PN-GR-4-4 | 1 |
| 48118417 / SAMN48118417 | PN-GR-4-2 | 2 |
| 48118418 / SAMN48118418 | PN-GR-4-6 | 3 |
| 48118419 / SAMN48118419 | PN-GR-3-4 | 4 |
| 48118420 / SAMN48118420 | PN-GR-3-2 | 5 |
| 48118421 / SAMN48118421 | PN-GR-3-6 | 6 |
| 48118422 / SAMN48118422 | PN-GR-2-4 | 7 |
| 48118423 / SAMN48118423 | PN-GR-2-2 | 8 |
| 48118424 / SAMN48118424 | PN-GR-2-6 | 9 |
| 48118425 / SAMN48118425 | NG-NR-1-4 | 10 |
| 48118426 / SAMN48118426 | NG-NR-1-2 | 11 |
| 48118427 / SAMN48118427 | NG-NR-1-6 | 12 |
| 48118428 / SAMN48118428 | PN-FR-4-3 | 13 |
| 48118429 / SAMN48118429 | PN-FR-4-6 | 14 |
| 48118430 / SAMN48118430 | PN-FR-4-8 | 15 |
| 48118431 / SAMN48118431 | PN-FR-3-3 | 16 |
| 48118432 / SAMN48118432 | PN-FR-3-6 | 17 |
| 48118433 / SAMN48118433 | PN-FR-3-8 | 18 |
| 48118434 / SAMN48118434 | PN-FR-2-3 | 19 |
| 48118435 / SAMN48118435 | PN-FR-2-6 | 20 |
| 48118436 / SAMN48118436 | PN-FR-2-8 | 21 |

Purely lexical patterns are exact: nine `PN-GR-{2,3,4}-{2,4,6}`, nine `PN-FR-{2,3,4}-{3,6,8}`, three `NG-NR-1-{2,4,6}`. These are string products, **not independently certified stage×lineage designs**. GR/FR/NR are not decoded to response classes; PN/NG are not decoded to drug order; 2/3/4 are not automatically evolution stages; final digits are not automatically S1 row indices. Isolate label 8 and sample-name suffix 8 need not mean the same thing.

The only attribute names in every sample are `strain`, `isolate`, `host`, `isolation_source`, `collection_date`, `geo_loc_name`, and `sample_type`. No explicit loop/order, stage/passage, parent/ancestor/lineage, figure/row, first/second attempt or retry field is present in that attribute-name schema. The values of host/source/geography/sample_type were not exported because they were outside this protocol's value whitelist.

## Does this authenticate S1 genome→row→stage?

Root's already reviewed supplement records two 16-row S1 F/G panels and colored row indices marking sequenced selected response groups. The recovered names are concrete candidates for an identity cross-check with those marked rows; the digits alone cannot complete the join. This audit did not reopen the PDF, see its numeric MIC cells or infer color from a name. The official BioSample schema provides no legend mapping its tokens to S1 panel, source culture, exact row, assay stage or first/second attempt. A numeric suffix falling within 1–16 is compatible with many interpretations and is not proof.

In particular, repeated suffixes across `2/3/4` could represent longitudinally related culture samples or something else. No relation table in these attributes certifies which genome existed **before** a future action versus being sequenced after endpoint-based strain selection. The public supplement's existence and the paper's selected-sequencing caption remain separate evidence; neither this count nor these aliases license treating all genomes as free early states.

**Finite decision:** exact sample/accession aliases now permit a targeted, independently documented source-label comparison. Keep genomic-prefix joins, retry ancestry, functional replicate IDs and completeness of alternative actions unqualified until the mapping is certified. Do not call the 21 BioSamples 21 founders, contexts or transfer/RSI tasks. Do not download FASTQ or reopen the stopped state-refinement novelty claim because names are structured. A cross-experiment phenotype diagnostic may still be possible on the publicly exposed MIC panels, but that is a separate task and is not a demonstrated molecular world-model contribution.

## Tests and integrity

Six synthetic tests passed: measured-value/title/contact/description exclusion, digit/leading-zero identity preservation, phenotype-bearing title/strain withholding, allowed taxonomy/owner/date projection, rejection of unapproved attribute values, and history-label preservation without semantic interpretation. `VERIFICATION.json` completed **317 PASS checks**, including all six pre-request hashes unchanged, exact source bytes/hash and 21-ID equality, approved field schema, accession uniqueness, actual name products and missing explicit join fields. The verifier did not decode source XML. Its scope is provenance/identity arithmetic, not biological signal, ancestry truth, genotype/function pairing, world-model/agent/RSI validity.

New code resides only in `research/serial_antibiotic_alternatives_20261022/` with `auditor_biosample` names; all new source, protocol, tests, receipt, projections and this report remain here. The safe postprojection census/verifier scripts were added after response export and are not falsely described as acquisition-pre-frozen. No further HTTP, PDF download, sequence/measurement import, model/API/GPU run or author contact occurred.
