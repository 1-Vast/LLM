# RSD final report: replicate-identified Virtual Cell posterior for noise-aware research decisions

2026-10-19. Development-grade study on exposed PRISM 19Q4 data (see "Independence" below). Frozen protocol `PROTOCOL.md`,
freeze `FREEZE.json` (04:15 UTC, before the selection and evaluation blocks were read), `verify.py` VERIFY OK (hashes,
stage rules, verdict recomputed); `verify.py --replay` reproduces all 67 headline estimates within 1e-6 in the `maestro` env.

## Verdict

| Primary hypothesis (evaluation block, 423 compounds, 130 clusters, graded on replicate read T) | Estimate [95% CI] | Holm p | delta | Label |
|---|---|---|---|---|
| H1-D1 context selection (10 lines per compound): `rsd - raw` | **+0.118 [+0.084, +0.157]** | 0.0005 | 0.067 | **SUPPORTED** |
| H1-D2 candidate progression (16 compounds per line): `rsd - raw` | -0.008 [-0.037, +0.025] | 0.70 | 0.070 | NOT_SUPPORTED |

**Recommendation: REVISE** one specific assumption: that one Gaussian posterior with Gaussian pair-level noise serves
every decision. Keep the replicate-identified posterior for within-compound context selection and for calibrated value
estimates of selected candidates. Replace the Gaussian pair-level noise with a heavy-tailed model before using the
posterior again for cross-compound progression. Drop the knowledge-gradient planner (it never beat exploit-first) and
the chemistry prior for new classes (it hurt). Reasons and the next experiment are at the end.

## 1. Question and why it matters

About half of the selective-response variance in one PRISM read is replicate noise: the selective residual has replicate
correlation 0.52 (pre-protocol descriptive pass, `EVIDENCE_MAP.md`). Earlier MAESTRO work graded policies and failure
detectors against single noisy reads and kept finding overconfidence on *selected* actions (1.6-19x), failure signatures
at AUROC 0.5 (FAR) and active-learning gains that vanish. The question here: can a Virtual Cell posterior whose signal
and noise geometry is *identified from replicate plates of reference compounds* improve one-read decisions on new
compound classes, graded on a third replicate that no policy can read and on a separate screening run?

## 2. Mechanism and architecture

Borrowed core: Noise2Noise / Noise2Self from computer vision. Independent noisy copies identify the clean signal
without clean targets. Here, the covariance between two replicate reads identifies the covariance of the reproducible
signal: `S = sym Cov(r_B, r_T)`, `N = Cov(r_B - r_T)/2`.

```
 REFERENCE COMPOUNDS (historical; reads A, B, T)           NEW COMPOUND CLASS (query block)
 purged of any label / name / Tanimoto>=0.5 edge            one screening read A per compound (20 pool wells)
 to the query block                                                 |
   chemistry prior mu (kNN + kernel ridge, cross-fitted) --+        |   (prior used only if the inner
   residuals r_B, r_T around the prior                     |        |    selection chooses it)
   S = sym Cov(r_B, r_T) -> rank-q + diagonal              |        v
   N = Cov(r_B - r_T)/2, optional pool-block term (rho)    +--> VIRTUAL CELL: Gaussian posterior over 481 contexts
   per-activity-tier scales alpha_k, beta_k                |    mean m = mu + S_o (S_oo + N_oo/r)^-1 (y_o - mu_o)
   inner selection of (q, rho, prior, q_pca):              |    variance V, predictive variance of one new read
   input A -> target T, 5 cluster folds, decision utility -+        |
                                                                    v
                         SCIENTIFIC AGENT (deterministic; state = posterior per compound x context)
                           D1  choose 10 contexts per compound
                           D2  progress 16 compounds per context
                           D3  plan: buy replicate B for 25% of compounds (knowledge gradient | exploit-first | ...)
                               execute through Acquisition (counts reads and wells; T is never reachable)
                               verify each purchased read against the posterior predictive (mean z^2;
                               flag POSTERIOR_PREDICTIVE_MISFIT outside [0.67, 1.5]); update; decide
                                                                    |
                                                                    v
                         SEALED EVALUATOR: replicate read T (same run) and primary-screen read (other run)
```

