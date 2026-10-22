# AZ chemical identity metadata qualification

2026-10-22. This is a read-only provenance/identity qualification, independent of numerical model performance. It cannot authorize a panel change or selection of new targets.

## Scope and allowed evidence

- Read previously captured primary article XML, Figshare metadata, author analysis code, and frozen metadata projections. Project only source drug IDs and query/target pair IDs from the design/census.
- A full first display of `DESIGN.json` also displayed its already-public reserve cell ID list. This is design metadata exposure only. No reserve source rows, responses, paid observations, arrays or model outcomes were opened or used.
- Do not infer chemical identity from ID proximity, pharmacological targets, compound counts, familiar names, or source ID pair disjointness. Chemical identity, treatment/formulation identity and dose equivalence are separate questions.
- Maximum four new HTTP retrieval attempts. The fourth is the parent-authorized Europe PMC supplementary archive route, with only the exact S2 identity entry eligible for decompression. Other entries remain uninterpreted compressed bytes.

## Completed local metadata work

- The saved paper says 37 individual drugs and directs compound/combination details to Supplementary Table 2.
- Its XML declares exact file `EMS194010-supplement-Table_S2.xlsx`, size 19,152 bytes and MD5 `1661f9b51a2e204e9af8a3f6f94ebe80`.
- The saved Figshare articles enumerate response-data resources, not an exact source-ID-to-chemical dictionary. Saved author figure code also does not supply that dictionary.
- The frozen census has 46 distinct source drug IDs. The current design contains 12 target pairs and 13 query pairs using 11 distinct IDs. The two sets of unordered source-ID pairs do not overlap. Chemical pair independence is not established by this result.

## Failures and corrections

1. The first local projection script assumed all captured bodies were JSON. Some author code bodies are raw R Markdown. It failed with `JSONDecodeError` before emitting a projection. The minimal correction distinguishes JSON from text and retains only identity/link lines from code. No environment changes were made.
2. Direct PMC S2 route returned HTTP 403. Its body and exact response receipt are retained as `s2_attempt_01.*`.
3. Europe PMC HTML S2 route returned HTTP 403 / challenge. Its body and exact receipt are retained as `s2_attempt_02.*`. No challenge was bypassed.
4. The article-declared cloudpmc URN was translated to a CDN route, which returned HTTP 404. Its body and receipt are retained as `s2_attempt_03.*`.

The fourth request and its eventual status must be read from `s2_attempt_04.http.json`. A retained ZIP prefix is not a complete HTTP body; the receipt explicitly distinguishes these cases. No additional GETs or same-URL retries are permitted in this qualification.
