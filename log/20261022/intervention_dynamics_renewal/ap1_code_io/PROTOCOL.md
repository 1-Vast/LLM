# AP1 memory code-I/O audit

Registered 2026-10-22 local, before code requests. Reviewer `/root/functional_auditor`.

Use the existing complete public repository manifest `root_scout/AP1_REPOSITORY_MANIFEST.json`, tree `ed565d810bd1aa0b067c761c13bfb98989240417`, reported `truncated=false`. Maximum three GET attempts, one for each exact manifested blob:

- `code/incucyte/tram.Rmd`
- `code/incucyte/ap1i/jnk_stat.Rmd`
- `code/dexmemFISH/dexmemfish_function.R`

Each response body is capped at3,000,000 bytes. No automatic redirect or retry. Verify each decoded file with Git's SHA1 blob framing against its manifested SHA. No CSV, XLSX, HTML notebook, plot or other source file may be fetched. Do not execute the retrieved R/Rmd code. Existing `skeptic/AP1_MEMORY_PRIMARY.body` may be inspected offline for primary-design context.

Static audit targets: tram colony functional units; expected CSV columns; condition, time and replicate semantics; excluded/reused repeats; and actual early-state/functional join keys. Fields, CSV position and technical repeats must not be counted as independent runs. A code-inferred schema is an expectation, not verified raw-data content. Any embedded observed constants or summaries read in published code must be recorded as published-code exposure, not sealed outcome evidence.

Record URL, UTC, status, body bytes and SHA256 for every request; retain failures. Save code-reading evidence, findings and unresolved joins under this log directory. All fetching/extraction/audit code belongs under `research/intervention_dynamics_renewal_20261022/`. Root will separately choose any subsequent numerical/header object.
