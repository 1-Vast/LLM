# Experiment record, 2026-09-27

> - **Path**: `log/20260927/README.md`
> - **Purpose**: Record four blocks. Block 1 (00:00-00:47) is the external-validation block: an audit of the evidence behind MAESTRO's decision claims, a firewall against outcome leakage (sealed policy view, one-time vault, manifests), a frozen 14-rung baseline ladder replayed on development data, masked and permuted virtual-cell controls, and a local candidate audit. Block 2 (03:00-05:40) is belief-space planning with a virtual-cell world model and its first external test: an audit of the repository after a Codex session, a new planner and world model, a new frozen protocol, and one locked run on GSE70138 (LINCS L1000 Phase II), downloaded under the owner's authorisation in the brief. Block 3 (11:30-13:30) is protocol external-validation-2: a code-level audit of eight review reports, an archive of both protocol-v1 experiments, clean-tree registration, fail-closed truth semantics with a whitelisted policy view, task headroom and power gates, a baseline-safe planner, cross-study calibration, virtual-cell and feedback decision gates, and a development screen. Block 4 (13:32-15:00) is an audit-and-plan pass over the owner's "MAESTRO v2" brief and its two-core addendum: a requirement matrix checked by executing the code, qualified historical claims, an execution-path wiring table, contribution cards for the agent, the world model and their combination, a deterministic replay of the engagement package, and a preregistration-ready experiment registry.
> - **Core points**: No local study is both unseen and compatible, so external validation is blocked; the candidate is L1000 Phase II (GSE70138), whose download needs the owner's approval. On development data (12,428 episodes, 360,412 records, no rule violations) the runtime selector with the virtual-cell channel (`maestro_vc`) was REJECTED under the frozen gates. It decided fewer correctly than the strongest simple baseline in SciPlex3 B (-0.054 [-0.095, -0.013]) and L1000 T (-0.031 [-0.050, -0.014]) and was inconclusive in SciPlex3 A and L1000 LT. It was cheaper in every tier (0.20 to 1.03 fewer measurements) and had fewer wrong eliminations except in SciPlex3 A. It sits on the same correct-versus-cost curve as a one-step expected-value rule. The virtual-cell channel had zero acquisition value in every tier (its one gain over masking was reproduced by another compound's predictions), and the selector's wrong-reading forecasts were 2 to 19 times too low. Production defaults and `src/` are unchanged. **Block 2:** on GSE70138 (38 new compounds, 380 episodes, run once behind the vault), the belief-planning agent was INCONCLUSIVE against the fixed expert order: -0.024 [-0.074, +0.011] correct decisions, with the pre-registered minimum improvement of +0.02 outside the interval. The virtual cell and real feedback changed actions but not decisions, and both contributions were REJECTED as practically meaningful. On development data the agent lost in SciPlex3 A (-0.134, REJECTED) and was inconclusive elsewhere (L1000 LT +0.024 [0.000, +0.050] with 0.57 fewer measurements). The audit found that a Codex session (00:59-02:56) had rewritten block 1's freeze and one replay fold, left an incoherent decision-value function, and changed a loader so that it emits truth-less episodes. Production defaults are unchanged; `src/` gained an opt-in planner and a coherence fix. **Block 3:** no MAESTRO policy meets the protocol-v2 success criteria, and the binding constraint is the task. The fixed order reaches 63-99.6% of the oracle's correct decisions, 76-82% of L1000 episodes cannot be decided from the menu, and a +0.02 effect needs 345-813 units against 38-256 available. The baseline-safe planner removes every development loss (SciPlex3 A -0.131 becomes 0.000) but departs from the fixed order in at most 0.24% of decisions, so it gains nothing. Wrong-risk forecasts are 2-5 times too low, and no recalibration transfers across studies. The virtual cell and feedback are not promoted. External-validation-1's freeze and one fold were rewritten; belief-planning-1's artefacts are intact. Production and `src/` are unchanged. **Block 4:** audit and plan only; nothing registered, promoted or committed. The historical numbers describe the transcriptomic MoA proxy task, not the agent's prerequisite-repair claim. On the engagement package (6 real cases) a selector given the same capability registry matched directed repair's decision and cost in every case the repair decided, so no additional algorithmic contribution was identified. The production repair path and the research belief planner are not connected. Protocol v2's legal menu moves with an outcome: 12 SciPlex3 conditions were profiled but dropped for low cell counts and are not offered. The fixed order reaches 63.3-99.4% of the oracle's correct decisions (block 3's "99.6%" does not reproduce). Go: boundary fixes, E-DATA1, E-CAL1 and the agent census; no-go: superiority tests, world-model promotion, external confirmation.

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

