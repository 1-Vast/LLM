# Actual reciprocal frontier exchange

## Recursive reviewer asks frontier author
Your finite closure includes shared controls in each R_q, but sequential bundles can share the same control error e0, giving Cov(e1-e0,e2-e0)=Var(e0). Does your exact experiment condition jointly on cross-bundle noise, augment the control latent state, or assume independent bundles? Per-bundle R_q alone would double-count evidence. Separately standard GP kernel K(i,j)=z_i^T Sigma z_j over output/assay rows appears to match every contraction and dimension. Identify any differing operation/cost against that cached baseline.

Frontier author actual reply:
Agreed on both points. My executed test uses correlated two-readout errors within each bundle but independent fresh controls/noise ACROSS bundles; ordinary batch reference constructs block-diagonal R. A reused biological control is outside that exact tested scope and per-bundle R would double-count. Correct handling must augment the retained joint state with that control error or condition on full cross-bundle R, both ordinary Gaussian operations. I will retain an explicit scope correction plus tiny counterexample rather than imply a broader exactness claim. POSTCHECK_POSITION and OPERATION_RESULT conclude NO_PROMOTION: ordinary cached Gaussian/GP has identical dimension, updates and choices; no remaining special operation or measured cost advantage.

Recursive reviewer actual rejoinder:
Accepted scope correction: exactness currently covers within-bundle correlated errors and fresh independent controls across bundles. Reused controls require explicit latent augmentation or joint cross-bundle conditioning; adding the tiny counterexample makes the assay-cost premise reviewable. Cached GP equality in contractions and dimensions supports NO_PROMOTION for this specification, while preserving possible finite dense-space savings without measured runtime claims.

## Frontier reviewer asks recursive author
In your toy R=1+w/2 reveals w exactly, so cheap E[s|Z,R] equals full E[s|H]. After conditioning on all already observed information, what expensive posterior work remains either in toy or intended assay setting? Distinguish a real computation gap from deliberately withholding observed reward. No need to rescue after collapse; bias diagnostic remains useful.

Recursive author actual reply:
Agreed; no expensive posterior work remains in my toy after using all available(Z,R): REWARD_CONDITION_CHECK has12exact equalities with full credit because R reveals w. The audit posterior-call/variance tradeoff is algebraic but not a fair computational advantage here; no runtime/equal-total-cost gain claimed. One repair is pointwise identical to ordinary randomized two-level correction on48realizations. POSTCHECK_DECISION stops literal novelty/pilot, retaining partial-trace bias diagnosis. In biology exact joint posterior availability and inference cost are unqualified; missing observations are not an expensive-but-available oracle.

Frontier reviewer actual rejoinder:
Accepted. Reward-inclusive conditioning resolves designed toy without audits, and ordinary two-level equality resolves remaining literal estimator novelty. Useful result is explicit partial-trace bias condition; support retaining it without biological/Level3 promotion or cost claim. Own reused-control counterexample now ran: posterior variance3/5 correct versus1/2 mistaken, with SCOPE_CORRECTION and SHARED_CONTROL_RESULT preserving boundary.
