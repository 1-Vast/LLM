# Generic-axis transcriptional transfer (GAT): report

Study `generic_axis_transfer_20261031`. Pre-registered in `PROTOCOL.md`, frozen 2026-10-31T04:53:24Z
(`FREEZE.json`), run once 04:54–04:59Z. Development record: `DEV_LOG.md`.

**Verdict.** H1 CONFIRMED and H3 CONFIRMED by the pre-registered rule: Holm-significant on NCI-60, with a
positive but non-significant point estimate on PRISM 24Q2. An independent verifier that never saw the run code
re-derived every number: PASS, 139 of 139 checks (`VERIFY/`). The generic-axis option was promoted to the
maintained module; its default behaviour is unchanged. Post-freeze disclosures are in `DEVIATIONS.md`.

## 1. Question

The maintained virtual cell (`src/virtual_cell/transcriptional_transfer.py`) predicts which cancer cell lines an
unseen compound kills selectively. It transfers the viability profiles of the five reference drugs whose L1000
responses are most similar by cosine. Many compounds share a few dominant transcriptional directions, largely a
cell-death and proliferation programme, so raw cosine pairs mechanistically unrelated cytotoxic drugs. The study
asked whether removing those directions before the similarity search transfers selectivity better, on data
never used in this programme.

## 2. Design

- Similarity source: GSE92742 level-5 landmark signatures, 10 µM, nine core lines × 6/24 h.
- C1: per condition, centre on the reference mean and remove the top D = 5 principal directions of the
  references' signatures, then mean cosine and the maintained transfer rule with k = 20. D and k were fixed
  on the exposed PRISM 19Q4 pool by a rule written before the deciding grid was read.
- Baselines: B0 the promoted rule (raw cosine, k = 5); B1 raw cosine, k = 20; B2 Morgan fingerprint
  similarity, k = 20; Z zero arm; L leakage control (C1 with permuted reference profiles).
- Confirmation 1, NCI-60 (CellMiner GI50 z-scores, 60 lines, a different assay and panel): 419 compounds with
  L1000 signatures, 293 active; ten folds by key hash; references from the other nine folds.
- Confirmation 2, PRISM Repurposing 24Q2 REP.1M (sealed since 2026-10-13): 101 new compounds with L1000
  signatures, 32 active, 568 lines; references are the 1,403-compound 19Q4 development pool.
- Primary: selective r on active compounds (Pearson r between predicted and observed profiles after removing
  the generic profile from each). Secondary: top-10% selective hit precision.

## 3. Results

Primary endpoint, mean selective r on actives:

| Arm | NCI-60 (293) | PRISM 24Q2 (32) |
|---|---|---|
| B0 promoted (raw, k = 5) | 0.3645 | 0.0988 |
| B1 raw, k = 20 | 0.3595 | 0.0952 |
| B2 chemistry, k = 20 | 0.3318 | 0.0751 |
| **C1 generic axes removed, k = 20** | **0.4053** | **0.1134** |
| L leakage control | 0.0137 | −0.0116 |
| Z zero arm | 0 | 0 |

Paired differences (bootstrap 95% interval; one-sided paired t-test; Holm over H1 and H3 within each set):

| Contrast | NCI-60 | PRISM 24Q2 |
|---|---|---|
| H1: C1 − B0 | +0.0409 [+0.0227, +0.0591], p = 7.5e-6, Holm reject | +0.0146 [−0.0083, +0.0369], p = 0.11 |
| H3: C1 − B1 | +0.0459 [+0.0291, +0.0635], p = 1.1e-7, Holm reject | +0.0182 [−0.0016, +0.0390], p = 0.046, not Holm |
| C1 − B2 (context) | +0.0736 [+0.0393, +0.1077] | +0.0383 [+0.0020, +0.0752] |
| B1 − B0 (context) | −0.0050 [−0.0229, +0.0137] | −0.0036 [−0.0277, +0.0200] |

- More neighbours alone did not help (B1 − B0 ≈ 0 in both sets), so the gain comes from the removal, not k.
- Leakage controls are null in both sets (p = 0.24 and 0.26), so the run is valid.
- Inactive compounds also gained on NCI-60 (C1 0.150 vs B0 0.101; reported, not tested).
- Secondary, top-10% selective hit precision on actives: NCI-60 C1 0.289 vs B0 0.280 (+0.009 [−0.011,
  +0.029]); PRISM 24Q2 0.158 vs 0.152 (+0.007 [−0.010, +0.025]). Chance is about 0.12, the permuted-reference
  arm L, not the protocol's nominal 0.10. **The correlation gain did not become a significant gain in picking
  the most sensitive lines.**
