Population: 2250 conditions, 1758 responsive (by line {'A549': 517, 'K562': 525, 'MCF7': 716}; by dose {'10.0': 390, '100.0': 410, '1000.0': 458, '10000.0': 500}).

Replicate ceiling (rep 1 vs rep 2, centered): responsive 0.230 [0.208, 0.254]; all 0.198 [0.176, 0.222]

| Arm | B1 responsive | B1 all | B1 scrambled | MSE skill | MSE skill scrambled |
|---|---|---|---|---|---|
| `zero` | 0.130 [0.098, 0.161] | 0.123 [0.093, 0.152] | -0.001 [-0.002, 0.001] | 0.000 [0.000, 0.000] | -0.243 [-0.282, -0.206] |
| `systematic` | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] | -0.056 [-0.080, -0.033] | -0.056 [-0.080, -0.033] |
| `ridge_chem` | 0.167 [0.140, 0.194] | 0.157 [0.132, 0.182] | -0.000 [-0.001, 0.001] | -0.073 [-0.120, -0.030] | -0.210 [-0.249, -0.174] |
| `knn_chem` | 0.136 [0.105, 0.168] | 0.125 [0.097, 0.154] | -0.000 [-0.001, 0.001] | -0.470 [-0.618, -0.341] | -0.588 [-0.695, -0.497] |
| `mlp_existing` | 0.157 [0.135, 0.178] | 0.150 [0.129, 0.170] | -0.000 [-0.001, 0.001] | -0.038 [-0.068, -0.012] | -0.206 [-0.240, -0.173] |
| `latent_pca` | 0.148 [0.127, 0.169] | 0.142 [0.122, 0.161] | -0.001 [-0.002, 0.000] | -0.061 [-0.094, -0.032] | -0.193 [-0.227, -0.160] |
| `latent_mae` | 0.134 [0.113, 0.154] | 0.129 [0.110, 0.148] | -0.000 [-0.001, 0.000] | -0.104 [-0.154, -0.061] | -0.216 [-0.261, -0.176] |
| `latent_jepa` | 0.147 [0.123, 0.172] | 0.141 [0.117, 0.165] | -0.001 [-0.002, 0.000] | -0.081 [-0.116, -0.048] | -0.248 [-0.283, -0.214] |
| `latent_jepa_moa` | 0.170 [0.146, 0.194] | 0.162 [0.140, 0.185] | -0.001 [-0.002, 0.000] | -0.090 [-0.142, -0.049] | -0.278 [-0.324, -0.238] |
| `latent_jepa_moa_shuffled` | 0.141 [0.119, 0.164] | 0.135 [0.113, 0.157] | -0.000 [-0.001, 0.001] | -0.095 [-0.133, -0.059] | -0.243 [-0.279, -0.209] |

B3 mechanism retrieval, 151 compounds in 22 classes: observed-profile ceiling 0.424 [0.351, 0.503]; chemistry nearest neighbour 0.464 [0.384, 0.543]; chance 0.080 [0.071, 0.090].

| Arm | B3 accuracy | B4 potency A549 / K562 / MCF7 | B5 context r | B5 interaction r | B5 top-line accuracy (majority rate) |
|---|---|---|---|---|---|
| `zero` | n/a | 0.000 / 0.000 / 0.000 | 0.000 [0.000, 0.000] | 0.168 [0.115, 0.221] | 0.000 [0.000, 0.000] (0.562) |
| `systematic` | n/a | -0.107 / -0.100 / -0.116 | 0.275 [0.246, 0.306] | 0.000 [0.000, 0.000] | 0.249 [0.189, 0.314] (0.562) |
| `ridge_chem` | 0.311 [0.238, 0.384] | 0.361 / 0.466 / 0.384 | 0.304 [0.272, 0.338] | 0.268 [0.230, 0.304] | 0.443 [0.373, 0.514] (0.562) |
| `knn_chem` | 0.384 [0.311, 0.464] | 0.327 / 0.413 / 0.307 | 0.282 [0.246, 0.319] | 0.174 [0.128, 0.217] | 0.454 [0.384, 0.524] (0.562) |
| `mlp_existing` | 0.199 [0.139, 0.265] | 0.287 / 0.450 / 0.296 | 0.257 [0.230, 0.285] | 0.176 [0.128, 0.222] | 0.395 [0.319, 0.470] (0.562) |
| `latent_pca` | 0.219 [0.152, 0.278] | 0.364 / 0.520 / 0.330 | 0.245 [0.213, 0.279] | 0.140 [0.107, 0.171] | 0.384 [0.314, 0.454] (0.562) |
| `latent_mae` | 0.252 [0.179, 0.325] | 0.353 / 0.485 / 0.313 | 0.255 [0.221, 0.291] | 0.123 [0.088, 0.158] | 0.346 [0.276, 0.411] (0.562) |
| `latent_jepa` | 0.172 [0.113, 0.232] | 0.282 / 0.420 / 0.381 | 0.224 [0.191, 0.257] | 0.225 [0.184, 0.263] | 0.373 [0.303, 0.443] (0.562) |
| `latent_jepa_moa` | n/a | 0.344 / 0.444 / 0.334 | 0.231 [0.197, 0.267] | 0.239 [0.200, 0.276] | 0.373 [0.303, 0.449] (0.562) |
| `latent_jepa_moa_shuffled` | n/a | 0.344 / 0.474 / 0.340 | 0.239 [0.206, 0.272] | 0.210 [0.173, 0.246] | 0.362 [0.292, 0.438] (0.562) |

