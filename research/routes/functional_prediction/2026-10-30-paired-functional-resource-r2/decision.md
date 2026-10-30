# Decision — 2026-10-30

## Scientific decision

Do not run a biological effect experiment on the current resources. The only plausible local bridge is not a matched proxy/function matrix: its transcript side is fixed at 24 h and 10,000 nM, whereas its PRISM side is a multi-dose pooled-viability AUC with no matched exposure time or independent preparation key. The row-level file also cannot be traced back to the missing SciPlex prepared source or to a saved PRISM curve-parameter source.

The paper therefore contributes a transferable **audit contract**:

1. keep directional, cell-type or module-level phenotype axes visible;
2. use a compact state that can be inspected and versioned;
3. let an external functional observation revise a frozen decision rule;
4. record failures and abstain when the observation cannot identify a safe update.

The broad operation is already covered by DrugReflector, BATCHIE and MDA. The only retained candidate is the narrower Astra R2 question: can cheap growth/viability certify a bounded domain of *post-washout durable functional loss*, while an Agent purchases a matched recovery assay only when the threshold decision could change? This is a conditional research question, not a validated mechanism or Agent advantage.

## Promotion gate

No candidate may enter `src/` or `tools/` until all of the following are available in a row-level source:

- drug structure/identity, cell or background, physical dose, exposure time, vehicle and treatment history;
- preparation/plate and independent biological replicate IDs, with technical wells nested beneath them;
- cheap proxy and an independent function endpoint collected under the same condition key;
- target engagement or genetic reference if a molecular mechanism is claimed;
- a frozen whole-drug and whole-background holdout, equal assay-cost budget and a fair comparison against direct measurement, hierarchical measurement-error, conformal/selective prediction and standard VOI.

The current episode satisfies none of the functional-pair gate, so its result is `data_unavailable`, `NO_EXPERIMENT`, and `NO_PROMOTION`.
