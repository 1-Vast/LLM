# Independent MULTIseq metadata qualification

2026-10-23. Local extraction from four parent-specified previously sealed official bodies only. Code: research/aml_identity_qualification_20261023/constructive/extract_metadata.py. Exact sample fields, line positions, selected Methods paragraphs and source hashes are in METADATA_EXTRACTION.json. No network, matrix payload, functional measurements, stats records or author-code execution. Methods text includes assay settings and author-reported demultiplex QC; those are source statements, not our performance results.

## New concrete metadata facts

| Source position | Exact field/excerpt | What this authenticates |
|---|---|---|
| aml_samples.body:110060 | `Library name: sample3_scRNA_humanAML_lines_preAraC` | GSM8791699 is pre-AraC GEX |
| 110085,110102 | `MULTIseq barcodes for demultiplexing sample3_humanAML_lines`; `Library name: sample3_MULTIseq_barcodes` | GSM8791700 is its MULTIseq library |
| 110103 | `"Antibody Capture" in processed data files` | MULTIseq signal is explicitly declared as a processed-data modality, not only unnamed raw reads |
| 110096 | `cell line: HL60, TF1, OCI-AML3` | The baseline MULTIseq library pools three human lines |
| 110123 | `SRA: https://www.ncbi.nlm.nih.gov/sra?term=SRX27660161` | Concrete existing metadata pointer for baseline multiplex library |
| 110146 | `Library name: sample4_scRNA_humanAML_lines_postAraC` | GSM8791701 is post-AraC GEX |
| 110171,110189 | `MULTIseq barcodes for demultiplexing sample4_scRNA_humanAML_lines_postAraC`; `Library name: sample4_MULTIseq_barcodes` | GSM8791702 is post-AraC MULTIseq |
| 110190 | `"Antibody Capture" in processed data files` | Same declared processed modality for endpoint |
| 110182,110185 | `cell line: HL60, TF1`; `treatment: 0.01ug/mL AraC (treated HL60 flasks)` | Post library includes lines and mixed control/treated flasks; not per-tag mapping |
| 110210 | `SRA: https://www.ncbi.nlm.nih.gov/sra?term=SRX27660163` | Concrete endpoint multiplex library pointer |

Both MULTIseq GSMs have supplementary_file_1=NONE (110124,110211). This is not evidence no processed MULTIseq data exist: the explicit Antibody Capture declaration and series-level matrices may refer to combined modalities. Matrix feature-type metadata has not been inspected here. Do not equate NONE at the sample field with absent signal, or assume a separate matrix archive exists without checking metadata.

## Primary Methods and code bridge

XML Methods paragraph24 states the HL60 pool is split at day23 post-FACS into scRNA-seq, fixation, cryopreservation and treatment; control/no-AraC and AraC conditions are duplicated; endpoint capture is after89days with MULTIseq. This authenticates experimental chronology at the protocol level, not individual tag labels. Paragraph27 describes LMO001 tagging and feature barcoding. Paragraphs29–30 specify CellRanger multi and adding MULTIseq barcode filtered matrices as Seurat Assay Objects before MULTIseqDemux. None contains a tag-sequence/name→HL60/TF1/OCI or A/B/control table.

aml_gex.body:24–26 explicitly reads Gene Expression and Antibody Capture into Sample assay; lines35 onward run MULTIseqDemux and reject Doublet/Negative. The example path is RS22_invitro_EP, a C1498 mouse example, not an instantiated human sample3/sample4 tag annotation. No replacement table, named MULTI tag assignments, or human flask metadata construction is supplied.

aml_lineage.body:179–192 states the existing strict_founder_hl60s object's sample labels and plotting times: Pre_exp_pool→0; A_midpoint/B_midpoint→36; Control_midpoint→43; A/B/Control→89. This is actual label/time code evidence, but the object is assumed rather than built. The code never joins these labels to GSM8791700/1702's MULTI_ID tags. No proof that all midpoint capture data belong to sample4 is available from these generic post-AraC descriptions. Do not silently place those midpoint cells in the endpoint matrix.

## Qualification decision

**PARTIAL_METADATA_POSITIVE / EXACT_TAG_MAP_UNAUTHENTICATED.** The processed multiplex modality and exact GEX↔MULTIseq library identities are more specific than the previous generic missing-data statement. Tag→line→flask→time remains unproven in these four existing sources. No numeric or modeling GO, no new core mechanism.

Minimal next metadata acquisition, if authorized by parent contract: inspect processed feature-type/name headers and archive member manifests without matrix values to identify whether Antibody Capture rows are present and what MULTIseq tag identifiers are called. Authenticate the sample3/sample4 tag key through a feature reference, CellRanger multi config, author annotation or explicit metadata table. Anonymous oligo IDs/counts alone do not reveal which culture was tagged. SRA library accessions are pointers, not a tag key. Then qualify per-cell demultiplex assignments or reproducible inputs plus the authenticated tag key. Do not infer line identity from endpoint expression response or choose tag labels to match published founder proportions.

Supplementary workbooks are outside this task's inspected source set. Previous schema-only reads cannot authenticate an absent individual-cell tag key, and this report makes no new workbook availability claim. Stop before founder dictionary construction unless the tag key and library namespace can be authenticated; the exact missing fields are tag identifier/sequence, species/cell line, culture/flask, treatment, sampling time, library ID and whether a label is baseline/midpoint/endpoint.
