# PPC targeted resource audit

Scope: one A reconnaissance and at most one decision-changing targeted follow-up. No fitting, experiments, external model APIs, protected/confirmation files, runtime changes, or edits outside the assigned new audit/download directories. Source/data acquisition is bounded at 80 MB.

## Initial identity queries (2026-10-30)

Actual tools: no native web/search browser tools were exposed; Python requests against official APIs is available. Targeted lit-survey workflow used; this is not an exhaustive field survey.

Three parallel API queries, all HTTP 200:

- `https://api.crossref.org/works?query.title=Pan-PreClinical&rows=6` — 42,794 response bytes; returned six irrelevant records. Not retained; titles inspected.
- `https://api.github.com/search/repositories?q=Pan-PreClinical` — 55 response bytes; zero repository hits. Not retained.
- `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=%22Pan-PreClinical%22&format=json` — 3,278 response bytes; four records, only one directly relevant: “A Pan-Cancer Ex Vivo Drug Screen Atlas for Functional Precision Oncology,” DOI `10.64898/2026.02.14.705918`, PPR1223457, first indexed 2026-05-19 and first publication date 2026-02-17. These are index metadata, not independent verification of paper data.

Decision: inspect the identified paper and official author repository/data routes. Requests from here are preserved with exact response bytes and SHA256 in `requests.jsonl`; downloaded source files go to the assigned `data/external/.../ppc/` directory. Preliminary ephemeral responses total 46,127 bytes and count toward the audit acquisition disclosure.

## Official identity and source resolution

The bioRxiv API and Crossref record authenticate the title, DOI, v1 date and preprint CC-BY license. The headline counts remain abstract claims. Full bioRxiv returned 429; Crossref-deposited HighWire syndication returned 403. No repeated restricted full-text retrieval, proxy/authentication workaround, numerical download, or fitting. The official API-supplied JATS locator is documented but not fetched.

Exact GitHub repository-name/README queries were empty. Authenticated author account kpich (22 public repos) and its linked homepage supplied no PPC-2026 release link; homepage text is updated 2020. Lab inventory had 26 public repos. UnitedPPC fork (created/pushed 2024) has a UnitedMet README and an inspected PPC loader expecting sample/drug/z-score/study CSV fields, but its relationship to the 2026 atlas is unverified. Pinned tree SHA `9e82fb2c7ee72dcdd268e4f035b73a0f8b3ab24b`, truncated false. The sole data CSV in that tree is a ccRCC metabolomics mapping and was not downloaded.

One targeted source-resolution follow-up inspected official author routes and pinned loader source. Google response was a redirect shell; Bing results were irrelevant PAN-card results, so neither supplied usable project evidence. Two guessed author accounts returned 404. Four requests had connection resets (official API alternate suffix, guessed lab website, lab org metadata, a raw job file). They were isolated; no broadening or extra source pass followed. A local log-summary command initially pointed to the download directory instead of audit directory and raised FileNotFoundError; the path was corrected. A census validation initially expected 21 rows but the file has 18; the independent parser/hash check established the correct count. These diagnostic errors did not modify downloaded sources or execute any experiment.

## Decision and verification

Stop A for this round because actual response data/schema and crossing support are unobservable. This is a resource eligibility stop, not a negative test of the scientific transport hypothesis. No overlap count is replaced by zero. README records a future numerical support/identifiability gate, strong ordinary explanation and screening-lab decision.

29 total requests (3 initial ephemeral, 26 logged); 22 complete saved responses, 928,107 bytes; completed observed response payload including initial requests 974,234 bytes. Partial failed-transfer bytes unmeasured. Hash/byte validation passed for every saved complete response; `support_census.csv` parsed with 18 rows. Numerical response rows and experiments/fits run: 0. No existing source files, protected outcomes, shared index or runtime code were edited.
