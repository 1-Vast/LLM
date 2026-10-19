# Three candidate directions and the selection

Common setting: drug x cellular context x assay x condition -> research decision. Local data: PRISM 19Q4 secondary
HTS002 (1,283 audited compounds x 481 lines x 8 doses x 3 replicate detection plates), PRISM primary (independent run),
L1000, Beat AML. All exposed; development evidence only.

## A. Replicate-identified Virtual Cell posterior for noise-aware decisions (RSD) - PRIMARY

* **Problem and consequence.** About half of the selective-response variance in one screen read is replicate noise (pre-
  protocol pass: selective replicate r = 0.52). Policies are learned and graded against single reads, so (i) selected
  candidates are optimistic (winner's curse; MAESTRO saw 1.6-19x overconfidence on selected actions), (ii) "VC failure"
  labels are largely unpredictable noise (FAR AUROC 0.5), (iii) false progression and wasted confirmation wells.
* **Borrowed mechanism.** Noise2Noise / Noise2Self (vision): independent noisy copies identify the clean signal; the
  cross-replicate covariance equals the signal covariance; a denoiser can be selected without clean targets.
* **Why direct transfer fails.** Replicate plates share compound plate and pool (noise not fully independent); pooled
  wells correlate noise within a pool; noise depends on compound activity; decisions are discrete top-k selections on a
  contrast (selective residual), not pixel regression; novel mechanism classes need not share the reference geometry.
* **New component.** (1) Reference-only identification of signal and noise covariance of the *residual around the VC
  chemistry prior* from two replicate reads, with activity tiers and an optional pool-block noise term; (2) the denoiser's
  configuration chosen by replicate-split decision utility *inside the reference set* (input read A, target read T), so no
  query outcome tunes it; (3) one posterior shared by three decisions; (4) an escalation agent that buys a second read by
  knowledge-gradient value and checks each purchased read against the posterior predictive (named inadequacy flag);
  (5) grading on a replicate read that no policy can access, plus a cross-run (primary screen) check.
* **Closest approaches / remaining difference.** EB/HTS shrinkage (scalar per compound or variance-moderated statistics),
  low-rank matrix denoising (PCA/soft-impute), MAESTRO program revision's Bayesian probe updating (low-rank ALS covariance,
  diagonal replicate noise), PerturbHD decision-level evaluation, data thinning. Difference: covariance *identified* from
  replicate cross-moments around a chemistry prior, selected by a replicate-split decision objective, and evaluated by
  decision utility on an untouched replicate across three decision types. This is a combination of known ingredients;
  the claim is empirical usefulness, not a new estimator.
* **Hypothesis (falsifiable).** At equal cost (one read per compound), the RSD posterior improves context selection (D1)
  and candidate progression (D2) graded on the held-out replicate, by at least half the value of buying a second read.
* **Data / implementation / failure modes.** Secondary HTS002 2.5 uM triples; ~300 lines of NumPy. Failure modes: no
  headroom (a second read does not help), novel classes outside the reference geometry, non-PSD noise estimates,
  shared-plate noise inflating apparent signal, D2 comparisons across compounds dominated by activity.
* **Decisive small experiment.** Search block: headroom gate (raw two reads vs one read on T); if a second read helps,
  does a one-read posterior recover >= half of it? Run in minutes.

## B. Audit-calibrated selected-candidate risk under one-sided feedback - FALLBACK 1

* **Problem.** VC-guided progression decisions are overconfident on selected candidates and calibration does not transfer
  across campaigns (Platt slope .45 vs .80); only progressed candidates are ever confirmed (selective labels).
* **Borrowed mechanism.** Active testing (Kossen et al.) and active statistical inference (Zrnic & Candès): randomised,
  importance-weighted audits give unbiased risk estimates with a model as control variate; conformal decision theory
  (robotics) calibrates the decision rule online.
* **Why direct transfer fails.** Audit labels cost wells; exchangeability fails across mechanism classes; outcomes are
  replicate-noisy so "false progression" itself must be defined on a de-noised quantity.
* **New component.** Randomised audit of a fixed fraction of both progressed and rejected candidates, with the RSD
  posterior as control variate and replicate-identified noise removed from the risk estimate.
* **Closest.** Weighted conformal selection (Jin & Candès), Bayesian hybrid shrinkage, KnowNo. Difference: design-based
  validity from the agent's own randomisation rather than calibration-set exchangeability.
