# Literature-guided dual-core follow-up

Search date: 2026-10-01 (Asia/Shanghai). Primary papers, publisher pages and official project sources were inspected. This is a focused methodological review, not a systematic review or a new model benchmark. The source ledger records access limits; an indexed abstract is not described as a downloaded full paper.

## Prediction quality and decision value

Ahlmann-Eltze, Huber and Anders found that the deep models in their genetic-perturbation comparisons did not beat their simple linear baselines. This supports retaining a simple comparator, rather than assuming model size establishes value. Their datasets and metrics do not establish the outcome for MAESTRO's chemical-response tasks. [Nature Methods, published 4 August 2025](https://www.nature.com/articles/s41592-025-02772-6).

Systema separates perturbation-specific prediction from systematic differences shared across treated samples and controls. A favorable expression-level score can therefore reflect background structure. Our follow-up keeps forecast quality, action changes and measured terminal utility as separate quantities. It does not replace expression metrics with a claim of causal target engagement. [Nature Biotechnology, published online 25 August 2025](https://www.nature.com/articles/s41587-025-02777-8).

Miller and colleagues present a counterpoint: models can beat uninformative baselines when metrics are checked against informative and uninformative controls. Their use of metric calibration concerns benchmark sensitivity, rather than calibrated outcome probabilities. This is a preprint. We retain both the true-forecast and context-permuted controls, and do not infer that either side of the benchmark debate proves local decision benefit. [Author preprint, 21 October 2025](https://www.biorxiv.org/content/10.1101/2025.10.20.683304v1), [author code](https://github.com/shiftbioscience/Perturbation-Models-Outperform-Baselines).

Mandi and colleagues study decision-focused prediction through rankings of feasible solutions. Wan and colleagues study sequential design using uncertainty relevant to downstream decisions. These motivate inspecting candidate rankings, chosen actions and terminal differences, rather than only average prediction error. No decision-focused training objective or directional-uncertainty algorithm from those papers is implemented here. [ICML 2022 paper](https://proceedings.mlr.press/v162/mandi22a.html), [2026 preprint](https://arxiv.org/abs/2602.05340).

## A conservative policy experiment

Baseline bootstrapping in offline reinforcement learning motivates retaining a known comparator where support is weak. SPIBB's guarantees concern its own assumptions and algorithm. The existing MAESTRO planner's `deviation_z=1.645` is an approximate forecast-standard-error threshold; it is not SPIBB and carries no certified safety or risk guarantee. [Laroche, Trichelair and Tachet des Combes, ICML 2019](https://proceedings.mlr.press/v97/laroche19a.html).

The only new policy intervention uses the existing baseline-anchor option: compare a proposed action with the next legal fixed action, keeping all other task settings fixed. Its four predeclared arms are fixed/no forecast, baseline/reference, anchored/reference and anchored/permuted. One value of the anchor threshold is tested. Test folds do not select a threshold, backend or winning combination. A negative or inconclusive result is retained and does not justify production promotion.

## World-model and evidence boundaries

Arc's official STATE project distinguishes its embedding and transition components and documents perturbation-response prediction. Those public capabilities do not prove that the installed local checkpoint supports a new compound, dose, time or context. This follow-up neither upgrades STATE nor trains a transition model. [Official STATE repository](https://github.com/ArcInstitute/state), [official release description](https://arcinstitute.org/news/virtual-cell-model-state).

Three interfaces remain distinct: production STATE predicts registered condition responses; research WorldV2 predicts readings; case-memory predicts a hypothesis-conditional outcome distribution. The anchored experiment calls the frozen ReferenceWorld. Its effects cannot be attributed to STATE or WorldV2. Hidden-result oracles remain diagnostic objects and are not deployed as policies.

The denominator experiment changes only `outcome_mode` for the same exposed LINCS2020 queries and saved reference cases. It tests whether valid-readout support is being mistaken for an attempted-experiment distribution. It cannot recover missing failed attempts or estimate unconditional QC probabilities. The decision-contract diagnostic similarly contrasts Bayesian action value with the registered evidence rule; a Bayesian posterior change does not authorize a scientific terminal decision.

## Module-to-experiment map

| Module | Question | Minimal check | Claim limit |
|---|---|---|---|
| Forecast/selector | Does conservative deviation preserve useful forecast content? | Frozen four-arm anchored replay, real versus permuted reference | Previously exposed tasks; no new-model generalization |
| Case-memory/data | Does the saved population contain the attempted-experiment denominator? | Same queries and selector, valid-readout versus attempted-experiment mode | Annotation proxies; missing attempts remain unobserved |
| Acquisition/evidence | Can Bayes value differ from legal evidence value? | Frozen real forecast-bank queries plus synthetic semantic tests | Diagnostic estimands; not a new deployed strategy |
| Runtime executor | Does the measured chain respect authority, budget and QC? | Existing engineering regressions plus new contracts | Software correctness, not biological superiority |
| STATE/WorldV2 | Are unsupported conditions and missing fitted artifacts exposed? | Preserve named refusals and artifact availability gates | No new inference, fitting or true-state gain arm |

Dataset-specific primary sources and eligibility decisions appear in [DATA_LITERATURE.md](DATA_LITERATURE.md). Results, commands and publication status appear in [README.md](README.md); precise source-access metadata appear in [literature_sources.json](literature_sources.json).
