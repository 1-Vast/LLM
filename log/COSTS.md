# Costs and Asset Boundaries

- Protocols, freezes, results, claims, deviations, artifacts, audit logs, and verification scripts at research roots are evidence and must be retained.
- `data/external/` (about 61 GB) contains original external data and models, not temporary caches; retain it.
- Large arrays and models in `research/knowledge_transfer_20261012/cache/` remain referenced by freezes, input audits, or replays and must not be removed wholesale.
- Dry-run caches and pytest temporary output are regenerable; before cleanup, record paths, sizes, hashes, and reference checks.
- Preserve provider calls, download states, and not-run states recorded in research materials; do not report an experiment as successful if no call occurred.
