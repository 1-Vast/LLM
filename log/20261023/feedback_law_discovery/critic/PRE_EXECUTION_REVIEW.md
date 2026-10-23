# Independent pre-execution review: bounded exposed-source pilot

2026-10-23. Read PILOT_PROTOCOL.md and research/feedback_law_discovery_20261023/pilot.py only. Did not load cache/data, run/import pilot, fetch sources, alter root code or read outcome payload. This review is before the pilot run to the reviewer's knowledge. Status: CONDITIONAL_PASS_FOR_EXPLORATORY_FALSIFIER; no scientific core GO.

## Leakage and endpoint

Code selects drugs on finite availability in source folds only; means/scales/covariance use source_rows only. Episode row selection is restricted to eligible source folds. Whole patient IDs determine folds, rather than sample IDs. Development supports depend only on sample/drug IDs and availability, and reveal exactly eight values. Training query mask excludes support outcomes. Development query mask excludes purchased supports. I find no implemented path taking development query values into trained parameters, covariance conditioning, or support ordering. The full Y-derived z tensor exists in train_model but only source row indices are used in training, so its existence is not itself leakage. Runtime/hyperparameter decisions must remain frozen rather than react to development results.

Eligibility and evaluation condition on observed assay availability, shared across arms. This is retrospective completion on the exposed panel, not missing-at-random generalization or discovery on unassayed drugs. No physical same-checkpoint claim is needed by this revised digital record-order contract. Mean raw AUC top3 regret is correctly implemented on unpurchased available drugs, and patient averaging follows per-sample loss averaging. This is not clinical efficacy or a calibrated cross-drug biological margin. Three seeds are not three biological replications.

## Model and budget correspondence

Fast updates match the denominator 2*SUPPORT=16 and sum over a package. Because each h row is separate, summing the batch loss without division by batch size gives each row its intended per-context gradient. AB/BA use two package gradients each and union one. Fixed recomputes AB twice; augmented and consistent use AB/BA/union. Their initialization and episode RNG resets are identical by seed; consistent alone adds the frozen two output penalties. Query labels for penalties are not separately consumed, although each query action's prediction is evaluated. Setting create_graph=False only during evaluation is appropriate for evaluating the learned update, not fitting it.

The consistent model can still learn weaker steps to reduce sensitivity. The protocol correctly requires both held-out raw MSE and regret improvement, not consistency alone. Ordinary mean, covariance conditional completion and DeepSets are real stopping sentinels; their failure to be beaten must stop expansion of this fixed configuration. Their success cannot be excluded because they have different parameter counts or compute. No world-model, agent, inheritance or RSI result follows from this screen.

This is matched source episode/outer-step comparison, not exact equal-total-FLOP evidence: the consistent arm backpropagates additional penalty terms. All arms compute penalty tensors, but only consistent differentiates them. The explicit runtime/work reporting plus exploratory scope is sufficient for a negative falsifier; a positive cannot establish total-budget superiority without later cost matching. DeepSets three identical query evaluations do not triple acquired feedback. Full covariance uses the same source outcomes and eight purchased observations; missing entries are source-centered zero-filled as declared.

## Repairable accounting gaps before execution

The protocol explicitly charges preprocessing/support selection/model work. Code records training and some evaluation times but does not time cache decoding, source preprocessing/support construction or mean evaluation, and does not save overall walltime. Add those timings or append a pre-run protocol clarification admitting them as unmeasured; do not report existing train_seconds as total cost. This is an accounting blocker to a literal all-cost report, not an outcome/leakage blocker.

Current query_view_evaluations counts context-view rollouts, not the number of measured source query scalar predictions. Query panel sizes vary. Preserve the existing rollout counter with its stated unit, and add total masked query coordinate evaluations and distinct source observation exposure counts if claiming exact label/work accounting. Likewise fast_package_gradient_evaluations is a per-context equivalent count, not the number of batched autograd calls. Explicit units avoid overclaiming.

For an auditable split manifest, record source_rows/normalization context and group IDs as well as training/query IDs. Means/covariance currently include ineligible source rows, which is legal and available to all arms, but train_contexts alone does not enumerate their exposure. This is provenance completion, not a reason to exclude those source rows or alter the frozen method.

Do not alter gamma, width, seed, drug threshold, fold or endpoint in response to results. Keep initiation and partial outputs on exceptions. Root should bind protocol, reviewed code and cache hashes in the pre-execution freeze; any code/accounting repair receives a new hash before first execution.

## Recommendation

Proceed after the narrow accounting/provenance gaps are repaired or explicitly bounded before outcomes. No change to model, biological hypothesis, source split, support rule or decision threshold is requested. If the stopping criterion fails, stop this exact configuration; if it passes, it only nominates a later fair-budget hypothesis and does not repair absence of a biological sharing law or establish any inherited improvement.
