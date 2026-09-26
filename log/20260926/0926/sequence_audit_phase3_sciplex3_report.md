# Matched replay: phase3_sciplex3_exploratory

SciPlex3 episodes already analysed by blocks 2 and 3 and the follow-up: exploratory, never confirmatory.
Every arm ran under the same menu, time order, two-measurement and 16-day budget, QC rule, stops and utility (+1 correct, -2 wrong, 0 otherwise).

## Rates

|Tier|QC rule|Arm|Correct|Wrong|Undetermined|Deferred|Utility|Measurements|Days|Neutral first|Second after neutral|Fallbacks|
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
|A|continue|fixed|0.640|0.057|0.304|0.000|0.527|1.63|11.05|196|196|0|
|A|continue|two_step_fallback|0.455|0.045|0.336|0.164|0.366|1.21|8.12|150|117|81|
|A|continue|magnitude|0.396|0.021|0.583|0.000|0.354|1.64|9.82|198|198|0|
|A|continue|da_unconditioned|0.426|0.039|0.357|0.179|0.348|1.22|7.93|142|126|0|
|A|continue|da|0.426|0.042|0.354|0.179|0.342|1.12|7.38|142|91|0|
|A|continue|one_step_utility|0.378|0.033|0.411|0.179|0.312|0.96|6.39|141|34|0|
|A|continue|two_step|0.381|0.036|0.408|0.176|0.310|0.97|6.43|147|41|0|
|A|continue|production|0.301|0.003|0.696|0.000|0.295|1.76|10.59|257|257|0|
|A|continue|two_step_permuted|0.301|0.009|0.360|0.330|0.283|0.74|5.04|121|21|0|
|A|stop|fixed|0.616|0.057|0.327|0.000|0.503|1.58|10.67|196|196|0|
|A|stop|two_step_fallback|0.440|0.045|0.351|0.164|0.351|1.18|7.92|150|117|80|
|A|stop|da_unconditioned|0.411|0.039|0.372|0.179|0.333|1.20|7.77|142|126|0|
|A|stop|magnitude|0.372|0.021|0.607|0.000|0.330|1.59|9.54|198|198|0|
|A|stop|da|0.411|0.042|0.369|0.179|0.327|1.09|7.22|142|91|0|
|A|stop|production|0.301|0.003|0.696|0.000|0.295|1.76|10.59|257|257|0|
|A|stop|two_step|0.366|0.036|0.423|0.176|0.295|0.95|6.25|147|41|0|
|A|stop|one_step_utility|0.357|0.033|0.432|0.179|0.292|0.92|6.11|141|34|0|
|A|stop|two_step_permuted|0.298|0.009|0.363|0.330|0.280|0.73|4.96|121|21|0|
|B|continue|fixed|0.582|0.049|0.369|0.000|0.485|1.52|9.10|1084|1084|0|
|B|continue|two_step_fallback|0.554|0.037|0.356|0.054|0.480|1.33|8.01|995|829|664|
|B|continue|da|0.528|0.031|0.368|0.074|0.467|1.17|6.99|921|510|0|
|B|continue|da_unconditioned|0.539|0.038|0.349|0.074|0.463|1.29|7.77|921|789|0|
|B|continue|magnitude|0.558|0.050|0.392|0.000|0.458|1.48|8.89|1026|1026|0|
|B|continue|one_step_utility|0.482|0.023|0.422|0.074|0.437|1.01|6.03|952|162|0|
|B|continue|two_step|0.482|0.026|0.420|0.071|0.430|1.03|6.16|970|203|0|
|B|continue|two_step_permuted|0.312|0.016|0.390|0.281|0.281|0.87|5.19|948|313|0|
|B|continue|production|0.172|0.006|0.822|0.000|0.160|1.88|11.28|1900|1900|0|
|B|stop|fixed|0.575|0.049|0.376|0.000|0.478|1.50|9.01|1084|1084|0|
|B|stop|two_step_fallback|0.552|0.037|0.357|0.054|0.478|1.33|7.98|995|829|663|
|B|stop|da|0.527|0.031|0.369|0.074|0.466|1.16|6.97|921|510|0|
|B|stop|da_unconditioned|0.538|0.038|0.350|0.074|0.462|1.29|7.75|921|789|0|
|B|stop|magnitude|0.551|0.050|0.399|0.000|0.451|1.48|8.85|1026|1026|0|
|B|stop|one_step_utility|0.481|0.023|0.423|0.074|0.435|1.00|6.01|952|162|0|
|B|stop|two_step|0.481|0.026|0.422|0.071|0.428|1.02|6.14|970|203|0|
|B|stop|two_step_permuted|0.312|0.016|0.391|0.281|0.280|0.86|5.18|948|313|0|
|B|stop|production|0.172|0.006|0.822|0.000|0.160|1.88|11.28|1900|1900|0|

