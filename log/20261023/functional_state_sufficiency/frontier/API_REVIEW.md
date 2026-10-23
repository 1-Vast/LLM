# Independent review of the actual API diagonal-plus-rank-one proposal

2026-10-23, after original frontier INDEPENDENT.md was sealed. Read constructive/INDEPENDENT.md, biology/INDEPENDENT.md and biology/AUTHOR_TASK_ADDENDUM.md, then the actual api/PROPOSAL.md. Root reports one actual deepseek-flash call3174tokens; this review made0 further API/GET calls. No numerical values/protected arrays, fit or toy execution. Original independent report remains unchanged. First guessed AUTHOR_TASK_ADDENDUM at root; file absent; rg found its actual biology/ location. This is a path-inspection correction, not a source/data failure.

## Task mismatch before method comparison

The authenticated existing BeatAML component task reveals eight **different drug** AUC outcomes for one patient/context and predicts unpurchased drugs in that patient. Eight points are not eight patients for each drug. The API instead defines n_d=8 feedback patients per drug and later proposes an unseen-drug holdout. That may define a separately legitimate static adaptation question, but it is not the completed task, source-frozen protocol or an authorized same-task continuation. No real result establishes that new task's proposed restriction.

The API also incorrectly suggests ordinary covariance conditioning lacks drug-identity-dependent derivatives. For the existing map, K_QS=Sigma_QS(Sigma_SS+lambda I)^(-1) explicitly depends on query/support drug identities even while it is constant with respect to the purchased numerical values for fixed identities. Context-dependent derivatives remain a legitimate possible restriction; drug-identity dependence alone is not an uncovered degree of freedom.

## Exact diagonal block calculation, with scope

Interpret a drug-response residual correction at fixed patient x as K(x)r, with diagonal D=diag(a_d) plus rank-one part. The API's actual formula uses the unweighted mean purchased residual, so for a support set S of sizek and unpurchased query Q,

delta_y_Q = D_QS r_S + u_Q g(x) (1/k)1_S^T r_S,

where g(x)=v^T phi(x). Since Q intersection S is empty, D_QS=0 exactly. Thus the realized correction is **u_Q*g(x)*mean(r_S)**. It consumes the purchased residual vector only through one scalar mean. It cannot use diagonal self-feedback at an unpurchased query; setting an unobserved r_q from its true label would leak it.

This is an exact operation-level reduction only for the stated diagonal-plus-API-mean form, fixed identities/x and legal unpurchased query. It does not prove arbitrary low-rank methods equal a scalar gate, does not say context effects are useless, and does not forbid finite-cost value from a one-dimensional restriction. If an alternative rank-one map has a learned support-side vector w_S, its scalar is w_S^T r_S rather than an unweighted mean; that is an additional specified operation and training cost, not present in this formula.

The closest same-information competitor is therefore ordinary source-trained rank-one/covariate-conditioned residual regression or constrained low-rank conditional estimation with the exact same source data/features and query/support identities. An ordinary model may implement precisely the displayed correction with the same parameterization, training objective and tuning budget. A per-drug two-parameter fit with eight patients is not the sole competent comparator for the old eight-drug task. The source global full covariance is another important strong sentinel, although differing capacity is not an exact equivalence proof.

No theorem makes diagonal+rank1 the unique identifiable structure from eight observations. Finite observations require priors/restrictions, but many other regularized factor, kernel or contextual maps can be estimated under their own assumptions. The source evidence supplied no covariance spectrum, repeated mechanistic restriction or resource measurement establishing this particular rank choice. Lack of that evidence, not membership in low-rank regression, prevents a justified pilot promotion here.

## If the task is changed to a new drug with eight patients

An unseen drug d has no previously learned identity-table a_d or u_d. The proposal supplies no legal drug descriptor, source-to-new-drug map, distance metric or independently fixed nearest-neighbor rule. Freezing an absent u_d is undefined; assigning its true value would be an oracle. Estimating it from the same eight feedback patients is possible only as a newly specified estimation rule and must count that freedom/uncertainty. A descriptor-to-loading prior or hierarchical regression is also permissible but requires explicit source training, lawful descriptors, a qualified task and ordinary EB/direct controls with identical information.

If only that one drug's eight patient outcomes are purchased, bar(r_pool)=bar(r_d), and the displayed correction becomes bar(r_d)[a_d+u_d*g(x)]. This is a shared mean-residual amplitude times an affine covariate correction. More drugs' target outcomes cannot be smuggled into the pool. This algebra does not preclude useful shrinkage but removes the unsupported impression of independently observed cross-drug feedback at target time. Source u dispersion alone does not define a new unseen-drug subset or establish a causal explanation of gains; uncertainty of source loading assignment would need consideration.

## CellHealth and GUI corrections

API's broad phrase “CellHealth health是预测非真值” must be scoped: the357 genetic guide×line conditions have separately measured health targets, with unmatchable replicates collapsed into consensus; the drug70-channel health values are predictions, while PRISM supplies real but dose-rank-aligned separate viability. No current report grants exact matched drug exposures, percell health or dynamic transition labels. Static genetic condition-level feedback research is not inherently forbidden by absence of trajectories; it just would not itself prove transition repair or our requested new core.

The newly read GUI source does not license an unknown pharmacological consequence oracle. Its Gamma already derives post-action outcomes from supplied state and known environment rules. Known biological rules could be legal prior knowledge if independently justified, shared and charged; their effect must be compared against rule-only and same-information direct controls. There is no generic reason to require a world renderer once a wrapper already encodes the needed functional answer.

## Disposition

**NO_SUPPORTED_NEW_CORE / NO_NEW_FIT_GO** for this actual proposal. Preserve the old task, stopped CD14 rationale and stopped low-rank/consistency configurations. Do not reopen them with rank1 labels or invent a new8patient-per-drug protocol from the former8drug result. A distinct future finite-budget question remains possible if source supports an independently justified residual pattern, explicit new-drug loading mechanism and an appropriate same-information ordinary competitor. None has yet been supplied. No five-way world/agent/inheritance/joint/improved-improver contribution follows from the API's formula or admissions.
