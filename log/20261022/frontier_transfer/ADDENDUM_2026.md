# Independent 2026 primary-source addendum

2026-10-22. Original INDEPENDENT_PRIMARY.md and seal remain unchanged. This addendum was written without reading the new opponent's independent position. **NO_PROMOTION remains the decision**, but a genuinely current 2026 CV paper now supplies a more directly relevant calibration operation than the earlier general agent papers. Its relevance is substantive; novelty for our application remains unproved. No fitting, numerical biological data read, reserve opening or production edit occurred.

## Bounded search and primary authentication

Two actual arXiv API searches restricted first submission to2026-01-01 through2026-10-22, returned eight most-recent entries each: (i)cs.CV with "test-time" or "world model"; (ii)cs.CL with "self-improvement" or "learned optimizer". Exact URL queries/HTTP bodies/headers/hash are sources/search2026_cv_ttt.* and sources/search2026_nlp_update.*. SEARCH2026_RESULTS.json preserves all16 titles, dates, abstracts and IDs. This is a recency-bounded search, not all-year exhaustive coverage or an externally validated innovation ranking. The original task's substantive review now contains four eligible primary papers across2025–2026, plus the screened-out2024Titans; the other API entries remain discovery metadata only.

Selected for full reading: **PhysiCalWorld: In-Context Physics Calibration for World Models**, Yunhao Luo, Wentao He, Yinpei Dai, Hyelin Nam, Hongze Fu, Joyce Chai, Nima Fazeli, Jeong Joon Park. [arXiv2610.30125v1](https://arxiv.org/html/2610.30125v1), repository DOI **10.48550/arXiv.2610.30125**, first submitted **2026-10-21 17:57:59 UTC**. API published timestamp and abstract submission history agree; abstract lists onlyv1. This is genuinely first-released2026, not a2025revision. No conference acceptance or journal publication is claimed.

- Abstract HTTP200,42,338bytes,SHA256 `4e95fd626a0e2730aaeee6ebe474108477356d00a13274ee914abbf3f39ddb8b`.
- v1 full HTML HTTP200,555,438bytes,SHA256 `3574e17db233c53fffe796021f4fda0b5e3420aa3e928b35f7f9030f6dec5f2f`.
- Content read: sections3.1–3.3, experimental design/baselines, AppendixA context sampling and algorithms, environment configuration counts in AppendixB. Raw original bodies and receipts retained. No independent reproduction or code execution.

## Actual operation, including its easy-to-miss supervision contract

The model encodes an exploratory observation/action clip from an unfamiliar physical configuration into a single64-dimensional descriptor. It conditions the future predictor on that descriptor, computed once and cached across rollouts. It makes **no test-time parameter update**. End-to-end training uses only future latent prediction loss, but depends on **known groups of episodes sharing the same hidden physics configuration**. AppendixA explicitly samples the context clip from a **different episode** in that group from the prediction segment. Thus the contribution is not just a token/encoder: a paired same-configuration/different-episode training contract makes the compressed state useful for separate future behavior.

Paper equations4–6, abbreviated without altering their operation:

`c_j = g_phi(C_j)`, where `C_j={(observation_i,action_i)}` is a different episode sharing configurationj.

`z_hat_(t+1) = f_theta(z_history, action_history, c_j)`.

`min_(theta,phi) E_(j,transition~G_j,context~G_j) ||f_theta(...,g_phi(context))-E_v(next_observation)||_2^2`.

At deployment, take exploratory actions that actually produce contact/motion, compute `c*=g(C*)` once, and reuse it only while the physical configuration stays fixed. The paper explicitly warns that noncontact/nonmoving observations cannot reveal dynamics. It compares long history, raw context prefix, estimated physics with privileged training labels, and an oracle with true physics. Four evaluated environments are simulations with varied center of mass, damping, contact dissipation, and coupled mass/friction/drag. For example Push-T/Reacher/FetchSlide use150physical configurations with135training/15heldout. This diversity is very different from our five physical source sites; repeated controls cannot manufacture135independent contexts.

## Concrete transfer and its strongest classical explanation

Transfer the **paired-context training contract**, not robot trajectories or the name "physics token": for each physical-source-site/cell/platform contextj, use only paid control bundlesQ as support, then train a shared context encoder to improve prediction on disjoint noncontrol bundlesT within that same context. Every source feature and baseline is recomputed excluding the held-out physical site. All contexts at a physical site stay together for CV.

Let `b_j(d)` be source-only E/M/H predictions in the protocol's units, and each acquired observation carry separate validity masks. Define an unordered support set

`C_j={(drug,dose, b_j(q), observed_E(q), observed_M(q), observed_H(q), validity_masks(q)): q in Q}`.

Then `c_j = g_phi(C_j)` and `y_hat_j(d) = b_j(d) + f_theta(b_j(d),drug,dose,cell,platform,c_j)`. Probability heads use their own valid link or clipping; H remains conditional and masks never become a fabricated physiological label. Train only on `sum_(d in T_j) loss_valid(y_hat_j(d),y_j(d))`. At a new site, infercfrom eight actual control bundles and reuse it across the96unqueried conditions. No target value enters training or descriptor construction.

Why this targets an existing negative: RKT's unconditional source mean ranks programs identically regardless of the new context. This transfer conditions the *response function* on actual context-specific perturbation outcomes before selecting an update. For CiPA, it could represent drug-specific residual pattern beyond a common offset or per-head affine map. That is an operational hypothesis, not a claim that such a pattern exists.

Why it is not a new core yet: this is an **amortized latent-context model / conditional neural process / learned system identification**. With linear `g` and `f`, `c=A r_Q` and `r_hat_T=Bc` imply `r_hat_T=(BA)r_Q`, exactly low-rank multivariate regression. A rank bottleneck and reusable encoding can trade accuracy against computation; naming it a physiological state does not identify ion channels or make it novel. A nonlinear support encoder is ordinary conditional meta-learning. The paper's large visual-context compression savings do not imply savings over closed-form ridge on eight low-dimensional CiPA bundles. Nor does this train an improvement strategy: it is primarily an adapted predictor. C4 still needs an independently tested old/new improver controlling a fixed common-start solver.

The important limitation of the analogy is grouping: CiPA has site/cell/platform metadata, but no authenticated well/run/donor IDs. Shared context is a usable **statistical calibration grouping**, not proof all control and noncontrol observations share one invariant biological mechanism. It is legitimate to test predictive transport within that grouping; not legitimate to claim recovery of hidden physiological parameters or cell dynamics from it.

## Cheapest falsification before any descriptor network

This supersedes the original two-step planner as the **first diagnostic priority**, without changing that sealed document. It is one operation/assumption to test; it does not add a second promoted candidate. A new preregistered source-only linear baseline can ask whether control residual *patterns* predict disjoint drug residuals at all:

1. Use the already fixed primary eight controls, five physical source sites and same96drug-dose evaluation population (known missing source bundle retains its existing mask). Build cross-fitted support residual vectorr_Q with explicit missing-value indicators. Fit a rank1 reduced-rank linear map from support residuals to noncontrol residuals, using a frozen source-only shrinkage rule. One physical site is one independent unit; multiple contexts remain blocked. No target mean filling of missing responses and no new endpoint transformations.
2. Compare to the full-rank same-input ridge map, hierarchical/per-head ordinary calibration, source lookup, and the exact registered direct/refit/program-selection families. A rank1 factorization is a conventional baseline, not an implementation of the paper's transformer. Permute context assignments across physical source sites while preserving masks and score on the same population to test whether grouping carries relevant information. Merely fitting source residuals is insufficient.
3. Before any proposed neural context encoder, require held-out source improvement over the best registered ordinary calibration and full-rank same-information ridge, plus superiority to the shuffled-context null. If source result fails, stop this particular compact-pattern expansion. This does not prove all nonlinear context models impossible. With only five sites, success is descriptive and provisional. Do not respond to failure by making the token larger or inventing independent tasks from query subsets.
4. Only a separately frozen follow-on could evaluate once on existing dev6/7; retain eight actual control queries and all three original endpoint scores. Require lower combined loss on both sites and no worsening of pooled components versus each strong ordinary comparator, including the direct support-to-target ridge. A success remains a useful conditional adaptation result, not a novel mechanism or RSI. A positive nonlinear residual result would need a stated representation/compute advantage over conditional neural process and learned-update controls before a core claim.

Exact linear dimension/missingness handling/shrinkage and any practical superiority margin would need a fresh protocol before fits; they are not silently supplied by this source review. This addendum **does not authorize or execute** that experiment. The paper gives a precise reason to test whether support conditions identify transferable context, but cannot turn five-site calibration into a demonstrated higher-order learner.

No additional HTTP failure occurred. Search was explicitly bounded at16metadata records/one2026fulltext, and stopped after a directly relevant authenticated method. Raw receipts preserve all outputs. Standard-library extraction regenerated prior derivative text identically; the original independent position/seal were not altered.
