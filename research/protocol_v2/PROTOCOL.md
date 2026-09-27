# Protocol external-validation-2

**Version:** `external-validation-2`, written 2026-09-27 12:10 (+0800).

**Machine-readable form:** [protocol.json](protocol.json).

**Supersedes:** `external-validation-1` (`research/external_validation/`) and `belief-planning-1`
(`research/belief_planning/`). Both are archived read-only in `research/experiments/`.

**Production default:** unchanged. No protocol-v2 code is imported by `src/`, and a protocol-v2
result cannot change the default. Changing it needs a separate decision after section 7's
criteria are met.

## 1. Question and estimand

**Question.** Does a MAESTRO measurement policy make more correct terminal mechanism decisions than
the fixed expert order, on compounds it has never seen, without more wrong decisions and at no
materially higher laboratory cost?

**Primary estimand.** The paired difference in correct terminal decisions, candidate minus fixed,
on identical episodes. The unit is the independent compound component (identity or Murcko-scaffold
connected component). Intervals are 95% unit-cluster bootstraps: 2,000 draws, seed 20260927,
`research/external_validation/statistics.py`. Episodes, cell lines, doses and replicates are
never units.

**Endpoints**, reported separately and never merged into one score:

| Endpoint | Population | Truth needed | Metrics |
|---|---|---|---|
| Acquisition and stopping | every metadata-eligible compound | no | measurements, assay-days, wells, stop reasons, QC failures, deferral |
| Mechanism correctness | compounds with a reliable post-hoc label whose class is in the reference-defined pool | yes, at scoring only | correct, wrong, deferred, decided, selective risk, net utility |

A mechanism result describes label-compatible compounds only. For GSE70138 that was 38 of 673
new compounds. It is never stated as a result "on unseen compounds" in general.

**Utility** (every arm, one price): correct +1, wrong or exhausted -2, undetermined or deferred 0,
less 0.02 per measurement. The hard assay-day budget is the runner's and is reported separately.

## 2. Data boundary and truth semantics

**Policy view** (`contracts.PublicContext`, a whitelist). An arm receives:
- the training reference tables;
- the validator calibration fitted on those tables;
- the menu and the pool;
- structures and unit keys;
- the planned-condition availability map;
- per-fold caches.

It does not receive held-out labels, profiles, QC fields, detection flags, validator outcomes,
or a label-derived eligibility list. Reaching for any of these raises `AttributeError`.

**Fixed from reference data before any external label is read:**
- the mechanism pool (`contracts.reference_pool`, reference compounds only);
- the candidate contrasts: every pair of pool classes for every metadata-eligible compound
  (`contracts.truth_free_episodes`), never "own class against each decoy";
- test inclusion, from metadata only;
- the action menu, the fixed order, the support rule and the calibration rule.

**Measurement states** (`contracts.MeasurementState`):
- `not_measured` is design metadata. It is never offered, never charged and never scored.
  Choosing it raises `NotMeasured`.
- `quality_failed` is charged and changes no evidence.
- `measured_undetected`, `measured_ambiguous` and `measured_eliminating` are the only biological
  readings.

**Scoring** (`contracts.score`) is the only place a truth meets a trace. A missing truth, or one
outside the episode's contrast, raises `TruthMissing`. Execution traces must not carry a truth.
The mechanism endpoint keeps, at scoring time, the episodes whose contrast contains the compound's
label (`contracts.mechanism_endpoint`).

## 3. Task and power gates

A task may be the primary benchmark only if (`headroom.py`):
- **Headroom:** the oracle-minus-fixed correct difference is at least 2 x MPIE (0.04), and its
  lower 95% bound is at least MPIE (0.02). The oracle reads hidden outcomes and is a bound, never
  a competitor.
- **Power:** the units needed for 80% power at two-sided 5% to detect +0.02 do not exceed the
  units available. The standard error comes from the current planner's paired difference.

Measured on the registered records:

