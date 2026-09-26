# Sequence audit protocol (Phase 3 intervention, Phase 4 independent validation)

Frozen before any L1000 validator reading, forecast or policy decision was computed. The hashes
of this file, `protocol.json`, the implementation and the prepared L1000 data are in
`freeze.json`. `protocol.json` is the machine-readable version; where the two differ,
`protocol.json` governs.

## What had been seen

- SciPlex3: everything. That covers blocks 2 and 3, the follow-up's recorded sequences, the Phase 1
  stopping attribution (`diagnose.py`) and the Phase 2 matched replay (`replay.py`). Any SciPlex3
  result for the revised policy is therefore diagnosis-informed and exploratory.
- L1000, metadata only:
  - condition counts;
  - vehicle-null thresholds;
  - detection counts per line and time;
  - class pools and sizes;
  - batch shares;
  - the cache-versus-official signature-strength concordance (`lincs_prepare.py`,
    `feasibility.json`).
- L1000, not seen: any validator calibration, any held-out reading, any forecast, any policy
  outcome.

## The one intervention: `two_step_fallback`

The base is the follow-up's contingent two-step planner, unchanged. It would defer before the
first measurement, or stop after a neutral or QC-failed result, in three kinds of case. The
revision classifies each stop by the Phase 1 hierarchy.

1. **Uninformed.** The cause is one of:
   - no references for any action;
   - no paired references for any continuation;
   - thin support: the continuation is positive on raw reference frequencies but not after the
     planner's Jeffreys shrinkage.

   The revision then takes the fixed early-to-late sequence's next legal action.
2. **Informed.** The references it has forecast no correct elimination, or a wrong-elimination
   risk above the 2:1 break-even. The revision stops, exactly as before, with the named reason.
3. **Illegal or unaffordable.** It stops.

Forecasts only choose actions. Evidence changes only when a real executed result is read through
the registered `OutcomeRule`s. No unsupported branch receives a probability. Production defaults
are unchanged.

Why this rule, from Phase 1:
- Stops and deferrals, not measurement choice, carried about 85% of the fixed sequence's tier-A
  advantage.
- Uninformed stops were 89 of 106 tier-A stops after a neutral first reading, and 610 of 767 in
  tier B.

## Rules every arm shares (`policies.run_matched`)

- **Measurements:** at most two, each a distinct action.
- **Time order:** exposure time is never earlier than any executed action, failed assays included.
- **QC, primary rule `continue`:** a failed assay is charged, updates nothing, and every arm
  chooses again. The two-step arms then value one remaining measurement from unconditioned
  forecasts.
- **QC, sensitivity rule `stop`:** every arm stops after a QC failure. This is SciPlex3 only,
  because L1000 episode compounds are measured at every menu condition.
- **Stops:** after any elimination, after two measurements, when no legal action remains, or when
  the arm names a stop.
- **Utility:** +1 correct, -2 wrong or exhausted, 0 undetermined or deferred.

## Independent validation on L1000 (primary)

**Data**
- Source: local GSE92742 metadata and the derived `subset48` condition cache.
- Profile: the cache's condition mean over 978 measured landmark genes.
- QC: at least two wells on two plates, finite values, and a matched official signature with at
  least two replicates.

**Detection:** Broad's `distil_cc_q75`, the median over matched signatures, must reach
max(0.10, q99). The q99 is taken from DMSO signatures at the same line and time.

**Labels:** exact Repurposing Hub joins, single-mechanism records only.

**Class pool:** per tier, classes with at least 6 InChIKey identity groups measured at every tier
condition. At least 2 of those groups must be detected at some tier condition.

**Folds:** 5. A fold unit is a connected component of compounds that share an identity block or a
Bemis-Murcko scaffold.

**Tiers**

| Tier | Role | Menu | Fixed sequence | Pool |
|---|---|---|---|---|
| LT | primary | A549, MCF7, PC3, VCAP × 6 h, 24 h at 10 µM | A549 6 h, then A549 24 h | 21 classes, 344 compounds, 6,880 episodes |
| T | secondary | A549 × 6 h, 24 h | as LT | 15 classes, 218 compounds, 3,052 episodes |

**Validator and gate**
- The SciPlex3 validator is used unchanged, calibrated per fold on training compounds with its
  grid and a 5% maximum wrong-elimination rate.
- A tier is evaluated only if at least 3 of its 5 folds can eliminate. Otherwise that tier gives
  no verdict.

**Cost and budget:** assay days are exposure days + 5; the budget is 12 days, which never binds
for two measurements.

**Arms:** `production`, `da`, `da_unconditioned`, `fixed`, `one_step_utility`, `two_step`,
`two_step_permuted`, `two_step_fallback`.

**Endpoints**
- Primary: utility and wrong-elimination rate, for `two_step_fallback − two_step` and
  `two_step_fallback − fixed`.
- Secondary:
  - correct, undetermined and deferral rates;
  - measurements, assay days and fallbacks;
  - the other contrasts;
  - forecast signal (`two_step − two_step_permuted`);
  - step-1 forecast calibration (ECE, Brier);
  - contrast-support strata (≤3, 4–7, ≥8 training compounds at the fixed first condition);
  - a plate diagnostic: whether the nearest winning template shares the held-out batch.

**Inference**
- Intervals are 95% percentile intervals from 2,000 paired cluster-bootstrap draws, seed 20260926.
- The unit is the held-out compound's fold component.
- Sensitivity: identity group, and batch cohort with a leave-one-batch-out range.

## Decision (tier LT; tolerance for wrong elimination 0.02)

Apply the rules in order; the first that matches decides.

1. **INCONCLUSIVE** if the LT gate fails.
2. **REJECT** if the fallback-minus-two-step utility interval lies wholly below 0, or its
   wrong-elimination interval lies wholly above +0.02.
3. **PROMOTE** only if all of the following hold. PROMOTE means eligible for an implementation
   review as the default two-measurement sequencing rule; nothing is switched automatically.
   - Fallback minus two-step: utility lower bound > 0, and wrong-elimination upper bound ≤ 0.02.
   - Fallback minus fixed: utility lower bound > 0, and wrong-elimination upper bound ≤ 0.02.
   - In tier T, both utility point estimates are ≥ 0.
4. **SHADOW** if the fallback-minus-two-step utility lower bound is > 0 and its wrong-elimination
   upper bound is ≤ 0.02. SHADOW keeps the rule opt-in and logged.
5. **INCONCLUSIVE** otherwise.

None of the following counts as evidence for promotion: profile cosine, forecast calibration on
its own, or any SciPlex3 result.
