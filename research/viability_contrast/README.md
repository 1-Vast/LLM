# Viability contrast: a low-cost task with a real choice space for the dual core

**File summary**
- **Path:** `research/viability_contrast/README.md`
- **Purpose:** block 1 of the post-`dual_core_v2` phase. `dual_core_v2` section 14 named the
  binding problem: the registered transcriptomic tasks lack effective discriminative information
  (SciPlex3: a median of 3.5 independent units per class; L1000: 85% of executed readings
  undetected), so no model improvement can become a decision improvement there. This block
  builds and qualifies a task that the same report asked for: cheap, already-public inputs; a
  real experimental choice space; a credible decision endpoint; enough independent units.
- **Core points:**
  - The substrate is the PRISM Repurposing secondary viability screen (local since 2026-08-23):
    517 compounds x 443 cell lines of fitted curve AUC, 39 primary-MoA classes with >= 8
    InChIKey-connectivity units, 370 menu lines carrying DepMap CRISPR. The reading (curve AUC)
    exists for every measured pair: there is no detection failure mode.
  - Four frozen protocols form one arc. v1 (template-band elimination) FAILED its gate: the
    validator measured template coverage, not evidence. v2 (score-margin validator) measured
    the task's real property: clairvoyant line choice certifies 98.8% of episodes at 0.2%
    wrong with 2.3 measurements, while uninformative choice certifies nothing at any tau.
    v3 (class-template world planner) and v4 (profile-conditioned world planner) certify
    nothing either: the compound-level channel helps prediction (beta = 0.25 in 3/5 folds)
    but not enough for a 5%-certified decision on the registered grid.
  - The dual-core estimand is now purified: floor (0 certified), realistic dual core (0
    certified), oracle (98.8% certified). The missing middle is a compound-level predictive
    good enough to keep margins honest under planning — the registered target for the next
    block, together with a non-margin-optimising acquisition rule and a thicker extreme-tau
    calibration base.
  - v5 (section 3.6) ran exactly those registered answers: a learned low-rank completion
    world with a precision blend, MI and Thompson acquisition against the margin rule, an
    extended tau grid, and a gated CRISPR tier. None certifies: the frontier stays at
    55-81% wrong wherever >= 20 calibration episodes decide, under three world models and
    three acquisition rules. The bottleneck is no longer the world's point predictions;
    the next move is a reformulation, not a fourth world.
  - v5b (section 3.7), after an external review found a numerical defect in the v5
    world (verified before registration): the frontier conclusion survives the fix, but
    the oracle decomposition overturns the ceiling's interpretation — perfect response
    prediction without the label qualifies NOTHING (0.77-0.87 wrong), the label with
    only templates reaches 0.26-0.40 wrong, and only the conjunction certifies. The
    v1-v5 'oracle' measured answer-key-guided evidence selection; the world-model lever
    on this task-policy pair is measured dead.
- **Interfaces / data:** `protocol.json`, `protocol2.json`, `protocol3.json`, `protocol4.json`,
  `protocol5.json`, `protocol5b.json`, `prepare.py`, `prepare3.py`, `prepare5.py`,
  `qualify.py`, `qualify2.py`,
  `world3.py`, `run3.py`, `world4.py`, `run4.py`, `world5.py`, `run5.py`,
  `world5b.py`, `run5b.py`, `llm_arm.py`,
  `freeze.py`, `freeze{,2,3,4,5,5b}.json`;
  pack in `outputs/viability_contrast_20260928/prepared/`; results in
  `outputs/viability_contrast_20260928/{qualify,qualify2,run3,run4,run5,run5b,llm}/`
- **Depends on:** `research/dual_core_v2/` (risk control, discipline), `research/premise_forecast/`
  (the census that showed the engagement-premise variant is NOT_READY), `data/raw/prism/`,
  `data/raw/depmap/`

Spend so far: $0, 0 wells, 0 downloads. CPU only, `maestro` env.

## 0. Why this task, and what it is not

The premise census (`research/premise_forecast/`) showed the full premise-repair variant of the
genetic-pharmacological discordance task is NOT_READY with local data: no in-context engagement
measurement exists for the discordance contexts (0 of 30 required clusters). This block does not
reopen that variant. It asks the question `dual_core_v2` section 14 actually posed: can the dual
core (agent + virtual cell) show a decision benefit on a task where (a) the choice of measurement
genuinely changes what can be decided, (b) the endpoint is a direct measurement, and (c) there are
enough independent units to tell?

