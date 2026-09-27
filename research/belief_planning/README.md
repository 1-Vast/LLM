# Belief-space planning with a virtual-cell world model, and the first external test

**Date:** 2026-09-27, 03:00 to 05:40 (+0800).

**Protocol:** `belief-planning-1` ([PROTOCOL.md](PROTOCOL.md), [protocol.json](protocol.json)),
frozen at 04:35:20 in [freeze.json](freeze.json).

**Diagnosis:** [DIAGNOSIS.md](DIAGNOSIS.md). **Data provenance:** [DATA.md](DATA.md).

**Outputs:** `outputs/belief_planning_20260927/`. They are not tracked; small copies are in
`log/20260927/0927/`.

## Answer

**No.** On an untouched public study (LINCS L1000 Phase II, GSE70138), a belief-space agent
chose real measurements with a virtual-cell world model, under the frozen protocol. It did not
reach more correct mechanism decisions than the fixed expert order. It was run once, behind a
vault, with policies, thresholds and analysis frozen first.

- **Correct decisions:** -0.024 against the fixed order, 95% interval [-0.074, +0.011], on 38
  independent compounds.
  - The frozen status is **INCONCLUSIVE**.
  - The pre-registered minimum practical improvement (+0.02) lies outside the interval, so a
    meaningful gain over the fixed order is not supported.
- **Against the model-based baselines** (the non-agent myopic expected-value rule,
  measured-profile retrieval, reference marginals), the agent made more correct decisions, by
  +0.02 to +0.04 with lower bounds above zero. It paid for them with more measurements and more
  wrong decisions, so those comparisons fail the cost and safety gates too.
- **The virtual cell did not change decisions.**
  - It altered the chosen sequence in about 1% of episodes, with no effect on outcomes.
  - On the L1000 development data it abstained entirely: the fitted kernel strength was zero.
  - Verdict: **REJECTED** as a practically meaningful contribution.
- **Feedback changed the agent's actions but not its results.**
  - Removing the feedback channel changed 23% of external measurement sequences. After an
    identical first measurement, the real reading changed the second choice in 12 of 173
    episodes.
  - Against the control that withholds the readings, correct decisions moved by -0.005
    [-0.024, +0.011].
  - Verdict: **REJECTED** as a practically meaningful contribution.
- **The development tiers say the same thing** (below). The agent helps in one L1000 tier, is
  level in SciPlex3 B and L1000 T, and loses badly in SciPlex3 A.

## Why the earlier planners lost (summary of [DIAGNOSIS.md](DIAGNOSIS.md))

1. **Refusal was scored as zero value.** With thin references, the card forecaster refused. The
   planners then stopped: 7-35% of episodes ended deferred, while the fixed order never defers.
2. **Noisy per-class cards.** 2-40 references per condition, maximised over 8-12 actions,
   selected noise.
3. **Readings were treated as independent.** Dose escalation looked valuable although it fails
   on the same compounds (SciPlex3 A: 16% correct against 44% unconditionally).
4. **No decision channel for the virtual cell.** It entered only as a tie-break.
5. **Little headroom.** The oracle beats the fixed order by 0.03 (A), 0.09 (B), 0.06 (LT) and
   0.001 (T), so an improvement of 0.02 is at or beyond the ceiling in two tiers.
6. **Few independent units:** 42-256 per tier.

The audit also found defects introduced after the 2026-09-27 registered run (DIAGNOSIS §1):
- `expected_terminal_decision_value` double-counted evidence. It is now fixed.
- The metadata tier path emits episodes whose truth is `None`.
- The earlier freeze and one replay fold were rewritten post hoc. The originals are recorded in
  the day log.

## Method, and why this combination

- **Planner** (`src/maestro/planning.py`). Exact finite-horizon expectimax over the runner's legal
  menu: belief-space planning in a POMDP (Kaelbling, Littman & Cassandra 1998) with at most two
  measurements.
  - The value is decision-theoretic: the expected value of sample information (Raiffa & Schlaifer
    1961; Lindley 1956) under the registered +1 / -2 / 0 utility.
  - It is not information gain. Information that cannot change the validator's decision is
    worthless here, and the mutual-information arm (`info_gain`) was already on the ladder.
  - A registered elimination is scored by the posterior mass it removes. This coherence is what
    the earlier Codex function lacked.
  - With two steps and 12 actions exact planning is cheap, so no Monte Carlo tree search or
    reinforcement learning is needed. The lookahead is non-myopic in the next-best-view sense (a
    measurement valued for what it enables next), and it is tested against a one-step control.
