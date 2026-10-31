# Generic-axis transcriptional transfer: pre-registration

Study `generic_axis_transfer_20261031` (GAT). Written 2026-10-31 before any confirmation outcome was read.
The freeze record (`FREEZE.json`) binds this file, the run code and the input files by SHA-256.

## 1. Question and drug-discovery use

A new compound is profiled once by L1000 (978 landmark genes, 10 µM, up to nine core lines at 6 and 24 h).
The maintained virtual-cell module `src/virtual_cell/transcriptional_transfer.py` predicts which cancer
cell lines the compound kills selectively. It averages the viability profiles of the five reference drugs
whose L1000 responses have the highest mean cosine similarity (block N, 2026-10-11, confirmed on 421 sealed
PRISM drugs). The use is indication finding for an unseen compound from one inexpensive profiling assay.

This study asks whether the similarity search improves when the directions shared by many compounds'
transcriptional responses are removed first. A self-supervised encoder was also developed as a learned
alternative; it lost on the development data and is not tested here (section 3).

## 2. Rationale and closest prior work

- Biology: L1000 compound responses share a dominant cell-death/proliferation programme (Szalai et al.,
  Nucleic Acids Res 2019, 47:10010). Mechanistically unrelated cytotoxic compounds then look alike under raw
  cosine, so neighbours are chosen by toxicity strength rather than by what decides selectivity.
- NLP: "all-but-the-top" (Mu and Viswanath, ICLR 2018) removes the common mean and a few dominant directions
  from word embeddings and improves similarity tasks.
- Computer vision: PCA whitening and down-weighting of dominant directions improves image retrieval
  (Jégou and Chum, ECCV 2012).
- Genomics: removing leading factors as unwanted variation (RUV, PEER) is routine. The operation is therefore
  not new. The claim under test is its effect on functional transfer for unseen compounds.
- Self-supervised learning: compound-identity contrastive learning on replicate profiles (Donner et al.,
  Mol Pharm 2018 for L1000; SimCLR/SCARF-style objectives) should learn context-invariant, compound-specific
  directions. Directions every compound shares carry no identity information, so the objective should
  down-weight them without being told which they are.

## 3. What was already seen (disclosure)

All development used exposed data only: the block N PRISM 19Q4 open and sealed tiers (1,403 compounds,
578 lines, opened by block N on 2026-10-11) joined to the block M landmark arrays. On that pool the principal
ran leave-one-out and 10-fold comparisons of raw cosine, centring, removal of the top D directions
(D = 1 to 30), PCA whitening, k = 5, 10, 20, 40, softmax weights, kernel ridge regression and two contrastive
encoders. `DEV_LOG.md` gives every number and the selection rules; scripts and logs are in `dev/`.

- A leave-one-out shortcut for kernel ridge leaked the held-out row through in-sample target centring; its
  apparent r of 0.48–0.64 is void. Kernel ridge was re-run with reference-only centring and fold refits.
- Both encoders (seed 0; variant 2 with cross-line positives, trained transductively on all L1000 compounds'
  signatures but no viability value) lost to generic-axis removal and did not beat raw cosine at matched k
  (best case: variant 2 at k = 5, +0.001 [−0.010, +0.012]; below raw cosine at k = 10 to 40). The encoder arm
  and its hypotheses were withdrawn before the freeze.
- One development run (`dev5.py`) stopped at its own timeout after 7 of 10 folds; its partial output was not
  used.
- The run code was smoke-tested on fake confirmation sets drawn from the development pool
  (`dev/make_smoke.py`, `dev/smoke_RESULTS.json`).

No NCI-60 or PRISM 24Q2 outcome has been related to any L1000 input. Before the freeze the principal read:
NCI-60 file headers; line counts per compound; the sign of CellMiner z-scores against −log10 GI50 on 300
compounds outside the test set (median r 1.0, so higher z means more sensitive); the 24Q2 metadata files and
README. The confirmation-1 input file `nci60.npz` was built before the freeze to fix it by hash. Only its
census was read: 419 compounds, 293 active. No arm was run on it. No 24Q2 response value has been downloaded.