Anchors holding in the observed data: `A1_hsp90_hsf1`, `A2_glucocorticoid_gr`, `A3_estrogen_receptor_mcf7`, `A5_phd_hypoxia`, `A7_p53_context`, `A8_bcr_abl_k562`, `A9_hdac_magnitude` (7 of 10); not holding: `A4_mek_mpas`, `A6_bet_hexim1`, `A10_no_functional_target`.

| Arm | Anchors reproduced out of fold | Passed although absent in data |
|---|---|---|
| `zero` | 0 of 7: - | A10_no_functional_target |
| `systematic` | 0 of 7: - | - |
| `ridge_chem` | 2 of 7: A5_phd_hypoxia, A9_hdac_magnitude | - |
| `knn_chem` | 3 of 7: A3_estrogen_receptor_mcf7, A5_phd_hypoxia, A9_hdac_magnitude | - |
| `mlp_existing` | 3 of 7: A1_hsp90_hsf1, A8_bcr_abl_k562, A9_hdac_magnitude | A10_no_functional_target |
| `latent_pca` | 1 of 7: A9_hdac_magnitude | A10_no_functional_target |
| `latent_mae` | 3 of 7: A1_hsp90_hsf1, A5_phd_hypoxia, A9_hdac_magnitude | A10_no_functional_target |
| `latent_jepa` | 3 of 7: A1_hsp90_hsf1, A8_bcr_abl_k562, A9_hdac_magnitude | A10_no_functional_target |
| `latent_jepa_moa` | 3 of 7: A1_hsp90_hsf1, A8_bcr_abl_k562, A9_hdac_magnitude | A10_no_functional_target |
| `latent_jepa_moa_shuffled` | 2 of 7: A8_bcr_abl_k562, A9_hdac_magnitude | A10_no_functional_target |

| Arm | B7 spread vs RMSE (registered) | B7 scale-free | B1 confident half | B8 PRISM |
|---|---|---|---|---|
| `zero` | n/a | n/a | n/a | 0.000 |
| `systematic` | n/a | n/a | n/a | 0.016 |
| `ridge_chem` | n/a | n/a | n/a | 0.273 |
| `knn_chem` | -0.031 [-0.118, 0.061] | 0.269 [0.162, 0.369] | 0.173 [0.124, 0.226] | 0.223 |
| `mlp_existing` | 0.453 [0.401, 0.507] | 0.089 [0.014, 0.150] | 0.099 [0.081, 0.117] | 0.257 |
| `latent_pca` | 0.525 [0.470, 0.580] | -0.076 [-0.153, 0.002] | 0.089 [0.072, 0.107] | 0.380 |
| `latent_mae` | 0.541 [0.489, 0.590] | -0.096 [-0.168, -0.016] | 0.089 [0.072, 0.106] | 0.317 |
| `latent_jepa` | 0.392 [0.335, 0.450] | 0.080 [0.009, 0.148] | 0.082 [0.061, 0.103] | 0.241 |
| `latent_jepa_moa` | 0.407 [0.348, 0.468] | 0.014 [-0.057, 0.090] | 0.103 [0.084, 0.122] | 0.308 |
| `latent_jepa_moa_shuffled` | 0.383 [0.322, 0.436] | 0.117 [0.047, 0.179] | 0.081 [0.063, 0.099] | 0.244 |

B8 observed: Spearman(shift norm, -PRISM AUC) = 0.513 over 227 compound-lines.

P1 `latent_jepa` - `knn_chem` (B1 responsive): 0.011 [-0.022, 0.042]
P2 `latent_jepa` - `latent_pca`: -0.001 [-0.020, 0.018]
P3 anchors: `latent_jepa` 3, `mlp_existing` 3, held in data 7

| Arm | specific_signal | beyond_retrieval | near_ceiling | anchor_depth | knows_what_it_does_not_know | sufficient_for_advisory_ranking |
|---|---|---|---|---|---|---|
| `systematic` | no | no | no | no | no | no |
| `ridge_chem` | yes | yes | yes | no | no | no |
| `knn_chem` | yes | no | yes | no | no | no |
| `mlp_existing` | yes | no | yes | no | yes | no |
| `latent_pca` | yes | no | yes | no | yes | no |
| `latent_mae` | yes | no | yes | no | yes | no |
| `latent_jepa` | yes | no | yes | no | yes | no |
| `latent_jepa_moa` | yes | yes | yes | no | yes | no |
| `latent_jepa_moa_shuffled` | yes | no | yes | no | yes | no |

Calibration `knn_chem` at 0.8: mean coverage 0.805; readouts at or above 0.70: 1.00; in distribution 0.809, novel 0.804; passed: True.

Calibration `systematic` at 0.8: mean coverage 0.804; readouts at or above 0.70: 1.00; in distribution 0.807, novel 0.803; passed: True.

Calibration `zero` at 0.8: mean coverage 0.805; readouts at or above 0.70: 1.00; in distribution 0.806, novel 0.804; passed: True.

Agent probe, 40 compounds, 17 classes (chance 0.059):

| Arm | Accuracy |
|---|---|
| `prior` | 0.150 [0.050, 0.275] |
| `tool` | 0.500 [0.350, 0.650] |
| `deepseek_signature` | 0.100 [0.025, 0.200] |
| `deepseek_card` | 0.425 [0.275, 0.575] |
| `jev_signature` | 0.075 [0.000, 0.175] |
| `jev_card` | 0.475 [0.325, 0.625] |

DeepSeek card minus signature: 0.325 [0.175, 0.500]; Jev card minus signature: 0.400 [0.250, 0.575]; DeepSeek card minus tool: -0.075 [-0.175, 0.000]; Jev agreement over repeats: 0.933; spend DeepSeek $0.0227 over 80 calls, Jev about $0.0053.