- **World model** (`research/belief_planning/world.py`).
  - An empirical-Bayes hierarchy (Efron & Morris 1975): condition, then class of the hypothesis,
    then structural neighbours. The references' readings are left-one-unit-out.
  - The virtual cell is a nonparametric structural kernel with an applicability domain. Its
    strength is fitted by leave-one-out likelihood and falls to zero when structure does not
    predict readings.
  - Feedback enters as history-conditioned forecasts: the POMDP's observation model.
  - Larger neural perturbation models (CPA, chemCPA, GEARS, State) were not added, for three
    reasons. The earlier block showed that better profile prediction (ridge, structure kNN) did
    not improve decisions. The oracle headroom is small. chemCPA-class models were pre-trained on
    L1000, which would contaminate a GSE70138 test.
- **Safety.**
  - A secondary candidate is anchored to the expert order, and leaves it only on 1.645 standard
    errors of evidence (safe policy improvement with baseline bootstrapping; Laroche et al. 2019;
    Thomas et al. 2015).
  - The risk gate is the directly measured wrong rate and its cluster-bootstrap bound.
    Conformal-style guarantees assume exchangeability, which fails across studies, so none is
    claimed externally.
- **Rejected alternatives:**
  - Causal experimental design: the hypotheses are mechanism classes read by a fixed rule, not a
    graph to learn.
  - Model-based reinforcement learning: nothing to learn by interaction when exact planning is
    available.
  - A factorised world model (detection pooled across classes): tried on development data, and
    worse.

## Data and task

| | Development | External |
|---|---|---|
| Studies | SciPlex3 (tiers A: A549 dose x time; B: 3 lines x 4 doses at 24 h), L1000 Phase I (LT: 4 lines x 6/24 h; T: A549 6/24 h) | GSE70138, L1000 Phase II Level 5 |
| Episodes | 12,428 (the 2026-09-27 registered manifests) | 380 |
| Independent units | 42 / 132 / 256 / 170 | 38 test-compound components |
| Task | tier-specific, at most 2 measurements | MCF7/HT29/PC3 x 0.04/0.12/1.11/10 uM at 24 h, at most 2 measurements, 16 assay-days (the SciPlex3 B structure) |
| References | training folds | 1,053 Phase II compounds already known to development; about 100 in the 11 pool classes |

GSE70138 has almost no 6 h profiles (1,094 of 118,050 signatures), so the development time task
was not forced onto it. The line-by-dose task matches SciPlex3 B instead. A stricter design used
a Phase I reference library for a Phase II line task; it yields only 96 development episodes
(`l1000_level5.phase1_line_task_feasibility`) and was not run.

## Results: development (internal, not confirmation)

The registered replay ran 20 tasks: 12,428 episodes, 298,272 records, 0 integrity problems. Every arm used the
same episodes, menus and rules. The ladder arms reproduce the 2026-09-27 registered rates exactly
(for example, fixed is 0.640 / 0.057 in A and 0.582 / 0.049 in B, and myopic EDV is 0.438 in A
and 0.529 in B).

| Tier (units) | Oracle | Fixed (correct / wrong / meas.) | **belief** (correct / wrong / meas.) | belief - fixed, correct [95% CI] | Wrong diff. | Status | Best other baseline under cap |
|---|---|---|---|---|---|---|---|
| SciPlex3 A (42) | 0.670 | 0.640 / 0.057 / 1.63 | 0.506 / 0.042 / 1.62 | -0.134 [-0.217, -0.057] | -0.015 | REJECTED | random_legal / ridge 0.449 |
| SciPlex3 B (132) | 0.668 | 0.582 / 0.049 / 1.52 | 0.590 / 0.038 / 1.50 | +0.008 [-0.018, +0.035] | -0.010 | INCONCLUSIVE | fixed 0.582 |
| L1000 LT (256) | 0.168 | 0.106 / 0.006 / 1.93 | 0.131 / 0.006 / 1.37 | +0.024 [+0.000, +0.050] | -0.000 | INCONCLUSIVE (G3 lower bound = 0) | info_gain 0.126 |
| L1000 T (170) | 0.231 | 0.230 / 0.011 / 1.85 | 0.224 / 0.009 / 1.70 | -0.006 [-0.010, -0.002] | -0.002 | INCONCLUSIVE | fixed 0.230 |

