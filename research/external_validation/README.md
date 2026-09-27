# External-validation firewall, baseline ladder and decision-focused evaluation

**Date:** 2026-09-27, 00:00 to 00:47 (+0800). Code, protocol and tests are in this directory. The
run outputs are in `outputs/external_validation_20260927/`, and the day record is
`log/20260927/README.md`.

## 1. Answer

**MAESTRO's decision-making has not been shown to beat simple baselines.** Its measurement choice
did not beat the strongest simple baseline in any tier of the development data. No unseen study
compatible with MAESTRO exists locally, so external generalization is **blocked, not tested**.

- **Method.** All 17 executed arms were replayed on 12,428 development episodes (360,412 records
  including the price sweeps). Each arm was sealed from hidden outcomes and run under identical
  menus, budgets and QC rules. Protocol, thresholds and code were frozen beforehand.
- **Verdict on the primary candidate.** `maestro_vc` is the runtime opt-in selector with the
  virtual-cell channel. Under the frozen gates it is **REJECTED** overall:
  - **SciPlex3 B:** 0.054 fewer correct decisions than the fixed sequence [0.013, 0.095].
  - **L1000 T:** 0.031 fewer than measuring both time points [0.014, 0.050].
  - **SciPlex3 A and L1000 LT:** INCONCLUSIVE.
  - **Cheaper everywhere, safer in three tiers:** 0.20–1.03 fewer measurements per episode, and
    fewer wrong eliminations except in SciPlex3 A (+0.015, not significant).
  - **What it actually does:** moves along the same correct-versus-cost curve as the simpler
    value-based arms, buying fewer measurements. At matched cost it is not better.
- **The virtual cell's acquisition value is zero.**
  - Its channel changed 0–19% of choices.
  - Its only gain over masking (SciPlex3 B, +0.013 [+0.005, +0.022]) is reproduced by priorities
    taken from a different compound (+0.003 [−0.003, +0.010] against the permuted control). What
    helps is a condition-level preference, not compound-specific prediction.
  - For the magnitude tie-break, permuted priorities decided as well as real ones.
- **The runtime selector's wrong-risk forecasts are 2–19 times too low.**
  - It forecasts P(wrong reading) at 0.001–0.003, where 0.005–0.038 was observed. Its calibration
    slope is 0.11–0.26.
  - The sparse-value model is conservative on wrong readings and better ranked (slope 0.65–1.15).
  - Terminal wrong-risk stayed low for every arm, because the validator itself is conservative.

## 2. What was built

| File | Role |
|---|---|
| [`AUDIT.md`](AUDIT.md) | Phase 1: data roles, data-dependent components, leak points, claim status, reused components |
| [`PROTOCOL.md`](PROTOCOL.md), [`protocol.json`](protocol.json), `freeze.json` | Pre-registration (frozen 2026-09-27 00:27:22 +0800), with 56 file digests and the grouped policy, model, retrieval-library, prompt, calibration and baseline-selection digests |
| `firewall.py` | Sealed policy view, visible-evidence store, JSON-Schema check, boundary reports, a `Vault` that opens once under a verified freeze, and fitting steps that refuse once it has opened |
| `schemas/*.schema.json` | Dataset (no labels), split (with boundary reports) and episode (no truth) manifests |
| [`manifests/external_candidates.json`](manifests/external_candidates.json) | Every local candidate study, why none qualifies, and exact files for the one that would |
| `arms.py` | The 14-rung ladder plus `production_default` and `sparse_two_step`; two permuted virtual-cell controls |
| `locked_replay.py` | Runs every arm through `sequence_audit.policies.run_matched` on the sealed view and records the menus each arm was offered. It refuses without a verified freeze, and refuses `--role external_test` by name |
| `manifests.py`, `freeze.py` | Writes the manifests and the freeze |
| `statistics.py`, `promotion.py` | Registered inference and the hierarchical gates (frozen) |
| `risk_audit.py`, `calibration_audit.py`, `paired_ablation.py`, `report.py` | Descriptive reports: rates, curves, Pareto sets, stratified calibration, the virtual-cell ablation; `report.py` applies the gates |
| `baseline_selection.json` | The comparator frozen for an external study: `fixed` (a four-way tie across tiers, broken by pooled correct rate) |
| `test_external_validation.py` | 26 contract tests (section 7) |

