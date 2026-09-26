# Why the contingent two-step policy stops, and whether a fix helps on independent data

Subsequent targeted repair: [sparse-reference value and acquisition cost](../sparse_value/README.md)
fixes the 32 fallback-first early stops and reports a new cost/risk-aware conditional-reference
policy. Frozen replay entry points explicitly preserve the original behavior described below;
new calls to `policies.arms` use the repaired continuation. These later results are retrospective.

**Date:** 2026-09-26, 21:52 to 22:45 (+0800)

**Status:**
- Diagnosis and a fair SciPlex3 replay are complete.
- One revision was pre-registered and evaluated on independent L1000 data.
- The frozen rule gives **SHADOW**. The effect is negligible, so the revision stays opt-in and is
  not promoted.

**Scope:** research code only. Nothing in `src/` changed, and production defaults are unchanged.

## 1. Answer

1. **Why the fixed sequence wins on SciPlex3: the two-step policy buys fewer measurements.**
   - In tier A it made 0.97 measurements per episode, against 1.63 for the fixed sequence.
   - Stops after a neutral first reading, deferrals before any measurement and stops after a QC
     failure account for 0.232 of the fixed sequence's 0.274 correct-decision advantage.
   - Different measurement choices account for 0.042.
   - Most of those stops were *uninformed*: the planner had no paired references, or too few,
     for the continuation (89 of 106 in tier A, 610 of 767 in tier B). None was a code defect.
2. **The QC asymmetry was real but small.** With identical rules for every arm, the tier-A gap is
   0.259 correct decisions [0.161, 0.360], against 0.274 in the unmatched comparison.
3. **The revision on SciPlex3.** It continues with the fixed sequence's next action only when the
   planner's stop is uninformed. On SciPlex3 it added +0.057 utility in tier A and +0.050 in
   tier B, but that data informed the rule.
4. **The revision on L1000 (independent, pre-registered).**
   - It added +0.0013 utility [+0.0002, +0.0026] in the primary tier: 11 more correct and 1 more
     wrong decision in 6,880 episodes, at the cost of 581 extra measurements.
   - It did not beat the fixed sequence (+0.014 [-0.012, +0.041]).
   - On L1000 most of the planner's stops are informed (84%), or forced by time order, so the
     fallback rarely applies.
5. **Verdict: SHADOW by the frozen rule.** The utility interval excludes zero only for the primary
   clustering unit; under batch-cohort clustering its lower bound is exactly 0. The rule stays
   opt-in and logged.

## 2. What the working tree already contained (verified, not assumed)

The follow-up (`research/acquisition_followup/`) came from a Codex session that ended at 21:01.
It is uncommitted and was preserved. None of its files were edited.

| Reported | Verified here |
|---|---|
| Runtime execution gate repaired | `src/agent/orchestrator.py` now filters execution by the selection in both coverage modes and hands a partial choice to the agent check. Covered by `tests/test_discriminating_acquisition.py`; the full suite passes (1,326). |
| Observation history propagated | `UpdateRecord` carries `outcome_label` and `candidate_hypotheses`, and `ReferenceCardForecaster.forecast` conditions on the latest valid neutral result. Covered by `test_followup.py`. |
| Directional elimination probability | `dyn_model` now reports the elimination probability for each hypothesis, refuses to call it a correct-elimination probability, and falls back to `dyn_ref`. Covered by `test_dyn_model.py`. |
| Paired-reference two-step planning and SciPlex3 run | Recorded source hashes match the current files, and the run reproduces. Every recorded plan equals a recomputation (0 mismatches). |
| Two-step minus one-step +0.009 (A) and 0.000 (B); two-step 0.366 against fixed 0.640 (A) | Confirmed from the records. The follow-up's intervals were compound-clustered. |
| Stops after neutral first results | Confirmed: 41 of 147 continued in tier A, 203 of 970 in tier B. |
| Sequence arms stop after QC failure; others continue | Confirmed. In tier A, `two_step` continued 0 of 9 times after a QC failure, `fixed` 16 of 16 and `da` 8 of 9. |
| L1000 ridge transition better than persistence, not better than the training 24 h mean | Confirmed from `outputs/acquisition_followup/lincs/summary.json`: MSE improvement over the mean -0.787 [-1.574, +0.095]. No transition model is used by any policy here. |
| Derived cache without its preprocessing runner; partial annotation | Confirmed. No script in the repository writes `subset48`. The six GEO metadata files match GEO's published SHA-512 sums; the expression cache cannot be re-derived locally, because no Level 3-5 GCTX is present. |

