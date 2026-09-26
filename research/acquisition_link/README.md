# The link from world-model prediction to measurement choice

Does anything the world model produces change which measurement MAESTRO buys, in a way that
separates the competing hypotheses better while keeping wrong eliminations, uncertainty and cost
under control? This directory holds the 2026-09-26 audit of that link, the repair, and its
pre-registered evaluation on the block-2 SciPlex3 episodes (`../dynamic_world_model/`).

## 1. Answer in one paragraph

**The link was broken in two places and missing in a third.**
- **Discarded.** The production controller (`from_workspace`, the CLI and the public loop)
  selects on the power-aware path. There it computed the virtual cell's per-action priorities and
  only logged them.
- **Borrowed.** A per-action query stated the template's exposure time, so a 72 h action was
  ranked by a 24 h prediction.
- **Missing.** No runtime object could carry "how would this measurement read under each
  hypothesis". Scenario cards had that distribution, but the selector interface reduced it to one
  detection probability, which drops the wrong-elimination risk. A thinly supported card deleted
  its action from the objective instead of being discounted.

**The repair** adds a distribution-aware selector (`maestro.acquisition.select_discriminating_action`)
and wires it into the orchestrator: opt-in, logged in shadow otherwise. It also stops per-action
queries from borrowing another condition.

**Evaluated on the 2,496 block-2 episodes under a protocol frozen beforehand**, the repaired
selector made neither more nor fewer correct decisions than the magnitude tie-break:
- tier B: −0.019 [−0.053, +0.017];
- tier A: +0.033 [−0.030, +0.089].

Its forecasts are well calibrated (ECE 0.058 and 0.085, against 0.101 and 0.154 for block 2's
cards), and the non-biological control collapses (−0.244 in tier B). The pre-registered verdict is
**INCONCLUSIVE**, so the selector stays opt-in.

**The magnitude tie-break, wired into the power-aware path,** raised utility strongly in tier B
(+0.298 [+0.205, +0.388]) but not significantly in tier A (+0.060 [−0.086, +0.199]), and it raised
tier-B wrong eliminations by 0.044. It failed its frozen keep rule and is not enabled.

**A fixed "24 h then 72 h" sequence** still beats every selector in tier A (+0.211 correct over the
repair).

## 2. What was suspected, and what the code actually does

The task brief listed six suspicions. Each was tested against the code, not assumed:

| Suspicion | Verdict | Evidence |
|---|---|---|
| Profile prediction → magnitude/p_correct → expected coverage → measurement | **True, and worse on the production path**: magnitude does not even reach it | `agent/orchestrator.py` `_select_budgeted_actions`: power-aware branch called `select_expected_coverage` without the priorities; probe P1 |
| Cards hold p_correct, p_wrong, p_ambiguous, p_undetected, references, epistemic interval | True (research only; no runtime type could hold them) | `research/dynamic_world_model/common.py` `card` |
| The selector reduces them to p_correct / detection power | True | `episodes.select_by_cards`; probe P2 chose a card with p_wrong 0.3 over p_wrong 0 |
| Dynamic priorities computed but ignored by the power-aware path | True | probe P1: swapping predictions leaves the power-aware choice unchanged |
| Supported 72 h measurements rejected before selection | **Partly**: never rejected. The served rung refuses 72 h correctly, but the per-action query stated 24 h and lent the 72 h action the 24 h answer, and cost is compared before any prediction | `_build_action_prediction_requests`; probes P4, P5 |
| A hard minimum-reference rule removes informative low-support actions | True | a refused card sets `distinguishes=()`; block-2 audit: 550 of 2,616 tier-A menu actions refused, 13.6% of them would have resolved correctly |

One break the brief did not list: `dyn_model`'s forecast card stored P(any elimination) under
the key `p_correct` with `p_wrong` absent. Wrong eliminations therefore counted as successes.
Post hoc, from block-2 records: the 234 step-2 choices it drove had a wrong share among
eliminations of 0.26, against 0.09 for `dyn_ref`.

## 3. Runtime data flow

**Before**