The directory is a Python package (run with `python -m`). Its `statistics` module therefore never
shadows the standard library for `src/` modules that import it.

## 3. Results by tier (development data, internal replay)

Correct decision, wrong elimination and measurements are per episode. Intervals are 95%,
cluster-bootstrapped over the unit (SciPlex3 skeleton, L1000 component).

| Tier (episodes) | Oracle | Fixed | Strongest baseline | `maestro_vc` | `maestro_vc` − baseline, correct | wrong | measurements | Status |
|---|---|---|---|---|---|---|---|---|
| SciPlex3 A (336) | 0.670 | 0.640 / 0.057 / 1.63 | `ridge` 0.449 / 0.027 / 1.31 | 0.426 / 0.042 / 1.12 | −0.024 [−0.107, +0.057] | +0.015 [−0.012, +0.042] | −0.20 | INCONCLUSIVE |
| SciPlex3 B (2,160) | 0.668 | 0.582 / 0.049 / 1.52 | `fixed` | 0.528 / 0.031 / 1.17 | −0.054 [−0.095, −0.013] | −0.018 [−0.030, −0.007] | −0.35 | **REJECTED** |
| L1000 LT (6,880) | 0.168 | 0.106 / 0.006 / 1.93 | `info_gain` 0.126 / 0.009 / 1.90 | 0.117 / 0.004 / 0.88 | −0.010 [−0.019, −0.001] | −0.005 [−0.007, −0.003] | −1.02 | INCONCLUSIVE |
| L1000 T (3,052) | 0.231 | 0.230 / 0.011 / 1.85 | `cost_only` (the same as fixed here) | 0.199 / 0.005 / 0.82 | −0.031 [−0.050, −0.014] | −0.006 [−0.010, −0.001] | −1.03 | **REJECTED** |

- **The fixed sequence is not always the comparator.** In SciPlex3 A it had the most correct
  decisions of any arm (0.640), but its wrong rate (0.057) exceeds the frozen cap (0.05). The
  comparator there is `ridge`.
- **In L1000 T** the menu has two actions, so every arm that never stops measures both. Those arms
  reach 0.230 against the oracle's 0.231.
- **Robustness of the primary differences.** Compound, scaffold, identity and batch-cohort
  clusterings give the same signs and nearly the same intervals. SciPlex3 A's plate-cohort
  clustering has two cohorts and is not usable.

**Secondary candidates** (Bonferroni 98.75%):
- `production_default` (the shipped default, no world-model input) is REJECTED in three tiers. It
  decides 0.056–0.410 fewer correctly than the comparator.
- `maestro_masked` is REJECTED or INCONCLUSIVE.
- `sparse_two_step` (the sparse-value research candidate) is INCONCLUSIVE in every tier; its
  correct-rate difference is −0.052 to +0.003.

**Cost curves** ([figure](../../outputs/external_validation_20260927/figures/correct_cost.png)):
- `maestro_vc`, `myopic_edv`, `sparse_two_step`, `marginal_only` and `retrieval` lie on one curve
  of correct decisions against measurements. Moving the price from 0.2 to 0 slides them along it.
- In SciPlex3 A, even at price 0 the curve stops at 1.22 measurements and 0.464 correct, far below
  the fixed sequence (0.640 at 1.63). The planners' forecasts do not value the second (72 h)
  measurement that decides slow mechanisms.
- In L1000 LT the value-based arms dominate the fixed sequence: more correct decisions with half
  the measurements.

## 4. Virtual-cell ablation (paired, identical episodes)

