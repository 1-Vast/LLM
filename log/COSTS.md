# Costs and Asset Boundaries

- Protocols, freezes, results, claims, deviations, artifacts, audit logs, and verification scripts at research roots are evidence and must be retained.
- `data/external/` (about 61 GB) contains original external data and models, not temporary caches; retain it.
- Large arrays and models in `research/knowledge_transfer_20261012/cache/` remain referenced by freezes, input audits, or replays and must not be removed wholesale.
- Dry-run caches and pytest temporary output are regenerable; before cleanup, record paths, sizes, hashes, and reference checks.
- Preserve provider calls, download states, and not-run states recorded in research materials; do not report an experiment as successful if no call occurred.
- 2026-10-17 `context_transfer_20261017`: Beat AML 2.0 release files (about 354 MB) in `data/external/beataml2_20261017/`, hashed by the study freeze; retain. deepseek-flash spend 0.2768 USD (confirmation LLM arm, 520 calls) plus 0.0156 USD (PRISM pilot); 0 wells purchased; 2,209 s confirmation run.
- 2026-10-17 `feedback_attribution_20261017`: 0 wells, 0 USD, no provider calls, no downloads; local compute only (registered runs about 18 min wall clock on 28 CPUs). Reads the confirmation's Beat AML domain cache and raw inhibitor file, already retained. Records and caches in `tmp/feedback_attribution_20261017/` are regenerable from the frozen code.
- 2026-10-17 `program_revision_20261017`: 0 purchased wells (archived PRISM 19Q4 outcomes; development wells are charged in the analysis, about 4,300 per revision arm and 167,722 for stepwise search), deepseek-flash 0.287 USD over 90 calls (0.088 pre-freeze smoke), no downloads. Reads `data/external/prism_19q4/raw` and DepMap features, already retained. Per-line records and the ledger are retained in the study's `records/`; the rest of `tmp/program_revision_20261017/` is regenerable.
