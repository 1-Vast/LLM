# Experiment record: 2026-10-10

> - **Path**: `log/20261010/README.md`
> - **Purpose**: Record two dual-core blocks. P1 tests same-spheroid functional endpoints with a world-model value gate. K tests measure-or-predict for later fate, across platform and time.
> - **Core points**: P1 is a registered null for STATE: basal transfer beats it (delta r -0.23), and the gate refusal held. In K, STATE's forecast does not transport to MIX-Seq (it harms the prior, -0.09 [-0.18, -0.005]). The gate's development MEASURE_EARLY call failed on 48 confirmation lines (-0.02 [-0.11, 0.08]). For trametinib, 5-day information accrues only at 24-48 h. An interval-based planner and two tools are promoted.

## 1. Record control

This record covers the block `research/astra/phenotype_anchor_20261010`, which was registered,
frozen at `2026-10-10T04:41:16Z`, evaluated once on held-out lines and verified.

Activity by other actors:

* Codex sessions in `D:\MAESTRO` this morning (09:56-10:58 local) wrote nothing to the tree.
  Their P0.5R work sits outside it, in `D:\MAESTRO_TMP`.
* STATE checkpoint files and the arc-state source were absent from `data/` (directories present
  but empty, stamped 2026-10-09 11:39). The cause is unattributed. Both were re-staged
  hash-identical.

**Block K** (`research/astra/kinetic_horizon_20261010`) was registered, frozen at
`2026-10-10T09:13:29Z`, run once on sealed tiers (receipts 09:13:40-09:16:51Z) and verified.

The same 2026-10-09 event had also emptied most other `data/external` and `data/raw` folders,
including PRISM, DepMap and LINCS. The needed public sources were downloaded fresh and
md5-verified.

Commit `e450d27` removed `research/astra/zeroshot_context_20261007/` from the tree. Block K does
not depend on it.

## 2. Research questions and hypotheses

Do frozen STATE zero-shot forecasts for checkpoint-held-out lines, read through a bridge fitted
on same-spheroid reference data, predict and select the drugs that selectively reduce a line's
survival? They must do so beyond basal-similarity transfer, lineage, driver-target knowledge and
an LLM prior.

Hypotheses:

* H1 (primary): prediction, STATE vs basal transfer.
* H2 (co-primary): top-10 decision, against basal transfer and against no context.
* H3: combination with basal transfer.
* H4: predicted-cell G1 readout.
* H5: LLM knowledge prior.
* D2: 8-well screening.
* Gate: does a perfect forecast clear the minimum useful benefit (0.05 r) on references?

**Block K** asks whether a virtual cell's forecast of the early (24 h) state can stand in for
measuring it when the decision concerns 5-day viability, and whether a failure is due to the
ceiling, to transport or to timing.

Registered tests:

* M1 (primary): a 24 h measurement complements a DepMap-scale prior.
* M2: STATE forecast transport.
* M3: top-10 line decisions under the measure-or-predict policies.
* T1-T3 (trametinib time course): when to observe, the temporal fingerprint, and the kinetic
  readout as a rate.
* K1-K3 (Tahoe 24 h to PRISM): the selectivity ceiling, potency (kinetic versus share) and the
  G1 sign.

## 3. Materials, data and computational environment

* Data: `arcinstitute/State-Tahoe-Filtered@fdf87abe`, read as range reads of obs codes and
  `obsm/X_hvg` rows only. 16.6 GB in 132,526 requests, each hashed in the study ledgers.
* Model: STATE `ST-HVG-Tahoe@ca6b7519` `final.ckpt` (sha256 `2c9b2e74…`), run with arc-state
  0.11.3 at commit `9bbfe78a`.
* Metadata: Tahoe drug and cell metadata, pinned and hash-verified.
* Compute: RTX 4060 Laptop GPU for 13,192 native forward sets in 179 s, and the `maestro` conda
  environment.
* LLM: DeepSeek `deepseek-flash`, 5 calls, $0.012.

**Block K** data:

* PRISM Repurposing 19Q4 (figshare 9393293 v4; 391 MB, md5-verified).
* MIX-Seq, scPerturb copy (`mcfarland_2020.h5ad`, 1.46 GB, sha256 `94a72400...`).
* DepMap 19Q4 CCLE expression (301 MB, md5-verified).
* The candidate STATE gene order (Rhaister `static_2k_genes.json`). It is supported by
  cross-platform line identity (18 of 18; null 0.03) but is not certified by lineage.

Compute: STATE ran 5,421 forward sets in 143 GPU seconds. There were no LLM calls.

## 4. Experimental design and controls

**Endpoints.** Relative survival (spheroid share against same-plate DMSO, with a
reference-line denominator) and phase log-odds shift. The target is selectivity versus the
reference panel.

**Units.** 40 count-qualified reference lines for all fitting, using leave-one-line-out. Five
lines are refused as `CONTEXT_UNDERCOUNTED`. The five held-out lines are used once.

**Arms.**

