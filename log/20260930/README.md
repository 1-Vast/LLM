# MAESTRO research reassessment (2026-09-30)

> - **Path**: `log/20260930/README.md`
> - **Purpose**: reassess the agent/world-model research problem and the data needed to identify decision value.
> - **Core points**: replay headroom mixes action choice and abstention; local raw metadata permits a deeper design audit; the current STATE adapter requires target rows in a registered, exposed context; a real pre-action state dataset is still missing.

## 1. Record control

Date: 2026-09-30. Scope: theoretical and source/data-availability analysis. No predictor,
planner, dataset or frozen result was changed. No experimental action or external dataset
acquisition was performed.

## 2. Research questions and hypotheses

The principal question is whether a decision-time state-informed policy can improve a
terminal scientific decision over the same-menu state-free policy. Three falsifiable
subquestions are whether action outcomes are comparable, whether real pre-action state
adds predictive information, and whether that information changes a scored action.

## 3. Materials, data and computational environment

Read current modules in `src/agent`, `src/virtual_cell`, `src/maestro`, `tools/datasets`
and `research/protocol_v2`. Inspected local file existence, SciPlex3 H5AD `obs` field
names, L1000 instance-header fields and one aggregated condition shape. No matrix values
were loaded into a model and no STATE inference was run. This review is not a test run.

## 4. Experimental design and controls

The proposed future comparison holds task, legal menu, budget, scorer, split and stopping
rules fixed while varying state availability. Design metadata is distinct from executed
attempts and from usable results. Oracle access to hidden outcomes is diagnostic only.

## 5. Experiment register and results

There is no new experiment. The registered output of this pass is the source audit and
research decision table below. Historical protocol-v2.1 and case-memory numbers were
read as diagnostics and were not re-estimated.

## 6. Deviations, failures and corrections

The supplied external audit assumed bulk sources were absent in its workspace. They
are present locally here, so the next step is an in-place lineage audit. Older audit
claims that interval emission and single-shot reconciliation are unimplemented were
superseded by 2026-09-29 repairs. No historical artifact was rewritten.
The external `/workspace/scratch/23cfc0dbed2f` session did not mount `D:\MAESTRO`;
its inability to read these files was an environment limitation, not evidence that
the local files did not exist. No upload or remount is needed for this workspace.

## 7. Interpretation and claim boundaries

File presence is not execution provenance. A protocol QC label is not a laboratory
failure receipt. A positive hindsight replay difference is not an identified policy
effect. An uncalibrated STATE shift is not qualified mechanism evidence.

## 8. Reproduction and artifact ledger

This report is the only new artifact. Its factual anchors are the paths named in the
tables below and `data/virtual_cell/registry.json`. No new numerical artifact exists.

## 9. Open items and next experiments

First reconcile the scorer and action legality; then join physical attempts, controls
and QC to SciPlex3 B and L1000 LT episodes. A pre-action state gain test is conditional
on that audit and on a temporally valid state source.

## 10. Curation provenance

Analysis was produced from the current working tree on 2026-09-30, using the latest
code after the 2026-09-29 consolidation. The report does not revise frozen protocols
or claim a new independent evaluation.

## Scope and evidence level

This is a theoretical and source/data-availability review of the agent, virtual-cell world
model, and dataset construction. It is not a new model experiment, a causal estimate, or a
qualification of a benchmark. No predictor, planner, dataset or frozen result was changed.

Evidence levels used below: **verified code** means the current implementation was read;
**local asset** means a file and its metadata are present, not that its scientific lineage is
complete; **hypothesis** names a question needing a controlled check. Older 2026-09-28
audits that describe the interval channel, single-shot reconciliation or revocation gate as
missing predate the 2026-09-29 repairs in this repository. They are historical diagnoses.

## Central finding

The project currently joins three distinct estimands: response prediction, choice of a
measurement, and terminal scientific decision. A gain at one level does not identify a gain
at the next. The binding research question is whether a *decision-time*, state-informed
policy has higher value than a state-free policy on a comparable action menu. Current
protocol replay suggests some diagnostic headroom, but its menu, scorer and experimental
provenance do not yet establish that policy value. The first research product should be a
task-level identifiability audit, then a data acquisition decision, then a state-value test.

## Findings from the current repository

| Finding | Evidence | Consequence / required check |
|---|---|---|
| The existing replay does not isolate action choice from abstention. | `research/protocol_v2/e_data1.py`: `legal_sequences` generates only nonempty sequences; `table_oracle` starts with the empty sequence, while `fixed_star` selects a nonempty sequence. `simulate_sequence` skips absent keys. | Recompute with identical action legality, stop rights, QC handling and terminal scoring. Report action-switch and abstention effects separately. Existing positive oracle-minus-fixed numbers remain protocol diagnostics. |
| The case-memory replay uses a narrower oracle question. | `research/case_memory_integration/external_replay.py`: the oracle requires one condition to produce its target reading against every decoy, while fixed scores the first sorted decoy and executes. | Its negative oracle-minus-fixed number is not a generic task ceiling. Unify decoy aggregation and abstention before using it for a task decision. |
| A planned condition is not an execution receipt. | `research/protocol_v2/design.py` derives menus from SciPlex3 `obs` or L1000 instance aggregates. `contracts.py:lifecycle_state` calls a planned condition with no prepared result `MEASURED_QC_FAILED`. | This is a protocol convention, not proof of a laboratory QC failure. Trace each condition to source well/instance and record an explicit unknown when the attempt cannot be verified. |
| The public benchmark does not carry menu provenance. | `tools/datasets/benchmark.py:_menu` derives the public menu from `row["outcomes"]` keys, although the upstream protocol intended those keys to come from design availability. | Preserve design-menu identity/hash separately from outcome coverage; verify public menu invariance when hidden results or QC status change. |
| The benchmark has no measured pre-action biological state. | `benchmark.py:_public` contains compound, hypotheses, menu, cost and metadata but no state measurement/time/source. `_hidden` contains measured outcomes. | It can test replay plumbing and some policy comparisons. It cannot test incremental value of a real pre-action state. Post-treatment expression cannot fill that slot. |
| The served STATE question is narrower than the proposed experiment-design question. | `src/virtual_cell/state_runner.py:inspect/subset` requires target-treatment rows as well as controls and copies both into the query file. The external State inference code samples basal features from controls for each treatment-labelled row (`data/external/arc_state/source/src/state/_cli/_tx/_infer.py`). | Actual treated expression does not appear to be the basal input in this path, but target-row existence, counts and grouping are required and can affect the served query. Test prediction invariance to treated expression; separately test sensitivity to treated-row count/group labels. A condition absent from the input asset cannot currently be served by this adapter. |
| The registered STATE deployment is narrow. | `src/virtual_cell/state_adapter.py` refuses unregistered contexts, unknown perturbation labels and free numeric dose/time; capabilities declare no dose/time support. `data/virtual_cell/registry.json` has one `tahoe_c39` context, NCI-H596, and no interval-calibration entries. | Do not call it a new-chemistry, new-context or time/dose planner. Separate checks of execution, response accuracy, calibration and independent deployment-domain transfer. Tahoe is an exposure-declared development domain for this checkpoint. |
| Model influence has distinct agent paths. | `src/agent/orchestrator.py` calls initial `planner.propose` before `_query_world_model`; predictions then enter selection and repair/briefing paths. Case-memory is off by default (`src/maestro/case_memory.py`). | Attribute any future action difference separately to selector, repair and case-memory. Do not describe initial proposal as state-informed unless the execution path changes and is evaluated. |
| Temporal availability is not fully evidenced by current case schemas. | `EpisodeObservation.availability` is a `pre_action`/`outcome_only` flag; `UserStateContext` carries assay/time/dose but no acquisition or availability timestamps. | For a new state-value dataset, retain measured-at, available-at and decision-at timestamps plus the population/same-sample relation. A declared flag alone cannot establish temporal order. |

