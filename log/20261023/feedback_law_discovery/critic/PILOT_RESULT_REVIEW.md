# Independent pilot result audit and decision

2026-10-23. Executed only critic/audit_pilot.py, which does not import the pilot, train a model or read X/events/G. It reads only permitted cache Y/groups/contexts/items and saved predictions. Freeze hashes, successful wrapper receipt and cache hash verified. Script/result sealed alongside this report.

## Independently reconstructed result

Rebuilt the historical subject-salted five folds, source-only finite-entry drug selection, source means/scales, fixed sample/drug hash support selection and query mask. Source normalization/covariance uses413contexts; training391; development101samples/90patients;123drugs. No source/development patient overlap. Eight supports per sample excluded from every query metric.

Recomputed raw-AUC squared error and top3 query-panel regret using a separate Python stable-sort implementation and patient-cluster averaging for all14 saved records. Maximum discrepancy from root metrics was5.4569682106375694e-12. No model had a tied predicted score at the top3 boundary in any development sample, so tie resolution did not affect shortlist selection. Missing outcomes were excluded, not imputed as evaluation truth. Root SUMMARY was read only after independent gate computation and agrees with the result below.

| Method | Mean MSE | Mean top3 regret |
|---|---:|---:|
| Ordinary covariance conditional completion |2054.557791|37.054722|
| Random-order augmented updater |2116.203832|38.974889|
| Consistency-trained updater |2143.422020|38.683091|
| DeepSets |2211.235133|39.824282|

Consistency training worsens MSE relative to augmentation in each of the three seeds. Regret improves only in seed0; seeds1and2 worsen. Thus0/3seeds pass the required joint functional gate. Averaging seeds, it beats mean and DeepSets on both metrics but loses both to ordinary covariance. The frozen continuation criterion is FALSE, independently of any interpretation of lower serialization sensitivity.

## Cost and scientific scope

Receipt reports successful exit0 and wrapper walltime29.17seconds; reported pilot overall time25.03seconds. These timings are retained evidence, not independently repeated measurements. Matched episode/view counts do not mean matched FLOPs; consistent adds backward work. Query view/replay counts are not new biological observations. Source and target record availability is shared among arms but conditions the retrospective endpoint.

Static pre-execution code review plus source-only reconstruction finds no implemented development-query training path. Saved-prediction reconstruction cannot independently prove every training tensor/access or reproduce optimizer trajectories; no such stronger claim is made. This is exposed development evidence, not independent confirmation, and the raw AUC shortlist is not clinical efficacy. It tests no RNA state contribution, active acquisition, inherited update algorithm or improved-improver capability.

## Binding disposition

STOP_EXPANDING_THIS_FIXED_CONSISTENCY_CONFIGURATION. Do not search gamma/width/seeds/subgroups or add modules to rescue this configuration. The useful result is precise: reducing serialization/partition sensitivity in this instantiated meta-updater was insufficient for the frozen functional success criterion, and a cheap ordinary same-feedback covariance solver remained stronger. This does not prove all symmetry constraints useless or rule out a separately specified biological update law. No core/world/agent/inheritance/RSI GO follows.