T1 is a mechanism-class proxy task, as the transcriptomic one was. It does not validate mechanism
claims; it validates (or refutes) the decision machinery: template-calibrated elimination,
budgeted line choice, abstention, and the dual-core interaction. The genetic-pharmacological
layer (tier G in `protocol.json` phase B) uses DepMap CRISPR as a buyable genetic measurement;
it remains a proxy, not an engagement claim.

**Seen before the freeze** (recorded in `freeze.json`): descriptive matrix statistics only —
density, class sizes, AUC quantiles, and a model-free profile-separability diagnostic
(`tmp/prism_census_probe*.json`). No fold, template, band, arm or outcome was computed before
the freeze.

## 1. Construction (frozen)

| Item | Value |
|---|---|
| Response matrix | PRISM Repurposing secondary, screen priority MTS010 > HTS002, one row per (compound, line) |
| Reading | Curve AUC (8-point, 4-fold dilution from 10 uM, 5-day pooled viability); lower = stronger killing |
| Compounds | 517 (batch-stripped Broad IDs, annotated, InChIKey-connectivity-deduplicated) |
| Lines | 443 (measured for >= 80% of class compounds; 370 with DepMap CRISPR) |
| Classes | 39 primary-MoA classes with >= 8 units |
| Folds | 5, unit-grouped, round-robin in SHA256 order within class strata (88-117 compounds per fold) |
| Validator | class survives a reading at L iff `|auc - median_c(L)| <= k * max(1.4826 * MAD_c(L), 0.05)`; templates need >= 5 training readings; k per fold by exact leave-one-unit-out on training compounds, smallest k with per-reading wrong-elimination <= 0.02 |
| Budget | 16 curves (sensitivity 8 and 32 registered) |
| Menu rule | a purchased line without a measured curve is a charged QC failure (budget spent, no reading) |

Pre-freeze descriptive evidence that the task has class structure: on centred AUC profiles the
within-class median cosine is 0.35 vs 0.03 chance-level nearest-neighbour agreement; targeted
oncology classes cohere (tubulin 0.44, GR agonist 0.43, MEK 0.38, Aurora 0.37, topoisomerase
0.35, EGFR 0.35) while non-oncology classes do not (COX 0.08, histamine 0.03) — the latter are
expected to stay abstained, which is the framework's honesty feature, not a defect.

## 2. Qualification gate (registered in protocol.json)

1. oracle - fixed_informative >= +0.05 correct decisions (unit mean);
2. fixed_informative - random >= +0.02;
3. oracle conditional wrong risk <= 0.10;
4. shuffled controls decide below the fixed panel;
5. >= 400 episodes and >= 20 classes with >= 8 units.

## 3. Results

### 3.1 Qualification v1 (protocol `viability-contrast-1`): GATE FAILED — measured

Frozen at 2026-09-28T07:37:31Z (`freeze.json`); run output in
`outputs/viability_contrast_20260928/qualify/`. 517 episodes, 39 classes, budget 16.

| Arm | Correct | Coverage | Conditional wrong | Measurements | Contradiction |
|---|---|---|---|---|---|
| oracle (diagnostic) | 0.166 [0.130, 0.193] | 0.557 | **0.701** | 9.3 | 0.060 |
| fixed_informative | 0.006 | 0.023 | 0.750 | 15.9 | 0.000 |
| random | 0.004 | 0.023 | 0.833 | 15.9 | 0.002 |
| oracle_shuffled (control) | 0.108 | 0.756 | 0.857 | 3.1 | 0.244 |
| fixed_shuffled (control) | 0.000 | 0.025 | 1.000 | 15.9 | 0.002 |

Gate: `oracle - fixed = +0.160` passed (+0.05 required); every other check failed:
`fixed - random = +0.002` (< +0.02), oracle conditional wrong 0.701 (> 0.10), and the shuffled
oracle (0.108) stayed far above the class-prior rate — the decision machinery itself produced
"decisions" on destroyed data. **The v1 validator, not the task, failed.**

