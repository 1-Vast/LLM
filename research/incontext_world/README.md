# In-context virtual-cell world model: report

**File summary**
- **Path:** `research/incontext_world/README.md`
- **Purpose:** block 6 of 2026-09-27. The owner asked to optimise MAESTRO's virtual-cell world model using six recent
  virtual-cell papers (PRESAGE, State, Tahoe-x1, Stack, SCALE, MultiFlow), with the implementation left to
  judgement. This package takes the ideas that fit MAESTRO's data and its world model's job, forecasting what a
  measurement will show before it is bought. It implements them and tests them against the current model on
  held-out compounds.
- **Core points:**
  - **Observation model (E-WM1: PASS on both datasets).** A learned in-context transition predicts a compound's
    profile at an unmeasured condition from its measured one. It roughly doubles the direction accuracy of every
    Tahoe-x1 baseline. On compound identity (State's discrimination score) it does **not** beat the simple prompt
    baselines.
  - **Planning world model (E-WM2: PASS on both datasets as registered, robust on SciPlex3 only).** The same
    transition, used as an attention kernel over references, lowers the reading forecasts' log loss. On SciPlex3
    the gain is -0.018 nats per item. On L1000 it is -0.008, carried by tier T alone and not robust to item
    weighting. A shuffled-prompt control gains nothing.
  - **Nothing is connected to the planner, the agent or `src/`.** The spec says a pass makes the model a candidate
    for a selected-step calibration test, which is the next step, not a result here.
- **Interfaces / data:** `transition.py`, `metrics.py`, `world.py`, `e_wm1.py`, `e_wm2.py`, `spec.json`,
  `test_incontext_world.py`; outputs under `outputs/incontext_world_20260927/`
- **Depends on:**
  - `research/belief_planning/world.py` (the current world model);
  - `research/protocol_v2/` (v2.1 tasks, sealed public view, executor);
  - `research/dynamic_world_model/common.py` (validator geometry).

Spend: $0 in provider calls, 0 wells, no downloads. Nothing was committed and no production default changed.

## 1. What the papers contribute, and what was taken

MAESTRO's world model is not a generative model of single cells. It forecasts P(validator reading | hypothesis,
measurement, what has already been measured) for a planner, on pseudobulk shift profiles from SciPlex3 (2,473 genes)
and L1000 (978 genes). The ideas were chosen for that job.

| Paper | Idea | Where it is used here | Status |
|---|---|---|---|
| **Stack** (Dong et al. 2026) | In-context learning: measured cells of a condition act as a prompt at inference, and a prompt must be available at query time | The compound's own measured shifts at conditions already bought in the episode condition the forecast at the next one (`world.py`). The target's own shift is never a prompt (tested) | Implemented, evaluated |
| **State** (Adduri et al. 2025) | A learned state transition across contexts; Cell-Eval metrics | `transition.ridge_st`, a linear analogue of State's transition: ridge regression from the principal components of prompt shifts to target shifts. Pearson delta and discrimination (`metrics.py`) | Implemented, evaluated |
| **Tahoe-x1** (Gandhi et al. 2025) | Null, global-mean, context-mean and perturbation-mean delta baselines; split-half noise ceiling | All four baselines plus Stack's additive PerturbMean are E-WM1's comparators; split-half ceiling on SciPlex3 | Implemented, evaluated |
| **PRESAGE** (Littman et al. 2025) | Attention over knowledge sources; source choice matters more than architecture; two-stage evaluation (effect size, then direction centred at the mean response); phenocopy | Two knowledge sources (prompt similarity, virtual-cell transfer similarity) weighted by empirically fitted global weights; source chosen per fold by likelihood; centred cosine as the primary metric; effect AUROC; phenocopy@5 | Implemented, evaluated |
| **SCALE** (Chen et al. 2026) | Endpoint supervision; biologically meaningful, protocol-aligned evaluation | Evaluation only: one fixed protocol, identical items for every arm, and the validator's own geometry as the functional readout. No latent flow model was built: SCALE itself reports that flow formulations can exploit shortcuts, and MAESTRO's decisions use pseudobulk readings | Evaluation principle only |
| **MultiFlow** (Wang et al. 2026) | Coupled multi-layer flows conditioned on a control-derived state | Not implemented: no paired second modality exists in these data. The analogue used is conditioning on another *condition* of the same compound | Not implemented |