```
EvidenceAction (declared: cost, distinguishes, detection_power, time_hours, execution_context)
  -> VirtualCellQueryTemplate.build(label)            # time, dose, context from the TEMPLATE
  -> StatePrediction [predicted, hypothesis-agnostic: state_change[readout], intervals]
  -> _prediction_action_priorities: |change| x relevance x reliability      # magnitude only
  -> power_aware (production): select_expected_coverage(detection_power -> cost -> size -> id)
                               priorities LOGGED ONLY
     budgeted (non-default):   BudgetedEvidenceSelector(coverage -> cost -> size -> priority -> id)
  [research] card: per-hypothesis branches, references, interval
     -> select_by_cards: detection_power := pooled p_correct     # p_wrong, support, interval dropped
     -> refused card (< 2 references): distinguishes=()          # action leaves the objective
  -> selected action -> CaseStore (awaiting_result) -> real MeasurementResult
  -> InterpretationTable -> admit_evidence -> EvidenceState.apply (only real, qualified,
     mechanism-scope readings eliminate; absence at implementation scope; QC failure named)
```

**After**

```
EvidenceAction
  -> template.build(label, time_hours=action.time_hours when the template states time)
     action declared in another context: no query (named reason, no borrowed answer)
  -> StatePrediction -> priorities; a request stating another time/context ranks nothing
  -> OutcomeForecaster.forecast(contrast, actions, evidence)        # per action, per hypothesis
     OutcomeForecast: P(label | H, action) over REGISTERED outcome labels + support (units)
  -> outcome_consequences(registered rules): label -> what it would eliminate
  -> select_discriminating_action (lexicographic):
       legal/affordable/forecast usable (0 support -> named refusal)
       wrong-risk gate: P(correct) > 2 x P(wrong), Jeffreys-shrunk        # declared +1/-2 utility
       max one-sided 95% lower bound of D = P(correct) - P(wrong)
       then support -> cost -> exposure time -> magnitude -> identifier
  -> logged every round ("discrimination_selection_computed"); drives the round only with
     discrimination_selection=True, else the coverage choice stands (shadow)
  -> no admissible action with the flag on: the case is deferred with a named reason
  -> evidence path unchanged
```

Only three things touch belief: a real measurement, a matching registered rule, and
mechanism-contrast scope. A forecast, a card, a priority or a selector output never reaches
`EvidenceState`.

## 4. The acquisition objective and why it is not a divergence

For each candidate action a and hypothesis H:
- a forecast gives P(y | H, a) over the registered outcome labels y;
- the registered rules say which hypotheses each y removes;
- P(correct | H, a) is the mass on labels that remove a candidate other than H and not H;
- P(wrong | H, a) is the mass on labels that remove H;
- D(a) = mean over H of [P(correct | H) − P(wrong | H)], with a uniform prior over the candidates.

D is the rule-conditioned discrimination: how often the rules MAESTRO will actually apply would
eliminate in the right direction, minus the wrong direction. For two hypotheses, D is bounded by
the total variation distance between the two outcome distributions. The two are equal only when
the registered reading is the Bayes-optimal one.

Total variation, Jensen-Shannon and information gain were rejected. They credit differences the
rules cannot act on. "Undetected under H1, unresolved under H2" has TV 1 and D 0, and acting on
it would mean reading absence as evidence. On the served tier-A menu the mean TV was 0.354 and the
mean D was 0.159. Most of the distributional difference is not something a measurement could
turn into a lawful elimination.

**Uncertainty.** Each branch is a Dirichlet posterior with the Jeffreys prior (½ per registered
label), using pseudo-counts equal to probability × support. Support is the count of independent
measured units, never simulation draws. The ranking key is the one-sided 95% lower bound of D
(normal approximation to the Dirichlet variance), so thin support widens the interval and
lowers the key without deleting the action.

**Wrong risk.** An action is admissible only if its shrunk P(correct) exceeds 2 × P(wrong).
That is the break-even of the declared utility (+1 correct, −2 wrong), not a tuned constant.
When no reference reading ever eliminated correctly, the refusal is named
`no_reference_reading_eliminates_correctly`; otherwise it is named
`wrong_elimination_risk_not_below_break_even`.

**Support rule.** Zero references means a named refusal (`no_reference_for_hypothesis:<H>`).
One reference is served, flagged `low_support`, and shrunk hard: a single correct reading gives
P(correct) 0.5, not 1. Two or more are served normally.

