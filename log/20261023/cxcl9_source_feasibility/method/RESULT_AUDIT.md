# Independent saved-result audit

2026-10-23. **PASS_SAVED_ARRAY_RECONSTRUCTION**. Reconstructed 336 comparison groups / 1,160 numeric components, maximum absolute discrepancy **6.66134e-15**, and all 13 prediction-freeze SHA256 bindings match. Root experiment was neither imported nor rerun. Audit code is research/cxcl9_source_feasibility_20261023/method/audit_saved.py; machine-readable detail is RESULT_AUDIT.json.

## Actual verification scope

Read the frozen protocol, manifest, saved source/target arrays and predictions/results, and root predict.py for specification. Reimplemented affine prediction analytically by covariance, per-drug residual corrections as design-matrix operators, and kernel ridge via symmetric eigendecomposition rather than root's linear solve. From saved arrays independently recomputed all source grids (3 slope penalties and 9 kernel configurations), both P12 sample directions, five-method source selection, chosen configurations, all eight complete 24-element predictions, 15-condition mean/sample MSE, all three menu winners/regrets/MSE, duplicate dispersion, directional checks and final status for both lines and both preprocessing variants. Verified literal feedback membership 9/control4/test15. No raw assay aggregation was audited; saved raw counts/means are not independently authenticated here. This is additional audit computation, not a new biological experiment or independent task.

## Reconstructed substantive result

The frozen pilot label is **NOT_SUPPORTED_OR_MIXED**. For primary within-well-IQR data, source selection chooses global_affine in both lines:

| Cell | control-anchored MSE | selected global-affine MSE | anchored mean regret | selected mean regret |
|---|---:|---:|---:|---:|
| BxPC3 | .04559537 | .06453188 | .04320560 | .04320560 |
| AsPC1 | .01671126 | .01710335 | .00843245 | .01225829 |

Thus the selected updater misses the MSE gate in both primary lines and worsens AsPC1 menu regret. Untrimmed BxPC3 also misses the MSE gate (.06065237 anchored vs .07337203 selected global_affine). Untrimmed AsPC1 selects residual_kernel and narrowly improves MSE (.08109298 to .08067512) with unchanged regret (.29573018); this does not rescue the joint primary-and-sensitivity rule.

Do not collapse the result into “feedback is useless.” Fixed drug_slope improves primary anchored MSE in both lines (.03580812 BxPC3, .01582215 AsPC1), with unchanged regrets. But plain control_affine has .03583813 and .01192123 respectively; extra drug-feedback value is not established across both lines by those selected comparisons. Frozen half_shift achieves primary BxPC3 zero mean menu regret, while its untrimmed regret worsens from anchored .03448280 to .08763009. Primary AsPC1 drug_shift reaches zero regret while MSE becomes .05125277. These are preserved conventional tradeoffs, not post-hoc promoted winners or new mechanisms.

## Decision boundary

STOP the fixed pilot after this audit as specified. Strong trimming sensitivity and source-selection transfer failure do not establish a repeatable action-attributable structural error. No new feedback subset, transformation, graph editor or reserve access is justified by these held outcomes. The result rejects the frozen source-selected diagnostic claim; it does not prove all action calibration, mechanistic graphs, nonlinear worlds or RSI impossible. No dynamic state model, active agent, capability inheritance, joint increment or improved-improver was tested.

The prior role FINAL_SEAL.json is retained. A new RESULT_SEAL binds it and the audit artifacts/code without rewriting old independent opinions. Local hashes do not repair historical global provenance uncertainty. No new HTTP/API call, wet assay, raw outcome read, root fit rerun, or protected AL outcome access occurred in this audit.
