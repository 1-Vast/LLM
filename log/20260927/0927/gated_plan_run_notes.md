# Gated plan: run notes (block 4, 2026-09-27)

Chronology (+0800). Times are file modification times or approximate tool-output times. Full commands and results
are in `research/gated_plan/VALIDATION.md`.

| Time | Event |
|---|---|
| 13:32 | Tree as found: `e5ad68f` on `main` (the owner committed block 3 at 12:55). Untracked: `inspect/` and `reference_0927/` (Codex slides session, 12:00-13:49); `research/prompt_review_20260927/` (Codex prompt-review session, 13:25-13:32, which revised the owner's prompt into this block's brief). A further Codex session (13:31 onwards) assessed novelty read-only. |
| 13:33-13:44 | Read the production core, the research harness and the data paths. Counted raw cells for the 12 SciPlex3 conditions missing from the prepared table, and checked scaffold overlap across SciPlex3 folds. |
| 13:46 | `python -m research.gated_plan.probes` → `outputs/gated_plan_20260927/probes.json` (copied here as `gated_plan_probes.json`). |
| 13:48-13:49 | Tests: `research/protocol_v2` 24 passed; five invariant files in `tests/` 123 passed; `tests/test_repository_shape.py` 9 passed. |
| during the block | The owner's addendum on two-core attribution arrived and was folded into the same deliverables. |
| 13:52 | Deterministic replay of the engagement_v1 package, six offline arms (`--policy repair`, run `gated-plan-engagement-20260927`, 0 provider calls); copied here as `gated_plan_engagement_replay.json`. |
| 14:00-14:55 | Wrote `research/gated_plan/` (README, AUDIT, DATAFLOW, PLAN, REGISTRY, `registry.json`, VALIDATION). |

## Costs

- Provider calls: none ($0).
- Laboratory: 0 wells, 0 days.
- Compute: under 2 minutes in total (probes 26 s, replay 3 s, tests about 75 s).
- Downloads: none.
