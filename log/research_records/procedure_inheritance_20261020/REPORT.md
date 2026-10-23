# Procedure inheritance: a learned executable plan reproduces what ordinary lookahead and distillation already give

**Decision: CLOSE the proposed novelty in this finite synthetic family.** A reusable observation-conditioned plan executes correctly and is worth about +0.0075
shortlist utility over fresh one-step planning when only three reads are allowed. Fresh two-step lookahead (+0.0066) and an amortised distilled policy give the same
amount, so the benefit is explained by ordinary planning and caching, not by inherited procedure. Pre-registered label: `CLOSE_NO_PRACTICAL_BENEFIT_OVER_FRESH_ONE_STEP_PLANNING`
(plan minus fresh one-step planner is below the 0.01 margin at both budgets). This is synthetic methodology development. Drug-discovery effectiveness is **NOT_TESTED**:
`INVENTORY_CHECK.json` found no measured action/readout/endpoint mapping with repeated latent regimes, read costs and an unexposed evaluation set, and nothing was opened or procured.
Eight streams support no confidence interval, significance test or SUPPORT label, and none is produced.

## What was built and what ran

- One shared response family for every arm (regime mixture + unexplained component U, noise estimated from released residuals, shrunk values for read pairs, top-5 shortlist),
  corrected one-step KG and two-step lookahead (`pi_model.py`); factor learning with leave-one-background-out replay (`pi_factors.py`); an executable plan with
  applicability condition, first read, observation-dependent second read, posterior update, shortlist and UNKNOWN / STOP / INAPPLICABLE exits, a hash identity over content and
  history, a search/validation/rollback lifecycle with incumbent and archive reuse, and an amortised-policy baseline (`pi_plan.py`).
- Frozen before scoring (`FREEZE.json`, 11 files): 8 streams (alias, chain, novel, null x 2 seeds), 4 generations, <= 12 candidate evaluations per arm per generation, one numerical thread,
  30 elapsed minutes, budgets 3 and 4, 12 later-task backgrounds per stream, 16 retention anchors. One run, no seed replacement, no change after the freeze.
- Dress rehearsal of the same code path on non-evaluation seeds 5/6 (not reported as results; it showed the same label). The plan promotion rule (one strict win instead of two on a
  4-background batch) was chosen on seed 5 before the freeze; every plan record stores whether the stricter library rule would also have passed.
- One verifier-only path fix (ledger location) was made after scoring and is recorded in `FREEZE_AMENDMENT.json`; no result-bearing file changed.
- Execution: 3.13 elapsed minutes in total (ceiling 30), 181.6 process-CPU seconds over eight streams plus 1.0 s for the transplant pass.

## Plan execution correctness (implementation only)

Fixtures (`pi_fixtures.py`, tests): the same plan reads a different second pair after different first observations (regime-1 background: pair 0 then its own effect pair; regime-3
background: pair 0 then the other marker) and nominates the regime's effect pairs; collapsing to a fixed second read loses the dependence; changing unused history metadata changes
the plan id but not the executed reads, changing an executed branch changes them; the UNKNOWN exit fires when no regime explains the reads and later reads become direct; STOP hands over
to the default planner; an inapplicable plan is exactly the fresh planner; tampered plan artifacts fail identity checks. In the evaluation, deployed plans took both branches in five of the six non-null streams (for example 15/4 and 6/10 branch counts in the two alias streams; `chain_71002` used one branch). The verifier re-executed all 3,840 rows of every arm (tasks, anchors, transplants)
from the stored libraries, plan JSON and student arrays against the logged reads and reproduced every query and nomination; every row names the fingerprint of the library it used.
One-step KG with 5 quadrature nodes is about 3 percent above Monte Carlo (25 nodes agree within sampling error); this approximation is shared by all arms.

## Later-task utility (batches 2-4, pooled over 8 streams; oracle 0.7328, fresh exploit 0.6385 at B=4)

