# Work and failures

2026-10-22. Independent literature review; no AZ response/model/performance access, no biological fits, no peer drafts read.

- Initial discovery downloads reached the text-extraction step, where an unavailable optional `bs4` dependency raised ModuleNotFoundError. The receipt catch incorrectly marked status null, so those are parsing failures, not evidence of HTTP failure. Both are explicitly retained in `SOURCE_RECEIPTS.jsonl` as failures.
- Replaced that dependency with the standard library HTML parser and repeated the two discovery GETs. These returned HTTP 200 with body/hash/status receipts. The initial pre-parse bodies used the same filenames and were superseded by these repeats; their original response status/hash was not preserved. No scientific evidence is based on those initial unreceipted bodies. Updated the downloader to use unique attempt names for all subsequent captures so later body versions cannot overwrite earlier evidence.
