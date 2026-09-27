# Protocol external-validation-2: can MAESTRO show decision value over the fixed expert order?

**Date:** 2026-09-27, 11:30-13:30 (+0800). Block 3 of `log/20260927/README.md`.

**Documents:**
- [PROTOCOL.md](PROTOCOL.md): the protocol-v2 specification.
- [DIAGNOSIS.md](DIAGNOSIS.md): evidence table, diagnosis, decision table and status of
  conclusions.
- [LITERATURE.md](LITERATURE.md): the method review.

**Outputs:** `outputs/protocol_v2_20260927/` (not tracked). Small copies are in
`log/20260927/0927/`.

## Answer

**Not yet, and not with the data in this repository.** No MAESTRO policy meets any protocol-v2
success criterion. The binding constraints are the tasks, not the planner:

1. **The fixed order already makes most of the decisions any policy could make.** It reaches
   63% (L1000 LT) to 99.6% (L1000 T) of the oracle's correct decisions. SciPlex3 A and L1000 T
   fail the headroom gate, so a +0.02 gain there is impossible by construction.
2. **Most L1000 episodes cannot be decided at all.** In 76-82% of them no planned condition
   eliminates either hypothesis.
3. **Too few independent units.** Detecting +0.02 needs 464 (SciPlex3 B-like), 813 (L1000
   LT-like) or 345 (GSE70138-like) units. The tiers have 42-256, and GSE70138 had 38.

A **baseline-safe planner** removes every development loss of the current planner, including
SciPlex3 A's -0.131. It does so by almost never leaving the fixed order: 0-0.24% of decisions.
The reference data rarely support a departure. The fixed action's forecast lacks support in 49%
(A), 58% (B), 79% (LT) and 8% (T) of decisions.

**The production default is unchanged.**

## What was built

| File | Role |
|---|---|
| `contracts.py` | Measurement states. Fail-closed scoring (`score`, `TruthMissing`). Whitelisted public policy view (`PublicContext`). Reference-defined pools and truth-free all-pairs episodes. |
| `runner.py` | Truth-free episode runner on the public view: availability menus, `NotMeasured`, and validator scores kept out of the arm's view. |
| `registry.py` | Clean-tree registration, write-once and read-only records, the environment lock, LF-normalised digests, verification at the registration commit, decision-level replay comparison. |
| `archive.py` | One-time evidence archive of both protocol-v1 experiments (`research/experiments/*/EVIDENCE.json`); sets the originals read-only. |
| `safe.py` | The baseline-safe (SPIBB-style) research arm and its multi-factor support rule. |
| `headroom.py` | Oracle headroom, changeable units, power and the task gate. |
| `calibration.py` | Leave-one-study-out wrong-risk calibration (raw, planner bound, Platt, hierarchical, discounted), the stop gate, and contamination-mixture belief updates. |
| `attribution.py` | The virtual-cell and feedback decision gates. |
| `run_dev.py`, `screen.py` | The pre-registered development screen and its analysis. |
| `records.py` | Streaming record loader. |
| `protocol.json` | The machine-readable protocol, including the development screen registered before it ran. |
| `test_protocol_v2.py` | 24 tests. |

Changes outside the package are listed in DIAGNOSIS.md section 5. They are:
- fail-closed scoring;
- a truth guard in `episode_list`;
- `belief_state` extracted in `belief_planning/arms.py`;
- two historical tests repointed to real evidence;
- eight unreferenced aliases or functions removed.

## Results

### Development screen (20 tasks, 12,428 episodes, 111,852 records, 0 integrity problems)

The screen reused belief-planning-1's episodes. Its record is `development_unregistered`: the
tree was dirty, and every tier had been analysed before. It can rule arms out, not in.

**Replay check.** Arms shared with belief-planning-1 reproduced its registered decisions exactly.
The only exception is 12 mismatches in SciPlex3 A, all on compounds with an unplanned condition,
which v2 no longer offers.

Correct / wrong / deferred / measurements, and the paired correct difference against fixed:

| Tier (units) | fixed | belief | safe | anchored | myopic_edv | oracle |
|---|---|---|---|---|---|---|
| SciPlex3 A (42) | 0.640 / 0.057 / 0 / 1.63 | 0.509 / 0.042 / 0 / 1.62; **-0.131 [-0.214, -0.054]** | 0.640 / 0.057 / 0 / 1.63; **0.000** | 0.640; 0.000 | 0.443; -0.196 | 0.670 |
| SciPlex3 B (132) | 0.582 / 0.049 / 0 / 1.52 | 0.590 / 0.038 / 0 / 1.50; +0.008 [-0.018, +0.035] | 0.582 / 0.049 / 0 / 1.52; 0.000 [-0.002, +0.002] | 0.582; 0.000 | 0.529; -0.053 | 0.668 |
| L1000 LT (256) | 0.106 / 0.006 / 0 / 1.93 | 0.131 / 0.006 / 0.20 / 1.37; +0.024 [0.000, +0.050] | 0.106 / 0.006 / 0 / 1.93; 0.000 | 0.107; +0.000 | 0.120; +0.014 | 0.168 |
| L1000 T (170) | 0.230 / 0.011 / 0 / 1.85 | 0.224 / 0.009 / 0 / 1.70; -0.006 [-0.010, -0.002] | 0.230 / 0.011 / 0 / 1.85; 0.000 | 0.230; 0.000 | 0.202; -0.028 | 0.231 |

**Pre-registered decisions:**

