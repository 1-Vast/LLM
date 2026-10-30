# Candidate v2 — intervention-gated target contrast

**Status: design hypothesis; not validated.**

## Core claim

For a same-target pair `(A,B)`, a virtual cell should predict the replicate-
level functional contrast from a calibrated molecular contrast, context, dose,
time and exposure; the Agent should select the next pair × context × control
observation only when it can separate a target-mediated world from a nuisance
world at equal cost, and should abstain when those worlds remain
observationally equivalent.

Let `r_c = y(A,c) - y(B,c)` and let `D = r_c1 - r_c2`. `D` is an interaction
estimand, not automatically a causal difference-in-differences. A target claim
requires an intervention or cellular-engagement readout.

## Smallest mechanism

The virtual cell is an ordinary hierarchical model with a measurement-error
term. It predicts `r_c` and its interval from absolute affinity or a fixed
occupancy transform, baseline state, dose, time and documented exposure. A
compact directional module state, inspired by PACE/CellQ, is optional and is
not part of the central novelty claim.

After a balanced initial block, the Agent chooses from a frozen menu of legal
actions: another pair, a context, a matched dose/time point, a target
perturbation or rescue arm, an exposure-matched control, or an orthogonal
functional endpoint. Its objective is expected posterior separation between:

* `H_T`: the A/B contrast contains a target-mediated occupancy component that is
  selectively reduced by target perturbation and restored by rescue; and
* `H_N`: exposure, off-target pharmacology, batch or assay mismatch explains the
  contrast and the target intervention pattern is absent.

The action cost includes matched controls, failed wells and independent assay
days. If `H_T` and `H_N` cannot be separated at the declared cost, the output is
`inconclusive`; scaling the virtual cell cannot turn an information gap into a
mechanism.

## Predictions and falsifiers

The target ordering should reproduce across held-out contexts and assay days,
attenuate under target perturbation, and return under rescue while exposure and
plate controls remain balanced. Persistence after target perturbation, removal
by exposure matching, or plate/day dependence supports `H_N` or a mixed
mechanism. Failure to separate the worlds is an identifiability result, not a
negative biological claim.

The candidate is rejected for a declared source if a simple hierarchical model
or standard VOI selector matches it at equal information and cost, if the
contrast is not reproducible, if exact target/exposure/replicate identity is
missing, or if the Agent changes the rule after seeing test outcomes. A masked
PRISM replay can test selection mechanics only; it cannot validate `H_T`.

## Mandatory rivals

Compare direct functional measurement, an ordinary hierarchical interaction
model, random and fixed-balanced selection, standard uncertainty/VOI, and a
complete-refit baseline. AdaMBind-style few-shot adaptation and PBCNet2.0-style
relative affinity are optional frozen inputs and must be removed if they do not
change the held-out decision.

## Minimum decisive study

Freeze two same-target pairs, including a near-null pair when available, at
least three measured contexts, matched dose/time and exposure, target
perturbation/rescue or qualified cellular engagement, and independent blocked
assay days. Reveal one balanced block to every selector, then let each policy
use the same small remaining budget. Evaluate target-gating on held-out days and
one held-out context, with the function endpoint and engagement endpoint kept
separate.

This differs from the paper's self-audited objective update: CDI keeps the
decision rule fixed and learns whether a molecular contrast is safe to transfer;
the action is selected to resolve a mechanism ambiguity rather than to optimize
an aggregate score.
