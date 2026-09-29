# Premise forecasts for repair selection: qualification report

**File summary**
- **Path:** `research/premise_forecast/README.md`
- **Purpose:** block 5 of 2026-09-27. The owner's brief asked whether an evidence-audited, hypothesis-conditional
  forecast can improve the agent's choice of a missing-premise measurement over a conventional planner with the same
  actions, knowledge, observations, budget and validation rules. If current data cannot answer, it asked for the
  exact task, measurement or units that are missing.
- **Core points:**
  - **Not testable with current data (NOT_READY).** The census finds 0 target genes with a real discordance case
    and a context-matched engagement or proximal-activity measurement under the registered rule, and at most 4
    under any relaxation (30 required).
  - **Joint support is zero.** No context has references whose premise state is known independently, so
    P(premise result | hypothesis) cannot be estimated.
  - **Prerequisite fixes are done** (protocol v2.1): the menu comes from the study design, pools come from training
    folds, and the unit mean is primary. The MoA proxy task stays eligible but underpowered, as before.
  - **E-CAL1 fails its gate.** On the steps the planner **selected**, wrong-elimination forecasts are 2x too low;
    on the fixed order's steps they are close (0.96x and 1.23x). This is consistent with the optimizer's curse.
  - Steps 4-6 (forecaster, evidence audit as an ablation, forecast-ranked repair arm) were **not built**: no
    qualified task exists.
- **Interfaces / data:** `census.py`, `census_spec.json`, `test_census.py`, [TRACE.md](TRACE.md);
  `research/protocol_v2/{design,tasks_v21,e_data1,e_cal1}.py`, `protocol_v2_1.json`; outputs under
  `outputs/protocol_v2_1_20260927/` and `outputs/premise_forecast_20260927/`
- **Depends on:** `research/protocol_v2/`, `research/belief_planning/`, `src/evaluation/`, `src/maestro/`

Spend: $0 in provider calls, 0 wells, 0 days. Downloads were metadata only: LINCS 2020 (4 tables, 471 MB) and
JUMP-Target/CPJUMP1 (5 files, under 0.3 MB). Nothing was committed, and no production default changed.

## 1. What changed

| Item | Where | Default behaviour | Tests |
|---|---|---|---|
| Study-design tables: 2,444 planned SciPlex3 conditions (2,432 prepared plus the 12 hidden ones) and 102,586 planned L1000 conditions | `research/protocol_v2/design.py`; `outputs/protocol_v2_1_20260927/design/` (SHA-256 manifest) | new | `test_protocol_v2_1.py` |
| Lifecycle states kept separate from readouts, mapped back to protocol-v2 states without loss; design-based availability; per-fold pools | `research/protocol_v2/contracts.py` (`Lifecycle`, `lifecycle_state`, `readout`, `v2_state`, `design_availability`, `fold_pools`); `public_view(..., design=)` | v2 unchanged unless `design` is passed | 7 tests, each also asserting the v2 defect |
| Runner: a planned condition without a usable row is a charged QC failure | `research/protocol_v2/runner.py` (`design_menu=True`) | v2 unchanged | same |
| v2.1 tasks: training-fold pools, design eligibility | `research/protocol_v2/tasks_v21.py` | new | same |
| Unit-mean paired estimate with a unit bootstrap | `research/protocol_v2/headroom.py` (`unit_paired`) | new | same |
| Protocol version in records | `research/protocol_v2/registry.py` (`protocol_version=`) | default `external-validation-2` | existing 24 |
| Protocol v2.1, written before any run | `research/protocol_v2/protocol_v2_1.json` | - | - |
| E-DATA1 and E-CAL1 runners | `research/protocol_v2/e_data1.py`, `e_cal1.py` | new | via outputs |
| Premise-only census | `research/premise_forecast/census.py`, `census_spec.json` (written before the code ran) | new | `test_census.py` (3) |
| Audit E3: unregistered sources count as dependence-unknown, not independent | `src/maestro/provenance.py` (`is_registered`, `independence`) | `independent()` unchanged | `tests/test_evidence_audit_prerequisites.py` |
| Audit E5: engagement premises without a sample site are reported | `src/evaluation/cases.py` (`PublicCase.unsited_engagement_premises`) | reported, not enforced | same (3 tests) |

