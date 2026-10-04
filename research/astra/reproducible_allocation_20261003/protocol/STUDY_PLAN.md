# Study plan and file ownership (written before any parallel edit)

Written 2026-10-03 23:50 +0800 by the parent session, before the three workstreams started.

## Question

Can reproducibility-aware predictions improve the allocation of a fixed resource budget between
screening, independent verification and stopping, beyond strong simple policies?

## Evidence status of the data

- Jaaks et al. 2022 (figshare 16843597, `original_screen_all_tissues_fitted.csv`, SHA-256
  `1188968c…a278`) was opened by `../feedback_validation_20261003` (its vault log lists the
  openings). **Every analysis of it in this study is EXPLORATORY** and must say so in its output.
- Outcome reads go only through `common.exposed_ticket(purpose, owner)`, which checks the earlier
  freeze is intact and appends to `protocol/access_log.jsonl`. The earlier vault log is never
  written.
- Data not yet opened (for example other GDSC releases, Nair et al. 2023) may be read for design
  columns only, until a protocol is frozen.

## File ownership

| Owner | May create or edit | Responsibility |
|---|---|---|
| parent | `__init__.py`, `common.py`, `protocol/`, `receipts/` (parent-level), `REPORT.md`, `RUN_MANIFEST.json`, `NEXT_PROTOCOL.json`, `test_reproducible_allocation.py`; outside this directory only the day log, `log/INDEX.md`, index docs and `pyproject.toml` test registration | Synthesis, any freeze, delivery |
| repeats (subagent 1) | `repeats/` only | Repeat provenance; prediction-model identification (scalar feedback correction) |
| allocation (subagent 2) | `allocation/` only | Budget conservation, physical resource accounting, allocation baselines (repaired exploratory replay) |
| review (subagent 3) | `review/` only | Statistical validity, stopping decisions, new-data qualification, novelty check, independent agent contribution; challenge of the other workstreams' assumptions |

Read-only for everyone: `research/certified_discovery/`, `research/astra/feedback_validation_20261003/`
(frozen; import, never edit), `research/astra/direction_exploration_20261003_v2/`, `src/`, `tools/`,
`tests/`, `data/` (except new downloads into `data/external/<new folder>/`, recorded in the
owner's download manifest), `log/`, all other documents.

## Shared rules

1. Write a plan file (`<owner>/plan.json`) with estimand, arms, metrics, units and stopping rule
   before the first outcome read of each new analysis. Record deviations; never edit a plan after
   its outcomes were read (write an addendum instead).
2. Units of inference are cell lines (stratified by tissue). Technical repeats, plates, seeds and
   repeated analyses are not independent biological experiments.
3. Unknown prices and resource quantities are recorded as unknown (`null` with a reason), never 0.
4. No new provider (LLM API) call without the parent's written approval; total new provider spend
   for the whole study is capped at USD 3 including retries. Never print or store credentials.
5. Downloads: only official public sources (figshare, the GDSC combinations portal, Europe PMC,
   publisher supplements, Zenodo, the authors' code repositories); no login, account or
   click-through; record URL, bytes, SHA-256 and time; never execute downloaded code.
6. Timestamps come from `date` or file times, never from estimates.
7. Nothing is committed or pushed. Outputs never overwrite an earlier result file.
8. Python: `D:/anaconda/envs/maestro/python.exe` with `PYTHONPATH="src;."` from `D:\MAESTRO`.

## Phases and gates

1. **Repair the exploratory verification comparison** (allocation). Equal feasible budget,
   carry-over, terminal verification capacity, branch-specific physical costs.
2. **What feedback can generalize** (repeats). Authenticate the repeat hierarchy or label it;
   fit the scalar correction `prior + lambda × feedback`, allowing lambda = 0; stop adding
   complexity if lambda is near zero or the correction does not beat the strongest simple baseline.
3. **Model × scheduler 2×2** (parent, with review). Frozen only if phases 1–2 meet their
   prerequisites and a qualified evaluation dataset exists; otherwise an executable protocol and
   a blocking receipt.
