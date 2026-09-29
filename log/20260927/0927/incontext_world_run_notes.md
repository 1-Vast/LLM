# In-context world model: run notes (block 6, 2026-09-27)

**File summary**
- **Path:** `log/20260927/0927/incontext_world_run_notes.md`
- **Purpose:** the command sequence, timings and checks behind block 6. The report is
  `research/incontext_world/README.md`.
- **Core points:** E-WM1 and E-WM2 both pass their registered gates. The E-WM2 pass is robust on SciPlex3 only. Fold
  0 was added after a numbering error.

## Sequence (Asia/Shanghai)

| Time | Step |
|---|---|
| 19:41 | Request received; six preprints extracted to text with PyMuPDF; Codex session 01a0e152 (13:25-19:36) found to have added a single-cell population flow and signed readouts (left unchanged) |
| 19:51:43 | `research/incontext_world/spec.json` written, before any code of the package |
| 19:52-20:00 | `transition.py`, `metrics.py`, `world.py` written; synthetic sanity check; smoke test on SciPlex3 B fold 1 (empirical Bayes 60 s) |
| 19:54-20:02 | `e_wm1 run` (folds 1-5 as written in the spec): SciPlex3 160,860 rows (294 s), L1000 127,498 rows (159 s); the analysis step failed on a reader bug (the arm "null" read as missing) and was fixed in the reader only |
| 20:04-20:14 | `e_wm2 run --workers 4` on 20 tasks (folds 1-5): 585 s, 0 problems; fold-5 tasks produced 0 items |
| 20:15 | Registered folds found to be 0-4; the E-WM2 metrics had not been read |
| 20:15-20:21 | Fold 0 added with identical code: E-WM2 4 tasks (204 s), E-WM1 `--folds 0 --suffix _fold0` (89 s) |
| 20:22-20:25 | Registered analyses read; post-hoc diagnostics (`e_wm2 robustness`, `e_wm1 ceiling`) written and run |
| 20:25-20:45 | Report, log block 6, index, memory; research test suites run |

## Checks

- 6,601 E-WM2 episodes, identical to E-DATA1's episode count on the same protocol-v2.1 tasks.
- `public_view_problems` returned nothing for all 24 task records.
- No-prompt (H0) forecasts of the in-context world equal the reference world's (maximum NLL difference 0.0).
- No transition contains a held-out compound (tested).

## Files copied here

- `incontext_world_e_wm1_analysis.json`
- `incontext_world_e_wm2_analysis.json`
- `incontext_world_e_wm2_robustness_posthoc.json` (post hoc; the Spearman-Brown ceiling is in the report)
