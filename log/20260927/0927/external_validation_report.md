# Locked development replay: decision, risk and ablation report

Status: internal replay on development data; not external validation. Records: 360,412. Freeze verified: True. Overall status of `maestro_vc`: **REJECTED**.

## sciplex3|A

Comparator (strongest baseline): `ridge`. Integrity problems: 0. Primary status: **INCONCLUSIVE**.

| Arm | Correct | Wrong | Decided | Selective risk | Measurements | Assay-days |
|---|---:|---:|---:|---:|---:|---:|
| `oracle` | 0.670 [0.533, 0.801] | 0.000 [0.000, 0.000] | 0.670 | 0.000 | 0.67 | 4.45 |
| `fixed` | 0.640 [0.500, 0.771] | 0.057 [0.018, 0.107] | 0.696 | 0.081 | 1.63 | 11.05 |
| `info_gain` | 0.467 [0.354, 0.586] | 0.057 [0.021, 0.095] | 0.524 | 0.108 | 1.58 | 11.23 |
| `sparse_two_step` | 0.452 [0.339, 0.574] | 0.036 [0.009, 0.063] | 0.488 | 0.073 | 1.15 | 7.55 |
| `random_legal` | 0.449 [0.333, 0.568] | 0.045 [0.018, 0.077] | 0.494 | 0.090 | 1.65 | 11.95 |
| `ridge` | 0.449 [0.327, 0.572] | 0.027 [0.006, 0.051] | 0.476 | 0.056 | 1.31 | 8.85 |
| `myopic_edv` | 0.438 [0.324, 0.557] | 0.039 [0.009, 0.068] | 0.476 | 0.081 | 1.11 | 7.58 |
| `maestro_masked` | 0.426 [0.310, 0.548] | 0.042 [0.012, 0.074] | 0.467 | 0.089 | 1.12 | 7.38 |
| `maestro_vc` | 0.426 [0.310, 0.548] | 0.042 [0.012, 0.074] | 0.467 | 0.089 | 1.12 | 7.38 |
| `maestro_vc_permuted` | 0.426 [0.310, 0.548] | 0.042 [0.012, 0.074] | 0.467 | 0.089 | 1.12 | 7.38 |
| `marginal_only` | 0.423 [0.304, 0.548] | 0.036 [0.009, 0.065] | 0.458 | 0.078 | 1.15 | 7.50 |
| `magnitude` | 0.396 [0.259, 0.530] | 0.021 [0.000, 0.051] | 0.417 | 0.050 | 1.64 | 9.82 |
| `magnitude_permuted` | 0.372 [0.235, 0.509] | 0.024 [0.003, 0.054] | 0.396 | 0.060 | 1.65 | 9.91 |
| `retrieval` | 0.366 [0.256, 0.482] | 0.033 [0.009, 0.062] | 0.399 | 0.082 | 0.88 | 5.91 |
| `cost_only` | 0.301 [0.167, 0.440] | 0.003 [0.000, 0.009] | 0.304 | 0.010 | 1.76 | 10.59 |
| `production_default` | 0.301 [0.167, 0.440] | 0.003 [0.000, 0.009] | 0.304 | 0.010 | 1.76 | 10.59 |
| `defer_floor` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 | n/a | 0.00 | 0.00 |

Primary comparison, `maestro_vc` minus the comparator (95%, clustered by the unit):

- correct -0.024 [-0.107, +0.057]; wrong +0.015 [-0.012, +0.042]; measurements -0.20 [-0.33, -0.07]; assay-days -1.46 [-2.51, -0.52]
- `maestro_vc` wrong-risk 0.042 [0.012, 0.074]
- gates: G1 True, G2 pass False / reject False, G3 non-inferior False / superior False / reject False, G4 False, G5 available False, G6 False

Secondary candidates (Bonferroni 98.75%):