Roles. The **Virtual Cell** is the response model: the chemistry prior plus a response geometry (which contexts respond
together, how noisy each read is, by activity tier). It predicts every context with a variance. The **Agent** holds the
state, plans and executes assay escalation under a well budget, verifies purchased reads against the posterior, and makes
the three decisions. No LLM is involved, because MAESTRO's matched LLM arms were null and nothing here needs language.

## 3. Literature, candidates, novelty

`LITERATURE.md` holds 23 verified sources with access level and preprint status. The closest work is:
- PerturbHD (decision-level evaluation of virtual cells; bioRxiv 2026).
- Rubbi et al. (probability-of-hit acquisition; ICML 2026 preprint).
- Active statistical inference and its robust version (Zrnic and Candès 2024; Li et al. 2025).
- Conformal selection (Jin and Candès).
- Bayesian hybrid shrinkage for the winner's curse (2026 preprint).
- Hierarchical HTS replicate shrinkage (2009).
- Data thinning and count splitting.

`CANDIDATES.md` compares three directions:
- A (this study): RSD.
- B: audit-calibrated selected-candidate risk.
- C: dose-condition transfer.

**Novelty claim (as tested):** no single ingredient is new. Disattenuation by replicate covariance, EB shrinkage, low-rank
denoising, honest noise splits and decision-level evaluation all exist. The contribution is empirical: the specific
combination for pooled viability screens, and a test of it by decision utility on an untouched replicate and on a
second run, across three decision types at matched read cost.

## 4. Design (frozen)

**Arena.** PRISM 19Q4 secondary, HTS002, 2.5 uM:
- 1,283 identity-audited compounds; 5 `AMBIGUOUS_STRUCTURE` refusals.
- 481 lines in 20 pools; ACH-001192 has no read, so 480 lines are informative.
- Each compound's three detection-plate replicates are assigned by salted hash to A (screening read), B (purchasable
  second read) and T (truth).

**Holdouts.** Families are built from all MoA labels (secondary and primary), shared name, and ECFP4 Tanimoto >= 0.5.
- Blocks: reference 424, search 215, selection 221, evaluation 423.
- Each block's references are purged of any direct edge to its queries.
- Evaluation tiers: 260 "strict" queries (component-isolated) and 163 "purged" queries (in the 509-compound giant
  component, edge-purged).

**Stages.**
- Search: development, headroom gate, practical threshold.
- Freeze.
- Selection: go/no-go, read once.
- Evaluation: read once.
- The configuration is chosen only inside the reference set, by replicate-split decision utility.

**Arms at matched cost.**
- One read (20 wells per compound): raw, scalar shrinkage, chemistry fusion, PCA denoising (established method, rank
  chosen by the same inner procedure), rsd and four ablations.
- Zero reads: VC-only.
- Two reads (40 wells): raw2, rsd2.
- D3 (25 wells): six escalation policies.

**Statistics.**
- Cluster bootstrap (4,000 draws), conditional on the fitted reference model and the fixed decisions.
- D2 re-selection bootstrap.
- Ten reference refits on 80% cluster subsamples.
- Holm over the two primary contrasts.
- Practical threshold delta = half the value of a second raw read on the search block.

## 5. Results

### 5.1 Headroom and the three blocks (graded on T)

| Contrast | Search (dev, 215) | Selection (221) | Evaluation (423) |
|---|---|---|---|
| `raw2 - raw` D1 (value of a second read) | +0.134 [+0.093, +0.179] | +0.176 [+0.130, +0.221] | +0.140 [+0.100, +0.186] |
| `raw2 - raw` D2 | +0.140 [+0.116, +0.166] | +0.183 [+0.144, +0.223] | +0.163 [+0.128, +0.211] |
| `rsd - raw` D1 | +0.081 [+0.035, +0.132] | +0.085 [+0.030, +0.150] | **+0.118 [+0.084, +0.157]** |
| `rsd - raw` D2 | +0.023 [-0.007, +0.057] | +0.031 [-0.003, +0.074] | -0.008 [-0.037, +0.025] |
| inner choice (q, rho, prior) | 3, 0, off | 2, 0, off | 2, 0, off |

The D1 gain held up in all three blocks. The D2 gain never reached delta in any block.