## 2. What was measured

### 2.1 E-DATA1: task and unit qualification under protocol v2.1 (MoA proxy task)

Unit mean, with 95% unit-cluster bootstrap intervals. Thresholds are those committed in
`research/gated_plan/registry.json` at `c3d2345`. 0 audit problems were found in any of the 20 tasks. The table
oracle reproduces the oracle arm's decisions in every episode.

| Task | Units (v2) | Episodes | Oracle - fixed* | Oracle - fixed | Units needed for +0.02 (belief SE) | Gate | v2 headroom (for reference) |
|---|---|---|---|---|---|---|---|
| SciPlex3 B | 105 (132) | 1,278 | **+0.070 [+0.041, +0.106]** | +0.068 | 314 | eligible, underpowered | +0.086 |
| L1000 LT | 205 (256) | 3,648 | **+0.047 [+0.023, +0.078]** | +0.044 | 714 | eligible, underpowered | +0.062 |
| SciPlex3 A | 34 (42) | 239 | +0.033 [+0.000, +0.096] | +0.033 | 645 | ineligible | +0.030 |
| L1000 T | 128 (170) | 1,436 | +0.004 [+0.000, +0.009] | +0.004 | 27 | ineligible | +0.001 |

- **Verdict: INCONCLUSIVE, and the registered failure rule applies.** Two tasks have eligible headroom, but none
  has the units a belief-like planner would need.
- **Fixed\* adds nothing.** The cross-fitted best fixed sequence matches the expert order in A and T, and differs
  by -0.003 (LT) and -0.002 (B) in correct decisions. In B it saves 0.064 measurements per episode.
- **Menu expansion.** On identical episodes, adding 72 h to SciPlex3 A's 24 h conditions raises the oracle
  ceiling by +0.132 [+0.050, +0.236]. Adding MCF7, PC3 and VCAP to L1000 A549 raises it by +0.044
  [+0.018, +0.074]. Both qualify, but both menus are already in the tiers, so this confirms what time and line
  choice are worth, not a new menu.
- **The fixes' visible effect.** Per-fold pools remove the classes that qualified only through held-out members, in
  18 of 20 tasks, and units fall by 19-25%. The design menu creates 16 (A) and 28 (B) charged QC-failure steps for
  the fixed order.

### 2.2 E-CAL1: wrong-elimination calibration on selected actions

The world model's forecast is scored on held-out steps, leave one study out. The unconditional forecast is scored
on the arm's executed valid steps; the selective risk on its decided episodes.

| Arm (how actions were chosen) | Step items | Observed / raw forecast, L1000 | SciPlex3 | Decided-episode risk: observed vs forecast, L1000 | SciPlex3 |
|---|---|---|---|---|---|
| belief (forecast-selected) | 6,981 | **1.98** | **2.10** | 0.051 [0.036, 0.072] vs 0.019 (2.65x) | 0.053 [0.041, 0.069] vs 0.016 (3.31x) |
| fixed (no forecast; forecasts computed after the fact) | 12,109 | 0.96 | 1.23 | 0.062 vs 0.060 (1.03x) | 0.064 vs 0.036 (1.78x) |
| myopic_edv (its own model) | 5,182 | 0.24 | 0.54 | 0.050 vs 0.135 (0.37x) | 0.050 vs 0.077 (0.65x) |

- **Gate: FAIL for every arm and bound.**
  - The planner's Jeffreys bound covers, but at 10-119 times the observed rate, which breaks the
    informativeness clause (at most 3 times).
  - The hierarchical and discounted bounds either cover only 58-89% of SciPlex3 strata (95% required), or sit
    4-26 times above the observed rate on L1000.
