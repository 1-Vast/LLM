# Bounded official metadata retrieval

2026-10-23. Read the goal objective and immutable HCC qualification decision before work. Six sequential HTTP requests were made, with no automatic retry. Exact UTC intervals, status, response headers, final URL, SHA256 and byte counts are saved in corresponding receipts; raw response bodies retained. No assay response values were parsed, printed, fitted or used for selection. No workbook was downloaded. Native agent model identity/usage is not attested.

1. Crossref DOI works endpoint: 200, 26146 bytes. Crossref link fields contain Elsevier XML/plain-text mining URLs; relation is empty. resource.primary is the linkinghub article route. No workbook link appears in the metadata.
2. Elsevier /content/article/pii/S258955592500103X?httpAccept=text/xml: 200, 1935 bytes. Body contains article coredata only, including authenticated DOI/PII and self/scidir links. HTTP success is not full article retrieval and supplies no supplementary attachment link.
3. Legacy www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=PMC12205652: 404, 1588 bytes. This does not establish that the current canonical PMC OA endpoint or article is absent. Root separately tested the current canonical endpoint; do not conflate the two requests.
4. EPMC search EXT_ID:PMC12205652: 200, 181 bytes, zero results. This was an inappropriate identifier field query, corrected by request 6; it is a recorded search failure, not missing-article evidence.
5. Crossref-supplied Elsevier PII: route with view=FULL: 401, 133 bytes, AUTHENTICATION_ERROR / Invalid API Key. No key was supplied. No attempt was made to discover or expose credentials. This is an access condition of this request, not evidence of global unavailability.
6. EPMC DOI core query: 200, 10742 bytes, one matching PMC12205652 record. hasSuppl=Y and hasData=Y; supporting_data appears among dataLinksTags. fullTextUrlList lists DOI and EPMC HTML/PDF only. No supplementary workbook URL is included. The broad data tags do not identify an Excel object or authenticate any guessed CDN filename.

## Independent conclusion

NO_NEW_AUTHENTICATED_WORKBOOK_LINK from these six metadata requests. Preserve NO_NUMERICAL_GO for the HCC task under the prior decision. This is scoped to these endpoints and payloads; it does not establish that the separate Excel file is globally unavailable. Metadata access, a broad supporting_data tag, and API coredata are not response-label acquisition or scientific performance progress. Full virtual-cell/agent/RSI objective remains unachieved and active.

No attachment filename was guessed and no unofficial download source used. No author contact, DeepSeek call, GPU job or numerical assay experiment. Two small new retrieval scripts are under research/hcc_link_recovery_20261023/agent/. The second reuses the first retrieval procedure with two explicit follow-up URLs. All prior sealed files remain unchanged.

Potential distinct next action, not executed here: inspect official EPMC data-link detail metadata to determine what supporting_data denotes. That endpoint may only refer to already inspected supplements. A future authenticated original source link, rather than metadata tags, would be required to change the present numerical gate.