| Arm | B=3 | B=4 |
|---|---:|---:|
| f1 plan (factors ON, plan ON) | 0.6960 | 0.7050 |
| f1 two-step lookahead (reference) | 0.6950 | 0.7050 |
| f1 distilled policy | 0.6958 | 0.7044 |
| f1 fresh one-step KG | 0.6884 | 0.7039 |
| f0 fresh one-step KG (factors OFF) | 0.6952 | 0.7004 |
| f0 plan (factors OFF, plan ON) | 0.6954 | 0.7016 |
| f1 plan rebuilt every generation | 0.6934 | 0.7032 |
| f1 plan, branch collapsed | 0.6863 | 0.7050 |
| f1 plan, partner-stream plan transplanted | 0.6884 | 0.7039 |

Paired per-stream differences (8 streams, margin 0.01; `SUMMARY.json` has every stream):

| Contrast | mean | streams positive |
|---|---:|---:|
| **Primary:** plan@3 - lookahead@4 (one assay unit fewer) | -0.0090 | 1/8 |
| lookahead@3 - lookahead@4 (cost of dropping a unit for the reference itself) | -0.0100 | 1/8 |
| distilled@3 - lookahead@4 | -0.0092 | 0/8 |
| plan@3 - fresh one-step@3 | +0.0075 | 5/8 |
| lookahead@3 - fresh one-step@3 | +0.0066 | 5/8 |
| plan@3 - lookahead@3 / - distilled@3 | +0.0010 / +0.0002 | 2/8 / 2/8 |
| plan@3 - plan rebuilt each generation (inheritance vs rediscovery) | +0.0026 | 2/8 |
| plan@3 - branch-collapsed plan | +0.0097 | 4/8 |
| plan@4 - fresh one-step@4 / - lookahead@4 / - distilled@4 | +0.0011 / -0.0000 / +0.0006 | 2/8 / 2/8 / 4/8 |
| factor inheritance, fresh planner: f1 - f0 at B=3 / B=4 | -0.0068 / +0.0034 | 0/8 / 4/8 |
| 2x2 interaction at B=3 / B=4 | +0.0074 / -0.0001 | |

- The primary estimand nominally holds (-0.0090 >= -0.01) but it is not unique to the plan: dropping a unit costs the reference planner 0.0100 and the distilled policy 0.0092, and the plan
  is not better than either by the 0.01 required (-0.0011 pooled, 2/8 streams). At B=4 nothing separates the arms (all within 0.0011).
- By kind at B=3 (plan minus lookahead): alias -0.0024, chain +0.0063, novel -0.0001, null 0.0000. The null worlds deploy no plan and every library arm equals fresh planning there.
- Branching matters when the plan matters: the collapsed plan loses 0.0097 at B=3 (and nothing at B=4, where the heavy branch dominates the tasks).
- Factor inheritance did not help the fresh planner at B=3 (-0.0068, 0/8 streams) and helped slightly at B=4 (+0.0034, 4/8); with plan learning ON the 2x2 interaction is +0.0074 at B=3 only. It cut
  factor-learning CPU from 0.63 to 0.46 s per stream (0-1 candidates per generation against 4 for the rebuilt library). Both libraries recover the planted regimes imperfectly (3-4 of 4).
- Inheritance vs rediscovery: the inherited plan is +0.0026 over rebuilding it each generation at B=3 (2/8 streams), +0.0018 at B=4. No stream shows a large reuse effect.
- Retention on never-released old-regime anchors: plan minus fresh one-step planner is +0.0029 / 0.0000 / 0.0000 / +0.0029 at the four checkpoints, worst stream -0.0008; the lookahead
  arm's worst stream is -0.0082, the distilled policy's -0.0107, the factor-OFF plan's -0.0137. The retention rule held (>= -0.01) for the f1 plan.
- Lifecycle (f1 plan): promotions 8 at B=3 and 9 at B=4 across the 6 non-null streams, none in null streams; incumbent reuse events 9 (B=3) and 5 (B=4); one incumbent retired by rollback (chain_71001, checkpoint 3, B=3); `chain_71002` deployed no plan at B=4. Only 2 of the 8 (B=3) and 5 of the 9 (B=4) promotions would also have passed the stricter two-win library rule.

## Total cost (process CPU seconds, one thread, mean per stream; includes factor learning, plan search/validation/distillation, invocation over all 16 tasks)

