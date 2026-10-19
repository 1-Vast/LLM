# Decoupled calibration protocol: Gaussian ranking with compound-level Student-t intervals

Status: frozen by `freeze.py` (`FREEZE.json`), after three development smoke runs on the exposed 2.5 uM search block
and before the pre-registered development readout (`DEV_RESULT.json`).

**Development-only study.** Every read it uses was already opened, by the RSD study (2.5 uM) or by the heavy-tail test
stage (0.625 and 10 uM). No unopened arena is authorised, so the confirmatory stage (section 9) is blocked, and nothing
here can be an independent confirmation.

Development steps and what they saw: `DEVELOPMENT_LOG.md`.

## 1. Question

Two frozen studies on the same arena:
- The RSD study (`../replicate_decisions_20261019/REPORT.md`) ranks with a replicate-identified Gaussian posterior. This
  improves within-compound context selection (D1) but not candidate progression (D2). Its 80% predictive coverage on
  D2-selected pairs is about 0.70.
- The heavy-tail study (`../heavy_tail_rsd_20261019/REPORT.md`, HEAVY_TAIL_DOES_NOT_FIX_D2) found the replicate noise
  tails are mostly compound-level. A compound-level Student-t posterior (`ht_compound`) brings selected-pair coverage to
  0.749 and selected optimism to -0.003. Used for ranking, it costs D2 -0.048, because one read cannot separate a noisy
  compound from a selective one.

Question: if the decisions are kept from the Gaussian posterior and only the value claims and predictive intervals of the
chosen pairs come from the compound-level model, are the Gaussian D1/D2 decisions kept unchanged? And does the 80%
coverage on D2-selected pairs reach [0.70, 0.90], with selected-pair optimism within +-0.15?

## 2. Method under test (`dc_run.py`, arm `dec`)

- **Ranking (unchanged, frozen).** Per (dose, block), the frozen Gaussian RSD inner selection
  (`rsd_core.inner_select`, frozen grid and folds) chooses (q, rho, prior). The frozen `VirtualCell.posterior` mean of
  read A ranks D1 (top 10 lines per compound) and D2 (top 16 compounds per line).
- **Claims (unchanged, frozen).** The claimed value of a chosen pair is the Gaussian posterior mean m_g, as in `rsd`.
- **Calibration layer (the addition).** Only the noise term of the predictive interval changes. The heavy-tail
  compound-level model is fitted to the same read A, with the frozen `ht_core` functions imported and never modified:
  - geometry (q, prior) from the Gaussian inner choice, rho = 0;
  - nu = the best compound candidate (nu in {2, 3, 4, 6, 10, 20}) by the frozen reference-only replicate-split utility
    (`ht_core.ht_inner_select`); this is the heavy-tail `ht_compound` rule;
  - scale s = maximum likelihood on the reference replicate differences (`ht_core.fit_tail_compound`);
  - posterior: `ht_core.ht_posterior(level="compound")`. It gives each compound i a posterior noise scale for a new
    read: sigma2_c[i, j] = s^2 beta_k n0_j E[1 / lam_i].

  The predictive distribution of a new read at a chosen pair is N(m_g, v_g + sigma2_c), where v_g is the Gaussian
  posterior signal variance. Compared with `rsd` (N(m_g, v_g + beta_k n0_j)), the layer gives more width to compounds
  whose read A looks noisy and less to compounds that look quiet.
- **Decision and claim invariance.** Nothing in the layer feeds back into a decision or a claim. K1 (section 6) checks
  that the D1 and D2 picks are identical to `rsd` in every unit. The `dec` and `rsd` claims, and hence their optimism,
  are identical by construction.
- **Changed after the development smoke run.** The first design took the claim and the interval from the compound model
  (now arm `dec_full`). It was changed to the design above after the 2.5 uM search-block smoke run, and before any
  primary-dose outcome of either variant was computed. The reasons and the smoke numbers are in `DEVELOPMENT_LOG.md`
  entry 6.
- No outcome of a query compound is used to fit anything. The truth read T is graded only by the frozen `Evaluator`.