The Codex session of 13:25-19:36 added a single-cell conditional population flow backend
(`src/virtual_cell/population_flow.py`, CellFlow/State-style, one A549 24 h 1 µM pilot, not wired into any path).
That is a different level from this package, which works on pseudobulk profiles across conditions and on the
planning forecast. Nothing here depends on it or changes it.

## 2. What changed

| Item | Where | Default behaviour | Tests |
|---|---|---|---|
| Specification: arms, metrics, gates and seeds, written before any code of the package | `spec.json` | - | - |
| Observation model: 5 baselines, `scaled` and `ridge_st` transitions with closed-form leave-one-out selection | `transition.py` | new | `test_incontext_world.py` |
| Cell-Eval / Tahoe-x1 / PRESAGE metrics in the validator's projected geometry | `metrics.py` | new | same |
| `InContextWorld`: the reference world plus one in-context layer with prompt and transfer sources, fitted by leave-one-unit-out empirical Bayes; carries model version, fitted layer and effective support in every forecast | `world.py` | new; kappa 0 equals the reference world exactly | same (6 tests) |
| E-WM1 and E-WM2 runners, analyses and post-hoc diagnostics | `e_wm1.py`, `e_wm2.py` | new | via outputs |

The in-context layer, for hypothesis h and reference r of h:

    a_r = kappa x (label-history weight of r) x prod over prompts p of exp(tau x (sim_r(p) - 1))
    forecast = (sum_r a_r x reading_r + reference forecast) / (sum_r a_r + 1)

`sim` is either the projected cosine at the prompt condition between the compound's measured shift and r's
(`prompt`), or the projected cosine at the target between the `ridge_st` prediction and r's measured shift
(`transfer`). kappa, tau and the source are chosen per fold by the predictive likelihood of training references' own
readings. Every reference of the target's unit is left out, and only non-eliminating prompt readings are used.

## 3. E-WM1: profile prediction from an in-context prompt

Items: a held-out compound, a prompt condition and a different target condition, both QC-passed. SciPlex3 has 16
conditions (153 units with a detected target); L1000 has 8 conditions (109 units). Transitions are fitted on
other-fold compounds only. Values are unit means on items whose target was detected, with 95% unit-bootstrap
intervals (10,000 draws).

| Metric | Dataset | null | global mean | context mean | prompt (pert. mean) | additive | **ridge_st** | ridge_st - best baseline |
|---|---|---|---|---|---|---|---|---|
| Centred cosine (**primary**) | SciPlex3 | 0.078 | 0.090 | 0 | 0.199 | 0.156 | **0.372** | +0.173 [+0.149, +0.197] |
| | L1000 | -0.170 | -0.074 | 0 | 0.166 | 0.187 | **0.361** | +0.174 [+0.149, +0.198] |
| Pearson delta | SciPlex3 | 0 | 0.221 | 0.319 | 0.149 | 0.248 | **0.432** | +0.113 [+0.099, +0.128] |
| | L1000 | 0 | 0.313 | 0.371 | 0.239 | 0.282 | **0.502** | +0.131 [+0.109, +0.152] |
| Phenocopy@5 | SciPlex3 | 0.043 | 0.095 | 0.078 | 0.245 | 0.245 | **0.333** | +0.088 [+0.068, +0.107] |
| | L1000 | 0.002 | 0.044 | 0.035 | 0.261 | 0.267 | **0.355** | +0.088 [+0.060, +0.117] |
| Discrimination (State) | SciPlex3 | -0.290 | -0.284 | -0.257 | 0.018 | **0.072** | 0.013 | -0.059 [-0.099, -0.016] vs additive |
| | L1000 | -0.707 | -0.713 | -0.718 | -0.278 | **-0.260** | -0.463 | -0.202 [-0.254, -0.156] vs additive |
| Effect AUROC (all items) | SciPlex3 | 0.5 | 0.446 | 0.656 | 0.749 | 0.774 | **0.839** | - |
| | L1000 | 0.5 | 0.437 | 0.547 | 0.810 | 0.811 | **0.856** | - |

- **Gate: PASS on both datasets.** `ridge_st` exceeds each of the five baselines on the primary metric, and every
  paired interval is above 0. It also has the lowest MSE on both datasets.
- **It holds when the prompt itself was undetected.** Centred cosine is 0.303 against 0.146 for the prompt baseline
  on SciPlex3, and 0.317 against 0.145 for additive on L1000. The transition carries information from the context
  pair, not only from the prompt.