## What the local data can and cannot resolve

The prior pasted audit was conducted in a workspace missing bulk sources. This workspace
contains `data/raw/sciplex3/SrivatsanTrapnell2020_sciplex3.h5ad` (2.46 GB), whose `obs`
has `plate`, `well`, `replicate`, `cell_line`, `dose_value`, `time` and perturbation fields;
the corresponding provenance records a matching source MD5 and SHA-256. It also contains
L1000 `GSE92742_Broad_LINCS_inst_info.txt.gz` with `inst_id`, `rna_plate`, `rna_well`,
perturbation, dose, time and cell fields. The local `subset48/conditions.json` has 102,586
aggregated conditions with well/plate counts and lists; plate metadata, control audit and
frozen `e_data1` tables are also present. These files make a deeper local audit feasible.

None of those file-presence checks proves which individual attempts failed, which controls
were usable for each treatment, or whether every comparison is exchangeable. In particular,
the L1000 Level 5 response is an aggregated signature, not an instance-level raw response;
the SciPlex3 cell count is not an independent experiment count. Shared controls, plate effects,
replicate/well dependence and chemical-structure grouping answer different questions.

The dataset audit should join four layers without collapsing them:

1. **Design:** action planned before outcome, legal menu, cost/time, and source design hash.
2. **Execution:** instance/well/plate, actual treatment/control, order, biological replicate,
   failure/missingness and QC reason. A missing processed row remains unknown until traced.
3. **Observation:** response value and scale, matched-control rule, detection/ambiguity,
   validator rule and uncertainty; preserve raw and aggregated identifiers.
4. **Decision episode:** exactly what was available before action, policy selection, hidden
   results, terminal scorer and provenance for every dependency.

Two local source questions now have precise, falsifiable joins. SciPlex3 `design.py`
expands every compound seen in a `(cell_line, time)` screen over the doses observed
for that screen. Compare this expanded menu with direct `(compound, cell_line, time,
dose, plate, well)` tuples in `obs`; record both set differences. A design-only tuple
is a discrepancy requiring a plate/layout or source-protocol check: absent surviving
cells alone cannot prove that the treatment was never planned or executed. For L1000,
expand each `conditions.json` entry to the `inst_id`, `rna_plate` and `rna_well` rows
in `GSE92742_Broad_LINCS_inst_info.txt.gz`, then link signature/QC records and controls
without treating a Level 5 aggregate as a single physical measurement. Retain
unmatched instances and unresolved control/QC causes explicitly.

For each task report episodes, actions, compounds, chemical blocks, physical wells, plates,
biological units and the unit used for uncertainty. Report menu, executed, interpretable and
policy-selected action coverage separately. If actions are missing, bound policy value using
a prespecified outcome/utility range; do not model-fill missing potential outcomes and label
the result point-identified. Known propensities require positivity and a defensible assignment
mechanism; a predictive outcome model is an assumption-based analysis, not data identification.
Identification depends on policy-reachable branches: fixed needs its reachable results,
a sequential candidate needs results for each branch it may choose, and a full-menu
oracle needs comparable results for the full legal menu. Action-record count alone is
insufficient.

## Research decisions for the two cores

**Agent.** Freeze one terminal scorer and admissible action set first. Compare a state-free
policy, a state-informed policy and their common fallbacks with the same budget, stop rights,
costs and validator. Log whether the world model affected the deterministic selector or the
repair proposal. Treat abstention as an explicit action with its own cost/utility. Until
candidate-selected outcomes are identifiable, an action-change rate is only a behavior metric.
Do not optimize a new VoI planner on the current replay ceiling.
The minimal scorer audit is a 2-by-2 comparison: fixed and outcome-informed diagnostic
oracle, each under forced-action and abstention-allowed rules. The fixed abstention
rule must use only information actually available to fixed. Use the same menu, QC
semantics and terminal endpoint throughout. Report within-rule action-choice gaps
and within-policy abstention gaps. Neither isolated gap is a causal effect without
an identifiable outcome design.

**Virtual cell.** Define the intended prediction target before changing readouts: unseen
compound, unseen cell context, new dose/time, or an already profiled condition with its
treated rows present are different tasks. The current STATE adapter supports the last of
these in one registered context. Test whether removing or permuting treated expression
leaves predictions unchanged, and whether changing only treated-row count/plate membership
changes them. A usable future-condition path would require an input built only from
decision-time controls plus an explicit virtual target design; it would need a separate
validation and calibration receipt. The existing interval and revocation code should remain
inactive for a scope without independent predicted-realized pairs.
The input-sensitivity study should hold checkpoint, controls, target label and seed
fixed while separately perturbing target expression, target-row count and target
batch/group metadata. Compare vector differences with repeated control-resampling
variation. Refusal for an absent target row is `unsupported_query`, not predictive
uncertainty.

**Cross-core.** Separate four contrasts: state value for forecasting, readout value for
interpretation, action-choice value and terminal decision value. Use identical episodes and
independent-unit splits. The case-memory outcome model is hypothesis-conditional, whereas
the STATE adapter serves a condition-level shift; neither should silently be treated as
the other's likelihood. Curated mechanism labels, response similarity and qualified target
evidence need distinct typed outcomes and separate claims.

## Priority and stopping points

| Priority | Research question and concrete output | Stop / branch |
|---|---|---|
| P0 | Reconcile `e_data1` and case-memory scorers, oracle information, legal menus and abstention. Output paired action-switch and abstention components. | If a consistent scorer cannot be specified, no headroom claim. |
| P1 | Trace SciPlex3 B and L1000 LT from frozen episode to raw design, physical attempt, control and QC; output episode-level coverage and unresolved-reason ledger. | If selected-action results are absent or incomparable, report partial bounds and specify a new complete-menu or randomized acquisition design. |
| P2 | Define the actual pre-action state source and timestamp, then audit whole-system checkpoint/data exposure. | If no temporally valid, independently measured state exists, do not run a state-gain experiment. |
| P3 | Only on an eligible task: compare state-free, true state and context-preserving shuffled state on future outcomes and selected-action utility, with calibration and independent-unit uncertainty. | If prediction improves but action/decision value does not, localize the bottleneck; do not increase planner complexity by default. |

