# Heavy-tail RSD protocol: Student-t pair noise for the replicate-identified Virtual Cell posterior

Status: frozen by `freeze.py` (`FREEZE.json`) after development on the exposed 2.5 uM reads and before any 0.625 or
10 uM read was loaded. Development-grade study on exposed compounds; it cannot be an independent confirmation.
Development steps and what they saw: `DEVELOPMENT_LOG.md`. The expectation written there before the test: no
heavy-tail candidate beat the Gaussian on the reference utility at 2.5 uM, so H2 is expected to fail.

## 1. Question

The RSD study (`../replicate_decisions_20261019/REPORT.md`, REVISE) found that its replicate-identified Gaussian posterior
improves within-compound context selection (D1, +0.118) but not cross-compound candidate progression (D2, -0.008), with
80% predictive coverage 0.675 on D2-selected pairs. Its exploratory diagnosis: the replicate noise is heavy-tailed
(excess kurtosis 3.2) and D2 picks land on the outliers. Does replacing the Gaussian pair-level noise by a heavy-tailed
model, identified from reference replicates, recover D2 and selected-pair calibration while keeping the D1 gain?

## 2. Method under test (`ht_core.py`)

* **Signal model: unchanged and frozen.** For each (dose, block) the frozen Gaussian RSD inner selection
  (`rsd_core.inner_select`: input A, target T, 5 reference-cluster folds, frozen grid) chooses (q, rho, prior). The
  heavy-tail posterior uses the same q and prior with rho = 0 (diagonal pair noise): signal x = mu + U f + g,
  rank-q + diagonal covariance, per-tier scales alpha_k, all from the frozen `VirtualCell` (subclassed only to record
  the factors).
* **Noise model: the revision.** One read y = x + e, with e Student-t:
  * `pair` level: one precision weight per (compound, line) pair, e_ij | lam_ij ~ N(0, s^2 beta_k n0_j / lam_ij),
    lam_ij ~ Gamma(nu/2, nu/2) (isolated outliers);
  * `compound` level: one weight per compound shared by its lines and its replicate reads (multivariate-t; a noisy
    compound is noisy in every read). The predictive for a new read uses the compound's posterior noise scale.
  * n0_j, beta_k: the frozen replicate noise variances (line, tier).
* **Tail fit from the reference replicates.** z = (s_B - s_T)/sqrt(2)/sqrt(beta_k n0_j) on the block's references at the
  dose. For every candidate (level, nu) the scale s is the maximum-likelihood fit to z: difference-of-two-t density
  (pair) or per-compound multivariate-t density (compound), by Gamma quadrature. nu_ML (profile likelihood on a
  41-point grid, 1.5-100) is recorded per level.
* **Selection inside the reference set only.** (level, nu) is chosen from {pair, compound} x {2, 3, 4, 6, 10, 20} by the
  frozen replicate-split decision utility: input A, target T of held-out reference clusters (the frozen fold salt),
  objective = mean of the D1 and D2 utility gains over the raw read, held-out references edge-purged from the fit; ties
  to the larger nu. The Gaussian score is recorded but is not a candidate: the arm under test is always heavy-tailed.
  No query outcome is used.
* **Posterior.** Mean-field VB-EM per compound (vectorised): given E[lam], Gaussian posterior in factor form; given q(x),
  E[lam] updated; at most 200 iterations, tolerance 1e-6. With nu = inf it equals the frozen Gaussian posterior
  (tested to 1e-8). Decisions rank by the posterior mean.

## 3. Arena (`ht_data.py`)

* Compounds, families, clusters, roles (reference 424 / search 215 / selection 221 / evaluation 423), per-block reference
  purges and the per-compound permutation of the three detection plates into (A screening read, B second read, T truth
  read): unchanged from the frozen RSD arena (`rsd_data.build_arena`, imported).
* Test doses: HTS002 0.625 uM and 10 uM (atol 0.01), with the frozen column rule (first `(broad_id, compound_plate,
  well)` with all of X1-X3 at that dose). A compound without a triple at a dose is dropped from that dose's queries and
  references; counts are fixed from metadata in `FREEZE.json` (`test_arena_composition`).
* Query sets: all three RSD query blocks (search, selection, evaluation), each with its own purged references, at both
  test doses: 6 (dose, block) units. Every block was opened at 2.5 uM by the RSD study; the 0.625 and 10 uM reads were
  not used by RSD or by this study's development. The compounds and their 2.5 uM reads are exposed, so every result here
  is development-grade.
* There is no second screening run at 0.625 or 10 uM, so no cross-run truth is used.

## 4. Arms (`ht_run.py`; one read = 20 pool wells per compound)

| Arm | Reads | Definition |
|---|---|---|
| `raw` | 1 | selective read A (zero-method arm) |
| `raw2` | 2 | mean of reads A and B (40 wells); the value of a second read sets the practical threshold |
| `shrink` | 1 | read A times its per-tier replicate reliability around zero; fixed definition (q = 0, rho = 0, prior off) |
| `rsd` | 1 | frozen Gaussian RSD posterior with its own frozen inner selection (`rsd_core.inner_select`, frozen grid) |
| `ht` | 1 | method under test (section 2) |
| `ht_pair`, `ht_compound` | 1 | best candidate within each noise level by the same reference-only score (secondary) |
| `ht_fit` | 1 | `ht`'s level with nu = nu_ML from the reference replicate differences, no utility selection (secondary) |
| `gauss_rho0` | 1 | `ht` geometry with Gaussian noise; equals `rsd` whenever its inner choice has rho = 0 (check) |

