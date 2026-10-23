# Repairing scientific contracts and testing whether mechanism falsification is studiable

Study folder: `research/mechanism_falsification_20261014/`. Status: **completed, not frozen; no confirmatory
experiment was run.** Governed by the brief "Repair Scientific Contracts and Investigate Evidence-Qualified
Mechanism Falsification". HEAD at start `9df96f62`. Zero downloads, zero paid calls, no sealed PRISM 24Q2 response
and no L1000 expression matrix opened; nothing committed or pushed.

## Result in four lines

1. **P0 contract defects were real** and are reproduced on the unchanged historical modules: an unauthenticated
   `no_signal` returns NO_GO, a GO is issued with a required prediction untested, a 64-character digest authenticates
   a file that does not exist, an `independent` flag nothing reads, and a prediction relabelled as an analysis decides.
   They are fixed in new, versioned, opt-in modules (`strict-review-1`) with 35 tests and a mutation check; no frozen
   file changed.
2. **A0 returned INSUFFICIENT_MECHANISM_TRUTH** (and INSUFFICIENT_CONTEXT_MATCHING): no local asset holds a measured
   positive or negative mechanism reference, and compound and genetic signatures are not observed at matched times
   or on shared plates. A1 and the algorithm phases were therefore **not run**.
3. **Conformal selection does not deliver its nominal FDR on this triage pool** (exploratory, exposed data) and
   cannot reject at this scale (needs about 5 x 10^5 calibration units); the exploratory `ML+context` comparator
   out-hits D3 at matched budgets but is not a confirmation.
4. **A provider-free 21-task evidence-boundary benchmark** exists (strict 21/21, legacy 6/21: specification
   conformance only).

**Verdict: ASSET_BLOCKED** ([SCIENTIFIC_VERDICT.md](SCIENTIFIC_VERDICT.md)).

## Documents

| File | Content |
|---|---|
| [INTEGRITY_AUDIT.md](INTEGRITY_AUDIT.md) | defects D1-D8, old versus new behaviour, open findings |
| [PRIOR_ART.md](PRIOR_ART.md) | assumptions per technique, verification levels, 4-class novelty matrix |
| [DATA_FEASIBILITY.md](DATA_FEASIBILITY.md), [CENSUS.json](CENSUS.json) | A0 decision and its evidence |
| [EVIDENCE_CONTRACT.md](EVIDENCE_CONTRACT.md) | receipts, lineage, independence, GO/NO_GO rules, C1-C7 |
| [PILOT_PROTOCOL.md](PILOT_PROTOCOL.md) | conditional pilot, **not run**, not frozen |
| [TESTS_AND_INVARIANTS.md](TESTS_AND_INVARIANTS.md) | tests, metamorphic invariants, mutation check |
| [CONFORMAL_TRIAGE_REVIEW.md](CONFORMAL_TRIAGE_REVIEW.md), [CONFORMAL_SIM.json](CONFORMAL_SIM.json), [CONFORMAL_TRIAGE.json](CONFORMAL_TRIAGE.json) | guarantee, simulation, exploratory comparison |
| [BENCHMARK_SPEC.md](BENCHMARK_SPEC.md), [BENCHMARK_FIXTURES.json](BENCHMARK_FIXTURES.json), [BENCHMARK_RESULTS.json](BENCHMARK_RESULTS.json) | benchmark |
| [ASSET_AUTH.json](ASSET_AUTH.json), [ASSET_AUTH_LARGE.json](ASSET_AUTH_LARGE.json), [ro-crate-metadata.json](ro-crate-metadata.json) | authenticated asset manifest |
| [SCIENTIFIC_VERDICT.md](SCIENTIFIC_VERDICT.md) | what was and was not established |

There is no `RESULTS.json`: the brief permits one only for an authorised, registered experiment, and none ran.

## Source added (outside this folder)

`src/maestro/evidence_registry.py`, `src/maestro/strict_decision_review.py`, `src/maestro/evaluation_contract.py`,
`src/maestro/tier_gate.py`; opt-in additions to `src/maestro/acquisition.py` and `src/maestro/endpoint_decision.py`;
tests `tests/test_evidence_registry.py`, `tests/test_strict_decision_review.py`, `tests/test_evaluation_contract.py`,
`tests/test_tier_gate.py` and additions to `tests/test_acquisition.py`, `tests/test_endpoint_decision.py`; helper
`tests/fixtures/strict_evidence.py`; four paths added to `pyproject.toml` `testpaths`.

## Replay

```
python research/mechanism_falsification_20261014/verify.py
```

See [PROTOCOL.md](PROTOCOL.md) for the other scripts and which need `data/external/`.

## Final verification record

Default asset-free suite: **903 passed** (2026-10-14, after the last source and test edit). `verify.py`: PASS.
Software PASS is not research reproduction; no earlier study was re-run.
