# A1: baseline-neighborhood prediction of conditional pair effects

Frozen candidate and proposed protocol v1, 2026-10-31, before EGI numerical access. Source/design evidence: egi_admission/identity_design_projection.json, original Methods S24 and the raw counts/library originals pinned there. This is a research-local capability probe. A graph smoother and four-term abundance contrasts are established constructions; neither is claimed novel.

## Claim, alternative and source admission

Question: after an untreated functional screen, environmental single-target measurements and a fixed environmental double-target anchor set, do untreated functional neighborhoods predict additional, reproducible pair-specific environmental changes? A negative result stops this candidate. The practical output would be a ranked follow-up list within the selected K562 library and one known ATR-inhibitor condition. Assay savings, new-drug transfer, arbitrary gene transfer, physical-time dynamics and drug-discovery benefit remain untested.

Only GI1 is admitted. Counts: data/external/conditional_interventions_20261030/egi/14_GI_expt1_counts.txt.gz, SHA256 105353899a4b91bc5446bfacc20ee91a13ff6bf17f8d53805fc8bb543f2a1403. Matched Rep1/Rep2 T0, UT and DRUG; DRUG is ATR inhibition, endpoints day9 after T0, two separately transduced/passaged culture ancestries. Do not open GI2 values or any published GI matrix. Library: 17_redirect1_dualsgrna_alignedlibrary.txt, SHA256 e2e23ee7296af9a3cd5f7b1782d5879afe8bd40e678b959025e48dd850ea38f5. All source gene labels with two distinct targeting guides are eligible initially (312); CSRP2BP has one and is excluded by identity only. Keep REV3 as its source label. All13 source NTC guide identities are controls. No published303-gene outcome-based subset is adopted.

Native published maps average replicate phenotypes before AB/BA/quadratic fitting. This test instead defines a new endpoint. It is not independent reproduction of the native standardized GI, and cannot by itself establish a genetic mechanism.

## Observation and endpoint

For ordered guide pair a,b in culture r, write L_r(a,b;X/Y)=log2((count_X+1)/(count_Y+1)). For each X/Y form

Q_r(a,b;X/Y)=L_r(a,b;X/Y)-median_n L_r(a,n;X/Y)-median_n L_r(n,b;X/Y)+median_(n,m) L_r(n,m;X/Y),

where n,m range over all13 NTCs. The response is the median of Q(DRUG/UT) across the eight ordered two-guide/orientation constructs for each unordered distinct gene pair. The untreated baseline is the same median of Q(UT/T0). This is a double-versus-single difference of log relative-abundance ratios. Common log library-size offsets cancel algebraically; no fitted quadratic label, global target distribution standardization, growth divisor or trajectory is used. Endpoint pseudocount=1 is fixed. The T0 term cancels from the environmental-vs-UT difference, but T0 remains needed for eligibility and untreated features.

Eligibility uses T0 only, never UT or DRUG depletion: retain an ordered targeting construct if both cultures' T0 count>=30. Each guide must have at least5 of13 T0-eligible guide/NTC constructs in each orientation; NTC/NTC median must have at least25 eligible constructs. Use these same identity masks in both cultures for all ratios. A gene needs both guides retained. A distinct gene pair needs at least4 retained ordered constructs and at least1 in each orientation. Medians use only retained identities. Single-target feature for a gene is the median guide/NTC L minus the NTC/NTC median across both orientations and its guides, separately for UT/T0 and DRUG/UT. The shared controls induce dependencies; pair counts are not culture replicates.

No numerical eligibility or headroom has yet been inspected. Abort fitting if fewer than10,000 eligible pairs or1,000 eligible test pairs. After endpoint creation, report cross-culture Pearson and Spearman, abundance/depletion QC and strong-effect counts. Abort fitting if training-pair cross-culture Spearman<0.20 or fewer than500 eligible pairs satisfy |y1|>=1, |y2|>=1 and equal sign. This is a fixed detectability gate, not evidence for the candidate. No favorable endpoint/condition replacement is permitted.

## Holdout and information contract

