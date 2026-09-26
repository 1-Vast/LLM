# Matched replay: phase2_matched_replay

SciPlex3 episodes already analysed by blocks 2 and 3 and the follow-up: exploratory, never confirmatory.
Every arm ran under the same menu, time order, two-measurement and 16-day budget, QC rule, stops and utility (+1 correct, -2 wrong, 0 otherwise).

## Rates

|Tier|QC rule|Arm|Correct|Wrong|Undetermined|Deferred|Utility|Measurements|Days|Neutral first|Second after neutral|Fallbacks|
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|A|continue|fixed|0.640|0.057|0.304|0.000|0.527|1.63|11.05|196|196|0|
|A|continue|magnitude|0.396|0.021|0.583|0.000|0.354|1.64|9.82|198|198|0|
|A|continue|da_unconditioned|0.426|0.039|0.357|0.179|0.348|1.22|7.93|142|126|0|
|A|continue|da|0.426|0.042|0.354|0.179|0.342|1.12|7.38|142|91|0|
|A|continue|one_step_utility|0.378|0.033|0.411|0.179|0.312|0.96|6.39|141|34|0|
|A|continue|two_step|0.381|0.036|0.408|0.176|0.310|0.97|6.43|147|41|0|
|A|continue|production|0.301|0.003|0.696|0.000|0.295|1.76|10.59|257|257|0|
|A|continue|two_step_permuted|0.301|0.009|0.360|0.330|0.283|0.74|5.04|121|21|0|
|A|stop|fixed|0.616|0.057|0.327|0.000|0.503|1.58|10.67|196|196|0|
|A|stop|da_unconditioned|0.411|0.039|0.372|0.179|0.333|1.20|7.77|142|126|0|
|A|stop|magnitude|0.372|0.021|0.607|0.000|0.330|1.59|9.54|198|198|0|
|A|stop|da|0.411|0.042|0.369|0.179|0.327|1.09|7.22|142|91|0|
|A|stop|production|0.301|0.003|0.696|0.000|0.295|1.76|10.59|257|257|0|
|A|stop|two_step|0.366|0.036|0.423|0.176|0.295|0.95|6.25|147|41|0|
|A|stop|one_step_utility|0.357|0.033|0.432|0.179|0.292|0.92|6.11|141|34|0|
|A|stop|two_step_permuted|0.298|0.009|0.363|0.330|0.280|0.73|4.96|121|21|0|
|B|continue|fixed|0.582|0.049|0.369|0.000|0.485|1.52|9.10|1084|1084|0|
|B|continue|da|0.528|0.031|0.368|0.074|0.467|1.17|6.99|921|510|0|
|B|continue|da_unconditioned|0.539|0.038|0.349|0.074|0.463|1.29|7.77|921|789|0|
|B|continue|magnitude|0.558|0.050|0.392|0.000|0.458|1.48|8.89|1026|1026|0|
|B|continue|one_step_utility|0.482|0.023|0.422|0.074|0.437|1.01|6.03|952|162|0|
|B|continue|two_step|0.482|0.026|0.420|0.071|0.430|1.03|6.16|970|203|0|
|B|continue|two_step_permuted|0.312|0.016|0.390|0.281|0.281|0.87|5.19|948|313|0|
|B|continue|production|0.172|0.006|0.822|0.000|0.160|1.88|11.28|1900|1900|0|
|B|stop|fixed|0.575|0.049|0.376|0.000|0.478|1.50|9.01|1084|1084|0|
|B|stop|da|0.527|0.031|0.369|0.074|0.466|1.16|6.97|921|510|0|
|B|stop|da_unconditioned|0.538|0.038|0.350|0.074|0.462|1.29|7.75|921|789|0|
|B|stop|magnitude|0.551|0.050|0.399|0.000|0.451|1.48|8.85|1026|1026|0|
|B|stop|one_step_utility|0.481|0.023|0.423|0.074|0.435|1.00|6.01|952|162|0|
|B|stop|two_step|0.481|0.026|0.422|0.071|0.428|1.02|6.14|970|203|0|
|B|stop|two_step_permuted|0.312|0.016|0.391|0.281|0.280|0.86|5.18|948|313|0|
|B|stop|production|0.172|0.006|0.822|0.000|0.160|1.88|11.28|1900|1900|0|

## Paired two_step minus baseline (95% interval, skeleton-clustered bootstrap)