- `production_default`: correct -0.149 [-0.256, -0.058], wrong -0.024 [-0.051, -0.003], measurements +0.45 [+0.26, +0.67] -> **REJECTED**
- `maestro_masked`: correct -0.024 [-0.128, +0.083], wrong +0.015 [-0.018, +0.054], measurements -0.20 [-0.38, -0.03] -> **INCONCLUSIVE**
- `sparse_two_step`: correct +0.003 [-0.095, +0.107], wrong +0.009 [-0.018, +0.036], measurements -0.16 [-0.33, -0.01] -> **INCONCLUSIVE**

Virtual-cell ablation:

- maestro_vc vs maestro_masked: first-step switch 0.006, any-step switch 0.006; correct +0.000 [+0.000, +0.000], wrong +0.000 [+0.000, +0.000]; zero: changed actions without a terminal gain
- maestro_vc vs maestro_vc_permuted: first-step switch 0.000, any-step switch 0.000; correct +0.000 [+0.000, +0.000], wrong +0.000 [+0.000, +0.000]; zero: the channel never changed an action
- magnitude vs cost_only: first-step switch 0.976, any-step switch 0.976; correct +0.095 [-0.027, +0.220], wrong +0.018 [-0.003, +0.048]; zero: changed actions without a terminal gain
- magnitude vs magnitude_permuted: first-step switch 0.095, any-step switch 0.247; correct +0.024 [+0.000, +0.068], wrong -0.003 [-0.009, +0.000]; zero: changed actions without a terminal gain

## sciplex3|B

Comparator (strongest baseline): `fixed`. Integrity problems: 0. Primary status: **REJECTED**.

| Arm | Correct | Wrong | Decided | Selective risk | Measurements | Assay-days |
|---|---:|---:|---:|---:|---:|---:|
| `oracle` | 0.668 [0.595, 0.741] | 0.000 [0.000, 0.000] | 0.668 | 0.000 | 0.67 | 4.01 |
| `fixed` | 0.582 [0.509, 0.660] | 0.049 [0.030, 0.068] | 0.631 | 0.077 | 1.52 | 9.10 |
| `magnitude_permuted` | 0.575 [0.506, 0.650] | 0.038 [0.022, 0.055] | 0.613 | 0.062 | 1.54 | 9.25 |
| `magnitude` | 0.558 [0.482, 0.634] | 0.050 [0.032, 0.070] | 0.608 | 0.082 | 1.48 | 8.89 |
| `sparse_two_step` | 0.530 [0.461, 0.601] | 0.031 [0.020, 0.045] | 0.561 | 0.055 | 1.25 | 7.53 |
| `myopic_edv` | 0.529 [0.461, 0.599] | 0.029 [0.018, 0.042] | 0.558 | 0.052 | 1.23 | 7.37 |
| `maestro_vc` | 0.528 [0.461, 0.599] | 0.031 [0.019, 0.044] | 0.559 | 0.055 | 1.17 | 6.99 |
| `maestro_vc_permuted` | 0.525 [0.458, 0.596] | 0.031 [0.019, 0.044] | 0.556 | 0.055 | 1.17 | 6.99 |
| `marginal_only` | 0.525 [0.455, 0.597] | 0.029 [0.019, 0.042] | 0.554 | 0.053 | 1.25 | 7.51 |
| `maestro_masked` | 0.515 [0.448, 0.583] | 0.030 [0.018, 0.043] | 0.545 | 0.054 | 1.17 | 7.04 |
| `info_gain` | 0.512 [0.448, 0.580] | 0.038 [0.024, 0.054] | 0.550 | 0.069 | 1.56 | 9.36 |
| `retrieval` | 0.478 [0.412, 0.548] | 0.026 [0.017, 0.038] | 0.504 | 0.052 | 0.98 | 5.87 |
| `ridge` | 0.391 [0.328, 0.461] | 0.031 [0.020, 0.044] | 0.423 | 0.074 | 1.44 | 8.65 |
| `random_legal` | 0.387 [0.329, 0.451] | 0.024 [0.015, 0.032] | 0.410 | 0.058 | 1.70 | 10.22 |
| `cost_only` | 0.172 [0.114, 0.238] | 0.006 [0.001, 0.013] | 0.178 | 0.034 | 1.88 | 11.28 |
| `production_default` | 0.172 [0.114, 0.238] | 0.006 [0.001, 0.013] | 0.178 | 0.034 | 1.88 | 11.28 |
| `defer_floor` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 | n/a | 0.00 | 0.00 |