**Time and dose.** The forecaster scores each (line, time, dose) condition on its own
references, so a 72 h action competes with 24 h actions on discrimination before cost. Unsupported
conditions are refused by name (`condition_not_in_reference_data:...`). No measurement is
synthesised for them.

## 5. Methods borrowed from other fields

| Method (source domain) | Mapping in MAESTRO | What it fixes | Assumptions it needs, and whether MAESTRO meets them | Smallest form used | Simpler alternative considered; not imported |
|---|---|---|---|---|---|
| Design for model discrimination: Hunter & Reiner 1965; Box & Hill 1967; Atkinson & Fedorov 1975 (optimal experimental design) | Hypotheses are rival models; an action is a design point; choose where their predicted readings differ | Magnitude trap | Needs a predictive distribution per rival model (yes: reference branches) and a reading the decision uses. MAESTRO's reading is fixed, so the difference must be taken through it | D: correct minus wrong elimination probability under the registered rules | T-optimality on raw profiles, JS divergence and total variation all reward differences the rules cannot act on |
| Query by committee: Seung, Opper & Sompolinsky 1992 (active learning, NLP) | Hypotheses are the committee; ask where their predicted readings disagree | Chooses informative queries without a single model's confidence | Committee members must be distinct predictors (yes: one branch per hypothesis) | Disagreement enters only through D | Vote entropy, which again counts disagreement the rules cannot act on |
| Chance-constrained / risk-sensitive planning: Blackmore, Ono & Williams 2011 (robotics) | A wrong elimination is the "collision"; constrain it, then optimise | Lets wrong-elimination risk dominate magnitude | Needs a risk estimate per action (yes: P(wrong)) and a declared tolerance (yes: the utility's break-even) | Lexicographic gate before ranking | A weighted score with a tuned λ; rejected as opaque |
| Pessimism under uncertainty / lower confidence bounds; the Jeffreys interval (Brown, Cai & DasGupta 2001) (safe bandits, offline RL) | Rank by the lower bound of D; the reference count sets the width | Thin support is discounted, not deleted | Needs independent units for the variance: references are independent compounds; the leave-one-out bias remains (section 8) | Dirichlet(½) posterior, one-sided 95% normal bound | A hard minimum count, block 2's rule, which deleted the resolvers |
| Selective prediction / reject option: Chow 1970; El-Yaniv & Wiener 2010 (ML, NLP) | Defer when no action is admissible, with a named reason | Refusal becomes a stated outcome, not a silent empty plan | A calibrated risk estimate: served ECE was 0.058 and 0.085 here | `no_admissible_action` status and a named case deferral | Always measuring the cheapest action; that is the old empty-objective behaviour |
| Next-best-view with replanning: Connolly 1985 (active perception, computer vision) | One measurement per round, replanned on the real result | Avoids pretending that two readings of one compound are independent trials | Needs a closed loop: the case loop already replans | One action per round | Bundle selection with an independence assumption (expected coverage); not imported for forecasts |

**Also not imported:**
- Full belief-space POMDP planning, and entropy-based information gain. MAESTRO's belief is a
  compatible set, not a posterior, and outcomes of different actions on one compound are
  correlated and unmodelled.
- Gaussian-process mutual-information sensor placement (Krause, Singh & Guestrin 2008). It needs
  a joint model this study does not have.

## 6. Regression tests and counterexamples

`tests/test_discriminating_acquisition.py` (19 tests, in the repository suite):

| Test | Old behaviour |
|---|---|
| Magnitude trap: a loud, non-separating action loses to a quiet, separating one | The legacy selector chose the loud one (asserted in the same test) |
| Late resolver: a costlier 72 h action that alone separates is chosen; unaffordable means a named `no_admissible_action` | Cost order chose 24 h |
| Wrong risk: equal P(correct), higher P(wrong) loses; a mild risk below break-even stays admissible | Reduced to detection power, the label decided |
| Zero references and a missing branch refuse by name; an unforecast action is named | A refused card vanished |
| One reference is served, flagged, shrunk to 0.5 and discounted, and still chosen over a non-separating action | Deleted |
| Absence is never credited (TV 0.71, D 0); a forecast cannot declare what a label eliminates | No such layer |
| Prediction-derived records and failed QC never eliminate; QC failure puts the case in `result_qc_failed` | Unchanged (pinned) |
| Deterministic ties; a rerun and an input-order change give an identical plan; magnitude breaks only exact ties, after cost | — |
| Runtime: with power-aware selection on, changing only the outcome forecasts changes the chosen action; nothing else about the case changes | TypeError: the capability did not exist |
| Runtime: forecasts are logged in shadow unless enabled; enabling without a forecaster is refused | — |
| Runtime: magnitude alone does not move the power-aware choice (its keep rule was not met) and breaks only exact forecast ties | Before: ignored silently; now: ignored and logged as unused |
| Runtime: a 72 h action is queried at 72 h and refused by name; it gets no borrowed priority | Queried at 24 h, took the 24 h priority |
| Runtime: an action declared in another context is not queried with the template's context, and the skip is logged by name | Queried as if in the template's context |

The new test file failed at import on the old code, because the interface did not exist.
`falsify.py --label before` reproduces each behavioural failure through the old API only.
`--label after` shows the query-time repair and records that power-aware magnitude stays unused
by design.

`research/acquisition_link/test_acquisition_link.py` (4 tests, outside the repository suite):
- forecast consequences equal what `common.evidence_update` removes;
- SciPlex3 branches stay whole, and the support rules differ only at one reference;
- the forecaster satisfies the runtime protocol;
- a rerun of one fold reproduces the recorded episodes and menu rows exactly.

**Suite totals:** baseline 1301 passed; after the repair 1320 passed.

## 7. Results

Pre-registered protocol: [`PROTOCOL.md`](PROTOCOL.md), frozen 18:59:44 before any episode with the
new selector. The report is generated by `analyze.py` into
`outputs/acquisition_link_20260926/analysis/report.md` and copied to
`log/20260926/0926/acquisition_link_report.md`.

All seven code-path consistency checks passed:
- `production_before` equals `cost_only`;
- `production_after` equals `magnitude`;
- `ec_cards_2ref`, `fixed`, `oracle`, `magnitude` and `cost_only` equal block 2's arms, episode
  for episode.

**Registered decision metrics.** Budget: two measurements. Held out: compounds by skeleton fold
in lines seen in training, so this is not an unseen-context test. Intervals are 95%
skeleton-clustered.

| Tier | Arm | Correct | Wrong | Deferred | Utility | Regret | Days | Wells |
|---|---|---|---|---:|---|---|---:|---:|
| B (2,160) | oracle | 0.668 | 0.000 | 0.332 | 0.668 | 0 | 4.0 | 4.0 |
| B | **da** (repair) | 0.539 [0.471, 0.607] | 0.038 | 0.074 | 0.463 [0.387, 0.543] | 0.205 | 7.8 | 7.5 |
| B | ec_cards_1ref | 0.548 | 0.040 | 0.050 | 0.469 | 0.200 | 8.1 | 7.7 |
| B | ec_cards_2ref (block-2 separation) | 0.514 | 0.033 | 0.132 | 0.447 | 0.221 | 7.4 | 7.0 |
| B | magnitude = production_after | 0.558 [0.484, 0.631] | 0.050 | 0 | 0.458 [0.362, 0.547] | 0.210 | 8.9 | 8.7 |
| B | cost_only = production_before | 0.172 | 0.006 | 0 | 0.160 | 0.508 | 11.3 | 7.8 |
| B | fixed | 0.582 | 0.049 | 0 | 0.485 | 0.183 | 9.1 | 9.1 |
| A (336) | oracle | 0.670 | 0.000 | 0.330 | 0.670 | 0 | 4.5 | 4.0 |
| A | **da** (repair) | 0.429 [0.304, 0.554] | 0.039 | 0.179 | 0.351 [0.202, 0.497] | 0.318 | 7.9 | 6.1 |
| A | ec_cards_1ref | 0.500 | 0.051 | 0.164 | 0.399 | 0.271 | 8.9 | 6.5 |
| A | ec_cards_2ref (block-2 separation) | 0.455 | 0.051 | 0.223 | 0.354 | 0.315 | 8.2 | 6.0 |
| A | magnitude = production_after | 0.396 [0.262, 0.536] | 0.021 | 0 | 0.354 [0.208, 0.500] | 0.315 | 9.8 | 7.3 |
| A | cost_only = production_before | 0.301 | 0.003 | 0 | 0.295 | 0.375 | 10.6 | 7.5 |
| A | fixed (24 h then 72 h) | 0.640 | 0.057 | 0 | 0.527 | 0.143 | 11.0 | 9.8 |

**Registered contrasts (paired, correct-decision rate unless stated).**

**P-A: da − magnitude** (the classification turns on this):

| Measure | Tier B | Tier A |
|---|---|---|
| Correct | −0.019 [−0.053, +0.017] | +0.033 [−0.030, +0.089] |
| Wrong eliminations | −0.012 [−0.026, +0.000] | +0.018 [−0.006, +0.048] |
| Utility | +0.006 [−0.041, +0.054] | −0.003 [−0.098, +0.080] |

**S1: production_after − production_before** (the wiring repair):

| Measure | Tier B | Tier A |
|---|---|---|
| Correct | +0.386 [+0.309, +0.463] | +0.095 [−0.033, +0.220] |
| Utility | +0.298 [+0.205, +0.388] | +0.060 [−0.086, +0.199] |
| Wrong eliminations | +0.044 [+0.026, +0.064] | +0.018 [−0.003, +0.048] |

**S2: the selector and support effects, isolated:**

| Contrast | Tier B | Tier A |
|---|---|---|
| Selector effect, `da` − `ec_cards_1ref` (same forecasts) | −0.009 [−0.019, +0.002] | **−0.071 [−0.131, −0.021]** |
| Selector effect under v1, `da_2ref` − `ec_cards_2ref` | −0.009 [−0.019, +0.000] | −0.060 [−0.119, −0.009] |
| Support effect, `da` − `da_2ref` | **+0.035 [+0.023, +0.048]** | **+0.033 [+0.012, +0.057]** |
| Support effect, `ec_cards_1ref` − `ec_cards_2ref` | +0.034 [+0.022, +0.048] | +0.045 [+0.018, +0.074] |

**S3–S6:**

| Contrast | Tier B | Tier A |
|---|---|---|
| S3: da − ec_cards_2ref | +0.025 [+0.010, +0.042] | −0.027 [−0.089, +0.030] |
| S4: da − fixed | — | **−0.211 [−0.321, −0.110]** (utility −0.176) |
| S5: da_permuted − magnitude | −0.244 [−0.292, −0.199] | −0.071 [−0.167, +0.027] |
| S5: da − da_permuted | +0.226 [+0.186, +0.264] | +0.104 [+0.024, +0.182] |
| S6: da_dynamic − da | −0.011 [−0.024, −0.000] | 0.000 [−0.045, +0.045] |

**Forecast calibration and uncertainty coverage (registered).**

| | Tier B | Tier A |
|---|---|---|
| v2 forecasts served | 99.8% of 25,920 step-1 menu rows | 100% of 2,688 |
| ECE | 0.058 | 0.085 |
| ECE on the true-hypothesis branch | 0.050 | 0.091 |
| Brier | 0.168 | 0.197 |
| Predicted P(correct), mean | 0.243 | 0.257 |
| Realised correct rate | 0.282 | 0.328 |

The forecasts still under-predict, which is the leave-one-out template bias. In every support
stratum of both tiers, the realised mean discrimination was at least the mean one-sided lower
bound. At one reference (tier A, n = 550) the forecasts predicted P(correct) 0.167 against a
realised 0.136; the Jeffreys prior did not over-credit single references.
- Admissible share of served forecasts: 57%.
- Gate refusals: `no_reference_reading_eliminates_correctly` 991 in tier A and 9,478 in tier B;
  `wrong_elimination_risk_not_below_break_even` 185 in A and 1,706 in B.

**Action distribution (registered).**

| Arm | Tier-A step 1 chose 72 h | 72 h after an undetected 24 h first step |
|---|---|---|
| `da` | 60 of 276 | 22 of 107 |
| `ec_cards_1ref` | 182 of 281 | — |
| `magnitude` | 0 of 336 | 0 of 168 |
| `da_dynamic` | — | 39 of 107 |
| `fixed` | — | 160 of 160 |

In tier B every arm stays at 24 h (no 72 h on the menu). `da` spreads over doses more than
`magnitude` does: 1,653 of its 2,001 first steps are at 10 µM, against 2,096 of 2,160 for
`magnitude`.

**Per class, tier A, da − magnitude:**
- BET +0.250 and Aurora +0.153 gained.
- DNA methyltransferase +0.062 and HDAC +0.038 gained a little.
- Histone methyltransferase lost −0.333 (3 compounds).

**Classification by the frozen rule: INCONCLUSIVE.**
- P-A excludes zero in neither tier, and both lower bounds sit below −0.02.
- Wrong eliminations stay within 0.02 in both tiers.
- No utility interval lies entirely below zero.
- The permuted control falls short.
- ECE is at most 0.10 in both tiers.

**Wiring repair: not kept.** Its tier-A utility interval includes zero. The orchestrator leaves
magnitude out of the power-aware path and logs `prediction_priorities_used: false`.

**Post hoc, labelled as such.** On the tier-A menu, 72 h conditions have a mean of 2.3 references
against 4.8 at 24 h. Their realised correct rate is higher (0.344 against 0.295), and so is their
wrong rate (0.036 against 0.007). The one-sided lower bound therefore steers the repaired selector
away from 72 h, which is exactly where slow mechanisms separate. That is the likely reason for the
selector effect of −0.071. Pessimism about thin support costs decisions here, because the thinly
measured condition is the informative one.

## 8. Registered, exploratory and post hoc

| Status | Findings |
|---|---|
| **Registered, on data seen in block 2** | Every number in section 7's tables, the verdict and the wiring decision. The support effect was anticipated from the block-2 card audit, so its confirmation is not independent. |
| **Exploratory** | The falsification probes; they use synthetic inputs and read no outcome. |
| **Post hoc** | The dyn_model wrong share (0.26); the 72 h support and risk profile; the mechanism behind the selector effect. |

**Not claimed:**
- that the selector improves decisions;
- that one-reference support generalises beyond SciPlex3;
- anything about unseen cell contexts or times;
- any biological mechanism from these data.

**Limitations:**
- The episodes are block 2's, so the design was informed by them and promotion is unavailable.
- Held-out compounds in seen lines, not unseen contexts.
- Only two time points, in one line.
- The forecasts inherit the leave-one-out bias: a reference sees one same-class template fewer
  than a held-out compound.
- The prior over hypotheses is uniform.
- One-step lookahead: the 24 h then 72 h sequence has value no single-step score sees, and the
  oracle regret of 0.32 in tier A shows how much is left.
- The normal approximation to the Dirichlet bound is rough at tiny counts; it is conservative on
  average here, but not guaranteed per action.

## 9. Blockers to resolving the question

**No independent data.** Every SciPlex3 episode with 72 h has now informed a design, so a real
answer needs a dataset this project has not analysed. It needs:
- several time points;
- mechanism labels;
- enough references per class and time to fit a branch.

Candidates:
- the L1000 `subset48` 6 h / 24 h pairs, after the Repurposing Hub mechanism join;
- a new time-course screen.

**Evaluate multi-step policies before any selector change.** Run a two-step
(non-myopic) discrimination policy and the bias-corrected forecasts against the fixed time
course on those data. The single-step objective cannot represent "measure now to learn when to
measure next".

## 10. Files and reproduction

| File | Role |
|---|---|
| `falsify.py` | Phase-B probes against the old or the repaired code (`--label before/after`) |
| `evaluate.py` | `ReferenceCardForecaster` (the SciPlex3 `OutcomeForecaster`) and all registered arms over block 2's episodes, plus the step-1 menu audit |
| `analyze.py` | Consistency checks, decision metrics, contrasts, calibration, distributions, the frozen verdict |
| `test_acquisition_link.py` | Harness invariants and a one-fold rerun |
| `PROTOCOL.md`, `protocol.json` | The frozen protocol |

```
python research/acquisition_link/falsify.py --label after
python research/acquisition_link/evaluate.py      # about 90 s on 10 processes; needs block 2's prepared data
python research/acquisition_link/analyze.py
python -m pytest -q research/acquisition_link/test_acquisition_link.py
python -m pytest -q tests/test_discriminating_acquisition.py
```

**Runtime use:**

```python
MAESTROOrchestrator(..., outcome_forecaster=forecaster, discrimination_selection=True)
```

Without the flag, the forecasts are only logged. No paid provider call was made for this block.
