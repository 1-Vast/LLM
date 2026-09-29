# Premise forecast qualification: run notes (block 5, 2026-09-27)

Chronology (+0800), from file modification times and tool output. Full commands and results are in
`research/premise_forecast/README.md` section 6.

| Time | Event |
|---|---|
| 17:51 | Tree as found: `c3d2345` on `main` (the owner's commit of block 4) plus another session's uncommitted repository reorganisation (Codex, 15:11-16:07: `src/maestro/planning.py` moved to `research/belief_planning/planner.py`, fixtures moved to `tests/fixtures/`, several unused evaluation modules deleted). Untracked: `inspect/`, `reference_0927/`, `research/prompt_review_20260927/`, `research/repository_cleanup_20260927.md`. A Codex prompt-design session was active and wrote nothing in the repository. |
| 17:52-17:59 | Read the reorganised tree: protocol-v2 contracts, runner, task loaders, L1000 pool code, engagement screening. |
| 18:00 | `python -m research.protocol_v2.design`: SciPlex3 2,444 planned conditions (2,432 prepared + the 12 hidden), L1000 102,586. |
| 18:02 | Per-fold pools built (`tasks_v21.py`); construction check: pools shrink in 18 of 20 tasks. |
| 18:07 | `protocol_v2_1.json` written (thresholds from `research/gated_plan/registry.json` at `c3d2345`). |
| 18:09 | `test_protocol_v2_1.py`: 7 passed after fixing the fixture fold (Panobinostat is in fold 3). |
| 18:12-18:15 | E-DATA1 run, 20 tasks, 6 arms, 5 workers (memory-limited host); 0 audit problems. |
| 18:15 | `census_spec.json` written. |
| 18:15-18:16 | E-DATA1 analysis. |
| 18:18-18:20 | E-CAL1 analysis (post-hoc forecasts for the fixed arm). |
| 18:21 | Downloads: JUMP-Target (commit `2da0551`), CPJUMP1 plate design (commit `56845c7`), LINCS 2020 `siginfo_beta`, `compoundinfo_beta`, `geneinfo_beta`, `cellinfo_beta` (10:21:08-10:21:50 UTC). |
| 18:25-18:45 | Census runs: primary population, then the sensitivity populations (added after the specification); two reader bugs fixed (a missing name in LINCS 2020; CPJUMP1 name keys). |
| 18:50-19:05 | Audit prerequisites E3 and E5 (`src/maestro/provenance.py`, `src/evaluation/cases.py`) with 3 tests; full production suite 1,348 passed; research suites 44 passed. |
| 19:05-19:30 | Wrote `research/premise_forecast/` (TRACE, README), index updates, this record. |

## Costs

- Provider calls: none ($0).
- Laboratory: 0 wells, 0 days.
- Downloads: 471 MB (LINCS 2020 metadata) and under 0.3 MB (JUMP-Target, CPJUMP1), metadata only.
- Compute: E-DATA1 about 3 minutes wall on 5 workers; E-CAL1 about 2 minutes; each census run about 2-3 minutes; tests about 12 minutes.
