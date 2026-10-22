# Independent saved-result and attribution review

2026-10-22. **Accept `STOP_CURRENT_ARENA_GRAMMAR` as the registered limited conclusion.** No raw response arrays loaded and no model fit rerun. Independently reassembled saved per-row scores and checked trajectories using `research/cardiac_mechanism_review_20261022/audit_rkt_saved_results.py`; exact audit is `RKT_SAVED_RESULT_AUDIT.json`.

Bound FREEZE SHA256: `2eb391ced09857c715ccd74f70059447fdb27ce2968d92d20f9340f1262bdda2`.

Bound screen SHA256: `5127ec8db6423052fa5ed6e00e0c1457b3a3da35539c0422ad3651ca534e7b86`.

All12 frozen file hashes match. The frozen screen contains all three pre-execution repairs from the independent review: only11non-S0 entries are permuted; `oracle>S0` is explicit in continuation, and S0 joins the ordinary envelope; the deployment seal states full-array decoding occurred before terminal-slice scoring. `PREFREEZE_REVIEW.md` and the frozen code document these fixes; no post-result algorithm change is needed.

All168 episode/seed/arm trajectories contain exactly four distinct non-S0 **program IDs**, common S0=4, and deployment among S0/requested IDs. Repeated candidate feedback is identical across arms. Saved sealed deployments are unchanged when terminal scores are attached. Total672 nominal candidate requests are consistent with the protocol. Independently rebuilt all104program/mixture episode scores as mean-within-compound followed by equal mean over32compounds and matched saved results within1e-12. Terminal trajectory scores match the deployed program's reconstructed score.

Reconstructed new−old = **−0.00006221793545108101**. Old is the strongest ordinary pooled-mean comparator, including S0, so this also fails the registered new-vs-ordinary contrast. The explicit positive-oracle condition is present but does not rescue the failed contrasts. The decision follows protocol. Oracle−S0 remains positive; the conclusion is not absence of finite-grammar headroom. `RESULT_DECISION.md` attributes this correctly.

Programs0/1/2 are intercept-only and differ only in lambda. Because the sole intercept is unpenalized, their fitted functions are identical; all eight saved terminal scores match exactly. Hence12nominal candidates contain redundant functions, and four distinct IDs do not guarantee four functionally distinct evaluations. Every arm uses this same frozen menu, so this does not invalidate the registered diagnostic, but it limits its opportunity interpretation. Do not deduplicate/reallocate budget and rerun after seeing this result. Stop this exact fixed grammar/learner/partition, not learned program improvement in general.

Limits of this audit: saved candidate trajectories omit the S0 development score, so the candidate-versus-S0 choice cannot be fully reconstructed from those saved scores alone; common-start fitting and S0 comparison were verified in the bound code. This is a minor logging limit, not an observed selection error. Historical cross-fold route dependence and full NPZ decode exposure remain material and disclosed. No significance, unseen-compound transfer, biological function, world/agent/joint contribution, or novel RSI result follows.