**Block 3 record control.**
- **Tree as found at 11:33.** `83b9aa9` on `main`, clean.
  - Every belief-planning-1 digest (54) matched the disk.
  - 78 of 79 regenerated external-validation-1 digests matched; `src/maestro/acquisition.py`
    did not.
  - This is the session-start witness in `research/experiments/*/EVIDENCE.json`.
- **The brief.** The owner pasted eight review reports into a Codex session (rollout `01a0dea8`,
  00:59-11:31) and had it draft this block's brief. That session wrote nothing to the tree.
- **Another session.** A Codex session started at 12:00 (rollout `01a0e105`) is building the
  owner's group-meeting slides in this repository. It created `inspect/` at 12:01 and
  `reference_0927/` at 12:25 in the repository root, and writes under `outputs/`. None of its files
  was touched.
- **Pre-registration.** `research/protocol_v2/protocol.json` (12:05:59) registers the
  development screen, the gates and the success criteria. The run record
  `outputs/protocol_v2_20260927/dev/run_record.json` (12:07:35, `development_unregistered`,
  dirty tree) holds its digest, the code and data digests, and the environment lock.
- **Archive.** `research/experiments/*/EVIDENCE.json` was written at 12:04.

**Block 4 record control.**
- **Tree as found at 13:32.** `e5ad68f` on `main`: the owner committed block 3 at 12:55.
- **Untracked, not ours.**
  - `inspect/` and `reference_0927/`: the Codex slides session, 12:00-13:49.
  - `research/prompt_review_20260927/`: a Codex session, 13:25-13:32, that revised the owner's prompt into this block's
    brief.
- **Another session.** A Codex session from 13:31 assessed novelty read-only.
- **Mode.** AUDIT_AND_PLAN, the brief's default. MINIMAL_IMPLEMENTATION was not selected.
- **Addendum.** The owner's addendum on two-core attribution arrived during the block; it changed no authorisation.
- **Scope of changes.** Nothing was registered, because the tree is dirty. Nothing was committed. No file under `src/`
  or `tests/`, no protocol and no registered record was changed.

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

