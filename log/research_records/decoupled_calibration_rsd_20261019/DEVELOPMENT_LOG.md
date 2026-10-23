# Development log (pre-freeze; 2.5 uM search block only)

All entries are dated 2026-10-19 and precede `FREEZE.json`.

Development used only the HTS002 2.5 uM reads of the search block. The RSD study had already opened them (its search
block), and so had the heavy-tail development. No outcome of the decoupled layer was computed on any other block or dose
before the freeze. The 0.625 and 10 uM reads were opened earlier the same day by the heavy-tail test stage. This study's
development did not load them: the smoke runs read only the 2.5 uM cache.

1. **Inputs read, no data.** These files set the design:
   - RSD: `REPORT.md`, `PROTOCOL.md`, `DEVELOPMENT_LOG.md`.
   - Heavy-tail: `REPORT.md`, `PROTOCOL.md`, `DEVELOPMENT_LOG.md`, `README.md`.
   - Code: the frozen `ht_core.py`, `ht_run.py`, `ht_data.py`, `rsd_core.py`, `rsd_run.py`.

   Facts taken from those reports:
   - Pooled over 0.625 and 10 uM, rsd's selected-pair 80% coverage is 0.698 and its optimism +0.030.
   - `ht_compound` (nu 20 in all 6 units) has selected-pair coverage 0.749 and optimism -0.003 on its own picks, but
     costs D2 -0.048.
2. **Design decisions, made before any decoupled-layer outcome was computed:**
   - **Interval model = the heavy-tail `ht_compound` rule.** Same geometry, same nu choice from the frozen
     reference-only utility, same ML scale. With this choice, `dec` and `ht_compound` differ only in the ranking, and
     `dec` and `rsd` differ only in the intervals: a factorial comparison.
   - **Likelihood-chosen nu (nu_ML) as a secondary arm** (`dec_ml`). For an interval model, a likelihood choice of nu is
     the natural alternative. It is not primary, to keep one pre-specified method.
   - **"Gaussian signal + compound noise" as a secondary arm** (`dec_noise`). It is the literal noise swap. It is not
     primary, because the Gaussian signal posterior assumed a base noise scale that the compound model rejects for noisy
     compounds.
   - **Fixed-definition baseline intervals.** For `raw`, `raw2` and `shrink` the noise comes from the fixed q = 0
     reference VC: flat-prior replicate noise for raw reads, and a scalar-reliability posterior for `shrink`. These
     arms existed only as decision arms before. Their coverage gives the zero-method reference for calibration.
   - **Primary readout = 0.625 + 10 uM.** This makes the numbers directly comparable to the heavy-tail pooled test.
     2.5 uM is secondary, because this study developed on its search block.
   - **Reads only from the existing heavy-tail caches.** The study refuses any dose without a cache and checks that
     the cache folder is unchanged after each load.
   - **Bootstrap, seed and stratification as in the heavy-tail pool.** The `rsd` and `ht_compound` intervals and the
     per-unit sums must then reproduce the frozen heavy-tail records. This is the pipeline check.
3. **Metadata check (treatment table only, no read values).** HTS002 has an 8-point dose series in the metadata. Doses
   other than 0.625, 2.5 and 10 uM exist but were not considered: they are the same compounds, this study does not
   know whether earlier MAESTRO studies opened them, and choosing a tier is the owner's decision.
4. **Unit tests** (`test_dc.py`, 8 tests, pass), covering:
   - the flat-prior raw/raw2 interval definitions, which are calibrated on simulated Gaussian replicates;
   - the bootstrap p values, Holm and the verdict rule;
   - write-once outputs;
   - refusal of an unopened dose (no cache written);
   - refusal of the confirmatory stage.