**Failure mechanism (measured, post-hoc diagnosis of the registered run):**
1. In decided oracle episodes the true class was eliminated before the decision in **163 of
   249 (65%)**, at median step **1**. Hard elimination with a single out-of-band reading kills
   the truth for any atypical class member; well-estimated (large, tight-template) classes are
   the easiest to kill — EGFR (37 episodes) decided at 0.568 with 0.027 correct.
2. Survival was driven by **falsifiability, not evidence**: classes with thin template coverage
   cannot be eliminated and win by default (template coverage correlates with class size,
   r = 0.354; glutamate class: 12 episodes, 0.917 decided, 0.750 correct). The winner held a
   valid template at a purchased line with p10 = 0.0 — some decisions landed on classes never
   tested at any purchased line.
3. The shuffled oracle inherited the same bias (decides 0.756 on noise), confirming the
   machinery produced decisions independent of readings.

This is the same structural lesson the transcriptomic task taught in reverse: an elimination
rule whose falsifiability is asymmetric across hypotheses measures template coverage, not
evidence. The v1 design is retired; artifacts are preserved unchanged.

### 3.2 Qualification v2 (protocol `viability-contrast-2`): gate failed as written; the measurement underneath is the task's real property

Frozen at 2026-09-28T07:48:53Z (`freeze2.json`; a first attempt crashed in the summary step
before any number was read; the crash-fixed code is what the freeze records). Run output in
`outputs/viability_contrast_20260928/qualify2/`. 517 episodes, 39 classes, budget 16.

| Arm | Correct | Coverage | Conditional wrong | Measurements |
|---|---|---|---|---|
| oracle (diagnostic) | 0.988 | 0.990 | 0.002 | 2.3 |
| fixed_informative | 0.000 | 0.000 (tau = +inf) | - | 16.0 |
| random | 0.000 | 0.000 (tau = +inf) | - | 16.0 |
| oracle_shuffled | 1.000 | 1.000 | 0.000 | 2.0 |
| fixed_shuffled / random-equivalent | 0.000 | 0.000 | - | 16.0 |

The v2 gate failed by its letter: `fixed - random = 0` (both abstain everywhere) and the
shuffled-oracle checks are uninterpretable, because a clairvoyant margin-maximising policy on a
443-line menu wins even on destroyed data (optimizer's curse in pure form; the valid artifact
controls are the shuffled floor arms, which decide nothing on noise: PASS).

**What the calibration tables show (the real measurement).** The score margin is a calibrated
confidence *only under an informed policy*: oracle calibration episodes decide ~230/400 at
margin >= 1 with **0.0 wrong**, while fixed and random policies never reach a 5% wrong rate at
any tau (51-95% wrong wherever >= 20 episodes decide). Uninformative line choice cannot certify
a single decision on this task; clairvoyant line choice certifies almost all of them.

**Interpretation.** This is exactly the property the task was built to have, and the exact
estimand of the dual core: everything between the abstaining floor and the clairvoyant ceiling
must come from *predicted* readings substituting for clairvoyant ones. The margin-calibrated
validator, the abstaining floor, and the oracle ceiling are all measured. Phase B (registered
as `protocol3.json`) therefore runs the dual core directly: a world-model-guided planner against
masked-world and shuffled-reading controls, with the same margin validator and per-arm tau
calibration. The v2 protocol's phase-B gate is superseded by that registration.

### 3.3 Dual-core v3 (protocol `viability-contrast-3`): gate failed; two mechanisms measured

Frozen at 2026-09-28T08:08:27Z (`freeze3.json`; smoke run printed shapes only). Run output in
`outputs/viability_contrast_20260928/run3/`. 517 episodes, 39 classes, budget 16, 7 arms.

| Arm | Correct | Coverage | Conditional wrong | Measurements |
|---|---|---|---|---|
| oracle (diagnostic) | 0.988 | 0.990 | 0.002 | 2.3 |
| planner_reference | 0.000 | 0.000 (tau = +inf) | - | 16.0 |
| planner_structural | 0.000 | 0.000 (tau = +inf) | - | 16.0 |
| planner_masked / planner_shuffled | 0.000 | 0.000 | - | 16.0 |
| fixed_informative / random (floors) | 0.000 | 0.000 | - | 16.0 |

No planner arm certifies at any tau. Two mechanisms, both measured:

