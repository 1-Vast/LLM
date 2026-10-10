# Experiment record: 2026-10-10

> - **Path**: `log/20261010/README.md`
> - **Purpose**: Record the phenotype-anchored dual-core study: same-spheroid functional endpoints, a world-model value gate, one-time held-out evaluation and promotion of the verified contracts.
> - **Core points**: Registered null for STATE. Basal-similarity transfer beats STATE (delta r -0.23) and generic ranking (top-10 +0.56 log2, 5/5). The gate refused STATE from reference data, and held-out lines confirmed it. STATE wins only on predicted-cell G1. Three contracts promoted.

## 1. Record control

This record covers the block `research/astra/phenotype_anchor_20261010`, which was registered,
frozen at `2026-10-10T04:41:16Z`, evaluated once on held-out lines and verified.

Activity by other actors:

* Codex sessions in `D:\MAESTRO` this morning (09:56-10:58 local) wrote nothing to the tree.
  Their P0.5R work sits outside it, in `D:\MAESTRO_TMP`.
* STATE checkpoint files and the arc-state source were absent from `data/` (directories present
  but empty, stamped 2026-10-09 11:39). The cause is unattributed. Both were re-staged
  hash-identical.

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

## 3. Materials, data and computational environment

* Data: `arcinstitute/State-Tahoe-Filtered@fdf87abe`, read as range reads of obs codes and
  `obsm/X_hvg` rows only. 16.6 GB in 132,526 requests, each hashed in the study ledgers.
* Model: STATE `ST-HVG-Tahoe@ca6b7519` `final.ckpt` (sha256 `2c9b2e74…`), run with arc-state
  0.11.3 at commit `9bbfe78a`.
* Metadata: Tahoe drug and cell metadata, pinned and hash-verified.
* Compute: RTX 4060 Laptop GPU for 13,192 native forward sets in 179 s, and the `maestro` conda
  environment.
* LLM: DeepSeek `deepseek-flash`, 5 calls, $0.012.

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

## 9. Open items and next experiments

* Wire `admit_world_model` into the orchestrator's prediction path.
* Look for an endpoint whose reference ceiling clears the gate. Candidates are transcriptomic
  composition or longer-term phenotypes.
* Test basal transfer plus screening on independent pooled-screen data, such as PRISM or MIX-Seq
  units not used here.
* Read the Tahoe *Cell* phenotype formulas when access allows.

## 10. Curation provenance

Prepared from `RESULTS.json`, `GATE.json`, `VERIFIED.json`, `DEVIATIONS.json` and the test
receipts on 2026-10-10. No number in this record was typed independently of those machine
records. Frozen files were not edited after the freeze.

## Additional 2026-10-10 record

The same date also includes source-axis recovery, observation reliability and the P0.5R targeted
extension. Receipts are `AXIS_RECOVERY.json`, `P05R_EXTENSION.json` and
`RESEARCH_CONSOLIDATION.json`; protocols, source receipts and reproduction code are indexed in
`research/INDEX.md` and retained under `research/decision_value/axis_recovery_20261010/` and
`research/decision_value/axis_extension_20261010/`.
