# Experiment record, 2026-09-27

> - **Path**: `log/20260927/README.md`
> - **Purpose**: Record two blocks. Block 1 (00:00-00:47) is the external-validation block: an audit of the evidence behind MAESTRO's decision claims, a firewall against outcome leakage (sealed policy view, one-time vault, manifests), a frozen 14-rung baseline ladder replayed on development data, masked and permuted virtual-cell controls, and a local candidate audit. Block 2 (03:00-05:40) is belief-space planning with a virtual-cell world model and its first external test: an audit of the repository after a Codex session, a new planner and world model, a new frozen protocol, and one locked run on GSE70138 (LINCS L1000 Phase II), downloaded under the owner's authorisation in the brief.
> - **Core points**: No local study is both unseen and compatible, so external validation is blocked; the candidate is L1000 Phase II (GSE70138), whose download needs the owner's approval. On development data (12,428 episodes, 360,412 records, no rule violations) the runtime selector with the virtual-cell channel (`maestro_vc`) was REJECTED under the frozen gates. It decided fewer correctly than the strongest simple baseline in SciPlex3 B (-0.054 [-0.095, -0.013]) and L1000 T (-0.031 [-0.050, -0.014]) and was inconclusive in SciPlex3 A and L1000 LT. It was cheaper in every tier (0.20 to 1.03 fewer measurements) and had fewer wrong eliminations except in SciPlex3 A. It sits on the same correct-versus-cost curve as a one-step expected-value rule. The virtual-cell channel had zero acquisition value in every tier (its one gain over masking was reproduced by another compound's predictions), and the selector's wrong-reading forecasts were 2 to 19 times too low. Production defaults and `src/` are unchanged. **Block 2:** on GSE70138 (38 new compounds, 380 episodes, run once behind the vault), the belief-planning agent was INCONCLUSIVE against the fixed expert order: -0.024 [-0.074, +0.011] correct decisions, with the pre-registered minimum improvement of +0.02 outside the interval. The virtual cell and real feedback changed actions but not decisions, and both contributions were REJECTED as practically meaningful. On development data the agent lost in SciPlex3 A (-0.134, REJECTED) and was inconclusive elsewhere (L1000 LT +0.024 [0.000, +0.050] with 0.57 fewer measurements). The audit found that a Codex session (00:59-02:56) had rewritten block 1's freeze and one replay fold, left an incoherent decision-value function, and changed a loader so that it emits truth-less episodes. Production defaults are unchanged; `src/` gained an opt-in planner and a coherence fix.

## 1. Record control

- **Tree as found.** Clean at `d011fcd`, where the owner committed the 2026-09-26 blocks and the
  Codex sparse-value work.
- **Other sessions.**
  - The Codex session that drafted this block's brief finished at 23:53 on 2026-09-26 and wrote
    nothing afterwards.
  - The one Codex session still active worked in `D:/SASG-ST`.
- **Pre-registration.** `research/external_validation/freeze.json` was written at
  2026-09-27 00:27:22 +0800. It records SHA-256 digests of 56 files: the protocol, the decision
  code, the policies and models, the prompt, the calibration inputs, the prepared data and the
  manifests.

| File | SHA-256 |
|---|---|
| `research/external_validation/protocol.json` | `84be2c60a894ee4cf4fd328135cb1404d95e27952a87d57d3ee3a94ae587a1c7` |
| `research/external_validation/PROTOCOL.md` | `4ec88d236c56ed4e4c53a9677d5379b9e721a3febeb66d01ced5a028d0be447a` |
| grouped `decision` digest (protocol, PROTOCOL.md, statistics, promotion) | `3803858175014d31b75451ed9b7ed181bf60dbca5deaba1aeb0360403836300f` |
| grouped `policy` digest | `fc4734687d01370eecaa5c611fc77ecf458554bc0a74d411f11c4251937c3f7b` |

The chronological notes, including the one failed smoke run, are in `log/20260927/0927/run-notes.md`.