### 5.2 Evaluation block: utility, hits, false progression, cost

| Arm | Wells / compound | D1 utility | D1 hit rate | D1 false progression | D2 utility | D2 hit rate | D2 false progression |
|---|---|---|---|---|---|---|---|
| vc_only (chemistry prior) | 0 | 0.143 | 0.168 | 0.466 | 0.104 | 0.141 | 0.486 |
| raw | 20 | 0.851 | 0.410 | 0.251 | 1.041 | 0.508 | 0.189 |
| shrink | 20 | 0.851 | 0.410 | 0.251 | 1.021 | 0.505 | 0.198 |
| fusion | 20 | 0.838 | 0.403 | 0.260 | 1.025 | 0.507 | 0.199 |
| pca | 20 | 0.763 | 0.367 | 0.237 | 0.831 | 0.421 | 0.247 |
| **rsd** | 20 | **0.973** | **0.428** | **0.170** | 1.033 | 0.503 | 0.191 |
| raw2 | 40 | 0.996 | 0.460 | 0.206 | 1.204 | 0.570 | 0.154 |
| rsd2 | 40 | 1.080 | 0.476 | 0.149 | 1.183 | 0.563 | 0.156 |

Utility is the mean killing `-s_T` of the chosen pairs. A hit is `-s_T >= 1`. False progression is a chosen pair with
`s_T > 0`.

- **D1 at half the cost.** At 20 wells, `rsd - raw2` (40 wells) is -0.023 [-0.071, +0.021]: one read through the
  posterior is statistically indistinguishable from two raw reads. It recovers 85% of the second read's value (halfway
  contrast +0.048 [+0.013, +0.083]). False progression drops from 0.251 to 0.170, which is lower than with two raw reads.
- **Block cost.** One read is 423 reads and 8,460 wells. Two reads are 16,920 wells. D3 is 529 reads and 10,580 wells.
- **Compute.** The evaluation stage (inner selection over 30 configurations x 5 folds, all arms, bootstraps, D3,
  sensitivity) took 1,161 s on a desktop CPU. No GPU, no paid call, no LLM.

### 5.3 Secondary hypotheses (evaluation block)

| ID | Contrast | D1 | D2 |
|---|---|---|---|
| H2 | `rsd - pca` (established denoiser) | +0.215 [+0.171, +0.258] | +0.202 [+0.159, +0.250] |
| H2 | `rsd - rsd_totalgeom` (one-read covariance instead of replicate identification) | +0.051 [+0.025, +0.077] | -0.020 [-0.045, +0.002] |
| H3 | `rsd - rsd_priorflip` (adding the chemistry prior) | +0.050 [+0.026, +0.076] | -0.000 [-0.018, +0.021] |
| -- | `rsd - rsd_poolflip` (adding the pool-block noise term) | +0.049 [+0.031, +0.067] | +0.034 [+0.013, +0.052] |
| -- | `rsd - rsd_notier` | +0.017 [-0.001, +0.034] | +0.001 [-0.034, +0.048] |
| -- | `rsd - fusion` / `rsd - shrink` | +0.136 / +0.118 | +0.008 / +0.012 (ns) |
| -- | `rsd2 - raw2` | +0.086 [+0.056, +0.116] | -0.021 [-0.042, +0.004] |
| H6 | cross-run, primary screen: `rsd - raw` | +0.090 [+0.062, +0.116] | -0.007 [-0.034, +0.021] |
| H6 | cross-run: `raw2 - raw` / `rsd - raw2` | +0.095 / -0.005 [-0.044, +0.032] | +0.097 / -0.104 |

- **H6 (cross-run).** The D1 result transfers to the independent screening run: on that run, one read through the
  posterior equals two raw reads.
- **H2 (replicate identification).** For D1, replicate-identified geometry beats total-covariance geometry. PCA
  denoising, the established method, is worse than raw reads for both decisions.
- **H3 (chemistry prior).** Every reference set preferred the model without the chemistry prior. On new classes, the
  chemistry prior alone is weak (VC-only D1 0.143 against 0.851 for one read), and adding it hurts by 0.050.
