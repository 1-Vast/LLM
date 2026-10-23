# Independent biological/method interpretation of the frozen result

Scope: read SUMMARY.json, GATE.json, METRICS.json, PREFIX_FITS.json, PREFIX_ELIGIBILITY.json, PREDICTION_SEAL.json and EXECUTION.json; independently calculate relative changes, selected-fit status and prefix-loss comparisons from these saved scalars. Read EXPOSURE_SCOPE_ADDENDUM.md. No new fit, author/root model import, raw outcome array, independent prediction reconstruction, new GET or peer result conclusions were used before this seal. This is result/fit-accounting interpretation, not full numerical replication.

## Main result and stop

Execution returned0. All76 anonymous cell-line/label curves were eligible; no prefix exclusion occurred. The moving-midpoint continuation requirement fails: **0/4 cells** improve both primary and secondary MSE, **27/76 curves** improve primary MSE, and the moving arm does not beat both ordinary controls. Support **STOP_THIS_MOVING_MIDPOINT_CONFIGURATION**, without another start/grid/model or subgroup rescue.

| Method |120h count-ratio MSE|75–120h count-ratio MSE|120h count-ratio MAE|
|---|---:|---:|---:|
| Fixed midpoint6 |5.716680|1.508723|1.718698|
| Moving midpoint7 |7.418557|1.859164|1.960316|
| Independent dose logistic |7.630526|1.987736|2.195066|
| Prefix-selected direct |5.090839|1.244340|1.791453|
| Persistence |18.896602|6.075677|3.789816|

Moving7 is approximately **29.77% worse** in120h MSE and **23.23% worse** in late-interval MSE than fixed6. All four cell means are worse on both MSE endpoints. Direct selection improves overall MSE over fixed6 by **10.95%** at120h and **17.52%** over the late interval, but its120h MAE is **4.23% worse**. Therefore direct prediction wins the declared MSE comparisons, not every functional metric or every cell. Fixed6 beats direct in120h MSE for T98G and UW228-3; at late-interval MSE it beats direct for T98G. Do not erase these heterogeneous results.

## Numerical nesting and fit limits

In75/76 curves, moving7 achieves lower best prefix SSE than fixed6 yet has worse overall extrapolation. This pattern is compatible with finite-prefix overfitting or weak extrapolation constraints; it is not proof of the cause. One curve has numerically higher moving7 prefix MSE by5.1412e−5 despite function-space nesting, demonstrating a finite-optimizer limitation. This does not invalidate the frozen stop, but it prevents interpreting all differences as intrinsic optimum comparisons.

Fixed6 has73/684 starts at the evaluation limit and8 selected best fits at the limit. Moving7 has65/684 limited starts and6 selected best fits at the limit. Independent logistic has0/1368 limited starts. Status at a finite budget is not certified global convergence. Aggregate saved fitting time is about35.76s fixed6,40.47s moving7 and5.70s independent logistic, with93,693/93,457/26,350 saved function evaluations, respectively. Those solver counts do not measure equal FLOPs or general hardware efficiency. No extra fit is warranted to rescue the stopped configuration.

## What biology is and is not established

The target is an actual exported image-based count divided by the same well's observed6h count, not unnormalized cell number, ATP, death fraction, actual engagement or a full120h fitted surface. The observation split is scientifically meaningful as a within-well forecasting task. It neither validates segmentation as viable-cell truth nor identifies the mechanism behind a curve's change.

The test provides no evidence that releasing only the fixed half-range midpoint improves the specified forecast. It does **not** prove every true biological midpoint is time-independent, rule out delayed death, certify the entire VUScope family, or explain its errors through any particular biological process. Both surface models retain common asymptote/slope restrictions, finite bounds and optimizer limits. Independent per-dose logistic's worse average MSE likewise does not establish that biological cross-dose sharing is always correct. The direct arm's ordinary gain is a finite-panel same-information forecasting result, not a new update law or demonstration of world-model necessity.

Anonymous label identity prevents attributing an error to a named compound or18-HD AC inhibitor mechanisms;19 anonymized curves per line were not chemically authenticated. The single-well-per-dose design, shared vessel/protocol structure and repeated times cannot be counted as independent biological replicates. No clinical ranking, drug-combination claim, generalization to new cell/drug tasks, agent acquisition benefit, inherited updater, joint benefit or RSI is established.

## Exposure and future-information scope

The append-only exposure clarification is accepted: schedule construction/prefix parsing transiently scans and text-decodes full rows, including future response strings, but does not numerically convert/retain/show them as outcomes or use them in fitting/selection. The root's earlier inspection displayed0..27h responses before protocol; this is logged exploratory prefix exposure, not a fresh blind confirmation.

The stated numeric dataflow uses only6..72h in fitting, prefix-only48→72 validation for direct selection, and N6 normalization. Predictions were persisted and hashed before late numerical scoring according to code/receipt; source has not independently monitored the live process or secured custody and does not claim cryptographic blinding. This scope differs from literal unread archive bytes, and the correction does not change endpoints or fitted models.

## Decision

Preserve the useful ordinary direct-versus-restricted forecasting comparison and the clear negative on the moving-midpoint configuration. Do not add gamma complexity, optimizer starts, late-data tuning, a death state or ATP calibration to rescue it. A genuinely new functional mechanism would require new specified evidence and an update operation beyond these ordinary fits. The complete virtual-cell/agent/RSI objective remains unachieved.
