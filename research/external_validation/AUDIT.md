# Repository and evidence audit (Phase 1)

**Date:** 2026-09-27, before the protocol was registered. It is based on the code at commit
`d011fcd` and the records it names. An assumption the repository cannot confirm is marked
**unknown**.

## 1. Which data are development or internal-validation only

| Study | Local path | How it has been used | Status |
|---|---|---|---|
| SciPlex3, Figshare 24681285 (CC BY 4.0) | `data/raw/sciplex3/` | Every acquisition block of 2026-09-26: blocks 2–4 and sparse-value, at tier A (A549, 24 h and 72 h) and tier B (A549 and MCF7, 24 h) | **development** |
| LINCS L1000 Phase I (GSE92742, `subset48` cache) | `data/external/lincs_l1000_phase1/` | Block 4's pre-registered fallback test, then the sparse-value design and its replay (tiers LT and T) | **development**; the block-4 test was the last use that was independent |
| Tahoe-100M subset `c39.h5ad` (NCI-H596) | `data/external/arc_state/tahoe_metadata_source/` | HVG alignment for the ARC State adapter; State itself was trained on Tahoe-100M | unused by decision work; **incompatible** (candidate audit) |
| sciPlex-GxE (GSM7056149) | `data/raw/kinome_gxe/` | Never used | **unassessed** |
| DepMap, PRISM, GDSC2, Nyman 2020, Hill 2017, PISA, kinobeads, CGI, combination sources | `data/raw/`, `data/external/` | Other programme blocks | out of scope (not transcriptome-response decision data) |

No local study is both unseen and compatible with MAESTRO's episodes. The one that would be,
L1000 Phase II (GSE70138), is not local.
[`manifests/external_candidates.json`](manifests/external_candidates.json) gives the facts, the
files and their sizes.

## 2. Components that depend on data

