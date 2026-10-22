# Independent numerical method contract

2026-10-22. Author: astra_rna_method. Status: INDEPENDENT_PROPOSAL / NOT_EXECUTED / NOT_A_NEW_CORE. Read before writing: research/REPORT.md opening decision register; the frozen headroom DECISION.md, MANIFEST.json and run_headroom.py; this phase EXPOSURE_AND_SCOPE.md, RNA_METADATA_PROTOCOL.md and SKEPTIC_NUMERICAL_PROTOCOL_DRAFT.md. No new preprocessing agent draft has been opened. A message announcing that draft and its single-array/all-probeset recommendation arrived while this text was being prepared; that contact is disclosed. No RNA values or previously unopened functional values were accessed. Existing source/development function exposure is acknowledged.

## Decision and bounded purpose

Proceed toward one frozen numerical pilot; do not add another theoretical qualification loop. The skeptic draft correctly separates observation information, parameterization, and a possible small-sample regularization benefit. Its main unresolved implementation choices are the precise readout, low-rank objective, feature scales, ordinary updating, and what is counted as a fit. The definitions below resolve those choices. They are a proposed contract for root to reconcile with preprocessing before numeric conversion, not a claim that the experiment has run.

Predict published High 24h DNA/100, with LDH/100 secondary, from a fixed Middle bundle comprising 2h RNA and 24h DNA/LDH. Unit is compound/proxy block, not cell or repeat. Use fixed source 24 and development 7; later 14 remains untouched. No Low, development High, or later RNA is opened. High source RNA is paid auxiliary supervision available to every ordinary model. Existing Low source function is available to every method through a shared function prior. The two Middle function replicates and their SDs are available to ordinary models; no additional dose is bought at deployment.

This N=24, one-Middle-bundle pilot can test predictive value at this small sample and feedback budget. It does not establish a sample-efficiency curve or an across-task benefit. The linear restricted construction is an ordinary constrained joint update; its exact-copy implementation is one method with two descriptions. No separate defeat of that copy is required or meaningful.

## Fixed coordinates and primitive regression

Use the final preprocessing protocol's exact ordered RNA coordinate list, identical for every fold. If gene annotation is not independently frozen, use all platform probeset IDs and call them probesets, not genes. A fold may not choose a different coordinate set. Each state vector is the fixed-coordinate treated-minus-matched-control mean log signal. No PCA, data-selected genes, detection filtering, supervised signature, or fold alignment is needed for this pilot.

The shared primitive is multi-output linear ridge with an unpenalized intercept:

`min_A (1/n) ||Yc - Xc A||_F^2 + lambda ||A||_F^2`.

Each input block is centered on training rows and divided by `sqrt(mean_row ||block-centered||_2^2)`; use 1 only when that RMS is zero. Concatenate blocks and divide by the square root of the number of blocks. This gives a whole RNA vector and a two-assay vector comparable prior feature energy without per-gene variance selection. Scale/center parameters belong to the current fit. Outputs stay in their original fixed coordinates/assay units. Fit in the dual with `K + n*lambda*I`; never form a genes-by-genes matrix. Store predictions in float64 and never clip functional predictions or assay values.

Design blocks are (a) fixed 2048-bit chemical proxy, (b) unit one-hot with a metadata-only vocabulary, (c) log10 absolute dose and log10(H/M). Compound names/IDs are joins, never predictors. At least one nonzero penalty makes a constant block harmless.

## Shared base pack: b, f, g

For each training set T and shared alpha in {0.1, 1}, fit exactly three ridge estimators:

1. `b(c,d)` predicts two-assay y from design using all source L/M/H rows in T.
2. `f(c,d)` predicts fixed-coordinate RNA x from design using source M/H rows in T.
3. `g(x,c,d) = b(c,d) + h(x, design, b(c,d))`, where h is linear ridge of `y-b(c,d)` on three blocks [x, design, b] using source M/H rows in T. The design block here comprises the already fixed design columns; its fitted block scaling is local to h.

The source rows used to fit b/h can be reused within this pack: this is ordinary training, not an OOF performance claim. Every pack excludes the complete externally held-out compound/proxy group. Therefore held-out f/g predictions and corrections cannot use that group's High RNA or function. Because b does not depend on x and h is linear in x, g is affine in x. No Jensen or distribution plug-in argument is available.

For a compound excluded from a pack, define in fixed coordinates:

`u_M=x_M-f_M; u_H=x_H-f_H; v_M=y_M-g(x_M,M); v_H=y_H-g(x_H,H)`.

v is conditional predictive error, including model/assay/lot effects. It is not an identified biological pathway outside RNA. g's outputs and both v vectors have fixed DNA/LDH units.

