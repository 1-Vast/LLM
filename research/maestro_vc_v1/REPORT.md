# MAESTRO-VC v1: an evidence-grounded case memory for the agent and virtual-cell loop

**File summary**
- **Path:** `research/maestro_vc_v1/REPORT.md`
- **Purpose:** the reproducible report of the 2026-09-29 investigation: a structured case memory, adaptive
  retrieval, a hypothesis graph, hypothesis-conditional forecasts and a closed-loop decision-support system,
  evaluated by replaying 6,601 real episodes, with an honest answer to whether the memory improves
  calibration, action selection, terminal decisions, efficiency, robustness to unseen contexts and
  resistance to misleading similarity.
- **Core points:**
  - **It does not improve the terminal decision.** No arm shows a development signal; no case-memory arm
    exceeds the fixed expert order by 0.02 in any tier (`cm_full` is 0.05 below it in SciPlex3 A), and
    only tier B has enough headroom (0.072) to show a gain at all.
  - **It does not improve forecast calibration.** Every memory world forecasts held-out readings with NLL
    0.432 to 0.433 and none differs detectably from the current reference world; on the actions a planner
    chooses, wrong-elimination risk is still under-forecast about 2.4 times.
  - **Failure and negative cases are essential.** Removing them raises forecast NLL by 5.02 nats
    [4.76, 5.28]; removing only the misleading readings leaves NLL nearly unchanged (+0.021) but makes the
    forecast of a wrong elimination 88 times too low.
  - **Adaptation works where it has work to do.** For a condition the memory has never read, borrowing
    the class's readings from other conditions beats pooled frequencies by 0.082 nats [0.054, 0.110]; the
    priced cost ranks sources correctly (Spearman 0.50), but pricing adds nothing over choosing the nearest.
  - **A hypothesis-conditional forecast is worth having; a scalar one is not.** Discrimination is 0.60 nats
    against 0 by construction, and choosing by predicted magnitude alone is harmful (correct decisions
    -0.172 [-0.296, -0.051] against the fixed order in SciPlex3 A).
  - The system, the memory, the data products and the audits are complete and tested; the evidence is
    development-grade only, because no untouched study exists locally.
- **Interfaces / data:** `research/scientific_case_memory/`, `research/maestro_vc_v1/`,
  `data/processed/maestro_vc_v1/`, `data/manifests/maestro_vc_v1_manifest.json`,
  `outputs/scientific_case_memory/`, `outputs/maestro_vc_v1/`.
- **Depends on:** [AUDIT.md](AUDIT.md), [protocol.json](protocol.json) and its freeze records.

Statements below are labelled by what they rest on: **measured** (a replay record or a file), **model
prediction**, **analogy** (a retrieved precedent) or **speculation**. A number without a label is measured.

## 1. The answer, question by question

| Question | Verdict | Measured evidence |
|---|---|---|
| Does the memory improve **prediction calibration**? | **No.** | Forecast NLL over 49,304 held-out items: `cm_full` minus the current world `+0.0009` [-0.0003, +0.0020]; SciPlex3 A is worse (+0.019 [+0.007, +0.035]). Overall wrong-elimination ratio observed to forecast is 1.06 to 1.07 for every non-ablated world; on chosen actions it is 2.35 to 2.46 for every planner (fixed order 0.91). |
| **Action selection**? | **No.** | Against the fixed order, the correct-decision difference of `cm_full` is -0.050, -0.016, +0.008, -0.008 (A, B, LT, T), none of the intervals reaches the +0.02 gain threshold; the retrieved prior changes 7 to 11% of first actions and 1 to 4% of decisions. |
| **Terminal decision accuracy**? | **No.** | All 23 arm-by-comparator screens return `NO_DEVELOPMENT_SIGNAL`. Headroom (oracle minus fixed) is 0.038, 0.072, 0.042, 0.003; only tier B passes the gate, and there `cm_full_prior` is -0.011 [-0.034, +0.014] against fixed. |
| **Experimental efficiency**? | **Not by the memory; yes by the planner.** | In L1000 LT the belief planner already defers 59% of episodes at step 0 and saves 1.33 measurements per episode (its deferrals are licensed 96% of the time). The memory adds -0.056 measurements and +0.0077 [+0.002, +0.015] correct on top: real but far below the 0.02 gain threshold. |
| **Robustness to unseen contexts**? | **Adaptation yes; retrieval no.** | Unseen-condition stress test: adapted forecast minus pooled `-0.082` [-0.110, -0.054] NLL; adapted minus naive borrowing `+0.0001` [-0.0036, +0.0035]. Structural novelty makes every world worse (NLL 0.461 novel against 0.386 familiar) and no world differs. |
| **Resistance to misleading similarity**? | **Not testable here.** | Only 18 units have a close structural neighbour of another class (fewer than 10 per tier), so the pre-registered interaction cannot be estimated; forecast NLL in that stratum is identical across worlds (0.550). In the second case family, semantic similarity is uninformative (below). |
| Value of **failure and negative cases**? | **Yes, decisively.** | Removing both: NLL +5.02 [+4.76, +5.28]; misleading only: +0.021 [+0.014, +0.031] and a wrong-elimination ratio of 88; negative only: +4.99 [+4.73, +5.25]. At the decision level, `cm_nofail` loses 0.17 correct in tiers A and B. |
| **Hypothesis-conditional** against **scalar** virtual-cell prediction? | **Conditional wins as a forecast; neither wins as a policy.** | Discrimination 0.60 nats [0.47, 0.74] against 0; NLL 0.432 against 0.589. Choosing by scalar magnitude changes the first action in 99 to 100% of SciPlex3 episodes and loses 0.17 correct decisions in tier A (B and LT are not distinguishable from 0); the in-context virtual cell (`vc_incontext`) changes 0 to 3% of decisions and matches the belief planner. |

