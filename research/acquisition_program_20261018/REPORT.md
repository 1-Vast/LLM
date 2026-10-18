# Acquisition-value programs on a whole-pool target task: report

**Internal development assessment on exposed PRISM 19Q4 (not independent biological confirmation); `verify.py` VERIFIED; no sealed
tier opened; nothing committed or pushed.** Result: the handwritten lookahead and the agent-searched program do **not** beat the
fixed A-optimal design on held-out task groups. The 12-proposal cycles produced one accepted agent edit (small, within noise) and no
accepted conventional edit. This is reported as unchanged performance for these candidates; it is not a project-wide STOP.

## 1. Clarification of the predecessor hindsight diagnostic
`D_hindsight` chose between rules per compound by squared error (a fit criterion), not by terminal decision utility. Recomputed
from public records: choosing per complete campaign the better of the ridge and R1 nomination lists by realised hits gives
**131 hits versus R1's 100 (ridge 95) over 36 campaigns**; an unavailable hindsight diagnostic only. Appended to the predecessor's
`REPORT.md` section 8; its registered decision is unchanged.

## 2. Task
Whole-pool target set (23 pools cut by a salted hash into groups of 6, 6, 6, 5); probes may only buy non-target pools, so none reveals
a target entry; events, nominations (32 per 64 compounds, ≤ 3 per compound), 3-pool budget and ridge-plus-feedback scoring are the
predecessor's. Decision: the second pool (seed pool and third pool fixed). Development: folds 0-1 × groups 0-1 × five paired noise
draws (20 cells); held-out: folds 2-4 × groups 2-3 × five fresh draws (30 cells). Noise draws are
averaged within a compound and are not biological samples. Costs are hypothetical pool wells (no plate map); all arms buy exactly
3 pools (lines per compound 71.5 fixed, 69.7 for the lookahead-based programs).

## 3. Programs and search
* Handwritten lookahead (conventional): joint posterior over a candidate pool's lines, 16 sampled outcomes, exact Gaussian update, 32
  posterior profile draws for event estimates, terminal value = event estimates of the three lines the scoring rule nominates. Model
  probabilities are unvalidated.
* Editable object: an expression over ten lookahead features (`PROTOCOL.md` section 4). Both searches start at the lookahead; 12
  proposals each; acceptance only if the development total rises and more cells are won than lost; the incumbent is otherwise kept.
* Conventional search: 12 random linear combinations of standardised features: all rejected (totals −7 to −48).
* Agent search (`deepseek-flash`, 12 proposals, 34k tokens): 1 accepted (proposal 4, `gain + 0.5*flip*(abs(gain)+0.01)`: +6 events
  over 20 cells, 8 cells better, 5 worse, 10% of decisions changed), 1 no-op identical to the incumbent (`gain`), 10 rejected. Every
  proposal's hypothesis, expected nomination change (it always predicted "up") and observed result are in `SEARCH_TRACE_agent.json`;
  every hypothesis predicted "up"; on the development cells only proposal 4 was confirmed (and it did not transfer).
* Selected incumbents were frozen (`FREEZE2.json`) before any held-out scenario was built.

## 4. Results
Development (events over 20 cells): fixed 305, lookahead 337 (+0.100 per 64 compounds [−0.003, +0.199]), agent incumbent 343,
conventional incumbent = lookahead 337; unavailable hindsight choice ceiling 410.

Held-out (events per 64 compounds, per task; five fresh draws averaged; family-cluster bootstrap 95%, one-sided p):

| arm | events | vs fixed |
|---|---|---|
| fixed design (ridge) | 1.822 | |
| handwritten lookahead = conventional incumbent | 1.717 | −0.106 [−0.262, +0.022], p 0.94 |
| agent-search incumbent | 1.725 | −0.097 [−0.232, +0.026], p 0.94 |
| agent − lookahead | | +0.008 [−0.033, +0.054] |
| R1 / gated R1 / forest (update rules on the fixed design) | 1.922 / 2.083 / 1.922 | R1 +0.100 [−0.281, +0.500] |
| prior (no feedback) | 0.931 | −0.892 [−1.213, −0.616] |

* The development lead of the lookahead (+0.10) did not transfer: the held-out point estimate is −0.11 and no contrast reaches the
  practical floor (0.1875). The agent's accepted edit changes 11% of decisions relative to the lookahead and moves nothing (+0.008).
* Feedback value is real on this task (prior 0.93 vs ridge 1.82); acquisition choice among non-target pools is not where the
  measurable gain is.
* Decision-level: the lookahead probability `la` ranks compounds (quintile means of realised events per compound 0.005 → 0.071, 14×)
  but overstates the level about tenfold (0.09-0.75 predicted vs the realised rates, which are after campaign-level nomination),
  so it is a ranking signal, not a probability. The lookahead chooses the fixed pool for 10% of decisions and spreads over all
  candidate pools; the agent incumbent behaves the same (10%). Unknown nominations: 91 fixed, 96 lookahead.
* Unavailable hindsight ceiling of the acquisition choice (held-out): 704 events versus 656 fixed (+7%); in development 410 versus
  305 (+34%). The shrinkage from development to held-out matches the transfer failure above.

## 5. Evidence statements
1. On a whole-pool target task, one-step posterior lookahead is not better than the fixed A-optimal second pool (held-out −0.106
   [−0.262, +0.022]); a development lead (+0.100 [−0.003, +0.199]) was not reproducible.
2. Within a 12-proposal budget the agent search found one development-accepted edit that does not differ from the lookahead on
   held-out groups; conventional random search found none. The agent did not beat conventional search (+0.008 [−0.033, +0.054]).
3. Model probabilities from posterior sampling rank but are not calibrated levels.
4. Unchanged: ridge-plus-feedback remains the backend; R1 and gated R1 as update rules (1.92, 2.08) are above the fixed design but
   with intervals including zero (R1 +0.100 [−0.281, +0.500]), consistent with the predecessor STOP.
5. Not shown: any benefit of a different acquisition program with a different feature set; the feature set and the single adaptive
   decision limit what a search can find. The ceiling of the choice (+7% held-out) bounds the possible gain from this decision.

## 6. Limits
Exposed folds; hypothetical costs; noise-draw averaging reduces variance of the synthetic noise but adds no biological sample; one
adaptive decision of three pools; event estimates in the lookahead use 32 draws (top-3 selection bias); the counterfactual table
is a cache of what an executed run would observe (tested). `DEVIATIONS.json` lists the shadowed-module launcher fix and the
no-op proposal.

## 7. Runnable incumbent
`INCUMBENTS.json` (fixed, `la`, conventional = `la`, agent expression). Reproduce: `python -B ap_build.py dev`, `python -B run_search.py`,
`python -B seal.py freeze2`, `python -B launch.py build-held`, `python -B launch.py evaluate`, `python -B verify.py`.
