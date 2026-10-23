# Heavy-tail RSD report: does Student-t noise repair candidate progression?

2026-10-19. Development-grade test of the REVISE recommendation in `../replicate_decisions_20261019/REPORT.md`.

- **Arena.** Exposed PRISM 19Q4 compounds, HTS002 0.625 uM and 10 uM reads.
- **Order of work.** Development on the already-exposed 2.5 uM reads, then the freeze (`FREEZE.json`, 08:06:08 UTC),
  then both test doses opened once (08:06:17 UTC).
- **Verification.** `verify.py` reports VERIFY OK: all hashes match, the imported frozen RSD files are unchanged, the
  test-dose read caches were written after the freeze, and the pooled statistics and verdict recompute from the stored
  per-block records.

## Verdict: HEAVY_TAIL_DOES_NOT_FIX_D2

Pooled over 2 doses x 3 query blocks: 1,715 compound-doses, 250 clusters, 4,000-draw cluster bootstrap stratified by
block. Practical thresholds = half the value of a second read on the same data: delta_D1 0.078, delta_D2 0.080.

| Primary | Contrast | Estimate [95% CI] | Holm p | Label |
|---|---|---|---|---|
| H1 D2 recovers | `ht - raw`, D2 | +0.015 [-0.014, +0.046] | 0.35 | NOT_SUPPORTED |
| H2 the noise model causes it | `ht - rsd`, D2 | **-0.007 [-0.011, -0.003]** | 1.00 | NOT_SUPPORTED |
| H3 D1 keeps its gain | `ht - raw`, D1 | +0.043 [+0.003, +0.076] | 0.060 | NOT_SUPPORTED (also below delta) |
| NI | `ht - rsd`, D1 | -0.015 [-0.025, -0.005] | -- | holds (bound > -0.039) |
| C1 | `ht` 80% coverage, D2-selected pairs | 0.690 [0.675, 0.707] | -- | fails (band 0.70-0.90) |
| C2 / C3 | `ht` all-pair coverage / selected optimism | 0.789 / +0.042 | -- | pass |

The heavy-tailed posterior is slightly worse than the frozen Gaussian posterior on both decisions. It does not restore
selected-pair calibration. This matches the expectation recorded in `PROTOCOL.md` and `DEVELOPMENT_LOG.md` before the
test doses were opened.

**Recommendation:**
- Close the "Gaussian to heavy-tailed pair noise" branch of REVISE for candidate progression.
- Keep the Gaussian RSD posterior for context selection and for value estimates of selected candidates. Its D1 gain
  replicates in sign at both new doses, at about half the 2.5 uM size.
- For progression, keep the conventional rule: one raw read, then re-read the top candidates. A second read is worth
  +0.16 here, and no one-read model came close.

## 1. What was tested

The RSD posterior is a frozen replicate-identified Virtual Cell posterior: rank-q + diagonal signal covariance and
per-tier scales. Its Gaussian pair noise was replaced by Student-t noise (`ht_core.py`), with two model classes:

| Level | Precision weight | Interpretation |
|---|---|---|
| `pair` | one per (compound, line) | isolated single-well outliers |
| `compound` | one per compound, shared across its lines and its replicate reads | multivariate t; some compounds are noisy in every read |

The signal geometry (q, prior) is inherited from the frozen Gaussian inner selection. The noise scale comes from a
maximum-likelihood fit to the reference replicate differences (B - T)/sqrt(2):
- a difference-of-two-t density for `pair`;
- a per-compound multivariate-t density for `compound`.

The noise model is chosen inside the reference set only, from {pair, compound} x nu in {2, 3, 4, 6, 10, 20}. Selection
uses the frozen RSD replicate-split decision utility: input A, target T, the frozen cluster folds, objective = mean of the
D1 and D2 gains over the raw read. The Gaussian is scored for comparison but is not a candidate, so the arm under test is
always heavy-tailed. The posterior is VB-EM per compound. With nu = inf it reproduces the frozen Gaussian posterior to
1e-8 (unit test); in every test unit `gauss_rho0` equalled `rsd` to below 1e-13.

Arms (one read = 20 pool wells per compound):
- One read: `raw` (zero-method arm), `shrink` (fixed-definition scalar shrinkage), `rsd` (frozen Gaussian, own frozen
  inner selection), `ht`, and the secondaries `ht_pair`, `ht_compound`, `ht_fit`.
- Two reads (40 wells): `raw2`.

Baseline definitions do not depend on the method's inner choices.

## 2. Results

### 2.1 Arms (pooled; graded on the sealed replicate T)

