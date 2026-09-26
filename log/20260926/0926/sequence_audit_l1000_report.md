# L1000 independent decision validation

Protocol frozen 2026-09-26T22:23:12.074133+08:00 before any L1000 validator reading or decision. Gates: {'LT': True, 'T': True}. Decision (tier LT): **SHADOW**.

## Rates

|Tier|Arm|Episodes|Correct|Wrong|Undetermined|Deferred|Utility|Measurements|Days|Neutral first|Second after neutral|Fallbacks|
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|LT|da_unconditioned|6880|0.121|0.004|0.527|0.348|0.112|0.97|5.62|3801|2216|0|
|LT|two_step_fallback|6880|0.118|0.005|0.557|0.320|0.109|0.97|5.53|4031|1986|581|
|LT|two_step|6880|0.117|0.005|0.530|0.348|0.107|0.88|5.05|3838|1599|0|
|LT|da|6880|0.116|0.004|0.532|0.348|0.107|0.88|5.05|3801|1555|0|
|LT|one_step_utility|6880|0.114|0.005|0.533|0.348|0.105|0.81|4.66|3790|1061|0|
|LT|fixed|6880|0.106|0.006|0.888|0.000|0.095|1.93|10.86|6432|6432|0|
|LT|production|6880|0.070|0.004|0.926|0.000|0.063|1.93|10.16|6432|6432|0|
|LT|two_step_permuted|6880|0.033|0.002|0.544|0.421|0.030|0.68|3.92|3751|725|0|
|T|fixed|3052|0.230|0.011|0.759|0.000|0.208|1.85|10.34|2591|2591|0|
|T|production|3052|0.230|0.011|0.759|0.000|0.208|1.85|10.34|2591|2591|0|
|T|da_unconditioned|3052|0.203|0.006|0.581|0.210|0.191|0.92|5.31|1804|397|0|
|T|da|3052|0.199|0.005|0.586|0.210|0.188|0.82|4.69|1804|82|0|
|T|two_step_fallback|3052|0.202|0.007|0.613|0.178|0.188|0.92|5.22|1916|284|194|
|T|two_step|3052|0.200|0.006|0.590|0.205|0.188|0.85|4.86|1836|172|0|
|T|one_step_utility|3052|0.198|0.006|0.586|0.210|0.187|0.81|4.62|1803|49|0|
|T|two_step_permuted|3052|0.058|0.003|0.362|0.577|0.052|0.44|2.46|1105|48|0|

## Paired contrasts (95% interval, component-clustered bootstrap)

