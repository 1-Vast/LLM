# H_MEAN.v1.1 — preserved pre-response clarification

2026-10-29. No response count has been accessed when this amendment is written. Read this document with unchanged protocol_v1.md and design_worker/recommended_design.md. Their original bytes and protocol_receipt.json are preserved. This amendment has precedence only for the following explicit clarification and execution-accounting corrections; it changes no data, model, split, score, optimizer, resampling draw or scientific-test budget.

## Decision rule

Resolve T-MEAN-01 using the already specified design's conflict-to-INCONCLUSIVE rule. With all eligibility, finite-value, convergence, nestedness and resource checks satisfied:

- Original Delta > 0 AND the linear empirical 5th percentile > 0: CONDITIONAL_HELDOUT_CURVATURE_GAIN.
- Original Delta < 0 AND the linear empirical 95th percentile < 0: EXPONENTIAL_PREFERRED_IN_THIS_COMPARISON.
- All other cases, including zero, point/stability sign conflict or any failed check: INCONCLUSIVE.

This is a comparison of the two specified fitted prediction procedures under fixed plates and row roles. It is neither an absolute adequacy/equivalence test nor a biological confidence statement. No outcome validates white measurement error, identifies process rates, licenses drug inference or establishes the general co-learning objective.

## Frozen inputs and audit corrections

protocol_receipt_v1_1.json binds the unchanged v1 documents, metadata, original receipt, this amendment, bootstrap_draws.npy, bootstrap_input_receipt.json and the final primary script before response access. Validate these identities and the declared array shape/type/range before count parsing. The separately written verifier uses the same frozen input array, not the primary program or results.

Count each attempted eligible response access immediately before field conversion. All raw predictions, training SSEs, validation losses, per-plate scores, aggregated scores and quantiles must be finite. Retain solver identity/version, original status/message/nfev and clearly labeled normalized/raw SSEs; summarize successful bootstrap termination statuses without dropping draws. No extra starts or outcome-driven repair run.

Check resources before original fits, throughout resampling and before classification/output. CPU accounting includes module imports through total process CPU time. Internal wall timing begins immediately after importing the standard time module, before other imports; the separate 180-second subprocess timeout covers interpreter launch, setup, imports and output. Memory is process peak working set. Checks are cooperative and the wall timeout terminates the child; no OS CPU/memory hard limit is claimed. Preserve failures and partial exposure, and do not replay after an execution receipt exists.

The pre-access independent assessments are mean_challenger/initial_review.md and mean_challenger/preaccess_code_review.md. Additional scope limits in T-MEAN-02–05 remain: nonrandom row split, unknown dependence/preparation, relative-only prediction, conditional resampling and no global-optimum certificate.