- **L1000 LT is the one tier where the agent looks better.**
  - It gives 0.024 more correct decisions than the fixed order with 0.57 fewer measurements
    (-2.97 assay-days), and the same wrong rate.
  - The lower bound of that difference is 0.000, so it misses G3 by the width of the rounding.
  - It beats the best simple baseline here (`info_gain`) by 0.005, which is not practically
    meaningful.
- **SciPlex3 B.** The agent matches the fixed order with 0.010 fewer wrong decisions.
- **SciPlex3 A.** The agent loses 13 points. The expert order (24 h, then 72 h, at the top dose)
  encodes time-course knowledge that 42 units of references cannot teach the world model.
- **Against the model-based baselines.** In every tier the agent makes more correct decisions
  than `myopic_edv`, `retrieval` and `marginal_only`, by +0.009 to +0.14 with lower bounds above
  zero. It uses more measurements and has slightly more wrong decisions, so those comparisons do
  not pass G2 and G4.
- **The anchored agent almost never leaves the fixed order.**
  - It departs in 0 episodes (A, T), 16 of 2,160 (B) and 334 of 6,880 (LT), changing 12 and 16
    terminal decisions respectively.
  - Correct differences are 0.000 in every tier.
  - With 2-40 references per class, the 1.645-standard-error rule is rarely met.

## Results: external (GSE70138, run once)

| Arm | Correct [95% CI] | Wrong [95% CI] | Deferred | Coverage | Selective risk | Measurements | Assay-days |
|---|---|---|---|---|---|---|---|
| oracle (bound) | 0.547 [0.395, 0.703] | 0.000 | 0.453 | 0.547 | 0.000 | 0.55 | 3.3 |
| **fixed** | 0.476 [0.321, 0.632] | 0.037 [0.003, 0.082] | 0.000 | 0.513 | 0.072 | 1.69 | 10.1 |
| anchored | 0.474 [0.318, 0.629] | 0.037 [0.003, 0.082] | 0.000 | 0.511 | 0.072 | 1.69 | 10.1 |
| belief (one-step) | 0.463 [0.316, 0.618] | 0.039 [0.008, 0.079] | 0.000 | 0.503 | 0.079 | 1.55 | 9.3 |
| magnitude | 0.461 [0.305, 0.618] | 0.021 [0.000, 0.055] | 0.000 | 0.482 | 0.044 | 1.62 | 9.7 |
| **belief** | 0.453 [0.308, 0.603] | 0.042 [0.011, 0.082] | 0.000 | 0.495 | 0.085 | 1.59 | 9.5 |
| belief, VC masked | 0.453 [0.308, 0.603] | 0.042 [0.011, 0.082] | 0.000 | 0.495 | 0.085 | 1.59 | 9.5 |
| belief, feedback withheld | 0.458 [0.308, 0.611] | 0.037 [0.008, 0.074] | 0.000 | 0.495 | 0.074 | 1.57 | 9.4 |
| marginal_only | 0.429 [0.287, 0.576] | 0.034 [0.008, 0.068] | 0.076 | 0.463 | 0.074 | 1.32 | 7.9 |
| myopic_edv | 0.424 [0.279, 0.574] | 0.032 [0.008, 0.061] | 0.076 | 0.455 | 0.069 | 1.28 | 7.7 |
| maestro_vc (2026-09-27 agent path) | 0.421 [0.279, 0.568] | 0.032 [0.008, 0.063] | 0.055 | 0.453 | 0.070 | 1.14 | 6.8 |
| retrieval | 0.411 [0.266, 0.561] | 0.026 [0.005, 0.053] | 0.076 | 0.437 | 0.060 | 0.98 | 5.9 |
| ridge | 0.300 [0.179, 0.426] | 0.021 [0.005, 0.042] | 0.082 | 0.321 | 0.066 | 1.54 | 9.3 |
| production_default | 0.158 [0.053, 0.289] | 0.005 [0.000, 0.013] | 0.000 | 0.163 | 0.032 | 1.89 | 11.4 |