5. **Smoke run v1** (`dev/smoke_2p5uM_search.json`, 692 s; first design, in which `dec` took both its claim and its
   interval from the compound model).

   The frozen pipeline is reproduced:
   - Gaussian inner choice q = 3, rho = 0, prior off; `rsd - raw` D1 +0.081, D2 +0.023; `raw2 - raw` +0.134 / +0.140.
     All equal RSD's `SEARCH_v2.json`.
   - The compound inner selection chose nu = 20 (Gaussian reference score 0.083 > every compound candidate,
     0.043-0.047). This matches heavy-tail entry 8.
   - Selected-pair 80% coverage: rsd 0.714, `ht_compound` 0.747. This matches heavy-tail entries 5 and 8.

   Decoupled readout on this block (rsd's D2 picks):

   | Arm | 80% coverage, selected [95% CI] | Optimism [95% CI] |
   |---|---|---|
   | first-design `dec` (now `dec_full`) | 0.743 [0.724, 0.757] | **-0.109 [-0.169, -0.062]** |
   | Gaussian claim + compound noise (then `dec_noise`, now `dec`) | 0.753 | -0.037 (equal to rsd's) |

   - First-design `dec`: claimed 0.667 against observed 0.776. P3 (optimism within +-0.15) has p 0.078, so the
     illustrative rule gave PARTIAL.
   - Other arms on the same picks: rsd 0.714 / -0.037; raw 0.619 / +0.798; raw2 0.661 / +0.557; shrink 0.723 / +0.050.
   - D1 and D2 picks of every decoupled arm equal rsd's (K1 holds). `dec_full - ht_compound` D2 +0.055: this is the
     ranking cost that decoupling avoids.
   - The mean compound weight E[lam] is 0.87 on rsd's D2 picks against 0.98 over all pairs: rsd's picks are enriched
     for compounds whose read looks noisy.
6. **Design change (disclosed): primary `dec` = Gaussian claim, compound-level noise interval.** Reason: the compound
   model's posterior mean shrinks every compound that looks noisy, including the genuinely selective compounds the
   Gaussian ranking keeps. On rsd's picks its claims are therefore pessimistic (-0.109). This is the mechanism the
   heavy-tail study diagnosed ("one read cannot tell a noisy compound from a selective one"), now appearing in the
   claims rather than in the ranking.

   Keeping the Gaussian claim, which RSD validated as nearly unbiased, and taking only the new-read noise scale from the
   compound model is the cleaner decoupling: ranking and claims from the Gaussian, width from the compound model.

   Changes:
   - The first design stays as the secondary arm `dec_full`.
   - `dec_ml` now mirrors the primary (Gaussian claim, compound noise at nu_ML).
   - A width-matched control `rsd_wm` was added. It applies one per-unit constant on rsd's predictive SD, matched to
     `dec`'s mean SD on rsd's picks, and uses no outcome. It asks whether the coverage gain comes from where the width
     goes or from more width.

   No primary-dose (0.625 or 10 uM) outcome of any decoupled variant had been computed when this was decided. The
   choice was informed by one development block, so it is a forking-path risk; the primary readout after the freeze is
   the check.
7. **Smoke run v2** (`dev/smoke2_2p5uM_search.json`, 659 s; final arm definitions; same 2.5 uM search block).

   | Arm | 80% coverage, rsd's D2 picks | All-pair coverage | Mean 80% width, picks |
   |---|---|---|---|
   | `rsd` | 0.714 | 0.798 | 2.00 |
   | `dec` | 0.753 [0.738, 0.767] | 0.814 | 2.23 |
   | `dec_full` | 0.743 | -- | -- |
   | `dec_ml` (nu_ML 16.8) | 0.754 | -- | -- |
   | **`rsd_wm`** (SD factor 1.114) | **0.764** | **0.842** | 2.23 |

   - `dec - rsd` coverage +0.040 [+0.018, +0.058]. Optimism of `dec` = rsd's = -0.037 [-0.093, +0.006]. The
     illustrative rule gives DECOUPLED_CALIBRATION_HOLDS on this block (P1, P2, P3 Holm p 0.0012, 0.0007, 0.0010).
   - **`dec - rsd_wm` coverage -0.011 [-0.030, +0.006].** On this block, uniformly widening rsd's intervals by the same
     mean amount covers the selected pairs at least as well. The coverage gain of `dec` is explained by its extra width,
     not by placing that width on noisy compounds.
   - D1-selected coverage: rsd 0.707, `dec` 0.719, `rsd_wm` 0.755.
8. **Secondary endpoints added after reading entry 7 (disclosed; primary tests unchanged).** Coverage alone cannot
   tell where width is useful: uniform widening raises it everywhere. Two proper scores on each arm's D2-selected pairs
   were added, with `dec - rsd`, `dec - rsd_wm` and the other coverage contrasts:
   - the 80% central-interval score (width plus 10 times the miss distance; Gneiting and Raftery 2007; lower is better);
   - the Gaussian log predictive density.

   These scores reward a model that puts its width where the misses are. They were not computed on any block before
   this decision. A third smoke run (`dev/smoke3_2p5uM_search.json`) checks the final code on the same block.
9. **Smoke run v3** (`dev/smoke3_2p5uM_search.json`, 614 s; the code frozen next). Every coverage number equals v2.

   Proper scores on rsd's D2 picks:

   | Arm | Interval score | Log score |
   |---|---|---|
   | `rsd` | 3.50 | -1.440 |
   | `dec` | 3.35 | -1.337 |
   | `rsd_wm` | 3.44 | -1.390 |
   | `dec_full` | 3.47 | -1.377 |

   | Contrast | Interval score [95% CI] | Log score [95% CI] |
   |---|---|---|
   | `dec - rsd` | -0.146 [-0.198, -0.092] | +0.103 [+0.070, +0.139] |
   | `dec - rsd_wm` | -0.085 [-0.120, -0.049] | +0.054 [+0.034, +0.078] |

   - Reading: on this development block, `rsd_wm` matches `dec`'s coverage only by widening every interval. `dec` scores
     better because its extra width sits on the compounds that miss.
   - `ht_compound` scores lower still (3.15) on its own, less extreme picks, which are different pairs.
   - The illustrative rule gives DECOUPLED_CALIBRATION_HOLDS on this block.
