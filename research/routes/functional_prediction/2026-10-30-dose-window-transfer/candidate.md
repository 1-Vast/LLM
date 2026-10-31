# I-C2 initial candidate: transport of anchored curve shape

Status: proposed, not fitted. Parent: the four-direction C1 descriptive dose-switch census. Initial draft follows source-independent structural scouting, while the root developed the following mathematical restriction. This is a hypothesis about functional response structure, not an algorithmic-novelty claim.

## Scientific question and practical use

Can the shape between two measured concentrations of the same compound remain sufficiently stable across cellular backgrounds to predict compound choices at several unmeasured concentrations? The useful output is a set of multi-window rankings from fewer dose conditions, not a single-dose choice that could be measured directly more cheaply. The biological hypothesis is an approximately shared within-drug curve shape after adjusting its two target-background endpoint responses. It does not assume that all compounds share a monotone response map; such a map would preserve compound rankings and cannot explain background-specific reversals.

At use time observe vehicle and two fixed dose conditions for every compound in a predeclared library. Historical backgrounds supply full matched-concentration curves. No target treatment response at an intermediate dose is available. Background IDs alone do not encode a transferable state. Calibration is functional input from separate wells; it is not passive genomic information, an adaptive Agent or proof of drug-induced causality.

## Necessary operation

Let a and b be fixed lower/upper measured log10 concentrations. Write u=(x-a)/(b-a), A_c,d=y_c,d(a), D_c,d=y_c,d(b)-y_c,d(a), and r_c,d(x)=y_c,d(x)-A_c,d-u D_c,d. Learn q_d(x) from historical backgrounds by ridge regression through the origin, r_c,d(x) approximately D_c,d q_d(x). Predict y_target,d(x)=A_target,d+u D_target,d+D_target,d q_d(x). This anchored shape restriction carries only the relationship to test; no latent-state stack is added.

The alternative is ordinary joint curve prediction: intermediate response can depend on both endpoint levels separately, on the whole anchor panel, or on compound-specific background sensitivity not captured by D. A full covariance conditional model, smooth GP, regularized Hill curve, log-dose interpolation, source-neighbor curve and same-information tree must receive exactly the same historical responses and target anchors. Known shape-invariant regression and dose-curve methods threaten algorithmic novelty; the contribution sought here is evidence for or against a usable cross-background functional rule. A positive internal score alone is incremental.

## Predicted distinctions and failure

If the restriction is useful, anchor-scaled shape transport reduces growth-unit candidate-selection loss beyond the strongest ordinary comparator at unseen backgrounds, and the drug-specific transferred shape contributes beyond log-dose interpolation and a pooled shape. It should retain its benefit when changing background family under a prospectively frozen replay. If ordinary covariance/GP or target curves match or win, there is no demonstrated need for this restriction. Potency shifts, changing multi-target engagement or a near-zero anchor difference with strong intermediate curvature may defeat it. Two anchors do not identify four unrestricted Hill parameters; priors and all fitting information must be explicit for that rival.

This initial draft is not the execution protocol. Exact eligible doses, compound library, source-only tuning, utility, headroom, gate and test exposure must be frozen after metadata/source qualification and independently challenged. HTS031 treatment counts remain unread.
