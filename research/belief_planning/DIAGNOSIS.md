# Diagnosis: why MAESTRO's measurement choice did not beat simple policies

Audit of 2026-09-27, 03:00-04:30 (+0800). It starts from the working tree at `d011fcd` with
uncommitted work from two sessions:
- this one's `research/external_validation/` (00:00-00:47);
- a Codex session (00:59-02:56) that edited `src/maestro/`, `research/dynamic_world_model/` and
  `research/external_validation/`.

Every claim below was re-checked in code or by a rerun. Nothing earlier was taken on report.

## 1. What actually runs

| Question | Finding | Evidence |
|---|---|---|
| Which policies run through the agent? | Only `select_discriminating_action`, and only with the opt-in `discrimination_selection` flag. It is logged and never drives the round by default. Every other policy (fixed, myopic EDV, sparse two-step, retrieval, `decision_sensitive_edv`) is a research arm in `run_matched`. | `src/agent/orchestrator.py:1794`; `research/external_validation/arms.py` |
| Is the new decision-sensitive value function used in a real execution path? | No. `select_decision_sensitive_action` is called only by the research arm `decision_sensitive_edv`. That arm was added to the frozen ladder after the registered run, and ran only in a rewritten L1000 T fold 1. | `grep` of `src/`, `research/`; `outputs/external_validation_20260927/replay/l1000_T_1.jsonl.gz` (mtime 02:52:44) |
| Are typed policy inputs enforced there? | Nominally. The arm builds a `PolicyInput` with empty evidence and uses only its action list and budget. Its forecaster reads `ctx.ft` and the runner's `EvidenceState` directly, and every arm still receives the whole sealed context. The "enforcement" is a blacklist of key names. The seal (`firewall.seal`) is what actually keeps held-out outcomes out. | `research/external_validation/arms.py` `decision_sensitive_edv`; `src/maestro/policy.py` |
| Are forecasts conditioned on hypothesis, context, dose, time and history? | See the list below. | `research/acquisition_link/evaluate.py` `ReferenceCardForecaster`; `research/external_validation/arms.py` `_vc_priorities` |
| Are outcome probabilities and elimination rules combined coherently? | No, in `expected_terminal_decision_value`. It zeroed the removed hypothesis before scoring the decision, which counts the reading twice. A reading that eliminates one hypothesis therefore always had a wrong-decision probability of zero, even when 20% of the true class reads that way. **Fixed** (`src/maestro/acquisition.py`, test `tests/test_belief_planning.py::test_decision_value_keeps_the_wrong_elimination_risk_of_a_noisy_reading`). | code; test |
| Do episodes, pools, retrieval, calibration or baselines use held-out labels? | Retrieval, validator calibration and every reference table use training folds only. Task construction uses the held-out labels in three ways, listed below. | `research/dynamic_world_model/common.py` `tiers`; `research/sequence_audit/lincs_prepare.py`; `research/dynamic_world_model/episodes.py` `episode_list` |
| Do saved replays reproduce? | Not with the current code for SciPlex3. The Codex change to `locked_replay.load` (the metadata tier path) adds 18 (tier A) and 153 (tier B) fold-0 episodes whose truth is `None`. The historical `episodes.contexts` path reproduces every registered SciPlex3 manifest exactly (10 of 10 tasks). L1000 is unchanged. | rerun, this audit |
| Were frozen results kept immutable? | No. At 02:52-02:53 the Codex session made three changes, listed below. The registered replay outputs other than that fold, the summary and the report are untouched (mtimes 00:27-00:33). | file diffs and mtimes |
| Which claims rest on development data? | All of them. Every result before today used SciPlex3 and L1000 Phase I folds. No untouched study had been evaluated. | registered manifests |

Conditioning of the forecasts:
- **Hypothesis, line, dose, time:** yes, through per-hypothesis reference cards at each condition.
- **The compound:** no. The virtual cell entered only as a magnitude tie-break, applied after
  coverage, cost and set size.
- **History:** partly, through a single "step-1 category" in the dyn_ref and sparse variants.
- **Refusal:** the card forecaster refuses when fewer than k references support a condition.

Uses of held-out labels in task construction:
- Class pools are counted over all labelled compounds, held-out folds included.
- A compound is eligible only if its own label is in the pool.
- Every episode is a forced choice whose pair contains the held-out label.

None of these reaches a policy, but the task is defined with hidden labels. This is disclosed as
an evaluation design.

Changes to the frozen record at 02:52-02:53:
- `research/external_validation/freeze.json` was regenerated. It still reads "registered before
  the development ladder ran", after new arms, a new multiplicity plan and edits to six frozen
  files. The original digests are in `log/20260927/0927/external_validation_freeze.json`.
- One registered replay fold (`l1000_T_1`) was rewritten with the new arm: 17,640 records against
  17,052 registered.
