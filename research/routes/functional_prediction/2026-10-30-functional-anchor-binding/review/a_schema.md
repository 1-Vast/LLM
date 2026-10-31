# A saved-output schema and independent verification scope

Frozen before the independent verifier reads new A outcome arrays. This file
records the coordinator's schema clarification to `output_contract_a.md`; the
protocol, v1.1 amendment, and numerical amendment retain precedence.

## Independent map reconstruction

Build `blocks = {g: np.flatnonzero(groups == g) for g in np.unique(groups)}`.
Visit these lexical groups in `np.unique` order and append each group to the
stratum keyed by `tuple(rounds[blocks[g]])`; tuple length encodes block size.
Initialize `np.random.default_rng(20261030)` once. For each of 49 draws, start
with the identity row mapping, visit `sorted(strata)` keys, draw
`rng.permutation(len(names))`, and let destination `names[target]` receive the
ordered row indices of `names[source]` for `target, source in enumerate(order)`.
Destination row i receives original call row `assignment[i]`. Apply the same
assignment to source and validation labels. `movable_compounds` counts rows in
strata containing more than one scaffold; `distinct_mappings` counts unique
complete mappings across the 49 draws.

## JSON keys

`summary.json` uses:

- `methods`: eight method names in the frozen panel order.
- `precision`, `recall`: 8 by 231 per-compound arrays.
- `mean_precision`, `mean_recall`: dictionaries keyed by method name.
- `recovered_totals`: eight exact integer totals.
- `candidate_method`, `best_direct_method`, `selected_gain`,
  `selected_integer_gain`, `null_gains`, `null_integer_gains`, `permutation_p`.
- `oracle`: 231 source-eligible oracle values; `mean_oracle`.
- `eligible_gene_counts`: dictionary keyed by `str(fold)`.
- `distinct_mappings`, `movable_compounds`.
- `annotated_mean_precision`: dictionary keyed by method name; descriptive.

`decision.json` uses the keys in `output_contract_a.md`: `status`,
`information_gate_pass`, `held_out_release`, `paired_scaffold_interval95`,
`conditional_interval_above_zero`, `robust_benefit_established`. A failure or
incomplete matrix forces all boolean gates false.

`run.json` records `status`, `threads`, `completed_nulls`, `python`, `numpy`,
`failure`, `access`, `freeze`, `shapes`, `wall_seconds`, `cpu_seconds`.
`settings` contains `threads=4`, `null_seed=20261030`,
`bootstrap_seed=20261031`, `n_null=49`, `n_bootstrap=2000`, `teacher_rank=32`.
`freeze.sha256` maps absolute or repository-relative paths to their SHA-256
digests. `access` is a nonempty human-readable boundary disclosure, not an
independently verified access log. `shapes` includes
`calls=[231,18415]` and `ranks=[8,231,20]`; other saved shapes are checked directly.

`launcher.json` records `status`, `timeout_seconds=1800`, `python`, `exit_code`,
and `wall_seconds`. The configured Python is
`D:/anaconda/envs/maestro/python.exe`. `permutation_assignments.npz` uses key
`assignments`, identical to `ranks.npz/null_assignments`.

`teacher_diagnostics.json` uses `aligned` (fold-keyed dictionary) and `nulls`
(49 such dictionaries). Each fold record contains `rank`, `positive_modes`,
`largest_eigenvalue`, `tolerance`, `boundary_gap`, `eligible_genes`. Rank is
`min(32, positive_modes)` and tolerance is `1e-10*max(1,largest_eigenvalue)`.
If positive modes exceed 32, the boundary gap is eigenvalue 32 minus 33 and
must exceed tolerance; otherwise the gap is null. The verifier checks these
declarations and the independent eligible counts, without recomputing the
eigensolution or source-centering operators.

## Limits

The verifier recomputes saved-rank arithmetic, eligibility, exact frequency
ordering and ties, coherent maps, integer direct selection and null test,
integer scaffold bootstrap, completeness, decisions, and required metadata.
It does not import the model implementation, launch fits, reconstruct full
unsaved predictions, establish label ancestry or biological validity, or
certify scientific claims from an arithmetic pass. The verifier itself is
hashed before any real A output arrays are read by its author.