- **Consequence:** no forecast-driven stop and no risk claim.
- **Interpretation.** The same forecaster is about right where it did not choose the action, and about 2x
  optimistic where it did. This matches the optimizer's curse (Smith and Winkler 2006) and accounts for part of
  the historical "2-5x too low".
- **Limits of that reading:**
  - Selected and unselected steps are different populations, so this is not a controlled comparison.
  - The fixed order's SciPlex3 episodes are also 1.8x off.
- `safe` executed the fixed sequence in 6,596 of 6,601 episodes, so it is reported through `fixed`.

### 2.3 Census (E-AG1 stage 0): premise-only

The case rule is engagement_v1's: strong dependency (≤ -0.7); selective (≤ 30% of models dependent); expressed
(≥ 2 log2 TPM+1); drug inactive (IC50 absent or above the top dose); curve r² ≥ 0.5. Only design columns of
signature tables were read.

| Population | Cases | Target genes | Engagement in context | Proximal activity | Same-cell phenocopy | Both (joint) |
|---|---|---|---|---|---|---|
| **Registered:** PRISM 19Q4, single target, selective | 23 | 6 | 0 | 0 | 1 gene | 0 |
| PRISM single target, any dependency | 404 | 33 | 0 | 0 | 5 | 0 |
| Sensitivity: PRISM multi-target + GDSC2, selective | 1,175 | 54 | 0 | 0 | 6 | 0 |
| Sensitivity: PRISM multi-target + GDSC2, any dependency | 11,831 | 130 | **4** (ATR, BRD4, CDK1, HDAC3) | 0 | **29** | 0 |

- **Decision (registered rule, 30 clusters): NOT_READY** for biological agent validation, in every population.
  Phenocopy track: INSUFFICIENT. Joint task: NOT_READY.
- **Why engagement is 0 under the registered rule.** The only in-context engagement release (PISA living cells) is
  K562, and K562 is not in PRISM's secondary screen. The 4 genes appear only through GDSC2 and pan-essential
  targets, which is how engagement_v1 found its K562 cases.
- **Phenocopy is not engagement.** A same-cell compound signature beside a knockdown or knockout signature of the
  target is a pathway-level readout; `BiologicalQuantity` has no such member, and the typed rules would not accept
  it as engagement. Its 29 genes come from the most permissive population and are mostly pan-essential targets
  (CDK1, PLK1, AURKA/B, TOP1, TUBB, MTOR).
- **CPJUMP1 adds nothing.** Its A549 and U2OS discordance cases share 1 compound with JUMP-Target (colchicine), and
  its target TUBB is not on the CRISPR list.

## 3. What failed or could not be tested

| Step of the brief | Status | Evidence |
|---|---|---|
| 1. Trace; missing connection; methods | **Done** | [TRACE.md](TRACE.md) |
| 2. Evaluation defects fixed, versioned, historical results kept | **Done** | protocol v2.1; v2 records untouched; 7 tests |
| 3. Qualified decision task: headroom, units, selected-action calibration, census | **Done, negative** | E-DATA1 INCONCLUSIVE (underpowered); E-CAL1 FAIL; census NOT_READY |
| 4. Research-only vertical slice (forecaster) | **NOT_READY, not built** | no qualified task; P(result \| hypothesis) has no data (sensitivity unknown; 0 independent references) |
| 5. Biological evidence audit, evaluated before ranking | **Partly.** Two audit prerequisites are closed (E3, E5) as reported properties. The audit as an ablation is NOT_READY | an ablation needs forecasts connected to actions on a qualified task |
| 6. Forecast-ranked repair arm with prediction-free fallback | **NOT_READY, not built** | same |
| Agent × world-model interaction | **NOT_READY**; no estimate made | no task holds both a genuine premise gap and a forecastable readout (joint = 0) |

