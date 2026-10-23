# Download failures and unintended development exposure

First pass: 47 HTTP requests with four concurrent workers; 9 new files succeeded, 38 returned HTTP429 (227byte HTML). One pre-existing JQ1 file reused. Original request receipts, headers and response bodies are preserved. No automatic retry was enabled. Root instructed a maximum four workers; this concurrency was within scope but exceeded server's rate allowance.

Correction plan: one explicit second attempt for only archived 429 files, sequential with minimum ten seconds between request starts. Stop immediately on another non200. Do not overwrite first-attempt evidence or download any selection/later payload.

**Exposure incident:** while inspecting failed response, agent mistakenly chose numeric index009 (`CHDI00465983`, successful file) rather than010 (`CHM-1`,429). `Get-Content` returned successful molecular table content including all-dose intensities and fit quantities; tool output was very large/truncated, but at least beginning/end response rows were visible. This violated the header-only prefreeze boundary. Agent immediately reported incident to root. Mark CHDI00465983 as additional **development-exposed full-dose processed molecular data**; do not claim all molecular values remained unopened or use this exposure for post-hoc method/threshold selection. Other96 protected drug payloads were not requested. The protocol/review must disclose this incident and avoid retrospectively claiming pristine preregistration.

Later failure inspection was guarded by actual file size <1024bytes and known HTTP429 receipt, revealing only error HTML. No other biological response payload was decoded by this agent in this phase.