1. **The structural channel carries nothing beyond the class template.** The fitted blend is
   lambda = 0.0 in every fold: the Tanimoto-neighbour mean does not improve training reading
   log-likelihood over the class median (neighbours are mostly same-class, so the neighbour
   mean is a noisier class mean). planner_structural is numerically identical to
   planner_reference.
2. **Margin-optimising destroys margin calibration (Goodhart mechanism, measured).** The
   planner is only marginally better than the fixed panel: at tau = 8 it decides ~103/400
   calibration episodes with 66-73% wrong (fixed: ~35 with 51-87%), and no tau reaches the 5%
   target. The oracle decides ~230/400 at tau = 1 with 0.0% wrong. The difference is not the
   validator but the selection pressure: a policy that *optimises the margin* inflates it
   regardless of truth, while the oracle optimises the margin *of the true class*. This is the
   E-CAL1 optimizer's curse shown mechanistically: the margin is a calibrated confidence only
   when the policy is not selecting on it.

**What this identifies as the missing core.** The belief-mixture predictive treats the compound
as a generic class member; the oracle's advantage is that it knows the compound's actual
readings and chooses lines where *this compound* will separate classes. The dual-core question
therefore reduces to: can the virtual cell predict the compound's own next reading from its own
previous readings (profile completion) well enough for margin calibration to survive planning?
Protocol `viability-contrast-4` registers exactly that channel.

### 3.4 Dual-core v4 (protocol `viability-contrast-4`): the compound-level channel helps prediction, not enough for certification

Frozen at 2026-09-28 (`freeze4.json`; smoke run printed shapes only). Run output in
`outputs/viability_contrast_20260928/run4/`. Non-profile arms imported unchanged from the frozen
v3 outputs.

| Arm | Correct | Coverage | Conditional wrong | Measurements |
|---|---|---|---|---|
| oracle (imported) | 0.988 | 0.990 | 0.002 | 2.3 |
| planner_profile | 0.000 | 0.000 (tau = +inf) | - | 16.0 |
| planner_profile_masked / _shuffled | 0.000 | 0.000 | - | 16.0 |
| planner_reference and floors (imported) | 0.000 | 0.000 | - | 16.0 |

- **The channel is real but small.** beta = 0.25 in folds 0, 1, 4 and 0.0 in folds 2, 3 by
  training reading log-likelihood (e.g. fold 0: +1,066 nats over the class template). Profile
  completion helps predict the next reading; it does not reach decision strength.
- **Margin calibration improves with tau but never qualifies.** Fold 0 calibration: wrong rate
  0.95 at tau 0, 0.49 at tau 13 (35 decided), 0.11 at tau 21 (9 decided). The qualifying region
  would need tau > 21 with >= 20 decided calibration episodes; at tau 21 only 4-15 episodes
  decide per fold. The direction is consistent with certification at extreme margins, but the
  calibration base is too thin to establish it — the same "not enough independent units at the
  boundary" limitation as the transcriptomic task, now measured on a task with 490 units.
- **Contrasts:** profile - reference = 0.0, profile - masked = 0.0 (neither certifies, so the
  compound-specificity test is vacuous at this operating point); oracle - profile = +0.988.

### 3.5 Synthesis across v1-v4

What this block established, in order:

1. **A task with a real choice space and a credible endpoint exists and is cheap.** PRISM
   viability curves: 490 units over 39 classes, a 443-line menu, every reading present, all
   inputs local and public. The oracle/floor gap is the widest ever measured in this project:
   clairvoyant choice certifies 98.8% of episodes at 0.2% risk with 2.3 measurements;
   uninformative choice certifies nothing at any tau.
2. **The validator, not the task, was the first bottleneck** (v1): hard elimination with
   asymmetric falsifiability measures template coverage instead of evidence. The score-margin
   validator (v2) fixes it and is retained.