Paired against the fixed order (same 380 episodes, 38 clusters):

| Candidate | Correct | Wrong | Measurements | G1 | G2 | G3 | G4 | Status |
|---|---|---|---|---|---|---|---|---|
| belief | -0.024 [-0.074, +0.011] | +0.005 [-0.016, +0.029] | -0.10 [-0.20, 0.00] | fail (upper 0.082) | fail | fail | pass | INCONCLUSIVE (practical gain excluded) |
| anchored | -0.003 [-0.008, 0.000] | 0.000 | 0.00 | fail (upper 0.082) | pass | fail | pass | INCONCLUSIVE (departs from fixed in 1 of 380) |

- **The fixed order also fails G1.** Its wrong rate bound is 0.082 on 38 clusters, so the 0.05
  cap cannot be certified for any arm that decides at this rate with this few units.
- **Where the agent's choices mattered.**
  - The agent took a different measurement sequence from the fixed order in 265 of 380 episodes,
    but the terminal decision changed in only 21 of them. It was better in 6 and worse in 15.
  - The oracle is better than the fixed order in 27 episodes: 23 where the fixed order was
    undetermined, 4 where it was wrong.

## Attribution: does the world model or the feedback earn its place?

| Setting | VC vs masked: switch / overall correct | Feedback vs withheld: switch / overall correct | Two-step vs one-step: overall correct |
|---|---|---|---|
| SciPlex3 A | 0.045 / +0.000 [-0.009, +0.009] | 0.324 (17 of 146) / -0.012 [-0.036, +0.009] | +0.003 [-0.045, +0.042] |
| SciPlex3 B | 0.032 / -0.002 [-0.005, +0.000] | 0.257 (122 of 854) / +0.003 [-0.004, +0.011] | +0.005 [-0.003, +0.013] |
| L1000 LT | 0.000 / +0.000 | 0.069 (23 of 3,525) / +0.002 [-0.000, +0.006] | +0.006 [-0.000, +0.013] |
| L1000 T | 0.000 / +0.000 | 0.033 (0 of 2,130) / -0.000 [-0.001, +0.000] | +0.018 [+0.006, +0.034] |
| GSE70138 (external) | 0.011 / +0.000 | 0.234 (12 of 173) / -0.005 [-0.024, +0.011] | -0.011 [-0.026, +0.003] |

The permuted controls match: the virtual cell permuted across compounds, and feedback replaced
by another compound's compatible real reading. See `summary.json`.

What "feedback withheld" does:
- The control replaces every reading in the agent's history with "did not end the episode",
  including the readings it imagines inside the lookahead.
- It therefore also changes some *first* actions: 434 of 2,160 in SciPlex3 B.
- The column counts both kinds of change. The number in brackets isolates execution-time
  feedback, the second action after an identical first one.

- **Virtual cell.**
  - Where structure predicts training readings (SciPlex3), the kernel is fitted at k = 1-2. It
    changes 3-5% of sequences, and those changes do not improve decisions.
  - On L1000 development data the fitted k is 0, so the virtual cell abstains.
  - On GSE70138 (k = 1) it changes about 1% of sequences, with no effect.
- **Feedback.** Removing it changes 3-32% of sequences. After an identical first measurement,
  a real reading changes the second choice in 0-14% of episodes. Withholding it
  never costs a practically meaningful number of correct decisions.
- **Lookahead.** It helps in L1000 T and is otherwise level or slightly worse.

## Calibration and safety

Calibration of the chosen action's forecast, for the true hypothesis, against the realised
reading:

