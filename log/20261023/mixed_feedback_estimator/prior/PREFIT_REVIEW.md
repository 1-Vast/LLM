# Static prefit review

2026-10-23. Read STATE_PROTOCOL.md and research/mixed_feedback_estimator_20261023/{predict.py,extract.py,test_predict.py} before any real run. This reviewer did not run extraction/prediction, decode the RNA matrix, read STATE_BY_GEM.npz, or inspect any new biological response. Decision: **GO_BOUNDED_SOURCE_STATE_FALSIFIER**, subject to clarifying the pre-freeze hash convention below. No new feature/search demand and no new-core approval.

## Access and extraction

The only proposed fresh state accumulation is the frozen 73 source pairs plus existing singles/controls, all fixed 103 raw readouts. Functional outcomes are not opened by either program. MatrixMarket parsing necessarily materializes excluded numerical triplets on both whole-file passes; the protocol and extraction report explicitly disclose this contact instead of claiming protected/non-source RNA was never opened. Excluded double state profiles are not accumulated. This is a retrospective whole-data extraction, not a sparse assay budget oracle.

Expression columns are never renamed; the intervention-label-only alias map and unchanged IDENTITY indices are checked against the raw reference. Existing single orientation selection and three control labels are frozen, as are mixed-guide pair pooling and pair-level membership. Whole-gene per-cell totals are accumulated only for candidate cells; UMI QC occurs before readout sums. Zero-readout entries are correctly represented as zero contributions to the per-cell mean. Every required group must remain nonempty; failed coverage stops instead of dropping a difficult pair/gem.

Within each retained cell the all-gene total supplies CP10K. The saved means distinguish mean(log1p per-cell CP10K) from log1p(mean CP10K), and save linear CP10K separately. Numerical shape and access constraints are explicit. Two full passes and the raw input's existing provenance are not independent biological validation.

## A/B separation and state design

form_arrays uses only A singles/controls to construct A-to-B inputs. The target is the mean across B gems of centered double minus centered single a minus centered single b, i.e. double-a-b+control. Controls are centered inside gem before aggregation. Reverse direction is separate and fixed. No target pair cell count weights the predictors. This reduces same-measurement algebraic noise coupling; it does not establish independent biological tasks or remove shared biases.

design computes mean_g sym(a_g b_g^T), not an outer product of averaged singles. Its diagonal is exactly mean_g(a_g elementwise b_g), so full-q ridge and the diagonal model receive the same q. Absolute-difference and summed-single linear inputs are swap invariant. Symmetric outer features also preserve pair swap. The full symmetric flattened matrix duplicates off-diagonal entries, but its columnwise train standardization and dimension-normalized kernel are the explicitly declared feature-standardized recipe; it should not be interpreted as an unstandardized Frobenius bilinear prior.

## Heldout scope and selection

Outer assessment rows do not enter model/penalty selection. Inner means, standard deviations and target intercepts use the inner training rows; outer refit recomputes these on outer training rows. The diagonal denominator and numerator use only the corresponding training rows, with zero-safe division. Labels from outer assessment do not enter the estimator. Features derive from legal singles without pair target fitting; computing their unscaled design globally does not itself leak target labels.

Full-q ridge, linear ridge and symmetric bilinear ridge are real regularized direct controls, not intentionally weakened models. Mean and additive baselines are present. The diagonal shrinkage has a different penalty meaning from the centered standardized ridge kernels, as disclosed; six candidate values do not imply identical parameters, identical regularization strength or equal computation. The fixed mixture averages separately inner-selected diagonal/q-ridge predictions, without outer-label choice of mixture weight. No further arm or feature class is required for this bounded state hypothesis.

One pre-freeze clarification: the prose currently says SHA256(pair) modulo 5, while hashed() uses the **first eight digest bytes, interpreted as unsigned big-endian integer**, then modulo 5. Inner ordering likewise uses that 64-bit prefix. These are different from a full 256-bit integer hash. Either exact convention is acceptable if frozen before values; the simplest correction is to make the protocol state the implemented first-eight-byte convention, without changing folds based on responses. No matrix access is needed for this correction.

## Gate and tests

The gate is conservative: log A-to-B diagonal needs at least 5% lower pooled OOF MSE and at least four positive fold differences against the predeclared strongest conventional arm, and reverse-log must strictly beat its own strongest conventional arm. CP10K is sensitivity, not an alternative selected after scores. Fold MSE is over pairs and fixed coordinates; no gene/cell pseudo-replication test is used. The posthoc best-arm envelope is disclosed as conservative comparison, not a deployable selector. The result auditor must implement exactly this gate; predict.py currently saves scores/choices and does not by itself label success.

test_predict.py meaningfully checks swap invariance, mean-of-gem products and assessment-label poisoning for all fitted arms. Extraction self_test checks selector exclusion, aliases on intervention identity, column inclusion and per-cell normalization. These are appropriate inexpensive checks; the tests do not claim biological validation or a comprehensive runtime proof. Static inspection additionally verified A/B target construction, which test_predict.py does not exercise directly.

No blocking implementation defect was found. Fix/document the hash convention before freezing, run the already planned synthetic checks, then proceed once. Do not turn this review into further feature search. After completion, independently recompute saved scores and gates and preserve any failure. A pass supports only exploratory source-state predictive structure; function/ranking utility, a novel core, world-model/agent necessity, inheritance and RSI remain unproved.