Primary comparison, `maestro_vc` minus the comparator (95%, clustered by the unit):

- correct -0.054 [-0.095, -0.013]; wrong -0.018 [-0.030, -0.007]; measurements -0.35 [-0.42, -0.28]; assay-days -2.11 [-2.55, -1.66]
- `maestro_vc` wrong-risk 0.031 [0.019, 0.044]
- gates: G1 True, G2 pass True / reject False, G3 non-inferior False / superior False / reject True, G4 False, G5 available False, G6 False

Secondary candidates (Bonferroni 98.75%):

- `production_default`: correct -0.410 [-0.515, -0.310], wrong -0.043 [-0.069, -0.019], measurements +0.36 [+0.27, +0.46] -> **REJECTED**
- `maestro_masked`: correct -0.067 [-0.119, -0.015], wrong -0.019 [-0.034, -0.005], measurements -0.34 [-0.43, -0.25] -> **REJECTED**
- `sparse_two_step`: correct -0.052 [-0.108, +0.001], wrong -0.018 [-0.034, -0.002], measurements -0.26 [-0.36, -0.17] -> **INCONCLUSIVE**

Virtual-cell ablation:

- maestro_vc vs maestro_masked: first-step switch 0.147, any-step switch 0.192; correct +0.013 [+0.005, +0.022], wrong +0.001 [-0.002, +0.004]; positive
- maestro_vc vs maestro_vc_permuted: first-step switch 0.070, any-step switch 0.100; correct +0.003 [-0.003, +0.010], wrong +0.000 [-0.002, +0.002]; zero: changed actions without a terminal gain
- magnitude vs cost_only: first-step switch 0.993, any-step switch 1.000; correct +0.386 [+0.311, +0.462], wrong +0.044 [+0.025, +0.065]; positive
- magnitude vs magnitude_permuted: first-step switch 0.622, any-step switch 0.716; correct -0.018 [-0.058, +0.021], wrong +0.012 [-0.002, +0.027]; zero: changed actions without a terminal gain

## l1000|LT

Comparator (strongest baseline): `info_gain`. Integrity problems: 0. Primary status: **INCONCLUSIVE**.

| Arm | Correct | Wrong | Decided | Selective risk | Measurements | Assay-days |
|---|---:|---:|---:|---:|---:|---:|
| `oracle` | 0.168 [0.130, 0.214] | 0.000 [0.000, 0.000] | 0.168 | 0.000 | 0.17 | 0.95 |
| `info_gain` | 0.126 [0.093, 0.164] | 0.009 [0.006, 0.013] | 0.135 | 0.068 | 1.90 | 11.05 |
| `sparse_two_step` | 0.124 [0.091, 0.162] | 0.004 [0.002, 0.006] | 0.128 | 0.031 | 0.92 | 5.30 |
| `marginal_only` | 0.122 [0.089, 0.160] | 0.003 [0.002, 0.005] | 0.125 | 0.026 | 0.91 | 5.24 |
| `myopic_edv` | 0.120 [0.088, 0.158] | 0.004 [0.002, 0.006] | 0.124 | 0.033 | 0.91 | 5.26 |
| `ridge` | 0.118 [0.087, 0.154] | 0.003 [0.001, 0.004] | 0.121 | 0.022 | 0.90 | 5.05 |
| `maestro_vc` | 0.117 [0.085, 0.154] | 0.004 [0.002, 0.007] | 0.121 | 0.035 | 0.88 | 5.05 |
| `maestro_masked` | 0.116 [0.084, 0.153] | 0.004 [0.002, 0.007] | 0.120 | 0.035 | 0.88 | 5.05 |
| `maestro_vc_permuted` | 0.115 [0.084, 0.153] | 0.004 [0.002, 0.007] | 0.119 | 0.035 | 0.88 | 5.05 |
| `fixed` | 0.106 [0.074, 0.141] | 0.006 [0.003, 0.009] | 0.112 | 0.051 | 1.93 | 10.86 |
| `retrieval` | 0.098 [0.070, 0.131] | 0.003 [0.001, 0.005] | 0.101 | 0.029 | 0.62 | 3.58 |
| `random_legal` | 0.080 [0.059, 0.104] | 0.005 [0.002, 0.007] | 0.085 | 0.057 | 1.95 | 11.18 |
| `cost_only` | 0.070 [0.043, 0.100] | 0.004 [0.001, 0.007] | 0.074 | 0.051 | 1.93 | 10.16 |
| `magnitude` | 0.070 [0.043, 0.100] | 0.004 [0.001, 0.007] | 0.074 | 0.051 | 1.93 | 10.16 |
| `magnitude_permuted` | 0.070 [0.043, 0.100] | 0.004 [0.001, 0.007] | 0.074 | 0.051 | 1.93 | 10.16 |
| `production_default` | 0.070 [0.043, 0.100] | 0.004 [0.001, 0.007] | 0.074 | 0.051 | 1.93 | 10.16 |
| `defer_floor` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 | n/a | 0.00 | 0.00 |

