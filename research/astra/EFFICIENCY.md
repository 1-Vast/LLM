# Audit and evidence processing efficiency

This iteration reduces repeated work in the existing execution path. It introduces
no controller, selection policy, persistent cache, model backend or evidence rule.
Production changes are limited to `src/agent/memory.py` and `src/agent/knowledge.py`.
The base is `897471b226058b338ffd2f5a3a849d357100232f`; execution code is `24ccfb5`.

## Measured software benefit

The unchanged [benchmark driver](efficiency_benchmark.py) constructs 600-node
reverse-inserted chains, and an audit containing 600 receipts for each of two
unique views plus unrelated events. Each operation runs three times on newly
constructed fixtures. Setup is outside the timer. Measurements use the same
Windows maestro environment and patched file-read counters. Reported values are
medians; these are engineering timings, not biological or physical confidence
intervals. The fixtures deliberately expose depth and receipt duplication, so
their speedups do not estimate typical end-to-end agent or inference speed.

| Operation | Base median | Final median | Base / final |
|---|---:|---:|---:|
| Memory retraction | 56.70 ms | 10.94 ms | 5.18 |
| Evidence retraction | 424.46 ms | 10.93 ms | 38.84 |
| Visible-ancestor filtering | 48.17 ms | 8.63 ms | 5.58 |
| Authenticated case-review reconstruction | 1,988.95 ms | 630.55 ms | 3.15 |

Audit view reads fall from **2,400 to 2**. The four output SHA256 values match
between the base and final run. Raw samples, source hashes and environment are in
[baseline.json](results/20261003_efficiency_v1/baseline.json) and
[optimized_final.json](results/20261003_efficiency_v1/optimized_final.json).
`optimized.json` retains the intermediate successful measurement; the table uses
the final code measurement. Three repeats describe local timing variability;
they are not a broad performance study or a guarantee for other graph shapes.

## Changes and preserved contracts

Memory and evidence retraction now build parent-to-child adjacency once and walk
reachable descendants with a visited set. Visibility propagates missing or
invisible ancestry through the same local graph traversal pattern. Dependency
traversal changes from repeated full scans, worst-case quadratic on these chains,
to O(V + E). SQLite loading/writes, claim checking and record parsing still have
their own costs. Temporary adjacency storage costs O(V + E); no persistent graph
or second fact authority is maintained.

The two stores retain their different permissions and retraction semantics.
Memory retraction only traverses active records; ledger retraction includes already
retracted records and still invalidates dependent claims without appending the
same reassessment rationale repeatedly. Missing/private/out-of-case/retracted
ancestors continue to hide descendants. Existing closed legacy-cycle visibility
is preserved by parity tests; this does not certify those records scientifically
or relax the public evidence ingress.

RunLogger streams events instead of loading the entire event file into memory.
For every unique view, it hashes and strictly parses the **same bytes**, validates
the RoundRecord once and retains an invocation-local authenticated snapshot.
Every retry receipt still checks its case, session, plan version, result identity,
expected path, containment, receipt hash and CaseStore ownership. Changed receipt
hashes cannot bypass validation by reusing an identity. Missing views, incomplete
coverage and absent original plans remain blockers. Later review calls read and
authenticate files again, so a file modified after an earlier review is rejected.
There is no cross-call trust cache or new guarantee of an atomic snapshot of files
being concurrently edited. The supported writer already makes these views immutable.

Failure explanation also streams events and returns the original first matching
failure. Prediction binding, inference/cache policies, action selection, evidence
admission, result facts, actual/reserved budgets and model APIs are unchanged.
An inspected prediction path was not optimized speculatively: its validation and
mutable-input fingerprinting remain intact, and no inference-speed claim is made.

## Verification and limits

- New tests compare retraction/visibility to independent fixed-point oracles for
  several deterministic graphs with cycles and multiple parents, preserve isolated
  records and claim invalidation, and reject conflicting duplicate receipts.
- Existing tests cover restart, both contradiction orders, multiple results,
  corruption after a successful review, missing views, original-plan binding,
  source scope, immutable records and first-failure explanation.
- Targeted verification passed 44 tests before the final three visibility cases
  were added. Final Windows default core passed **324**. The complete previously
  registered aggregate passed **1,993**, with no failure, error or skip. These
  overlapping counts must not be summed.
- Clean native Linux checkout and isolated test environment verification are
  recorded in `results/20261003_efficiency_v1/linux/`; the receipt owns its result.
- The existing audit reports **2,058 protected files unchanged**, original
  extraction parity and the old day-log prefix preserved. The current iteration's
  longer initial log prefix is checked separately in the new receipt.

Initial benchmark construction was rejected for a contradiction flag without a
belief delta. The fixture was corrected, and both immutable writes now assert
success. Initial new tests assumed a nonexistent claim timestamp column and put
unscoped records behind an explicit scope: seven fixture tests failed, eleven
passed. The tests were corrected against the actual schema/access contract and
then all eighteen passed before production edits. Details remain in
`results/20261003_efficiency_v1/before.json`; these were not scientific negative
results or production regressions.

No new STATE forward, live LLM/API call, training, physical experiment, calibration,
state-gain evaluation or agent utility comparison ran. Dataset qualification,
independent physical units, legal predecision availability, action support,
realisation measurements and reliable prices remain the scientific blockers.
Engineering speedups do not answer whether state improves prediction, changes
action ranking, improves measured utility or resolves competing mechanisms.

## Reproduction

Run from the repository root in maestro, with fresh output paths:

```powershell
$env:PYTHONPATH = 'src'
$py = 'D:/anaconda/envs/maestro/python.exe'
& $py research/astra/efficiency_benchmark.py --count 600 --repeats 3 --out NEW_OUTPUT/benchmark.json
& $py -m pytest -o addopts= -q --junitxml=NEW_OUTPUT/core.xml
& $py -m pytest tests research/astra research/scientific_optimization/test_population_flow.py research/scientific_optimization/test_response_training.py research/case_memory_integration/test_external_evaluation.py -o addopts= -q --junitxml=NEW_OUTPUT/full.xml
& $py research/astra/convergence_audit.py --out NEW_OUTPUT/preservation.json
```

For the base comparison, create a separate detached worktree at `897471b`, change
to that root, set `PYTHONPATH=src`, and invoke the driver from execution commit
`24ccfb5` by its absolute path. This uses the identical fixture code against base
production modules, without modifying historical source or results. The driver
records both module hashes and the exact driver bytes. It is independent of the
large historical datasets.

The full aggregate continues to require prepared historical assets. Use the exact
published recovery packages and instructions in [CONVERGENCE.md](CONVERGENCE.md)
and [PREDICTION_AUDIT_FOLLOWUP.md](PREDICTION_AUDIT_FOLLOWUP.md). Missing assets
remain explicit blockers; no automatic skips or frozen-hash replacements were added.
Linux's default core needs only the declared test extra; the self-contained
[verification script](results/20261003_efficiency_v1/linux_verify.sh) requires new
checkout, environment and receipt directories and a pinned pip bootstrap file.