3. **Margin confidence is policy-dependent** (v2/v3): it calibrates under the oracle policy and
   under no realistic policy tried. Margin-optimising planners inflate the margin regardless of
   truth (Goodhart mechanism; the E-CAL1 optimizer's-curse finding, now shown mechanistically).
4. **Prediction helps, decisions do not follow** (v3/v4): structure adds nothing (lambda = 0);
   profile completion adds a small real gain (beta = 0.25 in 3/5 folds) that does not reach
   decision strength. This mirrors dual_core_v2's central finding on independent data: forecast
   improvements do not become decision improvements, and the gap between class-level prediction
   and compound-level reality is where the value sits.
5. **The dual-core estimand is now purified.** The task cleanly separates three levels:
   floor (0 certified), realistic dual core (0 certified at tau <= 21), oracle (98.8% at 0.2%
   risk). What separates the realistic core from the oracle is exactly a compound-level
   predictive good enough to keep margins honest under planning. That is a precise, falsifiable
   target for the next iteration — better profile-completion models (learned rather than kNN),
   a non-margin-optimising acquisition objective, and a tau grid extended past 21 with a
   thicker calibration base are the registered directions.

**Registered but blocked:** the τ-gated `llm_agent` arm (protocol.json phase B) cannot run
because no realistic arm reaches a finite tau. An exploratory forced-argmax LLM diagnostic
(DeepSeek via `.env`, clearly labelled, not part of the registered grid) is reported in
`outputs/viability_contrast_20260928/llm/`; the forced-argmax references for it are
fixed_informative 0.130 and random 0.100 (231 episodes, folds 0-1). Two integration artifacts
are recorded as such: `deepseek-flash` is a reasoning model and unbounded reasoning consumed
the whole completion budget (200, then 2,000, then 4,000 tokens — always exactly exhausted,
content empty); the runs before `reasoning_effort = "none"` was set produced no valid episode
and were discarded, not read as results.

**Not attempted here:** the genetic tier (CRISPR as a buyable measurement); a learned (non-kNN)
profile-completion model; tau grids beyond 21 with leave-one-out calibration; longer budgets.
All development data (PRISM, DepMap local since 2026-08-23) are exposed to this block for the
first time as a scored substrate, but every result remains a development record, not an
untouched-test claim.

### 3.6 Dual-core v5 (protocol `viability-contrast-5`): learned world and non-margin acquisition do not move the certification frontier

Frozen at 2026-09-28T10:28:35Z (`freeze5.json`; a synthetic smoke run exercised every code
path including the genetic-purchase branch, printing shapes only). Run output in
`outputs/viability_contrast_20260928/run5/`. 517 episodes, 39 classes, budget 16, 9 new
arms (3 acquisition rules x {real, masked, shuffled}) plus 8 arms imported unchanged from
the frozen v3/v4 outputs. Runtime 38 min CPU.

| Arm | Correct | Coverage | Conditional wrong | Measurements |
|---|---|---|---|---|
| oracle (imported) | 0.988 | 0.990 | 0.002 | 2.3 |
| planner_learned_margin / _mi / _thompson | 0.000 | 0.000 (tau = +inf) | - | 16.0 |
| all masked and shuffled controls | 0.000 | 0.000 | - | 16.0 |
| planner_profile, planner_reference and floors (imported) | 0.000 | 0.000 | - | 16.0 |

Gate v5 FAILED: no realistic arm reaches a finite tau in any fold, even with the grid
extended to 55. The measurements underneath:

1. **The learned channel is real but thin.** Rank 16 is selected in every fold, yet the
   rank-selection log-likelihoods differ by <= 0.3% relative between ranks (e.g. fold 0:
   136,299 / 136,410 / 136,604 for r = 4 / 8 / 16). The precision blend replaces v4's
   fixed beta with an adaptive per-line weight; the prediction gain over the template
   stays small, exactly as v4 measured for the kNN channel.
2. **The certification frontier does not move.** The best achievable operating point
   (minimum calibration wrong rate where >= 20 episodes decide) is 0.55-0.81 across arms
   and folds, against the 0.05 target; at tau >= 21 only 1-14 episodes decide per fold.
   This is now measured under three world models (class template, kNN profile, learned
   low-rank completion) and three acquisition rules — the frontier is a property of the
   task-policy pair, not of one world.
3. **Goodhart mechanism, refined.** At tau = 8 the margin rule decides 54-99 calibration
   episodes per fold at 77-88% wrong; MI decides 54-63 at 63-70% wrong; Thompson decides
   59-66 at 66-86% wrong. The non-margin objectives reduce margin inflation in the
   registered direction (fewer decisions, lower wrong rate at fixed tau) but nowhere near
   certification. The margin remains a calibrated confidence only under the oracle policy.
4. **Boundary note (post-hoc reading of the registered tau tables, not a claim).** In
   fold 0, v4's kNN arm decided 9/1 (wrong) at tau = 21 while v5's margin arm decides
   10/9. Counts are tiny, but the direction is consistent with a mechanism worth
   registering for the next design: precision blending shrinks the world's predictive
   variance, and a margin-optimising planner exploits the tighter ranking, strengthening
   the selection pressure the margin must survive. A more confident world can calibrate
   worse under a gaming policy.
5. **Phase G5 blocked; the genetic channel fit is reported unconditionally.** No fold had
   a finite realistic tau, so the genetic arms never ran and the llm_agent unlock
   (protocol.json phase B) remains registered-blocked. The frozen channel fit kept 195/195
   class-fold models — reading the output exposed a baseline flaw: the frozen comparison
   used a pooled one-mean baseline, unfair to the per-line template. A post-hoc refit
   (`tmp/genetic_refit_posthoc.py`, clearly outside the frozen run) against the per-line
   template still keeps 35-36/39 classes per fold, but the median gain is ~0.1 nat per
   pair and the comparison remains sensitive to variance modelling (OLS MLE variance vs
   MAD-floored template scale). The channel's mean-level information is therefore NOT
   established; its decision value is untested. The literature prior (PLoS Comput. Biol.
   2023: DepMap CRISPR features add little over expression/kinome for viability
   prediction) stands unrefuted.

**Synthesis after v5.** The estimand is unchanged and now triple-measured: floor 0,
realistic dual core 0 at any tau, oracle 98.8% at 0.2% wrong with 2.3 measurements. The
compound-level accuracy a world would need to certify within budget 16 approaches knowing
the readings themselves [RETRACTED in section 3.7: perfect knowledge of all readings
yields zero qualified decisions]; every learnable channel tried (structure lambda = 0,
kNN beta = 0.25, learned rank 16) sits far below that bar. The registered conclusion is that
**the next iteration is a reformulation, not a fourth world model**: (i) certify on a
statistic the acquisition does not optimise (the margin fails because the policy can
select on it; a dual rank- or elimination-based certification may not), or (ii) move to
the framework's native estimand — a two-compound mechanism contrast (A vs B over the same
line panel), whose symmetric two-hypothesis decision space is one where budget-16
evidence can dominate, instead of one-compound MoA identification over 39 classes. Both
are Proposed; neither is attempted here.

