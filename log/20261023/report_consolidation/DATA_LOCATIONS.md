# Data locations after report consolidation

5174 files (16,965,601,085 bytes) were relocated out of `log/`. Content hashes were checked before and after each relocation. This is storage verification, not analysis of outcomes.

- Raw inputs: `data/raw/research_inputs/`.
- External datasets, documents and downloaded sources: `data/external/research_sources/`.
- Detailed derived data, model artifacts and numeric outputs: `data/processed/research_results/`.
- Retained third-party source copies from retired experiment folders: `data/external/retired_research_sources/`.

Exact original/current paths and hashes: [main migration receipt](DATA_MIGRATION_RECEIPT.json), [supplement](DATA_MIGRATION_SUPPLEMENT_RECEIPT.json), and [retained research record locations](ARCHIVE_LOCATIONS.json). Historical frozen manifests keep their original content; use these maps to resolve paths after organization. Key reports and result summaries stay in `log/`; experimental code stays in `research/`. No code was promoted to `src/` or `tools/`.
