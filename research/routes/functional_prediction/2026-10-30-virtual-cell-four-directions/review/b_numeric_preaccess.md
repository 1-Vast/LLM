# B1 independent output-verifier preaccess record

Recorded 2026-10-30 before running this verifier or inspecting any B outer
model score, prediction content, or selected configuration.

## Actual reading scope

- Read the full frozen `protocol_b.md` and `protocol_b_v1_1.md`.
- Listed filenames in `audit_b` and the original AssayBench source directory.
  Loaded `audit_b/train_gene_hits_manifest.json` only to display its top-level
  keys; the queried `schema` member was absent. Read only the header of
  `audit_b/metadata_census_source.csv`.
- Read the training metadata CSV header, selected unique endpoint-category and
  cleaned-phenotype strings, and one example dataset identifier per endpoint
  category. The CSV was loaded in full to select these metadata fields; no
  per-task `gene_count` or `hit_count` value was displayed or inspected.
- Read the first 35 lines of `biogrid_temporal_train_metadata.json`, exposing
  the first record's schema, retrospective assay context and split fields,
  without its gene/hit-count fields or any per-gene outcome.
- Opened the training NPZ only to list array names, shapes and dtypes. This
  loaded arrays for structural inspection, but no gene-index array values,
  per-gene labels, hit frequencies, predictions or model metrics were
  displayed, scored, or used to modify scientific criteria.
- Received the prediction/roster schema and exact method identifiers from the
  coordinating agent as an artifact contract. Did not open `pilot_b.py`,
  `roster.csv`, `top50.json`, primary `scores.csv`/`summary.csv`, model objects,
  `selection.json` configurations/validation scores, or an outer-score report.
- No physical Parquet chunks, official validation/test arrays, or LaTest data
  were opened. No network, fitting, installations, core/shared-index edits or
  subagents were used for this verifier.

This is an independently authored implementation over the same original
observations and frozen scientific protocol. It is arithmetic and limited
roster/eligibility leakage verification, not biological replication or new
independent experimental validation. The agent inherited its model
configuration; requested/effective model and reasoning metadata are
unavailable and are not inferred.

## What the script independently verifies

The script reconstructs the 1,231 valid endpoints from original official
training metadata, requires an exact roster match, and verifies that every
source in the five-publication component maps to canonical group 29083409.
It recalculates SHA256 folds and infers the final-fit, inner-fit, validation
and test group lists. Those lists are checked for disjointness but are not
observations of actual fitted transformations or training calls.

For each outer test fold, it uses all valid endpoint rows in the four
non-test folds to recompute screen-weighted gene hit frequency and the number
of canonical groups measuring each gene. Rarity requires hit frequency
<=0.10 and at least three canonical groups. The <=0.10 comparison uses exact
integer counts (`10 * hits <= measured`). Scoring eligibility depends only on
having at least 50 measured fit-defined rare genes. It is recorded for every
valid endpoint before held-out hit counts are consulted for scoring.

The verifier requires all 15 actual methods to predict the same eligible
task set for both all-library and rare analyses. Every prediction must have
exactly 50 distinct valid gene indices, all measured and additionally
fit-defined rare for the rare subset. The vocabulary must exactly match the
original training cache. Uniform ranking expectation is computed separately
from held-out library prevalence as `random_expectation`; it is not expected
in `top50.json`.

Precision, recall, prevalence and random-adjusted precision are recomputed
from held-out binary hits. Zero-hit libraries retain zero precision and
undefined recall. Each aggregate averages tasks within canonical source
first and then sources equally, with separate task-weighted values and
defined-denominator counts. Outputs include the two required phenotype
subsets, the preset exclusion of sources 29083409 and 30971826, fixed-rival
source differences, and all five outer-fold differences.

The best baseline is selected from the frozen baseline panel using overall
source-macro rare precision and deterministic name ties. The paired bootstrap
holds that rival fixed and uses 2,000 canonical-source resamples, NumPy
`default_rng`/PCG64 seed 1030, sorted source order, and 2.5th/97.5th percentiles.
This specifies a random-generator convention where the protocol specified
the seed but not a generator. Both the fixed rare-rival and best all-library
rival comparisons are supplied as gate inputs. The verifier does not issue
an overall continuation decision or audit actual fitted text transforms,
hyperparameter selection, model scores, or training-code behavior.

## Freeze, environment and execution

The initial script hash was superseded before any execution or B outcome
access solely to adopt the coordinating agent's canonical-environment output
path correction. The default input run is now `pilot_b_maestro`, with a
simple optional `--run-dir` override. The artifact schema, scientific
criteria and numerical calculations were unchanged by this path correction.

Only `ast.parse` syntax checks have run, including a final check with
`D:/anaconda/envs/maestro/python.exe`. No independent B result exists at this
preaccess stage.

Frozen script SHA256:

`4112418ac55c5d77a747ac90107cf18bc34664900ed61094b67e77e9fbe7972b`

Canonical command:

```powershell
& 'D:\anaconda\envs\maestro\python.exe' 'D:\MAESTRO\research\routes\functional_prediction\2026-10-30-virtual-cell-four-directions\review\verify_b_independent.py'
```

The script saves `review/b_independent_scores.csv`,
`review/b_independent_summary.csv`, and `review/b_verification.json` before
any separate comparison with primary outputs. It never reads primary
score/summary files. Runtime input and verifier hashes are included in the
independent JSON. Any correction after first execution must be recorded
with its reason and new hash; scientific criteria remain frozen.