### 3.7 Dual-core v5b (protocol `viability-contrast-5b`): the ceiling was measuring answer-key-guided evidence selection, not world-model quality

Frozen at 2026-09-28T11:39:31Z (`freeze5b.json`; synthetic smoke covered every new code
path, printing shapes only). Run output in `outputs/viability_contrast_20260928/run5b/`.
Runtime 81 min CPU. Trigger: an external review of the frozen v5 results raised one
numerical defect and three inference weaknesses; all four were verified against the
frozen v5 code BEFORE registration (diagonal-only posterior covariance in
`world5._predictive`, reproduced 1.99 vs 0.77 on a random PD matrix; uncalibrated
precision blend; point-estimate tau screening, CP UCB of 0/20 = 0.139; the oracle
mixing reading and label access). protocol5b.json registered the four corrections with
pre-stated revision criteria. v5 outputs are retained unchanged and imported for
cross-run comparison.

**C1 (variance fix) — the frontier conclusion SURVIVES.** With the full quadratic form
V sig V^T, no realistic arm reaches a finite tau_emp in any fold; the qualification
frontier (min wrong rate where >= 20 calibration episodes decide) is 0.57-0.86 across
arms and folds, against 0.55-0.81 in v5. Rank selection changed (16/8/8/16/16 vs all-16
in v5), confirming the defect was live, but it did not move any decision-level number
that v5 reported. The MI-at-tau-8 direction survives for the v5-comparable precision
blend (5/5 folds lower wrong than margin: e.g. fold 0, 42/62 vs 77/94) and is mixed for
the holdout blend (3/5). The v5 Goodhart-reduction claim for MI stands, unchanged in
strength.

