# Measurement choice for mechanism discrimination: pre-registered protocol

Frozen 2026-09-26 before any 72 h response, any decision episode and any transition-model
output was computed. Parameters are in [`protocol.json`](protocol.json); the SHA-256 of both files
is recorded in `log/20260926/0926/run-notes.md` at the freeze. A later change is a new version
with its time recorded, never an edit in place.

## 1. Question and the bottleneck it tests

MAESTRO's agent chooses the next measurement from a registered menu. Today the virtual cell
enters that choice only as a tie-break: among equally covering, equally cheap actions, the one
with the largest predicted response magnitude wins (`agent.orchestrator`, `maestro.selection`).
Magnitude is the wrong quantity for the decision the agent faces. A strong response at 10 uM can
be the generic stress response every drug class shares, and a missing response at 24 h cannot
tell "the perturbation failed" from "this mechanism acts later" or "this mechanism is inert in
this line". What the agent needs from a world model is, for each candidate measurement, how
differently the competing hypotheses predict it will come out, with honest uncertainty and an
explicit refusal where the model has no basis. The survey in
`reference/report/Drug_Synergy_Prediction_Landscape_and_Future_Directions.docx` (section 6) states
the same target: compare competing explanations and choose a discriminating assay, against a
fixed policy under the same budget.

## 2. Data, and what it can and cannot support

SciPlex3 (Srivatsan et al., Science 2020) as released on Figshare, read through the
identity-marker gate of `virtual_cell.identity_markers` (label offset +1):

- **24 h**: A549, K562 and MCF7; 188 compounds; 10 nM to 10 uM; two replicate wells per
  condition on different plates; two vehicle wells on every plate.
- **72 h**: A549 only; 47 compounds and vehicle; the same four doses; plates 49 to 52, with
  their own vehicle wells. Every 72 h condition also exists at 24 h.
- **Pairing**: sci-RNA-seq3 destroys the cells it reads. No cell is observed twice, and the 24 h
  and 72 h cells come from different wells on different plates. What is paired is the
  *condition* (compound, dose, line). The state modelled here is therefore the population state of
  a well, and a 24 h to 72 h transition is a statement about matched populations, not a cell
  trajectory. A shift is always taken against the vehicle of the same line, time and replicate,
  which removes the plate effect shared by a plate's wells.
- **Modalities**: RNA is measured. Pathway activity and cell-cycle position are inferred from RNA.
  Cells recovered per well is a measured proxy for population size. Protein, morphology,
  chromatin and metabolism are missing and are declared missing in every state record.
- **Time**: two time points in one line. Nothing here licenses extrapolation beyond 72 h,
  interpolation between 24 h and 72 h, or any time claim for K562 or MCF7; those queries are
  refused by name.

## 3. The deterministic validator (final authority on belief)

A measurement of a held-out compound is read only by a fixed rule, in this order:

1. **Quality**: both replicate wells present with at least 20 cells, and matched vehicles. A
   failure is `quality_failed`, is charged, and updates nothing.
2. **Detection**: the rep1 and rep2 shift vectors must agree beyond vehicle noise. The null is
   built from vehicle wells treated as pseudo-conditions, so it contains well and plate variance,
   the flaw of the 2026-09-26 within-vehicle null. Threshold: the larger of 0.10 and the null's
   0.99 quantile for that line and time.
3. **Absence**: an undetected response eliminates nothing. It is recorded at
   intervention-implementation scope: a failed perturbation and a mechanism inert at that
   condition predict the same observation.
4. **Mechanism evidence**: with the shared drug-response axis at that condition projected out
   (the lesson of the zero arm on 2026-09-26), the profile is compared with each class's
   *detected* training compounds at the same line, time and dose. B is eliminated in favour of A
   only if A's best match clears a floor and beats B's by a margin, or if B has no template while
   at least two B compounds were measured there and none responded.
5. **Calibration of floor and margin**: per fold, on training compounds only, by inner
   leave-one-compound-out. The chosen point maximises correct eliminations at a
   wrong-elimination rate of at most 0.05.

The validator emits a `MeasurementResult`, whose interpretation fields and metrics pass through
the repository's `InterpretationTable` and `EvidenceState`. No prediction, card or model answer
can reach it as evidence.

## 4. Episodes, menu, cost and budget

For each held-out compound of a pool class, and each other pool class, the hypotheses are "acts
by its own class" and "acts by the other class", presented in random order. The menu is every
condition of the tier (tier B: 3 lines x 4 doses at 24 h; tier A: A549 x 4 doses x 24 h and 72 h).
Each measurement costs 2 treated wells, 4 vehicle wells the first time a line and time is used, and
exposure plus 5 readout days (24 h: 6 days; 72 h: 8 days). The budget is two measurements, taken
one at a time with replanning; an episode stops at its first elimination. Correct elimination
scores +1, none 0, and a wrong elimination -2, so declining to decide beats guessing.

## 5. Policies

`random`, `fixed`, `cost_only` (repository selector, no world model), `magnitude` (the current
virtual-cell tie-break), `separation` (scenario cards from measured references, selected by the
repository's `select_expected_coverage`), `separation_permuted` (the same with class labels
permuted: the non-biological control), `dyn_ref` (step 2 conditioned on the step-1 outcome through
reference compounds that behaved the same way), `dyn_model` (step 2 forecast from the compound's
own step-1 profile by the best transition arm), and `oracle`.

Language-model arms act on one seeded contrast per compound in each tier, under identical
evidence, menu and budget: DeepSeek without cards, with cards, and with permuted-label cards;
Jev with and without cards, eight repeats per choice, a stable modal choice executed and otherwise
the separation action. Every chosen action is read by the same validator.

## 6. Transition models (secondary to the decision)

Before any larger latent model: `zero`, persistence or identity, scaled persistence, ridge on a
20-component training-only PCA latent, gene-space ridge, a one-hidden-layer MLP on the latent,
and measured-profile retrieval, for time (24 h to 72 h), dose (neighbouring doses of the same
compound) and context (another line) transfer. A larger model is added only if these leave a
specific failure a larger model could address. Multi-branch outcome prediction (each reference
compound a branch) is tested against a single class mean with replicate noise and against a
pooled, non-mechanistic marginal.

## 7. Primary analyses and promotion

P1 to P5 and the promotion rules are in `protocol.json`. Intervals are 95% compound-bootstrap
(2,000 draws, seed 20260926). A component that does not meet its rule is recorded as a negative
result and is not synchronised into `src/` or `tools/`.

## 8. What was already seen before this freeze

From the 2026-09-26 biological-depth run: 24 h out-of-fold predictions of every arm, the
literature-anchor audit at 24 h, the agent probe, and the calibration showing that only response
magnitude beats the average-response baseline. Structural counts of the 72 h cohort (compounds,
wells, cells per well, plates) were read to design this protocol. No 72 h expression value, no
detection statistic, no validator outcome and no transition-model output had been computed.
Background knowledge used in the design: HDAC inhibitors respond strongly by 24 h, and DNA and
histone methyltransferase inhibitors act over cell divisions.