## 3. Arena (exposed; development only)

- **Compounds and roles.** Compounds, families, clusters, roles (reference 424 / search 215 / selection 221 / evaluation
  423), per-block reference purges and the replicate roles (A screening, B second read, T truth) come unchanged from the
  frozen RSD arena (`rsd_data.build_arena`). Dose handling and the column rule are as in the frozen heavy-tail
  `ht_data`.
- **Reads.** Only the existing read caches of the heavy-tail study (`../heavy_tail_rsd_20261019/cache/`). This study
  never parses the log-fold-change file and never writes a cache:
  - `dc_run.require_cache` refuses a dose without an existing cache;
  - the cache folder is checked to be unchanged after every load;
  - `FREEZE.json` records the hashes of the three caches.
- **Units.** 3 doses x 3 query blocks (search, selection, evaluation), each block with its own purged references.
- **Primary development readout.** 0.625 and 10 uM pooled. These are 6 units, with the same compound-doses and
  clusters as the heavy-tail test stage (1,715 compound-doses, 250 block-clusters; the composition is copied into
  `FREEZE.json`). These reads were opened by the heavy-tail test stage. The decoupled layer's outcomes on them have not
  been computed before this freeze.
- **Secondary readout.** 2.5 uM, all three blocks. Its search block was used by this study's smoke runs.

## 4. Arms (`dc_run.py`; one read = 20 pool wells per compound)

| Arm | Wells | Ranks D1/D2 by | Claimed value and predictive interval for T |
|---|---|---|---|
| `raw` | 20 | selective read A (zero-method arm) | A itself; flat-prior replicate noise, T - A ~ N(0, 2 n1) |
| `raw2` | 40 | mean of A and B | the mean; T - mean ~ N(0, 1.5 n1) (2 n1 where B is missing) |
| `shrink` | 20 | A x per-tier replicate reliability r_k | r_k A; N(r_k A, (1 + r_k) n1) |
| `rsd` | 20 | frozen Gaussian posterior mean | frozen Gaussian predictive (signal variance + one-read noise) |
| `ht_compound` | 20 | compound-level t posterior mean | its own predictive (as in the heavy-tail study) |
| **`dec`** | 20 (+0) | **frozen Gaussian posterior mean** | **claim m_g; N(m_g, v_g + sigma2_c), sigma2_c = `ht_compound`'s compound noise scale for a new read** |
| `dec_full` | 20 (+0) | frozen Gaussian posterior mean | `ht_compound`'s own mean and predictive (the first design; secondary) |
| `dec_ml` | 20 (+0) | frozen Gaussian posterior mean | as `dec`, with sigma2_c from the compound model at nu = nu_ML (reference likelihood), not utility-selected (secondary) |
| `rsd_wm` | 20 (+0) | frozen Gaussian posterior mean | width-matched control: claim m_g; rsd's Gaussian predictive with its SD multiplied by one per-unit constant so that the mean predictive SD over rsd's D2 picks equals `dec`'s. It uses no outcome. It separates "more width" from "width placed on noisy compounds" (secondary) |

Notes on the arms:
- **Fixed-definition baselines.** n1 and r_k for `raw`, `raw2` and `shrink` come from the fixed-definition VC (q = 0,
  rho = 0, prior off). They are independent of every inner choice of the method. The rankings of `raw`, `raw2`,
  `shrink`, `rsd` and `ht_compound` are those of the frozen heavy-tail arms.
- **Cost of the layer.** It adds no well and no read. Its cost is compute only, logged in seconds.
- **Not a cost-matched arm.** `raw2` is the value of a second read (40 wells).

## 5. Endpoints (graded on the truth read T)

- **Decisions.** Selective response `s = y - rowmean(y) - g`; killing = -s.
  - D1: mean of -s_T over the 10 chosen lines per compound, averaged over (dose, compound).
  - D2: mean of -s_T over all chosen (compound, line) pairs.
  - Hits are -s_T >= 1; false progression is s_T > 0. Unknown T is excluded and counted.
