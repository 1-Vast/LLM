# Block P feasibility (exploratory, before the freeze)

Every number here comes from **already exposed** units: the 1,403 block-N compounds (block N ran its
confirmation on 421 of them on 2026-10-10, so all are exposed). Nothing in this folder reads the
975-compound sealed tier. These are development results used to choose the task, the endpoint, the
world model and the registered geometry. They are not evidence for any claim.

Scripts write their own JSON next to them; `*_rows.csv` holds the per-campaign rows.

## F0 - does the campaign task have headroom? (`f0_headroom.py`)

5 seeds x 14 lineages, pool 30% of 1,403, budget 10% of pool, kNN-5 transfer of lineage
selectivity.

| arm | hits found (of 268 reachable) |
|---|---|
| random | 20 |
| chemistry kNN, one batch | 125 |
| target kNN, one batch | 150 |
| L1000 (18 options), one batch | 166 |
| annotated class mean | 162 |
| oracle | 268 |

* Transcriptional transfer beats random by +93 [+46, +145] hits and is comparable to annotation.
* In-campaign feedback (refit the transfer on screened compounds) adds +13 [+3, +24] with the
  transcriptional kernel and +8 [+2, +17] with chemistry; the interaction is +5 [-4, +14].
* The 18-option GSE92742 kernel beats the 5 shared options by +53 [+19, +92], so the panel breadth
  matters.
* **Endpoint check.** Hits replicate on the independent PRISM secondary screen (different plates,
  dose response) in 60-100% of cases per lineage, against 1-26% for non-hits; primary and secondary
  selectivity correlate at r 0.37-0.67.

Decision: the task has headroom and the endpoint is measurable twice. Continue.

## F1 - which transcriptional kernel for phase-2 compounds? (`f1_kernels.py`)

542 block-N compounds that also have GSE70138 signatures, leave-one-out.

| kernel | selective r (killers) | hit AUROC | top-1% precision |
|---|---|---|---|
| GSE70138, all 7 lines x 6 doses, concatenated | 0.238 | **0.928** | 0.373 |
| GSE70138, 10 uM only, mean cosine | 0.223 | 0.915 | 0.360 |
| GSE70138, 1.11-10 uM, mean cosine | 0.241 | 0.906 | 0.400 |
| block N's own GSE92742 18-option kernel | 0.209 | 0.912 | 0.453 |
| cross-dataset (GSE70138 query vs GSE92742 reference, 5 shared lines) | 0.182 | 0.773 | 0.240 |
| generic profile only | - | 0.690 | 0.053 |

* The native phase-2 kernel reproduces block N's transfer quality on a different L1000 release,
  which is independent support for the promoted `transcriptional_transfer`.
* **The cross-release bridge is weak.** A compound's own GSE92742 signature is the single nearest
  GSE92742 reference for its GSE70138 signature only 11.6% of the time (median rank 238 of 1,403;
  median self-cosine 0.082).
* Consequence, and the reason this task is interesting: for a new compound the same-platform
  reference library is small (542 compounds), and **every compound a campaign screens enlarges it**.

Decision: `vc_native` = concatenated-cell cosine on GSE70138; `vc_cross` kept as a weak second
source; pool compounds never act as GSE92742 references.

## F2 - system-level arms on development campaigns (`f2_campaigns.py`)

3 seeds x 14 lineages; pool 60% of the 542 phase-2 compounds; reference = every other block-N
compound; budget 10% (32 screens), batch 6. Stacked logistic hit model over per-source
(selectivity, lineage mean, top similarity, missing) features plus lineage intercepts.

| arm | hits (of 158) |
|---|---|
| random | 22 |
| fixed class mean | 114 |
| virtual cell alone, one batch | 107 |
| no-virtual-cell stack, one batch | 122 |
| full stack, one batch | 128 |
| full stack, feedback (refit) | 129 |
| full stack, feedback (features only) | 131 |
| oracle | 158 |

Contrasts (lineage-cluster bootstrap, 4,000 draws):
* virtual cell's contribution inside the loop: **+10 [+2, +19]**;
* feedback within the virtual-cell-only stack: **+9 [+2, +17]**;
* feedback within the full stack: +1 [-4, +5]; without the virtual cell: -3 [-6, 0];
* feedback x virtual-cell interaction: +4 [-1, +9] (**not established**);
* full stack vs fixed class mean: +15 [+5, +27];
* full stack vs the better single core: -4 [-18, +9] (**not established**).