|Tier|Left|Right|Metric|Difference|95% CI|Units|
|---|---|---|---|---:|---|---:|
|LT|two_step_fallback|two_step|utility|+0.001|[+0.000, +0.003]|256|
|LT|two_step_fallback|two_step|wrong|+0.000|[+0.000, +0.000]|256|
|LT|two_step_fallback|two_step|correct|+0.002|[+0.001, +0.003]|256|
|LT|two_step_fallback|two_step|measurements|+0.084|[+0.072, +0.098]|256|
|LT|two_step_fallback|two_step|days|+0.481|[+0.408, +0.556]|256|
|LT|two_step_fallback|fixed|utility|+0.014|[-0.012, +0.041]|256|
|LT|two_step_fallback|fixed|wrong|-0.001|[-0.005, +0.003]|256|
|LT|two_step_fallback|fixed|correct|+0.012|[-0.013, +0.039]|256|
|LT|two_step_fallback|fixed|measurements|-0.966|[-1.020, -0.909]|256|
|LT|two_step_fallback|fixed|days|-5.326|[-5.637, -4.995]|256|
|LT|two_step_fallback|da|utility|+0.001|[-0.002, +0.006]|256|
|LT|two_step_fallback|da|wrong|+0.001|[+0.000, +0.002]|256|
|LT|two_step_fallback|da|correct|+0.003|[+0.000, +0.007]|256|
|LT|two_step_fallback|da|measurements|+0.091|[+0.072, +0.112]|256|
|LT|two_step_fallback|da|days|+0.485|[+0.375, +0.602]|256|
|LT|two_step_fallback|da_unconditioned|utility|-0.004|[-0.009, +0.000]|256|
|LT|two_step_fallback|da_unconditioned|wrong|+0.001|[+0.000, +0.001]|256|
|LT|two_step_fallback|da_unconditioned|correct|-0.002|[-0.007, +0.001]|256|
|LT|two_step_fallback|da_unconditioned|measurements|-0.005|[-0.027, +0.015]|256|
|LT|two_step_fallback|da_unconditioned|days|-0.086|[-0.209, +0.033]|256|
|LT|two_step_fallback|production|utility|+0.046|[+0.016, +0.080]|256|
|LT|two_step_fallback|production|wrong|+0.001|[-0.003, +0.005]|256|
|LT|two_step_fallback|production|correct|+0.048|[+0.019, +0.081]|256|
|LT|two_step_fallback|production|measurements|-0.966|[-1.020, -0.909]|256|
|LT|two_step_fallback|production|days|-4.625|[-4.923, -4.307]|256|
|LT|two_step_fallback|one_step_utility|utility|+0.003|[-0.000, +0.008]|256|
|LT|two_step_fallback|one_step_utility|wrong|+0.000|[-0.000, +0.001]|256|
|LT|two_step_fallback|one_step_utility|correct|+0.004|[+0.001, +0.009]|256|
|LT|two_step_fallback|one_step_utility|measurements|+0.163|[+0.144, +0.181]|256|
|LT|two_step_fallback|one_step_utility|days|+0.870|[+0.762, +0.977]|256|
|LT|two_step_fallback|two_step_permuted|utility|+0.079|[+0.054, +0.109]|256|
|LT|two_step_fallback|two_step_permuted|wrong|+0.003|[+0.001, +0.006]|256|
|LT|two_step_fallback|two_step_permuted|correct|+0.085|[+0.059, +0.115]|256|
|LT|two_step_fallback|two_step_permuted|measurements|+0.284|[+0.216, +0.349]|256|
|LT|two_step_fallback|two_step_permuted|days|+1.616|[+1.224, +1.989]|256|
|LT|two_step|two_step_permuted|utility|+0.077|[+0.053, +0.106]|256|
|LT|two_step|fixed|utility|+0.012|[-0.013, +0.039]|256|
|LT|two_step|two_step_permuted|wrong|+0.003|[+0.001, +0.005]|256|
|LT|two_step|fixed|wrong|-0.001|[-0.005, +0.003]|256|
|LT|two_step|two_step_permuted|correct|+0.084|[+0.058, +0.113]|256|
|LT|two_step|fixed|correct|+0.010|[-0.014, +0.038]|256|
|T|two_step_fallback|two_step|utility|+0.001|[-0.003, +0.004]|170|
|T|two_step_fallback|two_step|wrong|+0.001|[+0.000, +0.003]|170|
|T|two_step_fallback|two_step|correct|+0.003|[+0.001, +0.005]|170|
|T|two_step_fallback|two_step|measurements|+0.064|[+0.046, +0.089]|170|
|T|two_step_fallback|two_step|days|+0.361|[+0.257, +0.509]|170|
|T|two_step_fallback|fixed|utility|-0.020|[-0.043, -0.001]|170|
|T|two_step_fallback|fixed|wrong|-0.004|[-0.008, +0.000]|170|
|T|two_step_fallback|fixed|correct|-0.028|[-0.047, -0.012]|170|
|T|two_step_fallback|fixed|measurements|-0.934|[-1.006, -0.858]|170|
|T|two_step_fallback|fixed|days|-5.123|[-5.558, -4.672]|170|
|T|two_step_fallback|da|utility|+0.000|[-0.006, +0.004]|170|
|T|two_step_fallback|da|wrong|+0.002|[+0.000, +0.004]|170|
|T|two_step_fallback|da|correct|+0.003|[+0.001, +0.006]|170|
|T|two_step_fallback|da|measurements|+0.098|[+0.077, +0.122]|170|
|T|two_step_fallback|da|days|+0.533|[+0.415, +0.666]|170|
|T|two_step_fallback|da_unconditioned|utility|-0.003|[-0.009, +0.002]|170|
|T|two_step_fallback|da_unconditioned|wrong|+0.001|[-0.001, +0.004]|170|
|T|two_step_fallback|da_unconditioned|correct|-0.001|[-0.004, +0.002]|170|
|T|two_step_fallback|da_unconditioned|measurements|-0.005|[-0.031, +0.022]|170|
|T|two_step_fallback|da_unconditioned|days|-0.087|[-0.235, +0.069]|170|
|T|two_step_fallback|production|utility|-0.020|[-0.043, -0.001]|170|
|T|two_step_fallback|production|wrong|-0.004|[-0.008, +0.000]|170|
|T|two_step_fallback|production|correct|-0.028|[-0.047, -0.012]|170|
|T|two_step_fallback|production|measurements|-0.934|[-1.006, -0.858]|170|
|T|two_step_fallback|production|days|-5.123|[-5.558, -4.672]|170|
|T|two_step_fallback|one_step_utility|utility|+0.001|[-0.005, +0.006]|170|
|T|two_step_fallback|one_step_utility|wrong|+0.001|[-0.000, +0.004]|170|
|T|two_step_fallback|one_step_utility|correct|+0.004|[+0.002, +0.007]|170|
|T|two_step_fallback|one_step_utility|measurements|+0.109|[+0.085, +0.137]|170|
|T|two_step_fallback|one_step_utility|days|+0.596|[+0.461, +0.757]|170|
|T|two_step_fallback|two_step_permuted|utility|+0.137|[+0.095, +0.186]|170|
|T|two_step_fallback|two_step_permuted|wrong|+0.004|[+0.000, +0.008]|170|
|T|two_step_fallback|two_step_permuted|correct|+0.144|[+0.104, +0.194]|170|
|T|two_step_fallback|two_step_permuted|measurements|+0.477|[+0.402, +0.554]|170|
|T|two_step_fallback|two_step_permuted|days|+2.758|[+2.352, +3.190]|170|
|T|two_step|two_step_permuted|utility|+0.136|[+0.096, +0.185]|170|
|T|two_step|fixed|utility|-0.021|[-0.044, -0.001]|170|
|T|two_step|two_step_permuted|wrong|+0.003|[-0.001, +0.007]|170|
|T|two_step|fixed|wrong|-0.005|[-0.009, -0.001]|170|
|T|two_step|two_step_permuted|correct|+0.142|[+0.102, +0.190]|170|
|T|two_step|fixed|correct|-0.030|[-0.050, -0.014]|170|

