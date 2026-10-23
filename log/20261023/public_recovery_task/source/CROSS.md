# Actual cross-review and narrower assay-readout diagnostic

2026-10-23. Source read critic/INDEPENDENT.md and root/COUNT_HEADER.json/COUNT_DESIGN.json after its own independent seal. Root has separately retrieved the commit-pinned CSV, preserving all outcome bytes, but projected only headers/design so far. Source did not inspect the outcome suffixes. This cross-review changes no sealed original and makes no cryptographic-blindness claim.

## Authenticated design extension

The actual header is sample,replicate,schedule,0,7,14,21,28. Design projection contains VectorControl/V600E crossed with Continuous/Intermittent, six replicate labels each. These are **four sample/schedule groups**, not300nM/500nM groups. No dose column appears in this header. The original500nM protocol supplies dose/switch context; the header does not prove technical or biological replicate independence, matched cross-time wells, or independent repeated tasks.

## Conditional approval of weaker descriptive task

**GO for a frozen descriptive group-level released-assay-readout forecast**, conditional on actual parser/code pre-review. This is deliberately narrower than source's unqualified single-well/count/phenotype forecast. It does not require physical cell counts, same-well tracking, a complete RSI task bank, or proof that replicate labels identify independent biological preparations. Forecasting a measured CTG-proxy output is itself a legal empirical question.

For each of the four fixed groups and each time, take the arithmetic mean of every finite released value, retaining all values irrespective of magnitude. Divide by that group's day0 mean observed in the prefix. This ratio-of-means is a project-defined rescaling of the released assay table; it must not be replaced by mean of per-row ratios or represented as independently verified reproduction of the original initial-seeding normalization. The original primary says weekly CTG measurements were normalized to initial seeded numbers. Without further calibration, the released table scale remains a CTG-derived proxy, not physical count, absolute ATP, death rate or persister probability.

Freeze handling before inspecting outcomes: report finite-value counts at each group/time and missing/nonfinite locations; stop if any required group/time has no finite values or any baseline divisor is nonpositive/nonfinite. Do not add an offset, clip, remove7000-threshold observations, winsorize, choose log versus raw scale or change normalization after seeing results. Negative finite future values, if present, must be handled by the predeclared assay-readout scale, not silently dropped as “impossible counts”. Differing finite subsets can induce composition shifts; report that limitation. The common noisy day0 divisor induces correlated errors across times and is not another independent observation.

Use only the frozen7/14-day prefix and known sample/schedule as input to21/28-day queries. Day0 is only lawful baseline information. All forecasting methods must get identical information; known intermittent switches are real inputs, not privileged world knowledge. Hyperparameters, simple baselines, primary loss, endpoints and stop criterion must be fixed before query access. Do not give one model ProcessData's full-four-week lambda, growth_rates.csv, a full-fit fitness matrix, future control values or its author-selected outlier exclusion. A method beating only on-drug stationary extrapolation would not establish world-model necessity if a stronger schedule-aware ordinary method is equally good.

The four group readouts and two query times yield a tiny descriptive comparison. No significance test, independent-n=24 claim, broad transfer, unique resensitization mechanism, drug optimization, agent benefit, inherited updater benefit, joint gain or RSI follows. A positive prefix prediction can motivate further qualification; a simple baseline win can be useful negative evidence. The original author's full-trajectory model fit remains in-sample and cannot serve as held-out performance.

## Actual source objection to critic

Critic's independent “real cell-count observations” description was challenged using the originating2022 primary: weekly Fig2 and dose-response Fig3A/B use CellTiter-Glo, and Fig3C's PI death measurements are a distinct five-week10cm-dish experiment. Published molecular and PI endpoints cannot be joined to the four-week CSV by schedule name alone. Source also asked critic to evaluate whether the deliberately weaker group-readout diagnostic avoids the need for physical-count or same-well identification, rather than prohibit all numerical work because the full cellular/RSI claim is not yet supported.

Reciprocal response pending; final scope and any unresolved objections will be retained in a separate addendum before cross sealing.