Primary comparison, `maestro_vc` minus the comparator (95%, clustered by the unit):

- correct -0.010 [-0.019, -0.001]; wrong -0.005 [-0.007, -0.003]; measurements -1.02 [-1.07, -0.97]; assay-days -6.00 [-6.31, -5.67]
- `maestro_vc` wrong-risk 0.004 [0.002, 0.007]
- gates: G1 True, G2 pass True / reject False, G3 non-inferior False / superior False / reject False, G4 False, G5 available False, G6 False

Secondary candidates (Bonferroni 98.75%):

- `production_default`: correct -0.056 [-0.097, -0.015], wrong -0.005 [-0.011, -0.000], measurements +0.04 [+0.00, +0.07] -> **REJECTED**
- `maestro_masked`: correct -0.011 [-0.024, -0.001], wrong -0.005 [-0.008, -0.002], measurements -1.02 [-1.09, -0.95] -> **INCONCLUSIVE**
- `sparse_two_step`: correct -0.003 [-0.016, +0.010], wrong -0.005 [-0.008, -0.002], measurements -0.98 [-1.05, -0.90] -> **INCONCLUSIVE**

Virtual-cell ablation:

- maestro_vc vs maestro_masked: first-step switch 0.001, any-step switch 0.003; correct +0.001 [+0.000, +0.003], wrong +0.000 [+0.000, +0.000]; zero: changed actions without a terminal gain
- maestro_vc vs maestro_vc_permuted: first-step switch 0.002, any-step switch 0.003; correct +0.001 [+0.000, +0.003], wrong +0.000 [+0.000, +0.000]; zero: changed actions without a terminal gain
- magnitude vs cost_only: first-step switch 0.000, any-step switch 0.000; correct +0.000 [+0.000, +0.000], wrong +0.000 [+0.000, +0.000]; zero: the channel never changed an action
- magnitude vs magnitude_permuted: first-step switch 0.000, any-step switch 0.000; correct +0.000 [+0.000, +0.000], wrong +0.000 [+0.000, +0.000]; zero: the channel never changed an action

## l1000|T

Comparator (strongest baseline): `cost_only`. Integrity problems: 0. Primary status: **REJECTED**.

