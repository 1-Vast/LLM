# A output and independent arithmetic contract

Written before new real-data fitting. Model data directory: `data/processed/functional_anchor_binding_20261030/a`. A demonstrated global-reserve implementation repair, if needed, must use a separate directory with retained original outputs. No automatic replay.

`labels.npz` stores lexical `compounds`, lexical canonical `genes`, binary `calls` (231x18415), `folds`, `groups`, `rounds` and boolean `annotation_available`. Inputs are the corrected parent's exact development arrays and current metadata features; no other query outcomes. `ranks.npz` stores:

- `methods`: frequency, chemical_ridge100, knowledge_ridge100, joint_ridge1, joint_ridge10, joint_ridge100, joint_rbf1, joint_teacher32, in that order.
- `aligned_indices` and `aligned_scores`:8x231x20 gene indices and corresponding clipped finite predictions.
- `null_indices` and `null_scores`:49x8x231x20.
- `null_assignments`:49x231, the parent's frozen coherent reassignment mapping for source AND query truth. Destinationi receives call rowassignment[i].

Save `permutation_assignments.npz` separately with the same mapping. Partial ranks are atomically checkpointed and reported incomplete until49 nulls finish; incomplete execution forces false information/benefit/release gates. Preserve operator/teacher diagnostic identities and source-centering/eigenvalue metadata without claiming this is a full independent prediction audit.

`summary.json` reports each method's full mean/per-compound P@20 and eligible-call recall, source eligible-gene counts, per-compound source-eligible oracle and its mean, `candidate_method`, `best_direct_method`, aligned `selected_gain`,49 `null_gains`, `permutation_p`, mobility/distinct mapping counts. Gene frequency is exact count divided once; all methods recommend the identical source-eligible universe for each aligned/null fold. Non-call is not a proven negative. Query zero-call rows remain included. Oracle uses min(20,query eligible calls)/20; recall is0 if no eligible call.

Best direct maximizes exact total recovered calls over indices0..6; ties take first. Candidate index7 is fixed. Each null reselects its best direct. Null p=(1+count(null integer candidate-minus-direct recovered totals >= aligned total))/50. Bootstrap2,000 draws seed20261031 uses lexical np.unique scaffold groups, sample group indices by default_rng.integers and divides sampled integer differences by20 times sampled compound count; report 2.5/97.5 percentile values using NumPy's default linear interpolation. Source rarity uses counts>=1 and counts<=0.1*n_train (equivalently exact count*10<=n_train).

`decision.json` contains status NO_HELD_OUT_RELEASE, information_gate_pass (positive exact aligned gain AND p<=.05), held_out_release=false, paired_scaffold_interval95, conditional_interval_above_zero, robust_benefit_established=false. Failure forces every gate false. No63-compound release, physical gain, novelty, secure-blinding, Agent or core claim is supported by arithmetic PASS.

`run.json` pins scripts/protocol/amendments/inputs and records settings, actual array shapes,49 null completion, any label/access boundary, four compute threads, child wall/CPU and status/failure. `launcher.json` enforces1800 seconds and records exit/elapsed/failure. The independent verifier may read actual output arrays only after its own code is frozen; it recomputes saved-rank arithmetic, exact frequency/ties, completeness/eligibility, coherent maps/seeds, selection/null and bootstrap/decisions. It does not refit the other methods, certify label construction/biology or reconstruct full unsaved predictions.
