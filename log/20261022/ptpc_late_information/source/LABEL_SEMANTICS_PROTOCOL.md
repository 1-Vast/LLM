# PTPC author-Efficacy source-only definition audit

Scope: locate original experimental dose, response duration, assay and decision threshold for the S8/PTPC Efficacy annotation. Read only previously saved primary article text/HTML, SI text, author README, prior S8 Legend/header/identity evidence, and exact-DOI public publication metadata. Do not open any protein matrix values, any other background's labels, reserved outcomes, baseline predictions or 24h abundance. No contact, access application or restricted-access circumvention.

Extract literal source quotations with file hashes and text-line positions. Distinguish actual S8 statements from S1/PTDS, S7/PTNC, model classification cutoffs, and Fig5G–I dose-response experiments. Missing text is unknown, not proof that the complete paper lacks a definition. The current saved main article may be a subscription preview; record that explicitly.

Permit at most one ordinary GET each to Crossref exact DOI metadata and OpenAlex exact DOI metadata, DOI 10.1038/s41586-026-11001-9, to locate an author/institutionally released primary full text. Retain raw responses, URLs, timestamp, status and SHA256; timeout 40 seconds, cap 4 MiB, no automatic retry. Only follow a specific public full-text location if it is actually returned and relevant; otherwise stop the search without guessing URLs or requesting private access. No article assay data tables are downloaded or opened in this task.

Output an evidence ledger and report separating direct PTPC facts, nearby but nontransferable facts, unresolved details and implications for the already-authorized author-annotation task. No reanalysis of numerical baselines or functional/RSI claim.