- **Identity tiers (D1).** Strict queries gain +0.135 [+0.098, +0.169] and purged (giant-component) queries +0.091
  [+0.031, +0.188]. On the primary run, the figures are +0.087 and +0.094.

### 5.4 Calibration and selected-candidate optimism (H5)

80% predictive coverage is 0.797 over all pairs and 0.675 over D2-selected pairs (mean z +0.07). The table shows the
claimed value minus the observed value for the 16 x 480 pairs each arm selects:

| raw | raw2 | pca | fusion | shrink | rsd2 | **rsd** |
|---|---|---|---|---|---|---|
| +1.083 | +0.801 | +0.544 | +0.254 | +0.206 | +0.119 | **+0.069** |

The posterior's claims about the candidates it selects are nearly unbiased (claimed 1.10, observed 1.03): 94% of the raw
read's winner's curse is gone. Its intervals on the selected pairs are still too narrow (coverage 0.675 against 0.80).
Section 6 traces this to heavy tails.

### 5.5 Escalation (D3, H4; +25% reads, 25 wells per compound)

| Policy | none | random | uncertainty | exploit_first | voi_kg | raw_exploit_first |
|---|---|---|---|---|---|---|
| D2 utility | 1.033 | 1.069 | 1.108 | 1.119 | 1.120 | 1.125 |

- **KG against exploit-first:** `voi_kg - exploit_first` = +0.001 [-0.014, +0.015].
- **Escalating at all:** `voi_kg - none` = +0.087 [+0.054, +0.128].
- **Posterior against the conventional workflow:** `exploit_first - raw_exploit_first` = -0.006 [-0.043, +0.045].

Buying a second read is valuable. Neither the knowledge-gradient planner nor the posterior adds anything over the
conventional rule "re-read the current top candidates". The agent's verification raised no flag: posterior-predictive
mean z^2 was 1.12-1.43 for every policy. Yet the selected pairs are under-covered, so the [0.67, 1.5] band is too wide to
catch this failure.

### 5.6 Sensitivity

- **D2 re-selection bootstrap:** -0.002 [-0.026, +0.021].
- **Ten reference refits on 80% of clusters:** D1 +0.097 to +0.110 (SD 0.005); D2 -0.019 to -0.005.

The D1 gain does not hinge on a lucky reference set, and the D2 null holds under refitting.

## 6. Diagnosis of the D2 failure (EXPLORATORY, post hoc; `diagnose_d2.py`, `DIAGNOSTIC_D2.json`)

Established on these data:
- **Noise is heavy-tailed.** The replicate difference has excess kurtosis 3.2 and |z| > 3 in 1.35% of pairs (Gaussian:
  0.27%).
- **D2 picks land on the outliers.** D2 picks the extreme pairs. Among raw D2-selected pairs, 9.9% carry a screening-read
  error above 3 SD (1.5% over all pairs). Their mean error is -1.08, which is the winner's curse.
- **The error is pair-level.** A compound-level offset explains 0.6% of the selected-pair error.
- **Picks are spread out.** D2 picks cover 387 of 423 compounds.
- **Geometry transfer is not the bottleneck.** Fitting the geometry on the evaluation block itself (two-fold cross-fit)
  is worse than the reference geometry: D1 +0.073 against +0.128, D2 -0.006 against +0.017 at q = 2. Larger q is worse
  for both.

Interpretation, a diagnosis rather than a tested claim:
- **Why D1 works.** D1 compares contexts within one compound. A rank-2 response geometry with tier-scaled noise pools
  information across a compound's 480 contexts and down-weights inconsistent ones.
- **Why D2 does not.** D2 compares compounds within one context, and its winners are the most extreme single pairs. To
  a Gaussian low-rank model, a real line-specific hit and a single-well outlier look alike: both are off the low-rank
  axes. So it shrinks them alike and cannot reorder them. Only a second physical read separates them, which is why
  `raw2` and D3 escalation help D2 so much.
- **Untested.** Whether a heavy-tailed pair noise model (Student-t or outlier mixture identified from the replicate
  differences) would recover D2 has not been tested.

## 7. What is demonstrated, what is not, what is future