Per lineage the two cores disagree: the virtual cell wins for skin (24 vs 19), gastric (11 vs 8)
and uterus (10 vs 8), and loses for esophagus (9 vs 17) and upper aerodigestive (20 vs 29).

## F3/F8 - budget curve and the unexpected-hit endpoint (`f3_orders.py`, `f8_unexpected.py`)

5 seeds x 14 lineages, selection orders recorded to 10% of the pool. An **unexpected** hit is a hit
whose annotated mechanism class has no selective member for that lineage among the reference
compounds: what an annotation lookup cannot anticipate.

Totals at each budget (of 285 reachable hits, 99 of them unexpected):

| arm | hits @1% | @5% | @10% | unexpected @1% | @5% | @10% |
|---|---|---|---|---|---|---|
| fixed class mean | 57 | 158 | 207 | 2 | 14 | 34 |
| no-virtual-cell stack, refit | **69** | **193** | 217 | 4 | 33 | 44 |
| virtual cell alone, refit | 39 | 131 | 195 | 6 | 39 | 53 |
| full stack, refit | 65 | 189 | **236** | 3 | 29 | **57** |
| virtual cell alone, one batch | 39 | 128 | 189 | 6 | 41 | **60** |
| oracle | 127 | 285 | 285 | 37 | 99 | 99 |

* **For total hits, annotation knowledge is the strong core**, especially at small budgets
  (at 5%, the virtual cell alone loses 56 [5, 118] hits to the no-virtual-cell stack).
* **For unexpected hits the virtual cell is the source of value.** At 10% the full stack finds
  **+13 [+3, +25]** more unexpected hits than the same agent without it, and +23 [+10, +40] more
  than the fixed workflow.
