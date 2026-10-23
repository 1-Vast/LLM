# Source and reading ledger

All URLs were fetched with Python requests; exact URL, status, timestamps, size, hash and saved path appear in each *_receipt.json. Metadata queries are learned_update, experiment_design and model_revision, each max_results=12 sorted newest first within 2025-01-01 through 2026-10-22. All seven network requests succeeded; retrieval is not author-result replication.

| Source | URL | Read scope |
|---|---|---|
| AssayLoop | https://arxiv.org/html/2609.11877v1 | Abstract; introduction; results 2.1–2.3 opening; Methods 4.2–4.6; Appendix B context-delta and description ablations; portions of aggregate published baseline table exposed in the same passage. Individual gene labels mentioned in published illustrative captions are literature-exposed, not dataset extraction. |
| AR-BED | https://arxiv.org/html/2610.20832v1 | Abstract, introduction, background 2.1–2.2, related-work table and beginning method description; not all appendices/proofs/experiments. |
| DABS | https://arxiv.org/html/2607.16927v1 | Abstract, introduction, background, method 3.1–3.3; strong-heredity passages and Appendix B mismatch/ablation passages; limitation/conclusion passages. Not full author code or empirical reproduction. |
| AssayLoop official README | https://raw.githubusercontent.com/Genentech/assayloop/main/README.md | Entire README, package/API/split/released-checkpoint descriptions. No command from it executed. |

Three full bodies are retained as sources/*.txt, with derived *.readable.txt using standard-library HTMLParser. Reader retains some page script/style text, so mathematical claims were checked against surrounding prose/equations, not inferred from headings alone. No paper's reported performance is newly verified here.

Local processing failures retained here: bs4 import unavailable; attempted subsequent readable-file access FileNotFoundError because the failed parser had produced none; later inline regex command failed in PowerShell parsing before execution. read_html.py and source_passages.py replace these attempts. Network failures: none.

New exact synthetic result: CONTEXT_REWARD_CHECK.json. Its labels are manually enumerated abstract bits, not biological records. The stated paper formula is audited; code-level stochastic equivalence is not yet checked.
