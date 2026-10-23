# Static review before source values

2026-10-23. Read root's STATE_PROTOCOL.md and research/mixed_feedback_estimator_20261023/predict.py. Did not open STATE_BY_GEM, prediction results or any biological numerical output. Code was present before this review. The extraction implementation belongs to the support review; this review does not independently certify its matrix parser.

Protocol and predictor agree on the fixed 73 source pairs, 103 named readouts, two endpoint spaces and two directions, pair hashes, source-inner selection, same-gem symmetric bilinear products before averaging, and training-only standardization. The target formula correctly uses disjoint input and response gemgroup sets. The q diagonal is drawn from the full symmetric outer feature, preserving the intended nesting. No target-label access enters predictor scaling or feature construction.

The zero-intercept diagonal and other ridge intercept/scaling differences are now explicit, so this compares specified conventional recipes rather than claiming parameter-identical regularization. Full bilinear uses flattened symmetric features with individual training standardization, not an unscaled Frobenius norm; this is documented as feature standardization. The fixed mixture is not weight-selected.

Actual fit-call count in the current code should be 600: four endpoint/direction combinations, five folds, mean inner+outer=2 calls, and four regularized models each six inner+one outer=28 calls; 4*5*(2+28)=600. Candidate count is not equal compute. This was sent to root before execution; recording counters in code is preferable to relying on this hand count.

Recommendation: GO for one frozen source-structure execution. The final gate's reverse-log requirement is more conservative than my initial proposal and is scientifically permissible if fixed now. The strongest-conventional-arm envelope must list its exact included names, particularly fixed_mixture, before values; do not remove a winning control post hoc. The protocol explicitly records full raw-matrix numerical parsing contact and does not imply excluded RNA numbers remain unopened; no heldout function values are to be decoded.

No novelty, functional utility, independent biology or RSI conclusion is supported by this static review. The execution must stop rather than change eligible pairs/QC/genes if a required group is empty. A subsequent arithmetic review should use saved predictions without refitting.
