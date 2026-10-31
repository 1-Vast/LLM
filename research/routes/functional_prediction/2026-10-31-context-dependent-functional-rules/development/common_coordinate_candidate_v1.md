# Candidate v1: learn a common interaction coordinate in one stress, then transfer with target singles only

Frozen proposal, 2026-10-31. Proposer role; not an independent challenge. This record contains a mathematical proposal and a planned test, not an executed experiment. No response values, numerical files, HTTP resources, or author code were opened by this role. The initial reasoning is preserved separately in `initial_reasoning.md`.

## Scientific question and useful output

**Can an environmental change be predicted from measured single-perturbation responses and the untreated pair phenotype after learning one common nonlinear phenotype coordinate in another stress?**

The specific hypothesis is that a pair's interaction residual is constant in one learned coordinate, while every single perturbation may change arbitrarily with the environment. Consequently, a new environment needs single-control assays, but no pair outcomes for fitting the transfer rule. The output is the direct raw differential contrast Q for an unmeasured target pair, plus an explicitly reported input-support flag. This could help a functional-screening team prioritize combinations after paying for target singles and having an existing source screen. Its usefulness must be tested against an ordinary predictor with exactly the same information.

This is more permissive than assuming that treatment preserves all genotype rankings: measured single effects can reorder. It still makes a restrictive quantitative statement about combination responses. The contribution being investigated is the existence and useful transfer of this relation in this assay panel, **not a new fitting algorithm, proof of molecular rewiring, or general Virtual Cell efficacy**.

## Observations and the coordinate before transformation

Let g:h be an ordered guide construct; n:m denotes two non-targeting controls; r is one of the two independently transduced/passaged culture ancestries. Conditions in GI2 are UT, etoposide E, and glucose deprivation G, all at day 9. Each culture uses its authenticated common T0.

Use the already frozen pseudocount p. Do not retune p. Define

```
L[g:h,e,r] = log2((C[g:h,e,r] + p) / (C[g:h,T0,r] + p))
Y[g:h,e,r] = L[g:h,e,r] - mean_(n:m) L[n:m,e,r].
```

Thus Y is an NTC-centered, T0-referenced endpoint log-abundance change. There is no per-doubling conversion. No further environment-specific z score, native GI normalization, or fitted query quadratic is used. NTC centering removes a library-wide offset before the nonlinear transformation; a consistent count-depth convention and identical pseudocount placement remain essential. Unlike the direct raw Q, the nonlinear coordinate uses T0 and does **not** algebraically cancel T0 measurement error. That dependence is part of this proposal and must be reported.

For an increasing invertible function T, define

```
A[g,e,r] = mean_n T(Y[g:n,e,r])
B[h,e,r] = mean_n T(Y[n:h,e,r])
N[e,r]   = mean_(n:m) T(Y[n:m,e,r])
K[g:h,e,r] = T(Y[g:h,e,r]) - A[g,e,r] - B[h,e,r] + N[e,r].
```

**The proposed law is K[g:h,e,r] = K[g:h,UT,r].** It permits arbitrary baseline pair residuals K and arbitrary observed single responses. It forbids an additional pair-by-environment residual in the learned coordinate. Averaging is after transformation; replacing mean T(Y) with T(mean Y) changes the law and is not permitted silently.

For a new environment e, with no target double outcome observed,

```
z_hat = T(Y[g:h,UT,r])
        + A[g,e,r] - A[g,UT,r]
        + B[h,e,r] - B[h,UT,r]
        - N[e,r] + N[UT,r]
Y_hat[g:h,e,r] = inverse_T(z_hat).
```

Convert this prediction to the exact previously specified label, not the native processed GI target. Let D = log2((C_e+p)/(C_UT+p)) and d_N = mean_(n:m) D[n:m]. Then

```
D_hat[g:h,e,r] = Y_hat[g:h,e,r] - Y[g:h,UT,r] + d_N
Q_hat = D_hat[g:h] - mean_n D[g:n] - mean_n D[n:h] + d_N.
```

All single-control and NTC terms in that last line are observed in the target environment. The target double count is used only when scoring Q_hat. Predictions and labels are aggregated to unordered gene pairs with the same frozen guide/orientation weighting; cultures remain separately visible.

## Minimal implementable transform family

The scientific relation can be stated for a general common monotone T, but one small predeclared family should be tested first. An affordable v1 is the **ordinary Yeo–Johnson power transformation**, parameter lambda in [0,2]:

```
y >= 0:  T_lambda(y) = ((1+y)^lambda - 1)/lambda,
          with log(1+y) at lambda = 0.
y < 0:   T_lambda(y) = -((1-y)^(2-lambda) - 1)/(2-lambda),
          with -log(1-y) at lambda = 2.
```

