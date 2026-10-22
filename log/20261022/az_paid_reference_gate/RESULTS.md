# Paid-reference functional-coordinate experiment: measured results

2026-10-22. Both registered co-primary gates **FAIL**. Stop this exact paid-monotherapy-coordinate, pair-specific RBF configuration as a basis for agent/RSI expansion. The experiment is a source-specific retrospective structural opportunity test, not a novel algorithm or a full framework test. The overall research goal remains ACTIVE / NOT_ACHIEVED.

## Task and execution

Predict released 72h CTG-associated inhibition for a target source-ID combination from two metadata-selected, same-plate witness matrices, using their observed monotherapy and combination responses. This is a viability/growth proxy. Recommendation selects five target dose points by predicted purchased-reference excess `Yhat - max(u,v)`; observed utility is `Y - max(u,v)`. It is neither source HSA nor mechanistic/clinical synergy.

The frozen source is AZ2024, DOI 10.1158/2159-8290.CD-23-0388, PMC11061612, member `combo_well_stats_GDSC_007_05May22.csv`. Archive SHA256: `e8cb50f6ce860fa17586a555130cb3b019f6011ed1976c0f0d3e00fb072d3259`. Input conversion uses the declared inhibitory fraction unchanged; no clipping or outcome-derived scaling.

| Role | Assigned MASTERs | Episodes | Nominal target rows | Input / target coverage |
|---|---:|---:|---:|---|
| Train | 160 | 1,030 | 48,230 | 100% / 100% |
| Validation | 64 | 430 | 20,174 | 100% / 100% |
| Test | 96 | 644 | 30,212 | 100% / 100% |
| Reserve | 413 | 2,749 | 128,947 | Numeric responses unopened |

Test has seven eligible target source-ID pairs, not every member of the twelve-pair target pool. The denominator is the frozen 644 eligible episodes, not a hypothetical pair-by-cell Cartesian product. All 96 assigned MASTERs contribute to both endpoints. Each episode resets to the same model and receives only its own two paid bundles. No query policy, episode-to-episode updating or inherited improver is executed.

All four stages completed once: inputs, 48-configuration selection plus five deduplicated final refits, sealed test-target conversion, evaluation. There were no real-fit retries. Predictions, nominal top-five actions and validation selection were hash-sealed before conversion of the 30,212 test inhibition values. No test-target attached mono/fitted fields or reserve responses were converted. See `PREDICTIONS_SEAL.json`, stage receipts and independent audits.

## Primary evidence

Each score averages dose rows within episode, episodes within MASTER, then equally across MASTERs. MAE and utility select configurations independently on validation. These are family-level policies, not one parameter setting optimized for both tasks. Uncertainty is paired 10,000-resample MASTER percentile bootstrap, seed 20261022, conditional on this source population.

| Primary endpoint | Candidate effect | Validation-selected ordinary comparator | Candidate gain, positive is better | Paired 95% interval | Gate |
|---|---:|---|---:|---|---|
| MAE, lower is better | 0.077667654 | full direct: 0.066206799 | -0.011460855 | [-0.012786525, -0.010023394] | FAIL |
| Five-action U, higher is better | 0.048597279 | without-mono direct: 0.098467776 | -0.049870497 | [-0.057802529, -0.041956936] | FAIL |

Registered requirements were at least .02 absolute and 10% relative MAE reduction, or .02 U gain and 10% baseline-regret reduction, with gain CI lower bound above zero, plus coverage. Both endpoints were required. Coverage passes; neither performance endpoint passes. The recommendation comparator's regret is 0.069511995, above the .02 insufficient-headroom cutoff. The failure cannot be attributed to absent registered decision headroom.

## All registered policies

Columns use each endpoint's separately validation-selected policy. The complete cross-endpoint scores for all 22 policy instances are in `TEST_METRICS.json` and `RESULTS_SUMMARY.json`. The source-data oracle U is 0.167979770 for every policy; it is a noisy retrospective diagnostic.

| Family | MAE of MAE-selected policy | U of U-selected policy | Regret of U-selected policy |
|---|---:|---:|---:|
| Bliss | 0.091935571 | 0.019422034 | 0.148557737 |
| Historical pair-dose | 0.156649115 | 0.080389402 | 0.087590368 |
| Effect-coordinate residual | 0.077667654 | 0.048597279 | 0.119382492 |
| Dose-coordinate residual | 0.085425407 | 0.037965054 | 0.130014717 |
| Full direct | 0.066206799 | 0.095086125 | 0.072893646 |
| Without-mono direct | 0.067368140 | 0.098467776 | 0.069511995 |
| Effect + local offset family | 0.076810636 | 0.048597279 | 0.119382492 |
| Dose + local offset family | 0.083611338 | 0.037965054 | 0.130014717 |
| Full direct + local offset family | 0.066206799 | 0.095086125 | 0.072893646 |
| Validation mixture | 0.066206799 | 0.095086125 | 0.072893646 |
| Finite-menu enumerator | 0.066206799 | 0.098467776 | 0.069511995 |