| Arm | Correct | Wrong | Decided | Selective risk | Measurements | Assay-days |
|---|---:|---:|---:|---:|---:|---:|
| `oracle` | 0.231 [0.171, 0.292] | 0.000 [0.000, 0.000] | 0.231 | 0.000 | 0.23 | 1.28 |
| `cost_only` | 0.230 [0.170, 0.291] | 0.011 [0.006, 0.016] | 0.241 | 0.045 | 1.85 | 10.34 |
| `fixed` | 0.230 [0.170, 0.291] | 0.011 [0.006, 0.016] | 0.241 | 0.045 | 1.85 | 10.34 |
| `magnitude` | 0.230 [0.170, 0.291] | 0.011 [0.006, 0.016] | 0.241 | 0.045 | 1.85 | 10.34 |
| `magnitude_permuted` | 0.230 [0.170, 0.291] | 0.011 [0.006, 0.016] | 0.241 | 0.045 | 1.85 | 10.34 |
| `production_default` | 0.230 [0.170, 0.291] | 0.011 [0.006, 0.016] | 0.241 | 0.045 | 1.85 | 10.34 |
| `info_gain` | 0.212 [0.155, 0.271] | 0.009 [0.004, 0.014] | 0.221 | 0.040 | 1.26 | 7.30 |
| `marginal_only` | 0.208 [0.154, 0.266] | 0.006 [0.002, 0.010] | 0.214 | 0.028 | 1.01 | 5.77 |
| `sparse_two_step` | 0.207 [0.153, 0.265] | 0.006 [0.003, 0.010] | 0.214 | 0.029 | 1.00 | 5.67 |
| `random_legal` | 0.205 [0.152, 0.263] | 0.010 [0.006, 0.015] | 0.216 | 0.047 | 1.40 | 8.06 |
| `myopic_edv` | 0.202 [0.148, 0.260] | 0.006 [0.003, 0.010] | 0.209 | 0.030 | 0.88 | 5.09 |
| `maestro_masked` | 0.199 [0.146, 0.256] | 0.005 [0.002, 0.009] | 0.204 | 0.026 | 0.82 | 4.69 |
| `maestro_vc` | 0.199 [0.146, 0.256] | 0.005 [0.002, 0.009] | 0.204 | 0.026 | 0.82 | 4.69 |
| `maestro_vc_permuted` | 0.199 [0.146, 0.256] | 0.005 [0.002, 0.009] | 0.204 | 0.026 | 0.82 | 4.69 |
| `retrieval` | 0.198 [0.145, 0.254] | 0.005 [0.002, 0.009] | 0.203 | 0.026 | 0.78 | 4.51 |
| `ridge` | 0.175 [0.125, 0.227] | 0.003 [0.001, 0.006] | 0.178 | 0.018 | 0.69 | 3.93 |
| `defer_floor` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 | n/a | 0.00 | 0.00 |

Primary comparison, `maestro_vc` minus the comparator (95%, clustered by the unit):

- correct -0.031 [-0.050, -0.014]; wrong -0.006 [-0.010, -0.001]; measurements -1.03 [-1.11, -0.96]; assay-days -5.66 [-6.09, -5.20]
- `maestro_vc` wrong-risk 0.005 [0.002, 0.009]
- gates: G1 True, G2 pass True / reject False, G3 non-inferior False / superior False / reject True, G4 False, G5 available False, G6 False

Secondary candidates (Bonferroni 98.75%):

- `production_default`: correct +0.000 [+0.000, +0.000], wrong +0.000 [+0.000, +0.000], measurements +0.00 [+0.00, +0.00] -> **INCONCLUSIVE**
- `maestro_masked`: correct -0.031 [-0.058, -0.011], wrong -0.006 [-0.011, +0.000], measurements -1.03 [-1.13, -0.94] -> **REJECTED**
- `sparse_two_step`: correct -0.023 [-0.044, -0.006], wrong -0.005 [-0.010, +0.001], measurements -0.85 [-0.94, -0.76] -> **INCONCLUSIVE**

Virtual-cell ablation:

- maestro_vc vs maestro_masked: first-step switch 0.000, any-step switch 0.000; correct +0.000 [+0.000, +0.000], wrong +0.000 [+0.000, +0.000]; zero: the channel never changed an action
- maestro_vc vs maestro_vc_permuted: first-step switch 0.000, any-step switch 0.000; correct +0.000 [+0.000, +0.000], wrong +0.000 [+0.000, +0.000]; zero: the channel never changed an action
- magnitude vs cost_only: first-step switch 0.000, any-step switch 0.000; correct +0.000 [+0.000, +0.000], wrong +0.000 [+0.000, +0.000]; zero: the channel never changed an action
- magnitude vs magnitude_permuted: first-step switch 0.000, any-step switch 0.000; correct +0.000 [+0.000, +0.000], wrong +0.000 [+0.000, +0.000]; zero: the channel never changed an action

## Prediction diagnostics (secondary)

