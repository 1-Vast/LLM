# Dual-core innovation validation, 2026-10-21

Executed the dual-core innovation-validation brief. Package: [research/dual_core_innovation_validation_20261021](../../research/dual_core_innovation_validation_20261021/REPORT.md).
Decision: STOP_THIS_TASK_CONFIGURATION (PTV-1 / ProteinTalks public-data replay, published-label task, 7 final lineages, estimation pilot).

- World model (re-implemented ppODE, hidden 16): worse than the strongest conventional score on precision@5, calibration and as a confirmation score; trajectory pathway no help.
- Real feedback (functional, molecular, both): no gain over no update or ordinary kernel updating.
- Program search: 6 LLM requests (16,782 tokens, deepseek-flash), no accepted edit; conventional menu edit INCONCLUSIVE; combined claim NOT_TESTED.
- Frozen with 161 file hashes before the one-pass final run; `verify.py` passes 43 checks; 11 synthetic software tests pass.
- Resources: GPU 3,911 s; formal CPU training 13,040 s (dev), plus 6,334.95 s in eight aborted CPU selection attempts; no currency claim. Final outcomes are now exposed.
- Unrelated: `tests/test_repository_shape.py::test_repository_has_one_scientific_report_and_no_retired_release_tree` fails because of the concurrent `.build-1024-dgm-revision`.

## Repository cleanup

Removed the `.npz` predictions and `.pt` weights from `RUN/cpu_sel_aborted` (53,730,224 bytes). These belong to eight superseded CPU attempts and are absent from `FREEZE.json`; the eight small JSON records remain as the source for the 6,334.95-second failed-attempt resource total. Frozen code, selected models, final outcomes, and source datasets were retained.
