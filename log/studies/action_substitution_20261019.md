# Conditional pharmacological action units

This is a development assessment on the exposed Jaaks 2022 GDSC anchored combination screen. The gate plan was written
before any response column was read. Phase 2 and phase 3 were frozen before prediction. There is no independent
confirmation (BLOCKED).

- **Gate: CONDITIONALLY QUALIFIED.**
  - Same-target swap contrasts reproduce across seeding dates (interaction r 0.31).
  - The reproducible part is partner-specific, not partner x line: conditional share 0.08.
  - Efficacy swaps are mostly single-agent potency.
- **Phase 2 (unseen implementations):**
  - Interaction: NOT_BEYOND_BASELINE. The learned substitution model loses to a functional-similarity kernel by 49%.
  - Efficacy: INCONCLUSIVE. Potency matching does as well.
  - Post hoc: the same-target sibling copy is a weak reference. It is good in tight families (EGFR/HER2) and poor in
    multi-kinase ones.
- **Phase 3:**
  - One same-partner counterexample cuts interaction error by 17%, and the effect is partner-specific.
  - It moves no equivalence decision, even when every unit is probed, so agent value is bounded at zero.

Decision: NARROW. The programme as briefed is STOP. The only open question with a clear falsifier is whether measured
binding profiles (Klaeger 2017; download would need approval) separate the tight families from the loose ones. The full
record is in [`research/action_substitution_20261019`](../../research/action_substitution_20261019/REPORT.md).