- **Calibration (primary).** 80% central predictive coverage of T on each arm's own D2-selected pairs. A pair is covered
  when |F(T) - 1/2| <= 0.4, with F the arm's predictive CDF.
  - For `dec`, `dec_full`, `dec_ml` and `rsd_wm`, the selected pairs are rsd's D2 picks.
  - Pairs without a defined claim or a known T are excluded.
- **Calibration (secondary).** 50% and 90% coverage on D2-selected pairs; 80% coverage on D1-selected pairs; 80%
  coverage on all pairs; mean PIT z; mean 80% interval width on selected pairs.
- **Proper scores on D2-selected pairs (secondary; added before the freeze, `DEVELOPMENT_LOG.md` entry 8).**
  - The 80% central-interval score: (u - l) + 10 (l - T)+ + 10 (T - u)+, lower is better (Gneiting and Raftery 2007).
  - The Gaussian log predictive density of T, higher is better.

  Every predictive here is Gaussian: the compound-level model's new-read predictive is Gaussian given its posterior
  noise scale.
- **Selected-pair optimism.** Claimed minus observed killing on the arm's own D2-selected pairs. The claim is -(the arm's
  centre).

## 6. Hypotheses, thresholds and verdict rule (`dc_run.verdict`)

Primary (pooled over the 6 primary units; Holm over P1-P3 at alpha 0.05; one-sided percentile-bootstrap p):

