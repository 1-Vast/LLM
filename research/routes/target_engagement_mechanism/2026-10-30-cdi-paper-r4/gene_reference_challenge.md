# Gene/reference independent challenge — 2026-10-30

## Scope and decision

This is an independent review of the frozen **intervention-gated target
contrast** design and the newly supplied FLT3 genetic-reference and
engagement-overlap evidence.  I read the candidate, data-gate, overlap-search,
gene-reference JSONs, and the r3 `fresh_challenge.md`.  The two gene-reference
JSONs are stored under `raw/resource_metadata/`; they are not at the r4
top-level path named in the task.  I also re-read the saved r3 pair table and
the scripts that generated it.  No code or existing research file was changed.

The new evidence does not close the intervention gate.  It supports, at most,
a weak and unit-sensitive **genetic concordance/discordance** statement between
the PRISM response contrast and a later DepMap Chronos reference.  It does not
support target engagement, target-mediated drug response, causality, an Agent
advantage, or a cross-dataset validation claim.  The candidate should be
downgraded to a pre-registered diagnostic pilot; the full virtual-cell/Agent
stack should remain parked until a matched intervention or cellular-engagement
study exists.

## Source-supported observations

The following are observations recorded in the supplied files.  They are kept
separate from the critique below.

* `candidate_v2.md` defines `r_c = y(A,c) - y(B,c)` and
  `D = r(c1) - r(c2)`, explicitly calling `D` an interaction estimand rather
  than an automatic causal difference-in-differences.  It defines `H_T` as a
  target-mediated world and `H_N` as an exposure/off-target/batch world, with
  abstention when the two worlds cannot be separated at equal cost.
* `raw/resource_metadata/gene_reference_check.json` reports an exact
  `DepMap_ID` join of 409,428 pair-cell-dose rows, 395 cells, 153 pairs and
  eight nominal doses.  The source is the FLT3 row from official DepMap 26Q1
  GeneEffect/Chronos data; the response table is PRISM 19Q4/MTS010.  After the
  unit correction, the saved unique-cell calculation is `rho = 0.0642158465`
  for `delta_pKd` against the high-dependency-minus-low-dependency contrast,
  the pair-level mean-over-dose value is `rho = 0.1115705249`, and the
  repeated-row direct value is `rho = -0.0055816829`.  The earlier
  row-weighted `rho = 0.0716625155` remains in this challenge and the failure
  log as a rejected sensitivity result.
* `gene_reference_independent_check.json` independently reproduces the join
  counts and confirms that its calculation matches the canonical JSON.  It is
  an arithmetic and identity check, not a biological validation.
* Chronos gene effect is signed so that more-negative values indicate stronger
  inferred genetic dependency.  The gene-reference JSON itself limits the
  interpretation to genetic concordance/discordance and records the
  PRISM-19Q4 versus GeneEffect-26Q1 version boundary.
* The r3 FLT3 table contains one row per `pair_id × cell_id × nominal dose`
  after treatment columns were averaged within molecule × dose × cell.  The
  `n_cols_a`/`n_cols_b` fields count treatment columns and are not biological
  replicate counts.  The saved pilot has 153 pairs, 469 cells before the new
  exact GeneEffect join, 21 lineages, and a fixed MTS010 screen.  The r3
  expression-tertile contrast was `rho = 0.060124109743004896`.
* `target_engagement_overlap_search.md` reports CellEKT (MV4-11/HEK293T,
  midostaurin-FLT3 probe competition, 0.1–10,000 nM, one-hour exposure,
  biological duplicates) and a live-cell kinase-probe study (Jurkat,
  dasatinib/dinaciclib, 60–90 minutes, mostly duplicates) as the closest
  2025–2026 resources.  Neither has a verified PRISM/DepMap/GDSC row-level
  cell barcode, drug registry crosswalk, matched dose/time, and orthogonal
  viability row.  PRIDE raw files and large supplements were not downloaded.