| Task | Units | Oracle - fixed correct | Changeable units | MDE now | Units for +0.02 | Status |
|---|---|---|---|---|---|---|
| SciPlex3 A | 42 | +0.030 [0.000, 0.083] | 0.07 | 0.115 | 1,386 | ineligible (headroom) |
| SciPlex3 B | 132 | +0.086 [0.053, 0.123] | 0.31 | 0.037 | 464 | eligible, underpowered |
| L1000 LT | 256 | +0.062 [0.037, 0.091] | 0.10 | 0.036 | 813 | eligible, underpowered |
| L1000 T | 170 | +0.001 [0.000, 0.003] | 0.02 | 0.006 | 13 (candidate almost identical to fixed) | ineligible (headroom) |
| GSE70138 P2LD | 38 | +0.071 [0.003, 0.153] | 0.11 | 0.060 | 345 | ineligible (lower bound < 0.02) |

"Changeable units" is the share of units in which some legal sequence decides correctly where
fixed did not.

## 4. Arms

Every arm runs through `runner.run_episode`. All arms share the menu, the budget, the executor,
the validator, `EvidenceState`, the seed policy and the unit clustering.

| Arm | Role | Code |
|---|---|---|
| `fixed` | primary comparator | `external_validation/arms.py fixed` |
| `random_legal` | lower bound | `external_validation/arms.py random_legal` |
| `myopic_edv` | non-agent model baseline | `external_validation/arms.py myopic_edv` |
| `belief` | current planner | `belief_planning/arms.py belief_arm()` |
| `anchored` | current planner with the 1.645-SE anchor | `belief_arm(anchor=True)` |
| `safe` | **primary v2 candidate** | `safe.py safe_arm(gate_novelty=True)` |
| `safe_class` | sensitivity (no applicability gate) | `safe_arm(gate_novelty=False)` |
| `belief_robust` | robustness (contamination-mixture update, eps = 0.3) | `belief_arm(contamination=0.3)` |
| `oracle` | upper bound | `external_validation/arms.py make_oracle` |

**Support rule of `safe`.** Every threshold is an existing registered constant.
- A departure from the fixed action needs both actions supported. For each hypothesis that means:
  - at least 6 independent reference units at the condition;
  - a history-weighted support of at least 6;
  - at least 2 detected validator templates.
- The compound must sit in the structural applicability domain (nearest training Tanimoto of at
  least 0.40).
- The validator must be able to eliminate, and there must be no uncalibrated study shift.
- The gain must exceed 1.645 standard errors.
- There must be no increase in forecast wrong risk: point estimate within +0.005, and the
  conservative bound not higher.
- A refused forecast never becomes a stop. A model-driven stop needs the calibration gate
  (section 5) and a supported, confidently negative value for the fixed action.

## 5. Calibration and control

`calibration.py` compares, leave-one-study-out (SciPlex3 to L1000 and L1000 to SciPlex3):
- the raw forecast;
- the planner's own conservative bound;
- Platt recalibration;
- a hierarchical stratum rate (support x novelty x step, pooled with 20 pseudo-observations);
- its 95% bound;
- the same bound with the source evidence halved (power prior).

GSE70138 is reported post hoc only.

**Stop gate.** The model may drive a stop only if its bound covers the observed wrong rate on
both development targets: overall, in at least 95% of strata with 20 or more items, and with no
stratum significantly above it.

**Result, recorded before the screen ran.** The gate passes, but only for the planner's own bound,
which is 10-35 times the observed rate. The hierarchical and discounted bounds fail on SciPlex3
and, post hoc, on GSE70138. So a recalibrated wrong risk may not be used for control. Stops stay
conservative: under-forecast wrong risk overstates the value of continuing, not of stopping.

## 6. Immutable evidence and replay plan

**Registration.** `registry.register`:
- refuses a dirty tree and an existing record;
- hashes tracked files as LF-normalised content and untracked data as raw bytes;
- records the commit, the environment lock (interpreter, platform, BLAS, every installed
  distribution with one digest), the command and the seed;
- writes the record once and read-only.

A development run on a dirty tree gets `registry.development_record`, marked
`registered: false`. It is a disclosure, never a registration.

**To register an experiment:**

```powershell
git switch -c protocol-v2
git add research/protocol_v2 research/experiments <edited files>
git commit -m "Protocol external-validation-2"
git tag belief-planning-1 83b9aa9          # optional, owner's decision
& D:\anaconda\envs\maestro\python.exe -c "from research.protocol_v2 import registry as G; G.register(...)"
```

