# Development log (pre-freeze; 2.5 uM reads only)

All entries 2026-10-19, before `FREEZE.json`. Development used only the HTS002 2.5 uM reads, which the RSD study
(`../replicate_decisions_20261019`) had already opened in every block. No 0.625 or 10 uM read value was loaded before the
freeze: `ht_data.guard` refuses those doses while `FREEZE.json` is absent (`test_ht.py::test_test_doses_refused_before_freeze`),
and `freeze.py` refuses to run if a test-dose read cache exists.

1. **Metadata check (no read values).** HTS002 treatment metadata: 1,309 cores have an X1-X3 triple at 0.625 uM, 1,288 at
   2.5 uM, 1,282 at 10 uM; every triple column exists in the log-fold-change header (header row only).
2. **Arena reuse.** Compounds, roles, purges and replicate-role permutation come from the frozen `rsd_data` (imported, not
   modified). The dose-parameterised loader (`ht_data.load_reads`) reproduces the frozen 2.5 uM A, B, T arrays and the
   frozen search-block query/reference sets exactly (`test_dev_dose_reads_equal_frozen_reads`). It writes its cache into
   this folder only.
3. **Quadrature defect fixed before any use.** The first Student-t quadrature (40-node generalised Gauss-Laguerre) missed
   the extreme tail at nu = 2 (CDF error 0.0024 at |e| = 12; unit test failed). Replaced by a trapezoid rule on a
   quantile-bounded log-lambda grid (160 nodes); the difference-of-t mixture merges the 160 x 160 products on 400 log
   variance bins. Unit tests: t CDF within 2e-3 for nu in {2, 3, 4, 10, 20}; difference density within 0.01 of a
   400,000-draw simulation; simulated nu = 4, s = 0.8 recovered.
4. **Gaussian limit.** With nu = inf and s = 1 the factor-form VB posterior equals the frozen `VirtualCell.posterior`
   (rho = 0) to 1e-8 in mean and variance (`test_gaussian_limit_reproduces_frozen_posterior`); the recording subclass
   `FactorVC` leaves S0 and N0 bit-identical.
5. **Development run v1 on the 2.5 uM search block** (`dev/v1_2p5uM_search.json`; pair-level Student-t, the first design).
   The code hashes stored in that record were computed when the record was written, after two edits that touch only the
   evaluation stage (a `started_utc` timestamp and code hashing at launch); `run_block` was unchanged. Readout:
   * The frozen arm reproduces SEARCH_v2 (inner choice q = 3, rho = 0, prior off; `rsd - raw` D1 +0.081, D2 +0.023;
     selected-pair coverage 0.714). `gauss_rho0` equals `rsd` to 3e-14.
   * Standardised reference differences: excess kurtosis 1.21 after line and tier scaling (3.2 unscaled in RSD's
     diagnosis); pair-level t ML nu = 5.3 (log-likelihood -1.405 vs Gaussian -1.419 per observation).
   * The reference-only utility increases monotonically with nu (2: -0.027 ... 20: +0.070); selected nu = 20.
   * `ht - rsd`: D1 -0.022 [-0.043, -0.004], D2 -0.014 [-0.024, -0.005]; `ht_fit` (nu 5.3) worse (D1 -0.074, D2 -0.035).
     Selected-pair coverage 0.711 (rsd 0.714). Mean E[lam] on selected pairs 0.95.
   * Reading: downweighting isolated extreme pairs discards real line-specific hits as often as outliers. The pair-level
     model, as first designed, does not repair D2 on the development data.
6. **Noise anatomy (2.5 uM, evaluation-block references only; `dev_noise_anatomy.py`).** First run
   (`dev/noise_anatomy.json`) had NaN summaries because 76 of 356 references have fewer than 100 finite lines (division by
   zero rows); the likelihood fits in it were valid. Rerun as `dev/noise_anatomy_v2.json` on the 280 references with at
   least 100 lines:
   * Per-compound mean z^2 has SD 0.39 against 0.08 expected for homogeneous Gaussian noise (5%-95%: 0.54-1.67); tier
     means are all near 1, so the frozen tier scales do not capture it.
   * Per-read noise variances solved from the three reads: log-variance correlation 0.66-0.68 between a compound's
     reads. Noisiness is mostly a property of the compound (persistent across replicate plates), not of one well.
   * Removing each compound's own scale cuts the pair excess kurtosis from 1.12 to 0.55.
   * Likelihood: compound-level t (one scale per compound shared by its lines and reads; best nu about 10) -1.380 per
     observation, pair-level t -1.403, Gaussian -1.420. Most of the heavy tail is compound-level scale heterogeneity.