## Paired two_step_fallback minus baseline (95% interval, skeleton-clustered bootstrap)

|Tier|QC rule|Baseline|Metric|Difference|95% CI|
|---|---|---|---|---:|---|
|A|continue|two_step|correct|+0.074|[+0.036, +0.119]|
|A|continue|two_step|wrong|+0.009|[+0.000, +0.024]|
|A|continue|two_step|utility|+0.057|[+0.006, +0.107]|
|A|continue|two_step|measurements|+0.241|[+0.179, +0.304]|
|A|continue|one_step_utility|correct|+0.077|[+0.036, +0.125]|
|A|continue|one_step_utility|wrong|+0.012|[+0.000, +0.027]|
|A|continue|one_step_utility|utility|+0.054|[-0.006, +0.113]|
|A|continue|one_step_utility|measurements|+0.253|[+0.185, +0.321]|
|A|continue|da|correct|+0.030|[-0.021, +0.083]|
|A|continue|da|wrong|+0.003|[-0.006, +0.015]|
|A|continue|da|utility|+0.024|[-0.030, +0.080]|
|A|continue|da|measurements|+0.095|[+0.048, +0.152]|
|A|continue|da_unconditioned|correct|+0.030|[-0.018, +0.083]|
|A|continue|da_unconditioned|wrong|+0.006|[+0.000, +0.015]|
|A|continue|da_unconditioned|utility|+0.018|[-0.036, +0.077]|
|A|continue|da_unconditioned|measurements|-0.009|[-0.048, +0.033]|
|A|continue|fixed|correct|-0.185|[-0.265, -0.104]|
|A|continue|fixed|wrong|-0.012|[-0.039, +0.021]|
|A|continue|fixed|utility|-0.161|[-0.286, -0.045]|
|A|continue|fixed|measurements|-0.420|[-0.580, -0.265]|
|A|continue|production|correct|+0.155|[+0.048, +0.268]|
|A|continue|production|wrong|+0.042|[+0.009, +0.080]|
|A|continue|production|utility|+0.071|[-0.080, +0.208]|
|A|continue|production|measurements|-0.554|[-0.729, -0.372]|
|A|continue|magnitude|correct|+0.060|[-0.021, +0.143]|
|A|continue|magnitude|wrong|+0.024|[-0.003, +0.057]|
|A|continue|magnitude|utility|+0.012|[-0.113, +0.116]|
|A|continue|magnitude|measurements|-0.426|[-0.586, -0.274]|
|A|continue|two_step_permuted|correct|+0.155|[+0.077, +0.235]|
|A|continue|two_step_permuted|wrong|+0.036|[+0.009, +0.068]|
|A|continue|two_step_permuted|utility|+0.083|[-0.036, +0.193]|
|A|continue|two_step_permuted|measurements|+0.470|[+0.360, +0.583]|
|A|stop|two_step|correct|+0.074|[+0.036, +0.119]|
|A|stop|two_step|wrong|+0.009|[+0.000, +0.024]|
|A|stop|two_step|utility|+0.057|[+0.006, +0.107]|
|A|stop|two_step|measurements|+0.238|[+0.176, +0.301]|
|A|stop|one_step_utility|correct|+0.083|[+0.042, +0.131]|
|A|stop|one_step_utility|wrong|+0.012|[+0.000, +0.027]|
|A|stop|one_step_utility|utility|+0.060|[+0.000, +0.116]|
|A|stop|one_step_utility|measurements|+0.262|[+0.199, +0.327]|
|A|stop|da|correct|+0.030|[-0.021, +0.083]|
|A|stop|da|wrong|+0.003|[-0.006, +0.015]|
|A|stop|da|utility|+0.024|[-0.030, +0.080]|
|A|stop|da|measurements|+0.092|[+0.045, +0.149]|
|A|stop|da_unconditioned|correct|+0.030|[-0.018, +0.083]|
|A|stop|da_unconditioned|wrong|+0.006|[+0.000, +0.015]|
|A|stop|da_unconditioned|utility|+0.018|[-0.036, +0.077]|
|A|stop|da_unconditioned|measurements|-0.012|[-0.051, +0.030]|
|A|stop|fixed|correct|-0.176|[-0.262, -0.086]|
|A|stop|fixed|wrong|-0.012|[-0.039, +0.021]|
|A|stop|fixed|utility|-0.152|[-0.280, -0.030]|
|A|stop|fixed|measurements|-0.399|[-0.563, -0.247]|
|A|stop|production|correct|+0.140|[+0.027, +0.253]|
|A|stop|production|wrong|+0.042|[+0.009, +0.080]|
|A|stop|production|utility|+0.057|[-0.095, +0.199]|
|A|stop|production|measurements|-0.580|[-0.750, -0.405]|
|A|stop|magnitude|correct|+0.068|[-0.018, +0.158]|
|A|stop|magnitude|wrong|+0.024|[-0.003, +0.057]|
|A|stop|magnitude|utility|+0.021|[-0.104, +0.131]|
|A|stop|magnitude|measurements|-0.405|[-0.569, -0.250]|
|A|stop|two_step_permuted|correct|+0.143|[+0.068, +0.220]|
|A|stop|two_step_permuted|wrong|+0.036|[+0.009, +0.068]|
|A|stop|two_step_permuted|utility|+0.071|[-0.048, +0.179]|
|A|stop|two_step_permuted|measurements|+0.452|[+0.342, +0.568]|
|B|continue|two_step|correct|+0.071|[+0.052, +0.091]|
|B|continue|two_step|wrong|+0.011|[+0.005, +0.018]|
|B|continue|two_step|utility|+0.050|[+0.025, +0.074]|
|B|continue|two_step|measurements|+0.307|[+0.263, +0.352]|
|B|continue|one_step_utility|correct|+0.072|[+0.052, +0.092]|
|B|continue|one_step_utility|wrong|+0.014|[+0.007, +0.023]|
|B|continue|one_step_utility|utility|+0.043|[+0.017, +0.070]|
|B|continue|one_step_utility|measurements|+0.329|[+0.284, +0.374]|
|B|continue|da|correct|+0.025|[+0.008, +0.043]|
|B|continue|da|wrong|+0.006|[+0.002, +0.011]|
|B|continue|da|utility|+0.013|[-0.009, +0.034]|
|B|continue|da|measurements|+0.169|[+0.138, +0.201]|
|B|continue|da_unconditioned|correct|+0.014|[-0.004, +0.032]|
|B|continue|da_unconditioned|wrong|-0.001|[-0.006, +0.004]|
|B|continue|da_unconditioned|utility|+0.016|[-0.005, +0.037]|
|B|continue|da_unconditioned|measurements|+0.039|[+0.011, +0.067]|
|B|continue|fixed|correct|-0.028|[-0.060, +0.004]|
|B|continue|fixed|wrong|-0.012|[-0.022, -0.001]|
|B|continue|fixed|utility|-0.005|[-0.049, +0.041]|
|B|continue|fixed|measurements|-0.182|[-0.238, -0.127]|
|B|continue|production|correct|+0.381|[+0.310, +0.450]|
|B|continue|production|wrong|+0.031|[+0.017, +0.046]|
|B|continue|production|utility|+0.319|[+0.239, +0.397]|
|B|continue|production|measurements|-0.545|[-0.607, -0.484]|
|B|continue|magnitude|correct|-0.004|[-0.035, +0.028]|
|B|continue|magnitude|wrong|-0.013|[-0.025, -0.001]|
|B|continue|magnitude|utility|+0.022|[-0.020, +0.066]|
|B|continue|magnitude|measurements|-0.148|[-0.205, -0.090]|
|B|continue|two_step_permuted|correct|+0.241|[+0.202, +0.280]|
|B|continue|two_step_permuted|wrong|+0.021|[+0.013, +0.031]|
|B|continue|two_step_permuted|utility|+0.199|[+0.154, +0.241]|
|B|continue|two_step_permuted|measurements|+0.469|[+0.407, +0.530]|
|B|stop|two_step|correct|+0.071|[+0.052, +0.091]|
|B|stop|two_step|wrong|+0.011|[+0.005, +0.018]|
|B|stop|two_step|utility|+0.050|[+0.025, +0.074]|
|B|stop|two_step|measurements|+0.307|[+0.263, +0.352]|
|B|stop|one_step_utility|correct|+0.072|[+0.052, +0.093]|
|B|stop|one_step_utility|wrong|+0.014|[+0.007, +0.023]|
|B|stop|one_step_utility|utility|+0.043|[+0.017, +0.070]|
|B|stop|one_step_utility|measurements|+0.329|[+0.283, +0.373]|
|B|stop|da|correct|+0.025|[+0.008, +0.043]|
|B|stop|da|wrong|+0.006|[+0.002, +0.011]|
|B|stop|da|utility|+0.013|[-0.009, +0.034]|
|B|stop|da|measurements|+0.168|[+0.137, +0.200]|
|B|stop|da_unconditioned|correct|+0.014|[-0.004, +0.032]|
|B|stop|da_unconditioned|wrong|-0.001|[-0.006, +0.004]|
|B|stop|da_unconditioned|utility|+0.016|[-0.005, +0.037]|
|B|stop|da_unconditioned|measurements|+0.038|[+0.010, +0.066]|
|B|stop|fixed|correct|-0.023|[-0.056, +0.011]|
|B|stop|fixed|wrong|-0.012|[-0.022, -0.001]|
|B|stop|fixed|utility|+0.000|[-0.045, +0.049]|
|B|stop|fixed|measurements|-0.172|[-0.228, -0.115]|
|B|stop|production|correct|+0.380|[+0.310, +0.447]|
|B|stop|production|wrong|+0.031|[+0.017, +0.046]|
|B|stop|production|utility|+0.318|[+0.237, +0.396]|
|B|stop|production|measurements|-0.550|[-0.611, -0.488]|
|B|stop|magnitude|correct|+0.001|[-0.032, +0.037]|
|B|stop|magnitude|wrong|-0.013|[-0.025, -0.001]|
|B|stop|magnitude|utility|+0.027|[-0.017, +0.074]|
|B|stop|magnitude|measurements|-0.145|[-0.202, -0.087]|
|B|stop|two_step_permuted|correct|+0.241|[+0.201, +0.279]|
|B|stop|two_step_permuted|wrong|+0.021|[+0.013, +0.031]|
|B|stop|two_step_permuted|utility|+0.198|[+0.154, +0.240]|
|B|stop|two_step_permuted|measurements|+0.467|[+0.406, +0.526]|