What the memory does add, measured: a **hypothesis prior from retrieved precedents** with log-loss 0.452
against 0.693 for a uniform prior [0.414, 0.490], informative in 40% of episodes and favouring the true class
in 98.8% of those; a **closed-loop update** that lowers the NLL of later compounds by 0.0034 nats
[-0.0067, -0.0003]; and an answer format that states its abstentions.

## 2. What was built

Two packages, both research-only (nothing under `src/` changed), 66 tests, all passing.

| Module | Role |
|---|---|
| `scientific_case_memory/case_schema.py` | `Case` with every field of the design, typed measurement status, evidence classes, digests, `validate_case` naming each structural error, and `OpenProblem` (no truth field). |
| `case_store.py` | Append-only, digest-chained store; supersede-not-edit; tamper detection; timestamp-free gzip so file hashes are reproducible. |
| `case_index.py`, `case_retrieval.py` | Reading-code tables from cases only; stage 1 hard compatibility with named reasons; stages 2 to 4 with the nine-term `case_score` and a reason for every retrieved case. |
| `adaptation_model.py` | Difference signatures, a table of transfer successes, relative cost, declared prior only where history is missing. |
| `world.py` | `CaseMemoryWorld`: hypothesis-conditional forecasts, with a parity test proving it equals the reference world when its extensions are off. |
| `hypothesis_graph.py`, `evidence_cards.py`, `protocol_library.py` | Layered graph with registered and advisory hypotheses; the six evidence classes with promotion refused; costed protocol templates. |
| `build_cases.py`, `build_episode_replay.py`, `case_quality_audit.py`, `evaluate_*.py` | Fold-scoped case building and typing; replay integrity and a leak probe; ten audit checks; forecast-level and decision-level evaluation. |
| `maestro_vc_v1/` | Sources with verified-or-`unverified` provenance; preprocessing validation; the five tables and the policy and evaluator views; the second case family; the replay, arms and analysis; the stress and update tests; the decision-support system; figures. |

Data products (`data/manifests/maestro_vc_v1_manifest.json` names every file and its SHA-256):
state tables (SciPlex3 2,444 rows, L1000 3,390 rows), intervention tables, a 684-row transcriptome-viability bridge,
an evidence table of 49,304 real readings, 6,601 policy-view and 6,601 evaluator-view episodes, four full case libraries (88, 135, 442
and 218 cases), 20 fold snapshots, the second family (64 cases), 44 bridge cases and a 947-row case table.

## 3. Data, provenance and validation

**Measured.** All eleven validation checks pass (`outputs/maestro_vc_v1/preprocess/validation_report.json`):

- **SciPlex3 feature-label offset.** The first published label of the raw release is `id gene_short_name`
  (read from the file). The identity-marker check accepts the prepared labels at offset 0 and, given
  labels shifted by one row, recovers the offset of 1 and refuses offset 0, so the check discriminates.
