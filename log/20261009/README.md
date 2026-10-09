# Experiment record: 2026-10-09

> - **Path**: `log/20261009/README.md`
> - **Purpose**: Record STATE readout calibration, joint-feedback development and decision-value comparison.
> - **Core points**: Readout calibration improves a bounded RNA prediction metric but not final equal-budget choices. Joint feedback improves some reference diagnostics but not exposed-target acquisition utility. Strict no-screen comparison does not establish screening value.

## 1. Record control

This record summarizes the three canonical development studies. No model was promoted to production.

## 2. Research questions and hypotheses

The studies tested a drug-shared STATE readout, a joint A/B feedback model, and whether information acquisition earns its cost versus no-screen.

## 3. Materials, data and computational environment

All studies use the frozen compact boundary packet and the authenticated signed 39-gene RNA endpoint. The same five previously exposed target contexts remain descriptive.

## 4. Experimental design and controls

Readout selection uses complete-cell nested fitting. Feedback is fitted on training contexts and compares identical information as well as adaptive acquisition. Decision value uses strict whole-context LOO, no-screen, matched KG and explicit purchase refusal when risk and costs are unregistered.

## 5. Experiment register and results

Readout MSE falls 2.17% on reference folds and 7.84% on exposed targets, with unchanged final selections. Joint feedback improves matched-information reference utility but adaptive target utility falls 0.87%. Joint KG adds 0.0000544 RNA utility over no-screen in strict LOO while using eight additional measurements; strict EVSI refuses.

## 6. Deviations, failures and corrections

Incomplete full-menu references remain explicitly blocked. No zero placeholder is treated as an observed outcome, and no previous development split is substituted for the registered LOO comparison.

## 7. Interpretation and claim boundaries

These are engineering and development results. They do not establish independent decision value, an LLM advantage, functional phenotype or mechanism causality.

## 8. Reproduction and artifact ledger

Canonical results: `STATE_READOUT_REPAIR.json`, `STATE_FEEDBACK_REPAIR.json` and `DECISION_VALUE_REPAIR.json`. Code and freezes remain in their named research directories. See `MANIFEST.json` for file hashes.

## 9. Open items and next experiments

Use qualified, previously unused units with authenticated functional outcomes and registered model-risk, utility, cost and failure contracts.

## 10. Curation provenance

This compact record preserves the canonical results and limitations. The content manifest is generated with `python -m tools.log_manifest`.
