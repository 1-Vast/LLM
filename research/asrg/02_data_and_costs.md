# ASRG data and three-cost matrix

Three costs are kept separate for every asset, because "cheap" is ambiguous:

- **C1 access and preprocess**: download, licence compliance, and the work to reach the
  analysis-ready table.
- **C2 train and run**: fitting the effect coordinates and the cheap predictor, and running
  selection.
- **C3 deployment inputs per new candidate**: what must exist *before* a genuinely new
  candidate can be scored. This is the cost that decides whether the method is usable.

Network policy in this container blocked zenodo.org, api.figshare.com, huggingface.co,
ncbi.nlm.nih.gov, arxiv.org, openreview.net and pmc.ncbi.nlm.nih.gov, so **no file size or
checksum below was verified here**. Sizes marked (index) come from search indexes.

## 1. Primary pilot: SciPlex3

| Field | Value | Status |
|---|---|---|
| Source | Srivatsan et al., *Massively multiplex chemical transcriptomics at single-cell resolution*, Science 367(6473):45–51, 2020, [doi:10.1126/science.aax6234](https://doi.org/10.1126/science.aax6234) | verified |
| Design | 3 cancer lines (A549, K562, MCF7), 188 compounds, ~650,000 cells, ~5,000 samples | verified |
| Doses and time | Reported as four doses in a single treatment window; the repository protocol pins one `time_hours` | **unverified here** — confirm from the rebuilt table, not from memory |
| Harmonised copy | [scPerturb](https://doi.org/10.1038/s41592-023-02144-y) (Peidli et al., Nature Methods 21:531–540, 2024), Zenodo record 13350497, v1.4, CC-BY; v1.4 "corrects errors in SrivatsanTrapnell2020_sciplex3" | verified via index; record page blocked |
| Size | A mirrored copy is listed at 799,317 observations / 12.2 GB (index) | **unverified** |
| Alternative copy | Figshare file 43381398 / article 24681285, with MD5 `d1f51b9f8de35ca07638132539da9a99` recorded in `dataset/README.md` | document-only |

**C1** One `.h5ad` download in the ~10 GB class, plus a pseudobulk rebuild. The repository's
existing `prepare` step already streams the matrix in 4,096-row blocks, selects the top 2,000
training-expressed human ENSG features, and aggregates per
context × compound × dose × time × replicate × plate, refusing any condition with no
plate-matched control (source-verified in `src/evaluation/model_validation.py`). Bounded RAM
by construction; wall time not measured here.

**C2** Training-fold SVD plus ridge and a small dose-anchored MLP ensemble. The repository
already runs this design on CPU or CUDA. No foundation model, no fine-tuning.

**C3 (the important column)** For a new candidate: canonical SMILES or simple descriptors,
registered dose, time, cell background, and the plate-matched control pseudobulk of that
context. For the anchored variant, one existing measured response for the *current* action
`a0` in that context — which a repair situation already has. **No treated RNA from the new
candidate.** This is what makes the method deployable and what separates it from the
registered State backend, which needs the candidate's own measured rows to exist.

**Leakage guards required**

- Split by molecular identity, and additionally by Bemis–Murcko scaffold for any
  held-out-chemistry claim. The existing split hashes SMILES only, which keeps all doses of
  one compound together but does not separate analogues.
- Fit gene selection, coordinates, predictor, κ and conformal bands on training folds only.
  The existing pipeline already restricts gene ranking and the SVD to training rows.
- Keep the goal independent of the candidate's own hidden outcome.

## 2. External validation branch (one, after the pilot)

### 2.1 LINCS Cell Painting — preferred

| Field | Value | Status |
|---|---|---|
| Repository | [broadinstitute/lincs-cell-painting](https://github.com/broadinstitute/lincs-cell-painting) | verified |
| Design | A549; 1,571 compounds across 6 doses in 5 technical replicates; two sets of ~136 and ~135 384-well plates | verified |
| Doses | 0.04, 0.12, 0.37, 1.11, 3.33, 10 µM (from the paired-assay repository) | verified |
| Time | 48 h, evident in batch names such as `2016_04_01_a549_48hr_batch1` | verified |
| Levels | Level 3–5 profiles in `profiles/`, consensus as `.csv.gz` via git-lfs | verified |
| Licence | Code BSD 3-Clause; data, results and figures CC0 1.0 | verified |
| Paired assay study | Way et al., Cell Systems, 2022, [S2405-4712(22)00402-1](https://www.cell.com/cell-systems/fulltext/S2405-4712(22)00402-1): 1,327 shared compounds; Cell Painting more reproducible and more diverse, but fewer distinct feature groups | verified |

**C1** Moderate: processed profiles only, no images. **C2** Low. **C3** Same as the pilot.

**Critical preprocessing caveat (verified):** per-plate normalisation uses `mad_robustize`
against either the whole plate or DMSO wells, but **spherizing is fitted on the full batch,
all plates**. The released spherized profiles therefore saw the test compounds. Any strict
inductive split must refit normalisation and feature selection on training compounds only.
A published processed feature table is not intrinsically cheap or intrinsically clean.

**Do not pool with SciPlex3 by compound name.** Different cell line (A549 vs three lines),
different modality (morphology vs transcriptome), different window (48 h vs the pilot's), and
different measurement semantics. Treat it as a separately conditioned branch that tests
whether the *decision rule* transfers, never as paired ground truth.

### 2.2 L1000 — alternative

Subramanian et al., Cell 171(6):1437–1452, 2017,
[doi:10.1016/j.cell.2017.10.049](https://doi.org/10.1016/j.cell.2017.10.049): 978 measured
landmark transcripts, ~11,350 **inferred** genes, 12,328 total; GSE92742 Level 5 is
473,647 × 12,328 (verified via index; GEO page blocked, sizes unverified).

Use landmark genes only. Inferred genes are model outputs; scoring a predictor against them
partly scores the L1000 inference model. Lineage: the Connectivity Map idea itself
([Lamb et al., Science 2006](https://www.science.org/doi/10.1126/science.1132939)) is the
nearest-signature baseline ASRG must beat.

### 2.3 Considered and set aside for stage 1

| Asset | Why not now |
|---|---|
| [Tahoe-100M](https://www.biorxiv.org/content/10.1101/2025.02.20.639398v1) — 50 lines, 379 agents, 1,135 drug-dose conditions, CC0 (index) | Same modality and attractive scale, but State was trained on it, so it cannot validate the registered backend. Keep as a fallback for the *cheap* predictor only, after checking compound overlap with the pilot |
| [JUMP cpg0016](https://doi.org/10.1101/2023.03.23.534023) — 116,000+ compounds, U2OS, >250 TB total (index) | C1 far outside the brief; single main dose and a different cell background |
| New single-cell sequencing, phosphoproteomics, occupancy assays, raw-image modelling | Excluded by the brief for stage 1 |

## 3. Optional later biological checks

Only after the pilot and the external branch:

1. Existing public protein or functional readouts **in their own matched contexts**, never
   re-labelled onto the pilot's conditions.
2. Then one small prespecified assay: viability or cell count, basic microscopy, or a small
   fixed gene panel, in the same context, time and dose as the selected action.

None of these establishes target occupancy. A mechanism claim needs orthogonal functional,
genetic or rescue evidence, which is outside this stage by design.

## 4. Compute and cost honesty

No pilot run was executed for this report, so no hardware-hour figure is offered. The only
timings measured in this session are software microbenchmarks of the agent loop, which say
nothing about data processing. Gate G1 must report measured wall time, peak memory and output
sizes from the actual rebuild before any efficiency claim is made.

Provider and laboratory costs stay in separate ledgers, as the repository already enforces:
`evaluation/lab_cost.py` prices wells and turnaround days and charges a shared control once,
while `evaluation/provider_spend.py` reserves and charges API spend.