- The test that checks a saved fold reproduces now compares a rerun with that rewritten file, so
  it is circular.

## 2. Causal chain from code to the observed failures

The 2026-09-27 registered ladder showed three failures:
- the agent path lost to the fixed order (SciPlex3 B -0.054, L1000 T -0.031);
- it was cheaper but not better;
- the virtual cell had zero acquisition value.

The chain behind them:

1. **Refusal read as zero value (implementation).** With too few references, the card
   forecaster refuses and `select_discriminating_action` returns "no admissible action". The
   planners stopped:
   - 7.4% of SciPlex3 B and 17.9% of A episodes ended deferred;
   - 34.8% of L1000 LT;
   - the fixed order never defers.
   Deferring on thin support throws away decisions the fixed order makes.
2. **Noisy per-class cards (model).** A hypothesis card rests on 2-40 references per condition.
   Maximising over 8-12 actions picks whichever card is noisiest in the favourable direction (the
   optimizer's curse). In the development replay today, a planner with fixed priors lost 13
   points of correct decisions to the fixed order in SciPlex3 A (0.506 vs 0.640).
3. **Readings treated as independent (model).** Without history conditioning, a second
   measurement is valued at its marginal rate. In SciPlex3 A, 10 uM at 24 h is correct 44% of
   the time unconditionally, but 16% after an undetected 1 uM reading at 24 h (training 22%). The
   planner therefore preferred dose escalation at one time point, which fails for the same
   compounds. The expert order spreads its two measurements over time.
4. **The virtual cell had no decision channel (model and implementation).** The structure-kNN
   prediction reached the choice only as a tie-break after coverage, cost and size. It could
   change almost nothing, and permuted predictions changed it just as much.
5. **Little room to improve (task design).** The terminal decision is the registered
   validator's first elimination; the agent only chooses what to measure and when to stop. The
   oracle (it reads hidden outcomes, at most two measurements) bounds what any policy could gain:

   | Tier | Oracle | Fixed | Best non-oracle, registered |
   |---|---|---|---|
   | SciPlex3 A | 0.670 | 0.640 | fixed |
   | SciPlex3 B | 0.668 | 0.582 | fixed |
   | L1000 LT | 0.168 | 0.106 | info_gain 0.126 |
   | L1000 T | 0.231 | 0.230 | fixed / cost_only |

   In A and T the pre-registered minimum improvement (0.02) is at or beyond the ceiling. There,
   a "better than fixed" claim is impossible by construction, not merely unshown.
6. **Few independent units (data).** 42 units (A), 132 (B), 256 (LT), 170 (T). A 0.02 effect is
   below the resolution of every tier except LT.

## 3. Classification

- **Implementation defects:**
  - refusal treated as zero value;
  - double-counted evidence in `expected_terminal_decision_value` (fixed);
  - nominal policy typing;
  - a metadata tier path that emits truth-less episodes;
  - rewritten frozen artifacts.
- **Model limitations:**
  - class cards too thin to rank 8-12 actions;
  - no joint (history-conditioned) model of readings;
  - no compound-specific channel for the virtual cell;
  - card wrong-elimination forecasts 2-19 times too low (2026-09-27).
- **Task-design limitations:**
  - the validator, not the agent, makes the terminal decision;
  - oracle headroom at or below the MPIE in two tiers;
  - forced-choice contrasts built with held-out labels.
- **Data limitations:**
  - 42-256 independent units;
  - L1000 detection rates of 3-20% at 24 h and 10 uM;
  - no compatible untouched study held locally (GSE70138 downloaded today).
- **Evaluation artifacts:**
  - cheaper planners compared at different measurement counts;
  - unmeasured conditions scored as QC failures;
  - last-bit floating-point differences across builds (Codex rounded the serialised
    diagnostics; decisions are exact).

## 4. What the chosen method addresses

`research.belief_planning.planner` plus `research/belief_planning/world.py`:

- **Refusal read as zero value (1):** the world model backs off in layers (hypothesis class to
  pooled condition) instead of refusing.
- **Noisy cards (2):** the shrinkage strength is fitted per fold by empirical Bayes on training
  references, not fixed.
- **Independent readings (3):** the planner is an exact two-step expectimax whose second-step
  forecasts are conditioned on the compound's real first reading.
- **No decision channel for the virtual cell (4):** it enters as a structural kernel inside the
  forecast, with an applicability domain. Its strength is fitted the same way, and it is set to
  zero when structure does not predict readings.
- **Incoherent decision value (the Codex function):** readings are scored by the posterior mass
  they remove.
- **Risk of chasing noise (2):** a secondary candidate is anchored to the expert order (safe
  policy improvement).

**Not addressed:**
- The task-design ceiling (5) and the unit counts (6) are properties of the data. They are
  reported, not engineered around.
- The external study is used to test whether the method generalises, not to widen the ceiling.
