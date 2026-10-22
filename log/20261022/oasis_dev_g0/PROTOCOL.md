# OASIS development information qualification

Registered 2026-10-22, Asia/Shanghai, before any development response/count or CNN feature value is exported. This follows independent proposal, sceptical and data reviews in `log/20261021/autonomous_rsi_round1/`. Those reviews find no presently defensible novel RSI mechanism. This experiment tests a necessary information premise, not the full objective.

## Application and admissible evidence

Application: prioritising compound-dose conditions for additional **in-vitro primary-human-hepatocyte injury assessment**. OASIS is one five-donor pooled background, measured at 44 h. MT and LDH are simultaneous surrogate readouts, not clinical DILI, treatment efficacy or independently adjudicated cell death. No time dynamics or cross-donor transfer is claimed.

Use the existing immutable v2 chemical-group reservation: dev only (641 labels / 400 chemical groups). Selection (163 labels), reserve (156 labels) and quarantine (125 labels) are not opened to optimisation. All numeric exports and fits live here. The evaluator worker may physically decode mixed Parquet pages but exports only dev compounds and exact-name DMSO controls; this is a data-flow boundary, not an OS security boundary. Read identity columns first, then predicate-scan dev/DMSO. Source files are authenticated against existing manifests. Count and morphology are paid same-time measured inputs, separately identified from a chemistry-only forecast.

Frozen inputs: `RESERVATION_v2.json`, original raw biochemical manifest and all listed assets, compiled `metadata.parquet`, duplicate-read consistency report, paired-identity table, this protocol and executing code. Duplicates are collapsed only by physical (batch,plate,normalised well), with identity and raw-value equality required. Do not select the strongest readout. All records remain in source.

## G0a: raw control and technical-repeat qualification

Read raw `mtt_lumi`, `ldh_abs` plus raw signal/background for consistency diagnostics, and measured `Metadata_Count_Cells`; no published ridge-normalised values. Exact DMSO wells on the same plate are experimental controls. For each plate require at least 8 distinct DMSO wells, finite positive MT median, robust MT coefficient of variation <=0.25, and finite positive LDH MAD. These are conservative **screen qualification thresholds**, not biological truth or an accepted universal QC standard. Report every failing plate and affected dev coverage. No positive injury control is authenticated, so no Z-prime or dynamic-range claim.

Use `log2(MT / plate DMSO median)` and `asinh((LDH - plate DMSO median)/(1.4826*DMSO MAD))` as continuous targets. Count input is `log1p(count) - median_DMSO(log1p(count))`. No clipping or outcome-based active/inactive labels. MT<=0/nonfinite or missing count is a failed acquired observation, never a negative. Row/column and batch are technical features, shared by all models. Report failed observations and fixed menu coverage explicitly.

Technical-repeat qualification uses the first two distinct plates in lexicographic order for each compound-dose, independent of values; other repeats stay recorded. Report Spearman correlation, normalised squared repeat discrepancy, and chemical-group bootstrap intervals (2000 draws, seed 20261022). Plates are not presumed independent cultures. Advance G0b only if >=90% of dev biochemical wells survive declared QC, >=100 dev chemical groups have paired observations, and both transformed endpoints have Spearman >=0.60 with 95% lower bound >0.50. Failure stops this declared configuration, without claiming all morphology or world models fail.

## G0b: measured-state information ceiling

Only after G0a passes, acquire frozen public `cpcnn_raw.parquet`, Zenodo 17067683, 48,201,019 bytes, MD5 d79b1cebc8aa3999fa993ea2500fab8d. Independent upstream review establishes well-median embeddings, preceding subsequent MAD/spherisation. This is a frozen pretrained representation; pretraining-compound nonoverlap and unsupervised training are NOT certified. Feature whitelist is non-`Metadata_` numeric columns; all metadata outcomes/clinical/target columns are excluded. Join by exact batch/plate/well and verify compound/dose equality. Read schema first; refuse a mismatch. Transformations fit in each training fold only, with test-plate DMSO controls allowed under the paid assay condition. No test-compound responses enter preprocessing.

Five deterministic folds entirely inside dev: `int(SHA256('oasis_g0_20261022|'+group_id)[:16],16) % 5`. No reroll or seed search. All doses, aliases and physical repeats inherit a chemical-group fold. Evaluate continuous out-of-fold prediction at the well level, average squared errors per compound then per chemical group, and bootstrap groups. MSE is divided by the training-fold target variance. This is a predictive information screen; no arbitrary safety threshold or practical drug-discovery utility is inferred.

Fixed comparisons (same folds and allowed controls):

1. Dose + row/column + batch.
2. Chemistry (Morgan radius2, 512 bits) + dose + technical features.
3. Measured count + dose + technical features.
4. Chemistry + measured count + dose + technical features.
5. The same inputs as 4 plus measured CNN morphology.

For each input set use ridge (alpha=10, fold-fitted imputer/scaler) and ExtraTrees (200 trees, min_samples_leaf=5, max_features=1.0, n_jobs=4, seed=20261022). No tuning; family comparisons are reported separately and against the stronger count+chemistry member, with simultaneous conservative interpretation. Feature selection/imputation/scaling fits training only. Include a train-only residualised morphology variant removing ridge-predictable count/chemistry/technical information as diagnostic, not a second chance primary. CP-CNN membership can condition the fixed information-screen population but cannot change the raw G0a menu or create independent repeat evidence.

Information gate: morphology+count+chemistry must improve normalised MSE by >=0.02 against **both** count+chemistry predictor families for **both** endpoints, with positive chemical-group bootstrap lower bounds. This 2% variance margin is an engineering information threshold, not clinical utility. Otherwise stop this representation/endpoint information claim. A positive result licenses a subsequent predicted-state experiment, not a world-model or RSI claim. Per-dose/low-cell-loss analyses are descriptive and cannot rescue a failed primary gate.

## Full-objective attribution still required

Future world-model gate must compare chemistry->state->function against tuned direct models, identical auxiliary supervision/multitask capacity, ordinary batch/online/continual refitting and simple mixtures. Shared-history model comparisons are separate from closed-loop policy comparisons. Agent gate: same model/menu, fixed design, exploit-first, active learning and equal-budget program search. Inheritance gate: common model/program start, weight and procedure inheritance separately, same-history restart/retrieval/distillation. Joint gate: world/direct x agent/conventional 2x2, strongest complete conventional system must be exceeded. RSI gate: freeze old/new improvement strategies, restart from the exact same task program/model, same history, same k proposals and evaluations; compare improvements on subsequent untouched tasks and count historical strategy-development cost. No such gate is RUN by G0.

## Resources, failures and verification

Use `D:/anaconda/envs/maestro/python.exe`. <=4 numerical threads; no GPU, no DeepSeek call needed for this gate. <=100 MB new payload, <=60 min initial execution block. Log wall/CPU/RSS and bytes; record unmetered agent/web overhead as unknown. All experimental/test code in `research/oasis_dev_g0_20261022/`; all outputs/logs/failures here. Refuse existing output overwrite. Unit tests target leakage, duplicate handling, control normalisation and fold integrity before opening values; they do not establish biology. Preserve failure outputs and amendments; no changing margins after outcomes.

Success of this block: an auditable dev-only decision on the information premise, with replayable predictions if fits run, independent adversarial review and explicit untested full-objective claims. The overall research goal remains active regardless of G0 outcome.