## 3. Phase 1: where the stops come from (`diagnose.py`)

Every recorded stop after an unresolved or undetected first reading gets one reason, in this
order: legality or time order, budget, no paired references, implementation defect, thin
support, wrong-elimination risk, no gain.

The reasons are defined as follows:
- **Thin support:** the continuation is positive on raw reference frequencies, but not after the
  planner's Jeffreys shrinkage.
- **Wrong-elimination risk:** a correct elimination is forecast but fails the 2:1 break-even.
- **No gain:** no conditioned reference eliminates correctly.

Every recorded plan was recomputed with the follow-up's own `plan_two_step`, and all matched.

**Facts** come from the records and from each compound's own measured data:
- stops after a neutral first reading: 106 in tier A, 767 in tier B;
- stops after a QC failure: 9 in each tier;
- deferrals before any measurement: 59 in tier A, 153 in tier B.

**Explanations** come from the planner's reference forecasts:

| Tier, first reading, time | No paired references | Thin support | Wrong risk | No gain | Total |
|---|---:|---:|---:|---:|---:|
| A, undetected, 24 h | 3 | 50 | 8 | 2 | 63 |
| A, undetected, 72 h | 20 | 1 | 0 | 4 | 25 |
| A, ambiguous, 24 h | 10 | 1 | 0 | 2 | 13 |
| A, ambiguous, 72 h | 4 | 0 | 0 | 1 | 5 |
| B, undetected, 24 h | 253 | 182 | 21 | 115 | 571 |
| B, ambiguous, 24 h | 133 | 42 | 2 | 19 | 196 |

No stop was due to legality, budget or a code defect.
- **By class (tier A):** HDAC 29, Aurora 17, JAK 13, Sirtuin 13, histone methyltransferase 10,
  PARP 8, HIF 8, DNA methyltransferase 5 and BET 3. The per-class tables for both tiers are in
  `outputs/sequence_audit_20260926/diagnosis/summary.json`.
- **Timing (tier A):** 24 h stops are mostly thin support; after a 72 h first reading they are
  mostly missing paired references.

**What the fixed sequence's next measurement actually read, for the same compounds** (a fact):

| Stops | Correct | Wrong | Neutral | No legal next | QC failed |
|---|---:|---:|---:|---:|---:|
| Tier A, 106 | 27 | 5 | 58 | 15 | 1 |
| Tier B, 767 | 175 | 24 | 555 | 0 | 13 |

By reason in tier A:
- no paired references: 13 correct, 1 wrong;
- thin support: 11 correct, 2 wrong;
- wrong risk: 2 correct, 0 wrong;
- no gain: 1 correct, 2 wrong.

**Source of the fixed sequence's advantage.** The net correct-decision difference is split by the
two-step policy's path in pairs where exactly one arm was correct.

| Two-step path | Tier A | Tier B |
|---|---:|---:|
| Stopped after a neutral first reading | +0.140 | +0.101 |
| Deferred before measuring | +0.074 | +0.024 |
| Stopped after a QC failure | +0.018 | +0.001 |
| Continued, but with a different second measurement | +0.039 | +0.006 |
| First measurement eliminated | +0.003 | -0.032 |
| **Net** | **+0.274** | **+0.101** |

The advantage comes from acquiring more measurements, not from choosing better ones. In tier B
the two-step's own first choices were better; the difference is -0.032.

## 4. Phase 2: fair comparison (`policies.run_matched`, `replay.py`)

Every arm now goes through one runner that sets the following:
- candidate actions and exposure-time order, which also count failed assays;
- two measurements and 16 assay-days;
- the registered rules and `EvidenceState` updates;
- one QC rule for all arms;
- the stops and the terminal utility (+1 correct, -2 wrong, 0 otherwise).