## Restricted and ordinary joint correction

Fit two separate reduced-rank ridge maps on inner-OOF error rows. Target one is u_H; target two is v_H. Normalize u_M and v_M as separate input blocks using only these training errors. For rho in {0, 0.5, 1}, use inputs `[u_M, sqrt(rho)*v_M]` for the state map and `[sqrt(rho)*u_M, v_M]` for the functional map. Center/scale the two blocks before applying sqrt(rho); keep the same two-block normalization at every rho, including zero. An output-block intercept is allowed and is removed together with that correction when its route is off.

For a centered/scaled X and centered Y, compute SVD `X=U diag(s) V'`, form `Z=diag(s/sqrt(s^2+n*lambda))*U'*Y`, and retain its first r right singular vectors Q. The rank-r coefficient is

`A_r = V diag(s/(s^2+n*lambda)) U' Y Q Q'`.

Store it as factors, not as a full state-by-state coefficient. This solves ridge under a rank constraint in the ridge metric. r is independently capped at min(r, target dimension, available numerical rank) for each output block. Thus full joint does not receive less total rank than the restricted method. r is 1 or 2; lambda is 0.1 or 1. Combined with two base alphas, each rho family has exactly eight configurations.

Predictions are `x*=f_H+B_state(u_M,v_M)` and `y*=g(x*,H)+B_function(u_M,v_M)`. rho=0 is the candidate/ordinary block-restricted joint method; rho=0.5 is cross-block shrinkage; rho=1 is full joint. There are no extra "novel" and "ordinary copy" rows. A synthetic exact-copy check must verify the collapsed affine predictor has identical predictions to sequential evaluation.

The primary 2x2 is a route ablation of the source-selected rho=0 configuration: use the same fitted base and B maps, setting state correction and/or functional correction to zero. It requires no extra fit or retuning. v-only still computes g on actual Middle RNA. The no-observed-Middle-RNA comparison below is the actual measurement-information ablation.

## Strong ordinary families and fixed grids

Build direct models from inner-OOF auxiliary features, so their training features have the same deployment-like nuisance predictions as correction models. Full direct input blocks are: design for M/H, actual x_M, actual y_M plus replicate SDs, f_M, f_H, u_M, v_M, b_M/b_H, g(x_M,M), and g(f_H,H). Each block is normalized as above. They predict the residual `y_H-g(f_H,H)` and add that base back. This gives them source High-RNA supervision through f/g, observed Middle state/function, and the composed-world prior. Deterministic duplicate columns are permitted but the exact restricted-copy program remains merged with rho=0.

Freeze these families:

* Direct auxiliary ridge: alpha in {0.1,1}, direct lambda in {0.01,0.1,1,10}: 8 configurations.
* Direct auxiliary centered RBF KRR: alpha in {0.1,1}, lambda in {0.1,1}, bandwidth factor in {0.5,2}: 8. Kernel is exp(-squared distance/(factor*median positive training squared distance)); use denominator 1 only when no positive distance exists. Target centering and intercept are training-only.
* No observed Middle RNA direct ridge: same eight ridge configurations and source auxiliary supervision, but inputs contain only design, y_M/SDs, f_M/f_H, b_M/b_H, g(f_M,M), g(f_H,H), and `y_M-g(f_M,M)`. No actual x_M, u_M, g(actual x_M), v_M, or observed-RNA-derived SD enters this family.
* Ordinary weighted refit: refit b, f and g on source plus the queried drug's observed Middle rows, with Middle observation weight w in {1,4,16,64} and alpha in {0.1,1}: 8. Retain the source-fitted input transformations and use true weighted least squares for coefficients/intercepts; update b with y_M, f with x_M, and g with the actual paired x_M/y_M. Recompute b-derived g features under the updated b. No queried High target is available. This is ordinary refitting, not inheritance.
* Keep every original nine function/chemistry family output as an already-exposed comparator without rerunning old code. Also report a fixed 50/50 mixture of source-selected rho=0 and source-selected direct-ridge predictions, with no mixture search.

Do not add the four-gene stress baseline until its exact independent probe/gene mapping and scientific source are frozen. It is not needed to authorize this adequate finite comparison and its absence is not a reason for another search loop.

## Cross-fitting, selection, and budget

For every fixed configuration, leave one source proxy block out. Within the remaining 23 source singleton blocks, leave each complete block out again to generate training error/direct-feature rows. Then fit B/direct on those rows, fit the shared base on all 23, and forecast the outer compound from its Middle history. No outer High RNA/function enters any fitting, scaling, residual, bandwidth, or feature stage. Outer High function is available only to the source evaluator. The inner High RNA/function supplies inner-row targets after nuisance predictions are generated, never the corresponding nuisance fit.