**Block 2 record control.**
- **Tree as found at 03:00.** Still `d011fcd`, plus this session's uncommitted block 1, plus
  uncommitted edits by a Codex session: three turns between 00:59 and 02:56 (the last was
  interrupted), with sub-agents.
  - Codex edited `src/maestro/{acquisition,__init__}.py`, added
    `src/maestro/{policy,research_tests}.py` and `tests/test_decision_sensitive_acquisition.py`,
    edited `research/dynamic_world_model/{common,episodes}.py`, and translated the two Chinese
    READMEs.
  - It also edited block 1's frozen files (`protocol.json`, `PROTOCOL.md`, `statistics.py`,
    `arms.py`, `firewall.py`, `locked_replay.py`) and added `ontology.py`.
  - It regenerated `research/external_validation/freeze.json` at 02:53:48. The status text still
    says "registered before the development ladder ran".
  - It rewrote the registered fold `outputs/external_validation_20260927/replay/l1000_T_1.jsonl.gz`
    at 02:52:44: 17,640 records against 17,052 registered.
  - Block 1's original digests remain in `0927/external_validation_freeze.json`. None of the
    Codex work was reverted.
- **The brief** was drafted by another Codex thread at 02:57-02:59 and pasted by the owner. It
  authorises downloads and API calls.
- **Pre-registration.** `research/belief_planning/freeze.json` was written at 04:35:20 +0800 (copy:
  `0927/belief_planning_freeze.json`). It holds SHA-256 digests of 54 files: code, dependencies,
  protocol, the development caches, the GSE70138 metadata, the Level 5 gctx and the external
  manifest (`77b355659b8603afa5fa71a8931575987018c0715ed33c26190d6c0b8c390e1f`).

## 2. Research questions and hypotheses

**Q1.** On data it has not seen, does MAESTRO's measurement choice beat simple baselines on
terminal decisions, at equal or lower cost, within a wrong-elimination limit?
- **Primary candidate:** `maestro_vc`, the opt-in `select_discriminating_action` path with the
  structure-kNN virtual cell's priorities.
- **Primary comparator:** the strongest of ten baselines, chosen by a frozen rule.

**Q2.** Do the virtual cell's predictions change acquisition decisions for the better, compared
with masked and permuted controls?

**Q3.** Is any locally available study unseen and compatible enough to test Q1 externally?