## 4. Data

### Development pool (exposed; used only for choices above and for training-free directions in confirmation 2)

PRISM Repurposing 19Q4 primary screen, log2 fold change at 2.5 µM over 5 days, 578 lines (block N tiers), with
block M landmark signatures (mean level-5 MODZ z-scores at 10 µM per core line × time).

### Confirmation 1: NCI-60 (external; never used in this programme)

- Outcome: CellMiner 2.15 (2025-09-17) `DTP_NCI60_ZSCORE.xlsx`, compound activity z-scores over 60 lines
  (−log10 GI50 based; higher means more sensitive). SHA-256 of the downloaded archives is in `FREEZE.json`.
- Compound identity: InChIKey connectivity block (first 14 characters) computed by RDKit from the CellMiner
  SMILES. Profiles of NSC numbers sharing a key are averaged line by line.
- Inputs: GSE92742 level-5 landmark signatures at 10 µM, nine core lines × 6/24 h, every LINCS `trt_cp`
  `pert_id` whose `inchi_key_prefix` equals the key, mean per option (extractor validated against block M:
  identical values for 117 of 120 random block M compounds; the other 3 gain extra salt forms).
- Inclusion: at least 50 of 60 lines with a z-score and at least one measured L1000 option.
- Activity: a line is killed when the mean −log10 GI50 over experiments without a failure reason is at least
  5.60 (GI50 ≤ 2.5 µM, the PRISM dose). A compound is active when at least 3 lines (5%) are killed.
  For keys with several NSC numbers, experiments of all of them are pooled.
- Folds: 10 folds by SHA-256 of the key, modulo 10. References for a query are the included compounds in the
  other nine folds.

### Confirmation 2: PRISM Repurposing 24Q2 extension (sealed; same platform)

- Outcome: `Repurposing_Public_24Q2_Extended_Primary_Data_Matrix.csv` (figshare 25917643, file 46630984,
  MD5 042b15d3ebcc138a80a571b9286451ae), downloaded after the freeze into its own directory
  `data/external/prism_24q2_20261031/matrix/`. Only rows of the query compounds are parsed; the count of parsed
  rows is recorded. Values are collapsed log2 fold changes at 2.5 µM.
- Queries: the 1,229 eligible REP.1M compounds sealed on 2026-10-13
  (`log/research_records/knowledge_reality_20261013/sealed_compounds.csv`) that have at least one measured
  L1000 option (101 by the pre-freeze input census). Row choice: matrix rows whose `IDs` are listed with screen
  `REP.1M` in the release's compound list and whose Broad ID core equals the query's; if several, their values
  are averaged. Rows from the 19Q4 primary screen (`REP.PRIMARY`) are never used: three sealed compounds also
  have one, and none of them has an L1000 signature.
- A query whose InChIKey connectivity block equals that of a development-pool compound is dropped and listed.
- References: the 1,403-compound development pool with its 19Q4 profiles and block M signatures.
- Lines: the lines present in both the 19Q4 pool and the 24Q2 matrix.
- Activity: at least 5% of the evaluated lines have LFC ≤ −1; a missing value counts as not ≤ −1 (the same
  rule defined the development actives).

## 5. Arms

All arms predict a query profile as the clipped-similarity-weighted mean of the k reference profiles with the
highest similarity, skipping missing reference values (the maintained `transfer_profile` rule), unless stated.

| Arm | Similarity | k |
|---|---|---|
| B0 promoted | raw mean cosine over shared options | 5 |
| B1 neighbours only | raw mean cosine | K |
| B2 chemistry | Morgan radius-2 2,048-bit Tanimoto | K |
| C1 generic-axis removal | per option: centre on the reference mean, remove the top D principal directions of the references' signatures, mean cosine | K |
| Z zero arm | no selective prediction | – |
| L leakage control | C1 with reference profiles permuted among references (seed 20261031) | K |

