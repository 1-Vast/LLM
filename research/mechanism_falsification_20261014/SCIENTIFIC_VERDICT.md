# Scientific verdict

## Verdict: **ASSET_BLOCKED**

The mechanism-falsification question cannot be tested because the independent mechanism truth it needs is not
available (A0: INSUFFICIENT_MECHANISM_TRUTH). The only contribution this study can support is of the
`BENCHMARK_OR_SYSTEMS_CONTRIBUTION` kind: a repaired, tested decision contract and a refusal-first benchmark, with
a specification-conformance result. The conformal-selection workstream returns a separate scientific `NO_GO` for
FDR control on this pool. These are three different statements and are not averaged into one.

## What was established

| Claim | Status | Where |
|---|---|---|
| The historical decision review returns NO_GO on an unauthenticated flag, GO with a required prediction untested, and admits a digest of the right length for a file that does not exist | **Reproduced** on unchanged code | [INTEGRITY_AUDIT.md](INTEGRITY_AUDIT.md), `reproduce_defects.py` |
| A strict, versioned policy closes those defects and the independence, lineage, unit and approval defects, without altering any frozen file | **Implemented and tested** (35 new tests, 13-point mutation check, all mutants killed) | [EVIDENCE_CONTRACT.md](EVIDENCE_CONTRACT.md) |
| The evaluator-audit findings C1-C7 hold as executable contracts | Implemented | `evaluation_contract.py` |
| The strict policy and the old review differ on the benchmark (21 of 21 against 6 of 21) | **Specification conformance only**; expected outcomes were written with the strict code | [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md) |
| No local asset holds independent mechanism truth (0 measured positive, 0 negative references); Hub and MAP-KG are not independent; exposure times and plates do not match | **Census, metadata only** | [DATA_FEASIBILITY.md](DATA_FEASIBILITY.md) |
| Conformal selection does not meet its nominal level on this pool and cannot reject at this scale | **Simulation + exploratory, exposed data**; plus an arithmetic power bound | [CONFORMAL_TRIAGE_REVIEW.md](CONFORMAL_TRIAGE_REVIEW.md) |
| `ML+context` out-hits D3 at matched budgets | **Exploratory only**; split exposed, comparator chosen post hoc | same |

## What was not established

* **Whether any method falsifies wrong mechanisms or retains true ones.** The estimand is unidentifiable with local
  data. No FRR or FRetR exists. A1 and Phase 5 were not run, by design (the brief's stop rule).
* That the strict policy makes scientific decisions better. It makes them *accountable*: a GO now names the bytes,
  the independence groups and the human who approved. Accountability is not accuracy.
* That registered bytes measure what their receipts say. The ledger authenticates bytes and lineage; a wrong file
  registered with its true digest passes.
* Any property of `ML+context` beyond a post hoc ordering on exposed data.
* Gate outcomes for A1, B (mechanism), and the confirmatory part of C: not testable.

## Gates

| Gate | Result |
|---|---|
| P0 contract repair | **PASS** for the defects reproduced; D5, D7, D8 remain open in promoted modules, with reasons |
| A0 feasibility | **INSUFFICIENT_MECHANISM_TRUTH** (also INSUFFICIENT_CONTEXT_MATCHING) |
| A1 algorithm | **NOT RUN** (A0 gate) |
| B benchmark | built; **PASS** on specification conformance; no scientific claim |
| C conformal triage | review done; guarantee does not apply to this pool; empirical results exploratory |
| D reproducibility | `verify.py` PASS; software tests PASS; **research reproduction is separate**: studies were not re-run; large assets VERIFIED against upstream digests |

## Status ledger (kept apart)

* **PASS**: software contracts, asset-free suite, `verify.py`.
* **FAIL**: none outstanding.
* **BLOCKED/ASSET_MISSING**: engagement, rescue, dependency and matched-context truth; sealed PRISM 24Q2 (unopened by
  instruction).
* **Scientific NO_GO**: mechanism-falsification development on current assets; conformal FDR control for this pool.

## What could change the verdict

1. An authorised measured-engagement or CRISPR-dependency asset for at least 30 independent mechanism families, with
   a source digest, registered before analysis (see [PILOT_PROTOCOL.md](PILOT_PROTOCOL.md)).
2. Designed chemical-genetic pairs measured on one plate at one time.
3. For triage: a calibration set of the order of 5 x 10^5 labelled pairs, or a pool two orders of magnitude smaller,
   and a family-exchangeable split on an untouched release.

Until one of these exists, the supportable contribution is the repaired decision contract, the refusal-first
benchmark, the feasibility census and the negative finding on conformal selection. Nothing more should be said.