| Setting | belief: P(wrong) forecast / observed | belief: P(correct) forecast / observed | 2026-09-27 card (maestro_vc): P(wrong) forecast / observed | sparse model (myopic_edv): P(wrong) forecast / observed |
|---|---|---|---|---|
| SciPlex3 A | 0.013 / 0.026 | 0.41 / 0.32 | 0.002 / 0.039 | 0.059 / 0.036 |
| SciPlex3 B | 0.011 / 0.026 | 0.46 / 0.40 | 0.003 / 0.026 | 0.055 / 0.024 |
| L1000 LT | 0.001 / 0.004 | 0.094 / 0.096 | 0.001 / 0.005 | 0.036 / 0.005 |
| L1000 T | 0.005 / 0.005 | 0.136 / 0.132 | 0.003 / 0.006 | 0.046 / 0.007 |
| GSE70138 | 0.005 / 0.027 | 0.30 / 0.29 | 0.002 / 0.028 | 0.043 / 0.025 |

- **Wrong eliminations are under-forecast by the world model**, 1.2 to 5 times. That is better
  than the old card (2 to 18 times) but still unsafe as a control signal.
  - The shortfall is largest where support is 10-19 references: forecast 0.003 against 0.048
    observed externally.
  - It is also large where compounds are structurally far from the references: Tanimoto 0.3-0.4,
    forecast 0.006 against 0.053.
  - The references' own leave-one-unit-out readings rarely eliminate wrongly, but new compounds
    do. This is the same study-to-study gap the 2026-09-27 audit found.
- **The sparse model over-forecasts wrong eliminations** (0.1 to 0.6 times the observed rate),
  so it stops early. That is why it is cheaper and less correct.
- **Correct-elimination forecasts** are close on L1000 and GSE70138. They are optimistic on
  SciPlex3 by 0.06-0.10, and the ECE is 0.05-0.13 (diagnostic only).
- **Direct risk.**
  - Every arm's directly measured wrong rate on GSE70138 has an upper bound of 0.04-0.10, with
    38 clusters. The 0.05 cap can only be certified with more units.
  - On development data the agent's upper bounds are 0.008 (LT), 0.014 (T), 0.054 (B) and
    0.080 (A).
  - No development guarantee is carried to the external study.

## Verdicts

| Claim | Verdict | Evidence |
|---|---|---|
| The agent makes more correct decisions than the fixed expert order on unseen compounds | **INCONCLUSIVE** by the frozen rule; practically meaningful gain excluded | external -0.024 [-0.074, +0.011] |
| The agent beats non-agent model-based baselines (myopic EDV, retrieval, marginal) at equal cost and risk | **INCONCLUSIVE**: more correct (+0.02 to +0.04, lower bounds > 0) but more measurements and more wrong | external gates G2/G4 |
| The virtual-cell world model improves measurement choice | **REJECTED** (no practically meaningful contribution) | switch ≤ 5%, overall effect about 0 in every setting |
| The agent uses real feedback beneficially | **REJECTED** (changes actions, not outcomes) | feedback vs withheld, all settings |
| Two-step lookahead helps | **INCONCLUSIVE** (helps L1000 T, not elsewhere) | belief vs belief_h1 |
| Development-tier superiority | see the development table: internally supported nowhere under all four gates | registered development replay |
| Evidence coherence (forecasts never become evidence; eliminations scored by the posterior mass removed) | **DEMONSTRATED** (engineering) | tests; 0 integrity problems in 307,392 registered records |
| Deterministic replay across environments | **DEMONSTRATED** | identical decisions in Python 3.11.16 and 3.14.4; floating differences at most 3.1e-15 |
| Calibrated wrong-decision forecasts | **REJECTED** for the world model (5x too low externally) | calibration audit |
| External generalisation of any MAESTRO measurement policy | **NOT DEMONSTRATED**; no candidate passed on the one untouched study | this run |

## Limitations and the next experiment

- **The external test is underpowered.** Only 38 of 673 new compounds fell in the reference-built
  pool, and the 95% interval spans about 0.085. Even a true +0.02 effect would rarely be
  detected.
- **The ceiling is low in this task family.** The terminal decision is the registered
  validator's first elimination. The oracle's headroom over the fixed order is 0.07 externally
  and at most 0.09 in development.
- **Forced-choice contrasts contain the annotated class.** The policy never sees which member is
  true, but the task is built with hidden labels.
