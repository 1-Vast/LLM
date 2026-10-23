# Review of the retained, truncated API proposal

2026-10-23. Actual receipt says deepseek-flash, finish_reason=length; only the retained complete equations and the stated linear example are reviewed. No claims are inferred after the incomplete final sentence. No root falsifier/code/results read. Independence disclosure: this role sealed its own original before peer reading, then read frontier/INDEPENDENT.md and exchanged two cost/attribution challenges **before** root's message requesting blind API review arrived. Therefore this API review is independent of root numerical work, but not blind to frontier's earlier general prior-art assessment. Frontier's API opinion was not read.

## Real restriction worth distinguishing

The API constrains adaptation to a history-derived one-dimensional path and fits its magnitude on target feedback. Functional-coordinate alignment differs from naively averaging parameter deltas under different parameterizations. This is a legitimate restricted estimator and could improve small-feedback prediction under a shared direction. It is not rejected merely because least squares is conventional. However its example compares with an uninformative minimum-norm estimator that does not use the same inherited directional evidence. A strong ordinary comparator is a source-trained rank-one output-residual basis, pulled back through the same current Jacobian if parameter changes are needed, followed by scalar ridge. This is the same stated operation in the linear setting, not a weaker unstructured refit. The construction requires authenticated independent histories; source duplicates cannot supply them by renaming.

## Exact cancellation objection to the stated sharing law

The direction equation is a fit to a **shared mean correction**, not a rank-one axis estimator. With H histories and g_bar=mean_h g_h, expanding squares gives

    sum_h ||g_h-J_X s||^2
      = sum_h ||g_h-g_bar||^2 + H ||g_bar-J_X s||^2.

Thus histories with opposite but perfectly collinear corrections cancel. Use exactly the API's six-dimensional linear world, controls spanning e1..e4 and J_X=I. Let two historical increments be g1=e5+2e6 and g2=-(e5+2e6). These satisfy a perfect shared one-dimensional axis with varying signed task amplitudes. For every epsilon>=0 the unique constrained minimizer is s=0 (the objective is 2||g1||^2+(2+epsilon)||s||^2). A target true increment g1 and allowed feedback e5+e6, y=3 then cannot be fit by any alpha because alpha*s=0. Held e6 prediction0 has squared error4. A source-trained ordinary rank-one second-moment/PCA basis recovers span(g1), and scalar target fitting with lambda_R=0 recovers the exact response2. The relevant null-control condition holds exactly. This is exact algebra only, not measured biology or a run experiment.

This does not disprove a narrower family where historical increments share a common **signed mean** bounded away from zero. The API itself only says one-dimensional stable direction and permits unrestricted scalar alpha; if it intended same-sign amplitudes, that is an additional unverified assumption. Replacing mean fitting with a principal axis would repair this particular failure but would be a new formula and a direct ordinary low-rank residual learner, not the retained formula passing. No source-qualified evidence for either assumption was provided.

## A null tangent is not a finite control invariant

J_C*s=0 cancels only the first-order response. For one nonlinear control f_C(theta)=theta_1+theta_2^2 at theta0=(0,0), s=(0,1) satisfies J_C*s=0, but f_C(theta0+alpha*s)=alpha^2. For four controls use f_Ci(theta)=theta_i+theta_5^2 for i1..4 and s=e5+2e6: all first derivatives vanish, while all finite controls shift by alpha^2. Thus its written finite nonlinear path does not preserve measured controls unless the curve is projected back to the exact control level set or finite steps are separately checked. No statement that control-preserving adaptation is impossible follows. The API's optional functional-coordinate nonlinear refitting sentence does not explicitly enforce this level set, so it cannot be silently credited as solving the defect.

## Reparameterization claim is incomplete

Functional targets g_h avoid averaging incomparable historical parameter deltas, but epsilon||s||^2 depends on the current parameter chart. Under nonorthogonal theta transformations the Euclidean penalty and therefore predicted ridge pullback generally change. It can affect directional predictions when J_X is ill-conditioned or incomplete. With epsilon>0 uniqueness is justified; calling epsilon 'only numerical stability' does not make its exact influence disappear. For epsilon0, injectivity on the constrained subspace is required for uniqueness. A physically invariant functional regularizer or explicit metric is another new choice to test against the same metric-aware ordinary refit, not something supplied by the current equation.

## Decisions

REVISE / NO_CORE_GO for this incomplete API candidate. It does give a concrete inherited mean-direction restriction, but its own one-axis language is insufficient to guarantee a usable direction; finite control preservation is not established; same-information inherited low-rank residual/refit controls are missing. The final unfinished reparameterization example and any absent RSI protocol remain unassessed. The reported toy has no agent, later-task inheritance test, improved-improver or world-versus-static-direct separation. Do not reopen fixed CXCL99-to15 to rescue it. Any next formula must first declare signed-mean versus axis sharing and lawful independent histories, then freeze exact functional controls and total-cost comparisons before new labels.

No biological values, model fits, API calls, HTTP, GPU or executed toy experiment by this reviewer. Exact expansions and counterexamples are analytical evidence only. No root arithmetic was read. Existing global provenance qualification remains unchanged.
