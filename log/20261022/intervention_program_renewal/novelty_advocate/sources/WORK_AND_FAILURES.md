# Source work and failures

2026-10-22. Two explicit GETs completed once each: Hyperagents HTML and AIDE² abstract, both HTTP200, no redirect/retry, timeout30s/cap8MiB. Full bodies and receipts retained beside this file. No assay payloads requested.

The first local narrative projection failed with `ModuleNotFoundError: No module named 'bs4'` in maestro before producing projections. No HTTP request was repeated. Replaced the optional BeautifulSoup dependency with Python standard-library HTMLParser and reran only local narrative projection. This is a parsing/dependency failure, not a scientific result. Primary method/results narrative is exposed; biological response arrays remain unopened.