- The predictive arms B0, B1, B2 and C1 beat the zero arm on both sets (`VERIFY/check1_stats.json`); this excludes the leakage control L, whose PRISM mean is negative. On new PRISM compounds the transfer
  itself carries real selective signal: C1 0.113 [0.075, 0.154], B0 0.099 [0.058, 0.143].

### Post hoc (exploratory, after the run; not part of the verdict; `POSTHOC/`)

Sensitivity to the number of removed directions, mean selective r on actives (k = 20):

| Directions removed | 0 (centring only) | 1 | 3 | 5 (frozen) | 10 | 20 |
|---|---|---|---|---|---|---|
| NCI-60 | 0.373 | 0.397 | 0.408 | 0.405 | 0.392 | 0.373 |
| PRISM 24Q2 | 0.098 | 0.102 | 0.108 | 0.113 | 0.119 | 0.119 |

- Centring alone does nothing (NCI-60 +0.008 [−0.010, +0.027] over B0). The gain needs the directions removed.
- On NCI-60 (about 377 references per fold) every D from 1 to 10 beats B0 with an interval above 0; D = 20 does
  not. On PRISM (1,403 references) the estimate rises up to D = 10, though no setting is significant with 32
  actives. Larger reference sets seem to tolerate more removed directions. That is a hypothesis, not a result.

Neighbour mechanism (actives; generic fraction = share of a signature's centred energy in the top 5 reference
directions):

| | NCI-60 | PRISM 24Q2 |
|---|---|---|
| Neighbours' generic fraction minus the query's, raw cosine k = 20 | +0.061 [+0.050, +0.072] | +0.066 [+0.038, +0.093] |
| Same after removal (C1) | +0.013 [+0.002, +0.024] | +0.035 [+0.010, +0.059] |
| Top-20 neighbours shared between raw cosine and C1 | 56% | 53% |
| C1 − B1, lowest third of query generic fraction | +0.046 [+0.016, +0.074] | −0.009 [−0.045, +0.023] |
| C1 − B1, middle third | +0.019 [−0.004, +0.042] | +0.026 [+0.010, +0.042] |
| C1 − B1, highest third | +0.073 [+0.039, +0.106] | +0.038 [+0.000, +0.082] |

## 4. Development negatives (exposed data only; details in `DEV_LOG.md`)

- Two compound-identity contrastive encoders (SimCLR/SCARF-style; the second with positives forced across
  different cell lines and trained on all 7,707 multi-line L1000 compounds) lost to training-free removal by
  0.032–0.048 and never beat raw cosine at matched k. The learned representation did not find what a
  five-direction projection finds.
- Kernel ridge on the similarity kernel, with honest fold refits, added +0.006 [−0.000, +0.013] over removal and
  kNN. A leave-one-out shortcut with in-sample target centring had leaked the held-out row (apparent r 0.48–0.64);
  that number is void.
- PCA whitening (50 or 100 components) and softmax weights were worse than removal with clipped weights.
- Removing 10 directions was slightly better than 5 in development (0.2415 vs 0.2366); the pre-written rule chose
  5. Removing 30 directions was worse than 5.

## 5. Operational boundaries

Validated:
- GSE92742 landmark signatures at 10 µM in the nine core lines at 6 and 24 h (1–18 measured conditions per
  compound; median 14 for NCI-60, 15 for 24Q2).
- Directions fitted on the reference set itself, from 32 to 407 references per condition (NCI-60 folds) and from
  43 to 1,403 (PRISM pool).
- Selective profiles in the references' own assay: NCI-60 GI50 z-scores (within-panel transfer), and PRISM 19Q4
  references predicting PRISM 24Q2 compounds.
- The configuration 5 directions, k = 20.

Not shown:
- Significance on PRISM 24Q2. With 32 actives (standard deviation of the paired difference 0.065), 80% power
  at one-sided α = 0.025 needs a true difference of about 0.032; detecting the observed +0.015 would need about
  150 actives.
- A gain in top-10% hit selection on either set, so decision value for choosing which lines to test is
  unproven.
- The trust score (top similarity) on the new scale; other transcriptomic platforms (later L1000 releases,
  RNA-seq), other doses or cell types; organoids, primary cells or in vivo response.
- Absolute accuracy remains modest for new PRISM compounds (selective r about 0.11, against a 19Q4
  replicate ceiling of about 0.30 for the exposed pool).

## 6. Interpretation

Raw cosine retrieves references whose responses are more dominated by the shared programme than the query's
own response. In development, the most similar pairs under raw cosine were global transcriptional shutdown
compounds (alvocidib with doxorubicin, triptolide, AT-7519) whose selective profiles barely agree. On both
confirmation sets the raw neighbours carry about 0.06 more generic fraction than the query, and removal cuts
that excess to 0.01–0.035. Almost half the neighbours change. The gain is largest for the queries whose own
response is most generic, as the mechanism predicts. On NCI-60 it is also positive for the least generic third,
so it is not confined to strong cytotoxics.