* `data_gate.md` therefore remains `data_unavailable`: no inspected source has
  the same cell × drug × dose × exposure time × cellular engagement × genetic
  reference × orthogonal function × independent preparation contract.

These observations establish resource identity and arithmetic, not a
mechanistic result.

## Statistical-unit challenge

### The frozen tertile is not frozen at the stated unit

The comment in `run_gene_reference_check.py` says that dependency tertiles are
frozen on the joined cell set, but the code applies `qcut` to the merged table
of 409,428 repeated pair × cell × dose rows.  Cells with more complete pair or
dose coverage therefore receive more weight when the cut points and labels are
formed.  A genetic context label should be assigned once to each of the 395
unique joined cells, before response rows are merged.

I re-read the saved pair table and the extracted FLT3 row and performed this
unit correction without changing any source file:

| Calculation | Effective rows | Spearman rho | Reading |
|---|---:|---:|---|
| Original row-weighted tertile; pair × dose `D` | 1,109 | 0.0716625155 | Sensitivity/failure record; repeated cells and doses weight the result |
| **Unique-cell tertile; pair × dose `D`** | **1,109** | **0.0642158465** | Corrected primary descriptive check |
| Unique-cell tertile; `D` averaged across doses within pair | 153 | 0.1115705249 | Pair-level cross-dose unit sensitivity |
| Gene effect versus repeated-row `delta_y` | 409,428 | -0.0055816829 | Cell and pair coverage weighted repeatedly |
| Gene effect versus cell-level mean `delta_y` | 395 | -0.0705723949 | Unique-cell unit sensitivity |

The row-weighted and unique-cell cut points were approximately `-0.02904` and
`0.06465`, versus `-0.03067` and `0.07019` when calculated on unique cells.
Six of the 395 cells changed tertile.  This does not reverse the qualitative
weakness of the signal, but it means that `0.0716625` must not be presented as
the sole frozen primary result.  The corrected value to carry forward is
`0.0642158465`.

### Pair × dose rows are not independent evidence for a pair contrast

`delta_pKd` is constant within a pair, while each pair contributes up to eight
dose-specific `D` rows.  The 1,109-row Spearman calculation consequently
repeats the same molecular covariate and gives incomplete pairs/doses unequal
weight.  It is a useful descriptive plot, but its row count is not an
independent sample size and it has no cluster-aware uncertainty estimate.

After assigning the tertile at the unique-cell level and averaging `D` over
available doses within pair, the coefficient is `0.1115705249` over 153 pairs.
The dose-specific coefficients are unstable rather than showing one fixed
interaction pattern:

```text
dose (uM):   0.00061   0.00244   0.00977   0.0391   0.15625   0.625   2.5   10
rho:           0.230    -0.285     0.617    -0.079     0.094    0.128 -0.234 0.165
```

This spread is compatible with ordinary dose-response curvature, saturation,
missingness and noise.  It is not a stable target-gated context effect.  A
future analysis should choose in advance between a pair-level dose-averaged
estimand and a replicate-level mixed model with dose as a fixed or random
factor; it should not pool pair × dose rows and treat them as independent.

The direct gene-effect association is also unit-sensitive: the reported
repeated-row coefficient is `-0.0055816829`, whereas averaging `delta_y` within
unique cell gives `-0.0705723949`.  Neither coefficient is a causal estimate,
but the difference shows why a repeated-row “near zero” result cannot be used
as a strong negative mechanistic test.

The earlier r3 expression tertile was likewise formed in a repeated cell × drug
× dose table.  In this particular saved table its cell assignments happened to
match a unique-cell split, but the implementation should still be corrected and
the eligible cell set and cut points recorded before any outcome aggregation.

## What the genetic reference can and cannot say

### Permitted conclusion