* Controls: a zero arm (no context), same organ, driver-target and context-permuted STATE.
* Baseline: basal kernel transfer.
* STATE: bridge and response-profile kernel readouts.
* LLM shortlist.
* Observed-RNA oracles.

**Analysis.** Drug-cluster bootstrap (MoA-fine, 2,000 resamples). Success requires the CI to
exclude 0 and at least 4 of 5 lines to improve. All choices were made on references before the
freeze; section 9 of the protocol discloses what was seen beforehand.

**Block K design.**

* Units are cell lines. Splits are fixed before outcomes were parsed (seed 20261010):
  * Tahoe: 15 development and 16 confirmation lines;
  * MIX-Seq: 24 development and 48 confirmation unseen lines;
  * the 24-line time course, plus about 400 external PRISM reference lines.
* Priors (development-chosen): PCA-ridge or kernel on CCLE expression. Combinations are
  equal-weight z-sums with no fitted weights.
* Controls: permuted-context STATE, a random expectation, the same-line cross-platform ceiling
  and a cross-experiment replicate.
* Analysis: line bootstrap (2,000 resamples).
* Sealed tiers refuse by name before the freeze. The Tahoe zero-shot PRISM tier stays sealed.

## 5. Experiment register and results

| Step | Result |
|---|---|
| Qualification (reference) | Survival interaction replicates at r 0.40 across plates and 0.35 across doses. Spheroid totals do not replicate (r -0.12). |
| Gate (reference LOO) | B r 0.527; RNA-profile oracle 0.530; bridge oracle 0.148. Margin 0.003, so `WM_CEILING_BELOW_MUB`. |
| H1, STATE vs B | -0.226 [-0.266, -0.156], 0/5: fails |
| H2, STATE vs B, top-10 | -0.167 [-0.239, -0.004], 1/5: fails |
| H2, STATE vs Z, top-10 | +0.391 [0.169, 0.671], 4/5: passes |
| B vs Z, top-10 | +0.558 [0.235, 0.819], 5/5: passes |
| Gate check, oracle vs B | -0.037 [-0.086, 0.003]: the refusal holds |
| STATE vs permuted STATE | +0.375 [0.311, 0.452], 4/5 |
| H3, SB vs B | -0.069 [-0.092, -0.031]: fails |
| H4, STATE G1 cells vs B | +0.254 [0.156, 0.367], 4/5: passes |
| H5, LLM vs organ | -0.144 [-0.239, -0.000]: fails |
| D2 screen | Gains of +0.15 to +0.31 for every prior. Best: B with screen, 0.126 |

**Block K** (`KINETIC_HORIZON.json`):

| Step | Result |
|---|---|
| Development gate (point estimates) | MIX-Seq: ceiling +0.139, STATE -0.150, so MEASURE_EARLY. Tahoe 5-day selectivity: ceiling -0.182, so USE_PRIOR. |
| M1, 24 h measurement over the DepMap prior | -0.021 [-0.109, +0.078], 4/6 drugs: fails |
| M2, STATE forecast over the prior | -0.091 [-0.182, -0.005]: transport refusal confirmed |
| M2, STATE line-specific RNA r | trametinib 0.059 [0.032, 0.082]; others about 0. Split-half ceiling 0.35-0.79 |
| M2, same line Tahoe vs MIX-Seq / pool A vs pool C | 0.13 or less / 0.65 |
| M3, top-10 measurement policy vs prior | -0.061 [-0.165, +0.169], 2/6: fails |
| T1, 5-day r of response magnitude by time | 3 h 0.21, 6 h 0.25, 12 h 0.31, 24 h 0.56, 48 h 0.68. Increment over prior at 48 h +0.16 [0.01, 0.36] |
| T2, STATE 24 h forecast vs observed time course | generic r peaks at 12 h (0.43); 48 h 0.25 |
| T3, kinetic readout as a rate | pooled r 0.11 [-0.04, 0.24]: not supported |
| K1, Tahoe early state over the CCLE prior | -0.107 [-0.155, -0.059]: USE_PRIOR confirmed |
| K2, potency, kinetic vs share | +0.117 [-0.084, +0.363]: direction only |
| K3, G1 sign for top-variance drugs | +0.136 [+0.002, +0.254]: replicated |

## 6. Deviations, failures and corrections

* `verify.py` failed in Windows temporary-file cleanup after five checks had passed. It was
  rerun byte-identical under `ignore_cleanup_errors=True`, and all seven checks passed.
* The extractor gained a `--basal-rows` option before freeze.
* The first launches of the gate and the phase classifier were triggered one file early and
  failed without writing output.

All three are recorded in `DEVIATIONS.json`.

Two late additions are disclosed in protocol section 9:

* the kernel readout was added after a 10-line reference dry run;
* the protocol's D2 wording was corrected to match the implemented screen.

**Block K** (`DEVIATIONS.json`):