- **Gene identifiers.** All 2,473 SciPlex3 symbols and 978 L1000 landmark genes join to HGNC with no
  Entrez or Ensembl disagreement.
- **Compounds.** 188 and 478 structures parse; recomputed InChIKey connectivity blocks equal the stored
  independent-unit blocks in every case; three and ten identity blocks are shared by more than one compound.
- **Controls and batches.** Every treated (cell line, time) group has at least 8 vehicle wells and no
  control carries a dose. L1000 Level 5 signatures are normalised against plate population controls, so
  per-condition control matching is a property of the release and cannot be checked here.
- **Splits.** No independent unit, identity block or scaffold spans two folds.
- **Status.** SciPlex3: 918 qualified, 1,493 undetected, 21 QC-failed, 12 planned-missing conditions.
  L1000 (within the prepared scope of four cell lines): 307 qualified, 3,082 undetected, 1 QC-failed. A
  missing or failed condition is a status with no value.

**Public cross-checks** (`data/external/public_checks_20260929/`, metadata queries only, no data file
downloaded):

- Figshare licences: DepMap 24Q2 and PRISM 19Q4 are CC BY 4.0; SciPlex3 is CC BY 4.0 (the first query
  failed transiently and was retried); the local SciPlex3 file's recomputed MD5 equals Figshare's.
- PubChem: 118 of 120 sampled compound names resolved; the connectivity block agrees with the
  structure-derived block in 106 (89.8%). Nine of the 12 disagreements carry a salt or hydrate suffix in
  the name (Citrate, HCl, Ditosylate and similar); three (thioperamide, clobetasol, fluocinolone) are
  unexplained and were not corrected.
- ChEMBL: 13 of the 53 compounds of the genetic-pharmacological cases have a curated mechanism. By my
  reading of the strings, 12 name the same target as the PRISM annotation; triclabendazole is unsupported
  (PRISM DNMT1 and microtubule inhibitor against ChEMBL "Unknown"). The automated matcher counted only 1
  exact string agreement because ChEMBL spells out protein names; the counts above are a manual judgement.
  Forty compounds have no ChEMBL mechanism.

Sources without a stated licence in a local record carry the literal `unverified` (`kinobeads`, the
case packages, GEO series); nothing was filled in from memory.

## 4. The case memory

**Measured** (four full libraries and the second family):

| Kind | SciPlex3 A | SciPlex3 B | L1000 LT | L1000 T | Second family |
|---|---|---|---|---|---|
| canonical | 68 | 117 | 106 | 69 | 7 |
| contrastive | 0 | 2 | 1 | 0 | 36 |
| failure | 20 | 16 | 335 | 149 | 21 |
| adaptation records | 16 | 16 | 16 | 8 | 0 |

Typing rules were fixed before the replay: a **failure** case is undetected at every measured condition or
has at least a quarter of its readings matching a decoy; a **contrastive** case has a structural neighbour
of another class and another unit at Tanimoto 0.50 or more. Because most L1000 compounds are never
detected, 76% of L1000 LT cases are failures by the first rule: they are negative cases, the ones the
ablation shows the memory cannot do without. Reading kinds across the SciPlex3 B library: 7,255
canonical, 317 misleading, 14,784 negative, 3,484 ambiguous.

The second family holds the 58 typed-premise genetic-pharmacological cases and the 6 engagement cases,
each with a layered hypothesis graph (two registered hypotheses, three advisory ones) and its unmeasured
layers named: in every case target engagement, proximal function, pathway state and cellular state are
`not_planned`. A processed public record that is not condition-matched is `ambiguous`, never `qualified`.

**Typed bridges (measured).** `bridges.py` links each compound's transcriptomic reading in a cell line to its
fitted PRISM viability in the same line, by InChIKey connectivity block and cell line, and keeps the two as
separate typed observations (A549, MCF7 and PC3; K562 and VCAP are not in the PRISM secondary screen): 684
compound-by-cell-line pairs over 267 compounds. Stronger responses go with more killing (Spearman -0.43 to
-0.53 per dataset and line), yet of 277 pairs with a detected response 132 (48%) have an inactive AUC (0.85 or
more) and 41 (15%) an active one (0.60 or less); of 407 undetected pairs 19 (5%) are active. Using the case
package's declared thresholds, 44 discordant pairs (25 response without phenotype, 19 phenotype without
response) were written as contrastive cases with an unavailable engagement action. The two records are not
dose- or time-matched (a 24 h top-dose transcriptome against a dose-range AUC after a longer exposure), so the
bridge records a disagreement and cannot say why.