This is strictly increasing and maps the whole real line onto the whole real line. It has an analytic inverse, T(0)=0 and derivative T'(0)=1. These anchors prevent a constant or arbitrarily collapsed latent scale. Lambda=1 is the identity. The family is intentionally restrictive: it describes one common convex or concave coordinate and cannot represent every monotone shape, such as an arbitrary inflection. Failure therefore rejects this family/transfer rule, not all global-epistasis explanations.

A fixed grid lambda = 0, 0.05, ..., 2 is sufficient for this first test. Choose only from source ETOP data, minimizing prediction error in the original Q units, not transformed residual error. The latter would reward compressing difficult regions. Keep the full source error profile. If multiple source-compatible lambdas imply materially different glucose predictions, the coordinate is not identified; that remains a valid inconclusive scientific outcome even if a single selected lambda can be scored. A richer spline is a later material revision, not an automatic repair after inspecting glucose outcomes.

The family has a mathematical inverse everywhere, but empirical support still matters. Freeze a source input range from the admitted UT/ETOP training values before glucose double labels are opened. Flag target predictions when an input or predicted endpoint lies outside that range. Report coverage and errors both for all admitted pairs and the prespecified supported subset. Do not remove difficult pairs after reading target outcomes or call extrapolation validated.

## Constructive example and a precise failure boundary

The following is an algebraic thought experiment, not measured data or a simulation. At lambda=2 and y<0, T(y)=-log(1-y).

Take neutral phenotype 0. In UT, two single phenotypes are -1 and -1 and their double phenotype is -3. Their transformed values are -log(2), -log(2), and -log(4), so K=0. In a target environment, the measured singles are -2 and -1. The invariant-coordinate law predicts the double at -5, because -log(3)-log(2)=-log(6)=T(-5). The raw differential interaction is

```
Q = [(-5)-(-3)] - [(-2)-(-1)] - [(-1)-(-1)] = -1.
```

Thus nonzero differential epistasis is predicted even though the latent pair residual is unchanged. Identity-coordinate transport would predict Q=0. Several sufficiently varied source contrasts can distinguish the nonlinear coordinate from identity and other grid members; source data with no change cannot do so.

For the boundary case, keep **all** UT observations and target single observations identical, but set the actual target double to -8. The target information available at prediction time is identical, while Q becomes -4. The additional target latent residual is -log(9)+log(6). No single-only transfer algorithm can identify this arbitrary pair-specific deviation from those inputs. An actual target pair assay, or an independently validated restriction tying that deviation to other measured pairs, is needed.

This failure could result from more than one latent trait, an environment-dependent readout, measurement bias, or an actual changed interaction. It does not identify a molecular mechanism. Conversely, a successful prediction is evidence for a useful functional relation within the tested setting, not proof that cells literally contain the inferred latent coordinate.

## Ordinary equivalents and closest-prior threats

- The law is a monotone-link model with fixed pair effects and environment-varying single effects, with no pair-by-environment term in the latent coordinate. It is a constrained generalized additive/interaction model. The transform is established statistics. These facts rule out a new architecture/algorithm claim.
- Identity T, carrying the UT interaction residual in the original phenotype scale, and the assumption of no original-scale pair-by-environment term are the **same Q=0 baseline** under this contrast. They must not be counted as three independent rivals.
- A source-trained ordinary nonlinear regression can learn the same mapping or approximate it. It must receive the same untreated pair endpoint, untreated singles, target singles, and target control information. Superiority of the constrained rule is not assumed.
- Carlson et al., PNAS 2025, DOI 10.1073/pnas.2509444122 already examines rank-based restrictions of scalar global epistasis; the coordinator reports that its two-additive-trait example can break rank invariance without direct interactions. The proposed environmental transport equation, rather than a generic rank test, is the object here; its exact prior difference still needs verification.
- The coordinator identified Otwinowski, McCandlish and Plotkin, PNAS 2018, DOI 10.1073/pnas.1804015115, *Inferring the shape of global epistasis*, but the original method was not retrieved in the present source attempt. This is a serious closest-prior threat, not evidence of novelty or a documented exact distinction.
- The coordinator reports that PLoS Computational Biology 2026, DOI 10.1371/journal.pcbi.1014000, gives additive latent traits and phenotype-specific sigmoid readouts. This prevents interpreting success or failure as proof of changed direct molecular coupling.

These prior details are coordinator-provided source findings; this proposer did not independently open the originals. No claim of absence of prior work is made.

## Decisive test possible now, before glucose pair outcomes are opened

One deterministic comparison matrix can test the v1 within four CPU threads and 1800 s. It needs no author code, weights, new sequencing data, or new dependencies. Runtime feasibility follows from a one-parameter grid and tabular regressors; it is not a measured runtime guarantee.