- **Wrong-elimination forecasts are too low.** Neither the planner's chance constraint nor any
  forecast-based risk gate should be trusted until they are recalibrated on a separate study.
- **Next experiment.**
  - Pre-register a task where the oracle headroom exceeds twice the MPIE, for example a larger
    dose-by-line menu with a third measurement, or letting the agent decline an elimination and
    confirm it.
  - Draw at least 200 independent new compounds: the full LINCS 2020 Level 5 release, or
    Tahoe-100M after its schema and licence audit.
  - Keep this protocol's firewall and gates, and recalibrate wrong-elimination forecasts on a
    held-out study before using them for control.

## Implementation and tests

| File | Role |
|---|---|
| `src/maestro/planning.py` | the agent's planner: expectimax, Bayes belief update, baseline anchor, risk cap |
| `src/maestro/acquisition.py` | `expected_terminal_decision_value` coherence fix (surgical) |
| `world.py` | empirical-Bayes world model with virtual-cell kernel, feedback conditioning and controls |
| `arms.py`, `replay.py`, `locked.py` | agent arm, sealed replay of ladder and agent, registered runs and vault |
| `external_phase2.py`, `l1000_level5.py` | GSE70138 manifest (metadata only) and in-vault study; Level 5 readers |
| `analysis.py`, `figures.py`, `reproduce.py` | frozen analysis; descriptive figures; reproducibility check |
| `tasks.py`, `devrun.py` | development task loader (historical episode path); development iteration runner |

Tests:
- **Production:** `tests/test_belief_planning.py` (9 tests: coherence, lookahead, refusal,
  anchoring, risk cap, invalid inputs). The full production suite passes: 1,341 tests.
- **Research:** `research/belief_planning/test_belief_planning.py` (10 tests):
  - sealed-view equivalence;
  - held-out-outcome invariance;
  - masked-channel blindness;
  - feedback conditioning;
  - menus equal to the runner's;
  - forecasts never becoming evidence;
  - compatible permuted feedback;
  - unit-left-out readings;
  - a manifest free of labels and outcomes;
  - vault refusals;
  - every registered arm run end to end on a synthetic external study.
- **Full research suite:** 117 of 119 pass. The 2 failures are in
  `research/external_validation/`. Its post-hoc freeze lists `src/maestro/acquisition.py`, which
  the coherence fix changed. Its saved-fold test compares against the rewritten `l1000_T_1`, where
  only the fixed arm `decision_sensitive_edv` now differs (65 of 588 records, 1 terminal decision).

## Reproduction

```powershell
$py = "D:\anaconda\envs\maestro\python.exe"
# checks (the freeze must verify; locked.py refuses otherwise)
& $py -m pytest tests/test_belief_planning.py research/belief_planning -q -p no:cacheprovider
# registered development replay (about 30 minutes on 12 workers) and its analysis
& $py -m research.belief_planning.locked --dev --workers 12
& $py -m research.belief_planning.analysis --records outputs/belief_planning_20260927/registered/dev --out outputs/belief_planning_20260927/registered/dev_analysis --features outputs/belief_planning_20260927/registered/dev/compound_features.csv
# external: already run once; the vault log refuses a second replay
& $py -m research.belief_planning.analysis --records outputs/belief_planning_20260927/external/records.jsonl.gz --out outputs/belief_planning_20260927/external/analysis --features outputs/belief_planning_20260927/external/compound_features.csv
# determinism check against the registered records (any environment with the dependencies)
& $py -m research.belief_planning.reproduce --task sciplex3:A:1 --out tmp/repro.jsonl.gz --compare outputs/belief_planning_20260927/registered/dev
```

- **Data requirements:** the files in [DATA.md](DATA.md) (GSE70138 metadata and Level 5), plus
  the prepared SciPlex3 and L1000 development caches already in `outputs/`.
- **Environment:** Python 3.11.16 (`maestro` conda env), numpy 2.4.6, pandas 2.3.3, scipy 1.17.1,
  scikit-learn 1.9.0, rdkit, h5py.
- **Costs:** no provider calls ($0); no laboratory work (0 wells).