**Block 2 questions** (the owner's brief):
- **Q4.** On unseen compounds, with a fixed wrong-decision cap and budget, does an agent that
  plans real measurements with a virtual-cell world model reach better terminal decisions than
  strong simpler policies?
- **Q5.** Does the virtual cell change actions beneficially? Test it against masked and permuted
  predictions.
- **Q6.** Does the agent use observed feedback beneficially? Test it against withheld and permuted
  feedback.

## 3. Materials, data and computational environment

**Development data** (both have shaped earlier designs, so every result here is internal):
- SciPlex3 tiers A (336 episodes) and B (2,160), Figshare 24681285;
- L1000 Phase I `subset48` tiers LT (6,880) and T (3,052), GSE92742.

**External candidates audited:**
- the Tahoe-100M subset `c39.h5ad`;
- sciPlex-GxE (GSM7056149);
- the other `subset48` lines;
- the non-transcriptome datasets.

**Environment:** `D:/anaconda/envs/maestro/python.exe` (Python 3.11.16), 8 workers with one BLAS
thread each. No provider call was made.

**Block 2 materials:**
- **External study.** GSE70138 (LINCS L1000 Phase II), GEO. The metadata and Level 5 gctx
  (5.37 GB compressed) were downloaded at 03:07-03:16 and SHA-512 verified.
- **GSE92742 Level 5** (21.3 GB, verified) was used only for the feasibility check of a strict
  cross-study design, which was not run.
- Provenance, licence and overlap audit: `research/belief_planning/DATA.md`.
- **External task P2LD.** MCF7/HT29/PC3 x 0.04/0.12/1.11/10 uM at 24 h, at most 2 measurements,
  16 assay-days.
  - Reference arm: 1,053 Phase II compounds known to development.
  - Test: 673 new compounds, with 0 identity overlap and no shared batch.
  - Opened in the vault: 38 test compounds in the 11-class pool, 380 episodes.
- **Development data:** the block 1 episodes (SciPlex3 A/B, L1000 LT/T), through the historical
  `episodes.contexts` path, which reproduces every registered manifest.
- **Environment:** the same `maestro` env for the registered runs (12 workers). The determinism
  check also ran in Python 3.14.4. No provider call was made; laboratory cost was 0 wells.

## 4. Experimental design and controls

**Arms.** Every executed arm runs through `sequence_audit.policies.run_matched` on a sealed view.
The view holds no held-out profile, QC field, detection flag or annotation. The executor reveals
only what an arm buys, and each record carries the menus the arm was offered.

| Rung | Arms |
|---|---|
| Floors and simple rules | defer floor, random legal action, fixed sequence, cost-only |
| Reference-based | marginal-only, measured-profile retrieval |
| Predictor-based | magnitude tie-break with the virtual cell (and a permuted control), structure-to-profile ridge |
| Value-based | information gain, myopic expected decision value (mandatory) |
| MAESTRO | masked, with the virtual cell, with the virtual cell permuted |
| Registered only | MAESTRO with the virtual cell and Jev (not executed, `provider_arm_reserved_for_external_study`) |
| Upper bound | outcome-aware oracle (reads hidden results; excluded from comparisons) |
| Reference arms | the shipped default, the sparse-value two-step planner |

The myopic and sparse-value arms were also run over the price grid 0 to 0.2.

**Gates (frozen).** The wrong-risk cap is 0.05 per episode. The non-inferiority margins are 0.005
(wrong-risk) and 0.01 (correct rate). The minimum practically important effect is 0.02 correct.
The cost margins are 0.10 measurements and 0.5 assay-days. The gates run in order:
- G1: integrity;
- G2: safety;
- G3: effectiveness;
- G4: benefit;
- G5: external replication;
- G6: virtual cell;
- G7: prospective confirmation.

**Status.** The status is the worst across the four tiers.

**Inference.** 2,000 paired cluster-bootstrap draws over the skeleton (SciPlex3) or component
(L1000), with compound, scaffold, plate-cohort, identity and batch-cohort sensitivity.

**Controls:**
- the zero arm (defer floor);
- random choice;
- permuted virtual-cell priorities for both virtual-cell arms;
- the oracle as a ceiling.

**Block 2 design** (`research/belief_planning/PROTOCOL.md`):
- **Primary candidate `belief`.** Exact expectimax over at most 2 measurements
  (`maestro.planning`), with the +1 / -2 / 0 utility and 0.02 per measurement.
  - The belief is formed from real readings only. An elimination is scored by the posterior mass
    it removes.
  - The world model is layered (pooled, class, virtual-cell structural kernel) and uses feedback
    conditioning. Its s, k and e are fitted per fold by leave-one-out likelihood on training
    references.
- **Secondary candidate `anchored`.** Leaves the fixed order only on 1.645 standard errors.
- **Controls:**
  - virtual cell masked and permuted;
  - feedback withheld and permuted (compatible real readings of another compound);
  - one-step lookahead.
- **Comparators:** the block 1 ladder (17 arms, oracle as a bound). The primary comparator is the
  fixed expert order.
- **Gates:**
  - G1: upper bound of the wrong rate at most 0.05;
  - G2: wrong difference at most +0.005;
  - G3: lower bound of the correct difference above 0, and estimate at least 0.02;
  - G4: measurement difference at most +0.10;
  - G5: virtual cell; G6: feedback.
- **Inference:** 2,000-draw unit-cluster bootstrap.

## 5. Experiment register and results

**Replay:**
- 20 tasks, 29 arm settings, 360,412 records;
- rule violations, menu mismatches and boundary crossings: 0;
- freeze verified;
- a saved fold reran exactly.

**Primary: `maestro_vc` minus the strongest baseline**

| Tier | Comparator | Correct | Wrong | Measurements | Status |
|---|---|---|---|---|---|
| SciPlex3 A | `ridge` (fixed exceeds the wrong-risk cap, 0.057) | −0.024 [−0.107, +0.057] | +0.015 [−0.012, +0.042] | −0.20 | INCONCLUSIVE |
| SciPlex3 B | `fixed` | −0.054 [−0.095, −0.013] | −0.018 [−0.030, −0.007] | −0.35 | REJECTED |
| L1000 LT | `info_gain` | −0.010 [−0.019, −0.001] | −0.005 [−0.007, −0.003] | −1.02 | INCONCLUSIVE |
| L1000 T | `cost_only` (identical to fixed) | −0.031 [−0.050, −0.014] | −0.006 [−0.010, −0.001] | −1.03 | REJECTED |

Overall status: **REJECTED**.

**Secondary candidates** (Bonferroni 98.75%):
- the shipped default: REJECTED in three tiers, INCONCLUSIVE in L1000 T;
- `maestro_masked`: REJECTED or INCONCLUSIVE;
- `sparse_two_step`: INCONCLUSIVE in all four tiers.

**Virtual-cell ablation:**
- **Compound-specific information adds nothing.** In SciPlex3 B, `maestro_vc` against masked
  switched 19.2% of episodes and gained +0.013 [+0.005, +0.022] correct decisions. Against its
  permuted control it gained only +0.003 [−0.003, +0.010], so the gain does not need the
  compound's own prediction. Magnitude against its permuted control: −0.018 [−0.058, +0.021].
- **On L1000 the channel almost never acts.** The virtual cell answers only at 24 h, and cost
  ranks ahead of priority.
- **G6 fails in all tiers.**

**Prediction diagnostics (secondary):**
- the ridge profile beat the training-target mean on cosine in every tier (+0.063 to +0.089);
- the virtual cell beat it only in SciPlex3 B (+0.052 [+0.020, +0.082]);
- neither translated into a decision gain.

**Calibration of chosen-action forecasts:**

| Model | Correct-reading forecasts | Wrong-reading forecasts |
|---|---|---|
| Card forecaster (`maestro_vc`) | ECE 0.055–0.223, slope 0.11–0.26 | 0.001–0.003, against 0.005–0.038 observed |
| Sparse-value model | ECE 0.040–0.140, slope 0.65–1.15 | conservative |

The worst strata are L1000 batches (forecast 0.4–0.6, observed 0.00–0.04).

**Candidate audit:**
- **Tahoe `c39` is incompatible:**
  - 182 single-mechanism joins, and only one class with six or more identities;
  - 981 of 1,135 conditions from a single well;
  - one line and one time;
  - State, the virtual cell, was trained on Tahoe.
- **sciPlex-GxE** is unassessed.
- **The other `subset48` lines** are not independent.
- **L1000 Phase II (GSE70138)** is compatible:
  - minimal files: 5.0 GB of Level 5 plus about 10 MB of metadata;
  - the development tiers must first be re-derived in the same representation, from GSE92742
    Level 5 (20 GB), because the `subset48` runner is missing.

**Block 2 results.**

- **Registered development replay** (04:35-04:56): 12,428 episodes, 298,272 records, 0 integrity
  problems. The ladder reproduces block 1's registered rates exactly.
- **External run** (vault opened 04:35:44; replay 04:38:53-04:40:39): 9,120 records, 0 problems.

| Setting | Fixed | belief | belief - fixed, correct | Status |
|---|---|---|---|---|
| SciPlex3 A | 0.640 | 0.506 | -0.134 [-0.217, -0.057] | REJECTED |
| SciPlex3 B | 0.582 | 0.590 | +0.008 [-0.018, +0.035] (wrong -0.010) | INCONCLUSIVE |
| L1000 LT | 0.106 | 0.131 | +0.024 [+0.000, +0.050] (0.57 fewer measurements) | INCONCLUSIVE |
| L1000 T | 0.230 | 0.224 | -0.006 [-0.010, -0.002] | INCONCLUSIVE |
| **GSE70138 (external)** | 0.476 | 0.453 | **-0.024 [-0.074, +0.011]** | **INCONCLUSIVE**; +0.02 excluded |

- **Oracle bounds:** 0.670 / 0.668 / 0.168 / 0.231 / 0.547.
- **Against myopic EDV, retrieval and marginal:** the agent was more often correct in every
  setting (lower bounds above 0), but with more measurements and more wrong decisions (G2/G4
  fail).
- **Anchored:** leaves the fixed order in 0-334 episodes per setting, with correct differences of
  0.000.
- **Virtual cell:**
  - It changes 0-5% of sequences, with overall differences of 0.000 or -0.002.
  - It abstains (k = 0) in every L1000 development fold.
  - Verdict: REJECTED as a meaningful contribution.
- **Feedback:**
  - Removing it changes 3-32% of sequences.
  - After an identical first measurement, real readings change the second choice in 0-14% of
    episodes.
  - Overall differences range from -0.012 to +0.003.
  - Verdict: REJECTED.
- **Calibration:** the world model's wrong-elimination forecasts are 1.2 to 5 times too low
  (external: 0.005 forecast, 0.027 observed); correct-elimination forecasts are close on L1000.
- **Determinism:**
  - SciPlex3 A fold 1 rerun: identical decisions in Python 3.11.16 and 3.14.4, with a maximum
    floating difference of 3.1e-15 (tolerance 1e-9).
  - The external replay, rerun from its opened-study pickle, is identical.
- **Detail:** `research/belief_planning/README.md`; slim summaries in
  `0927/belief_planning_*_summary.json`.

## 6. Deviations, failures and corrections

- **Smoke check failure.** The first smoke check failed on L1000 because `episodes.lab_cost`
  holds SciPlex3's day table. It was replaced with a well rule that applies to any dataset,
  before the freeze.
- **Package layout.** The brief names a `statistics.py` module; as a plain script folder it would
  shadow the standard library for two `src/` modules. The directory was made a package, run with
  `python -m`.
- **Report code written after the freeze.** The descriptive report code was written after the
  freeze and during the replay, before any result was read. The frozen `statistics.py` and
  `promotion.py` decide every status.
- **Unreliable calibration fits in small strata.** Logistic calibration fits do not converge in
  small, perfectly separated strata (Newton overflow warnings); those strata's intercepts and
  slopes are unreliable.
- **Compute seconds.** They depend on arm order, because arms share per-fold model caches. They are
  indicative only.
- **Noted after the freeze.** The frozen 0.05 wrong-risk cap equals the validator's registered
  maximum wrong-elimination rate per reading. Nothing was changed.
- **Full suite.** 1,325 passed, 1 failed. `test_project_markdown_has_no_chinese_prose` fails
  because commit `d011fcd` tracked two Chinese READMEs from another session
  (`research/acquisition_followup/README.md`, `research/sparse_value/README.md`). They were left
  unedited.

**Block 2 deviations and corrections:**

**Development iterations before the freeze.** All disclosed in `protocol.json`:
- v0, fixed priors, 03:18-03:33;
- v1, empirical-Bayes fit and unit-left-out readings, 03:45;
- v2, factorised world model, rejected, 03:59;
- v3, anchoring, 04:05;
- v4, all controls: its first start crashed because permuted feedback could insert an
  eliminating label. That was fixed to compatible readings, and the run was stopped at 04:20
  after partial results.

These runs are in `outputs/belief_planning_20260927/dev/`, and are development only.

**Stale files.** `outputs/belief_planning_20260927/l1000_level5/phase1_{summary,tier}.json` and
`phase1_*.csv` come from a superseded version of `l1000_level5.py`. The feasibility record that
counts is `phase1_line_task_feasibility.json`.

**Protocol disclosure corrected.** `protocol.json` states that the anchored agent reproduced the
fixed order on every SciPlex3 episode; that was true of the v3/v4 runs. The registered replay
shows 16 departures in SciPlex3 B, with a correct difference of 0.000. The frozen file is
unchanged, and this line corrects it.

**Codex function fixed.** `expected_terminal_decision_value` (Codex, uncommitted) zeroed the
removed hypothesis before scoring. It was fixed in place, as the brief asked, with a test.
Consequences:
- block 1's post-hoc freeze no longer verifies (`src/maestro/acquisition.py` changed);
- the rewritten saved-fold test differs only in the `decision_sensitive_edv` records (65 of 588,
  one terminal decision).

These are the 2 failures among 119 research tests. The production suite passes: 1,341 of 1,341.

**Not fixed, reported.** `external_validation.locked_replay.load` (Codex's metadata path) emits
SciPlex3 episodes whose truth is `None`: 18 in A fold 0 and 153 in B fold 0. Block 2 used the
historical path instead.

## 7. Interpretation and claim boundaries

**What the replay shows:**
- **Economy, not accuracy.** On data that shaped its design, MAESTRO's decision layer is
  economical and safe but not more accurate than simple baselines. It makes fewer measurements and
  fewer wrong eliminations, and gives up correct decisions in proportion.
- **The same trade-off as a one-step rule.** Its trade-off is the one a one-step expected-value
  rule makes, so no gain here can be attributed to agent reasoning.
- **No compound-specific virtual-cell contribution.** The only virtual-cell effect visible is a
  condition-level preference that a permuted prediction reproduces.
- **Unsafe as a risk gate.** The runtime forecaster under-states wrong readings, so it should not
  be used as a risk gate until it is recalibrated on development data and re-frozen.

**Claim boundaries:**
- Nothing here is external validation.
- Nothing here concerns mechanism, target engagement, safety or generalization to other contexts.

**Block 2 interpretation.**
- **No external superiority.** On the one untouched study there is no evidence that planning
  with the world model beats the expert order, and a practically meaningful gain is excluded. The
  agent does beat the non-agent model-based planners on correctness, by spending the measurements
  they refuse to spend.
- **Neither core earns its keep.** In this task family the virtual cell and the feedback loop
  both work mechanically (the world model and replanning are coherent and tested) but not
  decisively.
- **The limits are the task and the data**, more than any missing model:
  - oracle headroom of at most 0.09;
  - 38-256 units;
  - a validator, not the agent, makes the terminal decision.
- **Claim boundaries:**
  - one external study, 38 units, the forced-choice design;
  - no claim about mechanism, target engagement, safety or other contexts;
  - no policy promoted.

## 8. Reproduction and artifact ledger

| Artifact | Location |
|---|---|
| Code, protocol, freeze, audit, candidate audit, README | `research/external_validation/` |
| Records (gzip JSONL), manifests, diagnostics, summary, report, figures | `outputs/external_validation_20260927/` |
| Report copy | `log/20260927/0927/external_validation_report.md` |
| Gates summary | `log/20260927/0927/external_validation_gates.json` |
| Replay manifest | `log/20260927/0927/external_validation_replay_manifest.json` |
| Freeze | `log/20260927/0927/external_validation_freeze.json` |
| Baseline selection | `log/20260927/0927/external_validation_baseline_selection.json` |
| Cost figure | `log/20260927/0927/external_validation_correct_cost.png` |
| Run notes | `log/20260927/0927/run-notes.md` |

**Commands:** `python -m research.external_validation.locked_replay --workers 8`, then
`python -m research.external_validation.report`. The tests run with
`python -m pytest research/external_validation -p no:cacheprovider` (26 pass).

**Block 2 artifacts:**

| Artifact | Location |
|---|---|
| Code, protocol, freeze, diagnosis, data provenance, README | `research/belief_planning/` |
| Planner (opt-in, not a default) | `src/maestro/planning.py`; tests `tests/test_belief_planning.py` |
| External manifest (metadata only) | `research/belief_planning/manifests/gse70138_p2ld.json` |
| Registered records and analyses | `outputs/belief_planning_20260927/{registered,external}/` |
| Freeze, vault log, manifests, summaries, figure | `log/20260927/0927/belief_planning_*` |

**Commands.** In `research/belief_planning/README.md`:
- `python -m research.belief_planning.locked --dev`;
- `python -m research.belief_planning.analysis ...`;
- `python -m research.belief_planning.reproduce ...`.

The external replay refuses a second run.

## 9. Open items and next experiments

- **External study.** Download GSE70138 on the owner's approval. Then:
  - re-derive both releases at Level 5;
  - re-run and re-freeze the development ladder;
  - open the vault once.
- **Recalibration.** Recalibrate the card forecaster's wrong-reading probabilities on development
  folds and re-freeze, before any use of the selector's risk gate.
- **Cost curves.** Test whether the value-based curve can reach the SciPlex3 tier-A fixed
  sequence's correct rate. The second (72 h) measurement is under-valued.
- **Jev arm.** Run it on a pre-registered 200-episode sample of the external study.

**Block 2 open items:**
- **External study.** The GSE70138 item above is done (block 2).
- **Next confirmation.** It needs:
  - at least 200 independent new compounds: the LINCS 2020 Level 5 release, or Tahoe-100M after
    its schema and licence audit;
  - a pre-registered task whose oracle headroom exceeds twice the MPIE, for example a third
    measurement, or letting the agent decline an elimination and confirm it.
- **Recalibration.** Recalibrate wrong-elimination forecasts on a held-out study before any
  forecast-based risk control.
- **Codex loader.** Decide with the owner whether to keep the metadata tier path, given its
  truth-less episodes.
- **Commits.** Nothing is committed.

## 10. Curation provenance

Written by the Claude session that ran the block, from the frozen files, the replay manifest and
the report in `outputs/external_validation_20260927/`. The figures were checked against three
earlier independent runs, which they reproduce exactly.

Block 2 was written by the Claude session that ran it, from the frozen files, the vault log, the
registered manifests and the analysis summaries in `outputs/belief_planning_20260927/`.