**Replay.** A registered experiment is replayed from a worktree at its commit
(`registry.replay_instructions`), never from the moving working tree. Integrity is checked at the
decision level (`registry.compare_decisions`):
- chosen actions, stop reason, readings, eliminations, terminal decision and measurements must
  match exactly;
- numeric diagnostics must match within 1e-8.

**Protocol-v1 evidence** is digested in `research/experiments/{external-validation-1,
belief-planning-1}/EVIDENCE.json`:
- freezes, with their verification at `83b9aa9` and whether they came from a dirty tree;
- every replay fold, with its registered record count and a status;
- the vault log and its single opening;
- the external records.

The 49 untracked originals are read-only. `test_archived_evidence_is_unchanged` fails if any of
them changes.

## 7. Pre-registered success and failure criteria

A candidate improves on fixed only if **all** of these hold on independent units in one run:
1. Correct difference estimate >= +0.02.
2. Correct difference lower 95% bound > 0.
3. Wrong difference upper 95% bound <= +0.005, and the candidate's wrong-rate upper bound <= 0.05.
4. Measurement difference upper bound <= +0.10 per episode, and assay-day difference upper bound
   <= +0.6.
5. The correct difference is positive in every sensitivity stratum with >= 50 units (Murcko
   scaffold seen or held out, study, batch, cell-line overlap, structural applicability). Its lower
   bound stays > 0 when re-clustered by scaffold and by batch.
6. Independent units >= the confirmatory minimum: the larger of 500 and the power model's
   requirement for the chosen task.
7. The registration verifies at its commit, the vault opened once, and the decision-level replay
   is identical.

**Failure** (any one):
- the correct difference upper bound is below +0.02 (a practical gain excluded);
- the upper bound is below -0.01 (inferior);
- the wrong difference lower bound is above +0.005;
- the gain appears in one stratum, study or batch only;
- the candidate buys fewer measurements without more correct decisions.

Below 200 units only INCONCLUSIVE or descriptive statements are allowed.

**Integrity failures invalidate a conclusion, whatever its numbers:**
- a truth-less or out-of-contrast score;
- a digest mismatch at the registration commit;
- a rewritten registration or replay;
- a policy that received held-out data;
- a replay mismatch;
- an unregistered external file read after registration;
- a not-measured condition executed.

The virtual cell and feedback are promoted only with verdict `KEEP` (`attribution.py`):
- action change > 0 and decision change > 0;
- correct gain >= 0.02 with a lower bound > 0 against every control (masked and permuted, or
  withheld and permuted);
- wrong difference upper bound <= 0.005 and measurement difference upper bound <= 0.10.

Anything short of `KEEP` stays an audit or research feature.

## 8. Experiment matrix

| Experiment | Data | Status |
|---|---|---|
| Headroom and power per task | registered v1 records | done (section 3) |
| Identifiability and second-step ceilings | v2 development outcome tables | done (README) |
| Leave-one-study-out calibration and stop gate | registered v1 records | done (section 5) |
| Virtual-cell and feedback gates | registered v1 records | done: REJECT_AS_DEFAULT everywhere |
| Development screen of all arms | 20 development tasks | done: `safe` SAFE_ON_DEVELOPMENT, NO_DEVELOPMENT_SIGNAL |
| External confirmation | an unopened study, >= 345-813 label-compatible units, a task that passes section 3 | **blocked**: no such study is local; GSE70138 is consumed |
| Confirmation-step (three-measurement) task | replicate-level readings, so a repeat is a new realisation | **blocked** |
| Study-held-out virtual cell | a study pair with >= 200 units on a shared task | **blocked** (96 episodes) |
| Cell-line-held-out policy | references without the test line | **blocked** (no such development task) |
| Continuous or discriminating world model | the first task that passes section 3 | deferred until then |
| Stochastic logging and doubly robust off-policy evaluation | wet-lab data with logged propensities | deferred; exact replay is used for replay data |

**Candidates for the external study.** Each count and audit uses metadata only, before any
outcome is read:
- LINCS 2020 Level 5 compounds absent from GSE92742 and GSE70138 by identity and InChIKey block;
  first a metadata-only count of label-compatible units against a reference-defined pool;
- a Tahoe-100M subset after its schema, licence and training-overlap audit (State was trained on
  Tahoe).
