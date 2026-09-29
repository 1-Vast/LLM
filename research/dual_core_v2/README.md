# Dual-core v2: verified repairs of the 2026-09-28 diagnosis

**File summary**
- **Path:** `research/dual_core_v2/README.md`
- **Purpose:** block 1 of 2026-09-28. The owner's brief (drafted by the Codex session that wrote
  `outputs/diagnosis_20260928/`) asked to verify that diagnosis independently, repair the confirmed
  defects in both MAESTRO cores, recompute what they affected, test the smallest justified improvements,
  and say what to keep, reject or leave experimental.
- **Core points:**
  - **Two defects confirmed and repaired, with failing-first regression tests.** Block 7's P3 never
    tested a nonzero threshold (it broke on the threshold 0, whose zero-decision loss sits on the null
    boundary, and fell back to 0). Block 7's calibration for test fold f used traces from models trained
    on f. A third, smaller one: `fit_pair` scored gamma on its own fitting residuals.
  - **The repairs do not change the verdicts; they change what the verdicts mean.** On block 7's own
    traces and on the new nested traces nothing is certified at alpha = 0.05: the outcome is now
    "no candidate certified" with an undefined conditional risk, not "abstain-always certified, error 0".
  - **The diagnosis is corrected in four places:** magnitude is not a reading input (the validator is a
    cosine rule gated by replicate agreement); Platt's absence from P2/P3 is immaterial (a monotone map
    cannot change reachable truncations); block 7's "25-30x more units" is an artefact of the
    Hoeffding-Bentkus bound; and at the registered alpha the risk of the unconstrained agent sits at
    alpha, so no sample size would certify it.
  - **World model, agent, population:** sections 5-9.
  - **Nothing is promoted.** `src/` and production defaults are unchanged; block 7's files are byte-identical.
- **Interfaces / data:** `risk_control.py`, `nested.py`, `world3.py`, `arms.py`, `run.py`, `analysis.py`,
  `report.py`, `transfer_honest.py`, `e1_honest.py`, `data_audit.py`, `horizon_headroom.py`,
  `population_eval.py`, `freeze.py`, `protocol.json`, `protocol_population.json`, `ISSUES.md`,
  `test_dual_core_v2.py`; outputs in `outputs/dual_core_v2_20260928/`
- **Depends on:** `research/dual_core/` (block 7, unchanged), `research/protocol_v2/`,
  `research/belief_planning/`, `research/incontext_world/`, `src/virtual_cell/population_flow.py`

Spend: $0, 0 wells, no download. CPU only.

## 0. Plan, acceptance criteria and whether they were met

| Phase | Acceptance criterion | Met? |
|---|---|---|
| A. Reproduce | Every diagnosis claim has a disposition backed by a command or test; the diagnosis is corrected where evidence contradicts it | Yes: 21 items plus 10 new ones in `ISSUES.md` |
| B. Repair | Failing-first regression tests for confirmed defects; lineage tests spy on real fitting inputs | Yes: 29 tests in `test_dual_core_v2.py` |
| C. Recompute | Old and new numbers side by side on the same items; nothing old overwritten | Yes: block 7 outputs untouched; v2 outputs in a new directory |
| D. Improve | Protocol frozen with hashes before any score | Yes: `freeze.json` 10:18:21, `freeze_population.json` 10:29:21 |
| E. Evaluate | World, policy and interaction effects separated | Yes (section 7) |
| F. Population | Keep, reject or experimental, with a named reason | Yes: experimental, reason `no_population_signal_beyond_pseudobulk` |
| G. Data, literature | Each source mapped to a change or "no change" | Yes (sections 10, 11) |

**How the work was protected.** Block 7's code was verified byte-identical to the SHA-256 digests in its
protocols before anything else, and none of it was edited: every correction is a new module here. Both new
protocols were hashed before their runs were scored (`freeze.py`, write-once). Seen before the freeze: block 7's
outcomes, the diagnosis's all-threshold Hoeffding-Bentkus p-values, one execution-only pilot (counts, audit
problems, anchor matches, timing, selected sources and training log-likelihoods). Code written after the
freeze is hashed in `freeze_population.json` or listed in section 13; `report.py` was debugged by an
execution-only smoke run that printed section status, never a number.

**Concurrent work.** The Codex session that wrote the diagnosis and this brief (rollout `01a0e152`,
08:22-09:41) was idle; no file in the tree changed between the diagnosis and the start of this block.

## 1. The verified issue matrix

The full matrix is `ISSUES.md`: evidence, reproduction, classification, consequence, repair, verification
criterion and disposition per item. In short:

| Class | Items |
|---|---|
| Confirmed software defects, repaired with tests | P3 control flow (A1), zero-risk-as-success report (A2), threshold 0 treated as abstain-all in P3 and P2 (B2, B3) |
| Evaluation flaws, repaired | calibration lineage (A3), in-sample gamma error (A4); minor: Platt item vs unit weighting (A17), inner reuse of outer (s, k, e) (A11, documented only) |
| Interface weaknesses, repaired, no historical effect | cache key without quality (A20), prompt type check without provenance (A21) |
| Modelling limitations, addressed or measured | additive refused by the world model (A5), rank boundary (A7), objective mismatch (A8), truncation-only risk policy (A14), conservative risk bound that does not rank (B5) |
| Data limitations, measured | two measurements at most (A12), event concentration (B4), an uninformative L1000 task (B7), three structural-abstention tasks (B1) |
| Diagnosis claims not supported | magnitude as a lost reading input (A9, in part), Platt's absence from P2/P3 as a defect (A19); data-integrity worries (B9) |
| Earlier claims corrected | section 12 |

## 2. Code changes, by finding