The corrected check is a weak, descriptive concordance/discordance test between
a molecular pair feature, a PRISM functional response contrast, and a later
DepMap genetic-dependency reference.  The result is small (`rho = 0.0642` at
the pair × dose descriptive unit and `rho = 0.1116` after pair-level
cross-dose aggregation), unstable across dose, and sensitive to the weighting
unit.  The appropriate statement is therefore “no strong or stable genetic
concordance was demonstrated in this cross-release slice.”

### Claims it does not support

Chronos is an inferred dependency score from genetic perturbation.  It is not a
measurement of intracellular drug occupancy, inhibitor exposure, target
engagement, or rescue of the drug response.  An exact `DepMap_ID` proves model
identity in the two releases; it does not prove that PRISM and DepMap used the
same passage, culture state, preparation, assay day or molecular profile.

The PRISM MTS010 treatment-column token `120H` is retained as a raw label, but
the local audit does not expose a structured preparation/exposure field.  The
GeneEffect row carries no drug dose or exposure time.  Thus neither the weak
positive interaction nor the near-zero direct correlation identifies a path
from affinity to cellular function.

A weak positive rho does not support target mediation: it can arise from
baseline growth state, lineage, missingness, pair composition, generic FLT3
dependency, or off-target pharmacology.  A near-zero rho does not falsify
target mediation either: saturation, exposure variation, nonlinear occupancy,
measurement noise, or the wrong context moderator can hide it.  Both results
remain at the genetic concordance/discordance level until a target intervention
or qualified cellular-engagement measurement is linked to the same functional
rows.

## Engagement overlap and cross-dataset mapping challenge

The two near-overlap papers are useful assay templates, but the fields do not
form a validation join.

* **CellEKT:** MV4-11 and HEK293T, midostaurin-FLT3 probe competition,
  0.1–10,000 nM and one-hour inhibitor exposure.  A nominal cell name is not a
  shared DepMap barcode; a compound name is not a verified PRISM registry or
  structure identity; probe-competition pIC50 is not PRISM DMSO-relative
  viability.  Biological duplicates do not supply a shared plate/preparation
  identity with the 19Q4 response table.
* **Live-cell kinase-probe assay:** Jurkat E6.1, dasatinib/dinaciclib,
  60–90-minute exposure and mostly duplicate measurements.  It contains no
  reported FLT3 result and no public same-row PRISM/DepMap/GDSC crosswalk.  It
  demonstrates that a cellular engagement assay can be run, not that a target
  engagement value has been measured for the PRISM rows.

The different endpoints, schedules, units, cell engineering/passage status and
replicate identities must remain explicit.  “MV4-11 appears in both sources”
or “dasatinib appears in both sources” is only a candidate overlap.  Until a
machine-readable structure × cell barcode × concentration × exposure ×
replicate × engagement row is joined to the same function preparation, these
resources must not be described as external validation or a retrospective
target-mediated CDI result.

## Minimal novelty and downgrade decision

The candidate's individual components have ordinary formulations:

| Candidate element | Smallest ordinary formulation | Residual distinction worth testing |
|---|---|---|
| `D = [y(A,c1)-y(B,c1)]-[y(A,c2)-y(B,c2)]` | Two-way factorial interaction; causal DiD only with an explicit intervention/design | A pre-registered intervention and measurement contract that makes attribution testable |
| Virtual cell with measurement error and occupancy | Hierarchical/conditional response regression with a noisy covariate | Proven held-out attribution or calibration under matched engagement |
| Agent chooses the next pair/context/control | Bayesian optimal design, active learning or standard model-discrimination VOI | Equal-cost separation of named target and nuisance worlds with a hard abstention rule |
| Abstain when worlds are equivalent | Standard decision-theoretic no-action/indifference rule | A reproducible biological data contract and stop rule |

