# Evidence-boundary benchmark (specification and reference results)

[benchmark.py](benchmark.py) builds 21 miniature, provider-free tasks. Decision tasks are **data**
([BENCHMARK_FIXTURES.json](BENCHMARK_FIXTURES.json)): sources with bodies, receipts, a policy, explanations and an
expected status. Any implementation can be scored on them. No task needs a provider, a download or an external
asset. Each task isolates one boundary: where evidence stops being admissible, where a claim outruns its evidence,
or where an evaluator reads what it should not.

## Scoring a submission

```
python research/mechanism_falsification_20261014/benchmark.py --score submission.json
# submission: {"P-01": {"status": "NEED_MORE_EVIDENCE", "reasons": ["UNTESTED:engage"]}, ...}
```

A decision task passes when the status equals the expected status and every expected reason prefix appears in the
submitted reasons. Executable tasks (E-, V-) run in the reference implementation only; they are in the results file
and in `tests/`, and a third-party system is scored on the decision tasks.

## Tasks

| Id | Axis | Boundary tested | Expected |
|---|---|---|---|
| P-01 | provenance | receipt names a source file that does not exist | NEED_MORE_EVIDENCE |
| P-02 | provenance | source bytes changed after the receipt was written | NEED_MORE_EVIDENCE |
| P-03 | provenance | three copies of one experiment, two independent groups required | NEED_MORE_EVIDENCE |
| P-04 | provenance | a virtual-cell prediction relabelled as a derived analysis | NEED_MORE_EVIDENCE |
| P-05 | provenance | QC-failed measurement | NEED_MORE_EVIDENCE |
| M-01 | mechanism | a database annotation offered as target evidence | NEED_MORE_EVIDENCE |
| M-02 | mechanism | overexpression-context measurement used for an inhibition prediction | NEED_MORE_EVIDENCE |
| M-03 | mechanism | candidates make no incompatible prediction on any available experiment | NEED_MORE_EVIDENCE (not identifiable) |
| M-04 | mechanism | true mechanism absent: measured engagement contradicts the progression explanation | NO_GO |
| D-01 | decision | one required prediction supported, the other untested | NEED_MORE_EVIDENCE |
| D-02 | decision | a no-signal assertion with no measured finding behind it | NEED_MORE_EVIDENCE |
| D-03 | decision | all supported and excluded, nobody has approved the consequential experiment | AWAITING_APPROVAL |
| D-04 | decision | approved GO, then a required receipt is withdrawn | NEED_MORE_EVIDENCE, certificate invalidated |
| D-05 | decision | conflicting independent measurements | NEED_MORE_EVIDENCE (`CONFLICTED`) |
| D-06 | decision | an approved experiment that exceeds the budget | refused |
| D-07 | decision | an exploration ranking read as a probability | refused |
| E-01 | evaluation | hidden outcomes, including missingness, change; pre-outcome nominations must not | invariant |
| E-02 | evaluation | normaliser fitted with a test row | refused |
| E-03 | evaluation | one compound core in two screens | refused, not averaged |
| E-04 | evaluation | fraction viability with overgrowth; 50 percent equals 0.5 fraction | boundary stable |
| V-01 | predictive validity | knowledge gain reproduced by a structure-preserving relabelling | class shortcut, not identity |

Not every row has a positive example for every GO path: only M-04 is a NO_GO and D-03 shows the approval stop. A
benchmark of 21 tasks cannot establish a rate.

## Reference results

| Implementation | Passes | Basis |
|---|---|---|
| Strict policy `strict-review-1` | 21 of 21 | executed |
| Historical `decision_review.review` | 6 of 21 | 15 failures: P-01..P-04, M-03, D-01..D-05 executed on the legacy code; E-01, E-04 reproduced from its logic; E-02, E-03, V-01 recorded from the evaluator audit, **not executed** |

**This is a specification-conformance result, not a scientific one.** The expected outcomes were written alongside
the strict implementation, so 21 of 21 shows that the code does what the specification says and that the old code
does not. It does not show that the specification is the right one, and it supports no claim that the strict policy
makes better scientific decisions. The legacy numbers for E-02, E-03 and V-01 rest on the audit's reading of the
frozen evaluator, which never ran, and are marked `audit_finding_not_executed` in the results file.

## Asset manifest

External assets a full replay of the study would read are listed with their authentication status in
[ASSET_AUTH.json](ASSET_AUTH.json), [ASSET_AUTH_LARGE.json](ASSET_AUTH_LARGE.json) and the RO-Crate-style
[ro-crate-metadata.json](ro-crate-metadata.json). Statuses: `VERIFIED` (matches an upstream digest),
`LOCAL_DIGEST_ONLY` (no upstream digest exists; the sha256 pins the bytes used), `MISMATCH`, `ASSET_MISSING`.
The benchmark itself needs none of them.