| File | Finding | Change |
|---|---|---|
| `risk_control.py` | A1, A2, B2, B3 | Learn-then-Test over explicit nonzero candidates; the tested null is the union of "conditional risk > alpha" and "coverage < rho x P0"; Holm's step-down; `ABSTAIN_ALL` as a policy; named statuses; NaN conditional risk; Hoeffding-Bentkus and a betting p-value (Waudby-Smith and Ramdas); repaired plug-in P2 |
| `nested.py` | A3 | Contexts with two folds excluded from every fit (tables, pool, validator calibration, world model, transfers) through one sentinel fold; `Lineage` and `check_independent` |
| `transfer_honest.py` | A4, A7 | Honest error of the complete `fit_pair` procedure (one extra CV level); `k_grid` argument for a training-only rank study |
| `world3.py` | A5, A9, A20, A21 | `WorldV2`: sources `additive` and `transfer_dist` compete with block 7's under its own training-only criterion; diagnostic oracle sources; `PromptSet` issued only by `LedgerV2`, validated by named reason; cache keys with quality, provenance and in-context parameters; `variant()` reproduces block 7's world exactly |
| `arms.py` | A14, A15 | One planner arm for every world model; three named risks recorded; risk-select reuses the planner's `wrong_risk_cap`, with a point-risk option |
| `run.py` | A3, A10, A12 | Nested jobs with lineage checks before any episode; P0, risk-select and oracle arms; per-step ablation of every world variant; reproduction anchor against block 2's planner |
| `analysis.py`, `report.py` | all | Designs `block7_crossfit`, `split`, `nested_crossfit`; unit-cluster bootstrap throughout |
| `e1_honest.py`, `data_audit.py`, `horizon_headroom.py`, `population_eval.py` | A4, A7, B4-B7, A12, population | The recomputations of sections 4, 8, 9, 10 |

## 3. Risk control and calibration, repaired

**The runs.** 40 nested jobs (every pair of held-out folds x 4 tiers), 0 audit problems, 0 lineage failures; the
v2 reference arm reproduced block 2's `belief_arm` action sequence in **640 of 640** anchor episodes. Six models
cannot eliminate at all (their validator calibration finds no floor and margin): L1000 LT with folds {0,2}, {0,3},
{1,3}, {2,3} held out, L1000 T {0,1} and SciPlex3 A {2,4}. They are structural abstentions and stay in every
coverage denominator. Models on three folds are weaker than block 7's four-fold models, so the unconstrained
agent's risk is higher here: SciPlex3 0.052 [0.029, 0.082] at coverage 0.60, **L1000 0.094 [0.038, 0.178]** at
coverage 0.10 (block 7: 0.049 and 0.047).

**Learn-then-Test, repaired (P3).**

| Traces (design) | SciPlex3 reference / v1 / v2 | L1000 reference / v1 / v2 | Smallest risk p-value over folds (betting) |
|---|---|---|---|
| Block 7 (`block7_crossfit`, flawed lineage), block 7's P3 | "abstain-always certified, error 0 [0, 0]" | same | never computed beyond threshold 0 |
| Block 7, repaired procedure | no candidate certified, all folds | no candidate certified, all folds | 0.37-0.66 (HB 0.80-0.97) |
| v2 `split` (exact lineage) | no candidate certified, all folds | no candidate certified, all folds | 0.70-0.88 (L1000 0.92-1.00) |
| v2 `nested_crossfit` | no candidate certified, all folds | no candidate certified, all folds | - |

With both p-values and every world model the answer is the same: **no abstention policy is certified at
alpha = 0.05, delta = 0.1**, and the test-fold outcome is the explicit abstain-all policy, coverage 0 and
conditional risk undefined. The guarantee the repaired procedure would give if it certified: under exchangeable
units and one frozen model-policy process, with probability at least 0.9 the chosen policy's population
conditional risk E[wrong_u]/E[decided_u] is at most 0.05 and it keeps at least half of the unconstrained agent's
decisions. Nothing here claims that guarantee.

**Repaired plug-in P2 (no guarantee).** SciPlex3 reference, split design: 0.024 [0.006, 0.047] at coverage 0.42,
against P0's 0.052 at 0.60. **This is not a transferable threshold.** The calibration fold of test fold 0 already
exceeded alpha, so the whole of test fold 0 (which carries most of the wrong events, B4) was abstained. Under
the nested cross-fit, P2 is worse than P0 (0.057 [0.033, 0.086] at coverage 0.49), and on L1000 P2 abstains
entirely in three of five folds. Block 7's conclusion that no threshold transfers across folds holds under
correct lineage.