D = 5 and K = 20 were fixed from development by the rule in `DEV_LOG.md` section 8. Principal directions
are recomputed on the references of each fold (confirmation 1) or on the development pool (confirmation 2).
The contrastive-encoder arm (C2) was withdrawn before the freeze (section 3).

## 6. Endpoints

Generic profile G: the mean profile of the references (per fold for confirmation 1; the development pool for
confirmation 2).

- Primary: selective r per query, the Pearson correlation between predicted and observed profiles after each is
  residualised on G (the maintained `selective_r`; minimum 40 shared lines for NCI-60, 50 for PRISM). The
  primary population is active queries. Undefined r counts as 0 for every arm.
- Secondary: selective hit precision. True hits are the 10% of evaluated lines with the highest observed
  sensitivity residual (−LFC residual for PRISM, z residual for NCI-60); predicted hits are the 10% with the
  highest predicted sensitivity residual. Precision is the shared fraction. Zero arm: 0.10.
- Reported, not tested: all-compound means; inactive-compound means.

## 7. Hypotheses, tests and decisions

One-sided paired t-tests on per-compound differences in the primary endpoint; Holm correction across
H1 and H3 within each confirmation set at family-wise α = 0.05. Percentile bootstrap 95% intervals (10,000
compound resamples, seed 20261031) are reported for every difference.

- H1: C1 > B0.
- H3: C1 > B1 (removal adds beyond the neighbour count).
- H2 and H4 (the encoder) were withdrawn before the freeze; the labels are kept so that earlier drafts map.
- Context, not in the family: C1 vs B2, B1 vs B0, every arm vs Z, the leakage control.
- Secondary endpoint: the same contrasts on selective hit precision, reported without a decision.

Verdicts per hypothesis:

- REPLICATED: Holm-significant on both sets.
- CONFIRMED: Holm-significant on NCI-60 and the 24Q2 point estimate is positive.
- NOT_CONFIRMED: otherwise.
- Leakage control: the run is INVALID, and nothing is interpreted, if in either set the mean primary r of L on
  actives is further than 0.03 from 0 and a two-sided one-sample t-test against 0 gives p < 0.01. (A plain
  ±0.03 band would be about 2 standard errors on the expected 40–60 24Q2 actives, so noise alone would void
  about one run in twenty.)

## 8. Promotion rule

- C1 is promoted as an option of `transcriptional_transfer` if H1 is CONFIRMED or REPLICATED and the 24Q2
  point estimate of C1 − B1 is not negative, and only after the independent verification (section 9) passes.
- Default behaviour of the maintained function stays unchanged. The new option carries its validated scope.
- If H1 holds but H3 does not, the report says the gain cannot be separated from using more neighbours.

## 9. Independent verification

A separate agent with a fresh context receives this protocol, the frozen input files and the saved
per-compound predictions, but not the run code. It must:

1. Recompute every primary and secondary number from the saved predictions and the raw outcome files.
2. Re-implement B0 and C1 from section 5 alone on confirmation 1 and reproduce their per-compound predictions.
3. Independently re-derive the NCI-60 inclusion and activity flags.
4. Check the MD5 of the 24Q2 matrix and re-derive the 24Q2 query rows, lines and activity flags from it.

A discrepancy larger than 1e-6 in any prediction, per-compound statistic, mean, t statistic or p-value voids
promotion until explained. Bootstrap intervals are recomputed with the verifier's own resampling and must
agree within 0.005.

## 10. Budget and costs

No paid API, no LLM call, no wet-lab cost. Downloads: CellMiner NCI-60 archives (8.5 MB + 21.4 MB), 24Q2
metadata (2.4 MB) and the 24Q2 outcome matrix (72.5 MB). Compute on the local workstation; the two
development encoders used its GPU for about four minutes each.

## 11. Deviations

Any change after the freeze is appended to `DEVIATIONS.md` with time and reason. The frozen version stays
authoritative for the verdict.