**C2 (blend variants) — the completion channel is retired at the decision level on this
task.** The training-selected holdout weight is w = 1.0 in 4/5 folds and 0.75 in fold 0:
the simulated-episode log-likelihood prefers completion-ONLY over any template blend.
Yet the holdout arms qualify nothing, and the template-only ablation (off_mi) posts a
BETTER frontier than holdout_mi in 4/5 folds (0.61-0.71 vs 0.58-0.83). Measured: the
channel's training-predictive gain, however real, does not convert into decisions under
any tested fusion rule — the registered retirement criterion (off matches or beats the
blend) is met. The reviewer's double-counting concern did NOT resolve toward w = 0; the
completion dominates predictive likelihood while adding nothing downstream. The v5
section-3.6 mechanism note (precision blending shrinks variance and a gaming planner
exploits it) remains Not established, as registered.

**C3 (oracle decomposition) — the headline.** Two new ceiling arms on the same term
matrix: oracle_reading (sees all classes' true future terms, not the label; buys the
candidate whose realised update maximises the top1-top2 margin) and oracle_label (sees
the label, not the readings; steers the true class's expected margin under its own
template; can be charged QC failures like a realistic arm).

| Arm | Frontier (min wrong, >= 20 decided) | Qualified decisions at any tau |
|---|---|---|
| oracle_full (imported v3 oracle) | 0.002 held-out (512 decided, 1 wrong; CP UCB95 0.0092) | 98.8% of episodes |
| oracle_label | 0.26-0.40 at tau 13 | none |
| oracle_reading | 0.77-0.87 at tau 34 | none |
| best realistic (any world, any rule) | 0.57-0.86 | none |

Three measured facts follow. (a) Perfect knowledge of every candidate reading, without
the label, is WORTHLESS for qualification — worse than several realistic arms, because
label-blind margin-chasing with perfect foresight is aggressive Goodhart: over 39
classes x 443 lines it always finds noise-driven separation for SOME class. (b) Label
access with only template-level response knowledge reaches 0.26-0.40 wrong — far better
than everything realistic, still 5-8x above the 5% bar. (c) Only the conjunction
certifies. Per the pre-registered criterion (gate check 2), the v5 sentence "the
compound-level accuracy needed approaches knowing the readings themselves" is
RETRACTED: the v1-v5 'oracle ceiling' measured the value of selecting evidence to fit
a known answer, not an upper bound on world-model quality. The world-model lever on
this task-policy pair is measured dead — perfect response prediction produces zero
qualified decisions under the score-margin validator and any tested acquisition rule.

**C4 (qualification statistics).** Every tau cell now carries a Clopper-Pearson
one-sided 95% UCB. Under the strict tau_ucb rule (decided >= 20 and UCB <= 0.05),
nothing realistic or partial-oracle qualifies anywhere — by construction nearly
unattainable at n = 20 (0/20 gives UCB 0.139; 5%-grade evidence needs >= 59 zero-wrong
decisions). oracle_full remains certification-grade post hoc on held-out decisions
(UCB 0.0092). Terminology: 'empirical qualification frontier' replaces 'certification
frontier' for point-estimate selection in all future text. Registered limitations
carried over: calibration episodes share templates and basis (UCBs optimistic in the
known direction); tau calibrated on half-fold worlds transfers to full-fold worlds by
assumption.

**Genetic tier.** The gate (any finite realistic tau_emp) never passed; the tier did
not run. The unconditional channel fit is byte-identical to v5's (frozen code path)
and is not re-interpreted here; the section-3.6 post-hoc re-analysis stands.

**Gate v5b: FAILED.** Checks 1 (any realistic finite tau_emp) and 2 (oracle_reading
above the best realistic arm) failed; check 3 (shuffled controls abstain) passed.

**Synthesis after v5b.** Three numbers now describe this task-policy pair: realistic
dual core 0 qualified; perfect response prediction 0 qualified; label-guided evidence
selection 98.8%. The registered next step (section 3.6) is unchanged in direction but
its justification is now stronger and different in kind: response prediction is
measured non-binding HERE, so the reformulation must change what the decision can be
dominated by — the paired two-compound contrast (symmetric two-hypothesis space,
pre-registered phenotype endpoint, confirmation data the adaptive policy cannot
select on) remains the identified lever. Two additions to the standing register:
(i) any future 'certification' claim requires UCB-grade evidence (>= 59 zero-wrong
decisions, or sequential methods with stated assumptions), not the 20-decision
point-estimate screen; (ii) a reading-level ceiling like oracle_reading is a required
control in any future ceiling design — a full oracle without its decomposition
misattributes label access to prediction quality, as it did here for five versions.