Select one configuration per family by mean source OOF DNA absolute error, breaking exact ties lexicographically by the frozen configuration serialization. These OOF rows are valid held-out predictions for each fixed configuration; the score after selecting on them is selection-exposed. Do not claim an unbiased performance estimate of the selection procedure or add a third nesting level. Final training uses all source and source leave-one-block-out nuisance rows. Development never selects alpha, rank, lambda, rho, family, genes, or weights.

Cache base predictions only by exact training-label set, alpha, transform/code/data hashes. With 24 singleton blocks there are 1+24+276=301 distinct full/leave-one/leave-two training sets, two alphas, three base estimators: at most 1,806 base fits. Release fitted large coefficient objects after exporting only needed out-of-fold predictions; no entire bank of full gene maps is retained in RAM.

For the proposed menu, a conservative pre-implementation estimator-fit ceiling is 3,567: 1,806 shared-base fits; 582 two-output-block correction fits (share ridge factorization across ranks; 576 outer plus six final); 579 direct/KRR/no-observed-RNA fits (576 outer plus three final); 597 ordinary-refit fits (576 outer plus 21 final across seven development drugs); three diagnostic-null fits described next. Fixed route masks, fixed rules, mixtures, and rank projections have zero additional estimator fits and separate counters. Final implementation must generate an exact run manifest and reconcile these counts before conversion. No silent retries or grid expansion; failed attempts remain in the ledger. Preprocessing, transform fits, SVD calls, cache hits, pipeline evaluations, estimator fits, wall time and peak memory are separate counts. The same eight-configuration source selection allowance applies to ordinary and constrained families; shared computations do not purchase additional hyperparameter search.

One fixed final-source diagnostic null, after source selection: derange the complete observed-Middle-derived feature bundle across source OOF rows using an explicit fixed seed/order, while retaining design, predicted priors and High targets. For B, the swapped block is the pair (u_M,v_M); for direct ridge it is all observed-Middle-derived feature blocks, including y_M/SDs. Refit selected rho=0 (two maps) and selected direct ridge (one estimator) and forecast authentic development histories. This is a paired-feedback-bundle association diagnostic, not an RNA-specific permutation test or a p-value. It does not permute raw arrays across fold ownership and therefore does not create hidden High-array contact. RNA specificity instead relies on the genuine no-observed-RNA and matched route comparisons. One null is descriptive, cannot supply statistical significance, and cannot rescue a failed primary gate.

## Scoring and stops

Seal all family configurations and development predictions before the scoring process accesses the already-exposed High function file. This prevents runtime target use; it does not restore blinding to an exposed development set. Primary score is equal-compound DNA MAE on all seven; report LDH, per-compound errors, both route comparisons, no-observed-RNA comparison, source High-state error, and all ordinary families. Do not score unobserved development High RNA. Group bootstrap intervals are descriptive with seven proxy groups and do not fix selection or identify donor generalization.

Use the original useful-gain rule without modification: the candidate must reduce DNA MAE strictly more than 0.02 and at least 10% relative to the best nonisomorphic ordinary alternative, including all original baselines. The rho=0 exact copy is merged and excluded as a separate opponent. The old development Middle-copy score 0.02335714 alone implies a necessary candidate MAE below 0.00335714; a stronger new ordinary baseline makes the requirement stricter. RNA utility, structural advantage and usefulness are separate reported contrasts. An equally good ordinary method can support measurement information, but cannot support a unique structural advantage.

Stop this configuration's expansion if the useful-gain gate fails, the observed-RNA increment is absent, or a strong nonisomorphic ordinary family explains the proposed advantage. Do not change endpoints, remove compounds, add Low/development-High/later RNA, widen search, or relax thresholds after results. Schema/identity/nonfinite/preprocessing failures stop numeric modeling and remain technical failures, not biological negative results. Record every failure in this phase only.

## The full user objective remains separate

This pilot only tests a potential world-state/function feedback structure. It establishes no active query agent, no cross-task model or program inheritance, no joint world-plus-agent gain, and no C4. A later agent comparison must give common observations, whole bundle costs, ordinary AL/CL/refit and equal-budget search. Inheritance must compare transfer with restart on later tasks. Joint benefit is a distinct matched comparison, not automatically superadditivity. C4 requires old/new checkpoints of the same improver acting from the same solver, history, permissions and search budget on later tasks. Choosing rank or shrinkage on source data is ordinary tuning and is not C4 or RSI. No new algorithm core is cleared, and this bounded pilot does not substitute for the full objective.
