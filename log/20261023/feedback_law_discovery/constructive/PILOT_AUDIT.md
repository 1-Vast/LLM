# Independent saved-updater numerical audit

2026-10-23. **PASS_SAVED_INFERENCE_RECONSTRUCTION / CONTINUATION_GATE_FALSE.** This is independent verification of one completed source-only exploratory run, not a new biological experiment or independent performance replication. RUN_RECEIPT confirms returncode0, COMPLETED,29.1684777seconds. All listed pre-execution freeze hashes match the actual files; freeze SHA256948ee458e2db1f6b43ba6d7d2baec2b8bb95831674bc73a766cb62905bd1e38f.

## What was reconstructed

The audit imports no root pilot module, never runs training, and loads all nine fixed/augmented/consistent saved models with torch.load(weights_only=True). Torch serves only to deserialize tensors; NumPy float64 performs the inference. For each AB/BA/union package path, compute p=E*tanh(h), gradient=sum((p_support-y_support)*E_support)*(1-tanh(h)^2)/8, and h-=softplus(step)*gradient from h0=0. Rebuilt27 full prediction arrays and compared them to saved PREDICTIONS.npz.

Maximum absolute discrepancy over all27 arrays is **5.043599680121247e-7 standardized**, below the discussed1e-5 expectation; raw AUC maximum is **2.5951118573175336e-5**, because per-drug standard deviations rescale errors. Maximum patient-cluster metric discrepancy is5.686658369086217e-6. These are consistent with independently evaluated float64 versus original float32 arithmetic and support-value casting. No prediction was rounded or altered to force agreement. Exact error per arm/view and saved-weight hashes are retained in PILOT_INDEPENDENT_AUDIT.json.

The cache reads only Y/contexts/items/groups, explicitly authorized for this audit. No X/events/G, protected outcome or new dataset was accessed. Independently reconstructed historical patient folds, source-only >=100 column retention, source means/SD/floor, eligible source/development contexts and identity-hash8-assay supports. Manifest scales and rows match exactly. Source/development patient groups are disjoint. Saved truth/query masks match the directly selected exposed values. A second audit execution added these input-contract checks after the first inference reconstruction; it did not rerun a model fit, search or experiment.

## Frozen gate

Independent AB patient-cluster scoring reproduces the recorded metrics within the numerical discrepancy above. Consistent versus augmented MSE, seeds0/1/2:

| Seed | Augmented MSE | Consistent MSE | Both-metric gate |
|---|---:|---:|---|
|0|2108.698185|2129.589614|false|
|1|2111.471839|2145.209013|false|
|2|2128.441472|2155.467424|false|

Seed0 shortlist regret improves from40.020263 to38.864746; seeds1/2 regret worsens. Thus every seed fails the frozen requirement to improve both metrics. The covariance sentinel has MSE2054.557791 and regret37.054722 and beats the seed-average consistent arm on both metrics. Consistent does beat source mean and this fixed DeepSets sentinel on seed-average both metrics; those scoped positives remain, but do not satisfy the gate. The required action is STOP_EXPANDING_THIS_FIXED_CONSISTENCY_CONFIGURATION, without new gamma/width/seed/subgroup rescue.

## Training/gate and scope audit

Read the accounted protocol/code diff and execution wrapper. The accounted version adds replay/coordinate counts and actual preprocessing/overall timing; it does not change model, split, normalization, three-view losses, gamma1,120steps,batch16,seeds or gate. Freeze includes this actual accounted implementation and checked synthetic pre-data tests. The wrapper validates hashes before launching once and preserves actual console/receipt. Matched episodes/unrolls do not imply exact FLOPs, explicitly stated before execution; this audit does not rerun source training or prove optimizer-gradient history was perfectly reproduced. Lower consistency sensitivity cannot override the functional gate. No world-model, agent, later-task inheritance, joint gain, or improved-improver claim follows from these results.

Code: research/feedback_law_discovery_20261023/constructive/audit_pilot.py. Evidence: PILOT_INDEPENDENT_AUDIT.json. All originals remain unchanged; this review is a separate addendum.
