# Pre-fit source code gate

2026-10-22. Static read only of diagnose.py, imported calibrate.py implementation and updated qualify.py. No imports, fits, numerical source tables, raw bodies or protected labels executed/read in this review.

Verdict: NO_EXECUTABLE_BLOCKER_FOUND for the frozen bounded descriptive diagnostic.

The SHA256 first-eight-byte big-endian modulo-five pair fold rule matches the protocol. All source pair guide/replicate observations remain in a common pair row. Inner training is first floor(3*n/4) after sorting outer-train source_order, with the remainder for candidate selection. Inner quadratic uses only inner-training y; outer quadratic refits only outer-training y. Ridge scalers use their training rows only. Completion receives only training residuals/indices. The common single RNA SVD/correlation uses paid single inputs, without pair outcomes. Priors are the existing permitted single growth inputs. Candidate validation selects among three parameters per applicable arm, never outer scores.

Fit accounting: each fold has two quadratic fits, two ridge arms each with three inner candidates plus one refit, and two nuclear arms each with three inner candidates plus one refit: 18 per fold, 90 total. No NAIAD refit is needed for this scope; no strongest-direct exhaustion claim is supported.

Direct reads are SOURCE_REPLICATES.csv, qualification summary, identity-only PAIR_SPLITS, SINGLE_RNA_FEATURES and SINGLE_GROWTH_PRIORS. The imported completion module has no numerical reads at module scope; its old-development-reading main is guarded and never called. The diagnostic asserts every supplied source pair belongs to source, checks complete finite endpoints and enforces separately averaged replicate discrepancy <=1e-10 after qualification PASS (which covers equal finite support). No raw body/protected numerical read exists in diagnose.py.

Outputs include original replicate means/offset, each arm residual means and centered residual correlation, pair-weighted guide disagreement/within-screen guide SD, and disagreement quartiles marked descriptive. No correction/reweighting uses those held-out statistics. The exact decomposition uses replicate mean, with y scored separately. Signed cross-products remain unclipped; result scope explicitly excludes noise variance, ceiling, biological structure and predictive-headroom claims. Nuclear stop flags are retained, enabling disclosure rather than outcome-driven rescue.

This is a static implementation audit, not independent numerical reproduction. Root and biology were sent the findings before fits; independent seals and prior cross-review remain unchanged.
