# Post-run protocol clarification

This file does not replace or rewrite the frozen `PROTOCOL.md`. The frozen protocol hash remains `a73b24c4c4e9b5633d82322243fb741761003a9db7ff1486a17d676279baac1e`.

The arm list in the frozen document repeats numbers after arm 5 and resumes at 7. The canonical arm identity is the string name in the `METHODS` list and `FREEZE.json`; the intended human-readable order is:

1. `raw_k5`
2. `raw_k20`
3. `chemistry_k20`
4. `global_residual_diagnostic`
5. `gat_d5_k20`
6. `pca_residual_k{2,5,10,20,50,100}`
7. `random_residual_k{2,5,10,20,50,100}`
8. `ridge_raw`
9. `full_flat_residual_k20`
10. `gat_permuted_null`

The numbering ambiguity is a traceability defect, not a post-run arm change. No arm, metric, fold or result was added after the freeze. The independent verifier used the string identities and confirmed the frozen hash.