**Retrieval on the second family** (descriptive; 58 cases, 40 genes, leave-one-target-gene-out; pattern
labels are derived from the same numeric features, so the pattern retrievers are circular by construction).
Semantic similarity (same compound or lineage) predicts the evidence pattern with accuracy 0.103
[0.035, 0.196], below the majority-pattern share of 0.207; the nearest semantic neighbour shares the
pattern in 13.8% of cases. **Analogy:** the two numeric retrievers recover the pattern at 0.62 and 0.72,
which is expected of features that define it and is not evidence of transferability.

## 5. The decision-support system

`research/maestro_vc_v1/system.py` implements the ten steps for the transcriptomic problem. Worked
examples on real held-out episodes are in `outputs/maestro_vc_v1/examples/`, each chosen by a rule fixed
beforehand:

- `informative_prior`: an in-domain compound with a supported prior.
- `misled_prior`: the retrieved prior favours the wrong class (0.84, from a single neighbour at
  similarity 0.425). The answer keeps the prior advisory, labels the outcome that would contradict it
  `contradictory_to_precedent`, and states that the prior rests on fewer than two effective precedents.
  The real reading was unresolved, so no hypothesis was removed.
- `no_decisive_action`: an L1000 fold whose validator cannot eliminate. Every forecast eliminating
  probability is below 0.005 with 12 to 22 supporting units; the system abstains with a named reason,
  says the finding is about the menu and not about the memory, and recommends extending the menu.

The examples exposed two defects, both fixed: the answer did not say when a prior rested on one weak
neighbour, and it described a well-supported "nothing can decide" forecast as a lack of support.

Closing the loop is tested (`test_ingest_supersedes_the_case_and_grades_the_forecast_append_only`): a QC
failure updates no hypothesis, an undetected reading removes nothing, a qualified reading removes one
hypothesis through the registered rules, the compound's case is superseded and never edited, and the
probability the system gave the realised reading is stored as a calibration entry.

## 6. Design of the replay

Fixed before the run in [protocol.json](protocol.json) and hashed in `freeze.json` (49 files) at
2026-09-29 11:47:01. Episodes are protocol v2.1's forced-choice contrasts on the 20 development tasks (SciPlex3
A and B, L1000 LT and T, five folds each): 6,601 episodes, 334 independent units. Fourteen arms ran through the
registered runner: `fixed`, `random_legal`, `coverage`, `scalar_vc`, `belief_class`, `belief_similarity`,
`cm_similarity_unitout`, `cm_full`, `cm_full_prior`, `cm_full_prior_anchored`, `cm_nofail`, `prior_only`,
`vc_incontext`, `oracle`. Zero integrity problems in any task; the case-memory belief arm reproduces the
existing belief arm's decisions exactly (0 mismatches over 61 real episodes with the structure kernel active)
and the case-memory world reproduces the existing world's forecasts exactly (maximum difference 0).

**Disclosure.** Every tier has been analysed repeatedly since 2026-09-26 and GSE70138 was opened, so this
replay can rule arms out and cannot rule any in. Before the freeze I had seen the training-side fits of six
tasks and a smoke run of two (which is why the failure ablation was split into two worlds). Nothing was seen
of the other 18 tasks, and no pooled or per-tier result existed.

## 7. Results

### 7.1 Terminal decisions (measured)

Correct / wrong / measurements per episode:

