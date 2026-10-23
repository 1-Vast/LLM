# Research storage policy

- `log/` keeps concise protocols, final reports, key result summaries, failures, decisions, and provenance/location manifests. It is the durable research record. Bulk datasets, downloaded source bodies, model checkpoints and prediction matrices belong outside this directory.
- `data/raw/` holds raw experimental inputs. `data/external/` holds downloaded external datasets and source documents. `data/processed/` holds derived datasets, model artifacts and detailed numeric outputs. Keep source/version and hash information in the corresponding log record.
- `research/` holds experimental implementations and research tests. It may be cleaned or removed; unique scientific records and data must not depend on its survival.
- `src/`, `tools/` and their tests receive implementations only after the applicable validation and promotion decision. This consolidation promotes no experimental code.

The October 23 consolidation initially copied research records and data together into `log/research_records/` following the earlier instruction. The user's later clarification supersedes that layout: reports and key summaries remain there; data and external sources are relocated to the appropriate `data/` subtree. The migration manifest records original and current paths and content hashes. Historical frozen manifests retain their original bytes; resolving an old path may require the migration map. Storage checks are not scientific validation.