|Tier|QC rule|Baseline|Metric|Difference|95% CI|
|---|---|---|---|---:|---|
|A|continue|one_step_utility|correct|+0.003|[-0.006, +0.012]|
|A|continue|one_step_utility|wrong|+0.003|[+0.000, +0.009]|
|A|continue|one_step_utility|utility|-0.003|[-0.027, +0.012]|
|A|continue|one_step_utility|measurements|+0.012|[-0.006, +0.033]|
|A|continue|da|correct|-0.045|[-0.080, -0.012]|
|A|continue|da|wrong|-0.006|[-0.021, +0.006]|
|A|continue|da|utility|-0.033|[-0.080, +0.015]|
|A|continue|da|measurements|-0.146|[-0.202, -0.089]|
|A|continue|da_unconditioned|correct|-0.045|[-0.095, +0.000]|
|A|continue|da_unconditioned|wrong|-0.003|[-0.015, +0.006]|
|A|continue|da_unconditioned|utility|-0.039|[-0.092, +0.015]|
|A|continue|da_unconditioned|measurements|-0.250|[-0.324, -0.182]|
|A|continue|fixed|correct|-0.259|[-0.360, -0.161]|
|A|continue|fixed|wrong|-0.021|[-0.054, +0.015]|
|A|continue|fixed|utility|-0.217|[-0.354, -0.077]|
|A|continue|fixed|measurements|-0.661|[-0.845, -0.479]|
|A|continue|production|correct|+0.080|[-0.015, +0.176]|
|A|continue|production|wrong|+0.033|[+0.006, +0.068]|
|A|continue|production|utility|+0.015|[-0.110, +0.131]|
|A|continue|production|measurements|-0.795|[-0.976, -0.607]|
|A|continue|magnitude|correct|-0.015|[-0.095, +0.060]|
|A|continue|magnitude|wrong|+0.015|[-0.009, +0.048]|
|A|continue|magnitude|utility|-0.045|[-0.158, +0.048]|
|A|continue|magnitude|measurements|-0.667|[-0.851, -0.482]|
|A|continue|two_step_permuted|correct|+0.080|[+0.006, +0.155]|
|A|continue|two_step_permuted|wrong|+0.027|[+0.006, +0.051]|
|A|continue|two_step_permuted|utility|+0.027|[-0.077, +0.122]|
|A|continue|two_step_permuted|measurements|+0.229|[+0.131, +0.330]|
|A|stop|one_step_utility|correct|+0.009|[-0.003, +0.024]|
|A|stop|one_step_utility|wrong|+0.003|[+0.000, +0.009]|
|A|stop|one_step_utility|utility|+0.003|[-0.021, +0.021]|
|A|stop|one_step_utility|measurements|+0.024|[+0.009, +0.042]|
|A|stop|da|correct|-0.045|[-0.080, -0.012]|
|A|stop|da|wrong|-0.006|[-0.021, +0.006]|
|A|stop|da|utility|-0.033|[-0.080, +0.015]|
|A|stop|da|measurements|-0.146|[-0.202, -0.089]|
|A|stop|da_unconditioned|correct|-0.045|[-0.095, +0.000]|
|A|stop|da_unconditioned|wrong|-0.003|[-0.015, +0.006]|
|A|stop|da_unconditioned|utility|-0.039|[-0.092, +0.015]|
|A|stop|da_unconditioned|measurements|-0.250|[-0.324, -0.182]|
|A|stop|fixed|correct|-0.250|[-0.354, -0.143]|
|A|stop|fixed|wrong|-0.021|[-0.054, +0.015]|
|A|stop|fixed|utility|-0.208|[-0.351, -0.065]|
|A|stop|fixed|measurements|-0.637|[-0.824, -0.461]|
|A|stop|production|correct|+0.065|[-0.030, +0.164]|
|A|stop|production|wrong|+0.033|[+0.006, +0.068]|
|A|stop|production|utility|+0.000|[-0.128, +0.119]|
|A|stop|production|measurements|-0.818|[-0.997, -0.643]|
|A|stop|magnitude|correct|-0.006|[-0.089, +0.077]|
|A|stop|magnitude|wrong|+0.015|[-0.009, +0.048]|
|A|stop|magnitude|utility|-0.036|[-0.155, +0.068]|
|A|stop|magnitude|measurements|-0.643|[-0.830, -0.464]|
|A|stop|two_step_permuted|correct|+0.068|[-0.003, +0.140]|
|A|stop|two_step_permuted|wrong|+0.027|[+0.006, +0.051]|
|A|stop|two_step_permuted|utility|+0.015|[-0.086, +0.104]|
|A|stop|two_step_permuted|measurements|+0.214|[+0.119, +0.310]|
|B|continue|one_step_utility|correct|+0.000|[-0.005, +0.006]|
|B|continue|one_step_utility|wrong|+0.004|[+0.000, +0.008]|
|B|continue|one_step_utility|utility|-0.007|[-0.018, +0.004]|
|B|continue|one_step_utility|measurements|+0.022|[+0.014, +0.030]|
|B|continue|da|correct|-0.046|[-0.062, -0.031]|
|B|continue|da|wrong|-0.004|[-0.010, +0.001]|
|B|continue|da|utility|-0.037|[-0.058, -0.017]|
|B|continue|da|measurements|-0.139|[-0.169, -0.109]|
|B|continue|da_unconditioned|correct|-0.057|[-0.078, -0.038]|
|B|continue|da_unconditioned|wrong|-0.012|[-0.020, -0.005]|
|B|continue|da_unconditioned|utility|-0.034|[-0.059, -0.009]|
|B|continue|da_unconditioned|measurements|-0.268|[-0.314, -0.221]|
|B|continue|fixed|correct|-0.100|[-0.144, -0.056]|
|B|continue|fixed|wrong|-0.022|[-0.036, -0.008]|
|B|continue|fixed|utility|-0.055|[-0.114, +0.004]|
|B|continue|fixed|measurements|-0.490|[-0.568, -0.412]|
|B|continue|production|correct|+0.310|[+0.245, +0.371]|
|B|continue|production|wrong|+0.020|[+0.010, +0.032]|
|B|continue|production|utility|+0.269|[+0.199, +0.338]|
|B|continue|production|measurements|-0.853|[-0.916, -0.788]|
|B|continue|magnitude|correct|-0.075|[-0.117, -0.036]|
|B|continue|magnitude|wrong|-0.024|[-0.039, -0.009]|
|B|continue|magnitude|utility|-0.028|[-0.083, +0.027]|
|B|continue|magnitude|measurements|-0.456|[-0.535, -0.375]|
|B|continue|two_step_permuted|correct|+0.170|[+0.134, +0.206]|
|B|continue|two_step_permuted|wrong|+0.011|[+0.003, +0.019]|
|B|continue|two_step_permuted|utility|+0.149|[+0.109, +0.186]|
|B|continue|two_step_permuted|measurements|+0.161|[+0.122, +0.201]|
|B|stop|one_step_utility|correct|+0.000|[-0.005, +0.006]|
|B|stop|one_step_utility|wrong|+0.004|[+0.000, +0.008]|
|B|stop|one_step_utility|utility|-0.007|[-0.018, +0.004]|
|B|stop|one_step_utility|measurements|+0.022|[+0.014, +0.030]|
|B|stop|da|correct|-0.046|[-0.062, -0.031]|
|B|stop|da|wrong|-0.004|[-0.010, +0.001]|
|B|stop|da|utility|-0.037|[-0.058, -0.017]|
|B|stop|da|measurements|-0.139|[-0.169, -0.110]|
|B|stop|da_unconditioned|correct|-0.057|[-0.078, -0.038]|
|B|stop|da_unconditioned|wrong|-0.012|[-0.020, -0.005]|
|B|stop|da_unconditioned|utility|-0.034|[-0.059, -0.009]|
|B|stop|da_unconditioned|measurements|-0.269|[-0.314, -0.222]|
|B|stop|fixed|correct|-0.094|[-0.139, -0.049]|
|B|stop|fixed|wrong|-0.022|[-0.036, -0.008]|
|B|stop|fixed|utility|-0.050|[-0.110, +0.011]|
|B|stop|fixed|measurements|-0.479|[-0.557, -0.400]|
|B|stop|production|correct|+0.309|[+0.244, +0.370]|
|B|stop|production|wrong|+0.020|[+0.010, +0.032]|
|B|stop|production|utility|+0.268|[+0.198, +0.336]|
|B|stop|production|measurements|-0.856|[-0.918, -0.793]|
|B|stop|magnitude|correct|-0.070|[-0.113, -0.027]|
|B|stop|magnitude|wrong|-0.024|[-0.039, -0.009]|
|B|stop|magnitude|utility|-0.023|[-0.080, +0.034]|
|B|stop|magnitude|measurements|-0.452|[-0.530, -0.373]|
|B|stop|two_step_permuted|correct|+0.169|[+0.134, +0.206]|
|B|stop|two_step_permuted|wrong|+0.011|[+0.003, +0.019]|
|B|stop|two_step_permuted|utility|+0.148|[+0.108, +0.185]|
|B|stop|two_step_permuted|measurements|+0.160|[+0.122, +0.198]|