## Unit sensitivity (QC rule `continue`)

|Tier|Baseline|Metric|Unit|Units|95% CI or range|
|---|---|---|---|---:|---|
|A|two_step|correct|compound|42|[+0.036, +0.116]|
|A|two_step|correct|scaffold|39|[+0.035, +0.119]|
|A|two_step|correct|plate_cohort|2|[+0.000, +0.078]|
|A|two_step|correct|leave_one_plate_cohort_out||[+0.000, +0.078]|
|A|two_step|wrong|compound|42|[+0.000, +0.024]|
|A|two_step|wrong|scaffold|39|[+0.000, +0.023]|
|A|two_step|wrong|plate_cohort|2|[+0.000, +0.009]|
|A|two_step|wrong|leave_one_plate_cohort_out||[+0.000, +0.009]|
|A|two_step|utility|compound|42|[+0.006, +0.107]|
|A|two_step|utility|scaffold|39|[+0.003, +0.107]|
|A|two_step|utility|plate_cohort|2|[+0.000, +0.059]|
|A|two_step|utility|leave_one_plate_cohort_out||[+0.000, +0.059]|
|A|one_step_utility|correct|compound|42|[+0.036, +0.122]|
|A|one_step_utility|correct|scaffold|39|[+0.034, +0.125]|
|A|one_step_utility|correct|plate_cohort|2|[+0.000, +0.081]|
|A|one_step_utility|correct|leave_one_plate_cohort_out||[+0.000, +0.081]|
|A|one_step_utility|wrong|compound|42|[+0.000, +0.027]|
|A|one_step_utility|wrong|scaffold|39|[+0.000, +0.027]|
|A|one_step_utility|wrong|plate_cohort|2|[+0.000, +0.013]|
|A|one_step_utility|wrong|leave_one_plate_cohort_out||[+0.000, +0.013]|
|A|one_step_utility|utility|compound|42|[-0.003, +0.110]|
|A|one_step_utility|utility|scaffold|39|[-0.003, +0.108]|
|A|one_step_utility|utility|plate_cohort|2|[+0.000, +0.056]|
|A|one_step_utility|utility|leave_one_plate_cohort_out||[+0.000, +0.056]|
|A|fixed|correct|compound|42|[-0.271, -0.107]|
|A|fixed|correct|scaffold|39|[-0.266, -0.107]|
|A|fixed|correct|plate_cohort|2|[-0.194, +0.000]|
|A|fixed|correct|leave_one_plate_cohort_out||[-0.194, +0.000]|
|A|fixed|wrong|compound|42|[-0.039, +0.021]|
|A|fixed|wrong|scaffold|39|[-0.040, +0.020]|
|A|fixed|wrong|plate_cohort|2|[-0.013, +0.000]|
|A|fixed|wrong|leave_one_plate_cohort_out||[-0.013, +0.000]|
|A|fixed|utility|compound|42|[-0.286, -0.051]|
|A|fixed|utility|scaffold|39|[-0.281, -0.048]|
|A|fixed|utility|plate_cohort|2|[-0.169, +0.000]|
|A|fixed|utility|leave_one_plate_cohort_out||[-0.169, +0.000]|
|B|two_step|correct|compound|135|[+0.053, +0.092]|
|B|two_step|correct|scaffold|120|[+0.052, +0.091]|
|B|two_step|correct|plate_cohort|5|[+0.049, +0.086]|
|B|two_step|correct|leave_one_plate_cohort_out||[+0.066, +0.083]|
|B|two_step|wrong|compound|135|[+0.005, +0.018]|
|B|two_step|wrong|scaffold|120|[+0.005, +0.018]|
|B|two_step|wrong|plate_cohort|5|[+0.005, +0.019]|
|B|two_step|wrong|leave_one_plate_cohort_out||[+0.008, +0.013]|
|B|two_step|utility|compound|135|[+0.026, +0.075]|
|B|two_step|utility|scaffold|120|[+0.025, +0.074]|
|B|two_step|utility|plate_cohort|5|[+0.034, +0.068]|
|B|two_step|utility|leave_one_plate_cohort_out||[+0.040, +0.057]|
|B|one_step_utility|correct|compound|135|[+0.053, +0.093]|
|B|one_step_utility|correct|scaffold|120|[+0.052, +0.092]|
|B|one_step_utility|correct|plate_cohort|5|[+0.056, +0.082]|
|B|one_step_utility|correct|leave_one_plate_cohort_out||[+0.068, +0.080]|
|B|one_step_utility|wrong|compound|135|[+0.007, +0.022]|
|B|one_step_utility|wrong|scaffold|120|[+0.007, +0.023]|
|B|one_step_utility|wrong|plate_cohort|5|[+0.006, +0.026]|
|B|one_step_utility|wrong|leave_one_plate_cohort_out||[+0.011, +0.019]|
|B|one_step_utility|utility|compound|135|[+0.017, +0.070]|
|B|one_step_utility|utility|scaffold|120|[+0.015, +0.069]|
|B|one_step_utility|utility|plate_cohort|5|[+0.022, +0.066]|
|B|one_step_utility|utility|leave_one_plate_cohort_out||[+0.030, +0.049]|
|B|fixed|correct|compound|135|[-0.058, +0.005]|
|B|fixed|correct|scaffold|120|[-0.058, +0.007]|
|B|fixed|correct|plate_cohort|5|[-0.055, +0.006]|
|B|fixed|correct|leave_one_plate_cohort_out||[-0.038, -0.013]|
|B|fixed|wrong|compound|135|[-0.022, -0.002]|
|B|fixed|wrong|scaffold|120|[-0.023, -0.002]|
|B|fixed|wrong|plate_cohort|5|[-0.023, -0.004]|
|B|fixed|wrong|leave_one_plate_cohort_out||[-0.015, -0.006]|
|B|fixed|utility|compound|135|[-0.048, +0.042]|
|B|fixed|utility|scaffold|120|[-0.048, +0.046]|
|B|fixed|utility|plate_cohort|5|[-0.039, +0.040]|
|B|fixed|utility|leave_one_plate_cohort_out||[-0.019, +0.013]|

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
