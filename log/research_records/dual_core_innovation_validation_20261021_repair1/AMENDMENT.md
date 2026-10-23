# Historical study corrections

This amendment corrects interpretation and implementation claims in the adjacent
`dual_core_innovation_validation_20261021` package. That package remains unchanged.
The calculations below read its already saved, exposed derived CSVs; they do not
load raw release outcomes, retrain, or run new model predictions. The source hashes,
full subgroup metrics, and recomputation settings are in `historical_corrections.json`.
No result from the ongoing repair replay is used here.

The original `STOP_THIS_TASK_CONFIGURATION` remains justified for its stored
implementation and comparisons. The evidence does not establish a general failure
of virtual-cell world models or self-improving agents, and it did not test a working
agent-query / world-model-update / refreshed-prediction loop.

## Molecular feedback changed probabilities

The original claim that molecular updating cannot reach the phenotype prediction
is incorrect. The predicted trajectory enters `head_x` directly. Updating shared
trajectory parameters can change predictions while phenotype-head weights remain
fixed. Recomputed Experiment Q means over seven lineages are:

| Measure | No update | Molecular feedback | Interpretation |
|---|---:|---:|---|
| Brier | 0.271238 | 0.269510 | Probabilities changed |
| Precision@5 | 0.514286 | 0.514286 | No change in this decision metric |
| AUROC | 0.564683 | 0.564683 | No change in this ranking metric |

The Brier reduction is 0.001728, with the original lineage-bootstrap convention
giving 95% interval [-0.002979, 0.007066]. This is inconclusive. Precision@5 and AUROC
are unchanged in every background. Those aggregate metrics cannot prove that the
complete drug ranking is identical. The support remains three drugs; the target
pool is the other eleven drugs. There is no established useful decision gain.

## The molecular table mixed single drugs and pairs

The original table aggregates 1,776 time-specific records: 1,293 single-drug records
from 431 cell-by-drug conditions and 483 pair records from 161 cell-by-pair conditions.
Each condition contributes three times. These are not 1,776 independent biological
replicates. The original prose attributed the mixed aggregate to single drugs.

The corrected 24-hour values are arithmetic means of the saved condition-level
metrics, matching the original aggregation convention. They are not pooled-protein
MSE or correlation estimates.

| Model / subset | Records at 24h | Change correlation | MSE | Baseline-copy MSE | Target-protein MSE | Baseline-copy target MSE |
|---|---:|---:|---:|---:|---:|---:|
| M1 / single drugs | 431 | 0.160641 | 0.009668 | 0.004194 | 0.008973 | 0.005149 |
| M1 / pairs | 161 | 0.406102 | 0.005758 | 0.003318 | 0.004701 | 0.010729 |
| M3 / single drugs | 431 | 0.139346 | 0.004369 | 0.004194 | 0.810635 | 0.005149 |
| M3 / pairs | 161 | 0.203998 | 0.003325 | 0.003318 | 0.869674 | 0.010729 |

For single drugs at 24 hours, C2/C3 change correlations are 0.117917/0.097733.
M1 has a larger descriptive change correlation, but worse MSE than baseline copying;
its single-drug target-protein MSE is also worse than baseline copying. Thus the
original mixed-table statement that M1 essentially equals persistence on target
proteins does not describe the single-drug subset. M3 retains a large target-protein
error. Missing target metrics are omitted from means; per-metric denominators and
all three time points are explicit in the JSON. Pair molecular measurements do not
authenticate the published pair functional endpoint.

## Architecture and initialization corrections

- `run_models.py` constructs PPODE before `train()` seeds torch. Consequently the
  stored s0/s1 labels do not identify reproducible initialization seeds. Stored
  checkpoints and their metrics remain historical observations. The repair seeds
  before construction and tests reproducibility within a fixed software/hardware
  configuration; cross-platform identity is not promised.
- `GroupNorm(1, hidden)` operates on `[batch, hidden, proteins]`. Its shared mean and
  variance couple proteins globally. The model has no explicit protein-specific
  interaction graph, but “no cross-protein interaction” is too strong.
- For a fixed background and parameter state, the 23 zero-target drugs share their
  predicted trajectory because their target-flag inputs are identical. Shared
  parameter updates can change these trajectories. Fingerprints can still separate
  their functional probabilities. “No drug-specific trajectory” does not mean
  “immune to feedback.”
- M1 versus M2 changes the trajectory pathway, phenotype-head architecture and
  capacity, and auxiliary molecular loss. It cannot isolate a causal benefit or
  harm of the trajectory pathway.

The last point also has an empirical limit: M1/M2 precision@5 is 0.514286/0.685714
for stored run s0, but 0.542857/0.514286 for s1. The direction reverses. M1 remains
below B1 (0.742857) in both runs. The stored-seed uncertainty and confounded ablation
must accompany any statement about why M1 underperformed.

## Decision and inference limits

The original final pool contains the same 14 drugs in each of seven lineages.
The 98 cell-drug predictions are not 98 independent experimental backgrounds.
The lineage bootstrap preserves resampling multiplicity correctly, but seven
independent lineages give limited resolution and no replication-noise estimate.

P1 is -0.228571 precision@5 and P4 is -1.142857 confirmed hits. Because the original
A0 simply confirms its static top five, P4 is exactly five times P1. They are
different reporting scales of the same selection behavior, not independent evidence
for two separate failures.

Oracle headroom over B1 is 0.142857 precision@5 and 0.714286 confirmed hits. Both
exceed their respective margins of 0.09 and 0.40. Opportunity is limited; absent
headroom is not an established explanation of this failure. The hindsight oracle
also does not establish an attainable or noise-free gain.

The repair protocol trains only on the original five development lineages and
selects programs on the original selection lineages. Original final models trained
on development plus selection. Training-defined pools and numeric outputs must be
reported separately. A difference between original and repaired scores is not a
paired estimate of the software repair's causal effect. All old final outcomes
have already been exposed; reuse is development/regression evidence only.

## Agent, isolation, and audit limits

Original Experiment E exposes fixed `W`, `prior`, and `nn` dictionaries. Functional
and molecular queries reveal observations and debit costs, but do not invoke Q
fine-tuning or replace W predictions. Q, R, and E are evaluated separately. Thus
original E does not establish or reject adaptive world-model feedback inside the
agent's experiment loop.

The original evaluator passes the live `Episode` object to candidate code and later
calls its public `result` method. The AST guard permits replacing that method; a
synthetic candidate was able to return a fabricated score. Full NumPy also exposes
file-access functions. No stored candidate was observed exploiting this. The
original “outside evaluator / sandbox” claim is nevertheless too strong. A separate
process with a Python syntax guard is not OS-level filesystem or network isolation.

A1 retains only strict winners; rejected candidates cannot become parents. It is
a greedy chain, not an archive with exploratory branches. A2's three prompt hashes
are identical, and all three generated program hashes are identical. Equal logical
requests do not establish matched resources: A1 used 6,549 tokens, A2 10,233, and
their evaluation-task schedules differ. No accepted program means inheritance and
directional mutual learning remain untested. The original proposer-evidence path
also calls the runner without checking its error, unlike the later selection check;
prompt hashes alone do not reconstruct the affected historical evidence.

The protocol explicitly records that lineage label prevalence was seen before the
partition. “Before any labelled analysis” overstates outcome blindness. The 43
verification checks establish their specified internal consistency properties;
they do not prove that final outcomes were read or evaluated exactly once. A
write-once stage claim is not an independent execution audit.

These corrections justify repairing the implementation and its claims. They do
not convert the historical negative into a biological success or establish that
the repaired method will outperform conventional updating and confirmation.
