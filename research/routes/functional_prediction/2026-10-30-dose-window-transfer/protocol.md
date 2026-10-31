# C2 prediction protocol v1: fixed-anchor dose-window choice

Status: frozen initial proposal for independent challenge, before new model fitting. Read with candidate.md and brief.md. HTS001 is already exposed development data. HTS031 treatment counts remain unread and are not admitted to this first matrix.

## Measurement and information

Use the parent's authenticated census_c_wells.csv, derived from HTS001 sha256 e6ff575664705d6021d98e1dad41751c87d86a425a3794f7e2a7e3b12468d617. The outcome y is log2[N(60)/N(24)] minus the plate vehicle median of that log growth. All interpolation brackets are before72h. Measurement availability is the last bracketing image, which can be later than60h; do not claim real-time60h availability. Six backgrounds remain after the original metadata-driven MGH exclusion. Keep the original endpoint and technical-well mapping; no new endpoint search.

Each background has14 compounds,10 physical molar doses and2 technical wells per condition. Sort each compound's dose grid ascending. Calibration anchors are zero-based indices1 and8, fixed by metadata, not selected from outcomes. Queries are indices2 through7 inclusive, strictly inside the observed anchor interval. The two endpoint conditions, all vehicle wells and known historical full curves are available to every model. Unmeasured target outcomes are available only for scoring. Two anchors are20% of the10-dose conditions and one third of the six queried interior conditions, per compound. These are condition counts, not certified assay-cost savings: controls, imaging, source collection and plate constraints still cost resources. For a one-dose decision, direct measurement may be cheaper.

Keep a known14-drug library with common grids across backgrounds; this is prediction of unmeasured drug-dose/background combinations for compounds observed historically. It is not unseen-chemical-identity or unseen-scaffold generalization. Both well endpoints are averaged for calibration. Predictions are compared with the same two-well query mean; also score each technical pseudo-replicate separately without refitting. One plate per background and shared PC9 ancestry prevent interpreting six background folds as six independent preparations.

## Candidate and rivals

Use the exact anchored equation in candidate.md. For each source background and drug form D=y(b)-y(a), u=(log10dose-a)/(b-a), r=y(x)-y(a)-uD. Fit drug-specific q(x)=sum(D*r)/(sum(D^2)+lambda*n*0.25^2), where n is the number of fit backgrounds. If the denominator is below1e-12 use q=0. Query prediction is A+uD+Dq. Lambda grid is[0,.01,.1,1,10]. All q and all other fitted quantities come from fit backgrounds alone. This is ordinary shape-invariant regression; no new algorithm, causal mechanism or simulator claim is licensed.

The complete fixed panel is:

1. Source mean curve: no calibration use, a difficulty diagnostic.
2. Target log-dose linear interpolation between the two anchors; no source responses needed.
3. Source additive anchored shape: source mean r(x), added to target anchor interpolation.
4. Candidate drug-specific anchor-scaled shape.
5. Pooled normalized shape, fitted through the origin across all drugs at each normalized dose position; same lambda grid. This tests whether drug-specific shape is needed.
6. Full anchored ridge: predict r(x) from[1,A,D] separately for each drug/dose, standardize A,D from fit rows, intercept unpenalized, ridge grid[.01,.1,1,10,100]. Add target linear interpolation. This relaxes the candidate restriction.
7. Full joint response-profile covariance conditioning: source vector is all14x10 mean responses, observed indices are every drug's two anchors. Use sample covariance plus diagonal observation regularization tau*global_fit_variance, tau grid[.001,.01,.1,1,10]; predict the posterior conditional mean. Global variance is mean squared centered fit entries, floored at.01. Use an algebraically equivalent small dual solve if helpful; no low-rank truncation.
8. Per-drug smooth GP: source mean curve plus an RBF residual GP conditioned on that drug's anchors. Amplitude is the mean source variance for that drug, floored at.01; length-scale grid[.5,1,2] in log10-molar units and noise/amplitude ratio[.001,.01,.1,1]. Exact Gaussian conditioning, no additional target observations.
9. Regularized3-parameter Hill curve: f(x)=-E/(1+exp(-ln(10)*h*(x-e))). Fit every source drug/background curve with bounded nonlinear least squares; define the drug-specific mean and diagonal variance of theta=(logE,logh,e), variance floored at.25. Target MAP minimizes the two anchor squared errors divided by global fit variance plus lambda times standardized parameter distance to the source mean; lambda grid[.01,.1,1,10]. Bounds E in[.001,10], h in[.1,5], e in[source_min_logdose-2,source_max_logdose+2]; initialize source fits at E=max(.1,-min(y)),h=1,e=median(logdose), max200 function evaluations, and target at the clipped source mean. A reported optimizer failure uses the source-prior Hill curve and is counted; never remove difficult tasks after fitting.
10. Source-neighbor anchored curve: fit-scale each of the28 anchor features by source standard deviation floored at.1; softmax weights exp(-mean_squared_anchor_distance/tau), tau grid[.1,1,10]. Average historical r(x) with those weights and add target anchor interpolation. This is ordinary response-profile prediction.
11. Same-information gradient-boosted trees: predict query y from drug one-hot, logdose,u,A,D,source_mean_y(x), and the complete28-dimensional anchor profile. Source means exclude the target background in the current fit. HistGradientBoostingRegressor, squared error,50 iterations, learning_rate=.1, max_depth in[2,3], min_samples_leaf in[5,10], l2_regularization=1, random_state1031, early_stopping=False. The same source/target measurements as all other models are permitted.
12. Wrong-drug shape diagnostic: reuse the candidate lambda and source q, rotate drug-specific q between sorted drug names within identical normalized-dose grids (one-place rotation, deterministic). Apply the target's A,D. This is a diagnostic, not an additional optimized rival.