| Arm | B=3 | B=4 | arm learning | candidates | validation replays |
|---|---:|---:|---:|---:|---:|
| fresh one-step KG (f1) | 0.50 | 0.51 | 0 | 0 | 0 |
| fresh two-step lookahead (f1) | 1.92 | 1.99 | 0 | 0 | 0 |
| plan (f1) | 1.87 | 2.31 | 1.39 / 1.81 | 42.8 | 476 |
| plan rebuilt every generation | 1.71 | 2.09 | 1.22 / 1.58 | 38.6 | 416 |
| plan, factors OFF | 1.77 | 2.18 | 1.11 / 1.51 | 42.0 | 465 |
| distilled policy | 6.89 | 6.91 | 6.42 | 112 teacher decisions | 0 |

Per-use planning CPU: plan 0.0012 s, lookahead 0.092 s, one-step 0.0027 s. Break-even reuse count (uses of the artifact after which its learning has paid for itself against planning fresh):
about 15 (B=3) and 20 (B=4) against fresh two-step lookahead for the plan, about 71 and 69 for the distilled policy, and 949 and 7,408 for the plan against fresh one-step KG. So the plan is a cheaper
cache of a lookahead than distillation, but caching the lookahead buys no utility over the cheap one-step planner at B=4 and nothing over the lookahead at B=3; the equal-candidate-cap
comparison is not equal CPU (actual search effort is reported above). Costs are instrumented compute, not assay costs.

## Failed cases, exits and limits that matter

- **UNKNOWN exit never fired on a genuinely novel regime** (0 of 32 novel-regime tasks in the two novel streams): the exit only reacts when the reads happen to hit the new regime's effect pairs, so
  it is not a novelty detector. It fired on known regimes in 3-9 of 128 tasks per stream (false exits).
- **The applicability condition is brittle.** The range check on the public reference rejected 21 of 112 plan invocations (15 of 16 in `chain_71002`, where the plan was trained on few backgrounds),
  falling back to fresh planning. All 112 partner-plan transplants were rejected by the same check, so the pre-registered transplant arm tested the exit, not the plan content.
- **Post hoc exploratory diagnostics** (`POSTHOC.json`, not pre-registered, label unchanged): with the range check disabled the plan is +0.0085 over fresh one-step planning at B=3 (+0.0009 over the
  registered plan arm; +0.0011 and -0.0001 at B=4); a content-only transplant of the partner plan is +0.0003 over fresh one-step planning and 0.0072 below the plan's own, so the benefit is specific to the plan learned in that world and
  is not a generic gain.
- Decision labels are stage-wise rules on pooled means of 8 streams; a plan advantage of +0.0075 against a 0.01 margin is within what eight streams cannot resolve, which is why the conclusion rests on the
  matched conventional arms (lookahead and distillation reach the same value) and not on the plan-vs-fresh gap.
- The generator contains structures where observation-dependent measurement matters (alias, chain); the null and novel kinds show no false deployment but cannot show reuse value. The conventional response
  family is the same mixture for every arm, so a continuous-latent comparator is not covered. Open-ended evolution, real-assay cost and measured utility are untested; four generations support at most bounded reuse.

## Next action warranted by the evidence

Do not build more agents, larger world models or favourable generators for this claim. If anything is continued, it is the cheapest decisive test of the part that survived: that a plan can serve as an
inexpensive cache of lookahead *when reads are scarce*. That needs a measured, complete action pool with replicated reads and real read costs (`INVENTORY_CHECK.json` lists the observation structure;
none exists locally), with a sampling unit of independent backgrounds and a variance/power analysis from measured between-background spread. Until then the procedure-inheritance novelty is closed here.

## Reproduction and files

```powershell
.\.venv\Scripts\python.exe research\procedure_inheritance_20261020\pi_freeze.py check
.\.venv\Scripts\python.exe research\procedure_inheritance_20261020\pi_verify.py
.\.venv\Scripts\python.exe -m pytest tests\test_procedure_inheritance.py -q
```

`CONFIG.json` / `FREEZE.json` (pre-registered decision rule), `RUN/eval` (streams with full query logs and plan artifacts, models), `RUN/LEDGER.json`, `RUN/RESOURCES.json`, `SUMMARY.json`, `POSTHOC.json`,
`PRESERVED_BEFORE.json` (the four predecessor packages, 632 files, unchanged). The run refuses to overwrite completed stages. No API, no commit, no purchase, no external contact.
