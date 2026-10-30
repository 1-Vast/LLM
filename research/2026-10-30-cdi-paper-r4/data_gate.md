# Data gate — 2026-10-30 paper-informed CDI revision

## Decision

`data_unavailable` for one public, analysis-ready table containing the same
cell × drug × dose × time rows with cellular target engagement, CRISPR/GeneEffect
reference, orthogonal function and independent preparation identity.

## Closest usable public stack

* **PRISM Repurposing 24Q2**, Figshare article 25917643,
  DOI `10.6084/m9.figshare.25917643.v1`: replicate-level viability, explicit
  `depmap_id`, dose in µM, five-day endpoint and triplicate plates. The release
  is mainly a 2.5 µM single-dose screen. FLT3 compounds are annotated, but
  `repurposing_target`/MOA is not measured engagement.
* **PRISM 20Q2 secondary screen**, Figshare article 20564034,
  DOI `10.6084/m9.figshare.20564034.v1`: eight-step four-fold dilution from
  10 µM, replicate metadata and viability dose-response fits. MTS010 is kept
  as a separate technical redo.
* **DepMap Chronos/GeneEffect 26Q1**, Figshare article 31660582,
  DOI `10.6084/m9.figshare.31660582.v2`: gene-effect matrices for a genetic
  reference, joinable through model IDs. This is not drug engagement and has no
  drug dose/time.
* **PXD047949**, DOI `10.1016/j.mcpro.2025.100963`: public live-Jurkat
  probe/kinobead target-engagement curves for selected kinase inhibitors,
  short exposure and biological repeats, but no FLT3/PRISM crosswalk or matched
  viability dose/time.
* **LT-171-861 FLT3 CETSA**, DOI `10.7150/thno.46593`: MV4-11 engagement,
  short-exposure CETSA, phospho readouts and 72-hour MTT in a few lines. It is
  a mechanistic exemplar, not a broad machine-readable PRISM/DepMap panel.

## Missing fields and access limits

No inspected source simultaneously supplies exact structure/pair identity,
cell barcode, dose, exposure time, cellular engagement, perturbation status,
orthogonal function, and independent preparation. Current DepMap portal pages
returned Cloudflare verification; official Figshare releases were used instead.
CancerRxGene page access failed, but this is not treated as global data absence.
Large PRIDE raw files were not downloaded.

## Bounded metadata acquisition

Within a five-file, 50 MB metadata budget, the coordinator downloaded the PRISM
24Q2 README, cell-line metadata, extended compound list and treatment metadata,
plus the small DepMap 26Q1 replicate-efficacy table. The README gives a
screen-level 2.5 µM, five-day treatment and triplicate plates. The treatment
table has 11,502 unique profiles, dose values 2.487/2.5 µM and replicate codes
X1/X2/X3; every `profile_id` contains the raw `120H` token, but the token is not
a separate structured exposure field.

The extended compound annotations contain 35 rows whose target string includes
FLT3 (41 if MOA-only matches are also counted). After normalizing the `BRD:`
prefix, only two of those annotated IDs joined exactly to treatment metadata;
name search found `FLT3-IN-1`, `SKLB-1028` and `URMC-099`. These are identity
observations only. They do not establish FLT3 engagement, and they do not yield
the matched target-perturbation or orthogonal-function contract. The exact
census and hashes are in `raw/resource_metadata/census.json`; the manifest
records the five downloaded data files separately from the generated API and
census snapshots.

### Genetic-reference check (completed under a separate budget)

To test whether a genetic reference changes the retrospective FLT3 result, the
official 26Q1 `gene_effect.csv` was streamed under a fixed 500 MB network and
10-minute budget. The source transfer was 413,544,937 bytes with the advertised
MD5; only the `FLT3 (2322)` row and model identifiers were retained. Exact
`DepMap_ID` matching to the existing PRISM 19Q4/MTS010 pair table gave 409,428
rows, 395 cells, 153 pairs and eight doses. The dependency-tertile interaction
correlation with `delta_pKd` was `rho = 0.0717`, versus `rho = 0.0601` for the
earlier expression-tertile contrast; direct repeated-row correlation was
`rho = -0.0056`. The check is descriptive and cross-release. Chronos is a
genetic dependency inference, not target occupancy, and this result neither
establishes nor rules out target mediation.

### Engagement overlap search (completed)

CellEKT (2025, DOI `10.1016/j.mcpro.2025.100961`) is the strongest near-overlap:
MV4-11 and HEK293T, midostaurin-FLT3 cellular probe competition, 0.1–10,000 nM,
one-hour inhibitor exposure, and two biological replicates per concentration.
The live-cell kinase probe study (2025, DOI `10.1016/j.mcpro.2025.100963`)
provides a Jurkat/dasatinib near-overlap with 60–90 minute exposure and mostly
duplicate measurements. Neither source has a verified PRISM/DepMap/GDSC cell
barcode and same-row dose-time crosswalk, so both remain assay templates rather
than matched validation. The full audit is in
`target_engagement_overlap_search.md`.

## Permitted next step

Freeze a PRISM 24Q2 + DepMap GeneEffect identity/replicate ledger and run a
masked predictive replay only if needed to test split discipline and equal-cost
selection. Do not call that replay target mediation or Agent savings. A
positive CDI mechanism requires a targeted matched cellular-engagement or
perturbation panel at the same inhibitor concentrations and a separate function
endpoint.