Pair fold is SHA256('MAESTRO-EGI-A1|'+min_gene+'|'+max_gene), first8 hex digits interpreted base16 modulo10:0..6 train,7 validation,8..9 test. An unordered pair stays in the same fold across orientations and cultures. All source identity mappings are fixed before numerical access. No held-pair DRUG double counts may affect training, features, graph, normalizers or hyperparameter selection; evaluators alone use them. DRUG singles/NTCs and all untreated/T0 data are allowed prediction-time measurements.

Run both directions with the same fixed model grid: culture1 anchors/validation/features -> culture2 held pairs, and culture2 -> culture1. A direction's predictors may use only its source culture's untreated map, singles and training-anchor responses. No target-culture values enter its fitting, graph or tuning. The source culture's held test response is used only for replicate-confirmed evaluation after predictions. Cross-culture transfer prevents a same-culture UT denominator from directly serving as a test-label noise shortcut. Two cultures and one batch remain the generalization limit.

Use median-zero imputation for absent baseline pair features and zero diagonal. The entire source untreated map is available, including held pairs; this is explicitly conditional prediction, not de novo prediction of an unmeasured untreated screen. No external graph, expression matrix or model weight is added.

## Fixed ordinary-model/candidate matrix

All models see the same source information; dimensional or graph transforms are fit using source untreated information only. Scalar features: baseline pair value; baseline and environmental single effects represented by sum, absolute difference and product; plus symmetric sum, absolute difference and product of each gene's8-dimensional untreated-map SVD coordinates. Standardize using training feature means/SDs; constant columns get divisor1.

Rivals: zero change; training mean; gene-additive Ridge on incidence features; direct Ridge on scalar/SVD features (alpha1,100,10000); ElasticNet on those features (alpha0.001,0.01,0.1; l1_ratio0.5, max_iter3000); HistGradientBoostingRegressor on those features (max_leaf_nodes7 or15, l2_regularization10, max_iter150, learning_rate0.05); symmetric soft-impute matrix completion on the training-anchor response matrix (rank2,8,16; 30 iterations; observed anchors restored each iteration). Ridge incidence alpha1,100,10000. All hyperparameters select source-validation MSE, ties use the listed order. Matrix completion uses no validation/test values in reconstruction.

Candidate: take the selected direct Ridge, then smooth its training residuals over untreated functional-profile neighborhoods. Center each source baseline profile over partner genes, normalize its Euclidean norm and form positive cosine similarities, excluding self. Retain10 largest positive neighbors per gene, ties gene order; normalize each row to sum1 (no positive neighbors -> zero row). Let W be this fixed directed neighborhood matrix, R the symmetric training-residual matrix and M its0/1 anchor mask. Add (W R W^T)/(W M W^T+lambda) to the direct prediction, with lambda0.1,1,10 selected by source-validation MSE. This is an ordinary neighborhood residual smoother. Negative control: the same candidate with the graph's gene identities permuted using numpy default_rng(20261031), with its own lambda chosen on the same validation. Retain the control regardless of outcome.

## Decision, uncertainty and resource limits

Rank test pairs by descending absolute prediction, ties canonical pair identity. TopK=100. A signed hit requires |y1|>=1 and |y2|>=1, sign(y1)=sign(y2)=sign(prediction); zero prediction is never a signed hit. Primary metric=P@100 of these reproducible signed strong effects; report negative-only discovery descriptively, MSE, MAE and correlations secondarily. The strict practical gate requires candidate at least5 additional hits per100 over EVERY ordinary rival in each direction, plus at least5 over the permuted-graph control in each direction, and at least20 hits in each direction. A mean-only/MSE gain cannot pass. This is a prespecified screening threshold, not a statistical-power assertion or biological validation.

Report exact hit identities and cross-culture agreement. With only two biological cultures do not claim a population-level confidence interval or p-value based on treating pairs/cells as independent. Show leave-one-gene-out sensitivity of the frozen rankings descriptively; it is not a culture-level confidence interval. No choice of method after test access, no model expansion after failure.

Before real numerical access: independent source/protocol challenge; root response; frozen runnable code and hashes; independent arithmetic checker and source-access review on synthetic fixtures only; archive original review bytes. One real matrix under D:/anaconda/envs/maestro/python.exe, <=4 threads, hard1800seconds; one globally shared spare only for demonstrated implementation/environment failure. No other condition/data/model run.