**Block 3 questions** (the owner's brief, 11:30):
- **Q7.** Which claims of the eight review reports on `83b9aa9` hold when checked against the code,
  the manifests, the replays and a rerun?
- **Q8.** Can a clean, versioned protocol decide whether MAESTRO adds decision value over the
  fixed order?
- **Q9.** Does a baseline-safe planner remove the current planner's losses, and does it keep any
  gain?
- **Q10.** Are wrong-risk forecasts calibrated across studies?
- **Q11.** Do the virtual cell and feedback pass a decision-level gate?

**Block 4 questions** (the owner's brief and addendum):
- **Q12.** Which requirements of the brief hold on the executed code? (SATISFIED, PARTIAL, MISSING, CONTRADICTED or
  UNVERIFIED.)
- **Q13.** Do the six supplied historical claims reproduce, and what are their population, denominator, uncertainty and
  exposure?
- **Q14.** Is the execution path wired as the architecture describes?
- **Q15.** Does prerequisite-directed repair (AG) add decision value over same-information planning? Does the world
  model (WM) add information beyond simple predictors? Does their combination (JOINT)?
- **Q16.** Which experiments are ready to register, and which are blocked by what?

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

**Block 3 materials:**
- The registered belief-planning-1 records: 298,272 development and 9,120 external, read only.
- The external-validation-1 folds.
- The prepared SciPlex3 and L1000 development caches.
- The same environment: Python 3.11.16 (`maestro` conda env). Every installed distribution is
  locked in `0927/protocol_v2_dev_run_record.json`.
- No download, no provider call ($0), no laboratory work (0 wells).

**Block 4 materials:**
- The registered protocol-v2 analyses in `0927/protocol_v2_*`.
- The SciPlex3 raw release, read for `obs` metadata only.
- The prepared SciPlex3 and L1000 caches.
- GSE92742 and GSE70138 metadata (`external_phase2.manifest`, which reads no measurement).
- The engagement_v1 case package and capability registry, whose outcomes were already opened on 2026-09-14.
- Python 3.14 (`C:\Python314`) for probes and the replay.
- No download, no provider call ($0), no laboratory work (0 wells).

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

**Block 3 design** (`research/protocol_v2/PROTOCOL.md`, `protocol.json`):
- **Evidence audit.** Every report claim is checked in code or by a run; the evidence table is
  in DIAGNOSIS.md section 2.
- **Archive.** Both protocol-v1 experiments are digested once (`research/experiments/`). Each
  freeze is verified at `83b9aa9` with line-ending equivalence. Untracked originals are set
  read-only.
- **Contracts.**
  - A whitelisted public view replaces the sealed context for v2 arms.
  - Menus hold only planned conditions.
  - Five measurement states.
  - Truth is joined after execution, and scoring fails closed.
  - Pools come from reference compounds, with all-pairs truth-free contrasts for external use.
- **Gates.**
  - Task headroom >= 2 x MPIE with lower bound >= MPIE, plus a power gate.
  - A leave-one-study-out stop gate for model-driven stopping.
  - `KEEP` for the virtual cell or feedback only through the full chain: action, decision,
    correct, then no extra wrong or cost.
- **Development screen**, registered in `protocol.json` before it ran:
  - arms `fixed`, `random_legal`, `myopic_edv`, `belief`, `anchored`, `safe` (primary),
    `safe_class`, `belief_robust` and `oracle`, on the 20 registered development tasks;
  - one runner, menu, budget, executor, validator and seed policy for all of them.
  - Disclosure: every tier had been analysed before, and `safe` was designed after seeing
    belief-planning-1's results. The screen can rule arms out, not in.
- **Support rule for `safe`.** It uses existing constants only:
  - >= 6 independent reference units and history-weighted support per hypothesis;
  - >= 2 templates;
  - nearest-training Tanimoto >= 0.40;
  - a gain > 1.645 standard errors;
  - no increase in wrong risk.

**Block 4 design** (`research/gated_plan/`):
- **Audit, not experiment.** Every statement code can decide was decided by `research/gated_plan/probes.py`, a
  read-only probe script, or by a test.
- **One deterministic replay.** The engagement package's six offline arms were replayed:
  - fixed expert;
  - outcome-aware selection;
  - `maestro_core`;
  - `registry_repair_rule`;
  - `registry_expanded_selection`, the same-information control;
  - random proposal.

  The replay reproduces the 2026-09-14 attribution finding and supplies a real repair trajectory. It is not a
  registered or claim-bearing run.
- **New specifications, not run:** E-DATA1, E-CAL1, E-WM1, E-AG1, E-JOINT1 (2 x 2 agent by world model) and EXT-1,
  with the WM-G0-G4 and AG-G0-G3 gates.

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

**Block 3 results** (`research/protocol_v2/README.md`):
- **Headroom (oracle minus fixed, correct):**
  - SciPlex3 A +0.030 [0.000, 0.083] and L1000 T +0.001: both fail the gate.
  - SciPlex3 B +0.086 [0.053, 0.123] and L1000 LT +0.062 [0.037, 0.091]: eligible, but they need
    464 and 813 units (132 and 256 available).
  - GSE70138 +0.071 [0.003, 0.153] fails the lower-bound rule. It had 38 units and would need 345.
- **Identifiability.** No planned condition eliminates either hypothesis in 81.6% (LT), 75.9%
  (T), 28.6% (A) and 28.2% (B) of episodes. The fixed order reaches 63-99.6% of the oracle's
  correct decisions.
- **Development screen**: 12,428 episodes, 111,852 records, 0 integrity problems.
  - Replay check: the shared arms reproduced belief-planning-1's registered decisions exactly,
    apart from 12 mismatches on SciPlex3 A compounds with an unplanned condition.
  - `safe` minus fixed, correct: 0.000 in every tier (B [-0.002, +0.002]). It departs in 0-0.24%
    of decisions. Verdict: SAFE_ON_DEVELOPMENT, NO_DEVELOPMENT_SIGNAL.
  - `belief` minus fixed: A -0.131 [-0.214, -0.054]; B +0.008 [-0.018, +0.035]; LT +0.024
    [0.000, +0.050] with 0.57 fewer measurements and 20% of episodes deferred; T -0.006
    [-0.010, -0.002]. Verdict: UNSAFE on development (A, B).
  - `belief_robust` gave essentially the same results as `belief`. `anchored` matched fixed.
- **Second-step ceiling** after fixed's first non-terminal reading: 0.149 (B), 0.066 (LT),
  0.024 (A), 0.000 (T).
- **Calibration** (wrong eliminations, forecast against observed, leave-one-study-out):
  - L1000 0.0023 against 0.0045; SciPlex3 0.0114 against 0.0258; GSE70138 (post hoc) 0.0053
    against 0.0265.
  - Platt and hierarchical recalibration do not transfer. The hierarchical 95% bound covers 48%
    of SciPlex3 strata and 54% of GSE70138 strata.
  - The stop gate passes only on the planner's own bound, which is 10-35 times too high.
  - A contamination-mixture update (eps = 0.3) removes the 0.3-0.5% posterior collapse and
    changes almost no decision.
- **Virtual cell and feedback**, recomputed from the registered records: REJECT_AS_DEFAULT in
  every setting.
  - Virtual cell: action change 0-4.5%, decision change 0-0.6%.
  - Feedback: action change 3.3-32%, decision change 0.1-4.2%.
  - Every correct-difference upper bound is below +0.02.

**Block 4 results** (`research/gated_plan/README.md`, `AUDIT.md`):
- **Historical claims, recomputed:**
  - The fixed order reaches 63.3% (L1000 LT), 87.1% (SciPlex3 B), 95.6% (SciPlex3 A) and 99.4% (L1000 T) of the
    oracle's correct decisions, and 87.0% on GSE70138.
  - Unidentifiable episodes: 81.6% (LT) and 75.9% (T).
  - Units needed for +0.02 depend on the current planner's variance: 13 to 1,386.
  - GSE70138: 686 new compounds; 673 metadata-eligible in 613 units; 38 label-compatible.
  - Forecasts were 1.98x, 2.27x and 4.98x too low.
- **Leaks found by execution:**
  - 12 SciPlex3 conditions were profiled (6-18 cells per replicate) and dropped by the 20-cell rule. The protocol-v2
    menu does not offer them, so an outcome shapes the initial menu.
  - L1000 development pools count detected identities before the split.
  - Unregistered duplicate citations count as independent sources in production.
  - A lysate engagement grant satisfies an engagement premise that names no site.
  - SciPlex3 folds are identity-disjoint (0 of 180 skeletons cross folds) but not scaffold-disjoint (12 scaffolds,
    30 compounds).
- **Wiring:**
  - The production default selects on declared detection power and does not use virtual-cell output.
  - `plan_measurement` and `ReferenceWorld` run only as research arms.
  - Plan composition and licence certificates are not called by any runtime path.
  - No path uses a forecast to value a prerequisite measurement.
- **Engagement replay** (6 cases):
  - Registry access turns 4 menu-only deferrals into licensed decisions.
  - `registry_expanded_selection` matches `registry_repair_rule`'s decision and cost in all 4.
  - They differ on ABL1/dasatinib, a different licensed decision; the control's decision is the one the independent
    kinobeads test marks consistent.
  - On MCF7/AZD2014 the repair spends 2.0 against 0, and both defer.
  - Zero wrong development actions in any arm.
- **Gates:**

  | Gate | Status |
  |---|---|
  | AG-G0 | PASS for existence (6 cases); NOT_READY for population |
  | AG-G1 | PASS (implementation correctness) |
  | AG-G2 | INCONCLUSIVE: no additional algorithmic contribution identified |
  | WM-G0 | NOT_READY |
  | WM-G1, WM-G2 | FAIL |
  | WM-G3 | FAIL on development; INCONCLUSIVE on GSE70138 |
  | E-JOINT1 | NOT_READY: nothing connects forecasts to repair, and no task qualifies |

- **Tests:** `research/protocol_v2` 24 passed; five invariant files in `tests/` 123 passed;
  `tests/test_repository_shape.py` 9 passed.

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

**Block 3 deviations and corrections:**
- **Scoring accepted a missing truth.** `policies.finish` and `episodes.finish` scored a missing
  truth as a decision. Both now refuse by name. `episode_list` skips compounds whose label is
  missing or outside the pool; the historical path never produced such compounds. Before this,
  the external-validation SciPlex3 replay crashed at HEAD (`TypeError`, fold 1) on the Codex
  metadata path.
- **Two historical tests pointed at rewritten artefacts.** One compared a moving tree with a
  regenerated freeze; the other compared a rerun with the rewritten `l1000_T_1`. They now:
  - check the regenerated freeze at the archive commit against its archived record;
  - rerun the original `l1000_T_0`, where every registered arm's records are reproduced.
- **Line endings.** 58 CRLF and 12 mixed-ending tracked files meant protocol-v1 digests depended
  on the checkout. Registration now hashes LF-normalised content for tracked files.
- **Post-witness edits.** The two frozen mixed-ending files this block edited
  (`dynamic_world_model/common.py`, `episodes.py`) no longer re-derive their v1 digests from disk.
  Their tie to `83b9aa9` rests on the 11:33 witness (clean status, all digests matching), recorded
  in `EVIDENCE.json` and `archive.EDITED_AFTER_WITNESS`.
- **A wrong timestamp.** `protocol.json` carries `written_at` 12:10, but the file was written at
  12:05:59 and hashed by the run record at 12:07:35. The field was an estimate. It is left
  unchanged, so the recorded digest still matches.
- **Code edited after the development screen.** Alias removals in `common.py` and `firewall.py`,
  the removal of `truth_free_episode_list`, and new functions in `contracts.py` came after the
  run. A rerun of seven tasks with the final code reproduced the screen's decisions (section 8).
- **Concurrent actor.** The Codex slide session created `inspect/` in the repository root at
  12:01. Five production tests resolve the runner verb `inspect` as a path relative to the
  working directory, so they fail while that folder exists. Run from another working directory,
  they pass. The folder is the other session's and was left in place. The path resolution in
  `src/virtual_cell/state_adapter.py` (`_argument_identity`) is a latent defect, reported, not
  changed here.
- **Removed after a reference search.** Four aliases of `metadata_episode_menu`,
  `build_metadata_tiers`, the `policy_input` and `policy_view` aliases, and
  `truth_free_episode_list`. None had a caller; all are recoverable from `83b9aa9`.

**Block 4 deviations and corrections:**
- **"99.6%" corrected.** Block 3 recorded the fixed order at "99.6%" of the oracle in L1000 T. The registered file gives
  99.4%. Block 3's documents are left as written; the correction is recorded here and in `research/gated_plan/AUDIT.md`
  section 2.
- **Block 3's measurement-state adoption was partly wrong.** Its item 7 treated a condition with no row as "not
  planned". Execution shows those 12 conditions were planned and measured, then dropped for too few cells. Protocol
  v1's handling (charged as a QC failure) was closer to correct. Recorded, not edited.
- **Replay invocation.** The first attempt lacked `PYTHONPATH`. The second passed a costing overlay that belongs to
  another package (`costing_entry_matches_no_action`). The recorded run omits the overlay.
- **Citations.** The contribution-card citations outside `research/protocol_v2/LITERATURE.md` were not re-resolved
  online; `VALIDATION.md` lists them.

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

**Block 3 interpretation.**
- **The binding constraint is the task.** Most L1000 episodes are undecidable from the menu. The
  fixed order already captures most identifiable decisions, and the tiers have a third to a fifth
  of the units a +0.02 effect needs.
- **The planner's losses are an estimation problem, and are fixable.** A support-gated safe
  planner removes them.
- **Its only gain is a cost trade.** The LT advantage comes from deferring on thin support.
- **Claim boundaries:**
  - no MAESTRO improvement over fixed is established;
  - development results rule arms out, never in;
  - GSE70138 is consumed;
  - the production default is unchanged, and `src/` is untouched.

**Block 4 interpretation.**
- **Scope of the historical numbers.** They bound planning on a proxy task: choosing transcriptomic conditions to
  separate annotated MoA classes. They say nothing about prerequisite-directed repair.
- **Agent.** Its demonstrated contribution is engineering: named prerequisites, typed admission, scope-limited
  updates. On the only real prerequisite task, its decision value belongs to the added capability (the action space),
  not to the repair operation.
- **World model.** It adds no decision-relevant information beyond its class-conditional simple layer on development
  data.
- **Combination.** Neither measured nor measurable yet.
- **Biology.** No statement here is a biological mechanism claim. `not_engaged` has no measured sensitivity, and the
  engagement exposure is not matched to the viability phenotype.

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

**Block 3 artifacts:**

| Artifact | Location |
|---|---|
| Protocol v2 code, protocol, tests, README, PROTOCOL, DIAGNOSIS, LITERATURE | `research/protocol_v2/` |
| Protocol-v1 evidence archive | `research/experiments/{external-validation-1,belief-planning-1}/EVIDENCE.json` |
| Screen traces, scored records, outcome tables, manifest, run record | `outputs/protocol_v2_20260927/dev/` |
| Headroom, calibration, attribution, screen analysis | `log/20260927/0927/protocol_v2_*.json` |
| Run record (environment lock) and screen manifest | `log/20260927/0927/protocol_v2_dev_run_record.json`, `protocol_v2_dev_manifest.json` |
| Run notes, test results | `log/20260927/0927/protocol_v2_run_notes.md` |

**Commands.** Listed in `research/protocol_v2/README.md`. Tests:
`python -m pytest research/protocol_v2 -q -p no:cacheprovider` (24 pass). Full-suite counts are
in `0927/protocol_v2_run_notes.md`.

**Block 4 artifacts:**
- `research/gated_plan/`: README, AUDIT, DATAFLOW, PLAN, REGISTRY, `registry.json`, VALIDATION and `probes.py`.
- `outputs/gated_plan_20260927/probes.json`, copied as `0927/gated_plan_probes.json`.
- `outputs/gated_plan_20260927/engagement_replay/`: run record and per-arm ledgers. The run record is copied as
  `0927/gated_plan_engagement_replay.json`.
- `0927/gated_plan_run_notes.md`.
- Reproduce with:
  - `python -m research.gated_plan.probes --out FILE`, with `PYTHONPATH` set to the repository and `src`;
  - the replay command in `research/gated_plan/VALIDATION.md` step 6.

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

**Block 3 open items:**
- **Confirmatory external study.** An unopened study with 345-813 label-compatible units, and a
  task that passes the headroom gate, is needed. The first step is a metadata-only unit count on
  LINCS 2020 Level 5 compounds absent from GSE92742 and GSE70138. It needs the owner's approval
  to download.
- **Registration.** Commit this block (the owner decides) and register the next experiment from
  a clean tree with `registry.register`. Tag `belief-planning-1` at `83b9aa9` if wanted.
- **Confirmation-step task.** Needs replicate-level readings, so that a repeated measurement is a
  new realisation.
- **Second-step ceiling.** SciPlex3 B's 0.149 is the one place feedback has measurable room.
  A discriminating second-step model is the parallel research arm to try there first.
- **Latent defect.** `src/virtual_cell/state_adapter.py` treats an existing path named like the
  runner verb as a file.

**Block 4 open items** (owner decisions first):
- **Commit.** Commit `research/gated_plan/` and decide on the other sessions' untracked folders
  (`inspect/`, `reference_0927/`, `research/prompt_review_20260927/`). Registration needs a clean tree.
- **Implementation.** Authorise MINIMAL_IMPLEMENTATION for P0-1 (design-based availability and lifecycle states),
  P0-2 (per-fold pools) and P0-3 (registered weighting), or not.
- **Downloads.** Approve, or refuse, a metadata-only census of CPJUMP1 and LINCS 2020. CPJUMP1 is the only candidate with
  measured pairing of genetic and chemical perturbations of the same genes in the same cells.
- **Next runnable steps.**
  - E-AG1 stage 0: a premise-only local census. With fewer than 30 target-gene clusters, biological AG validation
    stays NOT_READY.
  - E-DATA1 after P0.
  - E-CAL1: ready now, but register it first.

## 10. Curation provenance

Written by the Claude session that ran the block, from the frozen files, the replay manifest and
the report in `outputs/external_validation_20260927/`. The figures were checked against three
earlier independent runs, which they reproduce exactly.

Block 2 was written by the Claude session that ran it, from the frozen files, the vault log, the
registered manifests and the analysis summaries in `outputs/belief_planning_20260927/`.

Block 3 was written by the Claude session that ran it (11:30-13:30), from:
- `research/protocol_v2/`;
- the archived evidence;
- the outputs in `outputs/protocol_v2_20260927/`;
- the eight review reports, read from the owner's Codex attachments. Their claims were
  re-checked, not copied.

Block 4 was written by the Claude session that ran it (13:32-15:00), from:
- the executed probes and the engagement replay (`outputs/gated_plan_20260927/`);
- the registered protocol-v2 analyses;
- the code paths named in `research/gated_plan/AUDIT.md`.

The brief and its addendum were the owner's pasted prompts; their historical claims were re-checked, not copied.
