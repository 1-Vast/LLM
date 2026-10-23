# Pre-execution development diagnostic: weekly assay-response recurrence

2026-10-23. Full goal ACTIVE / NOT_ACHIEVED. This is a real archived-assay numerical diagnostic, not a new biological experiment, novel algorithm, intervention discovery, independent confirmation or RSI test. Author narrative outcomes and fitted model parameters have been read. Raw assay bytes have been downloaded but no numeric response token has yet been converted or displayed by root. Computational prefix/query separation is not security blindness.

## Data and question

Commit b21335969c76c25a36678db5af19e2d74571abad, SJHamis/phenotype_adaptation, generate_fitnessmatrix_and_fig1/invitro_data/kavran_28day_treatments.csv. Saved original root/count_header_source.body SHA2560370b090a0a81a55542616c25008fda7b0c23f000fb7797f9ac1b966848979b1;1384bytes. Actual header sample,replicate,schedule,0,7,14,21,28; Vector Control/V600E × Continuous/Intermittent; each has six row labels. Row labels do not authenticate longitudinal wells, independent biological replicates, plates, batches or paired schedules. Actual experimental source PMC8944661 says weekly cell-number readouts use CellTiter-Glo and initial-seeded-cell normalization. We predict the released assay proxy, not direct cell counts, ATP per cell, survival probability or clinical efficacy. Fig3 dose challenges and PI assays are separate and not joined.

For each condition and time take the arithmetic mean of ALL finite observed entries, including any finite negative background-corrected signal. Normalize by that condition's day0 mean: g_t=mean(Y_t)/mean(Y_0). This is ratio of means, not mean of per-row ratios, and adds a defined dimensionless response scale rather than recovering true cell number. Different available rows across times can change cohort composition. Report every valid/missing/nonfinite/negative count; negative is a descriptive subset of valid finite entries, not an exclusion. No7000 threshold/outlier removal or author growth_rates/calibrated fitness is used. Require at least3finite values per condition/time, mean(Y0)>0, g7>0 and g14>=0 (the global exponential uses its square root). Invalid aggregate/insufficient data stops the whole comparison without epsilon, group deletion, scale change or model substitution. g14=0 and any finite query including zero or negative are allowed. Unknown nonnumeric tokens stop parsing; only empty/NA/N/A/NaN are recognized missing.

Use only g7/g14 and the already known schedule to predict day21 and day28. Every method may access the same prefix/labels, though some ignore them. No other condition's later response is used. Known500nM on weeks1/3 and off2/4 for Intermittent; Continuous stays on. The CSV has no300nM field and is not treated as a complete dose/schedule experiment grid. This is four condition-level forecasts in a single experimental system, not24independent biological trajectories/tasks.

## Four fixed ordinary predictors, no tuning

Let a=g7, b=g14 and q=b/a.

| Method | day21 | day28 |
|---|---|---|
| persistence | b | b |
| global exponential response trend | b^(3/2) | b² |
| repeat latest weekly response multiplier | bq | bq² |
| repeat first on/off cycle | Continuous: bq; Intermittent: ba | Continuous: bq²; Intermittent: b² |

These are assay-response extrapolators; no physical birth/death process is inferred. The fourth method is an ordinary schedule-conditioned recurrence. For continuous conditions it is exactly the third method; for intermittent day28 it is exactly the second method. These equalities will be checked and preclude claims of an independent new endpoint operator. They do not require future labels to establish. No shrinkage, learned latent state, updater, genotype-specific rule, editor or hyperparameter search.

## Scores, gate and stop

Primary day28 squared error on the stated response-ratio scale, secondary equal-weight average day21/day28 squared errors. Report each condition/horizon, four-condition equally weighted MSE/MAE and all predictions/truth. No pvalues, bootstrap biological uncertainty, claimed meaningful clinical margin or benefit from reduced wet costs. No genuine replication-noise practical margin is authenticated; this necessary diagnostic cannot be promoted to efficacy.

The narrow information hypothesis is whether first-cycle recurrence improves two-horizon forecasting over merely repeating the last interval. Retain it only if cycle recurrence has strictly lower two-horizon MSE than latest-interval repetition in BOTH intermittent conditions. Otherwise **STOP_THIS_FIRST_CYCLE_RECURRENCE_CONFIGURATION**, with no alternative period, shrinkage, group, metric, normalization or outlier rescue. Even if that descriptive gate passes, it establishes at most ordinary recurrence utility in this exposed panel; no new-core GO follows. Do not require impossible all-method primary superiority given exact equalities, and do not describe lower average MSE in one group as transferable improvement.

Before query conversion save/seal prefix inputs and forecasts. Then score actual query responses. Freeze protocol/code/raw file and pre-execution opposing reviews before any numeric run. Independent result review must check pairing/units, arithmetic and gate without silently adding experiments. Failure records remain append-only. Full future world/agent/inheritance/synergy/improved-improver and equal-total-cost program-search requirements remain unmet.

Pre-freeze review change: the initial draft and first critic message assumed nonnegative individual-readout eligibility. Source and critic challenged that assumption because a signal proxy can be background corrected. Before any numeric run or freeze, adopt all-finite means and report individual negative values without excluding them. Existing sealed pre-review originals are preserved; final code/protocol approval must bind this version. This is a pre-outcome estimand correction, not a result-driven rescue.
