# Independent B implementation and access review

2026-10-30. Reviewed before B real-data execution. The reviewer's earlier A code review is disclosed; the reviewer did not co-author B's scientific design or implementation. Model/effort were inherited and effective settings are not independently asserted. This review covers the retained B protocol, amendment and output contract, source/metadata restrictions, final `b.py`/`run_b.py`, and synthetic checks. No phenotype profile body, profile header, B outcome or model result was opened.

## Verdict and launch conditions

**ADMIT the final inspected implementation for the single bounded exploratory B matrix, subject to the already required execution/input manifest and independent arithmetic-verifier freeze. No remaining blocking scientific/operator/access defect was identified in the final hashes below.** The execution manifest did not exist when checked during this review. Before numerical access it must bind the final code, controlling protocols, metadata/split, chemical inputs, frozen checker, and all eight original complete profile files to their admitted source hashes. The main function verifies listed hashes before reading profile rows; the completeness of that list remains a final manifest check.

Launch with `D:/anaconda/envs/maestro/python.exe` directly: the launcher inherits `sys.executable` rather than enforcing an interpreter path. Preserve the one-matrix/no-automatic-rerun and shared implementation-failure-only reserve rules. This review makes no claim that B will pass, that its assay geometry measures a causal mechanism, or that a positive gate establishes practical benefit or novelty.

## Row access and identity audit

The actual frozen identity metadata and split were read without numerical profile values. They reproduce 260 lexical compound IDs, 255 identity groups, 130 nominal targets and folds 47/56/56/52/49. Group members share a fold, and the declared SHA256 group-to-fold rule matches. All six hashes in `b_metadata_freeze.json` match; the chemical-feature archive was hashed as bytes, never decoded. Target-support metadata reproduce 198 IDs with another source compound for their target and 62 without. Both remain in the denominator.

Each of the four chemical plates has 260 admitted treatment rows and 64 negative-control rows; each ORF plate has 260 treatment wells for exactly the 130 split targets and 60 negative-control wells. No treatment compound outside the split or treatment ORF gene outside its targets occurs in the admitted metadata. Expected admission across all eight plates is **2,576 rows / 14,920,192 numeric cells**, with **496 rows skipped**. These are metadata-derived expectations, not observed feature-decoding counts. Compound treatments occur once and target ORFs twice per plate as required.

Final `read_profiles` first splits each physical line at its first two commas and parses only the plate/well identity prefix. It checks the pinned plate/well roster, duplicates and eventual completeness before interpreting permitted feature fields. Only `Metadata_pert_type == trt` or `Metadata_control_type == negcon` passes the feature parser and numeric conversion. Positive-control-role and empty rows therefore never tokenize their phenotype fields. Metadata plate/well strings contain no embedded commas or newlines; this supports the pinned identity-prefix convention. Headers are handled separately and must be identical, with two identity fields and 5,792 features.

An initial version tokenized the entire CSV row before its numeric-admission check. The coordinator tightened this boundary during review, before any real values. An instrumented in-memory CSV fixture placed forbidden tokens in excluded feature payloads and made the CSV parser fail if those payloads reached it. The final loader passed with exactly two admitted rows and two skipped rows, with neither excluded tokenization nor excluded numeric conversion. Real profile files were never opened to perform this test.

The access receipt records admitted counts, well identities, per-plate control/treatment counts and skipped counts; pinned metadata retain identities of skipped rows. Its `all_hashes_checked=true` is warranted by the preceding main hash loop only when the final manifest includes every actual input. The reviewer did not rehash or inspect original profile bodies. No CGI, S2, HTS031, protected historical outcome or network access appears in these B code paths.

## Controls and response construction

`preprocess` uses negative-control values alone for each plate's componentwise median and `1.4826 * median(abs(control - median))`. The all-eight-plate mask requires all controls finite and scale finite and greater than `1e-12`; fewer than 100 surviving features terminates. It never selects a feature using chemical activity, outcome agreement or prediction quality. Retained treatment nonfinite values terminate with `DATA_NONFINITE`; unretained feature values cause no response-based row exclusion or imputation.