## 4. Literature position (verified by retrieval 2026-09-28)

| Source | Status | What it bears on here |
|---|---|---|
| Corsello et al., PRISM Repurposing (depmap.org/repurposing; bioRxiv 730119) | resource paper | viability profiles cluster by MoA; the biological basis of the templates |
| BATCHIE, Tosh et al., Nat. Commun. (2025), doi:10.1038/s41467-024-55287-7 | published | Bayesian active learning for combination screens optimises *model information*; here the objective is *certified decision elimination* with an explicit validator and abstention — a different estimand |
| BioDiscoveryAgent, Roohani et al., arXiv:2405.17631 | preprint | LLM-agent experiment design without a validator or risk control; the registered `llm_agent` arm is its analogue inside this contract |
| DeepTarget, npj Precis. Oncol. (2025) | published | PRISM+CRISPR integration for static target prediction; here genetics enters as a *buyable measurement* inside a decision loop, not as a static feature |
| Wang et al., gene-essentiality signatures, bioRxiv:2022.11.07.514541 | preprint | essentiality features predict targets; supports the genetic world channel in phase B |
| `research/dual_core_v2/` risk control (Learn-then-Test repaired; Waudby-Smith & Ramdas betting p-values) | project standard | reused unchanged for abstention policies |
| Yan and Zhong, Optimism Stabilizes Thompson Sampling for Adaptive Inference, COLT 2026 (arXiv:2602.06014) | published (retrieval-verified 2026-09-28) | variance-inflated / optimistic Thompson restores valid adaptive inference; motivates the v5 thompson arm as a calibration-preserving selection rule — the measured gain was real but far from certification |
| Kinome inhibition states, PLoS Comput. Biol. 2023 (PMC9983880) | published (retrieval-verified 2026-09-28) | DepMap CRISPR/CNV/proteomics features did not significantly improve viability prediction over expression and kinome features; the registered prior that G5's static-feature value is small — unrefuted by v5's unconditional channel fit |
| Shim et al., Joint Active Feature Acquisition and Classification, NeurIPS 2018; Bingham, EIG-Cost clinical AFA, medRxiv 2026 | published / preprint (retrieval-verified 2026-09-28) | test-time feature purchase with cost-penalised information gain is the established estimand family for the G5 genetic tier; the novelty here is placing it inside a certified-risk elimination contract, not the estimand itself |

Novelty claim is narrow and stated against the contract: decision-directed elimination with
certified risk on a viability-contrast task, measuring the agent x world-model interaction under
identical menus and budgets. No new foundation model, no biological mechanism claim.

## 5. Reproduction

```bash
python -m research.viability_contrast.prepare
python -m research.viability_contrast.prepare3
python -m research.viability_contrast.freeze          # v1 digests
python -m research.viability_contrast.freeze --verify
python -m research.viability_contrast.qualify         # v1 (gate FAILED, section 3.1)
python -m research.viability_contrast.freeze --v2
python -m research.viability_contrast.freeze --v2 --verify
python -m research.viability_contrast.qualify2        # v2 (section 3.2)
python -m research.viability_contrast.freeze --v3
python -m research.viability_contrast.run3            # v3 dual-core grid (section 3.3)
python -m research.viability_contrast.freeze --v4
python -m research.viability_contrast.run4            # v4 profile channel (section 3.4)
python -m research.viability_contrast.prepare5        # v5 genetic pack addition (descriptive)
python -m research.viability_contrast.freeze --v5
python -m research.viability_contrast.freeze --v5 --verify
python -m research.viability_contrast.run5            # v5 learned world x acquisition grid (section 3.6)
python -m research.viability_contrast.llm_arm         # exploratory LLM diagnostic (needs .env)
python -m research.viability_contrast.freeze --v5b
python -m research.viability_contrast.freeze --v5b --verify
python -m research.viability_contrast.run5b           # v5b corrections + oracle decomposition (section 3.7)
```
