# Report: gate G1 on Beat AML (`beataml_g1_20261017`)

**Decision: G1 FAILED. Stop the low-rank state-model branch.** The frozen candidate beats the ridge by
+0.098 hits per sample [+0.045, +0.153], but the registered gate needs the lower bound, net of 0.05 per
extra round, to exceed 0.05. It is -0.005 net (+0.045 gross). A strong static model given the same probe
round gets nearly the same gain.

**Status: DEVELOPMENT.** Beat AML 2.0 is exposed: it shaped the confirmation, its repair and this design.
Nothing here confirms a method.

**Run.**

* `PROTOCOL.md`, the arms, the run and analysis code, the tests and the parity reference were frozen at
  2026-10-17T15:55:50Z. The run started 56 s later and wrote `records/records.json` once.
* `RESULTS.json` was written once by `g1_analyse.py`; `verify.py` recomputes it from the records and prints
  VERIFIED. 17 synthetic tests pass.
* Parity (stop condition) held on all 520 samples: the low-rank arms reproduce the attribution study's
  `t_vc0_coh`, `t_x4_coh`, `t_x8_coh` and the confirmed engine's total, and the ridge probabilities equal
  `strong_state` in all five folds.
* One documentation clarification after the freeze (`DEVIATIONS.json`); it touches no registered number.
* Cost: 0 wells, $0, no download, no sealed tier. The run took 43 s.

**Units.** A query is one archived 7-dose AUC profile; 16 queries stand for about 112 treatment wells.
The outcome is **total** known frozen events among the 16 queried inhibitors (probes included). A second
round needs banked cells and about 72 h; the declared value of a round is 0.05 hits per sample.
n = 520 samples, 479 patients (clusters).

## 1. The gate

| Arm | Rounds | Total hits | Reading |
|---|---|---|---|
| `A_item` empirical item ranking | 1 | 0.785 | |
| `S_ridge` drug-specific ridge on 30 basal PCs | 1 | 0.835 | strongest one-round arm |
| `C0` low-rank RNA prior, coherent score | 1 | 0.808 | |
| `E` confirmed two-round engine (promoted score, k = 4) | 2 | 0.854 | |
| `RF` ridge plus feedback (k chosen on source patients) | 2 | 0.917 | |
| `CAND` frozen candidate (coherent score, exploit-first, k chosen on source patients) | 2 | 0.933 | |

**Gate: `CAND - S_ridge` = +0.098 [+0.045, +0.153]** (positive in 57 samples, negative in 29, one-sided
sign-flip p 0.0005).

| Reading | Rule | Result |
|---|---|---|
| Strict (decides) | lo - 0.05 x 1 > 0.05 | lo - 0.05 = **-0.005**: FAIL |
| Gross | lo > 0.05 | 0.045: fail |
| Net positive | lo - 0.05 > 0 | -0.005: fail |

The net mean after the round charge is +0.048. The strict rule needs a lower bound above 0.10 hits per
sample; with intervals about 0.05 either side of the mean, it needs a point estimate of about 0.15.

## 2. Model benefit against the benefit of extra observations

Unadjusted, descriptive. "Net lower" is the lower bound minus 0.05 per extra round.

| Contrast | Mean [95% CI] | Extra rounds | Net lower | What it separates |
|---|---|---|---|---|
| `C0 - S_ridge` | -0.027 [-0.065, +0.011] | 0 | -0.065 | The low-rank model's own value with no observation: **none** (nominally worse than the ridge). |
| `CAND - C0` | +0.125 [+0.074, +0.180] | 1 | +0.024 | The probe round, for the low-rank model. |
| `RF - S_ridge` | +0.083 [+0.042, +0.127] | 1 | -0.008 | The same probe round, for a ridge prior. |
| `CAND - RF` | +0.015 [-0.036, +0.066] | 0 | -0.036 | The low-rank model's value when both get the same two-round protocol: **not distinguishable**, and the upper bound is below 0.10. |
| `CAND - E` | +0.079 [+0.032, +0.127] | 0 | +0.032 | The coherent score and k selection against the confirmed engine. |
| `E - S_ridge` | +0.019 [-0.033, +0.073] | 1 | -0.083 | The confirmed engine is not shown better than the one-round ridge. |
| `S_ridge - A_item` | +0.050 [-0.002, +0.109] | 0 | -0.002 | The ridge prior against the item ranking. |
| `C0 - A_item` | +0.023 [-0.025, +0.076] | 0 | -0.025 | The low-rank prior against the item ranking. |
| `CAND - A_item` | +0.148 [+0.088, +0.211] | 1 | +0.038 | |
| `RF - A_item` | +0.133 [+0.075, +0.197] | 1 | +0.025 | |

The identity `CAND - S_ridge = (C0 - S_ridge) + (CAND - C0)` holds exactly (0.098 = -0.027 + 0.125). Almost
all of the gain is the probe round: it adds +0.125 to the low-rank model and +0.083 to the ridge, and the
two models differ by only +0.015 once both have it.

