# External sources

Store downloaded external datasets, paper/source bodies and retained third-party source artifacts here. Preserve source/version information and applicable licenses. Keep derived numeric outputs in [processed](../processed/README.md).

Keep key conclusions and source/path/hash indexes in [log](../../log/README.md), and project experimental code in [research](../../research/README.md). Do not delete unique sources during research-code cleanup. See the [data inventory](../INVENTORY.md).

The [literature-survey workspaces](literature_surveys/) retain topic configuration, raw retrieval records, deduplication indexes and metadata drafts for three separate topics. Their [human-readable reports and actual completion states](../../log/README.md) remain in `log/`; the indexes are retrieval records, not new experimental predictions.

Additional retained source captures:

| Location | Contents and use |
|---|---|
| [State evidence source/protocol set](state_evidence_20261001/) | Seven retained formula/protocol `.raw` files moved from the former `tools/datasets/audit_results/` location on 2026-10-30. Four historical MAT payloads were structurally checked and removed; their hash-bound recovery is outside the project. |
| [Dual-core reference captures](literature_surveys/dual_core_reference_20261021/) | Twelve paper-text/HTML captures and the earlier DGM/Robin text captures, formerly scattered under `tmp/`; these are source material, not a completed additional survey |
| [PTV-1 source inspection](research_sources/20261021/ptv1_source_review/) | Article/supplement text, original PDF, source listing, downloaded README and dataset-loader capture; a partial inspection set, not an installable ProteinTalks distribution |
| [DGM checkout](../../tmp/dgm_reference_20261021/) | Third-party Git checkout retained at its existing path with its repository state intact; not moved into the source-capture collection |

The [current literature findings](../../log/RESEARCH_REPORT.md#literature-and-source-access) distinguish reviewed evidence, incomplete surveys and software checks. The source reader resolves the captures' former `tmp/` identities without rewriting the captured bytes.
