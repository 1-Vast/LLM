# STACK v1 raw-source and observation qualification

2026-10-22. New phase after the completed dead-stock target qualification abort. The old gate, its final inventory and all historical STOPs remain unchanged. Overall goal ACTIVE / NOT_ACHIEVED. This phase qualifies a multi-drug functional-trajectory source before proposing a new core or opening numerical responses. All code/tests go in research/stack_raw_qualification_20261022/; all records/data go here.

## Application and question

Potential application: early drug-induced cell-death/marker trajectory forecasting and budgeted follow-up triage across compound groups and actual cell/background screens. The source is Forcina et al. STACK 2017, primary PMC5509363, dataset DOI 10.17632/3pnv5wh5jm.1. A valid v1 landing was authenticated in the preceding phase; v2 is a soft404. Repository description claims a 1,833-member library file and three raw live/dead/QC result workbooks. It does not establish their present availability, run independence or operational schema.

The immediate falsifiable qualification claim is that exact version-bound files can be acquired and joined to explicit assay/observation/time/compound/run identities without inferring independent tasks from frames or wells. No prediction or RSI claim is made. Existing marker persistence, disappearing dead-object stock and source QC limitations remain in force; no stock-to-event substitution.

## Acquisition scope and stopping

1. Reuse retained v1 landing/state and primary text offline. Up to four metadata GETs: the API documentation link and/or exact client bundle route present in that landing, then at most two source-derived v1 manifest/metadata routes. Do not probe guessed versions/endpoints. Derive substituted dataset ID/version parameters explicitly from a retained route template.
2. Preserve each full/partial body and receipt (UTC, URL, status, redirect, bytes, SHA256, timeout/cap, errors). No retries or automatic redirects. Timeout25 s; metadata cap8 MB per object. If a documented request redirects, at most two explicit validated HTTPS redirect hops per selected object, retained as separate receipts.
3. Only if a version-bound manifest supplies exact file names/IDs/sizes/checksum/download URLs, acquire at most four listed library/results files, each cap100 MB and combined advertised size<=250 MB. Follow only manifest or explicit HTTPS redirect routes; stop an object on failed status, size/checksum mismatch, cap or timeout. No author contact or arbitrary repository crawl. Downloaded bytes on disk are not numerical exposure, but do not claim cryptographic isolation.
4. Initially inspect container/workbook structure, sheet names/dimensions, shared-string labels, and exact header/identity/time cells only. Do not convert or print assay-response cells, QC decisions, LF/AUC values, ranked effects, formulas' cached responses, or graphical assay results. If schema does not separate identities from outcomes, stop and specify a separate exposure protocol before further values.

The first one or two header rows may be projected as strings only when they are clearly labels; any ambiguous row is not a header authorization. Preserved XML/string tables may contain other text; only qualified labels/identities may enter reviewer output. Data-derived row inclusion/QC masks are response-dependent and cannot silently choose a benchmark. No fit, performance score, endpoint replacement, clipping, filtering or imputation is authorized now.

## Independent review and success

The source auditor independently checks the retained primary for exact marker/measurement definitions, time origin, screen identity/replication, QC selection and claims that cannot be transported. A skeptic independently checks whether actual available task identities would support the proposed comparisons or only within-screen development, and states minimum fair tests. Independent drafts precede peer drafts, then real challenges and replies are recorded. Root handles manifest acquisition. No agent consensus substitutes for source evidence.

Success requires exact acquired raw objects with version/hash/size provenance, a schema projection separating identities/time from outcomes, and an explicit source-qualified observation/readout and independence map. Partial success is reported at its level. An access or identity failure stops this bounded source task, not the whole research goal. No architecture is promoted by availability alone.

Before later numerical work: register exact readout, legal prefix/target, missingness/QC policy, grouped train/validation/test role, same-information direct and ordinary model baselines and budgets. Conditional D information must retain D0 and end-prefix snapshot controls. Any world claim needs comparison with direct history models; any agent/inheritance/RSI claim needs its own fixed-feedback/common-start/equal-budget controls and later tasks. Actual policy improvement of subsequent improvement must be distinguished from weights or a selected fixed procedure. If source tasks cannot support those distinctions, explicitly narrow the claim.
