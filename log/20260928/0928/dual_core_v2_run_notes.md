# Dual-core v2 run notes, 2026-09-28

**File summary**
- **Path:** `log/20260928/0928/dual_core_v2_run_notes.md`
- **Purpose:** the chronology of block 1 of 2026-09-28 (dual-core v2), with every disclosure in time order.
- **Core points:** what was seen before each freeze; what was changed after it; the one error in this block's
  own diagnostic and its correction.

| Time | Event |
|---|---|
| 09:42 | Start. Codex rollout `01a0e152` (the diagnosis, 08:22-09:39, and this brief, 09:39-09:41) idle; no tree change since the diagnosis. Block 7 code verified against its protocol digests (`e2.py` differs by block 7's own disclosed 23:15 post-hoc addition). |
| 09:45-10:05 | Phase A reproductions on saved outputs: P3 fallback in all 20 cells; lineage; event concentration; data integrity (no duplicates, genes aligned). Risk-forecast distributions read (outcome-blind) to set caps. |
| 10:05-10:16 | `risk_control.py`, `nested.py`, `world3.py`, `arms.py`, `run.py` and 22 tests. One execution-only pilot (SciPlex3 A, folds 0 and 1 held out): 0 problems, anchor 16/16, 60 s, selected sources and training log-likelihood gains printed. |
| 10:18:21 | `freeze.json` (32 files). Nested runs launched: 40 jobs, 3 workers, Python 3.14. |
| 10:18-10:29 | `analysis.py`; repaired Learn-then-Test on block 7's traces (all folds `no_candidate_certified`); risk ranking; data audit and power; `transfer_honest.py`, `e1_honest.py` (launched 10:22). |
| 10:29:21 | `freeze_population.json` (population protocol and the post-freeze analysis code). Population extraction; part 1 (registered verdict `no_population_signal_beyond_pseudobulk`); post-hoc fusion check with tempering and shuffle controls, labelled post hoc. |
| 10:46-11:05 | Population part 2 (maestro env); literature resolved through the bioRxiv and Crossref APIs; `report.py` written and debugged by an execution-only smoke test (section status only, no number printed). |
| 10:58 | `horizon_headroom.py`, first draft: correct and wrong eliminations were swapped by a sign error (`removed != truth` counted as wrong). Reported in the session as "170 of 202 wrong", then corrected within minutes by the refined version (95/31 SciPlex3 B; 18/4 A; 60/4 L1000 LT). Only the corrected numbers are recorded. |
| 11:06 | `analysis.load_runs` tags ablation rows with their job's model (after the addendum; no statistic changed) so the ladder can use the split design's test role only. |
| 11:09-11:12 | Repository suite in the maestro env: 1,369 passed, 0 failed (no `src/` or `tests/` file was changed by this block). |
| 11:18-11:19 | Last job; `report.py` scored all 40 jobs (0 problems, anchor 640/640). |
| 11:20-11:45 | Report, issue matrix, this record. |