**Demonstrated (development grade, one assay, one dose):**
1. A replicate-identified low-rank posterior improves within-compound context selection on new compound classes by 0.118
   killing units, beyond the pre-registered practical threshold. It matches two raw reads at half the wells, on both the
   held-out replicate and an independent screening run. It cuts false progression from 25% to 17%.
2. Its value claims for selected candidates are nearly unbiased (optimism +0.07 against +1.08 for raw and +0.80 for two
   raw reads).
3. Replicate identification matters: the total-covariance geometry and PCA denoising are worse.

**Not supported:**
- Candidate progression (D2) at one read.
- The knowledge-gradient escalation planner over exploit-first.
- Any benefit of the posterior inside escalation over the raw re-read rule.
- The chemistry prior for new classes.
- The pool-block noise term.
- Interval calibration on selected pairs (0.675).
- Breadth: one of the three decision settings benefited, not two.

**Plausible but not demonstrated:**
- **Other assays with replicates.** Any assay with at least two replicate reads on a few hundred reference compounds
  in the same panel layout could host the same core, e.g. L1000 replicate plates or Perturb-seq guide replicates.
- **Dose choice.** Condition selection over doses (fallback C).
- **Risk audits.** Audit-based progression risk (fallback B). The protocol did not trigger it, because selected-pair
  coverage fell below 0.70.

**When the simpler workflow is preferable:**
- For progression, take one raw read and re-read the top candidates.
- When a second read costs little, two raw reads equal the posterior for D1.

**Deployment needs:**
- Replicate reads on reference compounds in the same assay and pool layout.
- A held-out replicate or run for monitoring.
- At least 10 reference compounds per activity tier.

## 8. Independence and limitations

- **Exposed data.** All data are exposed PRISM 19Q4. This study's selection and evaluation blocks were read once each,
  under the freeze, but earlier MAESTRO studies used the same compounds and replicate plates. This is development
  evidence, not independent confirmation.
- **Pre-protocol exposure.** The pre-protocol descriptive pass saw replicate agreement in all partitions. The search
  block informed the design (`DEVELOPMENT_LOG.md`: defect fixes, grid extension, prior toggle, baseline repair).
- **Intervals are conditional.** They condition on the fitted reference model and on the chosen pairs. Re-selection and
  refit analyses are reported separately.
- **Shared plates.** Replicate plates share compound plate and pool. Noise common to all three reads is invisible to
  both the method and the grader. The primary-screen run guards against this partly: it has a different compound plate
  and run, but different handling.
- **Scope.** One dose (2.5 uM), one screen (HTS002). Utility is in log2 fold-change units of selective killing; no
  monetary price exists.
- **Bootstrap p-values.** p-values are percentile-bootstrap tails, and the minimum attainable is 1/4001.

## 9. Recommendation and next experiment

**REVISE.** What to keep and what to change:
- Keep the replicate-identified posterior for context selection and for calibrated value estimates.
- Revise the pair-level noise assumption (Gaussian to heavy-tailed) before any further claim for progression decisions.
- Retire the knowledge-gradient planner and the chemistry prior for new classes in this setting.

Why not ADVANCE: the core helped one decision type, not the two the brief requires. Its intervals are too narrow exactly
where decisions are made.

Why not RETIRE: the D1 effect held up in three blocks and on a second run. It equals a second read at half the wells.
The selected-candidate optimism fix (94%) answers the most recurrent failure in MAESTRO's history.

What remains unknown:
- Whether the D1 effect survives on compounds that were never exposed.
- Whether it survives at other doses and screens.
- Whether a heavy-tailed noise model fixes D2 and the selected-pair coverage.
- Whether the agent's verification can be made sensitive to selected-pair misfit, e.g. a band on selected pairs only.

**Next experiment most likely to change the decision:**
1. On the existing arena, fit a heavy-tailed pair-noise posterior. Use reference-only selection, as here.
2. Freeze it before running anything else.
3. Test D1 and D2 and selected-pair coverage on an unopened tier. Locally, the 0.625 uM and 10 uM HTS002 reads of the
   same compounds were not used by this study. They are same-compound evidence, so this is a development check only.
   For independence, use PRISM 24Q2, which needs the owner's authorisation.

A D2 gain above delta, with coverage restored, would turn REVISE into ADVANCE. A D1 loss on the new tier would argue
for RETIRE.
