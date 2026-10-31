# B independent arithmetic schema clarification

Frozen before the independent checker reads any B phenotype aggregates,
predictions or outcome summary. The checker author previously audited A; that
exposure does not include any B outcome. B uses a distinct morphology endpoint.

The controlling sources are `brief.md`, `protocol_b.md`,
`protocol_b_v1_1.md`, `output_contract_b.md`, `b_compound_split.tsv` and
`b_metadata_freeze.json`. Metadata-only source tables
`cpjump_source/compound_structure_grouping.tsv` and
`cpjump_source/selected_well_identity_freeze.tsv` are admitted to reconstruct
identity-group closure, folds, plate order, reference targets and allowed wells.

Group closure uses the exact frozen `same_name_group`,
`exact_InChIKey_group`, and `connectivity_block_group` keys without a new name
normalization. Each connected component's lexical minimum source ID names its
group. Its fold is `int(sha256(('20261030|'+group).encode()).hexdigest(),16)%5`.

The strongest comparator maximizes float64 full mean utility across indices
other than the fixed index6, in fixed lexical ID/cell order. Exact ties take the
first listed comparator. No numerical tolerance changes a winner or gate.
After selecting this comparator, selected gain is the float64 mean of paired
per-query candidate-minus-comparator utilities, not subtraction of separately
rounded means. The bootstrap and repeat/diagonal/off-diagonal gains use paired
utility differences and the same fixed signs and comparator. Tolerances of
1e-12 only validate saved arithmetic against independently reconstructed floats.

Global and pooled gene-shrink means count both ID/cell rows for each source ID;
the shrinkage weight is ten pseudo-observations. Gene-by-cell shrinkage uses
source IDs within the same cell and the same pseudo-observation weight.

`access_receipt.json` has status `complete` on success, root keys specified in
the output contract, and a `per_plate` dictionary. Each plate record contains
`decoded_rows`, `control_rows`, `treatment_rows`, `skipped_rows`, `allowed_wells`
and `path`. Expected allowed wells and counts are derived from the frozen
metadata. Only selected noncontrol `trt` chemicals, matched target ORFs and
negative controls are admitted. The eight original profile paths and SHA-256
values appear in the preexecution `run.freeze.sha256` manifest. The checker
checks these declarations and the loader's `all_hashes_checked` receipt without
opening the original raw profile files; the independent source/access review
owns original-byte hashing and decoding-boundary verification. The original
`source_manifest.tsv` is also a required nonraw input pin. Settings keys are
`n_bootstrap=2000`, `bootstrap_seed=20261032`, `alpha_ridge=100`, `alpha_rbf=1`.

The checker does not require future output files to have preexecution hashes.
It compares saved output identities and folds to the pinned split/metadata and
records postaccess hashes for all output artifacts. It independently rebuilds
cosines from saved normalized effect aggregates. This does not independently
certify raw control normalization, treatment aggregation, control-value
finiteness on omitted raw columns, or nuisance removal. The saved retained mask
must satisfy all recorded retained control scale/center constraints; the code
review separately checks how that mask was constructed from raw controls.

No B model implementation, raw phenotype feature cells, or numerical B output
is read during preparation. The checker and synthetic self-tests are frozen
before actual B access. No HTTP or fitting is performed by the checker.