1. **Freeze identities, labels, support, and splits.** Preserve the existing Q/pseudocount contract and fixed eligibility rules based on identities/T0/UT, never target double outcomes. Hash-split unordered gene pairs into source development and held test groups. All guides, orientations, and both cultures for a held pair remain together. Exclude the held pairs' ETOP double outcomes from transform and rival fitting, validation, and feature construction. UT pair baselines remain legitimate inputs by the stated task.
2. **Train in one stress.** Fit/select lambda only with UT→ETOP source development pairs. A source-only internal split selects the transform and ordinary-model hyperparameters. Fit a single T shared by the two ancestries. Do not retune separate culture or target transforms. Keep the source loss profile to reveal weak identification.
3. **Freeze predictions for glucose.** Use glucose single-control assays, glucose NTCs, and the allowed UT baseline for each held pair. Glucose double outcomes are not fitting inputs, feature inputs, support-selection inputs, or tuning data. Save per-culture predictions and exact provenance before opening those labels.
4. **Use equal-information rivals.** Include Q=0 and at least a source-trained symmetric feature regression with second-order terms/Ridge and a small ordinary nonlinear tabular regressor if already available. Inputs are the allowed UT double, UT singles, target singles, and control summaries. All learn only from the same ETOP development pairs. Keep a source same-context held-pair evaluation to distinguish inability to learn even ETOP from failure of cross-context transfer. A model that accesses the held pair's ETOP double response has extra information and is inadmissible as an equal-information rival here; it may only be a separately labeled additional-assay comparison.
5. **Score the stated function, not a saturated top-100 gate.** Primary output: held-pair Q error in original units versus the strongest ordinary rival and Q=0, reported by culture and jointly, with the complete paired error distribution. Also report agreement of useful response direction, coverage, and ranking behavior at a prespecified assay budget if ranking is practically desired. Do not demand five extra hits when a rival already obtains 98/100. Report uncertainty accounting for shared genes; two cultures do not support population-level biological-replicate inference. A single random split is a bounded internal result, not external validation.

The coordinator must freeze exact hashes/fractions, eligibility thresholds, rival settings, uncertainty rule, practical loss margin, and any ranking budget before fitting. Those are executable-protocol decisions; this proposal does not pretend they have already been frozen. The test must be independently challenged and admitted before any response-value access or execution.

## Measurement-cost interpretation

Under the reported 638-guide design with 13 NTCs, the identity arithmetic is 625 targeted guides, 390625 ordered target-target constructs, and 16419 single-control/NTC-control constructs (2*625*13 + 13^2), out of 407044 total. This is prospective assay-channel accounting only, conditional on that final identity count. The hypothetical new environment pays for the single-control/NTC-control panel and not target doubles used for fitting. The historical UT/source full screen is an explicit sunk/input cost.

This retrospective masked evaluation cannot establish a proportional reduction in sequencing cost, viable pooled-library manufacture cost, or equal precision of a physically redesigned sparse library. If useful Q prediction is achieved, an independently grown restricted target library is the constructive follow-up needed to validate the savings. A cost curve against target-trained predictors must count their target double calibration outcomes and must not be presented as equal information.

## Interpretation rules

- **Positive, useful internal evidence:** one source-learned coordinate predicts held-pair glucose Q with a prespecified meaningful advantage or acceptable error at the declared zero-target-double fitting cost, reproducibly across the two available ancestries, and is not matched by the ordinary equal-information rival. This supports a restricted common-coordinate transfer capability in this selected panel. It does not establish novelty, external context generalization, drug efficacy, or molecular mechanism.
- **Law supported but no added practical capability:** the coordinate transfers but ordinary regression matches or exceeds it. A compact descriptive relation may be reported, but it is not an algorithmic advance or a demonstrated screening improvement.
- **Negative:** a source-identified coordinate works on source held pairs but fails in glucose beyond noise/uncertainty, or never predicts source pairs usefully. The v1 family/transport rule fails in the corresponding setting. Preserve which case occurred. Do not rescue it by fitting glucose and relabeling that as transfer.
- **Inconclusive:** source contrasts do not identify a transferable coordinate; target input support is inadequate; the target Q variation is below replicate/guide uncertainty; or pair/guide replication is too weak for the declared useful effect. Report the actual missing observation.

If the coordinate is source-unidentified, acquire a small set of independently grown combinations spanning the ambiguous phenotype ranges under another source stress, chosen where source-compatible coordinates disagree. If target deviations are unrestricted, acquire target pair measurements: single-only observations cannot identify them. A small target calibration set helps only under an explicit, separately falsifiable structure on those deviations. Merely reading more expression summaries would not resolve this functional observation gap.
