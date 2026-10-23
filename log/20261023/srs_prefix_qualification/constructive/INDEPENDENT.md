# Independent qualification: prefix feedback from real SRS trajectories

2026-10-23. Cache-only design review of grounded_feedback_renewal/root/longitudinal_method.txt. No current-phase peer report read, HTTP request, raw data acquisition, new outcome extraction, fitting or numerical result. Source-reported quantities are not our experimental results. Verdict: a conditional ordinary-forecast qualification question is legitimate; no presently authenticated updater-inheritance experiment and no novel core.

## Minimal task and actual functional boundary

Use early observations from one experimentally independent treated well to predict a later observed mitotic-event outcome in that same well under its already administered constant treatment. Define the source-training wells, target wells, prefix cutoff, later assessment window, treatment identifiers and target before outcomes. Count unit is the well/independent experiment, not each movie frame or tracked cell. A later mitotic event is a real recorded event with a functional proliferation interpretation; it is not equivalent to clonogenic survival, drug killing, independent metabolic viability or an eventual therapeutic response. If source tables do not reliably distinguish mitosis from fusion/tracking artifacts, this event target is unavailable rather than inferred from disappearance.

An explicitly weaker alternative is future morphology/chemical-feature forecasting, correctly labeled observed-feature prediction rather than an independent functional endpoint. The separate MTS experiment in another plate is not a future label attached to the tracked cells. It must not be joined to them by drug identity and presented as paired single-cell functional feedback. No independent later viability/function assay paired to the tracked cells is authenticated by the cached article.

The minimal event task still requires authenticated trajectories/images, well/experiment/FOV and lineage identifiers, drug/input timing, prefix and later event annotations and censoring metadata. None has been qualified as a reusable public payload in this phase. The design is a proposed data contract, not permission to fabricate a table from the article's aggregate curves.

## What prefix feedback means

Fix a source-trained predictor before the target experiment. At the cutoff, all methods receive the exact same target treatment metadata and prefix measurements. Feedback can include observed early transitions and early event labels whose complete prediction interval lies inside that prefix. The ordinary update may fit residuals/parameters on those legal pairs, then freeze for the later query window. It may not use later tracking assignments, future normalization statistics, an overlapping label window or future event frequencies. A direct predictor can ingest the entire same prefix without parameter updates; observed prefix trajectories are information for every comparator, not an exclusive advantage of an adaptive model.

No fresh intervention is selected in this setup. The task is target-context adaptation under a constant delivered drug condition, not held-schedule control, active drug discovery or sequential experiment selection. Splitting the movie into stages does not create multiple independent biological research tasks.

## Prevent future-selection and preprocessing leakage

The article removes tracks with total length at most 20 frames and edge tracks after time-lapse collection. Retaining those finished tracks as the baseline population conditions eligibility on future survival, persistence or tracking success. Define an at-risk population using baseline/prefix observations alone. Do not drop it because a track later becomes short, fragmented or exits view. Distinguish observed mitosis, death-like fragmentation, field exit, segmentation failure and unresolved disappearance; disappearance is not a death label. Specify censoring/unknown outcomes and report coverage rather than silently imputing outcomes. If endpoint ascertainment is too incomplete or condition dependent, stop the functional task.

Tracking used to construct input must be causal at the cutoff; full-movie backward identity corrections can reveal future behavior. Post-cutoff review may ascertain withheld outcomes, but must not revise cutoff inclusion or input features. Per-track first-three-observation normalization is legal only when all those observations precede the cutoff; birth/daughter times and any later normalization cannot leak backward. Segmentation was manually corrected and retrained on the source study images, so a prospective claim requires frozen external or source-training-only preprocessing. Otherwise declare a retrospective curated-input benchmark and do not generalize its result to end-to-end prospective performance.

## Grouping and strongest controls

All frames, descendants and fused connected lineages belong to one split. All FOVs from a shared well stay together; wells sharing one treatment preparation/run require an experiment-level grouping decision. Hold out whole independent experiments when available and tune only inside source groups. Query cutoffs within one well remain correlated and do not supply independent task uncertainty. If only one movie/well per drug is available, cross-drug forecast may be described descriptively, but cannot estimate independent within-drug adaptation generalization or learned updater transfer.

Strong controls receive identical source data, target prefix, treatment identity, preprocessing, fit/search budget and measurement cost:

- Fixed direct trajectory predictor conditioned on the entire prefix and elapsed time, including a strong regularized temporal model and a capacity-matched nonlinear alternative selected without query labels.
- Last-observed-rate/persistence and source drug-specific or pooled event-rate forecasts, so a treatment prior or extrapolated prefix trend is not mistaken for adaptation.
- Ordinary per-target recalibration/residual correction, ridge/RLS or regularized event-hazard update on the legal prefix, and ordinary joint/source-plus-prefix retraining with the same tunable parameters/steps.
- Same-window ordinary dynamic identification if a dynamical library is introduced; no exclusive informative-window access for a proposed world model.

For a learned updater, compare against those ordinary updates at common model starts and equal prefix history, including equal-budget search over update rules. Report held-well predictive utility and calibration alongside censoring/coverage, with uncertainty at the independent experimental unit. A more complex update must justify itself by a prespecified useful gain; stop if a simpler same-information method matches utility/cost. No specific numerical threshold or performance is fabricated before the payload and scale are qualified.

## Inheritance and RSI decision

The article's several constant drug conditions and many related cell tracks do not demonstrate a sequence of independently sampled research tasks with disjoint updater-training and later-task evaluation. Source-pretraining plus target adaptation would establish ordinary transfer at most; an inherited updater benefit needs held independent later tasks and common-start, equal-history, equal-total-cost comparisons. RSI additionally needs the strategy that produces updates to become measurably better at producing later improvements, against a fixed strategy and equal-budget strategy search. Neither repeated frames nor better late-trajectory fit establishes that property.

Proceed only to bounded asset/metadata qualification if separately authorized. Do not fit, claim public functional labels, reopen stopped GI/count routes or nominate this as innovation now. The source makes actual trajectory forecasting scientifically possible in principle, but the present evidence supports neither an executable inherited-updater benchmark nor a positive result.