| arm | A | B | LT | T |
|---|---|---|---|---|
| `fixed` | 0.636 / 0.059 / 1.59 | 0.620 / 0.040 / 1.50 | 0.058 / 0.004 / 1.98 | 0.244 / 0.015 / 1.84 |
| `belief_similarity` | 0.582 / 0.046 / 1.38 | 0.603 / 0.031 / 1.49 | 0.066 / 0.002 / 0.65 | 0.235 / 0.015 / 1.68 |
| `cm_full` | 0.586 / 0.046 / 1.38 | 0.603 / 0.031 / 1.49 | 0.066 / 0.002 / 0.65 | 0.235 / 0.015 / 1.68 |
| `cm_full_prior` | 0.590 / 0.046 / 1.39 | 0.609 / 0.032 / 1.48 | 0.073 / 0.001 / 0.59 | 0.235 / 0.015 / 1.59 |
| `cm_full_prior_anchored` | 0.636 / 0.059 / 1.42 | 0.621 / 0.039 / 1.50 | 0.058 / 0.003 / 1.31 | 0.244 / 0.015 / 1.84 |
| `vc_incontext` | 0.569 / 0.038 / 1.38 | 0.602 / 0.027 / 1.49 | 0.066 / 0.002 / 0.64 | 0.234 / 0.015 / 1.64 |
| `scalar_vc` | 0.464 / 0.017 / 1.59 | 0.592 / 0.034 / 1.45 | 0.035 / 0.002 / 1.98 | 0.244 / 0.015 / 1.84 |
| `cm_nofail` | 0.464 / 0.008 / 1.40 | 0.453 / 0.023 / 1.63 | 0.028 / 0.000 / 1.32 | 0.244 / 0.015 / 1.83 |
| `oracle` | 0.674 / 0.000 / 0.67 | 0.692 / 0.000 / 0.69 | 0.100 / 0.000 / 0.10 | 0.247 / 0.000 / 0.25 |

Paired difference in correct decisions against `fixed` (95% unit-cluster interval, 2,000 draws):

| arm | A | B | LT | T |
|---|---|---|---|---|
| `belief_similarity` | -0.054 [-0.118, +0.016] | -0.016 [-0.040, +0.009] | +0.008 [-0.018, +0.035] | -0.008 [-0.018, -0.001] |
| `cm_full` | -0.050 [-0.110, +0.017] | -0.016 [-0.040, +0.009] | +0.008 [-0.018, +0.035] | -0.008 [-0.018, -0.001] |
| `cm_full_prior` | -0.046 [-0.107, +0.024] | -0.011 [-0.034, +0.014] | +0.015 [-0.008, +0.043] | -0.008 [-0.017, -0.001] |
| `cm_full_prior_anchored` | +0.000 [+0.000, +0.000] | +0.001 [-0.004, +0.005] | +0.001 [+0.000, +0.001] | +0.000 [+0.000, +0.000] |
| `vc_incontext` | -0.067 [-0.141, +0.008] | -0.018 [-0.042, +0.008] | +0.008 [-0.018, +0.035] | -0.010 [-0.019, -0.002] |
| `scalar_vc` | -0.172 [-0.296, -0.051] | -0.028 [-0.069, +0.012] | -0.023 [-0.051, +0.004] | +0.000 [+0.000, +0.000] |
| `cm_nofail` | -0.172 [-0.304, -0.041] | -0.167 [-0.220, -0.116] | -0.030 [-0.062, +0.002] | +0.000 [+0.000, +0.000] |

The pre-registered screens: every arm returns `NO_DEVELOPMENT_SIGNAL` against both `fixed` and
`belief_similarity`. The only arm that is `SAFE_ON_DEVELOPMENT` against `fixed` is `cm_full_prior_anchored`,
which by construction almost never leaves the expert order. Regret against the oracle is essentially the
headroom: for the arms above it is 0.155 to 0.243 in A and 0.145 to 0.286 in B (the two ablation and scalar
arms are the worst).

**Abstention quality (measured).** Delay is a success when the oracle could not decide correctly either. The
planners' delays are licensed 78 to 82% of the time in SciPlex3, 96 to 97% in L1000 LT and 99% in T, with
recall of licensed delay 91 to 99.8%; the memory changes these by under 2 points (for example `cm_full_prior`
in LT: 0.971 against 0.963). Removing failure cases lowers precision to 0.57 to 0.61 in SciPlex3.

### 7.2 Forecasts (measured, 49,304 held-out items)

| world | NLL | discrimination (nats) | observed / forecast wrong elimination | ECE |
|---|---|---|---|---|
| `class` | 0.4317 | 0.604 | 1.06 | 0.0028 |
| `similarity` (current) | 0.4320 | 0.600 | 1.07 | 0.0029 |
| `similarity_unitout` | 0.4328 | 0.603 | 1.07 | 0.0029 |
| `cm_full` | 0.4328 | 0.603 | 1.07 | 0.0029 |
| `cm_nofail` | 5.4567 | 0.920 | 2.93 | 0.0038 |
| `cm_nomisleading` | 0.4538 | 1.081 | 88.12 | 0.0057 |
| `cm_nonegative` | 5.4220 | 0.463 | 0.20 | 0.0225 |
| `scalar` | 0.5889 | 0.000 | 0.09 | 0.0589 |

