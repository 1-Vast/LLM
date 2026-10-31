# Independent B code and access review

2026-10-30, before B numerical access. The reviewer previously reviewed A but did not co-author B's scientific design. Model/effort were inherited; effective settings are unknown. No real profile header/body, phenotype values, B results or model main function were opened/executed.

## Verdict

**ADMIT the final inspected implementation for the single bounded exploratory B matrix, subject to the required final execution/input manifest and independent arithmetic-verifier freeze. No remaining blocking scientific/operator/access defect was found.** Before numerical access, the manifest must bind the final scripts, controlling protocols, metadata/split, chemistry, checker and all eight original complete profiles to their admitted source hashes. Main verifies every listed hash before profile interpretation; manifest completeness remains a final prelaunch check. The execution manifest was absent when checked during this review.

Use `D:/anaconda/envs/maestro/python.exe` directly; the launcher inherits its interpreter. Admission does not establish useful phenotype signal, predictive benefit, biology, novelty or practical probe-selection benefit.

## Access and processing

The metadata reproduce 260 lexical compound IDs, 255 identity groups, 130 targets and folds 47/56/56/52/49. Groups never cross folds; the declared hash-to-fold rule matches. All six metadata-freeze hashes match; the chemical NPZ was hashed without decoding. The 198 source-supported and 62 source-unseen-target query counts match.

Every chemical plate contains the intended 260 treatment rows plus 64 negative controls; each ORF plate contains two treatment wells for each of the 130 targets plus 60 negative controls. No admitted treatment falls outside the split/target catalog. Expected admission is **2,576 rows / 14,920,192 numeric cells**, skipping **496 rows**. These are metadata counts, not observed numerical-access counts.

Final `read_profiles` parses only the plate/well prefix before admission. Only `trt` or `negcon` rows reach feature parsing/conversion; positives and empties are skipped. Pinned identity strings contain no commas/newlines, supporting the prefix convention. Duplicate/unknown/missing identities and unequal 5,792-feature headers terminate. An instrumented synthetic CSV proved excluded feature payloads never reach either `csv.reader` or numeric conversion. The coordinator tightened this boundary during review before real access.

Negative controls alone determine each plate's median, `1.4826*MAD`, and the all-eight-plate finite/scale>1e-12 feature intersection. Fewer than 100 features stops. Retained treatment nonfinite values stop with `DATA_NONFINITE`; excluded columns do not cause response-based exclusions. Own-plate normalization and [-10,10] clipping precede the componentwise median of two ORF wells. Negative controls and measured ORF references are permitted prediction-time information with assay cost attached. Different control origins, fixed layouts and shared references remain limitations.

## Operator, rivals and arithmetic

All four chemical-plate by ORF-plate cosines are retained with the correct axes and zero-norm rule. Their mean is primary. The two chemical-repeat summaries average both ORF plates; diagonal/off-diagonal sensitivities reuse the same fixed actions. They do not increase the independent query count.

Inputs follow the frozen chemistry/target/cell and spatial definitions. The 46-column spatial basis includes explicit outer-two-row/column membership. In-memory synthetic fingerprints produced pooled/conditional/spatial/combined shapes 520x1154, 520x2309, 520x185 and 520x2494. All 384 well positions were checked. Spatial inputs use metadata only; query chemical profiles never enter them.

All five-fold fits exclude query IDs and both contexts. Source-only population-standardization, intercepts, Ridge100 and centered RBF1/gamma match the protocol. Global, pooled-target, cell and target-cell shrinkage use only source responses and the ten-observation fallback. The final twelve-method order and fixed candidate index 6 match. The strongest other-eleven comparator uses the first exact float64 tie in listed order, with lexical compound/cell summation and no tolerance.

Utility, regret, MSE, oracle and sign agreement match the contract. The group bootstrap uses both cells/all IDs, lexical groups, seed 20261032, 2,000 draws, proper sampled query counts and default linear quantiles. Repeat/sensitivity gains reuse the selected comparator without refitting/reselection. The gate requires positive full gain, both repeat gains positive and interval lower bound positive; there is no p-value. Robust-benefit, core-promotion and Agent gates remain false. The interval remains conditional on fixed predictions/comparator and omits shared-reference/control, selection and refitting uncertainty.

## Synthetic checks and failure handling

- Bundled Ridge fixture passed: maximum error `2.7755575615628914e-17`.
- Independent primal Ridge and centered-RBF fixtures, including constant columns/nonzero response mean, passed: errors `5.551115123125783e-17` and `3.3306690738754696e-16`.
- Generated control/treatment fixtures retained the expected 104/106 features, clipped chemical effects at 10, returned ORF median 7 from clipped normalized wells 20/4, and stopped on a retained treatment NaN. Independent loops reproduced all four cosine axes and zero norms.
- Source-only spies verified all 30 fitted-method dispatches; independent scalar calculations verified every simple mean/shrinkage output and absent-target fallback. Fits and filesystem writes were stubbed for this dispatch check.
- Five atomic checkpoint dispatches passed. The coordinator changed checkpoints to temporary-NPZ/replace before incrementing the fold receipt. One synthetic harness initially needed adapting to that replacement; its corrected in-memory rerun passed. No real matrix or repair reserve was consumed.

The launcher has the 1,800-second child limit, exit/failure receipt and no replay; the child sets four numerical-thread limits and bounds fit thread pools. Failure marks the run failed and all decision gates false, preserving the last completed checkpoint and reporting unavailable forced-stop CPU time. No main-path timeout experiment was performed. Eventual real saved-effect/prediction arithmetic remains the separate frozen verifier's work.

## Final SHA-256 identities

Episode-relative paths; final code includes only the prelaunch access/checkpoint corrections, with scientific settings unchanged.

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

Budget/access: **0 HTTP requests/body bytes/partial bytes; 0 real profile header/body or phenotype/outcome reads; 0 main executions, real-data fits, installations or model-code edits by the reviewer.** Synthetic values were generated in memory; no fixture/model-output files were written. Only this review is written. No agent was spawned.
