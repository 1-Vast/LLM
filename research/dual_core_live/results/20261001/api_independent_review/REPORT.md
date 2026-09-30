# Independent read-only review, 2026-10-01

Both independent receipts pass: 2,936 original/recovery checks and 1,080
supplementary checks, with no detected mismatch. This review made no network
request, changed no production/research source, trained no model, and modified no
frozen output. Only this fresh review directory was written.

The original preregistration hashes to
`fd30716bfee888fc7db18bf0f89c1914a009ff2b78be0dc7105ee0f58d87a19d`.
The recovered summary hashes to
`5d212f64bb11104dbe2f354d4d15e31ffd7d12548532b4162d979d64f08a91a5`.
The then-current parent commit is
`8271e8a119138d0e9c60fd9938f0abe11e081a79`; exact reviewed source hashes are
retained in the receipts because the new API and runtime changes were uncommitted.

## Original experiment and recovery

- All 522 preregistered input records match disk. All 134 executable-source
  records match their expected original or explicitly authorized recovery hash.
  The old benchmark source archive matches its original hash. An independent AST
  comparison finds only biological serialization, CLI recovery dispatch, and the
  added offline recovery function changed; biological replay semantics are
  unchanged after removing the finite-sentinel serialization wrapper.
- Every original receipt copied to the recovered directory is byte-identical;
  every recovered artifact-ledger hash matches. All 15 cached biological cards,
  proposal gates, proposal hashes, Jev report hashes, and exact receipt hashes
  join the recovered paths. The review does not rely on the recovery's own
  `same_card` flags alone.
- Formal receipts contain 80 logical provider exchanges, 40 per provider: 24
  general action proposals, one blinded batch review, and 15 biological
  decisions. The capability smoke separately contributes two per provider.
  Request/response hashes, model identifiers, token totals, median/p95 latency,
  and error counts were recomputed from raw exchanges. Logical completions do
  not establish independent provider-server request counts under hypothetical
  retries; no transport error was recorded in these exchanges.
- Provider request contents equal the saved public cards exactly. Review labels,
  evaluator truth, hidden validator scores/template counts, and truth-branch
  reading-quality records are absent. Every biological history contains exactly
  the already purchased public-step prefix; the offered menu and remaining
  budget join the registered trace. Forecast input/output hashes match frozen
  training identifiers, hyperparameters, condition and purchased history.
  Preserved probability distributions are predictions, not hidden outcomes.
- Evidence hashes remain unchanged by the API/auditor pipeline. Jev receipts
  explicitly deny evidence and repair authority. The final trace never carries
  evaluator truth or forecast evidence. Purchased reading/lifecycle/readout
  categories match the original frozen executor rows; failed QC creates no
  elimination.

The numeric review imports no benchmark runner or provider client. It separately
recomputes the 120 general-arm rows, the 48 known-defect labels and confusion
matrices, all 36 biological terminal scores/costs, selected NLL/Brier, episode
averaging, chemical-unit averaging, family and paired-family bootstrap intervals,
matched-common-decided risks/costs, changed-action counts, and partial-identification
endpoints. All six selected chemical units per task are unique. Reachable initial
menus contain no missing or previously flagged unresolved source result in this
pilot; this does not resolve the earlier source discrepancies elsewhere.

The audit supports the reported negative conclusions: the API matches the strong
one-step optimizer on these biological paths; changed sequences do not increase
terminal correctness/utility; L1000 net-utility savings arise from avoided
measurements on refused episodes. General unsupported-forecast choices remain
legal but fail the declared objective. The original zero arithmetic forecast
regret misses this objective violation and remains a limited diagnostic.

## Optional support contract and uncertainty correction

The new support helper was reviewed independently using all 24 original cards
and explicit scope probes, with network transports patched to raise. When the
support contract is absent, legal no-forecast actions remain accepted. Under an
explicit forecast-required contract, an unsupported action receives only the
declared defer fallback. A legal supported action is preserved even when another
legal action has a larger supplied forecast utility: this helper does not rank
or manufacture an optimal replacement. It mutates neither proposal nor card.

`ModelAuditAgent` still produces only input/proposal hashes and findings; it owns
no action, repair, execution, measurement or terminal payload. A caller's declared
refusal policy is separate from the report-only auditor. Passing formal legality
does not certify support, optimality, biological validity, or arbitrary model-bug
discovery. The support helper expects a validated registered card and does not
replace complete schema validation.

The separate corrected summary removes exactly four single-chemical-unit
selected-reading intervals and adds uncertainty annotations. A recursive numeric
comparison confirms that no count, mean, policy, observation or other interval
changed. The original summary bytes remain frozen. Six-unit zero-variance
conditional bootstrap results do not establish equivalence or future-population
uncertainty. One connected physical component per task remains insufficient for
physical-cluster confidence intervals.

## Reproduction and limits

```powershell
& D:\anaconda\envs\maestro\python.exe outputs/dual_core_live_20261001/api_independent_review/review.py
& D:\anaconda\envs\maestro\python.exe outputs/dual_core_live_20261001/api_independent_review/scope_review.py
```

Each receipt is write-once. To repeat, copy only these two scripts into a fresh
sibling directory at the same depth and run there; they write their receipts beside
themselves. The checked inputs, sources, archived/corrected summary hashes,
environment, command, and review-script hashes are retained in `receipt.json`
and `scope_receipt.json`.

This audit checks actual saved information flow and arithmetic. It does not
reconstruct undocumented hosted-provider training exposure, establish scientific
truth for development annotation proxies, certify new compounds/times/doses, or
prove general biological superiority. The later prospective API check is outside
the original-run receipt population reviewed here.