Each admitted treatment/control is normalized by its own plate and clipped to [-10,10]. Chemical effects use the single treatment well; ORF effects use the componentwise median of their two already normalized/clipped wells. Cells follow A549/U2OS order and the two plates per modality/cell follow lexical order. A synthetic fixture with 106 generated features retained the expected 104 after control-only failures, allowed nonfinite values in excluded columns, produced chemical clipping at 10, produced an ORF median of 7 from normalized wells 20 and 4 after clipping, and stopped on a retained treatment NaN. No real feature values entered it.

`relation_grid` computes every chemical-plate by ORF-plate cosine with axes compound, cell, chemical plate, ORF plate. Norm-zero pairs give zero, and numerical cosine values are clipped to [-1,1]. The primary relation is the mean over both plate axes. Each gate repeat averages both ORF plates for one chemical plate; diagonal and off-diagonal sensitivities use the specified fixed grid cells. Independent synthetic dot-product/norm loops reproduced all grid entries, including zero norms. Four cross-products remain summaries of the same query, not four independent observations.

The control/ORF measurements are allowed costly prediction-time references under the protocol. Chemical query values construct evaluation truth and never enter a fitted source response for their held-out fold. DMSO and biological ORF controls define separate assay origins; normalization and the spatial rival do not certify biological equivalence, nuisance removal or culture independence.

## Inputs, source-only rivals and arithmetic

The chemical input is the pinned 1,024-bit fingerprint plus 130 design-target indicators; broader target lists are unused. Pooled rows repeat each compound's input in both cells. Conditional inputs append signed cell (-1 A549/+1 U2OS) and its interaction with every pooled column. Position vectors have 46 columns: 16 row and 24 column indicators, row/column normalized to [-1,1], their squares/product and explicit outer-two-rows-or-columns membership. Chemical and matched-ORF position vectors are averaged across their recorded wells separately by cell, concatenated, and given cell/interactions. The combined rival concatenates the specified conditional and spatial inputs, including their declared repeated cell column.

Synthetic fingerprints substituted in memory yielded the expected feature shapes: pooled 520x1154, conditional 520x2309, spatial 520x185, combined 520x2494. Every one of 384 well positions was checked for indicator and outer-region semantics. No real fingerprint archive was decoded for these checks.

The five source/query splits exclude every query group's IDs and both contexts. Every fitted design uses only source feature means/population SD, source responses and the fixed alpha. Ridge uses alpha 100 and an unpenalized intercept. RBF uses alpha 1, source-varying-column gamma, source/kernel centering and response centering. The output is clipped to [-1,1]. Independently constructed primal Ridge and centered-kernel calculations, including constant features and a nonzero response mean, agreed at maximum errors `5.551115123125783e-17` and `3.3306690738754696e-16` respectively. The bundled synthetic Ridge check also passed at `2.7755575615628914e-17`.

The 12-method order matches the amendment. Global, pooled-target, cell and target-by-cell means/shrinkage use source rows only, with ten pseudo-observations and the declared absent-target fallback. A synthetic source-only spy checked all 30 fitted-method dispatches (six per fold), exact train/query feature slices and source response slices; independent scalar sums checked all simple mean/shrinkage outputs. These dispatch tests used generated relations and stubbed fits, not phenotype outcomes or real fitting.

Main arithmetic uses float64 arrays in the fixed lexical compound/A549-U2OS order. Utility is sign(prediction) times the primary relation; exact zero abstains. Regret, MSE, per-cell means, oracle and sign agreement match their contracts. Candidate index 6 is fixed; the other 11 methods remain in listed order and `argmax` takes the first exact floating tie. The bootstrap sums candidate-minus-selected-direct utilities across both cells and all IDs in each lexical group, uses count twice the IDs per group, 2,000 draws/seed 20261032 and default linear quantiles. Repeat/sensitivity gains reuse the same candidate/direct signs without refitting or reselection. The gate is exactly positive full gain, both chemical-repeat gains positive, and interval lower bound positive. No p-value is computed. Robust benefit, core promotion and Agent gates remain false on success or failure.

The eventual frozen verifier must independently check real saved-rank/effect arithmetic. This code review does not certify real aggregation, useful phenotype support, predictive performance, label biology, a prospective interval, or errors shared through controls, ORF references, fixed layouts and fitted models.

## Failure and time limits