| Arm | Wells | D1 utility | D1 hits | D1 false prog. | D2 utility | D2 hits | D2 false prog. |
|---|---|---|---|---|---|---|---|
| raw | 20 | 0.848 | 0.401 | 0.268 | 0.859 | 0.422 | 0.237 |
| shrink | 20 | 0.848 | 0.401 | 0.268 | 0.877 | 0.434 | 0.232 |
| **rsd (frozen Gaussian)** | 20 | **0.904** | 0.415 | 0.221 | **0.881** | 0.434 | 0.229 |
| ht (selected: pair, nu 20, all 6 units) | 20 | 0.889 | 0.410 | 0.221 | 0.874 | 0.431 | 0.230 |
| ht_compound (nu 20, all units) | 20 | 0.889 | 0.408 | 0.223 | 0.834 | 0.407 | 0.230 |
| ht_fit (nu_ML) | 20 | 0.846 | 0.396 | 0.222 | 0.839 | 0.420 | 0.233 |
| raw2 | 40 | 1.006 | 0.460 | 0.219 | 1.019 | 0.483 | 0.193 |

Secondary contrasts (unadjusted):

| Contrast | D1 | D2 |
|---|---|---|
| `rsd - raw` | +0.057 [+0.026, +0.085] | +0.022 [-0.005, +0.051] |
| `raw2 - raw` | +0.155 [+0.134, +0.176] | +0.159 [+0.144, +0.177] |
| `ht_compound - rsd` | -0.015 [-0.028, -0.004] | -0.048 [-0.064, -0.034] |
| `ht_fit - rsd` | -0.057 [-0.077, -0.038] | -0.043 [-0.055, -0.031] |
| `ht - shrink` | +0.043 [+0.003, +0.077] | -0.003 [-0.031, +0.023] |

### 2.2 Calibration and selected-candidate optimism (D2-selected pairs, own picks)

| Arm | 80% coverage, selected | 80% coverage, all pairs | Claimed - observed |
|---|---|---|---|
| raw | -- | -- | +0.964 |
| raw2 | -- | -- | +0.699 |
| shrink | -- | -- | +0.085 |
| rsd | 0.698 [0.683, 0.714] | 0.799 | +0.030 |
| ht | 0.690 [0.675, 0.707] | 0.789 | +0.042 |
| **ht_compound** | **0.749 [0.739, 0.757]** | 0.809 | **-0.003** |
| ht_fit | 0.670 | 0.761 | +0.094 |

`ht - rsd` selected-pair coverage: -0.008 [-0.010, -0.006].

Only the compound-level noise model moves selected-pair coverage into the 0.70-0.90 band and removes the residual
optimism. It does so by shrinking compounds that look noisy, and that costs D2 0.048.

### 2.3 Per dose (secondary)

| Contrast | 0.625 uM (859 compounds) | 10 uM (856 compounds) |
|---|---|---|
| `ht - rsd` D1 / D2 | -0.017 / -0.008 | -0.012 / -0.006 |
| `ht - raw` D1 / D2 | +0.035 / +0.039 | +0.050 / -0.014 |
| `rsd - raw` D1 / D2 | +0.053 [+0.024, +0.079] / +0.047 [+0.008, +0.087] | +0.062 [+0.022, +0.102] / -0.008 [-0.033, +0.015] |
| `raw2 - raw` D1 / D2 | +0.112 / +0.157 | +0.198 / +0.153 |
| selected coverage rsd / ht / ht_compound | 0.695 / 0.690 / 0.763 | 0.701 / 0.689 / 0.736 |
| optimism rsd / ht / ht_compound | -0.029 / -0.025 / -0.074 | +0.086 / +0.106 / +0.065 |

The same ordering holds at both doses: Gaussian >= pair t > compound t for decisions, and compound t is best for
calibration.

### 2.4 What the reference-only selection saw (per test unit)

| Unit | Gaussian config (frozen inner) | Gaussian score | Best pair (nu 20) | Best compound (nu 20) | nu_ML pair / compound | Excess kurtosis of z |
|---|---|---|---|---|---|---|
| 0.625 search | q 2, prior off | +0.050 | +0.034 | +0.022 | 7.2 / 25.5 | 0.79 |
| 0.625 selection | q 2, prior off | +0.045 | +0.033 | +0.018 | 8.0 / 25.5 | 0.76 |
| 0.625 evaluation | q 2, prior off | +0.044 | +0.036 | +0.021 | 7.2 / 23.0 | 0.79 |
| 10 search | q 5, prior on | +0.074 | +0.063 | +0.033 | 3.9 / 8.9 | 1.87 |
| 10 selection | q 5, prior on | +0.063 | +0.053 | +0.026 | 3.9 / 8.9 | 1.92 |
| 10 evaluation | q 3, prior on | +0.071 | +0.061 | +0.038 | 3.9 / 8.9 | 1.90 |

- The reference likelihood always prefers heavy tails: nu_ML is 3.9-8 for pair and 9-26 for compound.
- The reference decision utility always prefers the Gaussian, and among heavy-tailed candidates always the lightest tail
  on the grid.
- The data are heavy-tailed, but modelling the tails makes the rankings worse.
- At 10 uM the frozen Gaussian selection switched the chemistry prior on, which it never did at 2.5 uM (descriptive).

## 3. Why it fails (development diagnosis on 2.5 uM, before the freeze; `DEVELOPMENT_LOG.md` 5-9)

