# Recommended single primary diagnostic

Status: PRE-RESPONSE DESIGN; not run and not independently reviewed. All choices below precede count access. This document proposes one necessary-model check, not a new algorithm or a test that identifies molecular killing.

## Question and decision

Within the fixed seven HTS001 vehicle plates and their observed t<72h grids, does one added smooth curvature parameter improve prediction of untouched well means over a common exponential raw-count mean? A stable heldout improvement blocks the constant-r mean premise needed for the parent's covariance-to-rate interpretation in this nominal regime. Otherwise the premise remains unrefuted or inconclusive; white observation noise, latent Markov structure, culture independence and drug-specific applicability remain untested. No outcome authorizes latent birth/death interpretation.

The baseline hypothesis is a necessary implication of common homogeneous net growth plus zero-mean observation error, not the entire model: m_c(t)=A_c exp(r_c(t-t_c0)). Random starting counts are permitted if their average preparation is shared by training and validation wells. Common plate effects are conditioned on. Time-dependent observation bias, density dependence, changing composition, varying net rates or phase transients can break the implication. Pure serial zero-mean noise can escape this check completely.

## Data roles fixed from metadata

- Cells/plates: BR1, DS3, DS7, DS8, DS9, MGH, PC9; exactly one named plate per cell. Every plate has both columns02/23 and rows B–O, 28 controls. Controls only; drug-response count fields must never be accessed.
- Training: rows B,D,F,H,J,L,N, both control columns, 14 whole trajectories per plate. Validation: rows C,E,G,I,K,M,O, both columns, 14 whole trajectories. This balances columns and retains each row pair in one role. No role reversal or alternative split after inspection.
- Window: all and only observed t<72h, including each first frame. Counts remain on their original scale; retain exact irregular times. No log-count response, frame interpolation, time binning, well-specific normalization, first-frame conditioning, heldout amplitude fitting, outlier deletion or response-dependent censoring.
- The metadata shows 9–15 frames in this window. The seven plates receive equal weight; the observed frames within a plate receive equal weight. This estimates observed-grid prediction, not an integral over equally spaced time or a population of cultures.
- Fixed split exchangeability is an explicit working condition: training and validation rows must represent the same mean preparation conditional on plate. Alternating rows mitigates a simple positional imbalance, but cannot certify this condition or eliminate spatial correlation. A row gradient or shared acquisition artifact is a rival explanation, not a biological discovery.

## Estimation and one primary statistic

For plate c, J_c is its number of eligible frames, t_c0 the first eligible time, T_c the last minus first eligible time, and u_ci=(t_ci-t_c0)/T_c. T_c>0 is already metadata-checkable. Let ybar^T_ci and ybar^V_ci be arithmetic means of the 14 training and validation counts at frame i.

Fit separately on each training mean vector, by unweighted nonlinear least squares on RAW counts:

    m0_c(u)=exp(beta0_c + beta1_c*u)
    m1_c(u)=exp(gamma0_c + gamma1_c*u + gamma2_c*u^2).

The rival adds only gamma2. It represents increasing or decreasing instantaneous log growth, not a chosen biological mechanism. The baseline rate is rhat_c=beta1_c/T_c. A nonzero gamma2 is not a separate primary test. Fits use exactly the same training frames; all train data are unavailable to the validation scorer except through fitted predictions and scale. No validation value estimates any nuisance parameter.

Set s_c^2=(1/J_c) sum_i (ybar^T_ci)^2. Define

    D_c = [sum_i {(ybar^V_ci-m0hat_c(u_ci))^2
                  -(ybar^V_ci-m1hat_c(u_ci))^2} / J_c] / s_c^2
    Delta = (1/7) sum_c D_c.

Positive Delta favors curvature. This normalization is fixed by training magnitude, not fitted residual variance; it prevents a high-count plate from setting the entire question. It adds no pseudocount and no biological effect cutoff. Comparing mean squared errors of the 14 individual heldout well vectors gives exactly the same difference, because the within-frame heldout variance cancels. Neither formulation treats intervals or frames as independent replicates.

The precise estimand, conditional on a training set and the specified mean preparation, is the equally weighted seven-plate difference in expected observed-grid normalized squared prediction loss for a new control well from that same preparation. Delta is its heldout plug-in estimate. With fixed finite plates and uncertified row dependence, it is primarily a descriptive operational comparison; it is not automatically a consistent estimator for a biological population. The additional curvature parameter is learned only on training wells, so an apparent training fit gain cannot alone make Delta positive.

## Minimal numerical contract

Use existing local numerical dependencies only. Scale counts by a training-only positive count magnitude during optimization, and undo that scaling for predictions; this must be algebraically the same raw-count objective. Fit exp(linear/quadratic) directly to the arithmetic means. A log of a positive training mean may initialize an optimizer, but must not change the response/objective. If needed for zeros, initialize baseline from a flat positive training mean and beta1=0; never add a pseudocount to a response.

