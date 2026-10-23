# PLK1 SDL primary source — independent entry assessment

Independent of new peer source opinions. Local source only: `root_sources/plk1.txt`, primary XML body and retrieval receipt; DOI 10.1016/j.xgen.2025.100876, “Identification of targetable vulnerabilities of PLK1-overexpressing cancers by synthetic dosage lethality,” published May 9, 2025. Parent obtained the XML with HTTP 200, 290,243 bytes, SHA256 a4fbd1b664f35f53a04ca5709332e1d109656664548e6afdc8ff883052e9c05e. I made no network request and opened no supplementary numeric files, expression matrices, assay arrays, or reserves. Initial broad fulltext display was truncated; relevant Results, direct-capture methods, fitness methods, and availability were then read in targeted passages.

## What exists, without inflating its matching

| Component | Biological and assay unit | What the article establishes |
|---|---|---|
| Initial SDL fitness | HCT116 with inducible PLK1-S137D, pooled shRNA, days 0/8/16 | Approximately 18,000 genes screened, 960 hits. This is functional dropout, not transcriptomic state. |
| Arrayed validation | HCI-010 PDX-derived breast cells ±Cas9; 105 genes, two sgRNAs pooled per gene; image confluency | 60 hits; Table S6 advertised. Separate assay from Perturb-seq. |
| In vivo validation | HCI-010 PDX in mice ±Cas9, same 210-guide library, 3-week dropout | 15 hits; seven tumors per condition; Table S7 advertised. |
| State profiling | MCF7-Cas9; 65 previously validated genes; 130 targeting guides plus controls; single-cell RNA and guide capture | 22,041 sequenced cells, 7,434 retained, ≥50 cells for most knockouts. Three batches aggregated; no automatic claim of three independent experiments. |

The 65-gene Perturb-seq panel is the **union of positive in vitro/in vivo hits** (60 + 15 − 10 = 65), after upstream filtering/prioritization. It is not a random sample of all 105 validation targets or the genome. Six knockouts failed the expression-reduction check and were excluded from subsequent analyses. Exactly how many perturbations support a new proposed task cannot be inferred by treating 7,434 cells as independent target-level samples.

The state and independent functional assays are matched by target identity in principle, **not by cell background or sampling time**. Perturb-seq was in MCF7; the two 105-target validation assays were HCI-010. The initial shRNA screen was HCT116. All three express elevated PLK1, which is a biological hypothesis for transport, not equivalence. The source also explicitly says it did not prioritize PLK1-low/nonmalignant controls for all 65 hits at this stage; therefore the whole panel does not establish selective therapeutic vulnerability rather than generic essentiality.

A useful concrete source inconsistency: Results and Figure 2 legend say four days post-selection before Perturb-seq, while direct-capture Methods say harvested two days after selection. Any time-matched task needs a sample manifest to resolve this; silently choosing the preferable time would be invalid.

## Independent fitness versus a state-derived proxy

The 65-gene MCF7 single-cell analysis uses cluster occupancy, positive-control co-enrichment, and depletion of PLK1-high cells to shortlist genes. Those can reflect state change, survival, proliferation, capture efficiency, or guide representation; they are not an independently measured MCF7 viability label per target. In particular IGF2BP2 knockout reduces PLK1 expression itself, so fewer PLK1-high cells need not identify cell killing independently of transcriptional change. A model trained on state to predict a label defined from the same state would not establish state-to-independent-fitness capability.

The HCI-010 confluency and mouse-dropout assays are real separate functional outcomes, so the paper does not lack all independent functional measurements. A **cross-context transport** task could potentially ask whether MCF7 perturbation states help rank HCI-010 functional outcomes among a fixed selected target universe. That is scientifically meaningful and ordinary methods would be admissible. It must, however, be explicitly framed as transport across cell backgrounds and as conditional on outcome-dependent panel selection; it cannot be advertised as matched same-background fitness prediction or an unbiased new-target screen. The selection union also prevents claiming the in vitro/in vivo labels were wholly uninvolved in target availability.

The drug assays (72-hour resazurin responses to 5–75 μM compounds in MCF7/MDA-MB-231/BT-549, repeated experiments) validate selected IGF2BP2 inhibitors. They do not supply a broad 65-target matched drug-response panel or a series of independent improvement tasks. Genetic knockout and a chemical inhibitor are distinct interventions.

## Availability and finite experiment decision

The article names SuperSeries GSE203242, with GSE203237 for raw shRNA microarrays and GSE203240 for CRISPR deep sequencing. It states other data are available from the lead contact on request and original code was not reported. This text alone does **not** identify a publicly retrievable processed Perturb-seq gene-by-cell matrix, guide/cell mapping, complete independent fitness table, or replicate manifest. Conversely, the generic “CRISPR screen” accession description is not proof that Perturb-seq reads are absent. No GEO metadata/file listing was checked in this review, so availability is UNVERIFIED rather than asserted nonexistent.

Decision: **NO READY MATCHED-STATE + INDEPENDENT-FITNESS ENTRY FROM THE PRIMARY TEXT ALONE.** Retain this as a concrete source qualification lead, not a failed experiment. A later metadata-only accession inspection could settle whether expression/guide mappings and independent assay sample identifiers are actually public. It would not by itself solve cross-context transport, outcome-dependent target selection, sparse independent target count, or missing temporal task sequence. Do not open numeric supplements merely to see whether the hoped-for contrast is favorable.

No finite training experiment is registered or run here. The source supplies a genuine intervention-to-state-to-functional-validation scientific chain and a possible transport application; it does not yet supply a ready lawful feedback stream with enough independent held-out perturbations to compare a frozen versus evolving improvement constructor. Hence it does not change the original local-asset NO_READY_ENTRY conclusion or establish WM/agent/RSI contributions. This is not rejection for lack of a new algorithmic primitive.