**Registered classification.** The strongest one-round prior is `S_ridge`. The registered classifier reads
the feedback gain on it as "no net feedback gain at the lower bound" (`RF - S_ridge`: net lower -0.008).
Its mean is positive and its gross interval excludes zero, so the pattern is real but small: a round must be
worth less than about 0.08 hits per sample (point estimate; 0.04 at the lower bound) for it to pay.

## 3. Sensitivity (none of it decides)

* **Fixed probe counts.**

  | k | `C_k - S_ridge` | `RF_k - S_ridge` | `C_k - RF_k` |
  |---|---|---|---|
  | 4 | +0.065 [+0.012, +0.125] | +0.062 [+0.013, +0.114] | +0.004 [-0.035, +0.044] |
  | 8 | +0.131 [+0.076, +0.189] | +0.106 [+0.058, +0.162] | +0.025 [-0.023, +0.075] |
  | 12 | +0.073 [+0.028, +0.118] | +0.063 [+0.028, +0.104] | +0.010 [-0.038, +0.060] |

  k = 8 is the best fixed count for both models (0.965 and 0.940). The inner choice of k was noisy: the
  candidate's choices were 8, 12, 8, 8, 4 across folds and cost it 0.032 against always taking 8 (0.933
  against 0.965). Post hoc, `C_8 - S_ridge` would not pass the strict gate either (lower bound 0.076 gross,
  net 0.026), because k = 8 was not what the registered procedure selected and 0.076 is below 0.10.
* **More shrinkage in the ridge feedback** (`RF_s`, lambda = 0.5): 0.904; `RF_s - S_ridge` +0.069
  [+0.035, +0.108]; `CAND - RF_s` +0.029 [-0.021, +0.081]. The conclusion does not depend on the
  shrinkage.
* **Per fold** (`CAND - S_ridge`): +0.187, +0.078, +0.082, +0.073, +0.068. The gain is positive in every fold
  and largest in fold 0.
* **Probe returns.** 80-87% of probe readouts return a value (some pairs were never measured); wasted
  queries per sample are 2.6 (`E`) to 3.4 (`C0`).
* Within a fold the inner means for the three k differ by 0.00-0.06 hits, so the choice of k carries weak
  information; the outer table shows k = 8 best for both models.

## 4. Interpretation

1. **The feedback pattern, not the model, produced the gain.** Measuring the top few items and re-ranking
   adds +0.08 to +0.13 hits per sample to a ridge or a low-rank prior alike. That agrees with
   `feedback_attribution_20261017` (the update carries item-specific information) and sharpens it: the
   low-rank state model is not needed to get it.
2. **The low-rank prior is not better than a ridge on the same basal profile**, with or without
   observations (`C0 - S_ridge` -0.027; `CAND - RF` +0.015 [-0.036, +0.066]). The registered consequence
   follows: stop developing the bridged-transfer state model on this domain.
3. **The confirmed engine is weaker than the candidate** (`CAND - E` +0.079) but is not shown better than
   the one-round ridge (`E - S_ridge` +0.019). The coherent score is the part of the candidate that
   mattered; it is development-grade and not calibrated.
4. **Rounds decide.** After a 0.05 charge per round the strongest net result is `CAND - A_item` (+0.038
   lower bound) and `C_8 - S_ridge` post hoc (+0.026). No arm clears the 0.05 net usefulness line against
   the strongest one-round model.

## 5. What this does not show

* Any confirmation: Beat AML is exposed, and the folds are those of the confirmation.
* That a low-rank model cannot help elsewhere: only that it does not beat a ridge here at the declared
  margin. The upper bound of `CAND - RF` (+0.066) leaves a small benefit possible.
* That the declared 0.05 per round is the right price. If a round is cheaper, the ridge-plus-feedback
  pattern pays (`RF - S_ridge` +0.083); if it is dearer, nothing here does.
* Transfer of knowledge from PRISM or other screens, clinical benefit, absolute efficacy or causal
  mechanism. Every model is refitted within Beat AML.
* Anything about the LLM: no provider call was made.

## 6. Consequences

* **Stopped:** further variants of `BridgedTransferModel` on Beat AML (rank, prior, scorer, probe rule) and
  any claim that the low-rank state model adds to the feedback gain.
* **Retained:** the feedback design pattern (a few exploit-first probes, one update, the rest), on the
  strongest prior, with a ridge as the mandatory comparator. Keep `k = 8` as the working default from the
  fixed-k table; it is a post hoc choice.
* **Retained as infrastructure:** `agent.bridge_design`, the coherent scorer as a development scorer, and the
  promoted `virtual_cell.bridged_transfer`, within their documented scope. The confirmed label stays
  narrower than its protocol name.
* **Gate G2** (confirmation) is not opened: it needs a candidate that passes G1 and a new, independent,
  powered domain, and neither exists locally.
