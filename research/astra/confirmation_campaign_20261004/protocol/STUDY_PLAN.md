# Study plan and file ownership (written before any parallel edit)

Written 2026-10-04 by the parent session; file time 12:36:23 +0800. An estimated "12:40" typed
first was corrected to the file time before the freeze.

## Question

Under identical two-orientation history, an identical two-round deadline and an identical binding
resource cap, does the confirmation-aware predictor R obtain more measured confirmed discoveries than
the development-selected strongest simple predictor? Separately, does purchased target-line feedback
improve relative action value beyond a line-level correction? The registered details are in
`campaign_contract.json`. It is frozen in `freeze.json` before the first outcome read.

## Evidence status

Jaaks 2022 is EXPOSED. Every result of this study on it is EXPLORATORY. Outcome reads go only
through `common.exposed_ticket(purpose, owner)`. That call refuses until the contract is frozen,
checks both freezes, and appends to `protocol/access_log.jsonl`. Earlier studies' logs and files
are never written.

## File ownership

| Owner | May create or edit | Responsibility |
|---|---|---|
| parent | `__init__.py`, `common.py`, `protocol/`, `receipts/`, `REPORT.md`, `RUN_MANIFEST.json`, `EVALUATION_PROTOCOL.json`, `test_confirmation_campaign.py`; outside this folder only the appended day-log entry, `log/INDEX.md`, index docs and `pyproject.toml` test registration | Contract, freeze, synthesis, delivery |
| design (subagent) | `design/` only | Predictors, P2/P3 campaigns, comparator and f selection on development lines, evaluation on E, power for the exact contrast, the gated feedback diagnostic |
| resources (subagent) | `resources/` only | Receipt reproduction, cap versus consumption, 1/2/3-round frontier with stopping, physical accounting, native-plate replay with co-produced measurements |
| verify (subagent) | `verify/` only, plus new design-only downloads under `data/external/<new folder>/` | Pre-freeze challenge of the contract; independent re-implementation of the primary contrast; leakage, budget, stopping and condition-identity checks of the other workstreams' code; data qualification and blocker recovery |

Read-only for everyone: all earlier studies (`research/certified_discovery/`,
`research/astra/feedback_validation_20261003/`, `research/astra/reproducible_allocation_20261003/`,
`research/astra/direction_exploration_*`), `src/`, `tools/`, `tests/`, `log/`, other documents.

## Shared rules

1. No outcome read before `protocol/freeze.json` exists. Before its own first outcome read, each
   workstream writes `<owner>/plan.json` with the SHA-256 of the analysis code it will run.
   Deviations go into an addendum; a plan is never edited after its outcomes were read.
2. Development selection uses HD lines only. E outcomes are used only after the selection file is
   written and hashed.
3. Units are cell lines, with role assignments paired within a line. Plates, seeding events, role
   assignments and seeds are never independent units.
4. Unknown prices, labour, capacity and days are recorded as null with a reason, never 0.
5. No provider API call without the parent's written approval (cap USD 3 including retries; no
   secrets printed).
6. Downloads: official public sources only, no login, recorded with URL, bytes, SHA-256 and time;
   downloaded code is never executed.
7. Timestamps come from `date` or file times.
8. Nothing is committed or pushed. Outputs never overwrite existing files.
9. Python: `D:/anaconda/envs/maestro/python.exe` with `PYTHONPATH="src;."` from `D:\MAESTRO`.
   Write multi-line scripts to files, not shell heredocs, because apostrophes break heredocs in this
   harness.
10. Deviation from the user-level AGENTS.md worktree guidance: the prior studies this work depends
    on are untracked. A git worktree would not contain them, so work happens in the main tree under
    disjoint folders.