Paired NLL differences: `cm_full` minus `similarity` +0.0009 [-0.0003, +0.0020] (`NO_DETECTABLE_DIFFERENCE`);
minus `class` +0.0011 [-0.0024, +0.0048]; `similarity` minus `class` +0.0002 [-0.0030, +0.0036]. A high
discrimination is not a virtue on its own: `cm_nomisleading` discriminates best (1.08) and is the worst
calibrated, because a memory with no misleading precedents never forecasts a wrong elimination.

On the action each arm actually chose (step 0), observed to forecast wrong-elimination is 0.91 [0.42, 1.54]
for the fixed order and 2.36 [1.50, 3.38], 2.35 [1.50, 3.37] and 2.46 [1.56, 3.49] for `belief_similarity`,
`cm_full` and `cm_full_prior`. Choosing an action because its forecast risk is low selects the forecasts
that are lowest by chance; no world corrects it. The planners' own recorded forecasts show the same
(2.04 to 2.13). At two to five reference units, SciPlex3 A forecasts 0.026 and observes 0.053.

### 7.3 Unseen-condition stress test (measured)

Frozen before it ran (`freeze_stress.json`); defined in `stress.py`. Pooled NLL 0.620, naive borrowing
0.538, adapted 0.538, full memory 0.525. The priced cost of a source against the NLL of borrowing from it:
Spearman 0.496 [0.457, 0.539] over 1,230 (fold, target, source) triples, 99% with historical support. The
adaptation table's predicted success against what held-out compounds realised: 0.865 against 0.844 (same
cell line, time near, same dose), 0.940 against 0.909, 0.681 against 0.659, 0.521 against 0.446, and 0.576
against 0.356 (only 20 items): the table is slightly optimistic, in the safe-to-notice direction.

### 7.4 Closed-loop update (measured)

Frozen before it ran (`freeze_online_update.json`). Appending each revealed compound's real readings to
the memory (same independent unit excluded) lowers later compounds' NLL by 0.0034 [-0.0067, -0.0003]; by
arrival position 0.0036, 0.0039, 0.0033 and +0.0017 [-0.0038, +0.0070] (n = 19 units at position 50 or more).
The gain is largest where a class has few references: SciPlex3 A -0.024 [-0.047, -0.002]. It does not grow
with more arrivals: class-level counts are close to saturated.

### 7.5 Model predictions and analogies (labelled)

**Model prediction.** For the worked examples the system's forecasts are uncalibrated on held-out units and
are stated as such; a forecast wrong-elimination probability is a floor. **Analogy.** The retrieved prior is a
historical analogy that never enters `EvidenceState`; where it rests on fewer than two effective precedents
the answer says so. **Speculation.** The advisory hypotheses (artifact, compensatory response, molecular
response without phenotype) are stated as claims the current data cannot test.

## 8. Visual and textual verification

Fourteen figures in `outputs/maestro_vc_v1/figures/` were drawn from pipeline files and inspected one by
one: measurement status, replicate agreement, control matching, dose and time response, Hallmark pathway
direction by class, split overlap and structural novelty, adaptation cost against realised error,
calibration, uncertainty against error by support, decisions against the fixed order, efficiency, replay
trajectories, case embedding and a hypothesis graph. Inspection found and led to fixing:

- The first status figure listed L1000 cell lines outside the prepared release as `planned_missing`,
  overstating missingness (most rows of the plot were 100% missing). The state table is now restricted to the release's
  scope; only conditions inside it can be missing.
- Overlapping titles, legends and labels in six figures; inconsistent colours for one entity across
  panels (fixed).
- One redraw silently failed because the output was filtered through `grep` and a syntax error was hidden;
  the figures were checked by timestamp and redrawn.

Sanity checks the figures allowed: the pathway heatmap shows HDAC inhibitors lowering E2F, G2M and MYC
programmes and raising cholesterol homeostasis, as expected of a proliferation-suppressing class; the
replicate scatter of the strongest condition lies on the diagonal; SciPlex3 median replicate agreement is
only 0.08 because most conditions are undetected (detection 3 to 14% in L1000).

