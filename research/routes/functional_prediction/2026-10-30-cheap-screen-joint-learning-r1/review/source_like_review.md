# Source-like trimming sensitivity review

Source-like result was frozen before primary inspection (SHA256 `2c7f8189bac7bb65ae274d840a054f63f9db1a5d3b9e41bb6e687e3119acef8e`). It used the archived `01_preparing_inputs.R` method for each preparation separately: pool Sample1 and Sample2 events per stimulus×drug, use NumPy linear quartiles, retain strict inequalities, then equal-average surviving technical-well MFIs. The primary E001 method trims each technical well separately with closed bounds. The source script itself combines E3DA/E3DB in its preparation workflow, but this diagnostic deliberately keeps them separate as requested.

Compared 1140 arithmetic/Boolean fields against pilot_result.json; 888 differ at rel 1e-9 / abs 1e-7, as expected from the trimming mismatch. The mismatch is therefore material to numerical values, while the processing question is explicitly a post hoc robustness diagnostic.

| Prep | changed wells | changed retained counts | max MFI change | source-like Gain MAE | source-like B_const MAE | source-like overlap | best model |
|---|---:|---:|---:|---:|---:|---:|---|
| E3CA | 43/48 | 43/48 | 127.11 | 0.911970 | 0.447325 | 1/5 | additive |
| E3CB | 46/48 | 46/48 | 142.491 | 0.408933 | 0.378174 | 2/5 | constant_interaction |
| E3DA | 45/48 | 45/48 | 43.2517 | 0.490819 | 0.500479 | 3/5 | gain |
| E3DB | 45/48 | 45/48 | 292.25 | 1.279495 | 1.261254 | 2/5 | constant_interaction |

The qualitative negative conclusion does not change. Source-like Gain MAE remains worse than B_const in E3CA, E3CB and E3DB; E3DA remains the sole small Gain advantage. The same full-set pattern therefore survives this post hoc trimming diagnostic. This is descriptive robustness evidence only, not validation, a protocol revision, or a new candidate.

The mismatch matters because pooled trimming lets one technical well influence the other well’s cutoffs, while strict versus closed inequalities can differ at exact boundaries. The primary per-well method avoids that cross-well influence and was the frozen protocol used for the E001 decision. The source-like result should not replace it.

The assay remains capture-bead PE readout with unverifiable APC gating in these exports. Results are calibration-conditioned target holdout in the same assay, not external validation. No cell/molecular causal inference, biological-noise guarantee, CI, p-value, mechanistic novelty, or acquisition advantage is supported.

Diagnostic execution: wall 0.508932 s; CPU 0.500000 s; no network/API calls or cost.
