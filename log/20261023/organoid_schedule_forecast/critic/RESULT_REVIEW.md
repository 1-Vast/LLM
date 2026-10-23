# Independent stored-result audit

Root exposed the failed gate and two campaign ridge MAE summaries before this audit; no result-blind claim is made. Critic subsequently read stored FORECASTS/SEAL/RESULT, execution wrapper and original archive records to audit. No peer current result report was read. Did not import forecast.py or execute its main; separate audit code reconstructs models and metrics from stored lawful objects.

Independent audit PASS:408 numeric comparisons, maximum absolute difference1.1368683772161603e-13. All FREEZE input hashes still match, forecast SHA matches, execution receipt returncode0. All initial/history/query objects exactly match original archive filters, with initial gen0, cumulative gen<g and queries gen==g without cv/cv_err. Each query retains the declared IDs and action fields only. Reconstructed ridge via augmented design and unpenalized intercept normal equations, independently reconstructed mean/NN, every batch/campaign MAE/MSE, all paired differences and both gate branches. g1 frozen/cumulative are exactly equal for all families in both campaigns.

## Results and counterexamples

| Batch | Frozen ridge MAE | Cumulative ridge MAE | Cumulative mean MAE | Cumulative NN MAE |
|---|---:|---:|---:|---:|
| FACg2 |15.106833|6.066655|8.599409|5.675925|
| FACg3 |17.780178|7.044049|6.309218|8.063149|
| OLA-IBETg2 |8.870541|9.773148|9.754812|10.575401|

FAC shows scoped ordinary added-feedback benefit: all three model families improve MAE and MSE in both informative batches. Aggregate ridge MAE falls16.443506→6.555352 and MSE319.667840→48.760189. Ridge beats cumulative mean7.454313 and NN6.869537 in aggregate, but not on each batch: NN beats ridge in FACg2 on both metrics (MSE44.052319 vs44.230720), while mean beats ridge MAE in FACg3 (6.309218 vs7.044049), despite ridge's lower MSE53.289657 vs58.931721. Thus aggregate superiority does not establish a unique useful schedule representation or universal pointwise benefit.

OLA is the direct counterexample: adding feedback worsens all three families on both metrics. Ridge MAE8.870541→9.773148 and MSE112.890871→129.120611; mean MAE7.094177→9.754812, NN8.030401→10.575401. Frozen mean is better than both frozen/cumulative ridge on this batch, and cumulative mean also narrowly beats cumulative ridge. The common degradation is compatible with adaptive design/distribution or endpoint/batch effects, but these records do not identify a biological or measurement cause. Do not invent one or correct the panel post hoc.

The gate fails BOTH branches: OLA violates every-batch ridge improvement, and OLA cumulative ridge fails the campaign mean control. Gate is correctly false, decision STOP_EXPANDING_THIS_FIXED_RIDGE_FEEDBACK_CONFIGURATION. This is not an all-feedback failure: FAC ordinary benefit is real within this fixed retrospective task. Conversely FAC benefit cannot establish transfer to OLA, independent patients or future tasks.

## Integrity and scientific limits

Source code writes forecasts and SHA before scoring; frozen wrapper records input hashes before invoking numerical main. Matching hashes and artifacts support this execution chain, not cryptographic proof of response secrecy or unique invocation against a malicious operator. CSV bytes and future labels were available in the process; legal per-forecast exclusion is the claim. Source-level timestamps/order plus execution receipt establish the intended save-before-score record, not external trusted timestamps.

No clinical effect-size threshold, replicate-level uncertainty, independent-task test, counterfactual action oracle or optimizer superiority is established. Endpoint values above100 remain unaltered. Adding labels also expands observed design coverage; these comparisons concern ordinary feedback availability, not same-history update-law quality. The small ridge and local/mean controls do not exhaust strong direct models.

No new mechanism emerged. Keep world-model, agent, inherited-U, joint and improved-improver contributions NOT_ESTABLISHED. Preserve this panel, its FAC benefit and OLA failure, without tuning/re-encoding or choosing a later-response-conditioned hybrid. Further research requires a distinct prior-grounded candidate and independent evaluation evidence rather than rescuing this stopped configuration.
