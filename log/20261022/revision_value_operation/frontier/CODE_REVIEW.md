# Independent pre-value CDK functional code review

2026-10-22. **No remaining blocking defect found in the reviewed narrow protocol.** This approves only proceeding to the root's separately authorized, frozen exploratory test; it does not claim biological validity, a new method or prospective independence. I did not open S4, prepared.npz, old numerical predictions or any new outcome/result file. Read run.py, test_run.py and PROTOCOL.md statically. Root owns the source/identity qualification and experiment execution.

## Findings and corrections before S4 access

The initial evaluate() constructed eligible as list(np.flatnonzero(...)); its NumPy integer entries would fail json.dumps after outcomes were read. I reported this to root; root changed it to .tolist(), and added an evaluate-to-JSON synthetic check. The first reviewed predictor used pooled source ranks. Root changed this before value access to ranks computed separately within each source condition and each challenge, matching the clarified biological contract. Neither correction used outcome values.

The final target is the within-source-condition midrank (#lower + .5 #equal)/n. The within-condition mean is .5; singleton/constant groups have zero response residual. Features are centered using source members of the same condition (pooled source features only when none exist). A target condition with three cultures and a jointly held-out pair has at most one training culture; therefore its own residual and centered feature are zero, and a nontrivial pair ordering uses a mapping learned from other conditions. The protocol now states this explicitly. This is neither an independent within-condition response fit nor a calibrated IC50 prediction.

## Leakage and parsing boundaries

- Both held pair indices are excluded before target-rank construction and all response accesses inside predict() use train. Feature-centering members are also source-only. Computation of the all-culture Gram is transductive in measured prefix features, as declared; it does not use held labels.
- grams() uses only data[:,0] and data[:,1], square-root transforms them and constructs Early or the equal-weight Early/Middle Gram. Loading the compressed compositions array materializes End; neither this static review nor the test falsely calls that 'End never read'. End does not enter the prediction path. Existing source preparation/universe lineage remains the root's independently qualified dependency.
- read_selected() verifies the exact S4 file hash, matches resistant sample identity through B, converts only matched rows' C/D cells to float and skips vehicle outcomes. It rejects formulas on decoded cells and rejects invalid positive-finite outcome values. It requires exactly the expected sample-name set with no duplicate selected identity. It does not infer censoring from N/A.
- XML and shared strings are read/materialized for the worksheet, and B identities are decoded for other rows. Thus 'selective numeric conversion/use of matched C/D outcomes' is accurate; 'never materialized any other worksheet bytes or strings' would be inaccurate. Formula rejection is scoped to decoded identities/selected outcomes, not a whole-workbook formula audit. C/D challenge meaning relies on the pinned source qualification, not a new independent header check in this code.

## Ranking and aggregation

The baseline assigns the same .5 condition rank mean to the pair. Constant source outcomes yield zero centered response and zero fitted coefficients, so differing feature distances alone cannot manufacture a non-tied prediction through penalized-intercept shrinkage. Fixed lambda 1 is primary and .1/10 are reported sensitivities; no score-based selection appears in the code. Kernel trace scaling is source-only.

Exact true ties are excluded before scoring and listed. Predicted ties within absolute tolerance 1e-12 receive .5 loss; other pairs use the sign of predicted versus actual differences. Loss is averaged first over scored pairs in each condition and then equally over conditions with scored pairs, separately by challenge. A condition with only true ties/missing outcomes contributes no ranking estimand, not an invented zero loss. Overlapping pairs/challenge columns are not used as independent replicates; no inferential test is implemented. Reporting needs to retain true-tie counts, missingness, the contributing condition set and the source sizes available in saved rows.

Root's last change explicitly records pairs with fewer than two eligible source cultures as nonestimable, with their train indices and reason. I statically reread that change; it introduces no label or selection path. The success gate remains the predeclared direction requirement across both challenges and fixed sensitivity values. Missing/nonestimable cases cannot be silently turned into successes or biological null results.

## Verification actually executed

Executed only `D:/anaconda/envs/maestro/python.exe -B test_run.py` in the experiment code directory: **5 tests passed**, 0.235 seconds reported by unittest. They cover held-pair label exclusion and midranks; End-invariance; no-feature-signal ties; constant-source-target ties plus evaluate/JSON serialization; and separate monotone transformations of source conditions. Importing run.py does not invoke main(), read_selected(), or any source file. The later nonestimable-record edit was statically reviewed after this run; no broad new testing or biological execution was performed.

CODE_REVIEW_BINDINGS.json records the earlier test-time file hashes; CODE_REVIEW_BINDINGS_FINAL.json records the final static-review versions after the explicit nonestimable-record addition. No claim is made that all output values, actual missingness or source numerical coordinates have been audited before they exist. No old sealed research file was changed.