## Unit sensitivity (QC rule `continue`)

|Tier|Baseline|Metric|Unit|Units|95% CI or range|
|---|---|---|---|---:|---|
|A|one_step_utility|correct|compound|42|[-0.006, +0.015]|
|A|one_step_utility|correct|scaffold|39|[-0.006, +0.013]|
|A|one_step_utility|correct|plate_cohort|2|[+0.000, +0.003]|
|A|one_step_utility|correct|leave_one_plate_cohort_out||[+0.000, +0.003]|
|A|one_step_utility|wrong|compound|42|[+0.000, +0.009]|
|A|one_step_utility|wrong|scaffold|39|[+0.000, +0.009]|
|A|one_step_utility|wrong|plate_cohort|2|[+0.000, +0.003]|
|A|one_step_utility|wrong|leave_one_plate_cohort_out||[+0.000, +0.003]|
|A|one_step_utility|utility|compound|42|[-0.027, +0.012]|
|A|one_step_utility|utility|scaffold|39|[-0.026, +0.012]|
|A|one_step_utility|utility|plate_cohort|2|[-0.003, +0.000]|
|A|one_step_utility|utility|leave_one_plate_cohort_out||[-0.003, +0.000]|
|A|fixed|correct|compound|42|[-0.366, -0.167]|
|A|fixed|correct|scaffold|39|[-0.365, -0.160]|
|A|fixed|correct|plate_cohort|2|[-0.272, +0.000]|
|A|fixed|correct|leave_one_plate_cohort_out||[-0.272, +0.000]|
|A|fixed|wrong|compound|42|[-0.054, +0.018]|
|A|fixed|wrong|scaffold|39|[-0.055, +0.015]|
|A|fixed|wrong|plate_cohort|2|[-0.022, +0.000]|
|A|fixed|wrong|leave_one_plate_cohort_out||[-0.022, +0.000]|
|A|fixed|utility|compound|42|[-0.354, -0.089]|
|A|fixed|utility|scaffold|39|[-0.351, -0.078]|
|A|fixed|utility|plate_cohort|2|[-0.228, +0.000]|
|A|fixed|utility|leave_one_plate_cohort_out||[-0.228, +0.000]|
|B|one_step_utility|correct|compound|135|[-0.005, +0.006]|
|B|one_step_utility|correct|scaffold|120|[-0.005, +0.006]|
|B|one_step_utility|correct|plate_cohort|5|[-0.005, +0.007]|
|B|one_step_utility|correct|leave_one_plate_cohort_out||[-0.003, +0.002]|
|B|one_step_utility|wrong|compound|135|[+0.000, +0.008]|
|B|one_step_utility|wrong|scaffold|120|[+0.000, +0.008]|
|B|one_step_utility|wrong|plate_cohort|5|[-0.001, +0.008]|
|B|one_step_utility|wrong|leave_one_plate_cohort_out||[+0.002, +0.006]|
|B|one_step_utility|utility|compound|135|[-0.018, +0.004]|
|B|one_step_utility|utility|scaffold|120|[-0.018, +0.003]|
|B|one_step_utility|utility|plate_cohort|5|[-0.019, -0.001]|
|B|one_step_utility|utility|leave_one_plate_cohort_out||[-0.010, -0.002]|
|B|fixed|correct|compound|135|[-0.144, -0.057]|
|B|fixed|correct|scaffold|120|[-0.141, -0.053]|
|B|fixed|correct|plate_cohort|5|[-0.135, -0.065]|
|B|fixed|correct|leave_one_plate_cohort_out||[-0.111, -0.079]|
|B|fixed|wrong|compound|135|[-0.037, -0.009]|
|B|fixed|wrong|scaffold|120|[-0.038, -0.009]|
|B|fixed|wrong|plate_cohort|5|[-0.041, -0.009]|
|B|fixed|wrong|leave_one_plate_cohort_out||[-0.028, -0.014]|
|B|fixed|utility|compound|135|[-0.113, +0.003]|
|B|fixed|utility|scaffold|120|[-0.112, +0.009]|
|B|fixed|utility|plate_cohort|5|[-0.104, -0.005]|
|B|fixed|utility|leave_one_plate_cohort_out||[-0.070, -0.027]|

## Fixed minus two-step correct rate, by the two-step path in discordant pairs

- A|continue: deferred_before_first +0.074, first_eliminated +0.003, first_neutral_continued +0.039, first_neutral_stopped +0.140, first_qc_failed_continued +0.003
- A|stop: deferred_before_first +0.074, first_eliminated -0.012, first_neutral_continued +0.039, first_neutral_stopped +0.140, first_qc_failed_stopped +0.009
- B|continue: deferred_before_first +0.024, first_eliminated -0.032, first_neutral_continued +0.006, first_neutral_stopped +0.101, first_qc_failed_continued -0.000
- B|stop: deferred_before_first +0.024, first_eliminated -0.037, first_neutral_continued +0.006, first_neutral_stopped +0.101

## Reproduction of the original follow-up records

- fixed|continue vs original fixed: 2496/2496 identical
- da_unconditioned|continue vs original da: 2496/2496 identical
- two_step|stop vs original two_step: 2496/2496 identical
- one_step_utility|stop vs original one_step_utility: 2496/2496 identical
- two_step_permuted|stop vs original two_step_permuted: 2496/2496 identical