- **Compound identity.** State's discrimination score (Manhattan distance) is no better than the prompt on
  SciPlex3, and worse than additive on both datasets. Ridge shrinkage recovers the shared, direction-level
  response and loses compound-specific magnitude. **A prediction from this model is not a substitute for measuring
  that compound.**
- **Noise ceiling (SciPlex3).**
  - Tahoe-x1's split-half Pearson is 0.403. `ridge_st` exceeds it (0.432), because that ceiling compares two
    half-samples.
  - The Spearman-Brown-corrected ceiling for a perfect predictor against the full measurement is 0.723 (post hoc).
    `ridge_st` reaches 59% of it.
  - L1000 has no split halves, so its ceiling is unknown.

## 4. E-WM2: reading forecasts of the in-context world model

All 20 protocol-v2.1 development tasks (SciPlex3 A and B, L1000 LT and T, folds 0-4) were run through the sealed
public view: 6,601 episodes (the same as E-DATA1) and 634,809 items. 0 view or audit problems. Each item is a design-
planned target, with a history of none (H0), one prompt (H1) or two prompts (H2). The observed label comes from the
registered executor. Scores use the true hypothesis's branch.

| | SciPlex3 H1 | SciPlex3 H2 | L1000 H1 | L1000 H2 |
|---|---|---|---|---|
| Units / items | 98 / 122,219 | 97 / 87,152 | 221 / 202,002 | 204 / 174,132 |
| NLL, pooled / class / **reference (current)** | 0.923 / 0.839 / **0.826** | 0.911 / 0.825 / **0.812** | 0.316 / 0.231 / **0.234** | 0.224 / 0.173 / **0.172** |
| NLL, **incontext** | **0.807** | **0.793** | **0.226** | 0.172 |
| incontext - reference (unit mean, **primary on H1**) | **-0.018 [-0.036, -0.002]** | -0.019 [-0.032, -0.007] | **-0.008 [-0.017, -0.0004]** | +0.001 [-0.000, +0.002] |
| incontext - reference (item-weighted, post hoc) | -0.005 [-0.016, +0.006] | -0.012 [-0.023, -0.002] | +0.001 [-0.001, +0.004] | +0.001 [-0.000, +0.002] |
| permuted - reference (control) | +0.004 [-0.009, +0.016] | - | +0.000 [-0.003, +0.003] | - |
| Brier, incontext - reference | -0.021 [-0.032, -0.010] | - | -0.008 [-0.016, -0.001] | - |
| Wrong elimination observed / forecast: reference, incontext | 1.04, 1.04 | 1.17, 1.20 | 0.79, 0.78 | 0.78, 0.78 |

- **Gate: PASS on both datasets, as registered.** On H1 the unit-mean NLL difference has its whole interval below
  0. H0 forecasts are identical to the reference world's (maximum difference 0.0). The shuffled-prompt control is
  not better than the reference, so the gain comes from the compound's own measurements.
- **SciPlex3: a modest gain, robust.**
  - About 2% lower log loss. The Brier gain agrees, and the gain persists on two-prompt histories under both
    weightings.
  - The **transfer** source (the virtual-cell observation model) was chosen in 9 of 10 folds. It carries all of the
    gain: transfer-only gives -0.018; prompt-only gives -0.001 [-0.009, +0.007].
- **L1000: not robust.**
  - The unit-mean pass comes from tier T (-0.024 [-0.048, -0.002]). LT is -0.000 [-0.006, +0.005], and two of its
    five folds fitted kappa = 0.
  - Item-weighted, the model is not better, and it adds nothing on H2.
  - On L1000 the current reference world is itself no better than the class-only model on H1 (+0.003
    [-0.009, +0.017]).
- **Where the gain sits (post hoc).** It is concentrated in units with few non-eliminating readings: SciPlex3 -0.050
  [-0.094, -0.011], L1000 -0.031 [-0.056, -0.010]. Units with many such readings (mostly inactive compounds, whose
  prompts are noise) gain nothing. On L1000, the middle band is slightly worse (+0.006 [+0.000, +0.016]).
- **Calibration is unchanged.** On these unselected items the in-context forecasts are as calibrated as the
  reference's. E-CAL1's problem (forecasts 2x too low on the steps a planner *selects*) is untouched by this block
  and remains the next test.

