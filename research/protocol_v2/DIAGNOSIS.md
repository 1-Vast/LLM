# Integrated diagnosis: can MAESTRO show decision value over the fixed expert order?

**Date:** 2026-09-27, 11:30-13:30 (+0800). This is block 3 of `log/20260927/README.md`.

**Starting point:** `main` at `83b9aa9` (`Add belief-space planning and locked external
validation`). The working tree was clean at 11:33.

**Inputs:**
- Eight review reports the owner pasted into a Codex session between 09-26 17:00 and 09-27 11:26
  (Codex attachments; not in the repository).
- The owner's brief for this block.

Every claim below was re-checked by reading code or by running it. Numbers come from the files in
`outputs/protocol_v2_20260927/`, copied to `log/20260927/0927/`.

## 1. What was verified about the checkout

| Item | Finding | How verified |
|---|---|---|
| HEAD, branch, dirty state | `83b9aa9` on `main`. Clean at 11:33. | `git rev-parse`, `git status --porcelain` |
| Concurrent actors | Codex session 00:59-11:31 (the owner's review synthesis): no writes. A Codex session from 12:00 builds group-meeting slides in this repository. It created `inspect/` (an unpacked deck) at 12:01 and `reference_0927/` at 12:25, and writes under `outputs/`. It did not touch any file of this block. | `~/.codex/sessions/2026/09/27/*.jsonl` cwd and commands |
| Line endings | 58 tracked files are CRLF and 12 are mixed in the working tree; git stores LF. Protocol v1 freezes hashed raw working bytes. | `git ls-files --eol` |
| belief-planning-1 freeze | All 54 digests matched the disk at 11:33. It verifies at `83b9aa9` (34 exact, 3 line-ending equivalent, 16 untracked data on disk). The vault log recorded the same freeze digest when the vault opened. It was registered from a dirty tree (20 uncommitted paths). | `archive.py`; `research/experiments/belief-planning-1/EVIDENCE.json` |
| external-validation-1 freezes | The original (00:27) fails on 9 files a Codex session edited before any commit. The regenerated one (02:53) fails on `src/maestro/acquisition.py`. Neither verifies at any commit. | same, `external-validation-1/EVIDENCE.json` |
| Replay folds | 19 of 20 external-validation-1 folds are original (record counts and times match the registered run). `l1000_T_1` was rewritten (17,640 records against 17,052 registered). All 20 belief-planning-1 folds and its external records are original. | `archive.py` |
| Test state at HEAD | Production suite passed. Research suite: 2 failures, both historical, now fixed as described in section 5 item 2. | pytest, 11:35 |

## 2. Evidence table for the hypotheses in the brief

Status key: CONFIRMED, PARTLY (confirmed with a material qualification), REJECTED, OPEN.

| # | Claim | Source | Code path | Data dependency | Status | Confidence | Verification |
|---|---|---|---|---|---|---|---|
| 1 | The fixed strategy is strong and some tasks have very low oracle headroom | reports 1, 3, 8 | `headroom.py`; `external_validation/arms.py oracle_plan` | registered dev and external records | CONFIRMED | high | Oracle-minus-fixed correct: SciPlex3 A +0.030 [0.000, 0.083], L1000 T +0.001 [0.000, 0.003], SciPlex3 B +0.086 [0.053, 0.123], L1000 LT +0.062 [0.037, 0.091], GSE70138 +0.071 [0.003, 0.153]. The fixed order reaches 63% (LT), 87% (B), 96% (A) and 99.6% (T) of the oracle's correct decisions. A and T fail the task gate. |
| 2 | GSE70138 has about 38 independent units after filtering | reports 1, 3, 8 | `belief_planning/external_phase2.py open_study` | vault study summary | CONFIRMED | high | 673 metadata-eligible new compounds; 516 carry a single-MoA label; 38 (38 components) fall in the 11-class reference pool. Minimum detectable effect 0.060; 345 units needed for +0.02. |
| 3 | Pool and external evaluable subset are affected by held-out labels | reports 3, 8 | `common.tiers` (historical path), `lincs_prepare.main`, `episodes.episode_list`, `external_phase2.open_study` | labels, detection outcomes | CONFIRMED (evaluation contamination, not policy leakage) | high | Development pools count held-out labels. L1000 pools also use held-out detection outcomes, before folds are assigned. Eligibility requires the compound's own label to be in the pool. Every forced-choice contrast contains the truth. Externally the pool comes from reference compounds only (correct), but inclusion requires the test label to be in the pool (38 of 673). No policy receives a label: the seal and vault were checked, and the v2 public view is a whitelist. **New:** in the forced-choice design the true class is the only class common to all of a compound's contrasts. No arm stores state across episodes, so none exploits it, but v2 removes the leak (all-pairs contrasts). |
| 4 | The external test overlaps development in cell background and partly in scaffolds | report 8 | `external_phase2.manifest` audit | GSE70138 metadata | PARTLY | high | Lines MCF7, HT29, PC3 (MCF7 and PC3 are in the L1000 development tiers; HT29 is not). 152 of 673 test compounds share a Murcko scaffold with GSE92742, and 112 with the reference arm. Batches are disjoint, and there is no identity overlap. **Qualification:** the world model and validator were fitted on GSE70138's own known compounds. For the model the external test is therefore a new-compound, same-study test, not a study shift. |
| 5a | The planner treats refusal as a stop | report 4 | `src/maestro/planning.py plan_measurement` | none | CONFIRMED in code; rare in practice | high | An all-refused menu returns `stopped/world_model_refused`. In the registered belief-planning-1 replay no episode stopped that way. The world model backs off instead of refusing. Earlier planners stopped on refusal in 7-35% of episodes (belief-planning-1 DIAGNOSIS). |
| 5b | Stopping is valued inconsistently across planners | report 4 | `planning.py` (stop = 0), `acquisition.expected_terminal_decision_value` (`defer_loss` = 1) | none | CONFIRMED | high | The two conventions differ. Protocol v2 registers one utility (+1 / -2 / 0 with 0.02 per measurement) for scoring every arm. |
| 5c | The planner overvalues noisy actions (optimizer's curse) | reports 4, 5 | `plan_measurement` maximises point values; the SE enters only the anchor | registered records, v2 screen | CONFIRMED | medium-high | The unconstrained planner loses 0.131 in SciPlex3 A. Under the v2 support rule, the fixed action's value lacks support in 49% (A), 58% (B), 79% (LT) and 8% (T) of decisions. |
| 5d | The planner fails to condition on previous measurements | reports 4, 7 | `world.py _history_weights`, `arms.belief_state` | registered records | REJECTED for the current planner | high | The belief planner conditions on the real history. Withholding it changes 3-32% of sequences. The older card and sparse variants conditioned on a single step-1 category. |
| 6 | The world model predicts validator categories, not biology | reports 1, 2 | `world.py forecast` | none | CONFIRMED, qualified | high | It forecasts four reading labels plus QC failure. Arms that predict continuous profiles already exist and did worse (external: `ridge` 0.300, `retrieval` 0.411, fixed 0.476), so "continuous" alone is not the missing piece. |
| 7 | The virtual cell changes few actions, with no attributable terminal gain | reports 1, 6 | `attribution.vc_gate` | registered records | CONFIRMED | high | Action change 0-4.5%, decision change 0-0.6%. Real minus masked correct difference lies within [-0.009, +0.009] in every setting. Kernel k = 0 on L1000. Verdict REJECT_AS_DEFAULT everywhere. |
| 8 | Feedback changes second steps but not terminal correctness | reports 1, 7 | `attribution.feedback_gate` | registered records | CONFIRMED | high | Action change 3.3-32%, decision change 0.1-4.2%. Correct difference upper bounds 0.000-0.011, all below +0.02. **New:** the hidden-outcome ceiling after the fixed first measurement is 0.149 in SciPlex3 B and 0.066 in L1000 LT, so feedback has room the current model does not use. It is 0.024 in A and 0 in T. |
| 9 | Wrong-risk is under-calibrated on external and novel compounds | reports 1, 5 | `calibration.py` | registered records | CONFIRMED | high | Forecast against observed: L1000 0.0023 / 0.0045, SciPlex3 0.0114 / 0.0258, GSE70138 0.0053 / 0.0265 (5x). Recalibration fitted on the other study does not transfer: Platt on SciPlex3 forecasts 0.008. Hierarchical 95% bounds cover only 48% of SciPlex3 strata and 54% of GSE70138 strata. |
| 10 | Historical freeze and replay artefacts were rewritten after registration | reports 1, 3, 8 | `archive.py` | freezes, replays, vault log | CONFIRMED for external-validation-1; REJECTED for belief-planning-1 | high | See section 1. |
| 11 | Missing measurements silently become biological failures | reports 7, 8 | `episodes.execute` | SciPlex3 condition index | PARTLY | high | A not-measured condition becomes `quality_failed`, is charged and removes nothing. It is never read as undetected biology. 56 of 729 QC-false steps in the registered SciPlex3 replay (fixed 0, random 7, myopic 6, belief 1). The world model's QC-failure probability is the share of training compounds *not measured* at a condition, which conflates availability with assay quality. |
| 12 | Truth can be `None` in scored episodes | reports 1, 3, 8 | `external_validation/locked_replay.load` (metadata path) with `episodes.episode_list` | SciPlex3 labels | CONFIRMED on that path | high | The registered records hold no truth-less episode. At HEAD the external-validation SciPlex3 replay crashed (`TypeError`, fold 1) on unlabelled compounds. Scoring now fails closed by name. |
| 13 | The typed policy boundary is nominal | report 8 | `locked_replay.run_task` | none | CONFIRMED | high | `PolicyInput` is built at every step, but arms still receive the whole sealed context. |

## 3. Integrated diagnosis

**The decisive constraint is the task, not the planner.** In the four development tiers and the
external study the terminal decision is the registered validator's first elimination. The agent
chooses at most two measurements from a menu of 2-12 conditions. Three facts, all measured, bound
what any policy can gain:

1. **Identifiability.** No planned condition eliminates either hypothesis in:
   - 82% of L1000 LT episodes;
   - 76% of L1000 T episodes;
   - 28-29% of SciPlex3 episodes.

   Some condition would eliminate correctly in 17% (LT), 23% (T) and 61-62% (SciPlex3). No
   model, virtual cell or feedback channel can decide an unidentifiable episode (`screen.py`).
2. **The fixed order already captures most of what is identifiable:** 63-99.6% of the oracle's
   correct decisions.
3. **Independent units are too few** for the practical effect. The minimum detectable effect is:
   - 0.037 (B, 132 units) and 0.036 (LT, 256);
   - 0.115 (A, 42);
   - 0.060 (GSE70138, 38).

   Detecting +0.02 needs 464 (B), 813 (LT) or 345 (GSE70138-like) units.

**Model defects add to this, and they explain the losses, not the missing gains.**
- The unconstrained planner maximises point estimates from 2-40 references per class and
  condition, which rewards noise (SciPlex3 A -0.131).
- Its wrong-elimination forecasts are 2-5 times too low, and no recalibration fitted on one
  study transfers to another.
- The virtual-cell kernel is fitted to zero on L1000 and changes almost nothing elsewhere.
- Feedback conditioning changes second steps without finding the better ones: the second-step
  ceiling in B is 0.149, and the planner converts none of it.

**What a conservative planner does.** Requiring support before leaving the fixed order (the v2
`safe` arm) removes every development loss. It departs in at most 0.24% of decisions, so it
also removes every gain. In LT the only development gain, the current planner's +0.024
[0.000, +0.050] with 0.57 fewer measurements, comes from stopping early on thin support: 20% of
LT episodes are deferred at the first step. The support rule does not license those stops.

**Evaluation hygiene.** Protocol v1 had four integrity problems:
- freezes registered from dirty trees and hashed as raw bytes;
- one experiment's freeze and one replay fold rewritten after registration;
- task construction that reads held-out labels;
- a scoring path that could accept a missing truth.

None of them changed a registered belief-planning-1 result (section 1; the v2 replay reproduces
its decisions). They would have made a positive result uninterpretable.

## 4. Classification of every recommendation

Rollback, for every code change listed: revert the file to `83b9aa9`. Each change is
self-contained, and no production path imports protocol-v2 code. "Validation" names the test or
run that checks the change.

| # | Recommendation (reports) | Class | Code evidence | Rationale | Expected benefit | Bias risk | Validation |
|---|---|---|---|---|---|---|---|
| 1 | Refuse registration from a dirty tree; record commit, digests, environment, command, seed (1, 3, 8) | ADOPT | v1 freezes list 20-30 uncommitted paths | a registration must be reproducible from its record | auditable results | none | `registry.py`; `test_registration_refuses_a_dirty_tree_and_writes_once` |
| 2 | Keep historical evidence read-only; new protocol versions only (1, 3, 8) | ADOPT | section 1 | stops reinterpretation | fixed record of v1 | none | `archive.py`, `EVIDENCE.json`, `test_archived_evidence_is_unchanged` |
| 3 | Tag `belief-planning-1` in git (1) | DEFER | - | a tag is a repository-wide, possibly pushed, change; the owner decides | - | - | command in PROTOCOL.md section 6 |
| 4 | `truth is None` fails closed (1, 3, 8) | ADOPT | claim 12 | an unscorable episode must never be counted | integrity | none | `policies.require_truth`, `episodes.require_truth`, `contracts.score`; three tests |
| 5 | Separate truth-free execution from post-hoc scoring (3, 8) | ADOPT | `run_matched` needs the truth to finish | the policy path must not hold the truth | integrity | none | `runner.run_episode` returns traces with no truth; `run_dev` joins it afterwards |
| 6 | An explicit minimal public policy view instead of a blacklist seal (8) | ADOPT for v2 arms; MODIFY for v1 | claim 13 | a whitelist fails closed | an arm cannot read what it is not given | none | `contracts.PublicContext`; whitelist, invariance and `AttributeError` tests. v1 arms run unchanged on it. |
| 7 | Distinguish not measured, QC failed, undetected, ambiguous, eliminating (7, 8) | ADOPT | claim 11 | availability is design metadata; QC is an outcome | no charged pseudo-assays | changes decisions only on compounds with an unplanned condition (12 replay mismatches, all in SciPlex3 A) | `MeasurementState`; `NotMeasured`; runner menus; tests |
| 8 | Pool, contrasts, inclusion and menu from reference data before labels (3, 8) | ADOPT for external; MODIFY for development | claim 3 | removes evaluation contamination | an honest estimand | development pools stay historical (disclosed) for comparability | `reference_pool`, `truth_free_episodes`, `mechanism_endpoint`; test |
| 9 | Headroom gate H >= 2 x MPIE before using a task (1, 2, 3) | ADOPT, plus a power gate | claim 1 | a +0.02 claim is impossible below it | no uninterpretable benchmark | none | `headroom.py`; `test_headroom_gate` |
| 10 | Separate acquisition and mechanism endpoints (1, 8) | ADOPT | claim 2 | 38 of 673 is not "unseen compounds" | correct scope of claims | none | protocol.json `endpoints`; `mechanism_endpoint` |
| 11 | Sample sizes: 200 exploratory, 500 confirmatory, 800-1500 for +0.02 (1, 3, 8) | MODIFY | power model | derive from measured variance, not rules of thumb | right-sized study | none | confirmatory = max(500, units required): 813 (LT-like), 464 (B-like), 345 (P2LD-like) |
| 12 | Scaffold, study, batch and cell-line sensitivity (1, 3, 8) | ADOPT | - | generalisation claims need it | - | none | protocol.json success criteria; `screen.sensitivity` |
| 13 | SPIBB-style fallback to fixed on insufficient multi-factor support (2, 4) | ADOPT as a research arm | claim 5c | baseline-safe improvement on thin data | no development loss | the arm was designed after seeing v1 results (disclosed) | `safe.py`; stub tests; development screen: SAFE, no signal |
| 14 | Ensemble or worst-case (DRO) value, LCB utility (1, 2) | DEFER | - | needs a calibrated uncertainty radius, which item 16 shows does not transfer | - | a free radius is a tuning knob | revisit when a study-level calibration passes |
| 15 | Risk decomposition with study-shift and novelty penalties (1, 5) | MODIFY | claim 9 | implemented as a power-prior-discounted hierarchical bound, then measured | - | penalties fitted on the target would leak | `calibration.py`: fails coverage on SciPlex3 and GSE70138, so not used for control |
| 16 | Hierarchical, conformal and selective calibration (5) | MODIFY | claim 9 | hierarchical and discounted bounds measured leave-one-study-out; conformal deferred (exchangeability fails across studies) | known coverage | none | `calibration.py`; `test_hierarchical_calibration_shrinks_thin_strata_to_the_parent` |
| 17 | The world model must not drive stops while under-calibrated (5, brief) | ADOPT as a gate | claim 9 | stops rest on the model's values | safety | the gate passes only on the planner's own bound, which is 10-35 times too high; disclosed | `calibration.stop_gate`: allow = true; no supported stop occurred in the screen |
| 18 | Bounded-likelihood or contamination-mixture belief updates (1, brief) | ADOPT as a research arm | collapse 0.3-0.5% | prevents collapse on a misspecified likelihood | small log-loss gain | eps chosen on development | `belief_robust`: log loss 0.640 to 0.636 (L1000) and 0.761 to 0.735 (SciPlex3); collapse to 0%; decisions essentially unchanged |
| 19 | A three-step task with a confirmation action (1, 2, 3, 7) | DEFER (blocked) | runner ends at the first elimination; one realisation per condition | a confirmation of the same condition returns the same reading in replay | - | - | needs a new task definition and replicate-level data (PROTOCOL.md section 8) |
| 20 | Continuous or discriminating world model; direct decision-value estimation (1, 2, brief H) | DEFER | claim 6 | continuous-profile (`ridge`, `retrieval`) and direct decision-value (`myopic_edv`, `sparse_two_step`) arms exist and lost | - | building on a task without headroom cannot show value | a parallel arm is specified for the first task that passes the headroom gate; the endpoint is terminal utility |
| 21 | Split the virtual cell into tie-break, posterior and value interfaces with KL logging (6) | DEFER | claim 7 | the virtual cell fails before any interface matters: no decision change to attribute | - | - | revisit if a task shows decision change |
| 22 | Virtual-cell gate: real, masked, permuted, scaffold-held-out, applicability (2, 3, 6, brief F) | ADOPT | claim 7 | action, then decision, then correct, then risk and cost | stops promotion on switch rates | none | `attribution.vc_gate`; `test_attribution_verdicts` |
| 23 | Study-held-out virtual cell (brief F) | DEFER (blocked) | `phase1_line_task_feasibility`: 96 episodes | too few units | - | - | needs a study pair with >= 200 shared-task units |
| 24 | Feedback: real, withheld, permuted, first-measurement matched, horizons (3, 7, brief G) | ADOPT | claim 8 | as brief G | - | the matched subset is post-treatment (labelled descriptive) | `attribution.feedback_gate`; `screen.second_step_headroom` |
| 25 | Stochastic logging and doubly robust off-policy evaluation (7) | REJECT for replay data; DEFER for wet-lab data | complete condition tables | exact counterfactual replay is unbiased and cheaper | - | - | LITERATURE.md section 5 |
| 26 | Feedback delay (timestamps) (7) | DEFER | replay has no result latency | nothing to measure | - | - | only meaningful with live assays |
| 27 | Mutual-information diagnostics (1) | MODIFY | - | replaced by the exact decision-relevant bounds: identifiability and second-step headroom | clearer ceiling | none | `screen.identifiability`, `second_step_headroom` |
| 28 | Decision-level replay integrity with numeric tolerance (8) | ADOPT | v1 byte-equality tests were circular | decisions exact, numbers within 1e-8 | real determinism check | none | `registry.compare_decisions`; `test_v2_runner_reproduces_registered_decisions`; the screen replay check |
| 29 | Threshold-sensitivity perturbation of validator scores (8) | DEFER | - | v2 traces now store validator scores and templates, so it can be run later | - | - | - |
| 30 | Pytest and research tests in explicit CI (1) | DEFER | no CI configuration in the repository | the owner decides where CI runs | - | - | `maestro-test-research` exists |
| 31 | Log provider, model, prompt, seed, temperature, cost and result hash for API calls (3, brief) | ADOPT as a rule | - | - | - | - | no API call was needed in this block ($0) |
| 32 | Keep the production default unchanged (all) | ADOPT | `src/` untouched | - | - | - | no protocol-v2 import in `src/` (`git diff --stat src` empty) |
| 33 | Replace planner, validator, virtual cell or feedback wholesale | REJECT | section 3 | the ceiling is the task, not the architecture | - | - | - |
| 34 | Unify STOP and DEFER utilities; one price for every arm (4, 8) | ADOPT for evaluation; MODIFY for code | claim 5b | score every arm with one registered utility; the v1 acquisition function keeps its own convention (not used by v2) | comparable net utility | none | protocol.json `utility`; screen arm table |
| 35 | Stop tuning on GSE70138; treat it as consumed (1, 3, 5) | ADOPT | vault log | - | - | - | protocol.json `external_confirmation` |

## 5. Code changes in this block

1. **Fail-closed scoring.**
   - `sequence_audit/policies.py`: `require_truth` in `finish`.
   - `dynamic_world_model/episodes.py`: `require_truth` in `finish`; `episode_list` skips compounds
     whose label is missing or outside the pool. Such compounds cannot form a forced choice, and
     the historical path never produced them.
2. **Two historical tests** in `external_validation/test_external_validation.py` now test real
   evidence:
   - the regenerated freeze is checked at the archive commit against its archived record;
   - the replay test reruns the original `l1000_T_0` fold, not the rewritten `l1000_T_1`, for the
     arms the original run registered.
3. **`belief_planning/arms.py`.**
   - `belief_state` extracted from `belief_arm` so the v2 arms plan from the identical state. The
     v2 replay reproduces the registered decisions.
   - Optional `contamination` for the belief update; the default of 0 is unchanged.
4. **New package `research/protocol_v2/`:**
   - `contracts`, `runner`, `registry`, `archive`, `safe`;
   - `headroom`, `calibration`, `attribution`, `screen`, `records`, `run_dev`;
   - `protocol.json`, tests and documents.
5. **Removed after reference search.** Each is unreferenced in code, tests, scripts, manifests and
   documentation (`git grep`), and none is historical evidence:
   - four aliases of `metadata_episode_menu` and `build_metadata_tiers` in
     `dynamic_world_model/common.py` (duplicates of one function; the single test caller now uses
     the canonical name);
   - `policy_input` and `policy_view` aliases in `external_validation/firewall.py`;
   - `truth_free_episode_list` in `episodes.py` (no caller, hard-wired to SciPlex3). It is
     superseded by `contracts.truth_free_episodes`, which reuses the tested
     `external_validation/ontology.py` builder.

   The removed code is recoverable from `83b9aa9`.
6. **Archived, not moved.**
   - Protocol-v1 artefacts are digested in `research/experiments/*/EVIDENCE.json`.
   - The 49 untracked originals under `outputs/` are set read-only.

## 6. Status of conclusions

**Established** (measured, integrity checked):
- The fixed expert order captures 63-99.6% of the correct decisions any policy could reach in
  these tasks. SciPlex3 A and L1000 T cannot show a +0.02 gain by construction.
- 76-82% of L1000 episodes cannot be decided by any policy from the planned menu.
- Protocol v1's task construction reads held-out labels; the external evaluable subset is
  label-selected (38 of 673). No policy received a held-out label.
- The world model's wrong-elimination forecasts are 2-5 times too low. Neither ordinary nor
  hierarchical recalibration transfers across studies.
- The virtual cell and feedback change actions without changing terminal correctness.
- A support-gated baseline-safe planner is as good as fixed on development data.
- The v2 runner reproduces belief-planning-1's registered decisions exactly, except where it
  deliberately removed not-measured conditions.
- external-validation-1's freeze and one fold were rewritten; belief-planning-1's artefacts are
  intact.

**Inconclusive:**
- Whether any MAESTRO planner beats fixed on unseen compounds (GSE70138 -0.024 [-0.074, +0.011];
  minimum detectable effect 0.060).
- The current planner's L1000 LT gain (+0.024 [0.000, +0.050]; development, previously analysed,
  and earned by early stops the support rule does not license).

**Rejected:**
- "MAESTRO improves on the fixed baseline": no result meets any protocol-v2 success criterion.
- The current planner as a safe default: it is unsafe in SciPlex3 A (-0.131) and B on
  development.
- The virtual cell and feedback as decision-improving defaults.
- Cross-study recalibration as a control signal.

**Blocked by insufficient data:**
- A confirmatory external test: an unopened study with 345-813 label-compatible independent
  units and a task passing the headroom gate.
- A confirmation-step task, which needs replicate-level readings.
- A study-held-out virtual cell (96 episodes available).
- A cell-line-held-out policy test.
- Off-policy evaluation of wet-lab logging.