| Arm | Development safety | Development signal |
|---|---|---|
| `safe` (primary) | SAFE_ON_DEVELOPMENT | NO_DEVELOPMENT_SIGNAL |
| `safe_class` | SAFE_ON_DEVELOPMENT | NO_DEVELOPMENT_SIGNAL |
| `belief` | UNSAFE (SciPlex3 A, B) | NO_DEVELOPMENT_SIGNAL |
| `belief_robust` | UNSAFE (SciPlex3 A, B) | NO_DEVELOPMENT_SIGNAL |
| `anchored` | SAFE_ON_DEVELOPMENT | NO_DEVELOPMENT_SIGNAL |
| `myopic_edv` | UNSAFE (all) | NO_DEVELOPMENT_SIGNAL |

**Notes on the current planner (`belief`):**
- Its L1000 LT advantage comes from deferring 20% of episodes at the first step, which cuts
  measurements. The support rule does not license those stops.
- Net utility is +0.036 over fixed in LT and +0.029 in B, a cost trade that protocol v2 does not
  count as improvement.
- The fixed order's own wrong-rate upper bound is 0.107 (A) and 0.068 (B), and the current
  planner's is 0.080 and 0.054. Only arms that decide less often (`myopic_edv`, `random_legal`)
  stay under the 0.05 cap in SciPlex3 B. At these unit counts the cap can rarely be certified.

### How much any policy could gain

| Tier | Identifiable | Conflicting | Misleading | Unidentifiable with this menu | Second-step ceiling after fixed's first (share of episodes) |
|---|---|---|---|---|---|
| SciPlex3 A | 0.622 | 0.048 | 0.045 | 0.286 | 0.024 (63%) |
| SciPlex3 B | 0.606 | 0.062 | 0.050 | 0.282 | 0.149 (52%) |
| L1000 LT | 0.166 | 0.002 | 0.016 | 0.816 | 0.066 (94%) |
| L1000 T | 0.227 | 0.005 | 0.010 | 0.759 | 0.000 (85%) |

**Column definitions:**
- *Identifiable*: some planned condition removes only the wrong hypothesis.
- *Misleading*: only the true hypothesis can be removed.
- *Second-step ceiling*: after the fixed first measurement read nothing, how often some legal
  second measurement would have decided correctly, less how often fixed's own second did.

Feedback can only earn value inside that ceiling. It is real in SciPlex3 B and L1000 LT, and the
current planner converts none of it.

### Calibration of wrong eliminations (registered belief-planning-1 steps)

| Target (source) | Items / units | Observed | Raw forecast | Platt | Hierarchical 95% bound: strata covered | Planner bound (mean) |
|---|---|---|---|---|---|---|
| L1000 (SciPlex3) | 14,575 / 284 | 0.0045 | 0.0023 | 0.0081 | 100% | 0.158 |
| SciPlex3 (L1000) | 3,756 / 134 | 0.0258 | 0.0114 | 0.0083 | 48% (7 strata significantly above) | 0.381 |
| GSE70138 (both, post hoc) | 604 / 38 | 0.0265 | 0.0053 | 0.0124 | 54% | 0.251 |

**Belief collapse.** The posterior on the truth fell below 0.1 after one reading in only 0.3-0.5%
of first readings. A contamination-mixture update (eps = 0.3) lowers the log loss slightly (L1000
0.640 to 0.636, SciPlex3 0.761 to 0.735) and removes the collapse. It changes almost no decision
(`belief_robust` against `belief` in the screen).

### Virtual cell and feedback (recomputed from the registered records)

| Setting | Virtual cell: action / decision change; correct difference | Feedback: action / decision change; correct difference | Verdict |
|---|---|---|---|
| SciPlex3 A | 0.045 / 0.006; +0.000 [-0.009, +0.009] | 0.324 / 0.042; -0.012 [-0.036, +0.009] | both REJECT_AS_DEFAULT |
| SciPlex3 B | 0.032 / 0.004; -0.002 [-0.005, +0.000] | 0.257 / 0.036; +0.003 [-0.004, +0.011] | both REJECT_AS_DEFAULT |
| L1000 LT | 0 / 0; 0 | 0.069 / 0.006; +0.002 [-0.000, +0.006] | both REJECT_AS_DEFAULT |
| L1000 T | 0 / 0; 0 | 0.033 / 0.001; -0.000 [-0.001, +0.000] | both REJECT_AS_DEFAULT |
| GSE70138 | 0.011 / 0; 0 | 0.234 / 0.026; -0.005 [-0.024, +0.011] | both REJECT_AS_DEFAULT |

Neither channel is in the production default; both remain research and audit features.

## Reproduction

```powershell
$py = "D:\anaconda\envs\maestro\python.exe"
& $py -m pytest research/protocol_v2 -q -p no:cacheprovider
& $py -m research.protocol_v2.headroom --records outputs/belief_planning_20260927/registered/dev --records outputs/belief_planning_20260927/external/records.jsonl.gz --out outputs/protocol_v2_20260927/headroom_registered.json
& $py -m research.protocol_v2.calibration --out outputs/protocol_v2_20260927/calibration_registered.json
& $py -m research.protocol_v2.attribution --out outputs/protocol_v2_20260927/attribution_registered.json
& $py -m research.protocol_v2.run_dev --workers 16          # about 4 minutes; writes a write-once run record
& $py -m research.protocol_v2.screen --out outputs/protocol_v2_20260927/dev_screen_analysis.json
```

- **Environment:** Python 3.11.16 (`maestro` conda env), numpy, pandas, scipy, scikit-learn,
  rdkit, threadpoolctl. The environment lock is in `outputs/protocol_v2_20260927/dev/run_record.json`.
- **Costs:** no provider calls ($0); no laboratory work (0 wells).