SciPlex3 B and L1000 LT are audit priorities because frozen replay reported diagnostic
headroom, not because either task has already passed identification. SciPlex4 qualified
rescue contrasts remain unavailable; Tahoe's training exposure bars independent validation
of the current STATE checkpoint on Tahoe. An untouched evaluation population must be
selected against the exposure history of the entire agent-plus-world-model system.

## Limits of this review

This pass inspected code, source headers/schema and local asset presence. It did not join
individual wells to episodes, recompute headroom, inspect the full checkpoint training set,
run STATE inference, or estimate new confidence intervals. The findings above therefore
specify falsifiable research work; they are not new biological or performance results.

---

# Round 1: task identifiability and dual-core influence audit (executed 2026-09-30)

> - **Path**: `log/20260930/README.md` (this section is appended; the review above is unchanged)
> - **Purpose**: decide whether SciPlex3 B and L1000 LT action results are comparable enough to
>   support a strategy comparison, recompute the replay diagnostic under one scorer, and test
>   whether the served STATE query depends on the target treatment rows.
> - **Core points**: both e_data1 tasks are coverage-complete; the registered headroom number is a
>   ceiling and not a policy effect; the case-memory task cannot exercise action choice at all; the
>   served STATE shift does not read the target cells' expression; no real decision-time state
>   exists, so the state-gain arm was not run.

## R1.1 Record control

Date 2026-09-30. Scope: an audit that reads frozen artifacts and raw source files and writes new
artifacts under `outputs/identifiability_audit_20260930/`. No predictor, planner, dataset, frozen
result or registered asset was changed. `research/protocol_v2/*`, `research/case_memory_integration/*`
and `outputs/protocol_v2_1_20260927/*` were read only. No new model was trained, no direction
readout was developed, and no planner was optimised.

Added files (all new, nothing overwritten):

| Path | Role |
|---|---|
| `research/identifiability_audit/lineage_sciplex3.py` | SciPlex3 B per-action lineage |
| `research/identifiability_audit/lineage_l1000.py` | L1000 LT per-action lineage |
| `research/identifiability_audit/unified_score.py` | one scorer, four rules, coverage bounds |
| `research/identifiability_audit/state_sensitivity.py` | STATE input-sensitivity experiment |
| `research/identifiability_audit/verify_state_outputs.py` | embedding-level identity check |
| `research/identifiability_audit/dual_core_attribution.py` | forecast/policy attribution on frozen traces |
| `research/identifiability_audit/task_summary.py` | cross-task rollup and verdicts |
| `tests/test_identifiability_audit.py` | contract tests for the audit's invariants |

Work-tree commit at execution: `9ac2d9b` (dirty: `log/INDEX.md` modified; the paths above untracked).

## R1.2 Computational environment

| Role | Interpreter | Key versions |
|---|---|---|
| Phase 1 and 2 | `D:\anaconda\python` | CPython 3.9.13, numpy 1.26.4, pandas 2.3.2, h5py 3.7.0 |
| Phase 2 cross-check | `C:\Python314\python` | CPython 3.14.4, numpy 2.4.4, pandas 2.3.3, h5py 3.16.0 |
| Phase 3 | `D:\anaconda\envs\maestro\python.exe` | CPython 3.11.16, torch 2.7.0+cu126, anndata 0.12.19, numpy 2.4.6, arc-state 0.11.3 (editable, `data/external/arc_state/source`) |
| Tests | `C:\Python314\python` | pytest 9.1.1 |

The repository declares `requires-python >= 3.11`; phase 1 and 2 were executed on 3.9 because that
interpreter carries the registered research stack. Phase 2 was therefore re-executed end to end on
3.14: **129 numeric fields, 0 differences** (`outputs/identifiability_audit_20260930/verify_py314/`).

## R1.3 Commands

```bash
# Windows Git Bash, from D:\MAESTRO
/d/anaconda/python -m research.identifiability_audit.lineage_sciplex3
/d/anaconda/python -m research.identifiability_audit.lineage_l1000
/d/anaconda/python -m research.identifiability_audit.unified_score
/d/anaconda/python -m research.identifiability_audit.dual_core_attribution
/d/anaconda/python -m research.identifiability_audit.task_summary

/d/anaconda/envs/maestro/python.exe -m research.identifiability_audit.state_sensitivity --resamples 5
/d/anaconda/envs/maestro/python.exe -m research.identifiability_audit.verify_state_outputs

/c/Python314/python -m pytest -q --tb=no -p no:cacheprovider
/c/Python314/python -m pytest -q tests/test_identifiability_audit.py
```

Input digests recorded by the runs (full values in each `summary.json`):

| Input | SHA-256 (first 32) |
|---|---|
| `outputs/protocol_v2_1_20260927/design/sciplex3_design.csv` | `b92123aff9881bca37a38e26bb1c20ca` |
| `outputs/protocol_v2_1_20260927/design/l1000_design.csv` | `08c42ddb1c6433a1bab647c699726266` |
| `outputs/dynamic_world_model_20260926/prepared/conditions.csv` | `d0b7d2481fd87c4a1505e6485e6fad78` |
| `outputs/dynamic_world_model_20260926/prepared/wells.csv` | `4b393f449eeb9575a53d1c9cfb9df89a` |
| `outputs/sequence_audit_20260926/l1000/prepared/conditions.csv` | `28b0aa68b0525be553bba902bf728d91` |
| `GSE92742_Broad_LINCS_inst_info.txt.gz` | `9eddd1efbbd754588bb9cbe4fd4530a2` |
| `GSE92742_Broad_LINCS_sig_info.txt.gz` | `19da29c0ee12ddf27f9698cd0da40bea` |
| `GSE92742_Broad_LINCS_sig_metrics.txt.gz` | `54f19003e5e3445bc293347cca004eeb` |
| `subset48/conditions.json` | `7c8a121ad9583daf57018aa6f663218e` |
| obs cache written by this audit | `f08e07a7dce1bfa58b78ed1339687289` |

The raw SciPlex3 H5AD (2.46 GB) was read through `obs` only (no matrix values) and was not
re-hashed in this pass; the digest recorded in the dataset provenance is unchanged.

Artifacts total 461 MB under `outputs/identifiability_audit_20260930/`, of which 240 MB is the
single `target_rows_deleted.h5ad` (every NCI-H596 row except the target, kept so the refusal arm can
be re-run without touching the registered asset). The SciPlex3 `obs` cache is 56 MB.

## R1.4 Phase 1: source audit, per action

Counts are `(compound, action)` cells over each task's episode compounds. "Executed" means a raw
physical record, never a protocol inference.

| Task | Compounds | Episodes | Actions | Cells | Planned | Executed (raw) | Result valid | QC-failed label | Control missing | Unknown |
|---|---|---|---|---|---|---|---|---|---|---|
| SciPlex3 B | 108 | 1278 | 12 | 1296 | 1296 | 1296 | 1294 | 2 | 0 | 0 |
| L1000 LT | 268 | 3648 | 8 | 2144 | 2144 | 2144 | 2144 | 0 | 0 | 0 |