This combination may be a useful study design, but it is not yet a new
architecture or a demonstrated Agent capability.  A masked PRISM replay can
test leakage, grouping and equal-cost bookkeeping; it cannot validate `H_T`.
The candidate should therefore be **downgraded to a conditional
intervention-gated diagnostic hypothesis**.  Do not add CellQ, MAML, PBCNet2.0
or a larger virtual-cell representation to rescue the missing information.
Park or stop the CDI line if the matched engagement/perturbation resource is
not feasible.  Proceed only with one small, pre-registered falsification pilot
and its schema/data-acquisition gate.

## Planned tests

### Unit and provenance audit (required before interpreting a new rho)

1. Freeze the eligible unique-cell set and assign dependency/expression strata
   once per cell.  Record cut points, cell counts, and release hashes before
   joining any response rows.
2. Preserve replicate-level response rows and assay identifiers.  Do not use
   `n_cols_a`/`n_cols_b` as biological replicate counts; technical columns may
   be averaged only after their role is documented.
3. Report a pre-registered pair-level or mixed-effects estimand with dose and
   cell clustering.  Use cluster bootstrap or an equivalent hierarchical
   uncertainty calculation; no unclustered row p-value should be used as
   evidence.
4. Keep PRISM 19Q4/MTS010, DepMap 26Q1 and any new engagement release as
   separate versions.  A registry join is an identity check, not an assay-time
   alignment.

This audit can change the descriptive coefficient, as shown above, but cannot
by itself reopen the mechanism gate.

### One decision-changing minimum check

Run one small, pre-registered **matched intervention pilot** before building a
larger model.  Freeze two same-target pairs when available (one expected
near-null pair is required if the source contains one), three cell contexts
spanning predeclared unique-cell dependency strata, and the action menu before
any test outcome is revealed.  For each selected pair/context, include:

* A and B at matched, documented dose and exposure time, with intracellular
  exposure measurement or an exposure-matched control;
* parental, target-perturbed and rescue arms, or a qualified cellular-engagement
  assay that directly tests the same target in the same preparation;
* one separate orthogonal function/engagement endpoint, independent blocked
  assay days, randomized plate allocation and replicate-level raw outcomes;
* the same initial balanced block, candidate pool and cost for the
  intervention-gated selector, ordinary hierarchical regression plus standard
  VOI, and random/fixed-balanced selectors.

After the balanced block, permit each selector the same remaining small budget
to choose a legal next observation.  Evaluate the pre-registered attenuation
and rescue pattern on a held-out context and assay day, and evaluate
cost-adjusted separation/abstention against the ordinary baselines.  The pilot
changes the decision only if a target-sensitive contrast is reproducible under
the intervention while exposure and assay controls remain balanced, and the
selector adds model separation beyond the equal-cost baselines.

### Explicit falsifiers

The **mechanism falsifier** is: on a held-out context and independent assay day,
with exposure and plate/day balance verified, the A/B contrast does not
attenuate under target perturbation and does not return under rescue within an
equivalence margin fixed from replicate variance before unblinding.  Persistence
after exposure matching is an additional direct nuisance-world result.  Either
pattern falsifies the target-mediated interpretation for that source and keeps
the output at “inconclusive” or `H_N`.

The **algorithm falsifier** is: at the same candidate pool, information budget
and cost, ordinary hierarchical regression plus standard VOI achieves the same
held-out model separation and abstention calibration as the intervention-gated
selector within the pre-registered margin.  In that case CDI has no demonstrated
incremental Agent contribution and should be stopped as an algorithmic line.

## Final independent verdict

Carry forward the unique-cell correction (`rho = 0.0642158465`) and retain the
original row-weighted `rho = 0.0716625155` only as a sensitivity/failure record.
The pair-level cross-dose sensitivity is `rho = 0.1115705249`, and the
cell-level direct response sensitivity is `rho = -0.0705723949`; dose-specific
effects are unstable.  These numbers do not establish or refute target
mediation.  The engagement search supplies assay templates rather than a
verified crosswalk.  Conditional GO is justified for the one matched
intervention pilot; full-stack implementation, mechanistic claims and Agent
savings claims remain NO-GO.

