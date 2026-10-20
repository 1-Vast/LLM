# Protocol: does inheriting an executable experimental procedure beat ordinary refitting, planning and caching?

Status: SYNTHETIC METHODOLOGY DEVELOPMENT. Drug-discovery effectiveness is NOT_TESTED (`INVENTORY_CHECK.json`: no measured action/readout/endpoint mapping with
repeated latent regimes, read costs and an unexposed evaluation set exists; nothing was opened or procured). Every number below concerns generated worlds.
Predecessor packages (`functional_rule_revision`, `self_improving_virtual_cell`, `innovation_validation`, `innovation_validation_repair1`) are preserved byte for byte
(`PRESERVED_BEFORE.json`, 632 files, compared by the verifier). Nothing is committed, pushed, purchased or sent; no API is used.

## Research unit (one falsifiable statement)

A **plan** is a small program: applicability condition -> first read `p1` -> observation-dependent second read (`second[bin(y1 - a[p1])]`, or STOP) -> posterior update
-> top-5 shortlist, with explicit exits (UNKNOWN when the unexplained component dominates the posterior, STOP, INAPPLICABLE). It is not a loading matrix, a text
explanation or an unused probe list: the verifier re-executes every logged campaign from the stored plan JSON and the logged reads and must reproduce the same reads
and nominations; fixtures show that changing an executed branch changes the second read while changing unused metadata does not.

**Question.** On later backgrounds, can a plan learned from earlier feedback keep the quality of the strongest conventional planner using fewer assay units, or less
total planning computation, while retaining old-regime quality? **Primary resource estimand: assay units** (the scientific resource). Planning computation is the
secondary resource, reported with a break-even reuse count, never hidden in preprocessing or library construction.

## Shared response family (identical for every arm)

Residual `r = y - a` over 66 drug-pair units: regime profiles (null + learned, from released fully-measured backgrounds), noise variance estimated from the released
residuals, plus an unexplained component U (sd 0.30, prior 0.05). Observed pairs keep a Bayesian-shrunk value; shortlist = top-5 posterior-mean scores. UNKNOWN exit
(posterior of U > 0.5 -> all later reads direct) applies to every library arm. The conventional model is NOT capped: all arms use the same family and the same library.

## Arms (`pi_run.py`)

2x2: response-factor inheritance OFF/ON (`f0`/`f1`) x executable-plan inheritance OFF/ON (fresh one-step planning `kg1` / learned plan):
`f0_kg1`, `f1_kg1`, `f0_plan`, `f1_plan`. Conventional comparators on the f1 library: `f1_kg2` (corrected two-step lookahead for reads 1-2, one-step afterwards) and
`f1_distill` (amortised policy: depth-4 decision tree on (step, posterior over components) imitating the two-step teacher on all released backgrounds; teacher
cost counted). `f1_plan_re` rebuilds the plan every generation (equal discovery budget, no inheritance). Ablations: `f1_plan_nobranch` (observation-dependent second read
replaced by one fixed read), `f1_plan_xplant` (the plan learned in the partner stream of the same kind, applicability fingerprint bypassed, executed on this stream's
library), deletion = `f1_kg1` (an undeployed plan is exactly the fresh planner; tested). Statics: `prior`, `exploit`. Reads 3.. use the same one-step planner in every arm.

Factor learning (`pi_factors.py`): candidates = `add` (new profile from >= 2 mutually close unexplained residuals) or `refine`; <= 12 candidates per generation per
arm; promotion by leave-one-background-out replay (gain >= 0.004, wins > losses, wins >= 2; ties never promote). ON starts from the previous labelling, OFF from empty.
Plan learning (`pi_plan.py`): per generation and budget, <= 12 candidate plans scored on the training backgrounds (leave-one-out libraries; recorded vectors as
read table and truth); seeds = model-built plan (+ incumbent and <= 2 archived plans when inheriting), then deterministic mutations (alternative second reads, STOP toggles,
alternative first reads); the winner is validated against the incumbent/default on the newest batch (plan rule: gain >= 0.004, wins > losses, wins >= 1; a 4-background
batch cannot yield 2 wins for a plan that acts on only some regimes - this relaxation was chosen on non-evaluation seed 5 before the freeze, and every record stores
whether the strict library rule would also have passed); rollback to the default if the deployed plan is worse than it by more than 0.004. Archive reuse = incumbent kept
or an archived plan promoted.