Unavailable forecasts are never filled. After a QC failure, the two-step arms value one remaining
measurement from unconditioned forecasts, because a failed assay says nothing about the compound.

The replay reproduces the original records wherever the original rules were already matched. All
2,496 episodes were identical for each of these five pairs:
- `fixed` and `da` under `continue`;
- `two_step`, `one_step_utility` and `two_step_permuted` under `stop`.

Results under the matched rules (tier A; the full table is in
`outputs/sequence_audit_20260926/phase2_matched_replay/report.md`):

| Arm (QC `continue`) | Correct | Wrong | Utility | Measurements |
|---|---:|---:|---:|---:|
| fixed | 0.640 | 0.057 | 0.527 | 1.63 |
| magnitude | 0.396 | 0.021 | 0.354 | 1.64 |
| da (runtime history conditioning) | 0.426 | 0.042 | 0.342 | 1.12 |
| two_step | 0.381 | 0.036 | 0.310 | 0.97 |
| production | 0.301 | 0.003 | 0.295 | 1.76 |

Two-step minus fixed, skeleton-clustered:

| Tier, QC rule | Correct | Utility |
|---|---:|---:|
| A, `continue` | -0.259 [-0.360, -0.161] | -0.217 [-0.354, -0.077] |
| A, `stop` | -0.250 | -0.208 |
| B, `continue` | -0.100 [-0.144, -0.056] | -0.055 [-0.114, +0.004] |

Two-step minus one-step stays null (A: correct +0.003 [-0.006, +0.012]).

The sensitivity to the choice of unit (compound, Bemis-Murcko scaffold, plate cohort) changes no
conclusion. The tier-A plate cohort has only 2 clusters and cannot support an interval.

## 5. Phase 3: one pre-registered revision (`PROTOCOL.md`, `protocol.json`, `freeze.json`)

The revision is `two_step_fallback`. It applies when the base planner would defer, or stop after
a neutral or QC-failed result, and the cause is uninformed: no references, no paired references,
or thin support. In that case it takes the fixed early-to-late sequence's next legal action. It
still stops, with the named reason, when the references it has forecast no gain or a wrong risk
above break-even.

The protocol was frozen at 22:23:12 +0800, before any L1000 validator reading, forecast or
decision, and before the revision had run anywhere. The freeze covers:
- the rule;
- the thresholds;
- the baselines;
- the endpoints;
- the clustering unit;
- the decision criteria;
- the prepared L1000 data.

SciPlex3, exploratory (diagnosis-informed, so no weight in the verdict):

| Tier | Fallback minus two-step: utility | Fallback minus two-step: wrong | Fallback minus fixed: utility |
|---|---:|---:|---:|
| A | +0.057 [+0.006, +0.107] | +0.009 [0.000, +0.024] | -0.161 [-0.286, -0.045] |
| B | +0.050 [+0.025, +0.074] | +0.011 [+0.005, +0.018] | -0.005 [-0.049, +0.041] |

Even on its own design data, the revision closes only about a quarter of the tier-A gap. Most
tier-A deferrals are informed (55 of 59 are "no gain"), and the fallback respects them.

## 6. Phase 4: independent validation on L1000 (`lincs_prepare.py`, `lincs_evaluate.py`, `lincs_analyze.py`)

### Feasibility audit

Every requirement was checked from metadata before the freeze.

