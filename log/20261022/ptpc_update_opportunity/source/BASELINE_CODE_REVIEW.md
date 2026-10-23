# Independent pre-execution baseline code review

Scope: static review of `prepare_baseline.py`, `evaluate_baseline.py`, `test_baseline.py`, plus three synthetic tests. No mechanism drafts, future abundance values, preparation artifacts, fitted predictions or scores were read. The previous HCT116 label gate and identity-only source metadata are admissible inputs. No preparation or evaluation main routine was executed by this reviewer.

Reviewed code SHA256:

- prepare_baseline.py: `f65c088c11c6e16fa3462f6cad25dc935c373b2e4eda031ced8e2c44ab278d28`
- evaluate_baseline.py: `0b2b6b626841725aa14f415d786d2988586ced63c50a78d2aa7f3727830df28e`
- test_baseline.py: `85eea6e9eaf0e0a229ee0fd01ac16c731ce8d7247b97a115c03e20e7f0e957ab`

Verdict: no blocking label-leakage, cross-background abundance decode or demonstrated row-join defect found in these versions. A separate identity check sealed with this review validates the specific sample-key assumption used by preparation. This is permission to proceed with the finite development exercise under its frozen protocol, not certification of future numerical results.

## Decoding and correspondence

Preparation takes labels from the already-open HCT116 condition gate; strict-complete groups each have one known label key. Requiring molecular time 6 and asserting 601 conditions preserves the intended 6h-only population. It does not re-open A_metadata Efficacy cells or read labels from other backgrounds. B_drug_info accesses are restricted to Pert_ID and eligible conditions' declared name/SMILES; stored source headers agree with the hardcoded A/C/E positions. Metadata from every background and shared-string lookup nodes may reside in memory, but the resolver is not called on nonselected abundance cells.

For matrix rows, the background/time/eligibility test occurs before the loop that resolves abundance cells. Selected rows assert Sample_ID against metadata at the same ordinal position. Contiguous worksheet row numbers and full row count are checked. This is an ordinal join, not a many-to-many Sample_ID join. It reuses the prior sealed complete-ID-order authentication and rechecks both archive and exact S8 member hashes. It does not itself re-read first-column IDs on skipped rows. That is not a demonstrated pairing defect on the authenticated source, but the identity JSON must remain equal to its prior sealed hash; the review's identity check verifies it now. A future source substitution would require repeating full identity authentication.

The selected matrix values preserve missing tokens as NaN, finite stored zero as observed, and stop on negative/nonfinite intensities. The code applies log1p separately to each observed value, then nanmedian within Sample_ID, then nanmedian across distinct sample IDs per condition. This matches the root's explicit pre-value clarification. It differs from this reviewer's earlier raw-median-first recommendation; the difference is acknowledged and is acceptable because the order is fixed before outcomes of this baseline. No result-based transform change is authorized.

The implementation pools technical rows by Sample_ID rather than a composite context key. The attached identity check confirms that every selected Sample_ID has exactly one `(Cell_line, Pert_ID, time)` context on this exact source, so no cross-condition pooling is presently implied. All conditions have their metadata-defined selected sample IDs; aggregation does not filter on abundance or class.

## Chemistry and fold boundaries

The union-find now connects equal canonical SMILES and equal whitespace-removed/casefolded nonempty declared names, including valid/missing-SMILES aliases. Transitive components receive a stable minimum initial-key representative. Labels do not enter grouping or hashing. Fingerprints can differ within a conservative name-connected group, but the entire component remains in one fold. This resolves the earlier cross-representation alias gap without merging or selecting outcomes.

Outer and inner group hashes are deterministic. Inner tuning subsets are selected only from outer-training indices. Feature dropping, nanmedian imputation and StandardScaler fit only source-training protein rows for each fit; heldout values do not alter those transforms. Neither heldout labels nor full-data class frequencies enter logistic fitting, C selection or source-prior predictions. Class balancing is computed by sklearn from each fit's source labels. C ties retain grid order. Three synthetic tests passed, including target-value invariance of fitted training transforms and target-label invariance of tuning/prediction.

## Edge-case reporting and verification limits

At the reviewed evaluate version, a one-class source-training set silently returns the source prevalence for any family name; the synthetic test explicitly checks that behavior. This is safe with respect to heldout-label leakage, but the protocol should declare it before execution and the fold report should identify `prior_fallback`, rather than present it as successful chemistry/protein logistic fitting. This is a reporting requirement if that edge case occurs, not evidence that it will occur. All-inner-validation-AP-unavailable selects the first grid C deterministically. A zero-feature protein training partition raises an assertion; an empty outer fold also stops. Those stops are safer than silent repair, but should be recorded if triggered.

Tests do not exercise XML decoding, row correspondence or alias union end to end. The static reasoning and authenticated source identities support those paths, but future execution must still retain assertion failures, missingness/scale stops and convergence warnings. Do not weaken them based on favorable or unfavorable scores. No raw-assay provenance is claimed or required by this limited author-annotation development baseline. All other backgrounds and 24h protein values remain outside this run's decoding permission.