## 4. Exactly what is missing

1. **Task and units.** At least 30 target-gene clusters of discordance cases in which the missing premise can be
   measured in the case's own context: the same cell line, a dose within the phenotype assay's range, intact cells.
   Available: 0 under the registered rule. The binding limit comes before capabilities: only 23 selective cases (6
   genes) exist in PRISM's single-target annotations.
2. **Measurement.** An engagement or proximal-activity assay run in the discordance contexts.
   - Local releases cover K562 only (PISA), and PISA's exposure is undeclared.
   - At the package's declared price for a condition-matched engagement assay (24 wells, 4 days per case,
     `evaluation/engagement_cases.py`), 30 cases need about 720 wells.
3. **References for the forecaster.** At least 20 cases per hypothesis branch whose premise state is known
   independently, plus positive controls to measure the assay's sensitivity.
   - Candidates: the concordant-support pairs (420 PRISM cases, 27 genes: a strong selective dependency and an
     active drug), assayed for engagement in the same context.
   - At the same price, 40 controls add about 960 wells.
   - Until then P(not engaged | engaged) is `unknown`, and any forecast must refuse.
4. **A calibration base on selected actions.** Forecasts must be checked on the actions the planner would choose,
   not on all actions. E-CAL1 shows the difference is about 2x.

## 5. Go / no-go

| Decision | Items |
|---|---|
| **GO** | Keep protocol v2.1 as the evaluation boundary for new runs. Use the census as the gate for any agent study. Register E-DATA1, E-CAL1 and the census from a clean commit when the owner commits. |
| **NO-GO** | Building the forecaster, the audit ablation or the forecast-ranked repair arm; any Agent × world-model estimate; any planner-superiority test on SciPlex3 or L1000; any production-default change; any use of phenocopy as an engagement premise |
| **Owner decision** | Whether to commission the missing measurement in item 2 above (about 720 wells for cases, plus about 960 for sensitivity controls, at the declared price), or to register a separate premise type for pathway phenocopy, which needs its own validation |

## 6. Reproduction

Environment: Windows 11, Git Bash, `C:\Python314\python.exe`, with `PYTHONPATH="D:/MAESTRO;D:/MAESTRO/src"` for
research modules.

```bash
python -m research.protocol_v2.design
python -m research.protocol_v2.e_data1 run --workers 5
python -m research.protocol_v2.e_data1 analyse
python -m research.protocol_v2.e_cal1
python -m research.premise_forecast.census
python -m pytest research/protocol_v2 research/premise_forecast -q -p no:cacheprovider -o addopts=""
python -m pytest tests -q -p no:cacheprovider
```

The run record is `outputs/protocol_v2_1_20260927/e_data1/run_record.json`: `development_unregistered`, commit
`c3d2345`, dirty tree. Download provenance is in `data/external/lincs2020/provenance.json` and
`data/external/jump_target/provenance.json`.

## 7. Disclosures

- **Not registrations.** The tree held another session's uncommitted reorganisation, so `registry.register`
  refuses it. The runs are development records. Thresholds come from files committed before this block
  (`c3d2345`) or written before the runs (`protocol_v2_1.json` at 18:07, `census_spec.json` at 18:15; the first
  run started at 18:12 and the census ran after 18:15).
- **Two files edited after their runs, without changing any rule:**
  - the `written_at` fields of both specification files were corrected from estimated times to the file times;
  - `protocol_v2_1.json`'s pool note was completed ("18 of 20 tasks") before E-DATA1 ran.

  The run record's protocol digest therefore refers to the earlier bytes.
- **Sensitivity populations were added after the census specification** and are labelled as such. They cannot
  change the decision: the registered population gives 0 and every relaxation stays below 30.
- **The pool comparison was seen before writing the protocol** (a construction check; no outcome was read).
- **All development data are exposed.** Nothing here is external or confirmatory. GSE70138 was not used.
