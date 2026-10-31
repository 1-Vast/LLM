# Independent numerical-verifier preaccess record

Recorded 2026-10-30, before running the independent verifier or inspecting any
primary numerical output.

## Reading and independence

- Read `protocol_c_census.md`, `protocol_c_census_v1_1.md`, and the permitted
  `audit_c_metadata.json`. The metadata file was loaded in full; displayed
  output was truncated. A later selection read only HTS001's source path,
  SHA256, columns, and background labels. These files expose assay metadata and
  protocol-expected denominators, not treatment count values or census findings.
- Read only the header of the original local `hts001_raw.body`. No raw
  `cell.count` value was displayed, decoded, or used during authorship.
- Did not open `census_c.py`, `census_c_result.json`, any `census_c_*csv`, or
  another report of the primary endpoint/flip/reproduction counts.
- Authored `verify_c_independent.py` from scratch in a separately delegated
  agent context. It uses standard-library CSV/data structures, Decimal dose
  matching, and NumPy arithmetic. It does not import the primary code or read
  primary outputs. The implementation is independent of the primary code;
  the observations and frozen scientific protocol are shared. This is not
  biological replication, independent experimental validation, or an
  independently selected scientific analysis.
- The agent inherited its model configuration. Requested/effective provider,
  model, and reasoning metadata are unavailable and are not inferred.

## Frozen arithmetic and assumptions

The verifier calculates linear interpolation of counts at 24 and 60 hours
using only frames strictly before 72 hours. An exact observed target frame
uses that frame alone. It checks positivity and finiteness only for the counts
needed by these endpoints. It subtracts the median valid vehicle log2 growth
on the same plate, retains all wells and reasons for exclusion, and retains
all input backgrounds in the denominator audit.

Only complete two-well treatment conditions enter pair calculations. Drug
orientation is lexicographic drug A minus drug B; wells are sorted
lexicographically for the two pseudo-replicates. Numeric doses use exact
Decimal equality, with no dose interpolation. Every positive/negative mean
contrast witness is retained, including its technical-concordance flag. The
fixed margin is 0.25 log2 units. Both matched pseudo-replicates must meet the
directional margin and all four cross-well differences must have the required
strict sign at each technically concordant witness.

The primary witness uses the lowest numeric positive and lowest numeric
negative dose among technically concordant witnesses. The source unit is one
cell by unordered drug pair. Target availability requires complete two-well
measurements for both drugs at both exact witness doses. The verifier reports
the mean source-unit sign fraction, its denominator, the pooled fraction,
and the stricter margin fractions. Exact zero contrasts fail sign reproduction.

The frozen source has one plate per background and two input wells per
treatment condition. The verifier stops on violations of these structural
assumptions, changed source SHA256, unsupported units, changing well identity,
or duplicate/invalid frame times instead of adding an unregistered aggregation
policy. There are no fits, threshold sweeps, network calls, installations,
core edits, or shared-index edits.

## Freeze and execution

Only syntax was checked with `ast.parse`; the verifier was not imported or
executed. No independent numerical result exists at this preaccess stage.

Frozen script SHA256:

`412745d85b57a00f2b5b6571e4c30155d2a7e738a84d78dd87d16aaae404edab`

The coordinating agent can run the frozen script using:

```powershell
& 'D:\MAESTRO\.venv\Scripts\python.exe' 'D:\MAESTRO\research\routes\functional_prediction\2026-10-30-virtual-cell-four-directions\review\verify_c_independent.py'
```

It saves `review/c_independent_wells.csv` and
`review/c_independent_result.json`, including source/protocol/script hashes,
before any separate comparison with the primary census. The script itself
contains no primary-output comparison. Any implementation correction after
first execution must be separately recorded with its reason and new hash.
