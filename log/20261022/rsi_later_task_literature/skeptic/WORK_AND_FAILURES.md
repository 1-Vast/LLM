# Work and failures

2026-10-22. Scope: independent primary-literature review, at most six substantive sources. No AZ numeric artifacts or fitting processes accessed. New retrieval/parsing code stays under research/rsi_later_task_literature_20261022 with skeptic_ prefix.

- Initial local inventory command passed PowerShell `-ErrorAction` to rg, producing an argument error. No remote request occurred. Corrected by using literal known receipt paths.
- First four planned retrieval commands failed at import because maestro has no bs4. No HTTP requests occurred. Replaced that unnecessary dependency with Python standard-library HTMLParser, then resumed the same intended requests; this is not a repeated scientific outcome search.
- Three Google GETs returned HTTP200 JavaScript retry/interstitial pages with no useful scientific search result. Bodies/receipts retained; these are discovery failures, not substantive literature evidence. Switched to the arXiv Atom API, which returned usable primary metadata.
- Initial content-type detection assumed header capitalization; changed to case-insensitive key lookup and projected the already saved bodies without redownloading them.
- Selected exactly six substantive source papers after discovery: Hyperagents, SpecRSI, learned gradient-history optimization, Recursia, Épi, and the empirical RSI-evaluation audit. All six full HTML responses were HTTP200, uncapped, and hash-receipted. A single id-list API request separately verifies their titles/dates/versions. Broader discovery results are not treated as reviewed precedents.