Validation selects full direct config11 for MAE and without-mono direct config1 for U. The mixture selects effect weight zero at both endpoints; the enumerator selects the same ordinary comparators. Effect selects config6 for MAE, config7 for U; dose selects config4. MAE offset policies use effect config7/eta.25, dose config4/eta.5 and direct config11/eta0. All U-offset eta values tie, and eta0 wins by the registered order.

The episode-constant offset cannot alter a fixed base model's dose ranking. Effect-offset's 0.000857018 MAE improvement over effect compares selected families with different base configurations, so it is not an isolated fixed-model offset effect. It does not rescue the primary result or demonstrate decision adaptation.

## Retained positive and uncertain observations

Effect versus the same-capacity dose-coordinate residual gains 0.007757754 MAE, CI [0.006490712, 0.009035560], and 0.010632225 U, CI [0.003491082, 0.017830112]. Effect also improves on Bliss. Measured mono-effect coordinates therefore provide a useful bias within this small residual family on this panel. They do not establish sufficiency, superiority to strong same-information prediction, molecular dynamics, a new operator or RSI.

Full direct versus without-mono direct gains 0.001161341 MAE, CI [-0.000363916, 0.002687441], while its U difference is -0.003381651, CI [-0.007283168, 0.000515178]. Both intervals cross zero. These are uncertain family-level package differences; they do not establish significant monotherapy-information benefit or harm. All registered contrasts, including negative ones, remain in `ALL_PAIRED_COMPARISONS.json`; secondary intervals are not multiplicity-adjusted discoveries.

## Prespecified diagnostics and limits

30,191/30,212 target points lie inside their pair's training effect-coordinate rectangle; only 21 lie outside. Inside-support descriptive row MAE remains worse for effect (.077937073) than full direct (.066155901). Thus simple rectangle extrapolation is not an adequate account of the primary defeat. This is row-weighted descriptive analysis, distinct from the registered macro estimand; no subgroup was tuned or removed. No active test target pair is absent from training.

The prespecified plateau flag occurs in 549 episodes and 37,367 within-episode point pairs: at least a decade difference in one raw dose with effect-coordinate maximum difference at most .02. Their pair-weighted absolute released-response gap averages .069748943, maximum .940941724. These correlated, nonidentical-coordinate pairs are neither independent replicates nor a noise floor or irreducibility theorem. They raise a sufficiency question about collapsing dose/context, but do not identify its cause or justify a post-test correction.

The chemical dictionary remains UNRESOLVED for all eleven used IDs. Query and target pools are source-ID-pair disjoint; chemical independence is NOT_ESTABLISHED, and alias leakage has not been demonstrated. Shared source normalization, stock/plate dependence and uncertain biological independence limit extrapolation. MASTER bootstrap does not remove these limits. The endpoint and .02 usefulness margins are source-unit practical proxies, not clinical efficacy or measured assay noise thresholds.

## Resources and verification

| Cost | Recorded amount |
|---|---:|
| Selection pipeline fits | 48 |
| Final unique pipeline refits | 5 |
| Total pipeline / internal solver-estimator fits | 53 / 215 |
| Total fit seconds | 4,816.128401 |
| Fit plus prediction seconds | 4,830.855507 |
| Full fit-stage elapsed seconds | 4,852.011888 (80.87 minutes) |
| Evaluation elapsed seconds | 3.708670 |
| Logical paid bundles / rows / response fields | 4,208 / 192,752 / 578,256 |
| Unique converted paid matrices / rows | 2,744 / 125,496 |
| Episode updates / new wet-lab experiments | 0 / 0 |
| Current performance-phase DeepSeek / new source GETs | 0 / 0 |

Logical two-bundle purchases are charged per episode even when source bytes are cached. Separate chemical qualification used four GETs; literature receipts/capture limitations are reported in its own finalized phase. Equal twelve-configuration search is not equal CPU. Per-arm timing review may retain a small-model compute advantage, with no throughput, wet-lab savings or equal-wall-clock superiority claim. All-in finite-menu search includes component fitting costs.

Recorded fit+prediction totals for the twelve selection configurations are effect 1.433s, dose 1.196s, full direct 3,079.554s and without-mono direct 1,247.388s. These fixed implementations show that the small residual model is cheaper than the stronger direct implementations, while also losing accuracy/utility. The same-capacity dose implementation is cheaper still. These observations do not establish a global performance/cost frontier.

Preparation/model/metric/driver synthetic checks passed before execution. Independent input audit passes; independent validation audit reproduces 228 candidate score records / 123,996 numeric fields with maximum difference zero. Corrected independent result audit02 reproduces all 22 policies, fixed actions, metrics, gates and 24 paired contrasts exactly, maximum difference zero. Its first audit FAIL is retained: the verification script misaligned identical MASTER sets by hashed versus lexical order; a three-MASTER regression and identity-alignment-only correction fixed the auditor. No model, predictions, population, experimental result or frozen method changed.

Actual supporting, skeptical and data reviews and bilateral cross-examination are linked in `DECISION.md`. No world/agent/inheritance/joint/RSI success follows from software or audit PASS.