| Tier | Rows (detected) | VC cosine | Ridge cosine | Training-mean cosine | VC - mean | Ridge - mean |
|---|---:|---:|---:|---:|---:|---:|
| l1000|LT | 190 | 0.434 | 0.480 | 0.401 | +0.020 [-0.046, +0.081] | +0.079 [+0.052, +0.104] |
| l1000|T | 96 | 0.386 | 0.447 | 0.384 | -0.021 [-0.093, +0.053] | +0.063 [+0.032, +0.095] |
| sciplex3|A | 144 | 0.452 | 0.496 | 0.408 | +0.044 [-0.055, +0.130] | +0.089 [+0.039, +0.131] |
| sciplex3|B | 691 | 0.415 | 0.438 | 0.363 | +0.052 [+0.020, +0.082] | +0.075 [+0.050, +0.099] |

## Calibration of chosen-action forecasts (diagnostic)

| Arm | n | P(correct) mean | observed | ECE | intercept | slope | P(wrong) mean | observed wrong |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| l1000|LT|maestro_vc | 6040 | 0.169 | 0.133 | 0.055 | -0.53 | 0.26 | 0.001 | 0.005 |
| l1000|LT|myopic_edv | 6252 | 0.172 | 0.132 | 0.040 | -0.43 | 1.15 | 0.036 | 0.004 |
| l1000|LT|sparse_two_step | 6357 | 0.168 | 0.134 | 0.040 | -0.37 | 1.14 | 0.036 | 0.004 |
| l1000|T|maestro_vc | 2493 | 0.269 | 0.243 | 0.081 | -0.23 | 0.22 | 0.003 | 0.006 |
| l1000|T|myopic_edv | 2690 | 0.248 | 0.230 | 0.065 | -0.14 | 0.95 | 0.045 | 0.007 |
| l1000|T|sparse_two_step | 3041 | 0.235 | 0.208 | 0.057 | -0.21 | 0.94 | 0.043 | 0.006 |
| sciplex3|A|maestro_vc | 364 | 0.518 | 0.393 | 0.223 | -0.84 | 0.11 | 0.002 | 0.038 |
| sciplex3|A|myopic_edv | 360 | 0.495 | 0.408 | 0.140 | -0.46 | 0.72 | 0.059 | 0.036 |
| sciplex3|A|sparse_two_step | 377 | 0.491 | 0.403 | 0.139 | -0.46 | 0.65 | 0.055 | 0.032 |
| sciplex3|B|maestro_vc | 2509 | 0.497 | 0.455 | 0.124 | -0.3 | 0.13 | 0.003 | 0.026 |
| sciplex3|B|myopic_edv | 2642 | 0.469 | 0.432 | 0.060 | -0.19 | 0.98 | 0.055 | 0.024 |
| sciplex3|B|sparse_two_step | 2697 | 0.461 | 0.425 | 0.051 | -0.19 | 0.95 | 0.054 | 0.025 |

Largest stratum miscalibration (correct-reading forecasts, strata with 50 or more):

- l1000|LT|maestro_vc / batch=CPC014|RAD001: n 56, forecast 0.614, observed 0.000, ECE 0.614
- l1000|LT|maestro_vc / batch=CPC019: n 112, forecast 0.524, observed 0.018, ECE 0.537
- l1000|LT|sparse_two_step / batch=CPC019: n 119, forecast 0.500, observed 0.008, ECE 0.491
- l1000|LT|myopic_edv / batch=CPC019: n 120, forecast 0.491, observed 0.000, ECE 0.491
- l1000|T|maestro_vc / support_bin=2-4: n 96, forecast 0.477, observed 0.010, ECE 0.481
- l1000|LT|maestro_vc / batch=CPC006|CPC018: n 93, forecast 0.444, observed 0.000, ECE 0.444
- l1000|T|sparse_two_step / batch=CPC019: n 67, forecast 0.409, observed 0.000, ECE 0.409
- l1000|LT|myopic_edv / batch=CPC014|RAD001: n 54, forecast 0.399, observed 0.037, ECE 0.406

## Pareto sets

