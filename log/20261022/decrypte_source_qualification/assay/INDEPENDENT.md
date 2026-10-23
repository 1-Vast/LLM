# decryptE assay-contract independent review

Date: 2026-10-22. Scope: saved authenticated author full text only; no network requests, no supplementary workbook, no new biological matrix or protected reserve was read. No architecture proposed or biological performance claimed.

Sources: `log/20261022/early_update_mechanism/biology/decryptE_fulltext.xml` (SHA256 `16b7aea45dc88bf017248ce74e2eb24fecb6ade6c7adc069f49bd6fd87978640`) and `decryptE_PROSE.txt` (SHA256 `28a816e6ed43b28c9a91859cc80f08c391e365ffe6967b8e63c02f2f092f6fe6`). Bracketed paragraph indexes below refer to that prose extraction. Paper: Eckert et al., DOI 10.1038/s41587-024-02218-y.

## Independent disposition

**QUALIFY_METADATA_ONLY; functional learning task not yet qualified.** The paper does explicitly support dose-resolved phenotypic measurements for all 144 drugs and a close experimental relationship to the proteomics. It does not yet establish an accessible raw drug-by-dose-by-assay matrix with individual controls, independent repeats, stable join keys, or adequate signal beyond noise. "Only marginally affected" is a substantive signal risk, not evidence of a useful functional-prediction benchmark. Source qualification must precede model fitting or candidate promotion.

## What is and is not established

| Contract item | Explicit author evidence | Remaining limitation |
|---|---|---|
| Biological system | Jurkat Clone E6.1, ATCC TIB-152; main screen 144 drugs from 16 classes [7,24] | One cell background is not 144 independent cell tasks; drugs within class/chemistry can be dependent. |
| Dose/control | Five doses 1,10,100,1000,10000 nM and DMSO [7,27]; three DMSO controls per 48-deep-well plate [27] | Plate IDs, sample IDs, control allocations and numerical availability not yet known. |
| Exposure | Main treatment 18 h unless otherwise stated [27]; compound-treated proteomic pellets processed after 18 h [32] | Must not collapse all functional measurements to an exactly simultaneous 18 h endpoint. |
| Functional source relationship | After compound treatment 100 microliters of cell suspension **per well** transferred to 96-well plate [28]; main text says all drugs across same dose range "in parallel" [7] | Supports shared treatment-source aliquot/protocol, but an actual well-to-proteomic-row mapping is not supplied by prose. Do not claim same cells were measured destructively twice or an authenticated exact row join. |
| Cytotoxicity | IncuCyte Cytotox Dye, 250 nM final, with alamarBlue 10% v/v [28]. IncuCyte: 3 h time course, hourly, 10x, five images per well, phase contrast + fluorescence [28] | Which time-point or aggregate becomes the tabulated endpoint unknown. Five fields/time points are correlated measurements, not five independent biological repeats. |
| Morphology/confluency | IncuCyte Basic Analyzer used for confluency/cytotoxicity [28]; main text calls morphology [7,8] | Morphology may be images or confluency summary; do not assume a separate numerical morphological phenotype vector. |
| Metabolic activity | alamarBlue read after 3.5 h on FluoStar Omega, excitation 544 nm, emission 584 nm [28] | This is delayed relative to initial 18 h exposure (nominal ~21.5 h if incubation proceeds sequentially); not direct cell count, growth or killing. Whether drug exposure is maintained after dilution should be retained as protocol context, not assumed unchanged. |
| Normalization | Confluency and metabolic values divided by average DMSO controls; cytotoxicity first corrected for confluency, then normalized to average DMSO [29] | Exact cytotoxicity correction formula, plate/batch normalization scope, denominator values and control-level uncertainty not provided in prose. Near-zero baseline cytotoxicity may complicate ratios; do not infer its numerical severity without values. |
| Dose-response fits | Same four-parameter sigmoid procedure applied to normalized viability metrics [29,56,57] | Fitted outputs are not raw dose measurements; parameters/curves estimated using held-out doses would leak future feedback if used as targets/support features. |
| Full-screen repeats | Three DMSO per plate [27]; 48 DMSO proteomic replicates in full screen [7,63] | Number of independently cultured/treated wells per drug-dose functional condition is not stated. Do not extend special replicate experiments to the full 144-drug screen. |
| Noise/reproducibility | 19% median CV from 48 DMSO for proteomic assay [7, Extended Data Fig.2a]; four-repeat pEC50 analysis for palbociclib, panobinostat, colchicine [65, Extended Data Fig.2c] | Neither is a validated functional endpoint noise model. Across-dose protein CV [64] mixes dose effects with variability and cannot estimate independent measurement noise. |
| Functional dynamic range | Main text explicitly says metabolism, cytotoxicity, morphology "only marginally affected" [7]; viability marginal for HDAC examples [15] | No quantitative effect-vs-noise separation yet; obtaining all matrices may still result in a stop. |