## 5. What failed or is limited

- **Discrimination.** The observation model predicts the shared, direction-level response well. It does not
  identify individual compounds better than their own prompt.
- **L1000 E-WM2.** It passes only through tier T and unit weighting.
- **Sharpening, not calibration.** The planning gain is a sharpening of forecasts that were already roughly
  calibrated on unselected items. It says nothing about the planner's selected actions.
- **Development data only.** Every result is on development folds of data exposed in earlier blocks. This is a
  development screen, not an external or confirmatory test.
- **Not attempted:**
  - MultiFlow-style multi-modal coupling (no second modality exists);
  - single-cell flow models (Codex's pilot exists separately);
  - pretrained foundation embeddings (State SE, Tahoe-x1, Stack weights). They are not local, their licence and
    pretraining overlap with SciPlex3/L1000 would need checking, and PRESAGE's own ablations suggest source choice
    matters more than scale.

## 6. What remains untestable here, and the next step

- **Selected-step calibration.** Run E-CAL1 on the actions a planner using `InContextWorld` selects. The
  protocol-v2.1 runner would need to hand each arm the shifts it has bought, as opt-in public-step fields. It is the
  condition the spec sets before any planner use.
- **Decision value.** Planner superiority on these data is stopped by E-DATA1's registered failure rule: the task
  is eligible but underpowered, with 105 of 314 and 205 of 714 units.
- **Promotion.** No production path uses the reference world. Promoting `ridge_st` as a ladder rung in
  `src/virtual_cell/` (serving a prediction only when a same-compound prompt exists) is an owner decision. It needs
  its own contract tests.

## 7. Reproduction

From the repository root (Python 3.14, research dependencies installed):

```bash
python -m pytest research/incontext_world -q -p no:cacheprovider
python -m research.incontext_world.e_wm1 run            # write-once; refuses if the item files exist
python -m research.incontext_world.e_wm1 analyse
python -m research.incontext_world.e_wm1 ceiling        # post hoc
python -m research.incontext_world.e_wm2 run --workers 4
python -m research.incontext_world.e_wm2 analyse
python -m research.incontext_world.e_wm2 robustness     # post hoc
```

Outputs are in `outputs/incontext_world_20260927/`:
- `e_wm1/{sciplex3,l1000}_items*.csv.gz`, `analysis.json`, `ceiling_posthoc.json`;
- `e_wm2/items/<dataset>_<tier>_<fold>.{parquet,json}`, `analysis.json`, `robustness_posthoc.json`.

Each E-WM2 task record holds the fitted reference (s, k, e) and in-context (source, kappa, tau, likelihood tables)
hyperparameters. Runtime was about 13 minutes for E-WM2 with 4 workers (about 1.2 GB each) and 9 minutes for E-WM1.

## 8. Deviations and disclosures

- **Folds.**
  - `spec.json` says "folds 1-5"; the registered folds are numbered 0-4. The first runs used 1-5, so fold 5 was
    empty and fold 0 was never held out.
  - Fold 0 was then run with identical code and added as separate records (`*_fold0.csv.gz`; the `*_0` task
    files). The fold-5 records (empty) and the first files were kept.
  - The E-WM1 figures quoted mid-session came from folds 1-4. The E-WM2 metrics were not read before fold 0 was
    added. Both gates give the same verdict either way.
- **E-WM2 histories use only non-eliminating prompts.** The spec said "each other planned condition". An
  eliminating reading ends a real episode, and the reference world has no likelihood for it, so those states cannot
  occur for a planner. QC-failed prompts condition nothing and were not used as histories.
- **Post hoc.** Everything marked post hoc (item-weighted means, per-tier splits, unit-size bands, the
  Spearman-Brown ceiling) was written after the registered analyses were read and is not part of either gate.
- **`written_at`.** The value in `spec.json` was corrected after the runs from an estimate (19:53) to the file time
  (19:51:43). No rule changed.
- **The effect-AUROC bootstrap** resamples units and weights items by unit multiplicity. It is reported, not gated.
- **Leakage checks.**
  - Transitions and references come from the public view's training tables. A test asserts that no transition
    contains a held-out compound.
  - The empirical-Bayes fit leaves out each reference's whole unit. The ridge leave-one-out prediction still
    includes a reference's unit-mates in the principal components; this affects only the kernel fit, never a
    held-out score.
