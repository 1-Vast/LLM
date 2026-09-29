# Consolidation: Proven-Code Promotion Review and Report Taxonomy

Date: 2026-09-28. Executor: WorkBuddy agent session. Specification: `PROMPT_consolidation.md`
(designed 2026-09-28, executed the same day after viability-contrast v5b was completed and
recorded). Spend: $0, 0 wells, 0 downloads. No experiment was active or unrecorded at start
(outputs check: newest run directory `outputs/viability_contrast_20260928/` 19:39, recorded;
no python processes running).

## 1. Purpose

Execute the registered consolidation: (1) bring the repository to a state where every piece of
research code with a measured, reproduced positive result lives in `src/` or `tools/`, with
`research/` holding exploratory or negative-result work; (2) consolidate research reports under
an explicit categorized order.

## 2. Hard constraints honoured

- Contract tests treated as law: no `src/` package, tool folder, or forbidden filename was
  added or removed, so `tests/test_repository_shape.py` needed no same-commit change.
- Freeze integrity: promotion was evaluated as COPY+ADAPT only; in the event, zero files were
  copied. No frozen file was moved, renamed, or edited.
- In-progress work untouched: `research/viability_contrast/` and `research/dual_core_v2/`
  were read, never written.
- Surgical changes: only markdown placement, link targets, and index content changed. No
  Python source was modified.

## 3. Phase A — inventory

`research/CONSOLIDATION_INVENTORY.md` records all 22 blocks plus 10 root-level reports with
verdict (in each block's own registered words), freeze status, candidate modules, destination,
and evidence. Cross-checks against `task.md` sections 11-12 and `log/INDEX.md` are included.

## 4. Phase B — promotion decision: zero promotions

Every plausible candidate was verified against its own registered record, per the
specification's rule ("verify each against its evidence, do not assume"):

- `dual_core_v2` repaired pieces (`risk_control.py`, `nested.py`, `transfer_honest.py`,
  `world3.py`): the block's registered section 14 states "Production defaults and src/:
  Unchanged — Nothing above earns promotion"; each piece is assigned "Retain as the research
  standard". Promoting against the block's own registered recommendation would violate the
  evidence discipline in the specification's section 0.4.
- `incontext_world` `ridge_st`: positive on E-WM1/E-WM2 gates, but the block defers promotion
  to an owner decision requiring new contract tests, and the later registered record
  (`dual_core_v2` section 12) says "Do not promote".
- All other blocks: negative, inconclusive, design-only, archive, or already promoted.

Consequence: `src/`, `tools/`, and the contract tests are unchanged; no module was promoted
without a test, because no module was promoted.

## 5. Phase C — report taxonomy

- `research/README.md` rewritten as a categorized portal: (a) agent and decision core;
  (b) virtual cell and world models; (c) evaluation, risk control and validation methodology;
  (d) data, costs and assets; (e) literature and design sources; (f) engineering records.
  Every entry carries a verdict label and a link. The corrections/caveats paragraph and the
  reproduction section of the previous index were retained.
- Ten root-level reports moved to `research/topics/<category>/` with filenames unchanged:
  agent_architecture, decision_layer, typed_decision_model (a); dynamic_networks,
  virtual_cell_wm_audit_20260928 (b); judgment_stability (c); agent_research_20260925 (e);
  framework_optimization, engineering_record, repository_cleanup_20260927 (f).
- Inbound markdown links updated: `task.md` (5), `Innovation.md` (2),
  `topics/agent_decision_core/decision_layer.md` (1 internal relative link).
- Historical-record decision: `log/20260927/README.md` and
  `log/20260927/0927/premise_forecast_run_notes.md` mention the old
  `research/repository_cleanup_20260927.md` path inside inline-code spans as a statement of
  what was true on 2026-09-27. These are dated historical narratives, not navigation links;
  rewriting them would falsify the record. They are left as written, and this paragraph is
  the pointer to the file's current location
  (`research/topics/engineering_records/repository_cleanup_20260927.md`).
- `outputs/` archives and `PROMPT_consolidation.md` itself were not edited (historical
  records).

## 6. Pre-existing discrepancies (listed, not resolved)

1. `research/dual_core_v2/freeze.json` (written 2026-09-28 10:18:21): `--verify` reports
   `research/dual_core_v2/test_dual_core_v2.py` under `changed`. Predates this session.
2. `research/dual_core_v2/freeze_population.json` (written 10:29:21): manual digest check
   reports `research/dual_core_v2/analysis.py` changed. Predates this session.
3. `task.md` section 11 predates the 2026-09-27/28 blocks (dual_core, dual_core_v2,
   incontext_world, premise_forecast, viability_contrast). Listed in the inventory section 3;
   updating section 11 was out of scope because no promotion changed the verified list.

## 7. Verification (Phase D commands and results)

1. `python -m pytest tests/test_repository_shape.py -q`: 2 failures, both the documented
   environmental ones (no git binary in this sandbox; the fallback sweep reaches pre-existing
   Chinese files `research/prompt_review_20260927/review_zh.md` and
   `research/scientific_optimization/`). All 14 new or edited markdown files were scanned
   directly for CJK and emptiness with the test's own stripping rules: zero violations.
2. Freeze verifies: `research.viability_contrast.freeze --verify` for v1, v2, v3, v4, v5, v5b
   all report `all_match: true`. `dual_core_v2` freeze.json and freeze_population.json retain
   the two pre-existing mismatches listed in section 6 (unchanged by this consolidation).
3. Full suite `python -m pytest tests/ -q`: **1367 passed, 2 failed** (the same two
   environmental shape tests) in 93 s. No regressions.
4. Import smoke: `import src.agent, src.evaluation, src.maestro, src.virtual_cell` — clean.
5. Link check: all 37 links in `research/README.md` resolve; the 5 `task.md` and 2
   `Innovation.md` topics links resolve; the `decision_layer.md` internal relative link
   resolves.

## 8. Files changed

Created: `research/CONSOLIDATION_INVENTORY.md`; `research/topics/{agent_decision_core,
virtual_cell_world_models, evaluation_methodology, literature_design_sources,
engineering_records}/` (10 files moved in). Rewritten: `research/README.md`. Edited:
`task.md` (5 link targets), `Innovation.md` (2 link targets),
`research/topics/agent_decision_core/decision_layer.md` (1 link target, post-move).
No Python files created, edited, or deleted.

## 9. Non-goals honoured

No negative-result code or report was deleted; no research original was merged, rewritten, or
"improved"; `data/`, `outputs/`, `reference/` untouched; no new features; no execution while
an experiment was active.

## 10. Acceptance status and next steps

Acceptance items 1-5 of the specification are green within the documented environmental
limits (section 7). `research/CONSOLIDATION_INVENTORY.md` is in place; this record and the
`log/INDEX.md` row complete the acceptance set.

Registered next steps, not executed here: (i) the owner decision on `incontext_world`
`ridge_st` promotion (needs new contract tests); (ii) resolving the two pre-existing
dual_core_v2 freeze mismatches by the block's own update procedure; (iii) the
reformulation registered by viability-contrast v5b (two-compound contrast census), which is
the next research block and is not part of this consolidation.