* **Independent arithmetic verification failed.** The frozen evaluator compared r(prior) on all
  lines against r(prior + measurement) on measurable lines only. A labelled post hoc paired
  re-analysis gives the same verdicts: M1 -0.018 [-0.107, +0.082]; M3 -0.030; M2 -0.098.
* **The development gate's MEASURE_EARLY call was a false positive.** Its interval, computed post
  hoc, was [-0.049, +0.298].
* The oracle's selections were removed from the poisoning store before the freeze.

## 7. Interpretation and claim boundaries

**What this study shows.** For this endpoint the decision-relevant information sits in basal
state, and even a perfect transcriptional forecast adds nothing over basal transfer. The gate
found this before held-out access.

**Limits.**

* n = 5 lines. Their RNA was exposed in earlier blocks; their phenotypes were unopened.
* The endpoint is 24 h relative share. Spheroid wells are not independent culture starts.
* G1 is RNA-derived, and the phase classifier reaches 0.66 accuracy against a 0.61 majority
  class.
* There is no apoptosis, efficacy, mechanism or general dual-core claim, and no claim of LLM
  value.

**Block K: what it shows.**

* The frozen virtual cell fails on transport. Its line-specific response knowledge is bound to
  Tahoe. Even the same lines' observed Tahoe responses do not predict their MIX-Seq responses,
  although MIX-Seq responses replicate between experiments.
* A 24 h measurement did not beat a strong prior on independent lines.
* For trametinib, decision-relevant information appears at 24-48 h.
* The early G1 shift has a drug-class-dependent relation to later fate.
* Gate decisions made from point estimates on 24 units are unreliable.

**Limits.**

* One time-course drug; 35-60 cells per line and condition.
* PRISM is a different assay from both single-cell platforms.
* The gene order is supported, not certified.

## 8. Reproduction and artifact ledger

Receipts in this folder:

* `PHENOTYPE_ANCHOR.json`: identities, gate, results, D2, refusals, verification and
  resources;
* core, study, verification and shape records (listed in `log/INDEX.md`).

Code, protocol and outputs: `research/astra/phenotype_anchor_20261010/`. Bulk arrays:
`data/external/tahoe_phenotype_20261010/` (git-ignored).

Promoted, with contract tests:

* `src/maestro/world_model_value.py`
* `tools/datasets/tahoe_phenotypes.py`
* `src/virtual_cell/context_transfer.py`

**Block K receipts in this folder:**

* `KINETIC_HORIZON.json`;
* `KINETIC_HORIZON_VERIFY.txt`;
* the core and research test receipts (`KINETIC_HORIZON_CORE.txt`, `kinetic_horizon_core.xml`,
  `KINETIC_HORIZON_TESTS.txt`, `kinetic_horizon_tests.xml`).

Code, protocol, gate, results and post hoc analyses are in
`research/astra/kinetic_horizon_20261010/`. Bulk arrays are in
`data/external/kinetic_horizon_20261010/`, `prism_19q4/`, `mixseq_scperturb/` and `depmap_19q4/`.

Promoted, with contract tests:

* `plan_measure_or_predict` in `src/maestro/world_model_value.py`;
* `tools/evaluation/increment.py`;
* `tools/analysis/platform_identity.py`.

## 9. Open items and next experiments

* Wire `admit_world_model` into the orchestrator's prediction path.
* Look for an endpoint whose reference ceiling clears the gate. Candidates are transcriptomic
  composition or longer-term phenotypes.
* Test basal transfer plus screening on independent pooled-screen data, such as PRISM or MIX-Seq
  units not used here.
* Read the Tahoe *Cell* phenotype formulas when access allows.
* After block K:
  * test the interval planner prospectively;
  * qualify a world model inside the decision's own platform before any use;
  * use 24-48 h observations, not 3-12 h ones, if early measurement is revisited;
  * test the class-dependent G1 sign as a stand-alone, registered hypothesis;
  * the Tahoe zero-shot PRISM tier remains unopened.
* `tests/test_repository_shape.py` asserts that no root `Innovation.md` exists (`e450d27`), yet
  commit `0ad2e50` re-added the file. This pre-existing failure is left for the owner to resolve.

## 10. Curation provenance

Prepared from `RESULTS.json`, `GATE.json`, `VERIFIED.json`, `DEVIATIONS.json` and the test
receipts on 2026-10-10. No number in this record was typed independently of those machine
records. Frozen files were not edited after the freeze. The same applies to block K: its numbers
come from its `RESULTS.json`, `GATE.json`, `VERIFIED.json`, `DEVIATIONS.json`, `posthoc/` JSONs
and the test receipts.

## Additional 2026-10-10 record

The same date also includes source-axis recovery, observation reliability and the P0.5R targeted
extension. Receipts are `AXIS_RECOVERY.json`, `P05R_EXTENSION.json` and
`RESEARCH_CONSOLIDATION.json`; protocols, source receipts and reproduction code are indexed in
`research/INDEX.md` and retained under `research/decision_value/axis_recovery_20261010/` and
`research/decision_value/axis_extension_20261010/`.