| Requirement | Finding |
|---|---|
| Exact compound identity | Broad `pert_id` and InChIKey; perturbagens absent from `pert_info` are excluded. |
| Matched line and dose, both times | 4,133 compounds were measured at 10 uM at both 6 h and 24 h in A549, MCF7, PC3 and VCAP. The follow-up capped its sample at 1,200. |
| QC | At least two wells on two plates, finite values, and a matched official signature with at least two replicates. 45,095 of 45,174 conditions pass. |
| Detection | Broad's `distil_cc_q75` against a DMSO null at the same line and time, using the SciPlex3 rule max(0.10, q99). Thresholds are 0.48 to 0.69. The detected fraction is 1.7% to 9.0% per line and time (A549: 328 at 6 h and 379 at 24 h, of 4,338). |
| Mechanism labels | Exact Repurposing Hub joins with a single mechanism: 1,629 of 7,259 compounds (22%); 226 have several mechanisms. These are external annotations, not measured engagement. |
| Independent references per class | Pool rule: at least 6 identity groups measured at every tier condition, of which at least 2 are detected somewhere. Tier LT: 21 classes, 344 held-out compounds, 6,880 episodes. Tier T: 15 classes, 218 compounds, 3,052 episodes. |
| Leakage-resistant splits | 5 folds of connected components sharing an InChIKey block or a Bemis-Murcko scaffold (335 components). |
| Plate dependence | A class's largest single-batch share is 0.17 to 0.57; 1,059 conditions pool several batches. |
| Cache provenance | The six GEO metadata files match their published SHA-512 sums. The cache's condition-mean norm tracks Broad's official signature strength with Spearman 0.595. The cache cannot be re-derived locally. |
| Gate: the validator can eliminate in at least 3 of 5 folds | Passed 5 of 5 folds in both tiers. |

### Results

Tier LT is the primary tier: A549, MCF7, PC3 and VCAP × 6 h and 24 h, with the fixed sequence
A549 6 h then 24 h. Intervals cluster on the held-out compound's fold component.

| Arm | Correct | Wrong | Utility | Deferred | Measurements |
|---|---:|---:|---:|---:|---:|
| da_unconditioned | 0.121 | 0.004 | 0.112 | 0.348 | 0.97 |
| two_step_fallback | 0.118 | 0.005 | 0.109 | 0.320 | 0.97 |
| two_step | 0.117 | 0.005 | 0.107 | 0.348 | 0.88 |
| da | 0.116 | 0.004 | 0.107 | 0.348 | 0.88 |
| fixed | 0.106 | 0.006 | 0.095 | 0.000 | 1.93 |
| production | 0.070 | 0.004 | 0.063 | 0.000 | 1.93 |
| two_step_permuted | 0.033 | 0.002 | 0.030 | 0.421 | 0.68 |

| Contrast | LT utility | LT wrong | T utility |
|---|---:|---:|---:|
| **Fallback minus two-step** (primary) | **+0.0013 [+0.0002, +0.0026]** | +0.0001 [0.0000, +0.0005] | +0.0007 [-0.0032, +0.0043] |
| **Fallback minus fixed** (primary) | +0.014 [-0.012, +0.041] | -0.001 [-0.005, +0.003] | -0.020 [-0.043, -0.001] |
| Two-step minus fixed | +0.012 [-0.013, +0.039] | -0.001 | -0.021 [-0.044, -0.001] |
| Two-step minus permuted-label planner | +0.077 [+0.053, +0.106] | +0.003 | +0.136 [+0.096, +0.185] |

The fallback fired 581 times in LT and 194 times in T. In LT it added 11 correct decisions, 1 wrong
decision, 0.084 measurements and 0.48 assay-days per episode.

**Why it barely matters here.** L1000 has more references per class, so after a neutral first
reading the planner's stops are informed:

| Tier | Neutral-first stops | Of which |
|---|---:|---|
| LT | 2,239 | 1,827 "no gain"; 64 wrong risk; only 348 uninformed |
| T | 1,664 | 1,042 because the first measurement was 24 h, when 6 h is no longer legal |

In T, the fixed sequence's lead (+0.030 correct) comes from measuring 6 h first, which resolves
some compounds that are neutral at 24 h, and from always continuing.

**Other findings**
- **Calibration** of step-1 truth-branch forecasts: ECE 0.034 in LT and 0.071 in T. At support 2 to
  4 the forecasts over-predict (0.137 forecast against 0.064 realised).
- **Support strata.** No stratum reverses the primary contrast. At support of 3 or fewer (LT), the
  planners decide 0.16 correct against 0.04 for the fixed sequence.
- **Plate diagnostic.** Among eliminating readings, the nearest template of the winning class
  shares the held-out compound's batch in 0.44 of wrong eliminations, against a template base
  share of 0.31. For correct eliminations the figures are 0.15 against 0.08. Batch similarity
  therefore contributes to eliminations, wrong ones in particular: a validity limit of this
  validator on this cache.