- **Most of the heavy tail is compound-level, not pair-level.** On 2.5 uM references, each compound's noise variance
  spreads with SD 0.39 against 0.08 expected under homogeneity. A compound's per-read noise variances correlate 0.66-0.68
  across its three plates, so noisiness is a property of the compound. Removing each compound's scale halves the excess
  kurtosis (1.12 to 0.55). A compound-level t fits better than a pair-level t: log-likelihood -1.380 vs -1.403 per
  observation; Gaussian -1.420.
- **But one read cannot tell a noisy compound from a selective one.** A compound with large residuals off the low-rank
  axes may be noisy or genuinely line-selective. Both inflate the same single-read residual variance, so the
  compound-level model shrinks the selective compounds that D2 is looking for (D2 -0.048).
- **Pair-level tails do the same per pair.** A real line-specific hit and a single-well outlier are both large
  residuals. Downweighting large residuals removes hits as often as outliers, which costs D1 and D2 at every nu.
- **Heavy-tailed signal does not help either.** Giving the line-specific signal Student-t tails as well recovered at
  most +0.011 D2 over the Gaussian on 2.5 uM. It inflated selected-pair optimism to +0.1 to +0.7, so it was excluded
  before the freeze (log entry 9-10).
- **The D2 failure is about information, not the shape of the noise model.** One read does not carry what is needed to
  separate outliers from hits. A second physical read does (+0.16), and so does the compound-level noise scale, but
  only for calibration.

## 4. What is shown, what is not

**Shown (development grade; same compounds as RSD, two new doses):**
1. Replacing the Gaussian pair noise with Student-t noise, pair or compound level, selected or ML-fitted, does not
   improve candidate progression. It slightly worsens it relative to the frozen Gaussian posterior (-0.007 pooled,
   negative at both doses).
2. The reference-only replicate-split utility predicted this in all 6 test units and all 3 development blocks: the
   procedure has an internal signal that the revision does not help.
3. The frozen RSD context-selection gain replicates in sign at 0.625 and 10 uM: `rsd - raw` D1 +0.057 pooled, positive
   at both doses. It is half the 2.5 uM size (+0.118) and below half a second read here (0.078). Its selected-candidate
   optimism stays small (+0.030 against +0.96 for raw reads).
4. A compound-level noise scale restores selected-pair 80% coverage (0.698 to 0.749) and removes residual optimism
   (+0.030 to -0.003). The costs are D2 -0.048 and D1 -0.015.

**Not shown:**
- That a heavy-tailed model could help with more than one read per compound. The compound noise scale is estimated
  better from two reads.
- A decoupled design: rank with the Gaussian posterior, report intervals with the compound-level noise model. It is
  suggested by 2.2 but post hoc and untested.
- Anything on independent compounds. PRISM 24Q2 was not opened and needs the owner's authorisation.

## 5. Recommendation and next step

- **Retire** the heavy-tailed pair-noise revision for D2. Do not spend an independent tier on it.
- **Keep** the Gaussian RSD posterior for D1 and for value estimates of selected candidates. Its D1 gain is smaller at
  0.625 and 10 uM than at 2.5 uM, so the claim "equals a second read at half the wells" is specific to 2.5 uM.
- **For D2,** the conventional workflow stands: one read, then re-read the top candidates.
- **Most informative next experiment** (exploratory, cheap, on exposed data): the decoupled calibration layer. Rank with
  the frozen Gaussian posterior and attach compound-level-noise predictive intervals to the selected candidates. Then
  test whether selected-pair coverage reaches 0.80 without the ranking cost. Calibrated intervals on progressed
  candidates feed RSD's fallback B (audit-based progression risk), which RSD did not run because selected-pair coverage
  was below 0.70.

## 6. Independence, limitations, cost

- **Exposed compounds.** Same compounds, roles and replicate-plate assignment as RSD. The 0.625 and 10 uM reads were not
  used by RSD or by this study's development. Earlier MAESTRO studies used HTS002 at several doses, so the test reads are
  not guaranteed unseen by the programme. Development-grade evidence only.
- **Development informed the design.** Development used all three 2.5 uM blocks: the compound-level class and the
  exclusion of signal tails were decided after looking at them. Every step and its readout is in `DEVELOPMENT_LOG.md`.
  The 2.5 uM numbers are not evidence for any hypothesis.
- **Conditional intervals.** Intervals condition on the fitted reference models and the chosen pairs. Doses share the
  bootstrap draw because a compound appears at both. Bootstrap p has a floor of 1/4001.
- **No cross-run truth.** No second screening run exists at 0.625 or 10 uM, so H6-style cross-run checks were not
  possible.
- **H3 near miss.** H3 missed Holm by a narrow margin (0.060). It would also have failed the practical threshold
  (0.043 < 0.078).
- **Cost.** One-read arms 1,715 reads = 34,300 wells; `raw2` 68,600 wells. Compute: the test stage took 4,150 s on a
  desktop CPU (development about 1 h more). No GPU, no LLM, no paid call, no sealed tier, nothing committed.
- **Defects found and fixed before the freeze.** A Gauss-Laguerre quadrature tail error; NaN summaries in the first
  noise-anatomy record; a tuple/list crash in the first dry run. All are in the development log, and none touched a
  test-dose read.