## 9. Deviations, failures and corrections

- The protocol's first `written_at` was stamped 12:20 when the clock read 11:46; corrected before the freeze
  was used, with the correction recorded inside the protocol.
- `adaptation_model.signature` mapped a missing batch difference to `None`, so the zero-difference signature
  was never found and adaptation records in the replay's snapshot files carry declared-prior costs. Forecasts
  and decisions cannot be affected (the cost at zero difference is 0.0 under both versions, and adaptation
  cases are excluded from the index). Fixed after the freeze; recorded in `freeze_postrun_edits.json`; the
  published libraries were rebuilt with the corrected code.
- Two further frozen files gained additive changes while the replay ran (`case_schema` decision words,
  `world.add_query_compound`), recorded in the same addendum.
- The unit-out fit of the structure kernel chose `k = 0` in three of the five folds inspected before the freeze,
  where the reference
    fit chooses a positive value because it keeps same-unit analogues. Held-out SciPlex3 A NLL favoured the
  reference fit by 0.026 [0.008, 0.049]: the unit-out correction is too conservative there. The unit-out fit
  and the case-score terms together moved forecasts by no detectable amount (`cm_full` minus
  `similarity_unitout` +0.0000 [-0.0007, +0.0008]); this is reported as a null and was not tuned away.
- `protocol.json` says the training-side fits of "six tasks" were seen before the freeze; the list it gives
  has five (SciPlex3 A fold 0, B folds 0 and 2, L1000 LT fold 0, T fold 1). The file is hashed, so the miscount
  is corrected here and not there.
- The public ChEMBL comparison was automated crudely (protein names against gene symbols) and undercounted
  agreement; the agreement counts in section 3 are a manual reading and say so.

## 10. Claim boundaries

- **Development evidence only.** All 20 tasks and GSE70138 have been analysed before. Nothing here
  confirms a benefit and nothing here extends to unseen studies or classes.
- **Proxy task.** Terminal decisions are transcriptomic mechanism-class discriminations, not
  missing-premise repair; class labels are curated annotations, not ground truth; and most readings are
  undetected (57% of scored readings in the SciPlex3 B library, 92% in L1000 LT), which bounds every policy
  (the oracle decides correctly in 10% of LT episodes).
- **Small strata.** The misled-neighbour stratum has 18 units; the second family has 58 cases and its
  pattern retrievers are circular.
- **No wet-lab run.** Cost is priced in wells and assay days; nothing was executed.
- **Class-level counts are close to sufficient** for forecasting readings here. A gain from a richer memory
  would need a task in which the forecast, not the validator's headroom, is the binding constraint.

## 11. What would change the answer

The smallest data step that could make a decision possible is a study never opened by any session with at
least 200 label-compatible independent units (`research/protocol_v2/protocol.json` lists candidates: LINCS
2020 Level 5 compounds absent from GSE92742 and GSE70138, after a metadata-only unit count). Until then the
supportable position is: keep failure and negative cases in any memory; use hypothesis-conditional and never
scalar virtual-cell predictions to choose an action; keep the retrieved prior advisory; use the priced
adaptation for conditions a memory has not read; and treat forecast wrong-elimination risk as a floor.

## 12. Reproduction

```bash
python -m research.maestro_vc_v1.freeze --verify        # only the three documented post-freeze edits differ
python -m research.maestro_vc_v1.replay --workers 24    # about 16 minutes on 28 cores; writes outputs/maestro_vc_v1/replay/
python -m research.maestro_vc_v1.analyze
python -m research.maestro_vc_v1.stress
python -m research.maestro_vc_v1.online_update
python -m research.maestro_vc_v1.data_layer             # tables, views, libraries, manifest
python -m research.maestro_vc_v1.bridges                # after data_layer: bridge table, bridge cases, manifest entries
python -m research.maestro_vc_v1.run_audits
python -m research.maestro_vc_v1.plots
python -m research.maestro_vc_v1.examples
python -m pytest research/scientific_case_memory research/maestro_vc_v1 -q
```

Environment: `D:\anaconda\envs\maestro` (Python 3.11, RDKit, pandas, matplotlib 3.11). The run record is
`outputs/maestro_vc_v1/replay/run_record.json` (marked `development_unregistered`: the tree was dirty).