- **Unit sensitivity.** Fallback minus two-step utility, LT:

  | Clustering unit | Interval or range |
  |---|---|
  | Identity group | [+0.0001, +0.0025] |
  | Batch cohort (48) | [0.0000, +0.0025] |
  | Leave one batch out | +0.0010 to +0.0016 |

### Decision

These are the frozen rules for tier LT with a wrong-elimination tolerance of 0.02:
- no REJECT condition holds;
- the PROMOTE conditions fail: the gain over the fixed sequence is not shown, and tier T is
  negative against the fixed sequence;
- the SHADOW conditions hold.

**The verdict is SHADOW:** keep the rule opt-in and logged, and do not make it a default. The
protocol set no minimum effect size, so the verdict certifies only a non-negative, non-harmful
change. It is not a reason to adopt the rule.

## 7. What was fixed, what was only diagnosed, what remains unverified

**Fixed** (research harness; no `src/` change)
- Arms in the follow-up's comparison followed different QC-continuation rules.
- The fair runner now enforces identical sequence rules for every arm.
- `audit_record` catches any future asymmetry, and tests pin it.

**Diagnosed, not fixed**
- **SciPlex3's reference sparsity.** The stops are mostly correct refusals under thin data.
- **The time-order rule.** It makes a 24 h (or 72 h) first measurement terminal when only earlier
  actions remain. This is by design and applies to every arm.
- **Batch similarity** in the L1000 validator.

**Found after the L1000 run, not changed**
- After a fallback first measurement the plan has no continuation, and the frozen rule stops even
  when the audit finds a supported positive continuation. This happened in 32 of 6,880 LT
  episodes, labelled `implementation_defect`.
- A test pins this behaviour, so any change to it is deliberate and must be tested on new data.

**Unverified**
- Whether the cache's normalisation matches Broad's Level 4 or 5; no raw GCTX is local.
- Engagement behind any mechanism label.
- Any context beyond four lines at 10 uM, 6 h and 24 h.
- Any benefit from a learned transition, which is still not better than the training-target mean.

## 8. Tests

`test_sequence_audit.py` holds 21 tests, outside the repository suite.

| Area | Tests |
|---|---|
| Ported planner equals the original | synthetic cases, and every SciPlex3 contrast of two folds |
| Shared rules, enforced by the runner | identical legal menus across arms; time order also removes earlier actions; the QC rule belongs to the runner and charges the failed assay; illegal choices are refused; only real results change evidence |
| Record audit | five kinds of asymmetry are caught |
| Revised rule | fallback on missing paired references and on thin support, never after an informed stop; deferral fallback only when no reference informs; no invented branch after a QC failure; the post-run limitation above |
| Recorded runs | the SciPlex3 replay and all 79,456 L1000 records obey the shared rules; the L1000 QC encoding; a one-fold L1000 rerun reproduces its records exactly |

Results:

| Run | Passed |
|---|---:|
| `test_sequence_audit.py` | 21 |
| Related research tests (these 21 plus the follow-up, `dyn_model`, validator and acquisition-link tests) | 43 |
| Full repository suite (`maestro` env, Python 3.11.16) | 1,326 |

No paid API call was made; lab cost is 0.

## 9. Reproduction (conda `maestro`)

Run the commands in order.

```
python research/sequence_audit/diagnose.py
python research/sequence_audit/replay.py
python research/sequence_audit/analyze.py phase2_matched_replay
python research/sequence_audit/lincs_prepare.py
python research/sequence_audit/lincs_evaluate.py
python research/sequence_audit/replay.py --arms production,magnitude,da,da_unconditioned,fixed,one_step_utility,two_step,two_step_permuted,two_step_fallback --label phase3_sciplex3_exploratory
python research/sequence_audit/analyze.py phase3_sciplex3_exploratory
python research/sequence_audit/lincs_analyze.py
python -m pytest research/sequence_audit/test_sequence_audit.py
```

- `lincs_prepare.py` and `lincs_evaluate.py` run after the freeze. `lincs_evaluate.py` refuses to
  run if `PROTOCOL.md` or `protocol.json` differ from `freeze.json`.
- Outputs are under `outputs/sequence_audit_20260926/`; copies are in `log/20260926/0926/`.
