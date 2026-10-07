# Mono pretraining study (2026-10-05)

Question: does public single-drug (GDSC2 fitted LN_IC50) supervision supply transferable action-comparison information for
ranking anchor x library pairs in a new cell line with sparse combination history, beyond strong simple rankings, same-architecture
scratch and permuted-pretraining controls? **Answer: no** (exploratory; E never evaluated). Read [REPORT_ZH.md](REPORT_ZH.md) first.

| Material | Role |
|---|---|
| [REPORT_ZH.md](REPORT_ZH.md) | Chinese research report (question, related work, data, protocol, results, verification, next experiment) |
| [PROTOCOL_V1.md](PROTOCOL_V1.md), [PROTOCOL_V1_1.md](PROTOCOL_V1_1.md), `FREEZE.json`, `FREEZE_V1_1.json` | Frozen protocol, one declared post-outcome development-only repair; hashes; v1 code snapshot in `archive_v1/` |
| `literature/` | agent A: 66-source related-work matrix, novelty assessment, design lessons |
| `data_s0/` | agent B: S0 identity/unit/QC/overlap contract (no label read), source manifest |
| `decisions/` | agent C: decision space, agent role, evaluation design, framework gaps, independent verification (`VERIFY_REPORT.md`) |
| `bilinear.py`, `combo.py`, `mono.py`, `common.py`, `run_s1.py`, `run_s2.py`, `analyze.py` | research code (not promoted to src/tools) |
| `posthoc_ceiling.py`, `posthoc_reliability.py` | post-hoc, unregistered diagnostics (HD only) |
| `results/` | S1/S2 outputs (large `mono_params/*.npz` and `mono_labels.csv.gz` are local state); `RUN_MANIFEST.json` hashes |
| `test_*.py` | synthetic/integration contracts (software correctness only) |

Gates: G1 passed, G2 passed (v1.1; failed in v1 because of an under-regularised grid), G3 failed -> E sealed. Heed the report's
limits: fitted-parameter transfer from one joint NLME fit; the base ranking was chosen on the same HD lines; line-only intervals
are narrower than line x pair intervals.

Run (repo root, `PYTHONPATH='src;.'`, `OMP_NUM_THREADS=1`, maestro env): see section 12 of the report. `FREEZE.json` is the v1 freeze
(its changed files are preserved in `archive_v1/`); `common.FREEZE` points to `FREEZE_V1_1.json`.