| Pair | SciPlex3 A | SciPlex3 B | L1000 LT | L1000 T |
|---|---|---|---|---|
| `maestro_vc` vs masked: any-step switch; correct | 0.6%; +0.000 | 19.2%; +0.013 [+0.005, +0.022] | 0.3%; +0.001 | 0%; 0 |
| `maestro_vc` vs permuted: switch; correct | 0%; 0 | 10.0%; +0.003 [−0.003, +0.010] | 0.3%; +0.001 | 0%; 0 |
| `magnitude` vs `cost_only` (channel masked): switch; correct | 97.6%; +0.095 [−0.027, +0.220] | 100%; +0.386 [+0.311, +0.462] | 0%; 0 | 0%; 0 |
| `magnitude` vs permuted: switch; correct | 24.7%; +0.024 [0.000, +0.068] | 71.6%; −0.018 [−0.058, +0.021] | 0%; 0 | 0%; 0 |

- **G6 fails in every tier.** On L1000 the channel almost never acts, because the virtual cell
  answers only at 24 h and cost ranks ahead of priority.
- **Magnitude's large gain over `cost_only` in SciPlex3 B is not virtual-cell information.** With
  another compound's predictions (permuted) it is as large or larger.
- **Prediction metrics without decision value.**
  - The ridge profile beat the training-target mean on cosine in every tier (+0.063 to +0.089).
  - The virtual cell beat it in SciPlex3 B only (+0.052 [+0.020, +0.082]).
  - As an acquisition arm, ridge ranged from the strongest baseline under the cap (SciPlex3 A) to
    third from last (SciPlex3 B). Prediction accuracy did not predict decision value.

## 5. Risk and calibration (diagnostic)

- **Terminal wrong-risk stayed low for every arm.** `maestro_vc`: 0.004 to 0.042 per episode.
  Selective risk (wrong among decided) was 0.026 to 0.089. The only arms above the cap were the
  fixed sequence and `info_gain` in SciPlex3 A (0.057 each).
- **Chosen-action forecasts.** The runtime card forecaster that `maestro_vc` uses is optimistic on
  correct readings, with slopes of 0.11–0.26:

  | Tier | ECE | Intercept |
  |---|---:|---:|
  | SciPlex3 A | 0.223 | −0.84 |
  | SciPlex3 B | 0.124 | −0.30 |
  | L1000 LT | 0.055 | −0.53 |
  | L1000 T | 0.081 | −0.23 |

  It forecasts P(wrong) at 0.001–0.003 against an observed 0.005–0.038. The sparse-value model's
  slopes are 0.65–1.15; it over-forecasts wrong readings (0.036–0.059 against 0.004–0.036).
- **Ranking by confidence** (AURC, lower is better): the selector ranks its own decisions by risk
  worse than the sparse model in three tiers (0.114 against 0.044, 0.066 against 0.039, 0.037
  against 0.018), and better in L1000 T (0.017 against 0.042).
- **Batch drives the worst strata.** L1000 batches `CPC019` and `CPC014|RAD001` forecast 0.4–0.6
  correct readings and observed 0.00–0.04. That is the batch effect block 4 found, now visible in
  calibration.
- **Caveat.** Logistic calibration fits inside small, perfectly separated strata do not converge;
  their intercepts and slopes in `summary.json` are unreliable. The ECE and reliability bins are
  not affected.

## 6. Scientific status