## Unit sensitivity

|Tier|Right|Metric|Unit|Units|95% CI or range|
|---|---|---|---|---:|---|
|LT|two_step|utility|identity|339|[+0.000, +0.002]|
|LT|two_step|utility|batch_cohort|48|[+0.000, +0.002]|
|LT|two_step|utility|leave_one_batch_out||[+0.001, +0.002]|
|LT|two_step|wrong|identity|339|[+0.000, +0.000]|
|LT|two_step|wrong|batch_cohort|48|[+0.000, +0.001]|
|LT|two_step|wrong|leave_one_batch_out||[+0.000, +0.000]|
|LT|fixed|utility|identity|339|[-0.010, +0.037]|
|LT|fixed|utility|batch_cohort|48|[-0.014, +0.047]|
|LT|fixed|utility|leave_one_batch_out||[+0.006, +0.023]|
|LT|fixed|wrong|identity|339|[-0.004, +0.003]|
|LT|fixed|wrong|batch_cohort|48|[-0.003, +0.002]|
|LT|fixed|wrong|leave_one_batch_out||[-0.001, +0.000]|
|T|two_step|utility|identity|216|[-0.003, +0.004]|
|T|two_step|utility|batch_cohort|43|[-0.003, +0.004]|
|T|two_step|utility|leave_one_batch_out||[+0.000, +0.002]|
|T|two_step|wrong|identity|216|[+0.000, +0.003]|
|T|two_step|wrong|batch_cohort|43|[+0.000, +0.002]|
|T|two_step|wrong|leave_one_batch_out||[+0.000, +0.001]|
|T|fixed|utility|identity|216|[-0.042, -0.001]|
|T|fixed|utility|batch_cohort|43|[-0.040, +0.003]|
|T|fixed|utility|leave_one_batch_out||[-0.028, -0.014]|
|T|fixed|wrong|identity|216|[-0.008, -0.000]|
|T|fixed|wrong|batch_cohort|43|[-0.009, +0.001]|
|T|fixed|wrong|leave_one_batch_out||[-0.005, -0.001]|

