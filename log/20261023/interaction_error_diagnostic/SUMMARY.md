# Frozen development run: descriptive results

Published full-screen-conditioned GI units; two masks averaged within each context. Negative MSE change means improvement. Ranking change is identity-minus-score-direct regret.

|Support|Context|Source-mean MSE|Score-direct MSE|Identity MSE|Identity MSE change|Regret change|Unseen-endpoint query fraction|
|---|---|---:|---:|---:|---:|---:|---:|
|128|MCF7|0.99259|1.00145|1.05162|+5.01%|+0.34135|51.72%|
|128|MDAMB231|1.09407|1.06144|1.03624|-2.37%|+0.09094|51.72%|
|128|MCF10A|1.16205|1.02174|1.03325|+1.13%|+0.03702|51.72%|
|128|CAL27|0.97279|0.94041|0.95352|+1.39%|-0.28022|51.72%|
|128|CAL33|1.07315|1.05742|1.16966|+10.61%|+0.92026|51.72%|

Support128 equal-context mean mse: `{"source_mean": 1.0589294663709374, "support_mean": 1.016479837626943, "calibration": 0.9472767332788575, "score_direct": 1.0164904264787415, "identity_ordinary": 1.048857458920742, "identity_permuted_labels": 1.0823659732888997}`


Support128 equal-context mean bottom20_regret: `{"source_mean": 3.284750792521766, "support_mean": 4.366228124614981, "calibration": 3.284750792521766, "score_direct": 3.610862421117456, "identity_ordinary": 3.8327320779093252, "identity_permuted_labels": 4.333353232104775}`

|512|MCF7|0.99259|0.92184|0.91460|-0.79%|-0.00052|5.43%|
|512|MDAMB231|1.09407|0.97108|0.98353|+1.28%|-0.06671|5.43%|
|512|MCF10A|1.16205|0.98765|0.98315|-0.46%|-0.26689|5.43%|
|512|CAL27|0.97279|0.90522|0.90613|+0.10%|-0.02117|5.43%|
|512|CAL33|1.07315|0.95505|0.95750|+0.26%|+0.01309|5.43%|

Support512 equal-context mean mse: `{"source_mean": 1.0589294663709374, "support_mean": 1.0157635231685898, "calibration": 0.9407897310671446, "score_direct": 0.9481689266710381, "identity_ordinary": 0.9489820141147995, "identity_permuted_labels": 1.0448722920169922}`


Support512 equal-context mean bottom20_regret: `{"source_mean": 3.284750792521766, "support_mean": 4.366228124614981, "calibration": 3.284750792521766, "score_direct": 3.415543835857538, "identity_ordinary": 3.347102965032466, "identity_permuted_labels": 4.714567321861073}`


Screening gate: False; joint wins by budget: [(128, 0), (512, 2)]

Recorded main-run wall time 9.320s (imports outside this timer). Pipeline calls 520; estimator fits 397; kernel solves 171.

These totals include all registered tuning/refit/permutation operations. They exclude prior metadata tests/reviews and are not equal-cost comparisons or wet-screen savings. The identity permutation arm uses the true-support-selected configuration, so it is a negative-control diagnostic, not an independent null-selection test.