If a named panel method cannot execute, retain the execution failure; the continuation gate is INCONCLUSIVE, not a reduced-panel pass. Resource/implementation failure is distinct from scientific rejection.

## Fitting and fixed evaluation

Outer leave-one-background-out creates six prediction folds. Within the five remaining backgrounds, choose every model's hyperparameters by inner leave-one-background-out mean pair-choice regret (four fit backgrounds, one validation background), with all source means, scales, q, covariance and Hill priors recomputed inside the fit. Candidate and all rivals receive exactly the same fixed target calibration conditions. Ties between configurations follow the listed order; predictions tied between drugs choose the lexicographically earlier name. No tuning on an outer prediction or changing the grids after results.

An eligible comparison is an unordered drug pair at an exact same physical molar query concentration for both drugs, with complete two-well endpoints. The roster is metadata-defined and identical across methods. For each pair/dose, choose the compound with smaller predicted y and incur regret y_chosen-min(y_first,y_second). The primary aggregate averages doses within a drug pair, pairs within a background, then the six backgrounds equally. Regret0 is an oracle lower bound. Report actual pair/dose and background denominators, every method's six losses, MSE as secondary, and target-calibration/query condition counts.

Secondary utility: at each physical query concentration containing at least two drugs, choose the single best predicted drug and report growth-unit regret against the best observed member of that fixed menu, averaging concentrations within backgrounds. Report actual complete menus. This guards against a pairwise gain that harms the final compound choice.

Secondary phenomenon: a predicted flip requires at least one pair/query contrast>=.25 and one<=-.25. The observed technical flip requires both same-index well contrasts beyond the same opposite margins, and all cross-well signs agreeing at witnesses, as in C1. Report sensitivity/precision/counts across the complete pair roster. These technical/reused-pair counts are not independent biological samples; do not use pair resampling to claim biological significance.

## Continuation decision and headroom

Freeze the strongest primary rival as the non-candidate, non-wrong-shape panel method with smallest aggregate primary regret; use that same rival in per-background comparisons and the conditional bootstrap. Primary improvement is rival loss minus candidate loss. Report baseline oracle headroom before interpreting relative gains; if rival loss<.05, the absolute continuation margin is unattainable and label that fact, not an impossibility theorem about all methods.

To open the separate HTS031 test, require all of: full matrix complete; absolute regret reduction>=.05 log2-growth units AND relative reduction>=20%; improvement in at least4/6 background folds; central95% interval from2,000 paired-background resamples (seed1031) entirely above0; candidate beats linear interpolation, pooled normalized shape and wrong-drug shape by at least.01; secondary best-drug regret no worse than the primary rival; and nonnegative improvement against that rival when scoring either technical well separately. This conditional interval summarizes the six retrospective background predictions with shared training; it is not confirmation across independent preparations. A failure parks this particular shape restriction and leaves other virtual-cell hypotheses open. No post-score rescue search.

If the development gate passes, freeze and independently review a separate unchanged-hypothesis protocol for the126 common HTS031 drugs before decoding its counts. That would be a same-source different-background/panel transfer test, not independent external biology. Qualified independent validation and actual decision/cost evidence are still required for src/ or tools/ promotion; no Agent follows automatically.

## Execution guard

Canonical interpreter D:/anaconda/envs/maestro/python.exe; at most4 compute threads,15 minutes cooperative wall guard for this complete matrix. Save source/cache/protocol/script hashes, complete prediction and selection arrays, inner choices, optimizer status, time and unmeasured resource metrics as null. Keep preexisting dirty files intact. Independent code review precedes fitting; independent arithmetic follows outputs. Do not install packages or rerun the matrix merely to try a better setting.