- sciplex3|A: all arms `cost_only`, `defer_floor`, `fixed`, `info_gain`, `magnitude`, `myopic_edv`, `myopic_edv@0.05`, `myopic_edv@0.1`, `myopic_edv@0.2`, `production_default`, `retrieval`, `ridge`, `sparse_two_step`, `sparse_two_step@0`, `sparse_two_step@0.01`, `sparse_two_step@0.05`, `sparse_two_step@0.1`, `sparse_two_step@0.2`; under the wrong-risk cap `cost_only`, `defer_floor`, `magnitude`, `myopic_edv`, `myopic_edv@0.05`, `myopic_edv@0.1`, `myopic_edv@0.2`, `production_default`, `retrieval`, `ridge`, `sparse_two_step`, `sparse_two_step@0`, `sparse_two_step@0.01`, `sparse_two_step@0.05`, `sparse_two_step@0.1`, `sparse_two_step@0.2`
- sciplex3|B: all arms `cost_only`, `defer_floor`, `fixed`, `maestro_vc`, `magnitude`, `magnitude_permuted`, `myopic_edv`, `myopic_edv@0`, `myopic_edv@0.005`, `myopic_edv@0.01`, `myopic_edv@0.05`, `myopic_edv@0.1`, `myopic_edv@0.2`, `production_default`, `retrieval`, `sparse_two_step@0`, `sparse_two_step@0.2`; under the wrong-risk cap `cost_only`, `defer_floor`, `fixed`, `maestro_vc`, `magnitude`, `magnitude_permuted`, `myopic_edv`, `myopic_edv@0`, `myopic_edv@0.005`, `myopic_edv@0.01`, `myopic_edv@0.05`, `myopic_edv@0.1`, `myopic_edv@0.2`, `production_default`, `retrieval`, `sparse_two_step@0`, `sparse_two_step@0.2`
- l1000|LT: all arms `defer_floor`, `info_gain`, `maestro_vc`, `maestro_vc_permuted`, `marginal_only`, `myopic_edv`, `myopic_edv@0.05`, `myopic_edv@0.1`, `myopic_edv@0.2`, `ridge`, `sparse_two_step`, `sparse_two_step@0`, `sparse_two_step@0.005`, `sparse_two_step@0.01`, `sparse_two_step@0.05`, `sparse_two_step@0.1`, `sparse_two_step@0.2`; under the wrong-risk cap `defer_floor`, `info_gain`, `maestro_vc`, `maestro_vc_permuted`, `marginal_only`, `myopic_edv`, `myopic_edv@0.05`, `myopic_edv@0.1`, `myopic_edv@0.2`, `ridge`, `sparse_two_step`, `sparse_two_step@0`, `sparse_two_step@0.005`, `sparse_two_step@0.01`, `sparse_two_step@0.05`, `sparse_two_step@0.1`, `sparse_two_step@0.2`
- l1000|T: all arms `cost_only`, `defer_floor`, `fixed`, `info_gain`, `magnitude`, `magnitude_permuted`, `marginal_only`, `myopic_edv@0.05`, `myopic_edv@0.1`, `myopic_edv@0.2`, `production_default`, `retrieval`, `ridge`, `sparse_two_step`, `sparse_two_step@0.01`, `sparse_two_step@0.05`, `sparse_two_step@0.1`, `sparse_two_step@0.2`; under the wrong-risk cap `cost_only`, `defer_floor`, `fixed`, `info_gain`, `magnitude`, `magnitude_permuted`, `marginal_only`, `myopic_edv@0.05`, `myopic_edv@0.1`, `myopic_edv@0.2`, `production_default`, `retrieval`, `ridge`, `sparse_two_step`, `sparse_two_step@0.01`, `sparse_two_step@0.05`, `sparse_two_step@0.1`, `sparse_two_step@0.2`

## Figures

- Historical figure `figures/correct_cost.png` (unavailable in this checkout).
- Historical figure `figures/wrong_cost.png` (unavailable in this checkout).
- Historical figure `figures/risk_coverage.png` (unavailable in this checkout).

External comparator frozen for a future study: `fixed`.
Not executed: {'maestro_vc_jev': 'provider_arm_reserved_for_external_study'}.
