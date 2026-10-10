# Literature consulted for the phenotype-anchor block (2026-10-10)

Reading depth is stated per source. "Search abstract" means that only search-engine summaries,
indexed abstracts or publisher landing pages were read; no full text was read. No claim below
depends on a passage the study could not read.

| Source | Depth | What it establishes | Bearing on this study |
|---|---|---|---|
| Tahoe-100M, *Cell* 2026 (doi 10.1016/j.cell.2026.08.035); bioRxiv 2025.02.20.639398 | Search abstract; supplement and full text blocked (publisher 403, bioRxiv 429) | 50 lines co-cultured as "cell villages" (pooled spheroids), 24 h, 379 drugs x 3 doses. Survival (log fold change of cell counts vs DMSO) and cell-cycle arrest (log odds ratio) are reported phenotypes. Three low-count lines were excluded. | The endpoints are the dataset authors' own phenotypes, not invented here. The exact formulas are unread, so section 2 of the protocol is an adaptation. The low-count exclusion matches this study's CONTEXT_UNDERCOUNTED rule. |
| McFarland et al., *Nat Commun* 2020 (MIX-Seq; doi 10.1038/s41467-020-17440-w) | Search abstract | Pooled cell lines are demultiplexed by SNPs. Short-term transcriptional responses predict long-term viability. | Prior art for the RNA-to-viability bridge. That work used measured responses; here the bridge input is a world-model forecast for unseen lines. |
| Szalai et al., *NAR* 2019 (doi 10.1093/nar/gkz805) | Search abstract | A viability/proliferation signature dominates perturbation transcriptomes (LINCS paired with CTRP). Viability is predictable from signatures. | Prior art for the bridge. Its pairs crossed assays (L1000 vs CTRP); here RNA and phenotype come from the same spheroid. |
| Hafner et al., *Nat Methods* 2016 (GR metrics) | Known reference; not re-read | Division rate confounds drug-sensitivity estimates. | Motivated the growth-confound check. In development, the leading interaction factor did not track DMSO cycling fraction (r = 0.10). |
| Viñas Torné et al., *Nat Biotechnol* 2025 (Systema; doi 10.1038/s41587-025-02777-8) | Search abstract | Perturbation predictors largely reproduce systematic variation; simple baselines match them. | Requires baselines that capture systematic structure: arms Z, O and B, and selectivity targets that remove the drug mean. |
| Ahlmann-Eltze, Huber & Anders, *Nat Methods* 2025 (doi 10.1038/s41592-025-02772-6) | Search abstract | Deep perturbation models do not yet beat simple linear baselines. | B (basal-similarity transfer) and a linear bridge are the comparators STATE must beat. |
| MAP, *Nat Mach Intell* 2026 (doi 10.1038/s42256-026-01286-w) | Earlier MAESTRO blocks (2026-10-08/09) | Knowledge-driven prediction for unprofiled drugs, evaluated on RNA and GSEA. | No viability endpoint. A web search (2026-10-10) found no 2025-26 paper that chains a virtual cell's predicted transcriptome into zero-shot viability validated against measured viability. That is a search result, not a proof of absence. |

## Positioning

Two parts are established methods, not contributions: top-k selection from a ranked prior, and
kernel or ridge transfer between cell lines. The question under test is narrower. Does a frozen
virtual cell's forecast for an **unseen** line, read through a phenotype measured in the **same
spheroid**, carry decision information beyond basal-similarity transfer? The study also tests
two framework devices for refusing a world model before using it:

* the world-model value ceiling gate, using observed RNA as a perfect-world-model proxy on
  reference lines;
* count qualification.