7. **Design change (disclosed): second model class.** Added `level = "compound"`: a multivariate-t noise model with one
   precision weight per compound, shared across its lines and replicate reads (fitted from the reference differences by
   ML at each nu; VB-EM per compound; the predictive for T uses the compound's posterior noise scale). The reference-only
   inner selection now chooses (level, nu) over {pair, compound} x {2, 3, 4, 6, 10, 20} with the frozen utility; the
   Gaussian score is reported but is not a candidate.
8. **Exploration e1 (`dev_explore.py`, `dev/explore_e1.json`; all three 2.5 uM blocks, each block's recorded RSD
   configuration, point estimates; both levels x nu grid).** Reference-only inner score: Gaussian +0.083 / +0.078 /
   +0.082 (search / selection / evaluation); best pair (nu 20) +0.070 / +0.067 / +0.069; best compound (nu 20) +0.047 /
   +0.047 / +0.053. On the queries, D2 minus raw: Gaussian +0.023 / +0.031 / -0.008; pair nu 20 +0.009 / +0.025 /
   -0.019; compound nu 20 -0.032 / -0.029 / -0.066. D1 minus raw: Gaussian +0.075 / +0.081 / +0.127; pair nu 20 +0.053
   / +0.054 / +0.110; compound +0.039 / +0.046 / +0.110. Selected-pair coverage: Gaussian 0.714 / 0.694 / 0.675; pair
   nu 20 0.711 / 0.685 / 0.666; compound 0.747 / 0.737 / 0.721 (all-pair 0.81). Reading: compound-level noise repairs
   part of the selected-pair under-coverage, but shrinking compounds that look noisy also shrinks genuinely selective
   compounds, so D2 falls; pair-level tails cost D1 and D2 at every nu.
9. **Exploration e2 (`dev/explore_e2.json`): Student-t tails on the line-specific signal as well** (nu_s in {2, 4, 10},
   with pair nu in {4, 10, 20} and compound nu 10), the natural formalisation of "a real hit and an outlier look alike".
   Best D2 minus raw: +0.029 / +0.039 / +0.003 (Gaussian +0.023 / +0.031 / -0.008), but selected-pair optimism rises to
   +0.11 to +0.70 and selected-pair coverage falls (evaluation block 0.57-0.68). No signal-tail candidate beats the
   Gaussian reference-only score in any block (best +0.078 / +0.075 / +0.077).
10. **Frozen candidate set (decided here, before the freeze):** {pair, compound} x nu in {2, 3, 4, 6, 10, 20}, no
    signal tails. Reason: signal tails worsen the calibration this study is meant to repair and never beat the Gaussian
    on the reference utility; the noise-model question is the one REVISE asked. Expectation stated before the test:
    on the development dose no heavy-tail candidate beats the Gaussian on the reference utility, so H2 is expected to
    fail; the test checks this at two doses the development never saw, and measures whether compound-level noise
    restores selected-pair coverage there.
11. **Dry run v2** of the final pipeline (`ht_run.py dev v2 search`) on the 2.5 uM search block crashed after the frozen
    Gaussian inner selection (`TypeError`: the candidate tuple was concatenated with a list in `ht_inner_select`;
    `dev/dev_v2_search.log`). Fixed (`list(cands)`). No record was written. A fast smoke test then ran `run_block` on the
    2.5 uM search block with the frozen Gaussian inner selection replaced by the configuration SEARCH_v2 recorded
    (q = 3, rho = 0, prior off) and a reduced candidate set (25 s): all arms, calibration, optimism, the JSON round trip
    that `verify.py` relies on, pooling and the verdict rule run; `gauss_rho0` equals `rsd` to 3e-14; selected
    candidate pair nu = 20; `ht - rsd` D1 -0.022, D2 -0.014; `ht_compound - rsd` D1 -0.026, D2 -0.055; selected-pair
    coverage rsd 0.714, ht 0.711, ht_compound 0.747 (consistent with entries 5 and 8). The unstubbed frozen
    inner selection had already run inside `run_block` in entry 5. The smoke script was a scratch file and is not kept.