Baseline start: intercept log(mean_i ybar^T_ci), slope0. Rival start: converged baseline intercept/slope, curvature0. Use deterministic double-precision nonlinear least squares, maximum200 objective/Jacobian evaluations per fit, with solver's documented convergence criteria recorded. No response-driven model or bound changes. Nestedness supplies a numerical check: the rival's training objective must not exceed the baseline's beyond documented floating-point tolerance. Record the solver, its defaults, status, objective and parameters. A failed convergence, nonfinite prediction, zero training scale, or unresolved nestedness violation makes the scientific comparison INCONCLUSIVE; do not drop that plate/draw or add starts until a desired answer appears. This is a numerical safety rule, not proof of a global optimum. An independent verifier should check the two fitted functions and primary-score arithmetic, and flag material optimizer ambiguity rather than silently repair the scientific specification.

## Nuisance uncertainty and conditional stability

Use B=500 row-block bootstrap draws, fixed seed20261029 and a recorded generator. Within each cell and role, sample seven row labels with replacement from that role's seven rows, retaining both column trajectories and their full temporal vectors for each selected row. Resample training and validation roles independently; keep plates fixed and never resample isolated frames. On EVERY draw recompute both training mean vectors, all baseline and rival parameters, s_c^2, heldout means, D_c and Delta. Thus baseline-rate/amplitude uncertainty, rival-selection estimation cost, scale uncertainty and heldout sampling variability are carried through the calculation. Holding rhat fixed would omit a material nuisance.

Report the original Delta, all seven D_c, the empirical 5th/95th percentiles of Delta*, and the sign fraction #{Delta*>0}/500. The one-sided 5th percentile is a conventional descriptive stability summary, not a calibrated 95% biological confidence bound or a p-value. Seven row blocks per role are small; no power assertion is made. Whole-row resampling retains within-well serial noise and within-row correlation but does not capture arbitrary cross-row spatial dependence, plate-to-plate acquisition noise, culture-to-culture variability, unknown nesting or shared time-dependent artifacts. With one plate per cell, a biological interval is unavailable. Do not describe many frames or 196 wells as 196 independent cultures.

The resource ceiling remains CPU120s/wall180s/working set512MiB per process, cooperatively measured. If 500 valid draws cannot complete, or any material numerical ambiguity remains, report incomplete stability and INCONCLUSIVE. Do not spend the run budget repeating a selected subset, increasing thresholds, or dropping failures.

## Frozen outcome interpretation and stop rule

1. If the empirical 5th percentile of Delta* is strictly positive and numerical checks pass: record CONDITIONAL HELDOUT CURVATURE GAIN. This is evidence against using the common exponential mean as the default model for the seven-plate average observed-grid prediction task, conditional on the split and row-block resampling scheme. Stop homogeneous covariance-to-rate interpretation in this regime. The result cannot distinguish density, temporal growth changes, heterogeneous rates, common imaging bias or spatial preparation differences. Per-cell scores locate contributions only; they do not license seven individual hypothesis claims.
2. If the empirical 95th percentile is strictly negative and numerical checks pass: record EXPONENTIAL PREDICTION PREFERRED FOR THIS COMPARISON. The one simple curvature rival did not beat the baseline under this conditional assay comparison. Do not call the homogeneous/white-noise model validated or claim a rate-calibration result.
3. If the stability interval contains zero, point/stability signs conflict, metadata eligibility fails, or numerical/resource checks fail: record INCONCLUSIVE. A finite noisy control collection has not resolved this necessary mean question; failure to reject is not equivalence. Retain the uncertainty and stop mechanistic promotion.

All three branches end this single diagnostic. Residual covariance tests, autocorrelation tests, alternative horizons, extra mean models and parameter sweeps are NOT RUN in this pilot. Any later covariance study needs a separately specified, reviewed question; sufficient independent preparation information; a mean estimator with propagated uncertainty; and explicit serial-observation and heterogeneous-growth rivals. There is no justified transition from outcome2 directly to biological rate feedback.

## Source grounding and limits

Parent root_derivation.md proves the residual-covariance identities only for the correct common exp(rh) transition factor, uncorrelated latent innovations and independent white observation error; it already states estimated factors need separate wells or propagated uncertainty. Wu2025 DOI10.1038/s41540-025-00560-8, original published-primary passages Sec27–29 (saved evidence_worker/wu_covariance_exact_passages.json with source hash) explicitly writes additive N(0,c^2 I) observation error and a full multitime covariance CLT likelihood, and notes aggregate heterogeneous counts are not Markov. Thus ordinary multitime inference is the strong prior; the present gate is not a methodological novelty.

BESTDR primary JATS evidence_worker/p5_bestdr.xml, s2-1, relies on Markov/time-homogeneous trajectory transitions and on count variance for otherwise unidentifiable parameters. Its s4 discussion acknowledges observation noise can inflate inferred rates and cannot be fully disentangled, and that phase transients can violate exponential waiting-time assumptions. These original statements motivate a prerequisite check; they do not establish its outcome in HTS001. The planned quadratic mean curve is an ordinary diagnostic rival, not a verified biological mechanism.

No count has been read by this worker. No empirical finding, white-noise conclusion, drug-selection advantage, independent validation or new co-learning algorithm is claimed.