| Status | Claims |
|---|---|
| **Demonstrated** (code and replay integrity) | Policies cannot read held-out results (sealed view, two tests). All arms were offered identical menus and rules (360,412 records, 0 violations). The replay is exactly reproducible. The earlier headline numbers reproduce under sealing. |
| **Internally supported** (development data only) | Value-based selection reaches the fixed sequence's correct rate on L1000 LT with half the measurements. The production default is the weakest non-trivial arm. The runtime selector's wrong-reading forecasts are far too low. The magnitude tie-break's gain comes from condition-level preference, not compound-specific prediction. |
| **Inconclusive** | `maestro_vc` against the strongest baseline in SciPlex3 A and L1000 LT. `sparse_two_step` and `maestro_masked` against the strongest baseline. |
| **Rejected** (frozen gates, development data) | `maestro_vc` as a better decision-maker than the strongest simple baseline in SciPlex3 B and L1000 T. The virtual cell's acquisition value (G6) in all tiers. |
| **Not yet tested** | The Jev arm (registered, reserved for an external study). Prospective confirmation (G7). |
| **Blocked by missing external data** | Any claim of generalization to an unseen study (G5). |

**Production defaults are unchanged.** The opt-in decision-sensitive selector and typed
`PolicyInput` boundary live in `src/maestro/`; no policy passed a promotion gate.

## 7. Tests

`python -m pytest research/external_validation -p no:cacheprovider` runs the external contract,
firewall, calibration, and replay checks; the current workspace completes the suite without
failures.

**Leakage and boundaries:**
- no compound or group crosses a fold;
- the external boundary refuses shared compounds, scaffolds and batches;
- internal plate crossing is reported, not hidden.

**Sealing:**
- the sealed view holds no held-out measurement or annotation;
- two studies that differ only in hidden results give identical views and first choices.

**Vault and fitting:**
- the vault opens once, only under a verified freeze;
- no fitting step runs after the vault opens, while components prepared before it keep predicting;
- calibration and reference tables use training rows only;
- retrieval neighbours come from the reference library.

**Rules:**
- the registered prompt contains no compound identifier;
- identical menus, budget and QC rule across arms;
- a failed assay is charged the same for every arm and re-offered the same menu.

**Virtual-cell channel:**
- the structure virtual cell reproduces the frozen magnitude rule;
- masking changes only the priority channel, and the explicit arms equal block 4's discrimination
  arm;
- the permuted channel keeps the schema but breaks alignment.

**Statistics and promotion:**
- the oracle bounds every arm and never errs;
- mutual information and calibration metrics are recovered on known cases;
- the promotion statuses follow the registered gates.

**Reproduction:**
- the freeze verifies and detects a change;
- a saved fold is reproduced exactly after canonicalising persisted diagnostic floats to 15 decimal
  places. Decisions, actions, outcomes and labels are compared without rounding.

## 8. Reproduction and data requirements

```powershell
$py = 'D:\anaconda\envs\maestro\python.exe'
& $py -m research.external_validation.manifests      # dataset and split manifests (hashes ~3 GB)
& $py -m research.external_validation.freeze         # only when re-registering; it rewrites freeze.json
& $py -m research.external_validation.locked_replay --workers 8
& $py -m research.external_validation.report
& $py -m pytest research/external_validation -p no:cacheprovider
# opt-in contract suite (the default pytest target remains tests/)
& $py -m maestro.research_tests
```

**Development data required:**
- `data/raw/sciplex3/`;
- `data/external/lincs_l1000_phase1/`;
- the prepared tables under `outputs/dynamic_world_model_20260926/prepared`,
  `outputs/biological_depth_20260926/prepared` and `outputs/sequence_audit_20260926/l1000/prepared`.

All of these are digested in `freeze.json`. The replay takes about 6 minutes on 8 workers, and the
report about 1 minute.

**For an external run:**
- **Files.** [`manifests/external_candidates.json`](manifests/external_candidates.json) lists the
  exact GSE70138 files: 5.0 GB of Level 5 signatures plus about 10 MB of metadata. It also lists
  the representation caveat. The development L1000 cache has no runner, so the development tiers
  must first be re-derived from GSE92742 Level 5 (20 GB) and re-frozen.
- **Permission.** The owner must approve the downloads.
- **Procedure.** Section 10 of the protocol gives the sequence: metadata-only manifests, exclusion
  of development compounds and scaffolds, `prepare`, a single vault opening, the Jev sample, and
  the gates as written.
