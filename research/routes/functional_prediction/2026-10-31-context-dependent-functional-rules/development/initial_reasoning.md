# Initial development reasoning — preserved before coordinator feedback

2026-10-31. Requested role: difficult scientific development; requested Astra/MAX, effective runtime telemetry unconfirmed. This is a proposer note, not an independent review. No HTTP request, response-value inspection, author-code execution, simulation, or experiment has occurred in this role. Read `innovation-research/SKILL.md`, the complete received `references/idea-development.md`, and this episode's `record.md`. The skill output had a short truncation near its final implementation/persistence guidance; no missing passage is used here.

## Starting decision

The most defensible available opening is to make the **coordinate used for functional interaction** an explicit scientific question. Environment-dependent numerical epistasis can arise even if the underlying genotype relation is unchanged, when treatment changes a common nonlinear map from that relation to measured growth/abundance. An interaction-score regressor, a low-rank completion, or residual smoothing cannot by itself separate these explanations.

A useful question is therefore whether a limited set of target assays can establish a restrictive, testable response relation whose violations require something beyond a common monotone readout remapping. Two possible levels must be kept separate:

1. A single latent genotype ordering, mapped monotonically to each environment's endpoint, predicts rank preservation for held-out double perturbations. This is a deliberately strong, falsifiable global-readout hypothesis, and is an ordinary global-epistasis/monotone-calibration model rather than a new method.
2. Allowing environment-specific single-perturbation strengths but an unchanged pair relation is biologically more plausible, but a sufficiently flexible link plus arbitrary pair residual may make the desired decomposition unidentifiable. The development task is to find an observable restriction or an explicit missing observation, rather than claim that fitting such a model identifies mechanisms.

The first level can be empirically falsified with the existing GI2 endpoint and its untreated baseline; it can also fail because single perturbations genuinely reorder, which would make that particular null too weak a scientific explanation. The second level is worth developing only if it yields an exact, nonvacuous constraint after allowing those single effects.

## Candidate constructive route to examine

At fixed environment, a common increasing readout of additive latent single-perturbation contributions imposes ordinal constraints on rows/columns of the double-perturbation table. These constraints survive arbitrary monotone scale changes, unlike ordinary difference-based epistasis. Environment changes may alter individual single contributions while preserving such a relation. A reversal of the effect of one perturbation between two partner backgrounds can violate this hypothesis without specifying the readout curvature.

The constructive question is whether **a sparse set of partner backgrounds can learn a transferable background ordering or substitution relation** that predicts held-out functional comparisons, with a partial-order / interval output when it cannot uniquely predict a magnitude. The rival is equal-information ordinary prediction, and the nearest mathematical equivalents include ordinal additive conjoint measurement, monotone single-index/global-epistasis models, and sign epistasis. None is currently claimed novel.

## Nonnegotiable observations and costs

The exact direct functional label stays the predeclared raw differential contrast Q, with the provided control subtraction and fixed pseudocount. Target doubles are labels only. UT/T0 baseline and observed target singles may be legitimate inputs. Every guide, orientation, and culture belonging to a held unordered gene pair must be grouped. Two ancestries are only two culture replicates; shared UT couples ETOP and glucose outcomes. The panel was selected for ATR sensitivity. These constraints preclude a claim of broad context transfer, a time/dose law, or causal identification of a biological mechanism.

The next note will choose a concrete version, derive its exact prediction and counterexample, and decide whether GI2 can falsify it within the existing one-matrix budget. No positive pilot is required to allow a well-posed falsification test.