Baselines keep these definitions whatever the method's inner choices. Policies read only A (and B for `raw2`) through
the frozen `Acquisition`; only the frozen `Evaluator` holds T.

## 5. Endpoints (graded on the truth read T, as in RSD)

* Selective response `s = y - rowmean(y) - g` (g = reference line mean of the dose); killing = -s.
* D1: mean of -s_T over the 10 lines chosen per compound, averaged over (dose, compound).
* D2: for each line, the 16 compounds chosen from the (dose, block) query set; mean of -s_T over all chosen pairs.
* Hits -s_T >= 1, false progression s_T > 0; unknown T excluded and counted.
* Calibration: 80% central predictive interval coverage for T on each posterior arm's own D2-selected pairs and on all
  pairs (Gaussian predictive for `rsd`; Gaussian signal posterior plus Student-t noise for `ht`).
* Selected-pair optimism: claimed minus observed killing on each arm's own D2-selected pairs.

## 6. Hypotheses, thresholds and verdict rule (`ht_run.verdict`)

Practical threshold per decision: delta_D = 0.5 x the pooled `raw2 - raw` estimate on the same test data (half the
value of a second read, the RSD definition applied at the test doses). The 2.5 uM values (D1 0.067, D2 0.070) are
reported for reference only.

| ID | Contrast (pooled over both test doses and three blocks) | Rule | Role |
|---|---|---|---|
| H1 | `ht - raw`, D2 | Holm p < 0.05 and estimate >= delta_D2 -> SUPPORTED | primary: D2 recovers |
| H2 | `ht - rsd`, D2 | Holm p < 0.05 -> SUPPORTED | primary: the gain is due to the noise model |
| H3 | `ht - raw`, D1 | Holm p < 0.05 and estimate >= delta_D1 -> SUPPORTED | primary: D1 keeps its gain |
| NI | `ht - rsd`, D1 | lower 95% bound > -0.5 x delta_D1 | D1 not worse than the Gaussian posterior |
| C1 | `ht` 80% coverage on its D2-selected pairs | in [0.70, 0.90] | selected-pair calibration recovers |
| C2 | `ht` 80% coverage on all pairs | in [0.75, 0.85] | descriptive criterion |
| C3 | `ht` selected-pair optimism (claimed - observed) | absolute value <= 0.15 | descriptive criterion |

Holm over H1-H3 with one-sided bootstrap p. A primary contrast whose `raw2 - raw` lower bound is not above zero is
labelled `UNINFORMATIVE_NO_HEADROOM`. A Holm-significant H1 or H3 below delta is `SIGNIFICANT_BELOW_PRACTICAL`.

Overall verdict:
* `ADVANCE_TO_INDEPENDENT_TEST` if H1, H2 and H3 are SUPPORTED, NI holds and C1 holds (development-grade; the next step
  would be PRISM 24Q2, which needs the owner's authorisation).
* `HEAVY_TAIL_DOES_NOT_FIX_D2` if H2 is not SUPPORTED.
* `PARTIAL` otherwise, with the unmet items listed.

Secondary (unadjusted, labelled): `rsd - raw` (does the frozen D1 gain replicate at other doses), `raw2 - raw`,
`ht - raw2`, `ht - shrink`, `ht_pair - rsd`, `ht_compound - rsd`, `ht_fit - rsd`, `shrink - raw`, `ht - ht_fit`; `ht - rsd`
selected-pair coverage difference; calibration and optimism of every posterior arm; everything per dose.

## 7. Statistics

* Pooled over the 6 (dose, block) units. Cluster bootstrap, 4,000 draws, seed 20261019: clusters resampled by multinomial
  within each block (stratified), the same draw applied to both doses (a compound's two doses are not independent).
  Intervals condition on the fitted reference models and the chosen pairs.
* One-sided p = (number of draws <= 0, plus 1) / (draws + 1). Holm over the three primary tests.
* Per-dose aggregates and all secondary contrasts are reported unadjusted and labelled secondary.

## 8. Stage rules, isolation and versions

* One test stage (`ht_run.py evaluation`), run once after `FREEZE.json`; it checks every frozen hash (study code and
  protocol, the imported frozen RSD files, data files) before loading a test-dose read and writes `RESULT.json` once.
  No retuning after the test doses are opened; any later analysis is labelled exploratory.
* `ht_data.guard` refuses test-dose reads while `FREEZE.json` is absent; `freeze.py` refuses to run if a test-dose read
  cache exists; `verify.py` checks that the test-dose read caches were written after the freeze time.
* Compute only (no paid or LLM call). Cost accounting in wells: one read = 20 pool wells per compound; `raw2` = 40.
* Code, data and environment hashes, grids, candidate set and thresholds: `FREEZE.json`.