**SciPlex3 B.** The design menu and the raw `obs` tuples agree exactly: no design-only condition
exists, so nothing has to be marked "design pending verification". Both unusable results are fully
traced and are *not* unknown: `Alisertib (MLN8237)` and `SRT3025 HCl` at `A549|024h|10000nM` have
raw `obs` records of **13** and **17** cells in the rep1 well against the 20-cell minimum, so the
row was dropped by a cell-survival outcome, not by a missing plate entry. Controls are present at
every (line, time, replicate): 16 vehicle wells per replicate. Physical unit = one well;
replicate = the second well; uncertainty unit = Murcko scaffold (108 units). 8–9 distinct plates
per action. Discriminating readings: 404/1296 (31.2%).

**L1000 LT.** Every condition is planned and every condition has `inst_info` wells. The two
aggregate levels are reported separately and never summed: **13,594 raw `inst_info` wells** against
**3,573 Level 5 signature records**; the per-condition median is 5 wells and 1 signature. Five of
2,144 conditions (all `MCF7|024h`) disagree by one well between `subset48/conditions.json` and the
current `inst_info`; one of them is a duplicated `(rna_plate, rna_well)` slot, the other four are
unresolved. Detection: 117/2144 (5.5%); discriminating readings: 43/2144 (2.0%). Vehicle controls
exist at every (line, time): 540–1400 vehicle signatures and 914–2,657 vehicle wells per stratum.
Physical unit = `inst_info` RNA well; replicate = a distinct RNA plate; uncertainty unit = InChIKey
connectivity block (268 units).

Two protocol encodings are recorded as encodings, not measurements. L1000 sets
`n_cells_rep1 = n_cells_rep2 = 20` in the prepared table purely so `common.qc_passed` reproduces the
L1000 rule, so its `independent_units = 2` is asserted rather than measured. SciPlex3's
`measured_qc_failed` label is `contracts.lifecycle_state`'s convention for a planned condition with
no usable prepared row; no laboratory receipt exists for either task.

Field basis (which column is a raw record and which is a protocol inference) is recorded in
`field_basis` inside each `summary.json`.

## R1.5 Phase 2: unified scoring

One legal menu, one decoy rule, one QC semantics, one endpoint (`correct +1`, `wrong/exhausted −2`,
`undetermined/deferred 0`), one cost model (days per condition). Four conditions: `fixed` and the
diagnostic `oracle`, each under `must_act` and `may_abstain`.

