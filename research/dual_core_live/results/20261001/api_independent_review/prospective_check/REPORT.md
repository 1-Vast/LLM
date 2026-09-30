# Independent prospective receipt review, 2026-10-01

The prospective integrity review passes 321 checks with no detected mismatch.
This is a separate review from the original/recovery review's 4,016 checks.
It imports no experiment runner or provider client, makes no network call, and
edits no source or frozen result.

The eight preregistered generated cards and all seven current source hashes match.
The prompt is byte-identical to the original benchmark prompt in both the freeze
and every actual DeepSeek request. The freeze predates the saved run start. All
16 exchanges, request/response hashes, served identifiers, token totals, card and
proposal hashes, empty evidence hashes, and per-card/summary artifact hashes match.
DeepSeek and Jev each have eight logical exchanges. The same raw proposal is
evaluated by both gates; no alternate measurement is manufactured and Jev has no
evidence, repair or action authority.

Independently recomputed public-objective scores and family-weighted statistics
match the summary. Raw, base gate and support gate each succeed on 8/8 cases,
with six deferrals and two measurements. The support gate therefore adds **no
observed action gain** in this new sample. The four fixed generated families
provide only an exploratory contract probe, not general biological validation.

Jev's objective judgment is correct on 6/8 cases. Its two false negatives remain:

| Card | Family | Recorded probability | Judgment | Public-objective truth |
| --- | --- | ---: | --- | --- |
| `prospective_95ace9e24609` | missing forecast | 0.45 | false | true |
| `prospective_ff816d03e596` | unsupported | 0.49 | false | true |

Jev correctly answers all eight support questions and all eight measured-evidence
questions. Typed answers remain advisory; their semantic errors do not authorize
an execution or create evidence.

The new cards explicitly expose the optional forecast-support contract. An
unchanged prompt therefore does not imply unchanged task information. The
original 20/24 versus new 8/8 action results are different populations; they
cannot be presented as a paired model improvement or a gate-effect estimate.
The original failures are retained, and the deterministic scope probes establish
only the new declared refusal boundary.

Reproduction:

```powershell
& D:\anaconda\envs\maestro\python.exe outputs/dual_core_live_20261001/api_independent_review/prospective_check/review.py
```

The receipt is write-once. Copy the script into a fresh sibling directory at the
same depth to repeat. Exact source/input/output hashes, command, check count and
both negative Jev judgments are recorded in `receipt.json`.