| Component | Where it lives | Chosen or fitted on |
|---|---|---|
| Validator floor and margin | `dynamic_world_model/common.py` `calibrate` | Each fold's training compounds, over a grid (floor 0.1–0.3, margin 0–0.3, at most 0.05 wrong eliminations per reading) that was set on SciPlex3 |
| Detection threshold | `common.detection_null`, `lincs_prepare.vehicle_null` | Vehicle wells or DMSO signatures only: no compound outcome enters |
| Tier pools and eligible compounds | `common.tiers`, `lincs_prepare` | Class counts over **all** compounds, held-out ones included (see §3) |
| Fixed sequence, SciPlex3 tier A (24 h then 72 h) | `sequence_audit/policies.py` | Chosen after block 2 found 72 h decisive, on the same episodes |
| Fixed sequence, tier B and L1000 | same | By analogy (early then late, or second line); L1000's was pre-registered in block 4 |
| Terminal utility +1 / −2 | shared | A declared constant |
| Two-step smoothing and fallback | `acquisition_followup/two_step.py`, `sequence_audit` | Designed on SciPlex3 (block 4) |
| Discrimination selector | `src/maestro/acquisition.py` | A 2× break-even gate (the utility's), a one-sided 95% lower bound (z 1.645), Jeffreys 0.5, and minimum one reference (chosen after the block-2 audit on SciPlex3) |
| Sparse-value model and price | `sparse_value/model.py`, `policy.py` | κ 2, Jeffreys 0.5, the price grid and the 0.02 ablation point, set after the SciPlex3 and L1000 diagnosis |
| Virtual cell (structure kNN) | `dynamic_world_model/episodes.py` `Magnitude` | A rule, not a fit: five nearest training compounds, 24 h only (the served rung's domain) |
| Prompts | `dynamic_world_model/agent_arms.py` | Zero-shot; wording developed during block 2's SciPlex3 smoke runs |
| Retrieval libraries | per-fold `FoldTables`; `data/virtual_cell/sciplex3_signature_library` | Training folds of the same study; the tool library is built from SciPlex3 |
| Probability calibration | none | No recalibration layer exists; forecasts are smoothed reference frequencies |
| Baseline selection | per block, by hand | No frozen rule existed before this block |

## 3. Where hidden outcomes could leak

- **Policy context (fixed in this block).** Every research arm received the whole data object,
  including the held-out compound's profiles, QC fields and mechanism annotation at every
  condition, plus its detection flags. No arm was found reading them, but nothing prevented it.
  The arms now receive a sealed copy (`firewall.seal`). Two tests fail if a policy could read a
  hidden result:
  - two studies differing only in held-out results give identical views and choices;
  - the view holds no held-out row.
- **Episode design.** The tier pools and eligible compounds are computed from class counts that
  include the held-out compounds. The labels therefore shape which contrasts exist; they do not
  reach any policy. This is recorded, not repaired, because changing it would change every
  earlier result.
- **Plates and batches.** SciPlex3 hashing and L1000 plating put held-out and reference compounds
  on shared plates.
  - Block 4 found a same-batch nearest template in 0.44 of L1000 wrong eliminations, against a
    base share of 0.31.
  - Internal folds therefore cross batches. This harness reports it.
  - An external boundary must be batch-disjoint, and `boundary_report` refuses it otherwise.
- **Optimism within training.** The reference readings are leave-one-compound-out. Another
  reference with the same skeleton can still raise the in-training similarity, which makes
  forecasts optimistic. It is not a test leak (noted by the sparse-value record).
- **Designs tuned on their own test data.**
  - Designed on the data they are later scored on:
    - the tier-A fixed sequence;
    - the validator grid;
    - the selector's minimum support;
    - the fallback;
    - the sparse-value constants.
  - Every internal result is therefore optimistic for those designs. For the fixed sequence this
    works against MAESTRO.
- **Prompt examples.** None exist: the registered prompt is zero-shot, and a test checks that it
  contains no compound identifier from either study.
- **Virtual-cell training data.** ARC State was trained on Tahoe-100M. A State-based arm on any
  Tahoe study would have seen it. The structure-kNN virtual cell used here draws its neighbours
  from training folds only.

## 4. What the current claims rest on

| Claim | Status | Record |
|---|---|---|
| The production selector ignores virtual-cell output | **supported** (code and probe) | `acquisition_link/README.md` |
| Exposure time (72 h) decides slow mechanisms in SciPlex3 | **internally supported, post hoc** | block 2 |
| The two-step policy lost to the fixed sequence by stopping on uninformed references | **supported** (diagnosis) | `sequence_audit/README.md` |
| The fixed-sequence fallback | **SHADOW**: negligible on L1000, its one independent test | `sequence_audit/README.md` |
| The sparse-value policy beats the repaired fallback on net value | **internally supported** on L1000 LT; **inconclusive** on SciPlex3 | `sparse_value/README.md` |
| The sparse-value policy beats marginal-only | **inconclusive** (+0.0005 [−0.0055, +0.0060]) | same |
| Virtual-cell predictions improve measurement choice | **not demonstrated** | blocks 2–3 |
| The discrimination selector beats magnitude | **inconclusive** | block 3 |
| Probability calibration is adequate for risk-weighted choice | **not demonstrated**: SciPlex3 A ECE 0.139, optimistic | `sparse_value/README.md` |
| MAESTRO beats simple baselines on an unseen study | **not tested**: blocked | this block |
| Jev lowers the cost of reaching an admissible action | **not demonstrated** | task.md |
| Provenance of the `subset48` representation | **unknown**: its runner is missing | block 4 |

## 5. Reused without modification

- **Runner and audit** (`research/sequence_audit/policies.py`): `run_matched`, `legal_menu`,
  `audit_record`, `Setting`, `fixed`, `production` and `discrimination` (the last is the reference
  for `maestro`).
- **Episodes and validator:**
  - `research/dynamic_world_model/episodes.py`: `execute`, `episode_list`, `contexts`, `Magnitude`;
  - `research/dynamic_world_model/common.py`: `read_profile`, `build_fold_tables`, `calibrate`,
    `evidence_update`.
- **Models and planners:**
  - `research/sparse_value/model.py`: `SparseReferenceModel`;
  - `research/sparse_value/policy.py`: `make_policy`, `best_single`, `value`, `note`;
  - `research/acquisition_link/evaluate.py`: `ReferenceCardForecaster`, `registered_rules`,
    `magnitude_priorities`.
- **Selectors** (`src/maestro/acquisition.py`, `src/maestro/selection.py`):
  `select_discriminating_action`, `outcome_consequences`, `BudgetedEvidenceSelector`,
  `select_expected_coverage`.
- **L1000 loaders and unit definitions:**
  - `research/sequence_audit/lincs_prepare.py`: `load`, `tiers`, `setting`;
  - `research/sequence_audit/lincs_evaluate.py`: `context`;
  - `research/sequence_audit/analyze.py`: `sciplex3_units`;
  - `research/sequence_audit/lincs_analyze.py`: `units`.

The external harness now also depends on the typed policy boundary and the opt-in
decision-sensitive acquisition API in `src/maestro/`. The historical production and replay
defaults remain unchanged.

## 6. Defects fixed in this pass

The two README files that previously contained Chinese prose were translated to English, so
`tests/test_repository_shape.py::test_project_markdown_has_no_chinese_prose` is green. Episode
menus now have an explicit metadata-only builder; strict external contexts build class support from
non-held-out references and attach truth only after the candidate menu is fixed. The policy firewall
projects only visible evidence into `maestro.policy.PolicyInput`, rejects evaluator-only fields, and
copies revealed profiles. Small or separated calibration strata use a bounded Jeffreys/Beta-Binomial
fallback and report direct wrong-risk upper bounds. No policy passed a promotion gate.