The fixed abstention rule uses only decision-time information: it abstains when the first condition
of the fixed sequence has **no detected training reference template for one of the two hypotheses**
(`build_fold_tables` on the fold's training compounds). It is pre-declared and was not tuned after
the fact.

| Task | Rule | Utility gap (unit mean, 95% CI) | Correct-rate gap (95% CI) |
|---|---|---|---|
| SciPlex3 B | must act | **+0.1473 [+0.0937, +0.2131]** | **+0.0702 [+0.0418, +0.1059]** |
| SciPlex3 B | abstain allowed | +0.1790 [+0.1314, +0.2391] | +0.1209 [+0.0884, +0.1582] |
| L1000 LT | must act | **+0.0546 [+0.0271, +0.0878]** | **+0.0473 [+0.0216, +0.0790]** |
| L1000 LT | abstain allowed | +0.0778 [+0.0480, +0.1115] | +0.0764 [+0.0466, +0.1102] |

Abstention components (utility): SciPlex3 B fixed −0.0317 [−0.0518, −0.0057], oracle 0.0000;
L1000 LT fixed −0.0232 [−0.0422, −0.0059], oracle 0.0000. Abstention saves measurements
(SciPlex3 B oracle −0.305, L1000 LT fixed −1.553) but the endpoint prices `deferred` and
`undetermined` identically, so abstention buys cost and not correctness. The pre-declared fixed
abstention rule is *harmful* on both tasks because it fires where acting still pays.

**Reproduction check.** The must-act correct-rate gaps, +0.0702 and +0.0473, reproduce the
registered numbers exactly. The registered `table_oracle` already starts from the empty sequence,
but abstention only ever replaces `undetermined` with `deferred` (both utility 0), so the
registered number happens to coincide with the must-act gap. The registered comparison is still a
mixed rule: oracle-may-abstain against fixed-forced-to-act.

**Coverage and bounds.** No action is absent from any episode table on either task
(`unplanned_tier_conditions = 0` everywhere). Missing *results*: 28 of 12,936 SciPlex3 B episode
cells (0.22%), zero on L1000 LT. Enumerating all three resolutions of each missing reading, shared
by both policies as one fact about the world, bounds the oracle-may-abstain minus fixed-must-act
utility difference at **[+0.1364, +0.1936]** — it does not cross zero, and the realised +0.1790
sits inside it. L1000 LT needs no bound.

**Case memory.** 25 of 26 test units have exactly **one** legal action (menu sizes 1×25, 3×1).
Under the must-act rule the oracle-minus-fixed gap is **0.0000** for both decoy aggregations, so
the frozen −0.192 contains no action-choice component at all. Decomposed: under the frozen
aggregation pair the gap is +0.6154 of which the oracle's abstention alone contributes +0.6154;
under a single all-decoy aggregation the abstention contribution is +0.9231. The negative number is
an abstention-and-decoy-aggregation artefact, not a task ceiling.

**Verdicts** (`outputs/identifiability_audit_20260930/task_summary/`):

| Task | Verdict | Reason |
|---|---|---|
| SciPlex3 B | comparable | menu and results complete; the within-rule gap excludes zero, but the oracle arm reads hidden outcomes, so this is a ceiling and not a policy effect |
| L1000 LT | comparable | same, with 2.0% discriminating readings |
| case memory | replay only | 25/26 units have one action; action choice cannot be exercised |

## R1.6 Phase 3: STATE input sensitivity

Registered context `NCI-H596` of `tahoe_c39`, control `[('DMSO_TF', 0.0, 'uM')]`, target
`[('Adagrasib', 0.05, 'uM')]` (378 rows), 586 control rows, `X_hvg` (2000 features), checkpoint
`state_generalization_zeroshot_X_hvg`, seed 42. Every arm uses the command the adapter issues and
the runner the adapter calls. Reference: 5 control resamples at 80%, relative L2 change
0.855–1.093 (median 0.934, max 1.093).

| Arm | Served | Relative L2 change vs baseline | Cosine | Verdict |
|---|---|---|---|---|
| target expression permuted | yes | **0.000** | 1.000 | not influential |
| target expression replaced by control values | yes | **0.000** | 1.000 | not influential |
| target plate relabelled (existing plate) | yes | **0.000** | 1.000 | not influential |
| target plate relabelled (unseen plate) | yes | **0.000** | 1.000 | not influential |
| half the target rows (two independent draws) | yes | 0.9295 (identical for both draws) | 0.561 | within the control-resampling reference |
| a quarter of the target rows | yes | **2.3735** | 0.066 | above the reference |
| target rows deleted | **no** | — | — | `unsupported_query` |

The predicted embedding is **byte-identical** (SHA-256 `7ac2b8e0d6a2bd66…`) across baseline,
expression-permuted, expression-replaced and both plate-relabelled arms, although the query files
differ (target-block max difference 5.02). The row-count arms change the output but are identical
across two different subsets of the same size, which is what a seeded basal-control sample of size
N would produce: the served shift depends on the *number* of target rows, not on which rows or on
what they express. The two half-size draws agree exactly, so row identity does not enter either.

Answers to the three questions: (1) target expression does **not** enter the served prediction;
(2) row count does, but only detectably at a 25% reduction — a 50% reduction is inside the
control-resampling fluctuation, and batch/group metadata does not enter at all;
(3) deleting the target rows is refused at query construction with
`no rows for the declared context contain the perturbation`. That is an `unsupported_query`
interface refusal — **not** predictive uncertainty and not a refused measurement.

## R1.7 Dual-core attribution and why the state-gain arm was not run

Attribution was computed on the frozen traces, with the episode, menu, budget, stopping rule and
scorer held fixed. No arm was re-run and no planner was changed.

| Task | Arm | Uses a forecast | First action changed | Terminal changed | Δutility vs fixed (95% CI) | Abstention rate |
|---|---|---|---|---|---|---|
| SciPlex3 B | belief | yes (ReferenceWorld) | 0.737 | 0.086 | −0.0054 [−0.0436, +0.0386] | 0.000 |
| SciPlex3 B | myopic_edv | yes (SparseReferenceModel) | 0.742 | 0.152 | −0.0404 [−0.0864, +0.0067] | 0.124 |
| SciPlex3 B | safe | yes + novelty gate | 0.002 | 0.002 | +0.0005 [−0.0019, +0.0027] | 0.000 |
| SciPlex3 B | random_legal | no | 0.900 | 0.286 | −0.1731 [−0.2433, −0.1012] | 0.000 |
| SciPlex3 B | oracle | hidden outcomes | 0.783 | 0.380 | +0.1418 [+0.0889, +0.2065] | 0.308 |
| L1000 LT | belief | yes | 0.915 | 0.630 | +0.0137 [−0.0096, +0.0408] | 0.332 |
| L1000 LT | myopic_edv | yes | 0.971 | 0.703 | +0.0068 [−0.0159, +0.0330] | 0.776 |
| L1000 LT | safe | yes | 0.000 | 0.000 | +0.0000 [+0.0000, +0.0000] | 0.000 |

The forecast-informed arms change the first action on 74–97% of episodes and their decision-gain
intervals still contain zero. **Action change is not decision gain.** A separate 1,212 of 3,648
L1000 LT episodes (33%) end in `registered_validator_cannot_eliminate`, so the validator cannot
eliminate there at all.

The state-gain arm was **not run**, and this is a stop-rule decision, not an omission by accident.
Every frozen arm's forecast is built from the fold's *training* compounds
(`SparseReferenceModel`, `belief_planning.world.ReferenceWorld`); no arm receives a decision-time
measurement of the held-out compound, and Phase 3 shows the served STATE query requires the
target's own post-treatment rows. There is therefore no temporally valid pre-action state for
these episodes, so a state-value experiment would have no estimand. It becomes runnable only with
a source that carries measured-at, available-at and decision-at timestamps and a population
untouched by the agent-plus-world-model system.

## R1.8 Deviations, failures and corrections

- Phase 1 and 2 were first run on CPython 3.9, below the declared `requires-python >= 3.11`. This
  was disclosed and then corrected by an independent 3.14 re-execution of phase 2 (0 differences
  over 129 numeric fields).
- The first missing-result bound was mislabelled: it bounded the *deviation* of the difference
  instead of the difference itself. Corrected to bound oracle-minus-fixed directly.
- The first `case_memory_report` mixed the decoy-set choice into the arm definition. Corrected to
  a single `resolve()` used by both policies, with aggregation as an explicit axis.
- The raw-h5ad `obs` cache is written once
  (`outputs/identifiability_audit_20260930/sciplex3_B/sciplex3_obs_cache.csv`, 56 MB) so the 2.46 GB
  asset is read only once. No matrix values are read.
- No historical artifact was rewritten. `+0.0702`, `+0.0473` and `−0.192` are carried into
  `unified_score.json` under `original_protocol_replay` and are not recomputed.

## R1.9 Tests run and checks not run

Run: `C:\Python314\python -m pytest -q --tb=no -p no:cacheprovider` (full suite,
`outputs/identifiability_audit_20260930/pytest_full.log`) and
`pytest -q tests/test_identifiability_audit.py`. Result: **1458 collected, 1457 passed, 1 failed**.
The single failure is `tests/test_repository_shape.py::test_project_markdown_has_no_chinese_prose`,
which is **pre-existing**: it fails identically after stashing this pass's new files, and is caused
by Chinese prose in `research/case_memory_integration/*.md` and
`research/scientific_optimization/README.md`. The six new contract tests pass; they pin
whole-menu coverage in the frozen tables, the reproduction of the registered headroom numbers, the
byte-level STATE invariance, the `unsupported_query` refusal class and the verdict vocabulary.

Not run, and why:

- No re-execution of `research.protocol_v2.e_data1 run`: the frozen replay was left untouched.
- No checkpoint training-set exposure audit for the STATE checkpoint.
- No re-derivation of the `subset48` cache, so the five well-count disagreements stay unresolved.
- No independent-unit re-split; the frozen fold assignments were taken as given.
- No calibration or interval receipt for the STATE endpoint; the registered scope has none.
- No measurement of forecast quality (NLL, calibration) for the world model; that would need a
  pre-registered forecast evaluation, not an audit.
- No state-gain arm, for the reason in R1.7.

## R1.10 What this pass licenses and what it does not

Licensed: both e_data1 tasks are coverage-complete and their within-rule oracle-minus-fixed gaps
exclude zero; the case-memory negative number is explained and cannot be used as a ceiling; the
served STATE shift is invariant to target-row expression and batch labels, sensitive to target-row
count, and refuses a missing target row by name.

Not licensed: any policy-effect claim. The oracle arm reads hidden outcomes, `fixed_star` is fitted
on other folds' outcomes, the uncertainty unit is a scaffold or an InChIKey block rather than a
physical replicate, and SciPlex3's two "replicates" are two wells against one pooled vehicle
reference. Prediction improvement and action change are reported separately and are **not** a
dual-core synergy.

---

# Round 2: forecast to action to terminal-decision audit (2026-09-30)

## R2.1 Outcome and scope

The audit completed eight predeclared cells on all five folds of SciPlex3 B and L1000 LT. The reference baseline reproduced every historical `belief` action sequence. No model was trained and production `src` was not changed. Historical oracle arms remain diagnostic ceilings. WorldV2 forecast swap and its policy interaction were not executed: fitted transitions were not serialized, and recreating them would fit a model. ReferenceWorld is reported under its own name.

Real reference forecast content improves SciPlex3 reading quality and choices relative to permutation, but does not establish terminal benefit over fixed. Paired baseline-minus-fixed utility is -0.0054 [-0.0436,+0.0386] on SciPlex3 and +0.0137 [-0.0096,+0.0408] on L1000. Both chemical-cluster CIs include zero. Risk-select lowers unconditional errors and costs while also reducing correct decisions and coverage; this is not general decision improvement.

All datasets, outcomes and research backends have development exposure since 2026-09-26; this is a descriptive path audit, not independent generalization, biological mechanism validation or evidence of decision superiority. STATE is audited only at its registered Tahoe c39 condition.

## R2.2 Round 1 recovery and corrections

The missing log and six contract tests were recovered byte-for-byte from stash object `11f7e57`, without applying or dropping the stash. `recovery.json` records hashes. Both raw-source action tables were independently regenerated in a fresh directory and matched all 1,296 / 2,144 rows. The source gate passed 59 checks, including the actual 2.456 GB SciPlex3 H5AD SHA-256 and every original e_data1 output hash. `verification.json` and `round1_input_hashes.json` are the receipts.

SciPlex3 has two recorded low-cell-count conditions: Alisertib (MLN8237), 13 rep1 cells; SRT3025 HCl, 17 rep1 cells; both at A549 / 24 h / 10,000 nM, versus a 20-cell threshold. They are known QC-failed attempts, not absent treatments or laboratory failure receipts.

L1000's four unresolved well counts are BRD-K00627859 (23 vs 24), BRD-K02130563 (23 vs 24), BRD-K72703948 (12 vs 13), and BRD-K88742110 (23 vs 24), all MCF7 / 24 h / 10,000 nM. BRD-K81418486's 190 cached vs 191 instance rows reduce to 190 distinct well slots; its plate count still disagrees, 153 vs 154. Thus four well-count source linkages remain unresolved and a fifth plate-count linkage is also unresolved. All five affected source conditions enter conservative path bounds. The extra plate caveat was recorded before L1000 outcomes were summarized in `source_addendum_pre_l1000.json`.

Corrections to R1: 108 and 268 are compound counts; the frozen uncertainty groups number 105 Murcko skeletons and 205 identity/scaffold components. SciPlex3's full episode-action grid has 15,336 cells (1,278 x 12), not 12,936. The R1 latent-reading bound compares oracle-may-abstain with fixed-must-act; its observed diagnostic is 0.1473, whereas 0.1790 uses fixed-may-abstain and is a different contrast. Original artifacts and original log prose remain preserved; this section supersedes those interpretations.

## R2.3 Four-arm unified-score review

The fixed arm here is R1's cross-fitted `fixed_star`, distinct from the registered fixed order in R2 policy swap. Rates below are chemical-unit means, with all metric cluster intervals in each `*_four_arm_summary.json`. Days now charge only executed attempts. R1 charged the whole chosen sequence even after an early elimination; this changed cost figures, not terminal utilities.

| Task | Diagnostic arm | correct | wrong | undetermined | deferred | measurements | days | utility |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| sciplex3_B | fixed_may_abstain | 0.5743 | 0.0290 | 0.2919 | 0.1048 | 1.2729 | 7.6377 | 0.5162 |
| sciplex3_B | fixed_must_act | 0.6250 | 0.0386 | 0.3364 | 0.0000 | 1.4370 | 8.6218 | 0.5479 |
| sciplex3_B | oracle_may_abstain | 0.6952 | 0.0000 | 0.0000 | 0.3048 | 0.6952 | 4.1711 | 0.6952 |
| sciplex3_B | oracle_must_act | 0.6952 | 0.0000 | 0.3048 | 0.0000 | 1.0000 | 6.0000 | 0.6952 |
| l1000_LT | fixed_may_abstain | 0.0224 | 0.0007 | 0.1889 | 0.7881 | 0.4051 | 2.4308 | 0.0210 |
| l1000_LT | fixed_must_act | 0.0515 | 0.0036 | 0.9449 | 0.0000 | 1.9577 | 11.7464 | 0.0442 |
| l1000_LT | oracle_may_abstain | 0.0988 | 0.0000 | 0.0000 | 0.9012 | 0.0988 | 0.5600 | 0.0988 |
| l1000_LT | oracle_must_act | 0.0988 | 0.0000 | 0.9012 | 0.0000 | 1.0000 | 5.2915 | 0.0988 |

The statement that abstention buys cost but not correctness is valid for the diagnostic oracle alone: it turns undetermined into deferred without changing correct or wrong. It is false as a general fixed-policy claim. Fixed abstention lowers correct-unit means by 0.0507445 (SciPlex3) and 0.0290901 (L1000), and utility by 0.0316969 / 0.0231873. The widened oracle-minus-fixed correctness gap partly reflects damage to fixed, not new model or action value. Utility `correct - 2*wrong` has no cost term; cost savings are reported separately.

## R2.4 Frozen interventions and information

SciPlex3 B: 1,278 episodes, 12 menu actions, 16-day budget, maximum two attempts. L1000 LT: 3,648 episodes, eight actions, 12-day budget, maximum two attempts. Each fold's exact episodes, legal menu, training set, validator calibration, QC, endpoint, costs and reference parameters are in `*_freeze.json`; initial seed is 20260930. QC failures cost days and change no evidence. Time order, distinct actions and stopping on the first registered elimination remain fixed.

Forecast swap uses one existing belief expectimax planner: none, original reference, within-task action permutation, and a constant uniform five-reading forecast. Permutation remaps forecast queries/history among the same task's actions while retaining hypothesis/context and the offered action identifier. WorldV2 is unavailable. Policy swap supplies the same immutable reference query-to-forecast function to fixed, baseline planner, discrimination selection and existing upper-risk-select. No held-out result selects a combination or threshold. Risk caps use the historically predeclared middle upper cap: 0.5294 / 0.2558. The two extra none/reference fixed cells are negative controls for forecast presence by policy interaction.

Policies see hypotheses, structures, training-only reference tables, frozen validator parameters, design menu, budgets and purchased readings. Hidden truth and unpurchased readings stay on the scoring/execution side. The original `P.discrimination` wrapper's inaccessible magnitude field is bypassed by feeding the same forecasts directly into the existing `select_discriminating_action`; no magnitude priority or new selector is added. Forecasts enter selection, not repair or final evidence updates. Fixed deliberately ignores forecasts. Selector calls, quality probes and forecast input/output SHA-256 are distinct in `*_forecasts.jsonl.gz`.

## R2.5 Task-level terminal results

These point rates describe the frozen local replay. Where a selected condition has unresolved source linkage, the inferential comparison is only the utility interval shown; the raw replay point and its bootstrap interval do not resolve that source uncertainty. Same exact fixed paths have zero paired difference under every shared missing-world resolution. Other bounds are conservative outer bounds using U in [-2,+1]; no forecast fills a missing biological outcome.

| Task | forecast / policy | correct | wrong | deferred | measurements | days | utility | replay U-fixed (95% CI) | identification U-fixed bounds |
|---|---|---:|---:|---:|---:|---:|---:|---|---|
| sciplex3_B | constant / baseline | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | -0.5533 [-0.6495, -0.4598] | [-0.5533, -0.5533] |
| sciplex3_B | none / baseline | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | -0.5533 [-0.6495, -0.4598] | [-0.5533, -0.5533] |
| sciplex3_B | none / fixed | 0.6268 | 0.0368 | 0.0000 | 1.5013 | 9.0078 | 0.5533 | +0.0000 [+0.0000, +0.0000] | [+0.0000, +0.0000] |
| sciplex3_B | permuted / baseline | 0.2417 | 0.0167 | 0.0000 | 1.7927 | 10.7562 | 0.2083 | -0.3451 [-0.4367, -0.2560] | [-0.3451, -0.3451] |
| sciplex3_B | reference / baseline | 0.6076 | 0.0298 | 0.0000 | 1.4925 | 8.9549 | 0.5480 | -0.0054 [-0.0436, +0.0386] | [-0.0054, -0.0054] |
| sciplex3_B | reference / discrimination | 0.5684 | 0.0292 | 0.0000 | 1.2955 | 7.7733 | 0.5101 | -0.0433 [-0.0865, -0.0004] | [-0.0433, -0.0433] |
| sciplex3_B | reference / fixed | 0.6268 | 0.0368 | 0.0000 | 1.5013 | 9.0078 | 0.5533 | +0.0000 [+0.0000, +0.0000] | [+0.0000, +0.0000] |
| sciplex3_B | reference / risk_select | 0.4573 | 0.0214 | 0.1657 | 1.2053 | 7.2315 | 0.4145 | -0.1389 [-0.1889, -0.0864] | [-0.1389, -0.1389] |
| l1000_LT | constant / baseline | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | -0.0448 [-0.0741, -0.0168] | [-0.0448, -0.0448] |
| l1000_LT | none / baseline | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | -0.0448 [-0.0741, -0.0168] | [-0.0448, -0.0448] |
| l1000_LT | none / fixed | 0.0548 | 0.0050 | 0.0000 | 1.9776 | 11.1158 | 0.0448 | +0.0000 [+0.0000, +0.0000] | [+0.0000, +0.0000] |
| l1000_LT | permuted / baseline | 0.0315 | 0.0007 | 0.6239 | 0.6209 | 3.4032 | 0.0300 | -0.0148 [-0.0433, +0.0122] | [-0.0159, -0.0142] |
| l1000_LT | reference / baseline | 0.0641 | 0.0028 | 0.6239 | 0.5943 | 3.4125 | 0.0585 | +0.0137 [-0.0096, +0.0408] | [+0.0137, +0.0137] |
| l1000_LT | reference / discrimination | 0.0601 | 0.0028 | 0.6629 | 0.4557 | 2.6444 | 0.0544 | +0.0097 [-0.0143, +0.0369] | [+0.0091, +0.0100] |
| l1000_LT | reference / fixed | 0.0548 | 0.0050 | 0.0000 | 1.9776 | 11.1158 | 0.0448 | +0.0000 [+0.0000, +0.0000] | [+0.0000, +0.0000] |
| l1000_LT | reference / risk_select | 0.0251 | 0.0031 | 0.7422 | 0.3780 | 2.1665 | 0.0188 | -0.0260 [-0.0488, -0.0050] | [-0.0260, -0.0260] |

## R2.6 Forecast quality and path changes

NLL and multiclass Brier score the attempted reading distribution under the true hypothesis after freezing predictions; QC is a separate class. Initial all-menu quality and selected-action pre-measurement quality are separate. Structural validator folds never consumed a forecast; their placeholder quality probes are excluded from quality claims. None has no quality estimate.

Ranking below is the explicitly defined unconditioned one-step forecast utility minus day price, not an assertion that every selector uses that ranking. Forecast-swap changes are relative to reference/baseline; policy-swap changes are relative to reference/fixed. Later actions and terminal changes, conditional and unconditional unchanged-terminal shares, all CIs and paired correct/wrong differences are in `task_summary.json` and episode path tables.

| Task | forecast / policy | NLL all-menu | NLL selected | ranking changed | first changed | later changed | sequence changed | changed-action same-terminal / changed actions |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| sciplex3_B | constant / baseline | 1.6094 | NA | 1.0000 | 1.0000 | 0.4925 | 1.0000 | 0.0000 |
| sciplex3_B | none / baseline | NA | NA | 1.0000 | 1.0000 | 0.4925 | 1.0000 | 0.0000 |
| sciplex3_B | none / fixed | NA | NA | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| sciplex3_B | permuted / baseline | 1.0751 | 1.2247 | 1.0000 | 1.0000 | 0.8322 | 1.0000 | 0.5657 |
| sciplex3_B | reference / baseline | 0.8218 | 0.9755 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| sciplex3_B | reference / discrimination | 0.8218 | 0.9848 | 0.0000 | 0.7542 | 0.4755 | 0.8335 | 0.8586 |
| sciplex3_B | reference / fixed | 0.8218 | 1.0616 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| sciplex3_B | reference / risk_select | 0.8218 | 0.9750 | 0.0000 | 0.9077 | 0.4817 | 0.9368 | 0.6834 |
| l1000_LT | constant / baseline | 1.6094 | NA | 1.0000 | 0.3761 | 0.2182 | 0.3761 | 0.0000 |
| l1000_LT | none / baseline | NA | NA | 1.0000 | 0.3761 | 0.2182 | 0.3761 | 0.0000 |
| l1000_LT | none / fixed | NA | NA | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| l1000_LT | permuted / baseline | 0.2452 | 0.2069 | 1.0000 | 0.3384 | 0.1642 | 0.3703 | 0.8730 |
| l1000_LT | reference / baseline | 0.1998 | 0.3172 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| l1000_LT | reference / discrimination | 0.1998 | 0.3305 | 0.0000 | 0.9700 | 0.9377 | 0.9984 | 0.3273 |
| l1000_LT | reference / fixed | 0.1998 | 0.4121 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| l1000_LT | reference / risk_select | 0.1998 | 0.3434 | 0.0000 | 0.9505 | 0.9398 | 0.9733 | 0.2437 |

## R2.7 Dependence, interactions and abstention

- sciplex3_B: reference-presence x baseline-versus-fixed interaction in local utility: +0.5480 [+0.4581, +0.6402]. This compares a planner that stops when forecasts are absent with fixed, which ignores them; it is not a WorldV2 interaction or superiority over an acting fixed policy.
- sciplex3_B: 48 distinct treatment plates; 4 connected dependency component(s). Adding the registered shared control-calibration strata gives 1 combined component. Physical plate/batch CI is not estimable from independent clusters. Chemical CIs condition on this assay and do not quantify physical replication; see `physical_controls.json`.
- l1000_LT: reference-presence x baseline-versus-fixed interaction in local utility: +0.0585 [+0.0285, +0.0911]. This compares a planner that stops when forecasts are absent with fixed, which ignores them; it is not a WorldV2 interaction or superiority over an acting fixed policy.
- l1000_LT: 1053 distinct treatment plates; 1 connected dependency component(s). Adding the registered shared control-calibration strata gives 1 combined component. Physical plate/batch CI is not estimable from independent clusters. Chemical CIs condition on this assay and do not quantify physical replication; see `physical_controls.json`.

Chemical intervals use 2,000 paired cluster-bootstrap draws at seed 20260930 on the exact frozen skeleton/component grouping, never cells/wells/episode rows as independent draws. Cost, errors, abstentions and correctness have their own cluster intervals in JSON. Matched acted episodes and jointly decided episodes report both policies' correctness, risk and costs at the same subset coverage. The jointly decided subset is outcome-selected and descriptive; it is not a deployable pre-action abstention rule or a risk guarantee. No matching is possible when none/constant abstains everywhere. A lower unconditional error rate alone is not general decision improvement.

## R2.8 Historical WorldV2 review, kept separate

Cached nested-model forecasts were rescored on identical previously acquired steps, with no new model calls. These models and purchased histories differ from the intervention freeze. They do not supply a full-menu forecast bank and cannot establish a forecast-swap effect.

- sciplex3_B: 6314 matched step records; with a purchased prompt, WorldV2-reference NLL -0.0098 [-0.0293, +0.0100].
- l1000_LT: 6198 matched step records; with a purchased prompt, WorldV2-reference NLL -0.0177 [-0.0325, -0.0052].

## R2.9 STATE interface

The inherited 14 served query/output pairs were independently checked: controls and labels stay fixed, embeddings match saved vectors, and six expression-perturbation seeds / three plate-label variants remain invariant. Nine new inferences repeat baseline, permutation and replacement at inference seeds 42, 77, 123: every perturbation is byte-identical to its own seed's baseline. This does not assert cross-seed equality.

| Target rows | Existing query | Relative L2 change from 378-row baseline |
|---:|---|---:|
| 38 | rows_10pct_s100 | 2.615666 |
| 94 | rows_25pct_s250 | 2.373517 |
| 189 | rows_50pct_s401 | 0.929526 |
| 189 | rows_50pct_s402 | 0.929526 |

Row deletion was independently retried and returned `unsupported_query` before inference, with no prediction. STATE action-ranking impact is unidentified: SciPlex3 B / L1000 LT have no registered STATE context and no consuming selector. This behavior is restricted to NCI-H596, registered Adagrasib 0.05 uM, fixed control and checkpoint. It establishes no support for unmeasured chemistry, new time or new dose. Checkpoint SHA-256, query/output hashes and exact inference commands are in `state/state_summary.json`.

## R2.10 Execution ledger, limitations and reproduction

Executed: source/raw-hash verification; all 39,408 episode-cell replays; four-arm cost-corrected reviews; reading/selected-action quality; ranking/action/terminal attribution; paired fixed contrasts; conservative unresolved-source bounds; matched-subset risk/cost; forecast-presence interaction; separate physical-connectivity analysis; cached WorldV2 reading review; STATE inheritance verification and nine fresh inferences; contract and existing planner/selector/state tests.

Not executed: WorldV2 forecast swap or WorldV2 x policy interaction; case-memory on this incompatible population; true-state-gain experiment; model training; external evaluation; production changes. Unidentified: physical-cluster CI, general decision improvement from abstention, STATE-to-action ranking, new-domain performance and source-comparable point effects on unresolved paths.

All output is under `outputs/identifiability_round2_20260930/`. `artifact_ledger.json` records input, output and source hashes, environment and commands; `predeclared.json` records the original run version, and resume receipts preserve the helper corrections. Review-stage failures were an extra argument to `fixed_star` and serialization of a structural validator infinity. Completed traces were preserved; no model/selector repair or production runtime defect was identified. An initial STATE comparison treated categorical dictionary changes as cell-value changes; comparing actual values confirmed control invariance. Failed attempts remain recorded.

Environment: `D:/anaconda/envs/maestro/python.exe`, Python 3.11.16; exact package versions in the run manifest and final ledger. Native numerical libraries were limited to one thread for the intervention run. New files use exclusive creation; to reproduce in another directory, run the source replays into that directory first, then use the same `--out` for all stages.

```powershell
& 'D:\anaconda\envs\maestro\python.exe' -m research.identifiability_audit.lineage_sciplex3 --out outputs/identifiability_round2_20260930/round1_replay/sciplex3_B
& 'D:\anaconda\envs\maestro\python.exe' -m research.identifiability_audit.lineage_l1000 --out outputs/identifiability_round2_20260930/round1_replay/l1000_LT
& 'D:\anaconda\envs\maestro\python.exe' -m research.identifiability_audit.unified_score --out outputs/identifiability_round2_20260930/round1_replay/unified_score
& 'D:\anaconda\envs\maestro\python.exe' -m research.identifiability_audit.round2 verify
& 'D:\anaconda\envs\maestro\python.exe' -m research.identifiability_audit.round2 run
# --resume was used only after the documented review failures; never overwrites completed task traces.
& 'D:\anaconda\envs\maestro\python.exe' -m research.identifiability_audit.round2 analyse
& 'D:\anaconda\envs\maestro\python.exe' -m research.identifiability_audit.round2_cached_world
& 'D:\anaconda\envs\maestro\python.exe' -m research.identifiability_audit.state_round2
& 'D:\anaconda\envs\maestro\python.exe' -m research.identifiability_audit.round2_physical_controls
& 'D:\anaconda\envs\maestro\python.exe' -m research.identifiability_audit.round2_validate
& 'D:\anaconda\envs\maestro\python.exe' -m research.identifiability_audit.round2_report
```

## R2.11 Conditional risk and matched coverage supplement

`matched_risk_summary.json` adds chemical-cluster 95% intervals for wrong-among-decided risk. Zero-decision cells have undefined conditional risk. The jointly decided subset has equal coverage for both arms but is outcome-selected; its costs and correctness are descriptive, not a new abstention policy.

| Task | policy with reference | decided coverage | wrong among decided (95% CI) |
|---|---|---:|---|
| sciplex3_B | fixed | 0.6636 | 0.0554 [0.0306, 0.0863] |
| sciplex3_B | baseline | 0.6375 | 0.0468 [0.0244, 0.0747] |
| sciplex3_B | discrimination | 0.5976 | 0.0488 [0.0276, 0.0760] |
| sciplex3_B | risk_select | 0.4788 | 0.0448 [0.0230, 0.0735] |
| l1000_LT | fixed | 0.0598 | 0.0836 [0.0242, 0.1748] |
| l1000_LT | baseline | 0.0668 | 0.0417 [0.0125, 0.0923] |
| l1000_LT | discrimination | 0.0629 | 0.0446 [0.0116, 0.1029] |
| l1000_LT | risk_select | 0.0282 | 0.1112 [0.0347, 0.2252] |

On L1000, risk-select reduces unconditional errors while its conditional wrong-among-decided risk is higher than fixed. A lower error count caused by lower decision coverage is not a general decision gain. Matched acted and jointly decided correctness/risk/cost summaries are retained for each cell.

Additional executed command: `python -m research.identifiability_audit.round2_risk`. Final scoped contract and log-layout checks: 15 passed (`delivery_tests.xml`), after the earlier 50-test planner/selector/STATE run. The complete production suite was not rerun because no production code changed.