Active compounds carry more generic signal than inactive ones (0.269 vs 0.239 on NCI-60). This is consistent
with the shared directions being dominated by cell death and proliferation, but the study did not test the
directions' biological identity.

Relation to the 2025 literature, added after the run (not cited in the frozen protocol): Systema (Viñas Torné et
al., Nature Biotechnology 2025, doi 10.1038/s41587-025-02777-8) showed that systematic variation shared by
perturbations inflates the evaluation of genetic perturbation-response models. This study's endpoint guards
against the same effect on the outcome side (selective r removes the generic profile). C1 removes it on the
input side, where it was misdirecting analogue retrieval. The operation itself is old: all-but-the-top in NLP,
PCA whitening in retrieval, RUV/PEER in genomics. What this study observed is an incremental effect on functional
transfer for its held-out compounds; this does not establish standalone novelty or a Virtual Cell core innovation.
The two learned contrastive encoders also did not find a better space in the exposed development comparisons.

## 7. Independent verification

A fresh-context agent received the protocol, the frozen inputs, the raw outcome files and the saved
predictions, but not the run code. Its verdict was **PASS, 139 of 139 checks**:
- It re-derived the observed profiles, the NCI-60 inclusion, folds and activity, and the 24Q2 rows, lines and
  activity from the raw files. All reproduce exactly.
- It re-implemented all five arms. Predictions match to 8.4e-15.
- Per-compound statistics, means, t statistics and p-values match to 2e-15. Its own bootstrap intervals agree
  within 0.0016.
- No frozen file changed after the freeze. The 24Q2 matrix was written 24.6 s after it.

It found one undescribed pre-freeze rule: one Broad ID kept per InChIKey block. That rule left out one eligible
24Q2 compound. Reading that compound's row afterwards showed it is inactive, so the primary population and every
verdict are unchanged (`DEVIATIONS.md` section 1). It also listed seven protocol details that the
implementation had to choose; none changes a verdict. Its report is `VERIFY/REPORT.md`, saved verbatim by the
principal because subagents cannot write report files.

## 8. Promotion

The pre-registered rule required three things: H1 CONFIRMED, a 24Q2 C1 − B1 point estimate that is not
negative, and a verification pass. All three hold.

`src/virtual_cell/transcriptional_transfer.py` gains:
- `fit_generic_axes(references, n_axes=5)`, which returns `GenericAxes`;
- `remove_generic_axes`;
- an optional `generic_axes=` argument to `transfer_profile`.

Calls without it behave exactly as before.

The result's `scope` names the validated configuration: `GENERIC_AXES_SCOPE` for 5 axes with k = 20, and
`UNVALIDATED_SCOPE` for any other choice. The docstring states the evidence and what was not shown. For speed,
only the query's measured conditions are cleaned; similarity is identical, because unmeasured conditions never
contribute.

Checks:
- `POSTHOC/promotion_check.py` runs the maintained module on both confirmation sets. It reproduces the run's
  B0 and C1 predictions to 1.8e-15, with the expected scope tags.
- Four new contract tests:
  - the axes recover a planted shared direction;
  - removal finds the compound-specific neighbour that raw cosine misses;
  - unmeasured conditions are skipped;
  - the scope tags and mismatch refusal work.
- `tests/virtual_cell` and the repository shape test pass.

Not promoted: the encoders, kernel ridge and any agent component. The trust score of the new option is
untested.

## 9. Files

- `PROTOCOL.md`, `DEV_LOG.md`, `FREEZE.json`: pre-registration, development record and freeze.
- `gat_core.py`, `gat_data.py`, `gat_run.py`, `gat_freeze.py`: study code. `dev/`: development scripts and logs.
- `RUN/`: the one confirmatory run (`RESULTS.json`, per-compound metrics and predictions).
- `VERIFY/`: the independent verifier's code, `VERIFICATION.json` and `REPORT.md`.
- `DEVIATIONS.md`: post-freeze disclosures. `POSTHOC/`: exploratory analyses and the promotion check.
- Not in git: the eight `.npz` payloads in `RUN/` and `VERIFY/` (predictions and the verifier's derived arrays)
  stay local with the inputs, under the repository's storage policy. `RUN/metrics_*.csv` keep every per-compound
  value the statistics use.
- Inputs: `data/processed/generic_axis_transfer_20261031/` (hashed in `FREEZE.json`); the 24Q2 matrix in
  `data/external/prism_24q2_20261031/matrix/` (MD5 042b15d3ebcc138a80a571b9286451ae, downloaded after the
  freeze).