The launcher records its 1,800-second subprocess timeout, exit code and elapsed/failure; it does not replay. Child and launcher both refuse existing execution journals. The child sets four numerical-thread limits before NumPy imports and limits source fits to four numerical threads. Launcher failure marks the run failed, preserves the returned exit code or timeout null value, records elapsed time/CPU unavailability, and forces every decision gate false.

During review the coordinator changed fold checkpoints to temporary NPZ plus atomic replacement, then advances `completed_folds` and writes the run receipt. Five replacement dispatches passed the synthetic in-memory fixture. A forced stop can leave an incomplete temporary file while retaining the last completed checkpoint. One initial synthetic dispatch harness failed because it stubbed NPZ writing but had not yet stubbed the newly added replacement; the harness was corrected in memory and passed. This was neither a B main execution nor a real matrix failure and does not use the global repair reserve. No timeout/main-path runtime experiment was performed.

## Final inspected SHA-256 identities

Paths are relative to this episode. Final code hashes include the identity-first loader and atomic checkpoint fixes; scientific endpoints, candidates, inputs and hyperparameters were unchanged.

| File | SHA-256 |
|---|---|
| `brief.md` | `16a01753825ce5a170b2fab2ab441e0eacef1574e44918cc838b7ff1fce5d6cd` |
| `protocol_b.md` | `95ea64ad2a3a386f951ba3926df8396a83be9714692fd5dd48bd132cdb7f2fff` |
| `protocol_b_v1_1.md` | `362e6cd85dcc18bc4ba2ce55f21dc9b6558405dbd005b20d8a73537613838f46` |
| `output_contract_b.md` | `dbd87180474f3ca2ca740fa533551cd09a212fa57d4eed284b37de3512e9c767` |
| `b.py` | `2e65fe8f8041b2388097206f092afbe305d7eceaca5624652e29847e684401c9` |
| `run_b.py` | `1a9cd105d3955b9918abf9a5aa8d9657abf59fb1cbe60b5451fdf4edb9b2aed5` |
| `b_metadata_freeze.json` | `12656ab8fd2529bfd6e51b1b166b9fa2606d24755116e1b7a130ddf6ac41d6f8` |
| `prepare_b_metadata.py` | `97ec47d67c3ad85a1238b79f059d31d0c261d0e4f9c872e83f832f955f9609f9` |
| `b_compound_split.tsv` | `3c1bbb61ad85dde7130df9a41b2caf3334799d9bb47ab9a384d66cdebe06d7b5` |
| `b_chemical_features.npz` (hash only) | `aa1d779bef69d7d87b36ccc4e37317c4ec0371f5af711ec65fad55dd46e1e86c` |
| `cpjump_source/compound_identity_and_annotations.tsv` (hash only) | `27ee1004447ec31b85e1cdce1fe28d44652a10635280e180434d66db371a11f0` |
| `cpjump_source/compound_structure_grouping.tsv` (hash only) | `bf59b0760a294d0a6a68eebe13eeaf1e473e142303ab7fe58718228000086cff` |
| `cpjump_source/selected_well_identity_freeze.tsv` | `0b3145e32e6798a97552b6563e8fb1dd99499509c14d6465083d32c6b6155983` |
| `cpjump_source/admission_contract.md` | `d30d6c4f14e35c3674e877bfba23f7474d643bb98ee3083abd2c221ff7c5bb8d` |
| `cpjump_source/metadata_dictionary.md` | `780669cdcf2ba3183898f348b449d2f78d41e16aa38c5ddc04c10a677e3e5f9a` |
| `review/b_protocol_initial.md` | `65dddfe7903e22a7c1f4ea90e6f406382f16aaed97456d9a14c93055f363a27e` |
| `review/b_amendment_check.md` | `94ac340d683491d1ec2c4f5e82c746bcb23cbaa164d9c1f07bcea540ec0577c1` |

Access/budget: **0 HTTP requests/decoded response bytes/known partial response bytes; 0 real profile body or header reads, 0 real phenotype/outcome reads, 0 main executions, 0 real-data fits, 0 installations and 0 model-code edits by the reviewer.** Synthetic profile values were generated in memory; no fixture files or model outputs were written. Only this review is written. No agent was spawned.
