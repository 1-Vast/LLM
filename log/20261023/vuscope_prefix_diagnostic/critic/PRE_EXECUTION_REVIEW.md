# Concrete pilot pre-execution review

2026-10-23. Read current PROTOCOL.md, research/vuscope_prefix_diagnostic_20261023/pilot.py and test_pilot.py as text. No biological values, outcome files, training, author code execution or GET. No peer report consulted. Exact reviewed versions are bound by the accompanying seal.

Status: REVISE_NARROW_RECORDING_AND_COMPLETION_CHECKS_BEFORE_RUN. No change to scientific model, data window, dose selection, tuning opportunities or endpoints is requested.

## Matches verified by code inspection

Actual prefix is6..72h; model time subtracts6h and converts to days. Forecast points75..120h include exact120. Every method receives the same six dose histories and per-well6h normalization. Surface code matches the released logistic/dose formula with expit for numerical safety;7parameter variant adds only gamma drift scaled by2.75days and nests the6parameter model at zero drift. All asymptotes and starts fit prefix only. Safe positive capacity bounds remove the time0zero denominator; a<1 permits declining curves.

Nine fixed surface starts, bounds, SSE selection and nfev caps match protocol. Independent-dose logistic has three starts per dose, identical capacity/rate bounds, and12total parameters. Direct model has exactly eight configurations, one shared per-curve configuration chosen on<=48h→51..72hvalidation, then refit through72h. Polynomial ridge leaves intercept unpenalized; local log1p is zero-safe. Persistence uses actual72h. None uses late outcomes for fitting or selection. No log-count noise assumption, future controls, CTG or fitted GRIVUS is introduced.

Surface nfev and njev are solver counters, not necessarily every numerical-Jacobian residual invocation; actual time is more complete cost evidence than interpreting nfev as exact FLOPs. All methods receive differing disclosed search/model capacities; this is a fixed ordinary diagnostic, not equal-total-search proof. Independent-dose relaxation and direct menu remain legitimate sentinels even if they use different parameter counts.

Primary mse120 is mean over six actual120h normalized-count errors; secondary mse_late averages16future timestamps then six doses. Raw-count reconstruction multiplies each error by its measured baseline, correctly yielding absolute-count error. Per-curve means receive equal weight overall; per-cell means are also recorded. Missing/negative late values abort rather than being selected out. Shared timepoints/doses/anonymous compound labels are not biological replication. No ranking/clinical/RSI claim is warranted.

## Narrow blockers to literal execution contract

1. Prefix exclusions are appended locally, but persisted only in RUN_RECEIPT after outcomes. The protocol says they are recorded before outcomes. Save prefix eligibility/exclusions and denominators/schedule keys alongside fits before sealing predictions. An invalid late row must leave this eligibility history reviewable even if no final receipt is written.
2. With all groups invalid in a cell, or even no eligible groups overall, current code can proceed to empty np.mean calls and write NaN summary values with a nominal receipt. Assert sufficient/nonempty eligible cells before outcome access. At minimum require all four declared cells have an eligible group because the gate explicitly uses3/4cells; record any narrower eligibility contract before outcomes. Do not add an outcome-driven minimum after seeing results.
3. The frozen gate and promised paired wins are not yet computed in this code. Save an exact predeclared gate function/result (either here or a separately frozen audit script) using: same-cell improvement of BOTH mse120 and mse_late in at least3of4cells; strictly more than half eligible curves improving mse120; BOTH overall endpoints beating independent-logistic AND direct-selected. All clauses must hold. Preserve per-curve pairing; do not silently treat fewer available cells as a changed denominator or invent numerical tolerance after results. Any missing/nonfinite method/group should abort or fail the frozen gate explicitly.

The already frozen direction of these repairs does not authorize extra starts, optimizer iterations, alternate endpoints or changed models. Rebind code/protocol hashes after repair before running.

## Important qualifications rather than model blockers

read_rows converts response fields to float only for requested times. It nevertheless decodes and splits the complete text line for unrequested late rows, so the synthetic test proves no future response FLOAT conversion/use, not that no late text bytes were decoded or decompressed. The fitted dataflow receives only prefix values; this is the relevant leakage property. Use that precise language or strengthen the byte parser before claiming literal non-decoding. It also parses all wells at requested times although only scheduled wells enter fits; disclose this exposure and avoid claiming all unused prefix counts remain unseen. No future numeric value enters model fitting in the inspected code.

The nested7parameter optimizer has the same initial starts with zero drift but is not explicitly initialized from the eventual6parameter optimum. Consequently finite local optimization can make its selected training loss worse despite nesting. The fixed-stop protocol correctly rejects expansion of this configuration; this would not prove the larger mathematical family itself is inferior. Report fit statuses/train loss/nfev limitation rather than silently add starts to rescue it.

Synthetic tests are meaningful necessary formula, clock-dataflow and zero-handling checks, not a biological validation or complete independent reimplementation. Reviewer did not rerun/import them. Snapshot/late outcome evaluation must remain separate: parameters/predictions/eligibility sealed before any future numeric conversion, final receipt only after all finite checks, no rerun after failed gate. After the three recording/completion repairs, this fixed diagnostic has no identified remaining scientific-execution blocker.
