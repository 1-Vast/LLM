# Protocol: repair scientific contracts, then decide whether mechanism falsification can be studied

Status: **completed, not frozen.** No confirmatory experiment was registered or run. This file records what was
authorised, what was done and what was refused, so that a later reader cannot mistake an engineering audit and a
feasibility census for a mechanism result.

## Authority

Allowed and done: read the repository, frozen studies and local metadata; write new source modules, tests and a
study folder; compute from local metadata files; authenticate local assets against upstream digests that are
themselves local files.

Not done, by instruction: new dataset downloads; opening sealed PRISM 24Q2 responses; paid LLM calls; external
experiments; remote deployment; pushing to GitHub; committing; modifying frozen protocols, frozen sources or their
hashes. No LLM was called, so the provider-cost ledger for this study is zero.

## Phases and what each could return

| Phase | Question | Returned |
|---|---|---|
| 0 | State of HEAD, tree, tests, freezes, assets | HEAD `9df96f62`, clean tree, default suite passing, freezes intact |
| 1 | Are the P0 contract defects real, and can they be fixed without touching frozen files? | Yes: D1-D3c reproduced on unchanged modules; new strict modules and 34 tests ([INTEGRITY_AUDIT.md](INTEGRITY_AUDIT.md)) |
| 2 | What is known, under which assumptions, and what is new? | [PRIOR_ART.md](PRIOR_ART.md) |
| 3 (A0) | Is the mechanism-falsification estimand identifiable on local data? | **INSUFFICIENT_MECHANISM_TRUTH**, also blocked by INSUFFICIENT_CONTEXT_MATCHING ([DATA_FEASIBILITY.md](DATA_FEASIBILITY.md)) |
| 4-5 (A1) | Algorithm research | **Not run**: A0 is not feasible, and the brief says to stop |
| 6 | Conformal selection for drug triage | Review plus exploratory real-data comparison ([CONFORMAL_TRIAGE_REVIEW.md](CONFORMAL_TRIAGE_REVIEW.md)) |
| 7 | Evidence-boundary benchmark | 21 provider-free tasks ([BENCHMARK_SPEC.md](BENCHMARK_SPEC.md)) |
| 8 | Gates P0, A0, A1, B, C, D | [SCIENTIFIC_VERDICT.md](SCIENTIFIC_VERDICT.md) |

## Pre-declared stopping rule that fired

If A0 is any state other than FEASIBLE_FOR_EXPLORATORY_TESTING or FEASIBLE_FOR_INDEPENDENT_VALIDATION, stop
mechanistic method development. A0 returned INSUFFICIENT_MECHANISM_TRUTH. There is therefore no `RESULTS.json`
in this folder: the brief permits one only for an authorised, registered experiment, and none ran. The conformal
simulations and the real-data triage comparison are labelled exploratory and live in their own files.

## Exposure statement

Every L1000 signature, CTRP curve and PRISM compound used by any script here was exposed to earlier MAESTRO
studies. Results derived from them are exploratory and cannot be confirmatory for any claim. The sealed PRISM 24Q2
response file was not opened (`CENSUS.json: prism_24q2_responses_opened = false`); L1000 expression matrices were
not opened (`expression_matrices_opened = false`).

## Replay

```
python research/mechanism_falsification_20261014/verify.py
python research/mechanism_falsification_20261014/reproduce_defects.py
python research/mechanism_falsification_20261014/benchmark.py            # rewrites BENCHMARK_*.json
python research/mechanism_falsification_20261014/census.py               # reads local metadata only
python research/mechanism_falsification_20261014/conformal_sim.py        # synthetic, seeded
python research/mechanism_falsification_20261014/conformal_triage.py     # needs the frozen triage study's inputs
python research/mechanism_falsification_20261014/authenticate_assets.py [--large]
```

`verify.py` replays only what is stable without large local assets. The census, the triage comparison and the asset
authentication need `data/external/` and report `BLOCKED/ASSET_MISSING` if it is absent; their stored outputs are
checked by `verify.py` for internal consistency, not recomputed.