* **Hypothesis.** On a new block, the audit estimator's false-progression estimate is within +/-0.05 of the replicate-graded
  rate using a 10% audit, while the model's own estimate is off by more than 0.10.
* **Decisive experiment.** Requires only the RSD posterior and the selection block. Failure modes: too few audits per
  campaign (variance), shared-plate noise.

## C. Dose-condition transfer through cross-dose replicate geometry - FALLBACK 2

* **Problem.** Primary screens use one dose; the selective window of a compound may lie at another dose. Choosing the
  confirmation dose is a real decision (condition selection) with no tested method in MAESTRO.
* **Borrowed mechanism.** Equivariance / compositional generalisation in vision (log-dose shift as translation) and
  value-equivalent models (predict only what the dose decision needs).
* **Why direct transfer fails.** Hill slopes and efficacy vary by line and mechanism; doses are coarse (4-fold); curves
  are noisy; pan-toxicity at high dose removes selectivity.
* **New component.** Cross-replicate covariance between doses (identified from replicate plates at two doses) gives the
  transfer operator from a read at 2.5 uM to the selective profile at another dose.
* **Closest.** chemCPA/CPA dose models (transcriptional), dose-specific growth-inhibition predictors for unseen lines.
* **Hypothesis.** A 2.5 uM read plus the cross-dose operator chooses lines at 0.625 uM better than the raw 2.5 uM read.
* **Decisive experiment.** Same arena, other doses of the same plate. Failure modes: different compound wells per dose,
  missing doses, small selective signal at low dose.

## Trade-offs and selection

| Criterion | A (RSD) | B (audit risk) | C (dose transfer) |
|---|---|---|---|
| Novelty | Moderate: known ingredients, new combination and decision-level replicate grading | Moderate: design-based audits are known; biology-specific one-sided feedback | Moderate-high in MAESTRO; dose models exist elsewhere |
| Scientific importance | High: decides whether earlier "model failure" signals were noise | Medium-high: progression risk control | Medium: one condition axis |
| Practical use | Direct: one read instead of two, fewer false progressions | Direct for go/no-go governance | Direct for confirmation dose choice |
| Breadth | Three decisions from one posterior | Any go/no-go decision | Condition decisions only |
| Data suitability | Best: replicate triples for all 1,283 compounds | Good, but audits shrink usable n | Fair: dose wells differ, missing doses |
| Testability now | Minutes, with a headroom gate | Needs A's posterior | Needs extra loading and new truth definition |

**Selected: A**, because it addresses the bottleneck the evidence points to (noise, selected-candidate optimism), it has a
cheap decisive gate, and both fallbacks reuse its posterior. B is the first fallback (it tests a different value claim of
the same posterior: risk estimation rather than ranking). C is the second fallback and is explicitly out of scope unless
A's posterior is adequate.

## Roles of the two cores in A

* **Virtual Cell** represents the selective response of a compound across 481 contexts as a Gaussian posterior: a
  chemistry prior mean (Tanimoto kNN + kernel ridge on purged references) and a response geometry (signal and noise
  covariances identified from replicate plates of reference compounds, by activity tier). It predicts every line,
  including lines missing from the read, with a predictive variance.
* **Scientific Agent** (deterministic, no LLM) holds the research state (posterior per compound x line), plans assay
  escalation under a well budget by knowledge-gradient value for the progression decision, executes reads through an
  accounting interface, verifies each purchased replicate against the posterior predictive (mean z^2; named flag
  `POSTERIOR_PREDICTIVE_MISFIT` when outside [0.67, 1.5]), and makes the final context and progression decisions.
* **Interaction.** The VC's replicate-identified uncertainty is what makes the agent's VOI meaningful (earlier VOI failed
  with uninformative uncertainty); the agent's purchased replicates are the VC's adequacy test on the new block.

## Precise novelty claim (to be tested, not assumed)

"For pooled viability screens, identifying the signal and noise covariance of the residual around a chemistry prior from
replicate cross-moments, selecting the resulting posterior by replicate-split decision utility on reference compounds,
and grading three research decisions on an untouched replicate, improves one-read decisions over raw reads, scalar
shrinkage, fixed fusion and PCA denoising at equal cost." Closest competitors: EB/variance-moderated HTS shrinkage,
low-rank denoising, PerturbHD-style decision evaluation, MAESTRO's Bayesian probe updating, data thinning.
