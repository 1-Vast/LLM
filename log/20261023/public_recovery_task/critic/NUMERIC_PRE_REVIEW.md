# Independent qualification review before narrow numerical diagnostic

2026-10-23. APPROVE a conditional, descriptive measured-readout forecast, with the specification below frozen before outcome parsing. Read only COUNT_HEADER.json and COUNT_DESIGN.json, never the response CSV or response values. No code executed or new GET. This is a development diagnostic with author narratives already exposed, not a blinded external benchmark or biological efficacy test.

## Why the measurement contract is sufficient for this limited question

The primary identifies the actual endpoint as CellTiter-Glo-derived cell-number/viability estimates normalized to initial seeding. The fixed-commit CSV header/design projection identifies Vector Control/V600E by Continuous/Intermittent, replicate labels1..6 and days0/7/14/21/28. Those assets can support a descriptive condition-time average of the released measured proxy without knowing whether every column label traces the same living well. Do not treat replicate numbers as longitudinal identities or independent biological runs.

Physical cell-count calibration, separation of ATP/cell versus live-cell number, and original author normalization details are needed for stronger biological interpretations, but need not block computing an accurately named forecast of the released CTG-derived readout. Rebaseline each condition's per-time mean by its own observed day0 mean; this is a transparent definition of a dimensionless response, not proof of absolute viable counts or reversal of drug resistance. If inputs were already normalized, this operation remains an explicitly defined secondary baseline ratio; do not claim recovery of raw luminescence.

The one question is whether the first observed two-week multiplicative response pattern can predict the third/fourth-week measured condition means under the known schedule. This is meaningful even in a single engineered cell system. It is not updater inheritance, novel world-model discovery, prospective drug scheduling or an RSI task series. No requirement for full RSI assets should prevent this small calculation.

## Exact shared inputs and fixed operations

For each condition and time, take all finite nonnegative recorded measurements and their arithmetic mean m_t; define g_t=m_t/m_0. Day0/7/14 are the permitted prefix. Days21/28 are exclusively query responses. Future values cannot tune normalization, parameter choice, eligibility, model selection or interpretation of the initial state.

The four proposed methods use the same permitted prefix and schedule information: persistence gives (g14,g14); global exponential gives (g14^(3/2),g14^2); recent-week repetition with q=g14/g7 gives (g14*q,g14*q^2); phase repetition gives the recent-week rule for Continuous, and (g14*g7,g14^2) for Intermittent. The intermittent formula correctly repeats the first on-week factor g7 and first off-week factor g14/g7. It is a simple ordinary phase-dependent rule, not a new world-model mechanism. Global exponential assumes the first14-day average log slope; recent-week repetition assumes the latest seven-day factor persists; these are competing explicit restrictions, not fitted biological states.

All four receive the same source bytes/prefix availability. A method choosing not to use a known schedule is still a legitimate fixed baseline; beating it alone does not establish a novel contribution. No author four-week-fit parameters or challenge matrix should be introduced into these methods.

## Conditions that must be fixed before execution

Report every condition/day's eligible count and counts of blank, negative, nonfinite or otherwise invalid fields. Finite/nonnegative filtering is a predeclared measurement-eligibility rule, not an outlier filter; no threshold trimming or replicate selection. Preserve the fixed24 design rows and explicit missingness. Different times may have different valid n; do not infer a matched trajectory from available-case means.

Require each necessary mean to exist, m0>0 and g7>0 for a complete four-method comparison. If a required denominator is zero/missing, apply an explicit predeclared invalid/STOP outcome rather than adding epsilon, changing formulas or removing a condition to improve averages. g14=0 and zero query outcomes are allowed on an ordinary squared-error scale. Forecast overflow/nonfinite output must also be reported as invalid, not clipped after observing outcomes.

Use a fixed mean squared error over the eight condition-by-query endpoints, weighting four conditions and two horizons equally; show the complete per-condition/per-horizon errors and forecasts. A compatible MAE may be descriptive secondary if frozen in advance. Do not add p-values, confidence claims based on24 independent biological trajectories, winner-selected subgroups, or post-hoc log transforms. Baseline-ratio scales can amplify noise in low-baseline conditions; disclose that limitation and do not change scale after a result. Identical predictions between rules in some conditions/horizons are expected, not a coding error.

## Interpretation and stop rule

A phase rule win would show this ordinary first-cycle pattern has descriptive forecasting value on these measurements; it does not identify adaptation states, birth/death rates or virtual-cell necessity. A failure would falsify this fixed multiplicative extrapolation on the measured endpoints, not every ordinary dynamic model or recovery mechanism. Do not add residual heads, gates, clipping or new time windows to rescue it. The selected source remains useful even if the simplest baseline wins.

Freeze protocol, input commit/path/hash, complete condition set, formulas, loss, eligibility and code after independent code review, before parsing any response. Execute once, retain all predictions/errors/failures and audit arithmetic. No fit or native experimental cost comparison is asserted. World, agent, inheritance, synergy and improved-improver benefits remain unestablished.