## Contrast-support strata

|Tier|Stratum|Arm|Episodes|Correct|Wrong|Utility|Measurements|
|---|---|---|---:|---:|---:|---:|---:|
|LT|<=3|da|334|0.156|0.000|0.156|0.76|
|LT|<=3|fixed|334|0.039|0.000|0.039|1.97|
|LT|<=3|two_step|334|0.162|0.000|0.162|0.74|
|LT|<=3|two_step_fallback|334|0.162|0.000|0.162|0.89|
|LT|4-7|da|3411|0.140|0.004|0.132|0.98|
|LT|4-7|fixed|3411|0.135|0.006|0.123|1.92|
|LT|4-7|two_step|3411|0.141|0.005|0.132|0.95|
|LT|4-7|two_step_fallback|3411|0.143|0.005|0.134|1.08|
|LT|>=8|da|3135|0.085|0.005|0.075|0.78|
|LT|>=8|fixed|3135|0.083|0.006|0.070|1.95|
|LT|>=8|two_step|3135|0.086|0.005|0.075|0.82|
|LT|>=8|two_step_fallback|3135|0.087|0.006|0.076|0.86|
|T|4-7|da|2104|0.223|0.004|0.215|0.82|
|T|4-7|fixed|2104|0.257|0.009|0.239|1.83|
|T|4-7|two_step|2104|0.224|0.005|0.213|0.83|
|T|4-7|two_step_fallback|2104|0.227|0.007|0.214|0.91|
|T|>=8|da|948|0.145|0.007|0.130|0.81|
|T|>=8|fixed|948|0.170|0.015|0.140|1.90|
|T|>=8|two_step|948|0.146|0.007|0.131|0.91|
|T|>=8|two_step_fallback|948|0.147|0.007|0.132|0.92|

## Step-1 forecast calibration (truth-branch correct-elimination probability)

- all: {'rows': 61144, 'mean_forecast': 0.07829349037631726, 'realised': 0.06005495224388329, 'ece': 0.03746613877248101, 'brier': 0.04016895279949926}
- tier_LT: {'rows': 55040, 'mean_forecast': 0.06823962155267513, 'realised': 0.048673691860465114, 'ece': 0.0337089472093617, 'brier': 0.03322446597119107}
- tier_T: {'rows': 6104, 'mean_forecast': 0.16894960768517422, 'realised': 0.16268020969855831, 'ece': 0.07134487789995272, 'brier': 0.10278765447546301}
- support_2-4: {'rows': 2650, 'mean_forecast': 0.13717061332699487, 'realised': 0.06377358490566037, 'ece': 0.09361017112593403, 'brier': 0.06340017564793438}
- support_>=5: {'rows': 58494, 'mean_forecast': 0.07562613345390991, 'realised': 0.059886484083837656, 'ece': 0.03492260121757538, 'brier': 0.03911649031534099}
- refused_share: 0.0

## Plate diagnostic (eliminating step-1 readings)

- all: {'eliminating_readings': 3850, 'nearest_template_same_batch': 0.167012987012987, 'templates_same_batch_share': 0.09419150690579263}
- correct: {'eliminating_readings': 3672, 'nearest_template_same_batch': 0.15359477124183007, 'templates_same_batch_share': 0.08354892883079158}
- wrong: {'eliminating_readings': 178, 'nearest_template_same_batch': 0.4438202247191011, 'templates_same_batch_share': 0.3137395220260389}

## Decision checks

- {'reject_utility': False, 'reject_wrong': False, 'gain_over_two_step': True, 'wrong_vs_two_step_ok': True, 'gain_over_fixed': False, 'wrong_vs_fixed_ok': True, 'tier_T_consistent': False}
