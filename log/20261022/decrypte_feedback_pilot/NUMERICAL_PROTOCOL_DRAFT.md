# Development-only conventional feedback test (review draft, values unopened)

## Question and scope

Primary endpoint: published DMSO-relative Jurkat **Metabolic activity**, at the five nominal treatment concentrations1,10,100,1000,10000nM. This is an observed normalized endpoint (~18h treatment plus3.5h assay); not clinical response, independent functional noise, or a new wet experiment. The source methods say values are normalized then curves fitted. A stored per-dose column can be analyzed as the published observed endpoint without proving it is an unprocessed single-well value; record remaining export uncertainty. Do not use curve parameters C:I or Effect V, neither as features nor targets.

Only the48 development drugs in PARTITIONS.json will have response values decoded. Other96 drug numeric rows and all primary-cell responses remain unopened. Already qualitatively exposed(+)-JQ-1 is development; missing structure CHDI00465983 is development and excluded from chemistry-specific subgroup claims. Known Murcko scaffolds do not cross splits; this is not a chemical-distance or independent-background guarantee. Published-paper knowledge exposure remains.

The three endpoints' development J:T cells can be extracted only for predeclared quality/normalization checks. Primary models use K:O metabolic relative intensity. J and P:T are used solely to test denominator compatibility, not as free target-drug support features. Secondary Confluency/Cytotoxicity only report finite/missing/range and the same fixed descriptive signal metrics; no endpoint switching or extra model selection based on them.

## Data and normalization checks before prediction

Validate source hash, exact identity join, numeric non-formula payloads, finite values, and exactly one row per developmental drug×assay. Preserve raw payload text in development-only JSON for reproducibility. No imputation, clipping or removal of high-response/outlier drugs; numerical zero is valid. Negative values are reported and retained if finite. If any nonfinite/missing primary values occur, stop prediction and report missingness rather than silently drop tasks. Check whether raw/relative ratios are constant across five doses within each drug/assay; this is algebraic compatibility with one shared denominator, not proof of normalization code or independent noise. Report mismatch to relative zero baseline without assuming its empirical provenance. Cytotoxicity corrections may make raw/relative differ and will not invalidate metabolic tasks automatically.

## Finite budget / target contracts

Compare B=0,1,2 functional observations for each target drug. B1 reveals dose10000nM only. B2 reveals1 and10000nM. **All budget comparisons use the identical three unrevealed target doses10,100,1000nM.** No evaluation point is also a support point. All algorithms know dose positions, the same source data and the target's chemical metadata. B0 lacks target functional feedback. Source training tasks have all five published values; source cost is48 complete development curves, and each outer test model has only other source drugs. B1/B2 are offline hypothetical local acquisitions, not actually purchased assays. Do not call B2 better than B1 feedback efficiency unless matching the additional feedback cost explicitly.

## Preregistered ordinary programs

All scores from outer leave-one-scaffold-group-out within48 developmental drugs. Inner group leave-one-out selects regularization/hyperparameters using source curves only and the same three target doses. Test supports may enter prediction only after tuning. Evaluate each program separately; a source-selected portfolio among them may also be reported with fully nested selection, but is not a new method.

1. DMSO constant1 (B0), support-high constant(B1), log-dose straight line through endpoints(B2). These are deliberately simple references, not sole comparators.
2. Source mean per dose at B0; source empirical Gaussian conditional prediction at B1/B2: source five-dose mean/covariance, condition on observed target supports using diagonal ridge λ times average marginal variance. λ∈{0.01,0.1,1,10}; B0 no tuning. Do not call this a new world-model mechanism.
3. Direct regularized response prediction at each B from ECFP radius2/2048bit chemical kernel plus source-standardized support-value linear kernel. Chemical kernel is Tanimoto; support kernel dot/B for B>0; sum the two (fixed equal weights). Center both kernel blocks using source training statistics. Ridge λ∈{0.01,0.1,1,10} in the convention K+NλI. Center output by source mean. Missing-structure rows use zero chemical similarity (identity diagonal1 only); presence indicator and subgroup limitation reported. No optimization of feature weights on target curves.
4. Source curve-library posterior average at B1/B2: source full curves weighted by Gaussian distance to the target's observed supports, σ∈{0.1,0.3,1,3}×source support standard deviation; at B0 source mean. A kernel smoother / ordinary empirical prior, not a novel update rule. Use stable logweights and source-only scaling; target evaluation values are never used in weights.

This first test diagnoses whether functional feedback is predictively useful at all under strong ordinary use. It does not test learned world dynamics, agent policy, inherited rule or recursive editor; it does not waive their full future comparisons to ordinary retraining, continual learning, active learning, mixing or equal-budget program search.

## Metrics and advance/stop decision

Primary loss: mean squared relative-intensity error, averaged equally over three target doses then equally over target drugs. Secondary MAE and per-dose risks. Report full task population, not selected strong-response subsets. Report mean absolute deviation from1, full dose range distributions and the fraction of observed error at high-response tasks; do not invent assay-noise thresholds.

Report paired gain of each same-program B1/B2 over its B0 and against the best B0 conventional program; bootstrap48development drugs at scaffold-group level10000 draws, seed20261022. This is exploratory uncertainty conditional on these observed curves, not a measurement-noise interval or external confirmation. Report intervals for all predeclared comparisons without selecting a favorable endpoint. No significance claim without qualification; exploratory apparent-positive estimates may guide hypotheses only.

Advance to a molecular incremental-information pilot only if a source-selected ordinary feedback program beats the source-selected B0 on primary loss with paired95%bootstrap interval entirely above zero, gain direction nonnegative in at least two of three dose-wise mean losses, and mean gain remains positive after deleting each of the three largest per-drug absolute paired gains separately. This is a statistical development gate, not a clinical or noise-based utility threshold. If not, STOP expansion of this exact task/menu into molecular model+RSI; preserve any narrower exploratory feedback signal. No extra grid, endpoint switch, new split or high-response filtering to rescue it.

Even if this gate passes, a separate assay-supported decision/cost requirement and molecular same-information controls are necessary before application/WM promotion. No hypothesis about novelty follows from baseline success. Full objective remains active.

## Verification and costs

Save each outer prediction/support set/tuning choice, row exposure list, source versions, environment, runtime and seeds. Synthetic checks must establish no target-query values affect fit/tuning, and no support dose enters loss; an independent auditor should reconstruct decoded development payloads and recompute metrics without importing model implementation. Unopened96numeric rows must never be extracted by the selective reader. Preserve all failures, budget costs and uncertainty. No API call is required for this pilot.