**Calibration of the step risk after selection** (Platt on the calibration fold, scored on the test fold, the same
frozen model; block 7's numbers used calibration traces from models trained on the test fold):

| | Block 7 (flawed lineage) | v2 split: reference | v1 | v2 |
|---|---|---|---|---|
| SciPlex3 observed / forecast, raw | 1.70 [0.95, 2.52] | **1.88 [1.04, 2.85]** | 1.94 [1.08, 2.95] | 1.96 [1.09, 2.99] |
| SciPlex3 after Platt | 1.05 [0.57, 1.61] | 1.13 [0.64, 1.70] | 1.15 | 1.12 |
| SciPlex3 log loss, Platt - raw | **+0.006 [+0.001, +0.012]** | -0.008 [-0.021, +0.002] | -0.010 [-0.022, +0.001] | -0.009 [-0.022, +0.002] |
| L1000 observed / forecast, raw | 1.96 [0.96, 3.20] | **2.84 [1.31, 5.26]** | 2.81 [1.15, 5.40] | 3.08 [1.25, 5.94] |
| L1000 after Platt | 0.94 [0.47, 1.53] | 0.80 [0.38, 1.40] | 0.82 | 0.82 |
| L1000 log loss, Platt - raw | **-0.008 [-0.015, -0.002]** | -0.005 [-0.015, +0.002] | -0.005 [-0.015, +0.003] | -0.005 [-0.015, +0.003] |

- **Confirmed and sharpened:** forecasts of wrong elimination are 1.9-3x too low on the actions the planner
  selects, now with correct lineage.
- **Not confirmed:** block 7's "Platt improves log loss on L1000 and worsens it on SciPlex3". Under correct
  lineage neither change is distinguishable from 0 and the fitted slopes are negative in some folds
  (SciPlex3 -0.53 to 1.35; L1000 -0.17 to 0.66). The direction of the lineage bias was therefore not uniform:
  it made Platt look better on L1000 and worse on SciPlex3. Block 7's calibration numbers stand only as a
  descriptive record of those traces.

## 4. The response model: honest errors, aggregation, rank, quality and the selection rule

Recomputed on block 7's own E1 items (`e1_honest.py`). The pair models are refitted on outer-training compounds
exactly as block 7 did, plus an honest error of the whole procedure; outer outcomes are used only for scoring.

| | SciPlex3 | L1000 |
|---|---|---|
| Pairs where `rrt_q` beats `ridge_st` in inner MSE: block 7 (in-sample gamma) / honest | 97.9% / **69.5%** | 100% / 99.3% |
| Honest `rrt_q` / `ridge_st` MSE, median [10%, 90%] | 0.9993 [0.984, 1.002] | 0.997 [0.993, 0.999] |
| Median optimism of block 7's `rrt_q` inner error | 1.1% | 0.06% |
| A2 inverse-error weights, honest minus block 7 (direction / discrimination) | 0.000 / 0.000 | -0.0001 / -0.0001 |
| A2 inverse-error minus equal weights (direction / discrimination) | +0.003 [+0.003, +0.004] / +0.009 [+0.007, +0.011] | +0.0002 [0.000, +0.0004] / -0.0003 [-0.001, +0.0004] |
| A2 most reliable single prompt minus equal (direction / discrimination) | -0.014 [-0.019, -0.009] / **+0.063 [+0.050, +0.076]** | -0.047 [-0.059, -0.036] / **+0.028 [+0.011, +0.046]** |
| A2 equal-weight `rrt_q` minus additive mean (direction / discrimination) | +0.221 / **-0.062 [-0.108, -0.012]** | +0.202 / **-0.089 [-0.138, -0.042]** |

- **The residual term's honest gain is about 0.07% of MSE on SciPlex3**, not block 7's 0.2-0.8%; on L1000 it
  holds (0.3%). Block 7's E1 keep rule used outer-fold scores and is unaffected.
- **"Precision" weighting is equal weighting in practice.** The two prompts' errors are similar, so the larger
  weight is about 0.52 whether errors are honest or not. The honest correction changes no A2 conclusion.
- **Averaging trades identity for direction.** The single most reliable prompt, or the additive mean,
  discriminates compounds better than any average of `rrt_q` predictions, and loses direction.
- **Rank boundary (training only, L1000).** With k up to 128 instead of 32, 142 of 280 fits choose 128 (the new
  boundary) and 94 choose 96. The honest error falls by a median 1.4% (lower in 96% of pairs), so the k = 32 cap
  was binding for MSE. Whether that helps direction, identity or decisions was not scored, because only exposed
  outer folds exist to score it on.
- **Quality weighting** (`rrt_q` - `rrt_const`, detected targets, strata within each dataset, because the two
  quality scores are not comparable). L1000 (`cc_q75`): better in every stratum, rising from +0.001 (lowest
  quality tertile) to +0.040 [+0.023, +0.061] (top tertile, detected prompt), so the gate removes noise.
  SciPlex3 (split-half r): slightly worse in the low and middle tertiles (-0.002 to -0.004 discrimination) and
  better only in the top one (+0.007), so the gate suppresses some informative weak prompts
  (`diagnostics/quality_weighting_strata.json`).

**Estimand and selection rule per layer** (fixed here; applied to the planner layer in the v2 runs):

| Layer | Primary estimand | Selection rule |
|---|---|---|
| Response prediction (E1) | compound discrimination among held-out truths at the target, unit mean; direction co-primary | A candidate replaces another only if it is better on discrimination and not worse on direction by more than 0.01 (block 7's margin). On that rule `rrt_q` does not replace additive transfer (additive discriminates better) and additive does not replace `rrt_q` (loses about 0.2 direction). No single response model dominates |
| Reading forecast (world model) | log-likelihood of the realised reading under the true hypothesis | Training-only nested reading log-likelihood among {reference, prompt, transfer, additive, transfer_dist}; `WorldV2` uses exactly this, so additive can win on its merits |
| Decision policy | unit-level conditional wrong-elimination risk with a coverage requirement; correct decisions and measurements | Repaired Learn-then-Test (guarantee) or repaired plug-in P2 (no guarantee) |

## 5. The agent: risk definitions, ranking and risk-aware selection

**Three risks, kept apart.** Each is recorded before a purchase, and none is the evaluation target:
- `risk_step`: P(the next measurement eliminates the true hypothesis); this is block 7's risk;
- `p_wrong_plan`: P(some wrong elimination in the rest of the episode under the chosen plan);
- `p_wrong_upper_plan`: its conservative version, the one the planner's existing `wrong_risk_cap` constrains.

The target is the population conditional decision risk P(wrong | decided). A guarantee for that event is not
a statement about any of the three scores, and a calibrated step risk is not a decision risk.

**Can the scores rank dangerous steps?** Unit-cluster bootstrap AUROC for "this step eliminated the true
hypothesis":

| Score | Block 7 traces: SciPlex3 / L1000 | v2 split test folds: SciPlex3 / L1000 |
|---|---|---|
| step | 0.66 [0.56, 0.75] / 0.58 [0.51, 0.64] | 0.55 [0.46, 0.64] / 0.78 [0.68, 0.88] |
| plan (point) | 0.60 [0.49, 0.69] / 0.53 [0.46, 0.62] | 0.52 [0.45, 0.61] / 0.80 [0.70, 0.90] |
| plan (conservative) | 0.50 [0.39, 0.59] / **0.38 [0.25, 0.53]** | 0.41 [0.30, 0.52] / 0.60 [0.48, 0.72] |

Ranking is weak and unstable across model and fold configurations: 38-51 events in about 20 units per dataset
(16-31 in 11-16 on L1000). The conservative bound never ranks usefully; it tracks reference support. A
recalibration map (Platt) changes the probability scale and cannot change these AUROCs, so recalibration alone
cannot make a threshold policy discriminate.

**Risk-aware selection versus stopping.** Same view, menus, budgets, executor and ledger; split test folds.
Risk-select is the planner's `wrong_risk_cap`, the existing Lagrangian re-selection that compares safer actions
before stopping; no new selector was written. Stop-only is exact truncation of the P0 traces on the same risk
measure. The primary comparison is conditional risk at matched coverage (stop-only interpolated at the
risk-select coverage in each bootstrap draw):

| Cap (pre-declared) | Risk-select coverage / risk | Stop-only at the same cap: coverage / risk | Risk-select - stop-only at matched coverage |
|---|---|---|---|
| SciPlex3 reference, point 0.0131 | 0.52 / 0.043 | 0.18 / 0.055 | -0.009 [-0.027, +0.007] |
| SciPlex3 reference, point 0.0174 | 0.56 / 0.053 | 0.35 / 0.053 | +0.003 [-0.006, +0.012] |
| SciPlex3 reference, point 0.0222 | 0.58 / 0.050 | 0.50 / 0.053 | -0.000 [-0.006, +0.006] |
| SciPlex3 reference, upper 0.4388 / 0.5294 / 0.6254 | 0.28 / 0.39 / 0.51 | 0.11 / 0.20 / 0.40 | -0.013 [-0.038, +0.008]; +0.013 [-0.000, +0.030]; +0.004 [-0.006, +0.015] |
| SciPlex3 v2 (point, three caps) | 0.53-0.58 / 0.048-0.055 | 0.19-0.50 | -0.001 to +0.006, all intervals contain 0 |
| L1000 reference, point 0.0008 / 0.0021 / 0.0048 | 0.049 / 0.069 / 0.088 | 0.031 / 0.042 / 0.069 | +0.008 [-0.073, +0.083]; **-0.037 [-0.103, +0.001]**; 0.000 [-0.023, +0.016] |
| L1000 reference, upper (three caps) | 0.018-0.083 | 0.005-0.047 | -0.004 to +0.040, all intervals contain 0 |

- **Re-selection buys coverage, not a better frontier.** At the same cap, re-selection keeps up to three times
  the decisions that stopping keeps, because it finds another action within the cap. At matched coverage its
  risk equals stop-only's in every SciPlex3 cell.
- **The one suggestive cell is L1000, point cap 0.0021:** conditional risk 0.018 [0.000, 0.042] against P0's
  0.095, at coverage 0.069 against 0.101, and -0.037 [-0.103, +0.001] against stop-only at matched coverage.
  It rests on about three wrong events and is one of twelve cells; it is recorded, not claimed.
- **Choosing a cap on the calibration fold (repaired P2)** reproduces the fold-level artefact of section 3
  (abstain-all in the folds whose calibration fold exceeded alpha).

Decision: **risk-select stays an opt-in research arm.** Truncation-only abstention and re-selection are
different operating points on one frontier. Neither has a certificate.

## 6. Where information is lost, module by module

The chain, and what each step keeps. Evidence is on identical executed steps (split test role; the ablation
records of the `reference` arm; `analysis.json` `ladder` and `outcome_changes`).

| Step | What it keeps and discards | Evidence |
|---|---|---|
| Raw data -> pseudobulk shift | Keeps the mean; discards single-cell distribution | Observed distributions add no mechanism signal beyond the mean (section 9); little is lost here for this task |
| Shift -> response prediction (A1) | Direction is recovered (centred cosine about 0.37-0.44); identity is partly lost by shrinkage | Section 4 |
| Prediction -> projected cosine to references (kernel) | Discards magnitude. The reading is a cosine-to-template rule gated by replicate-agreement detection, so magnitude matters only through detection | `transfer_dist` (magnitude-keeping) is selected by training likelihood in 12 of 40 models, yet changes step log loss by -0.002 [-0.007, +0.004] (SciPlex3) and -0.003 [-0.008, +0.004] (L1000) |
| Kernel -> reading probabilities (reference weighting, shrunk to the reference world) | The in-context layer can only reweight training references' readings; unit shrinkage; nothing before the first purchase | v2 changes the forecast at 33% (SciPlex3) and 41% (L1000) of executed steps (99-100% of steps with a prompt); log loss -0.004 [-0.010, +0.004] and -0.000 [-0.006, +0.007] |
| **Perfect response knowledge through the same interface (oracle, diagnostic)** | Upper bound of better prediction | Log loss **-0.086 [-0.135, -0.039]** (SciPlex3) and -0.014 [-0.038, +0.006] (L1000); forecasts change at every step |
| Reading probabilities -> chosen action | Expectimax over at most two steps; stop on first elimination | v2 changes the chosen action at 3.5% (SciPlex3) and 4.0% (L1000) of decision points; the oracle at 25% and 10% |
| Chosen action -> decision outcome | The validator decides; most readings are "undetected" or "ambiguous" whichever condition is bought | The oracle changes the first action in 312 of 1,056 SciPlex3 episodes, yet changes the decision in only 34, net correct **+0.008 [-0.004, +0.021]**; L1000 18 of 1,895, +0.002 [-0.006, +0.012]. v2: 10 and 6 episodes, correct -0.002 [-0.006, +0.002] and +0.002 [-0.004, +0.008] |

**Where the improvements disappear.**
- **Predicted responses to reading forecasts.** Response-model gains that are real in RNA space (section 4)
  shrink to nothing in reading log loss. The oracle shows that the interface could carry much more
  (SciPlex3 -0.086 nats), so on the forecast side **response prediction quality is the bottleneck**, not the
  cosine conversion.
- **Better forecasts to better decisions.** Even perfect response knowledge moves decisions by at most about one
  percentage point, and not detectably. On the decision side **the task (which conditions can decide a
  compound, and the validator) is the bottleneck**, which agrees with protocol v2's headroom finding (the fixed
  order reaches 63-99% of the oracle's correct decisions).

**Attribution.** Across the 40 models v2 chose `transfer` 15 times, `transfer_dist` 12, `prompt` 6, `additive` once
and nothing (kappa = 0 or no elimination) 6 times. On L1000, half of v2's executed steps used `transfer_dist`
and a fifth used the direct prompt similarity. No gain may be attributed to `rrt_q` where another source formed
the kernel. The minimal alternative conversion (`transfer_dist`) was implemented and tested: it adds nothing.

## 7. Dual-core comparison: world model, policy and their interaction

The 2 x 3 grid on the split design's test folds (identical episodes, menus, budgets, executor). Stop-only is the
repaired P2 threshold on the step risk; risk-select is the pre-declared median point cap. Unit means; effects
are unit-bootstrap medians and 95% intervals.

| Cell | Coverage | Wrong per episode | Wrong among decided | Correct | Measurements |
|---|---|---|---|---|---|
| SciPlex3 reference x P0 | 0.602 | 0.032 | 0.053 [0.029, 0.082] | 0.570 | 1.52 |
| SciPlex3 reference x stop-only | 0.421 | 0.010 | 0.024 [0.006, 0.047] | 0.411 | 1.04 |
| SciPlex3 reference x risk-select | 0.556 | 0.029 | 0.053 [0.027, 0.085] | 0.526 | 1.54 |
| SciPlex3 v2 x P0 | 0.600 | 0.031 | 0.052 [0.028, 0.082] | 0.569 | 1.52 |
| SciPlex3 v2 x stop-only | 0.301 | 0.008 | 0.026 [0.004, 0.058] | 0.294 | 0.83 |
| SciPlex3 v2 x risk-select | 0.563 | 0.031 | 0.055 [0.030, 0.087] | 0.532 | 1.54 |
| L1000 reference x P0 | 0.101 | 0.010 | 0.095 [0.039, 0.182] | 0.091 | 1.00 |
| L1000 reference x stop-only | 0.049 | 0.004 | 0.088 [0.015, 0.232] | 0.044 | 0.42 |
| L1000 reference x risk-select | 0.069 | 0.001 | 0.018 [0.000, 0.042] | 0.068 | 0.73 |
| L1000 v2 x P0 | 0.102 | 0.010 | 0.094 [0.038, 0.177] | 0.093 | 0.98 |
| L1000 v2 x stop-only | 0.050 | 0.004 | 0.085 [0.014, 0.218] | 0.046 | 0.41 |
| L1000 v2 x risk-select | 0.072 | 0.001 | 0.017 [0.000, 0.040] | 0.071 | 0.72 |

| Effect | SciPlex3 | L1000 |
|---|---|---|
| **World-model improvement** (v2 - reference under P0): correct | -0.001 [-0.005, +0.002] | +0.001 [-0.004, +0.009] |
| same: wrong per episode | -0.0005 [-0.0014, 0.000] | 0.000 [-0.0001, 0.000] |
| same: measurements | 0.000 | **-0.021 [-0.029, -0.014]** |
| **Agent-policy improvement**, stop-only - P0 (reference): correct / wrong | -0.157 [-0.218, -0.104] / -0.021 [-0.037, -0.010] | -0.047 [-0.077, -0.021] / -0.005 [-0.010, -0.001] |
| same, risk-select - P0 (reference): correct / wrong | -0.043 [-0.065, -0.025] / -0.002 [-0.007, +0.001] | -0.023 [-0.037, -0.012] / **-0.008 [-0.015, -0.003]** |
| **Interaction**, stop-only: coverage / wrong | -0.117 [-0.174, -0.066] / -0.002 [-0.004, 0.000] | 0.000 / 0.000 |
| same, risk-select: correct / wrong | +0.007 [-0.005, +0.020] / +0.002 [0.000, +0.006] | +0.001 [0.000, +0.004] / 0.000 [0.000, +0.0001] |

- **World-model improvement: none on decisions.** v2 decides as the reference world does. The one significant
  difference is 2% fewer measurements on L1000 at unchanged decisions, which is too small to matter
  (0.02 measurements per episode, about 0.1 assay days).
- **Agent-policy improvement: a trade-off, not an improvement.** Every abstaining policy buys fewer wrong
  eliminations with correct decisions, at a rate no better than the unconstrained frontier (section 5). The
  SciPlex3 stop-only gain comes from abstaining whole folds.
- **Interaction: no synergy.** The one interval away from 0 (SciPlex3 stop-only coverage, -0.117) is the same
  threshold-selection artefact as block 7's. The v2 world's calibration fold exceeded alpha in two folds instead
  of one, so it abstained twice as much. It is not an interaction between the cores.

## 8. Future information value and a longer horizon

**Can the first measurement be worth choosing because its profile improves later predictions?** In these runs
the v2 arm differs from the reference arm *only* through prompt-conditioned forecasts at step 2. Its first action
and first belief update are identical by construction; the test `test_no_prompt_forecast_equals_reference_world`
and 0 of 2,951 differing first actions confirm it. So v2 - reference on identical episodes is the realised value
of "the first profile improves the next prediction". It is -0.002 [-0.006, +0.002] correct decisions (SciPlex3)
and +0.002 [-0.004, +0.008] (L1000). The oracle, which also knows the step-1 response, bounds it at +0.008
[-0.004, +0.021] and +0.002 [-0.006, +0.012]. With the realised value indistinguishable from 0 and the ceiling
about one point, a planner that values the first measurement for its future prompt, by predictive integration
over the profile, has nothing to gain on these tasks. It was **not built**; the limited approximation used is
this empirical bound. No simulated profile was ever treated as evidence.

**A longer horizon.** Every registered tier allows at most two measurements (`max_measurements = 2`, budgets of
12-16 days for 5.25-8-day conditions), so steps with two or more prompts are 0 of every run and multi-prompt
aggregation (A2) cannot occur. That is why A2 prediction gains are not decision gains. Before defining a third
step, an oracle headroom check (`horizon_headroom.py`, diagnostic; it reads outcomes) asked, for every block 7
episode still undecided after two measurements, whether any untried design-available condition would decide it:

| Tier | Undecided after two | With an untried condition | Some untried reading eliminates correctly | ... wrongly | Units that could decide |
|---|---|---|---|---|---|
| SciPlex3 A | 69 | 69 | 18 | 4 | 11 |
| SciPlex3 B | 467 | 467 | 95 | 31 | 51 |
| L1000 LT | 795 | 795 | 60 | 4 | 14 |
| L1000 T | 857 | 0 | 0 | 0 | 0 |

A clairvoyant third step would add at most about 113 correct decisions in 1,517 SciPlex3 episodes (7%) and 60 in
5,084 L1000 episodes (1%), each at one more condition (6 to 8 assay days and at least 2 wells). A real planner
would reach a fraction of that, and the in-context layer, the reason to want a third step, adds nothing at step 2
(section 6). **No longer-horizon task was introduced.** If the owner wants one, it must be a separately specified
experiment (a budget of at least 18-24 days, three measurements, costs counted in wells and days), and SciPlex3 B
is the only tier with enough headroom to test it. The registered benchmark is unchanged.

(An earlier version of this table, in this block's working notes, had "correct" and "wrong" swapped by a sign
error in the first draft of `horizon_headroom.py`. The version above is the corrected one.)

## 9. The population backend

`src/virtual_cell/population_flow.py` was evaluated under `protocol_population.json`, frozen before any feature
was computed (`population_eval.py`). The data: SciPlex3, 24 h, 10 uM, three cell lines, all 188 compounds; 564
conditions with up to 128 seeded cells each; vehicle cells of the same line and plate (51 vehicle groups); 32 PCs
fitted on vehicle cells only (20.5% of single-cell variance). Units are InChIKey connectivity blocks over the
registered folds.

**Part 1: is there decision signal in observed populations beyond pseudobulk?** The task is the mechanism
class of a held-out compound from its three-line profile: 135 compounds, 132 units, 17 classes with at least 3
units each; multinomial logistic regression, no tuning; outer folds are the registered folds.

| Features | Log loss | Balanced accuracy | Macro AUROC |
|---|---|---|---|
| A: pseudobulk mean shift (3 x 2,473 genes) | 2.092 | 0.280 | 0.846 |
| B: A + distribution (sd ratios on 32 PCs, responder fraction, energy distance) | 2.123 | 0.229 | 0.842 |
| C: distribution only | 2.217 | 0.171 | 0.767 |
| D: A + abundance (cells at 10 uM / 10 nM) | 2.106 | 0.277 | 0.842 |

- **Registered verdict: no population signal beyond pseudobulk.** B - A log loss is +0.033 [+0.002, +0.065]
  (worse). Abundance adds nothing (+0.015 [-0.010, +0.041]); the shuffled-distribution control behaves like B.
- **Post hoc (written after part 1 was read), a design check.** In B the 102 distribution features compete with
  7,419 pseudobulk features inside one PCA. Giving them equal weight by late fusion lowers log loss (-0.22
  [-0.38, -0.08]), but tempering A's own probabilities lowers it more (-0.38 [-0.57, -0.20]), and fusion is worse
  than tempered A (+0.16 [+0.04, +0.29]). On temperature-free ranking metrics fusion equals A (macro AUROC
  -0.002 [-0.018, +0.015], balanced accuracy -0.012 [-0.099, +0.065]). The distribution block carries some
  signal on its own (AUROC 0.77), but it is redundant with the mean. The verdict stands.

**Part 2: does the flow predict held-out populations better than population-preserving baselines?**
564 pairs, 185 units, 5 grouped folds, epoch chosen on the next fold (selected epochs 2-21 of 80).

| Unit mean | Flow | Mean shift | Vehicle | Chemical NN | NN with its sd ratios | Oracle mean (diagnostic) |
|---|---|---|---|---|---|---|
| MMD | 0.0200 | 0.0206 | 0.0234 | 0.0356 | 0.0362 | 0.0008 |
| Energy distance | 1.378 | 1.408 | 1.566 | 2.220 | 2.298 | 0.286 |
| Squared error of the mean (PC space) | 0.559 | 0.575 | 0.659 | 1.040 | 1.040 | 0 |
| Squared error of log sd ratios | **0.036** | 0.046 | 0.046 | 0.046 | 0.056 | 0.046 |

- **Registered verdict: the flow is not better than every baseline.** Against the mean shift: MMD -0.0006
  [-0.0019, +0.0007], energy -0.030 [-0.102, +0.042], mean error -0.016 [-0.056, +0.024]. It beats the vehicle
  and both nearest-neighbour baselines, and it predicts variance ratios better than every baseline (-0.0097
  [-0.011, -0.009]): a real, small second-moment gain.
- **The mean carries almost all of the distribution difference** (the oracle mean reaches MMD 0.0008), and a
  chemical nearest neighbour is worse than predicting no effect.
- **Decision link: not supported by the data.** Part 1 found no mechanism signal in observed populations beyond
  pseudobulk, so the flow's better variance ratios cannot help this decision task. The backend stays
  **experimental**. Flow time is numerical, and couplings are not lineages.
- The Codex pilot's "PASS" (4 test groups, 1 uM, A549) is superseded. At that scale the flow, the mean shift and
  the vehicle were within 0.003 MMD of each other, with no uncertainty.

## 10. The data bottleneck

From the registered data and block 7's traces (`data_audit.py`; post hoc, exposed development data):

| | SciPlex3 | L1000 |
|---|---|---|
| Independent units (labelled) | 185 (134) | 335 (335) |
| Classes; units per class (min / median / max) | 18; 2 / 3.5 / 25 | 25; 5 / 11 / 32 |
| Rows detected (among QC-passed) | 38% | 9% |
| Replicate quality (median) | 0.085 (split-half Pearson) | 0.19 (`cc_q75`) |
| Batch-class association (Cramer's V; batches) | 0.24 (27 plates) | 0.47 (264 batches, most small) |
| E2 decision units; units that ever decide | 105; 84 | 229; 53 |
| Coverage of the unconstrained agent (unit mean) | 0.63 | 0.14 |
| Executed readings "undetected" | 40% | 85% |
| Wrong eliminations; units carrying them; top-5 share | 51; 22; 51% | 31; 16; 52% |
| Wrong events by fold (0-4) | 31 / 9 / 5 / 0 / 6 | 8 / 3 / 4 / 9 / 7 |
| Structural abstention (validator cannot eliminate) | tier A fold 2 (20 episodes) | tier LT folds 0 and 3 (1,212 episodes) |

The limitations are separated as follows.
- **A poor model:** partly. Direction is predicted (centred cosine about 0.37-0.44), but compound identity is not
  (section 4), and the oracle ceiling (section 6) shows how far the reading forecast is from what better response
  prediction would allow.
- **A weak risk-ranking signal:** yes. Step-risk AUROC is 0.66 [0.56, 0.75] (SciPlex3) and 0.58 [0.51, 0.64]
  (L1000); the planner's conservative bound does not rank at all (B5).
- **An uninformative task:** L1000, where 85% of readings are "undetected" and three-quarters of units never decide.
- **Insufficient power, and a conservative bound:** these must be separated. Block 7's "25-30x more units" came
  from Hoeffding-Bentkus. Take the one SciPlex3 operating point where abstention lowers the risk (threshold 0.01:
  risk 0.026, coverage 0.33). A betting test certifies it with probability about 0.58 at 400 units and about 1.0
  at 800 for a single pre-chosen candidate, or needs about 1,600 with Holm over 15 candidates; HB needs about
  3,200, and fails with Holm even then. That is 4-15x the 105 units available, not 25-30x, and it holds only
  for that operating point. **Where the risk sits at alpha (SciPlex3 P0 0.049, every L1000 policy), no number
  of units certifies**, because the quantity is at the boundary. That, not the bound, is why the unconstrained
  agent cannot be certified.
- **What data would help.** More independent compounds per mechanism class (SciPlex3 has a median of 3.5 units
  per class) with responses measured at conditions where they are detected, and, for L1000's weakly responding
  compounds, a second assay whose readings are informative. More expression rows for the same compounds, or
  more cells, do not add units. Loosening alpha to obtain a certificate is not acceptable and was not done.

## 11. Literature: what each source changed

Identifiers were resolved on 2026-09-28 through the bioRxiv and Crossref APIs.

| Source | Status found | What it changed here | Adaptation or novelty |
|---|---|---|---|
| PRESAGE, doi:10.1101/2025.06.03.657653 | v1 only, preprint | Nothing new beyond block 7 | - |
| State, doi:10.1101/2025.06.26.661135 | v2; published, *Cell* 189(19), doi:10.1016/j.cell.2026.07.052 | Discrimination kept as the response-layer primary | Adaptation |
| Tahoe-x1, doi:10.1101/2025.10.23.683759 | v1, preprint | Mean-shift and context-mean baselines, also in the population evaluation | Adaptation |
| Stack, doi:10.64898/2026.01.09.698608 | v2 (2026-06-08), preprint; abstract unchanged from v1 | Purchased-prompt rule, now enforced by `PromptSet` | Adaptation, stricter contract |
| SCALE, doi:10.64898/2026.03.17.712536 | **v2 (2026-09-03)**, preprint; abstract identical to v1; full-text changes not inspected | Population evaluation against population-preserving baselines, not reconstruction alone | Adaptation |
| MultiFlow, doi:10.64898/2026.08.20.746112 | v1, preprint | No second modality in these data; not used | - |
| Learn then Test, *Ann. Appl. Stat.* 19(2):1641-1662 (2025), doi:10.1214/24-AOAS1998 | published | Risk control as multiple testing over explicit candidates; union-null p-value for two constraints; Holm instead of a guessed fixed sequence | Adaptation |
| Waudby-Smith and Ramdas, *JRSSB* 86(1):1-27 (2024), doi:10.1093/jrsssb/qkad009 | published | Variance-adaptive betting p-value (`betting_pvalue`) | Adaptation |
| Yu and Liu, arXiv:2606.08517 (2026) | preprint | Confirms the design: bound the ratio risk and the acceptance rate together, with variance-adaptive bounds, selecting on the certifying data | Independent convergence; not novel here |
| Bai and Jin, arXiv:2603.24704 (2026), SCoRE | preprint | Risk conditional on selection with e-values is the next step if per-episode guarantees are wanted; not implemented | Noted |
| Fannjiang et al., *PNAS* 119(43) (2022), doi:10.1073/pnas.2204569119 | published | Calibration data generated by the model's own choices (feedback covariate shift) is why calibration and test must come from one frozen model-policy process (`split` design) | Adaptation of the argument |
| Heidari et al., doi:10.64898/2026.02.14.705879 (2026) | v1, preprint | Correlation and distributional metrics are scale-sensitive and energy distance misses gene-gene dependence; population part 2 reports mean, sd-ratio, MMD and energy side by side, anchored by vehicle and oracle mean | Adaptation |
| Agarwal and Bisht, arXiv:2606.12639 (2026) | preprint | The metric picks the winner for unseen chemistry: a per-layer selection rule is declared (section 4) instead of choosing a metric after scoring | Adaptation |
| Ahlmann-Eltze et al., *Nat. Methods* (2025), doi:10.1038/s41592-025-02772-6 | published | Simple baselines stay live candidates: additive now competes in the world model | Adaptation |
| Huang et al., POPPER, ICML 2025 (PMLR 267), arXiv:2502.09858 | published | Sequential e-value falsification with type-I control is the agent-side analogue; MAESTRO's agent does not aggregate evidence across experiments that way | Noted, not implemented |
| Non-myopic design (Rainforth et al., doi:10.1214/23-STS915; two-step lookahead BOED) | published | Future-information value is bounded empirically (section 8) before any non-myopic planner is built | Adaptation of the question |

No source makes the v2 world model or agent methodologically novel. The contribution is verification:
repaired risk control and lineage, measured bottlenecks, and negative or null results with named reasons.

## 12. Corrections to earlier claims

| Earlier claim (source) | Correction |
|---|---|
| "Learn-then-Test certifies only the vacuous always-abstain" (block 7 README 6.3, log 2026-09-27 block 7) | Nothing was certified. The fixed-sequence loop broke on the untestable threshold 0 and fell back to it. The repaired procedure also certifies nothing: "no candidate certified" |
| P3 "wrong among decided 0 [0, 0]" at coverage 0 (block 7 README 6.3) | Undefined, not 0 |
| "Cross-fitted Platt ... improves log loss only on L1000 and makes it worse on SciPlex3" (block 7) | Lineage-dependent. With calibration and test from one frozen model, neither change is distinguishable from 0 |
| Wrong-elimination forecasts are "1.6-2.0x too low on selected actions" (block 7) | Confirmed and larger with correct lineage and three-fold models: 1.9-3.1x |
| "Certification would need about 2,700-3,400 units on SciPlex3 and about 1.5 million on L1000"; "the binding limitation is the number of independent units" (block 7) | Specific to Hoeffding-Bentkus and one operating point. A betting test needs about 400-800 units (single candidate) or about 1,600 (Holm over 15) at the SciPlex3 point where abstention helps. Where the risk sits at alpha, no n suffices; the risk level, not n, is binding there |
| "Inner MSE falls by only 0.2-0.8%" for `rrt_q` (block 7 README 5) | In-sample for gamma. Honest: a median 0.07% on SciPlex3 (`rrt_q` beats `ridge_st` in 69.5% of pairs, not 97.9%) and 0.3% on L1000 |
| "precision" aggregation weights (block 7) | Inverse inner-CV error weights, near 0.5, equivalent to equal weighting in practice; not calibrated precisions |
| E1 keep rules "passed", read as `rrt_q` being the backend of choice (block 7 E2 protocol) | The keep rule compared `rrt_q` with `ridge_st` only. Additive transfer discriminates better; no response model dominates on the declared rule |
| "The world model's magnitude and distribution never enter the transfer kernel, so small magnitude gains are erased" (diagnosis 2026-09-28 section 3) | The registered reading is a cosine-to-template rule gated by replicate-agreement detection, so magnitude matters only through detection. A magnitude-keeping kernel was tested and adds nothing |
| "Platt results do not enter P2/P3" presented as a defect (diagnosis section 5) | Immaterial: a monotone increasing recalibration cannot change which truncations a threshold can reach |
| "Correct direction: isolate each outer fold ... bias direction unknown" (diagnosis section 7) | Confirmed and repaired. The bias was not uniform in direction (calibration above) and did not change any certification verdict |
| The population pilot "PASS" (Codex, 2026-09-27) | Superseded: at 564 pairs and 185 units the flow ties the mean-shift baseline; observed populations add no decision signal beyond pseudobulk |
| "PyTorch here is a CPU-only build" (memory of 2026-09-27) | The `maestro` env has a CUDA build (2.7.0+cu126); block 7's experiments ran in `C:/Python314`, which has a CPU build |
| Block 6 and 7's in-context gains described as world-model gains of `rrt_q` | On L1000 most kernels came from other sources (prompt in 4/5 T folds in block 7; `transfer_dist` in half of v2's steps). Attribution is by source |

## 13. Resources, unfinished items and limitations

**Resources.** About one hour of wall time for the experiments, run concurrently: nested runs 10:18-11:18, E1
honest 10:22-11:06, population 10:29-11:05; about 4 CPU-hours in all. 20 physical cores were available, but 3
workers were used because only 0.3-1.6 GB of RAM was free (other applications held most of the 16 GB). GPU unused.
$0, 0 wells, no download; literature via the bioRxiv and Crossref APIs and web search. Outputs: 74 MB
(`block7_repaired` 26 MB, `e1_honest` 19 MB, `population` 16 MB, `runs` 15 MB).

**Unfinished or not attempted, by name.**
- A predictive-integration planner for future prompt value: not built, because the empirical bound is null (section 8).
- A longer-horizon task: not introduced, because the oracle headroom is small and it needs an owner decision (section 8).
- Honest re-selection of the reference world's (s, k, e) inside inner folds (A11): documented, not repaired.
- The extended rank grid was scored on training data only; its effect on direction, identity or decisions is unknown.
- Conditional-on-selection risk control with e-values (SCoRE) and cross-experiment e-value aggregation (POPPER):
  noted, not implemented.
- SCALE v2's full-text changes were not inspected.
- The production path (`src/`) was not touched: no research component earned promotion.

**Limitations that bound every conclusion here.**
- All data are exposed development data (SciPlex3 and L1000 since 2026-09-26). No result here is an untouched
  test, and E-DATA1's failure rule still forbids planner-superiority claims on these tasks.
- Wrong-elimination events are few and concentrated (about 20 units per dataset), so every risk quantity is noisy
  and fold-dependent.
- Models on three folds are weaker than block 7's four-fold models. The corrected numbers describe a
  somewhat weaker agent, which is the price of correct lineage.
- Mechanism labels are reference annotations, not measured target engagement.
- The population evaluation covers one time point and one dose (24 h, 10 uM) with 128 cells per condition and
  logistic regression without tuning. A different decision task (for example viability or subpopulation
  response) could find population signal this one did not.

## 14. Promotion recommendation

| Component | Decision | Reason |
|---|---|---|
| `risk_control` (repaired Learn-then-Test, P2, explicit abstain-all) | **Retain as the research standard**; replaces block 7's P3 for any future risk-control analysis | Confirmed defect repaired and tested; valid under its stated assumptions |
| `nested` split design and lineage checks | **Retain as the required design** for any calibration or threshold claim | Without it no finite-sample statement is valid |
| `transfer_honest` errors | **Retain** for error estimates and weights | Removes an optimism that is small in practice |
| `WorldV2` contract (`PromptSet`, cache identity) | **Retain** as the research world-model interface | Closes two contract gaps at no measured cost |
| `WorldV2` new sources (`additive`, `transfer_dist`) | **Keep experimental** | Selected by training evidence in 13 of 40 models; no forecast or decision gain |
| In-context world model (v1 or v2) over the reference world | **Do not promote** | No decision effect on identical episodes; about 2% fewer measurements on L1000 only |
| Risk-select (`wrong_risk_cap`) and stop-only abstention | **Keep as opt-in research arms; no default** | Same frontier; no certificate; the conservative bound does not rank |
| Platt recalibration of step risk | **Do not use as a gate** | Not distinguishable from raw under correct lineage; cannot improve ranking |
| Population flow backend | **Keep experimental**, reason `no_population_signal_beyond_pseudobulk` | Ties the mean-shift baseline; better only on variance ratios, which carry no decision signal here |
| Production defaults and `src/` | **Unchanged** | Nothing above earns promotion |

**What would change this.** More independent units per mechanism class at detectable conditions, a task in
which the choice of condition changes what the validator can decide (section 6), and a risk score that ranks
danger. A bigger world model is not on that list: the oracle shows that perfect response knowledge moves
decisions by about one point here.

## 15. Reproduction

Tests run in the `maestro` env (`D:/anaconda/envs/maestro/python.exe`, Python 3.11.16). Experiments ran in
`C:/Python314/python.exe` (Python 3.14.4, numpy 2.4.4, scikit-learn 1.8.0, pyarrow 24.0.0), the interpreter that
produced block 7's outputs; population part 2 ran in the `maestro` env, as the Codex pilot did.

```bash
python -m pytest research/dual_core_v2 -q -p no:cacheprovider -o addopts=
python -m research.dual_core_v2.freeze --verify
python -m research.dual_core_v2.run --workers 3
python -m research.dual_core_v2.report
python -m research.dual_core_v2.e1_honest run
python -m research.dual_core_v2.block7_repaired
python -m research.dual_core_v2.data_audit outputs/dual_core_v2_20260928/block7_repaired/traces.pkl outputs/dual_core_v2_20260928/diagnostics/data_audit.json
python -m research.dual_core_v2.horizon_headroom outputs/dual_core_v2_20260928/block7_repaired/traces.pkl outputs/dual_core_v2_20260928/diagnostics/horizon_headroom.json
python -m research.dual_core_v2.population_eval extract
python -m research.dual_core_v2.population_eval part1
python -m research.dual_core_v2.population_eval part2
```

`block7_repaired` writes block 7's E2 traces to one pickle (`traces.pkl`) for the two diagnostics. Outputs in `outputs/dual_core_v2_20260928/`: `runs/*.{json,traces.jsonl.gz,ablation.jsonl.gz}` (40 nested
jobs, write-once), `analysis.json`, `e1_honest/`, `population/`, `diagnostics/`, `block7_repaired/`.