* Replication on the secondary screen tracks total hits (the full stack's +24 [+3, +45] over fixed).
* **A negative worth keeping:** within the virtual-cell-only arm, feedback *reduces* unexpected hits
  at 10% (-7 [-14, -2]). Refitting on what was screened pulls the ranking back toward classes that
  are already known to work.

Decision: the registered primary endpoint is **unexpected hits**, with total hits and
secondary-replicated hits as co-registered secondaries, at a 10% budget.

## F4 - why does the virtual cell's value depend on the lineage? (`f4_context_match.py`)

Hypothesis: transfer works for a lineage when the L1000 panel contains a context sharing its
vulnerability (A375 is BRAF-mutant melanoma; the panel has no squamous line).

Per-lineage hit AUROC of single-line kernels: refuted. YAPC (pancreatic) is the best single line for
skin (0.915 against A375's 0.778), and MCF7 is the best for gastric and upper aerodigestive. The
all-line kernel is at or near the best everywhere. Panel composition does not explain the pattern,
so any arbitration must be learned rather than assigned from panel identity.

## F5 - learned per-lineage arbitration (`f5_arbitration.py`) - REJECTED

F2 showed the two cores win on different lineages, and choosing the better model per lineage in
hindsight would give 140 hits against the pooled stack's 129. Three arbiters were tried over the
model families {virtual cell, no-virtual-cell, all}, on the same campaigns:

| arm | hits (of 158) |
|---|---|
| pooled stack, refit (F2's `refit_all`) | **129** |
| lineage-specific source weights (L2-shrunk interactions) | 124 |
| weights from out-of-fold reference log-likelihood | 126 |
| the same, updated by prequential campaign log-likelihood | 125 |
| hindsight best of the three families | 140 |
| oracle | 158 |

* Every arbiter *loses*: -3 [-11, +4], -4 [-12, +3] and -5 [-13, +3]. None is established as
  different from the pooled stack, and none captures the +11 hindsight headroom.
* **Diagnosed cause.** The reference log-likelihood is far too sharp, so the mixture collapses onto
  one family (skin: weights 0.999/0.001/0.000 for vc/novc/all; esophagus: 0.000/0.439/0.561). The
  arbiter therefore inherits one family's weaknesses instead of blending. The pooled stack already
  blends at the feature level, which works better.
* A likelihood temperature would soften this, but it is a knob that would be fitted on development
  data for a gain the data do not establish.

Decision: arbitration is **not** part of the registered design. The pooled stack is the world model.

## F6 - is the LLM lineage prior informative? (`f6_llm_prior.py`)

One deepseek-flash call per compound (name, mechanism, targets, phase, indication; never an
outcome), returning P(selective hit) for each of the 14 lineages. 2,378 compounds, 0 failures, 0
truncations.

| predictor | hit AUROC | average precision |
|---|---|---|
| LLM prior | 0.762 | 0.044 |
| leave-one-out class-mean selectivity | **0.868** | **0.232** |
| base rate | - | 0.0096 |

* The prior is informative but weaker than an annotation lookup, and far weaker in precision.
* It is well scaled: mean predicted probability 0.0069 against an observed rate 0.0096.
* **No memorisation detected.** On the 540 compounds also run with the name withheld, named AUROC
  0.803 against masked 0.792, and masked average precision is *higher* (0.100 against 0.083). The
  prior comes from mechanism and target annotation, not from recalling PRISM.

## F7 - the LLM prior inside the loop (`f7_llm_in_loop.py`)

Same campaigns as F2, prior added as a stacked feature (weight learned from evidence).

* Added to the full stack: **+2 [-3, +9]** - null.
* Added to the agent without the virtual cell: **0 [-6, +5]** - null.
* One batch, no feedback: +1 [-2, +4] - null.
* The virtual cell's contribution *given* the prior: **+12 [+3, +23]**.
* The learned logit weight is positive and stable (0.52-0.61), so the stack does use it; it simply
  does not change which compounds are screened.

Consistent with blocks M and N: literature-grounded LLM knowledge adds nothing beyond annotation on
this task family, while the virtual cell does.

## F9 - power rehearsal at the confirmation geometry (`f9_power.py`)

The confirmation tier holds 975 new compounds. F9 rehearses the two candidate geometries on
development compounds at batch 5, budget 10%, using a **pooled-stack loop with no explore stream** -
which is exactly the configuration later registered as the primary agent (`explore_seats = 0`), and
with a clean comparator in both arms.

| geometry | campaigns | virtual cell's contribution to unexpected hits | agent's contribution to hits | vs fixed, unexpected |
|---|---|---|---|---|
| 5 libraries x 195 | 40 | +4 [+0, +9] | +24 [+8, +43] | +13 [+4, +24] |
| **3 libraries x 325** | 31 | **+7 [+1, +14]** | +23 [+1, +47] | +15 [+5, +27] |

* Both geometries give the same qualitative answer; the larger library is better on the primary
  endpoint, because a 10% budget of 32 screens reaches deeper into a richer pool.
* Nominal intervals only. A family-wise bootstrap widening would erase +7 [+1, +14]; that is why the
  registered verdict rule is the exact cluster sign-flip test, under which this effect reaches
  `p = 0.016`.

Decision: 3 disjoint libraries of 325 compounds, batch 5. Together with F8 (+13 [+3, +25], 5 seeds,
batch 6, no LLM prior in either arm), F9 is the rehearsal the registered H1 prediction rests on.

## F12 - budget sensitivity, disclosed but not used to choose (`f12_budget_power.py`)

The two primary contrasts at budget fractions 10%, 20% and 30% of a 325-compound library, with
screens and rounds so a larger budget is not treated as free.

**This sweep does not select the registered budget.** The registered value is 10%, inherited from
every experiment F0-F11; picking the fraction that maximises the effect would be exactly the
threshold-shopping the project's standards forbid. F12 ran alongside the freeze and its three
output files are listed in `FREEZE.json` under `pending_excluded`, with that reason, so a later hash
check does not read a legitimate late write as tampering.

**What F12 is, and is not, evidence about.** F12 is the only development script that drives
`maestro_agent.Maestro`, and it ran with `explore_seats = 2` and the *pre-fix* explore ranking, so
its `agent_novc` kept virtual-cell access in 2 of 5 seats per batch. Its virtual-cell contrast
(+2 [0, +5] at 10%, +3 at 20%, +0 at 30%) is therefore a **contaminated rehearsal of the secondary
arm A7**, not an estimate of the registered H1. Replaying three campaigns with the explore ranking
forced each way reproduced F9's recorded rows with own-source explore (9, 3, 7 hits) and F12's with
virtual-cell explore (7, 4, 6), which is what identified the cause; the arms are deterministic
within a process. Entry P6 of `DEVIATIONS.json` records the investigation, and the earlier,
mistaken note in P1 is marked corrected rather than edited away.

Its genuine lesson is about **budget**, and it is a caution: at 20% and 30% of the library every arm
converges toward the reachable ceiling (maestro 151 of 161 hits at 30%), so all contrasts shrink to
nothing. A deep screen needs no planner. The interesting regime is the shallow one.

## F10 - is the endpoint gameable, and does a two-stream portfolio help? (`f10_portfolio.py`)

5 seeds x 14 lineages, pool 60% of the phase-2 compounds, budget 10%, batch 6. 285 reachable hits,
99 of them unexpected.

| arm | hits | unexpected | secondary-replicated |
|---|---|---|---|
| pooled stack, refit (the baseline) | **238** | 57 | **191** |
| candidates restricted to novel classes, ranked by the virtual cell | 63 | **63** | 44 |
| the same restriction, ranked by the full stack | 63 | 63 | 43 |
| portfolio, half the batch to each stream | 229 | 60 | 189 |
| portfolio, seats moved by observed yield | 233 | 60 | 190 |

* **The endpoint is not gameable.** The trivial policy that buys only novel-class compounds gains
  nothing reliable on the primary endpoint (+6 [-7, +21]) while losing almost three quarters of
  total hits (-175 [-270, -91]) and of replicated hits (-147 [-238, -69]). With the registered
  non-inferiority requirement on total hits (H6) such a policy cannot produce a confirmed result.
  The pooled stack already finds the unexpected hits that are findable.
* **The portfolio does not help.** Both variants are within noise on unexpected hits
  (+3 [-10, +20] fixed, +3 [-4, +12] adaptive) and slightly worse on total hits.

Decision: the primary agent carries **no** explore stream. The two-stream variant is registered as
the secondary arm `maestro_explore` with its own hypothesis (H9, predicted NOT_SUPPORTED), so a
component this block built and does not believe in is still tested on sealed data.

## F13 - is the unexpected-hit definition sound? (`f13_novelty_definition.py`)

The registered definition uses the **exact** Repurposing Hub mechanism string. Hub strings are
comma-separated token lists, so string equality could call a hit novel while a known hit shares one
of its tokens. Four nested definitions, on the 5 development seeds (99 reachable unexpected hits):

| definition | reachable unexpected hits |
|---|---|
| no reference hit shares the exact mechanism string (**registered**) | 99 |
| no reference hit shares **any** mechanism token | 99 |
| ... and none shares an annotated target | 85 |
| ... and none is within Morgan Tanimoto 0.4 | 83 |

* The string and token definitions **coincide exactly**, so the multi-token worry is empty on this
  data: no hit is novel by string while sharing a token with a known hit.
* Requiring no shared annotated target as well removes 14 of 99 (14%); adding chemical
  dissimilarity removes 2 more.

Decision: keep the registered string definition, and report the strictest count
(`token_target_chem`) as a descriptive alongside it, so a reader can see the claim at both
strictnesses.

## Scripts written but not run

* `f11_agent.py`: a development rehearsal of the assembled agent at batch 5. Superseded once F10
  moved the registered agent to `explore_seats = 0`, a configuration for which F3/F8 already give an
  uncontaminated rehearsal (the pooled refit stack against the same stack with no virtual-cell
  source: +13 [+3, +25] unexpected hits at a 10% budget). Kept in the frozen packet, with
  `DEVIATIONS.json` entry P5, so the record shows what was built and not used.

## Decisions carried into the protocol

1. **Task:** lineage-selective killing campaigns, 3 disjoint libraries of 325 new compounds, budget
   10% of the library (33 screens), batch 5.
2. **Primary endpoint:** unexpected hits (validated against stricter definitions in F13, and shown
   not to be gameable in F10). Secondaries: total hits, secondary-screen-verified hits.
3. **World model:** one pooled stacked hit model over `vc_native`, `vc_cross`, `klass`, `target`,
   `chem`, with the LLM prior as a gated feature. Per-lineage arbitration rejected (F5).
4. **Agent:** persistent state, refit every round, named refusals, verification that never feeds
   selection, parameter-free stopping. **No explore stream** (F10); the two-stream variant is a
   declared secondary arm.
5. **Registered arms:** fixed workflow, deterministic adaptive planner, agent without the virtual
   cell, virtual cell without the agent, conventional LLM-agent-with-tool, the proposed system, its
   two-stream variant, permutation twins, random zero arm, oracle bound.
6. **Verdict rule:** exact cluster sign-flip test over the 14 lineages, Bonferroni within each
   family; the cluster bootstrap interval reported as the effect size. Chosen because 14 clusters
   make the interval the weaker instrument.
7. **Known risks stated in advance:** total hits are near the annotation ceiling at a 10% budget;
   feedback reduced unexpected hits in the virtual-cell-only arm (-7 [-14, -2]); the design needs at
   least 6 consistently positive lineages to reach `p <= 0.025`; and the world model
   **over-forecasts** its own yield (about 3.9 expected against 1-2 realised hits per batch of 5),
   so the stopping rule is expected to fire rarely.