## Special functional followups cannot substitute for full-screen labels

The NFAT T-cell activation experiment uses engineered TCR/CD3 effector cells, selected HDAC inhibitors at the same five doses, **16 h** pretreatment followed by CD3/CD28 activation and **5 h** before luciferase readout, normalized to DMSO [68]. It is not the ordinary E6.1 18 h proteomic assay and not a universally measured 144-drug endpoint. Its independent repeat count is not stated in the prose method.

Primary-cell work involves two healthy donors (both male, age 26) [36], sorted CD4/CD8 and naive/activated conditions, activated cells preincubated 48 h, then selected HDAC inhibitors 18 h [38]. Five images per well were treated as replicates for aggregation analysis [69]; Fig.5e pictures are n=1, with five pictures used for aggregate-size error bars. Fields are not independent donors/wells; apparent phenotype task expansion would create pseudoreplication. These assays may have decision value, but their distinct cell/timing contract and small compound family must remain explicit.

## Author-linked supplement identities (XML metadata only)

| XML ID | Exact author-linked member | Caption |
|---|---|---|
| MOESM1 | `41587_2024_2218_MOESM1_ESM.pdf` | Reporting Summary |
| MOESM2 | `41587_2024_2218_MOESM2_ESM.xlsx` | Supplementary Tables 1–3 |
| MOESM3 | `41587_2024_2218_MOESM3_ESM.zip` | Supplementary Figs. 1 and 2 |

The local-data XML hrefs authenticate file identities, not an independently retrieved HTTPS response or worksheet contents. Main text [7] links Supplementary Table 1 to drug identity and fitness; it does not prove Table 1 holds complete 144x5 raw functional outcomes. Public data declaration [data availability] gives MassIVE MSV000093659 / PXD047799, ProteomicsDB and Shiny; those locations are source-authenticated, but download inventory and joinability remain unverified.

## Required next evidence and stopping boundaries

1. Inspect workbook identities/sheets/headers only; distinguish per-dose functional measurements from fitted summaries and highest-dose summaries. Never silently turn a curve fit into independent measurement feedback.
2. Establish dose units, assay/time endpoint, drug alias identity, missingness, plate/control IDs, and independent well/biological replicate count. An explicit row join is required for molecular-functional pairing; same drug names alone do not settle dose/time/sample mapping.
3. If raw/normalized per-dose measurements exist, freeze numerical signal qualification before reading values. Signal criterion must distinguish effect sizes and actual endpoint noise; use source-supported repeat uncertainty when available. No universal borrowing of proteomic 19% CV.
4. If only high-dose summaries exist, stop the proposed dose-feedback contract; they may support a different explicitly limited prediction task after separate preregistration. If independent functional noise is unavailable, disclose that limitation rather than manufacture a noise-normalized success gate.
5. Even a useful static dataset cannot establish new laboratory feedback, agent utility, world-model contribution, inheritance, or improved-improver RSI. These remain separate claims and require their own frozen comparisons.

No candidate novelty STOP from the prior phase is reopened by this source review.
