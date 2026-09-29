# Why the new estimator did not beat the frequency baseline

Historical version-2 diagnosis. See [the version-3 repair report](SCIENTIFIC_REPAIR_V3.md)
for subsequent estimator changes and a separate development calibration experiment.

This is a post-hoc diagnosis of the existing development run, not parameter fitting or model
selection. Production code, constants and the frozen external evaluation were not changed.
Reproduction: `python -m research.case_memory_integration.diagnose_shrinkage`.
Outputs: `outputs/case_memory_integration/scientific_fix/shrinkage_diagnosis.json` and
`shrinkage_diagnosis_items.jsonl`.

## What was actually compared

The run selects `FeatureArm.SCALAR` and supplies no directional user-state vector. It uses all
compatible reference episodes. On these cases state similarity is 1, historical reliability is
the default 0.5, weights are equal, and the domain-shift penalty is inactive. Both estimators
therefore use the same class × cell × contrast outcome counts. This is a smoothing comparison,
not a comparison of a learned virtual-cell model against a data-free baseline.

Rebuilding the 54-unit training store reproduces its recorded snapshot and every realised-label
probability for all 156 scored items within 1e-12, for both the candidate and baseline.

For five outcomes, the baseline is `(count_y + 0.5) / (n + 2.5)`: it already incorporates a prior.
The candidate first transforms empirical probabilities to `p^(1/1.5)` and renormalises, then
mixes that distribution with a uniform prior with weight `8 / (n + 8)`.
Actual per-branch support is 6–14 units. Thus uniform-prior weight is 36.4–57.1%, averaging
43.5% across scored items, on top of temperature flattening. Neither constant was fitted to
an independent calibration set. Temperature stays at 1.5 even at infinite support, so this
transformation need not converge to the empirical distribution as data grows.

## Fixed-operation ablations

These four settings isolate operations already present in the two estimators. They are not a
search for the best setting on these labels and do not constitute a validated replacement.

| Setting | Temperature | Prior strength | NLL | Multiclass Brier | Top-1 outcome accuracy |
|---|---:|---:|---:|---:|---:|
| Jeffreys baseline | 1.0 | 2.5 | 1.353464 | 0.696295 | 0.467949 |
| Temperature change only | 1.5 | 2.5 | 1.364134 | 0.699285 | 0.467949 |
| Prior-strength change only | 1.0 | 8.0 | 1.356338 | 0.696392 | 0.467949 |
| Full candidate | 1.5 | 8.0 | 1.372004 | 0.704323 | 0.467949 |

Both operations preserve the frequency ranking, explaining the identical top-1 accuracy. The
candidate gains no additional discrimination in this experiment. Its excess NLL is 0.018540
per item. Averaging each operation's marginal effect over the two possible operation orders
attributes +0.013168 to temperature and +0.005372 to prior strength. This is algebraic attribution
within this run, not a causal or cross-population importance estimate.

## Which outcomes account for the difference

Positive differences mean the candidate is worse; outcomes are proxy readings, not confirmed
biological mechanisms. The outcome slices overlap in independent compounds.

| Realised outcome | Items | Candidate NLL minus baseline |
|---|---:|---:|
| Resembles own annotated class | 87 | +0.202981 |
| Resembles competing class | 22 | +0.114364 |
| Unresolved | 19 | −0.224386 |
| Below the operational signal threshold | 28 | −0.464994 |

The smoothing helps atypical/low-signal outcomes but reduces probability assigned to the many
class-matching readings. In this mixture the latter cost is slightly larger. Hence the result
does not mean shrinkage is always harmful, nor that all low-support forecasts are worse.

The strongest descriptive class losses are JAK inhibitors (+0.219) and opioid agonists (+0.150).
ACE inhibitors (−0.128), opioid antagonists (−0.047) and PARP inhibitors (−0.053) improve on
their respective observed mixtures. Each class has only 2–3 held-out compounds: these are
localisations of the current error, not reliable class-specific treatment rules.

## A mismatch between the task and the outcome space

The evaluation scores processed Level-5 proxy readings. Its label generator emits exactly four
types: own match, other match, unresolved and low signal. It cannot emit QC failure. Nevertheless,
both forecasts allocate mass to a fifth outcome, `qc_failed`. The candidate allocates a mean
8.706% versus the baseline's 3.926%.

For a realised non-QC label, write its probability as `(1-q_QC) * p(label | non-QC)`. The extra
NLL attributable to reserving QC mass is exactly
`log(1-q_baseline) - log(1-q_candidate)`, averaging +0.051089. After conditioning both forecasts
on non-QC, the remaining NLL difference is −0.032549; together these yield +0.018540. This
decomposition overlaps with the smoothing attribution above and must not be added to it.

This does not license deleting QC failure from prospective experiment planning. It means the
current benchmark evaluates readings conditional on having a processed signature, whereas the
five-outcome forecaster also reserves probability for obtaining no valid experiment. Those are
different estimands. A better design separates:

- `P(QC success | assay, laboratory, context, action)`, estimated from attempted experiments,
  including failures and missingness with clearly distinguished causes;
- `P(readout | QC success, hypothesis, pre-action state, action)`, evaluated on valid readings.

For a benchmark whose generator structurally has only four readings, define and register that
conditional task before scoring. Do not remove an outcome merely because it happened to be absent
from a small held-out sample.

## What the small sample allows us to conclude

There are 156 items but only 11 independent held-out compounds. Seven compounds have higher mean
NLL under the candidate and four improve. Equal-compound mean difference is +0.027286. An
exploratory compound bootstrap gives a descriptive 95% interval of approximately [−0.086, +0.128].
It crosses zero and is fragile at this sample size. We cannot conclude population-level
inferiority, nor compare this interval with the earlier frozen external study as if it were the
same task. There is no confirmed performance improvement here.

## Next experiment, without tuning on this diagnostic

1. Register the estimand: conditional valid-readout prediction or complete attempted-experiment
   prediction. Align labels, failure data and losses for all comparators.
2. Keep the empirical-frequency model as a serious baseline. Learn any added state dependence as
   a residual over that baseline rather than assuming a more uniform prior is more scientific.
3. Use independently split calibration units (or nested grouped folds on development data) to
   fit regularisation and compare no-temperature, temperature and hierarchical shrinkage models.
   Calibrate by assay/context only where independent support permits; do not fit separate rules
   for the 2–3 compounds in each diagnostic stratum.
4. To test the agent/virtual-cell combination, give it a measured pre-action state and predict a
   different, later action's outcome. Never feed the expression signature used to calculate the
   target label back as a supposedly predictive feature. Show incremental value beyond matched
   class/assay/context frequencies before claiming that the dual core helps.
5. Freeze the resulting method and evaluate once on a new untouched population. For action
   selection, additionally require multiple legal actions and comparable utilities, costs and
   abstention policies.

The integrity fixes remain useful even if the simple baseline wins. They establish which claims
and measurements can support a forecast; they are distinct from demonstrating that a particular
probability transformation improves predictive performance.