## Worlds and schedule (`pi_world.py`, fixed before any scored run)

Four kinds x two seeds = **8 streams** (seeds 71001, 71002): `alias` (two-level identification: marker pairs shared by regime groups), `chain` (sequential decision list,
no marker), `novel` (alias plus an unseen regime 5 in batch 4 - tests the unknown exit), `null` (no effect - false-positive control). 66 pairs, 8 released history
backgrounds, 4 generations (checkpoints 0-3), 4 task backgrounds per generation (batch b is run with the state validated after checkpoint b-1), 4 never-released
old-regime retention anchors per checkpoint. Later-task outcome = batches 2-4 (12 tasks). Budgets 3 and 4. Reads return a fixed noise table, so a repeated read of a
pair in a background is identical in every arm. Smoke tests used seed 5/6 streams only (non-evaluation). No seed replacement, threshold change or generator edit after
the freeze; failed or null worlds stay in every table.

## Resources and stopping rules

One numerical thread, <= 30 elapsed minutes for the whole 8-stream run plus transplant pass, <= 12 candidate evaluations per arm per generation (the cap is not equal
computation: process CPU and elapsed time are recorded per component). Total cost per arm = shared factor learning + arm-specific learning/validation/distillation +
invocation over all 16 task backgrounds; per-deployment cost = arm learning; amortised over the 16 task invocations in this study; break-even reuse count reported against
fresh Kg1 and Kg2. Costs are instrumented process time, not assay costs. Stage ledger: `eval` and `xplant` can each be claimed once; outputs are write-once.

## Primary contrast, margin and decision rule (all fixed before the run)

Primary: pooled `f1_plan@3 - f1_kg2@4` (>= -0.01 means "keeps the reference quality with one assay unit fewer"). It is meaningful only if the plan also beats the
conventional comparators at the same budget (`f1_plan - max(f1_kg2, f1_distill) >= +0.01` pooled at B=3 and >= 0 in 6/8 streams); otherwise any saving is explained by
planning or distillation. Margin delta = 0.01 (predecessor margin; ~1.3 percent of mean utility). Decision labels (`CONFIG.json`): `ADVANCE_TO_POWERED_INDEPENDENT_DESIGN`,
`CLOSE_NO_PRACTICAL_BENEFIT_OVER_FRESH_ONE_STEP_PLANNING`, `CLOSE_EXPLAINED_BY_CONVENTIONAL_LOOKAHEAD_OR_DISTILLATION`, `INCONCLUSIVE_DEVELOPMENT`. Eight streams are not
powered: no confidence interval, significance test or SUPPORT label is produced; per-stream paired differences and sign counts are reported.

## Alternative information paths and limits

Plans share pair identities with the library, so a plan can exploit the same pair-level information the library holds; any plan benefit beyond the library is therefore
conditional on search, not on new information. The generator contains structures (aliasing, sequential decision lists) in which observation-dependent measurement
matters; this favours plans relative to unstructured worlds, and the `null` and `novel` kinds check false positives and the unknown exit. The conventional response family
is the same mixture family for every arm (a continuous latent comparator is out of scope here and is NOT claimed to be matched). Quadrature (5/3 Gauss-Hermite nodes) is
accurate to a few percent (fixture: <= 6 percent relative error on one-step KG, 25 nodes agree with Monte Carlo). Real utility, open-ended evolution and wet-lab
relevance are untested.

## Reproduction

`python pi_freeze.py write` (once) -> `python pi_exec.py` (writes RUN/eval, RUN/LEDGER.json, RUN/RESOURCES.json) -> `python pi_stats.py RUN/eval SUMMARY.json` ->
`python pi_verify.py`. Tests: `tests/test_procedure_inheritance.py`.