| ID | Statistic | Null rejected when | Meaning |
|---|---|---|---|
| P1 | coverage80_sel(`dec`) - coverage80_sel(`rsd`) | > 0 | the layer improves selected-pair coverage on the same picks |
| P2 | coverage80_sel(`dec`) | inside [0.70, 0.90], two one-sided tests: p = max(p(<= 0.70), p(>= 0.90)) | selected-pair coverage in the band |
| P3 | selected optimism(`dec`) | inside [-0.15, +0.15], two one-sided tests | value claims of chosen pairs nearly unbiased (the layer keeps rsd's claims, so this tests them on the readout) |
| K1 | D1 and D2 picks of `dec`, `dec_full`, `dec_ml`, `rsd_wm` vs `rsd` | identical in every unit, so `dec - rsd` D1 = D2 = 0 exactly | decisions kept (a structural check, not a test) |

Bootstrap p values:
- `p(<= x) = (number of draws <= x, plus 1) / (draws + 1)`;
- `p(>= x)` is defined likewise.

Overall verdict (development-grade; label carries `grade = DEVELOPMENT_ONLY`):
- `DEFECT_DECISIONS_CHANGED` if K1 fails.
- `DECOUPLED_CALIBRATION_HOLDS` if P1, P2 and P3 are all Holm-significant.
- `DECOUPLED_CALIBRATION_FAILS` if the `dec` point estimate of selected coverage is outside [0.70, 0.90], or its
  |optimism| > 0.15.
- `PARTIAL` otherwise, with the unmet items listed.

Secondary (unadjusted, labelled):
- Decision contrasts D1/D2:
  - `rsd - raw`, `raw2 - raw` (value of a second read; delta = 0.5 x this, for context), `shrink - raw`;
  - `ht_compound - raw`, `ht_compound - rsd`;
  - `dec - raw`, `dec - rsd` (identically 0), `dec - ht_compound` (ranking cost avoided), `dec - raw2`.
- Coverage contrasts, plus interval-score and log-score contrasts on the same pairs:
  - `dec - rsd_wm` (does the placement of width matter, beyond its amount?);
  - `dec - rsd`, `dec - dec_full`, `dec - ht_compound`, `dec_full - rsd`, `dec_ml - rsd`, `ht_compound - rsd`.

  The `ht_compound` comparisons use different pairs (its own picks).
- All-pair coverage of `dec` in [0.75, 0.85] (descriptive).
- Every arm's calibration and optimism; everything per dose; the 2.5 uM readout.

## 7. Statistics

- **Bootstrap.** Pooled cluster bootstrap, 4,000 draws, seed 20261019.
  - Clusters are resampled by multinomial within each query block (stratified by block).
  - The same draw applies to every dose, because a compound's reads at several doses are not independent. This is the
    heavy-tail construction, reimplemented in `dc_run.pool` and checked against it.
- **Ratio statistics.** Coverage and optimism are ratios of per-cluster sums.
- **Conditioning.** Intervals condition on the fitted reference models and on the chosen pairs.
- **Reproduction check.** The `rsd` and `ht_compound` per-unit sums at 0.625 and 10 uM must equal the frozen heavy-tail
  `RESULT.json` records (max abs difference <= 1e-9). This includes the inner choices and the noise scale. A mismatch is
  a defect, reported before any result.

## 8. Stage rules and isolation

- **Development.** `dc_run.py dev <tag> <block>` on 2.5 uM only, write-once `dev/` records, before the freeze.
- **Freeze.** `freeze.py` writes `FREEZE.json` once and refuses if `DEV_RESULT.json` exists. It records:
  - hashes of this study's code, protocol, development log and records;
  - hashes of the imported frozen RSD and heavy-tail files, each checked against its own study's freeze;
  - the three read caches;
  - the metadata files;
  - the environment and every threshold.
- **Development readout.** `dc_run.py devread` runs once after the freeze. It checks every frozen hash first and writes
  `DEV_RESULT.json` once. No retuning after it; any later analysis is labelled exploratory.
- **Verification.** `verify.py` is read-only:
  - freeze hashes, readout after freeze, K1 and the heavy-tail reproduction;
  - pooled statistics and verdicts recomputed from the per-unit records;
  - `--replay` re-runs every unit.
- **Constraints.** No paid or LLM call, no sealed tier, PRISM 24Q2 not opened. Nothing outside this folder is written
  (the `research/STUDIES.json` and `research/EVIDENCE.md` entries excepted).

## 9. Confirmatory test: BLOCKED

A confirmation needs reads that no MAESTRO study has opened, with replicate structure for reference identification
(two replicate reads of a few hundred reference compounds) and a held-out replicate or run for the truth read. Every
HTS002 dose this protocol can use is already opened. The decision about an independent tier belongs to the owner:
- PRISM 24Q2 is sealed and needs the owner's authorisation.
- Other HTS002 doses of the same compounds exist in the metadata. They would not be independent compounds, and this study
  does not know whether earlier MAESTRO studies opened them.

This study does not choose a tier: `dc_run.py confirm` refuses.

If the owner authorises a tier, it would be opened once under an amendment frozen before opening. The amendment would
add only a loader for that tier, with its composition from metadata. The method, arms, endpoints, P1-P3, K1, thresholds,
bootstrap and verdict rule stay as above, with the label `grade = CONFIRMATORY`.

## 10. Expectations recorded before the readout

Sources: the frozen heavy-tail pooled record (0.625 + 10 uM) and the smoke runs (2.5 uM search block).

- **K1 holds by construction.** `dec - rsd` is exactly 0 for D1 and D2.
- **P1 expected SUPPORTED.** rsd's selected-pair coverage was 0.698 pooled in the heavy-tail record: 0.695 at 0.625 uM
  and 0.701 at 10 uM. `dec` added +0.040 on the smoke block, so 0.72-0.75 pooled is expected.
- **P2 expected SUPPORTED, but it is the most fragile test.** It needs the lower 95% bound above 0.70, and a gain of
  half the smoke size would leave it near the edge.
- **P3 expected SUPPORTED.** `dec`'s claims are rsd's, whose pooled optimism was +0.030 [-0.001, +0.059].
- **Expected overall:** DECOUPLED_CALIBRATION_HOLDS (development grade).
- **Expected secondary results:**
  - `dec - rsd_wm` coverage <= 0;
  - `dec - rsd_wm` interval score < 0 and log score > 0 (placement of width matters);
  - `dec_full` claims pessimistic (optimism below rsd's).
- **What would falsify the layer's rationale on the readout:**
  - `dec` coverage not above rsd's, or below 0.70;
  - `dec` no better than `rsd_wm` on both proper scores.

## 11. Versions

Code, imported frozen files, read caches, metadata hashes, environment, thresholds, candidates, doses and composition:
`FREEZE.json`.
