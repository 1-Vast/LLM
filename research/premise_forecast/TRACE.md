# Premise-to-decision path: trace, missing connection, methods

**File summary**
- **Path:** `research/premise_forecast/TRACE.md`
- **Purpose:** step 1 of the 2026-09-27 block-5 brief. It traces the executed path from naming a missing premise to
  updating a mechanism claim, names the one connection that does not exist, and reviews outside methods only where
  they bear on that connection.
- **Core points:**
  - Premise identification, typed admission, set-based updates and licensing exist and are tested.
  - The repair operators value a premise measurement through **declared, deterministic** outcome templates.
  - The forecast-driven selectors value only **readouts** of a mechanism contrast.
  - Nothing computes P(premise-measurement result | mechanism hypothesis, context, history), so no forecast can
    reach a repair choice.
  - The data that forecast would need do not exist locally: census and E-CAL1 in [README.md](README.md).
- **Depends on:** `src/maestro/`, `src/evaluation/`, `research/belief_planning/`, `research/protocol_v2/`

Line numbers are from the working tree of 2026-09-27 18:50 (+0800), after another session's uncommitted
reorganisation moved `src/maestro/planning.py` to `research/belief_planning/planner.py`.

## 1. The executed path

| Stage | Production (`src/`) | Research | Consumes | Produces | Status |
|---|---|---|---|---|---|
| 1. Name the missing premise | `ContrastCheck.missing_prerequisites` (`maestro/contrast.py`); `PremiseRequirement.unmet_reasons` (`maestro/models.py:537`); replay: `PublicCase.missing_premises` (`evaluation/cases.py`) | - | typed premises, grants | named unmet premises with reasons (quantity, site, context, time) | **Exists**. Two latent gaps: E3 and E5, now reported (section 4) |
| 2. Choose a premise measurement | `_directed_prerequisite_repair` (`maestro/contrast.py:556`): most missing fields covered, then cost | `RegistryRepairRulePolicy` (`evaluation/proposal_arms.py:127`): a repair whose **declared** `expected_outcomes` separate the pair first; `RegistryExpandedSelectionPolicy` (`:198`) control; exact contingent optimum over declared outcomes (`evaluation/contingent.py:611`) | capability registry (`evaluation/capabilities.py:163`) | one proposal, compiled into an admitted action | **Exists without probabilities**: outcomes are declared per hypothesis, one outcome each |
| 3. Choose a readout | default `select_expected_coverage` (`maestro/acquisition.py:116`, detection power); opt-in `select_discriminating_action` (`:764`) with an `OutcomeForecaster`; virtual-cell priorities logged, not used | `plan_measurement` (`research/belief_planning/planner.py:158`); `ReferenceWorld.forecast` (`world.py:305`) | readout actions of a mechanism contrast | ranked readouts; contingent two-step plan (research) | **Exists for readouts only** |
| 4. Forecast contract | `OutcomeForecast` / `OutcomeBranch` (`maestro/acquisition.py:329-360`): per-hypothesis distribution over registered reading labels, including `quality_failed`; `support`; `basis`; `refusal`; `model_version`; always `MODEL_PREDICTION` | `ReferenceWorld` fills it for transcriptomic readouts | action, contrast, evidence | forecast or named refusal | **Exists**; missing fields: training and calibration version, condition match, direct or analogous support, extrapolation, contradicting observations |
| 5. Admit a real result | `InterpretationTable.interpret` (`maestro/outcome.py:373`), `admit_evidence` (`:205`): a model prediction or retrieved text never updates; QC failure and condition mismatch cannot eliminate | the protocol-v2 runner routes readings through the same table | observation record | typed interpretation | **Exists** (123 invariant tests, block 4) |
| 6. Update or defer | `EvidenceState.apply` (`maestro/outcome.py:296`), a set, not a posterior; `DecisionEngine.decide` (`maestro/decision.py:121-132`): a singleton needs a licence; an empty set is a contradiction | `contracts.score` joins truth after execution | evidence state, licensing evidence | licensed decision, deferral or contradiction | **Exists** |

## 2. The missing connection

A premise measurement has uncertain results, and their probabilities depend on which mechanism is true. Take the
engagement gap: under *insufficient functional perturbation* the drug is expected not to engage, and under *mode
non-equivalence* it is expected to engage. The value of buying the measurement is the expected utility of the
decision licensed after each result, minus cost and delay. Three facts block computing that today:

1. **No producer.** No code returns P(engaged, not engaged, QC-failed, uninterpretable | hypothesis, context,
   history) for a capability action. `RegistryRepairRulePolicy` reads one declared outcome per hypothesis
   (`pair.issubset(item.action.expected_outcomes)`). That is a noise-free template, so repair behaves as if the
   assay were perfect.
2. **No consumer.** `select_discriminating_action` and `plan_measurement` value readouts inside the current
   contrast. Neither takes a repair action. The one routine that does compute two-stage value (premise result, then
   licensed decision), the contingent optimum, takes declared outcomes, not distributions.
3. **No data to fit the producer.** The PISA release gives a vehicle-null false-positive rate (0.036, one-sided 95%
   upper bound 0.037) but **no sensitivity**, so P(not engaged | truly engaged) is unknown. Estimating P(result |
   hypothesis) needs reference cases whose premise state is known independently of the measurement, in the same
   context. The census finds **0** such target genes in every population (README section 3).

What exists and what is missing, for the smallest link:

| Needed for the link | Exists | Missing |
|---|---|---|
| Hypothesis-conditional distribution with refusal and support | `OutcomeForecast` | a forecaster for capability outcomes |
| Two-stage value (premise, then decision or follow-up readout) | exact contingent optimum over declared outcomes (`evaluation/contingent.py`); contingent plans in `plan_measurement` | probabilities in place of declared outcomes |
| Prediction-free fallback that keeps the experiment available | the declared-template rule (`RegistryRepairRulePolicy`) and fixed orders | - |
| Admission that a forecast can never eliminate | `InterpretationTable`, `EvidenceKind.MODEL_PREDICTION` | - |
| Calibration evidence on selected actions | E-CAL1 machinery (`research/protocol_v2/e_cal1.py`) | a calibrated forecaster: E-CAL1 FAILS (selected-step forecasts 2.0-2.1x too low) |
| A task to evaluate on | engagement_v1 (6 cases, 5 genes) | at least 30 target-gene clusters; 0 found |

## 3. Methods that address this connection

Only methods that value a measurement whose results are uncertain and hypothesis-dependent, or that decide when a
forecast may be trusted. "Fit" is judged against the facts above.

| Method | What it assumes | Fit here | Why |
|---|---|---|---|
| Value of information (Howard 1966) | a decision model and outcome probabilities | **Right objective; inputs missing** | The two-stage structure (the premise result changes which decision is licensed) is exactly a VOI problem. The contingent optimum already implements it over declared outcomes. What is missing is the probabilities (fact 3). |
| Bayesian experimental design, expected information gain (Lindley 1956; Rainforth et al. 2024) | a correct likelihood p(y \| theta, a) | **Fails without a likelihood** | EIG ranks designs by how much they would move a posterior. With a template in place of a likelihood it prefers whatever the template says separates, which is what repair already does. Information about the mechanism is also not the target: only decision-changing information counts (decision-focused VOI). |
| Decision-theoretic troubleshooting (Heckerman, Breese and Rommelse 1995) | a Bayesian network of faults with elicited probabilities; repair and observation actions with costs; myopic VOI | **Closest formal analogue** | "Measure the premise, act on the mechanism, or stop" is their repair-or-observe choice. Their probabilities are elicited from experts. Here any elicited sensitivity would have to be labelled `unknown`/elicited and could never pass as calibrated. |
| Model-based diagnosis, measurement selection (de Kleer and Williams 1987) | deterministic component models, prior fault probabilities, minimum-entropy probing | **Partial** | Matches the set-based `EvidenceState` (candidates are removed, not reweighted). It assumes noise-free observations, which engagement calls are not (measured false positives). |
| Noisy active learning over decision regions: EC², adaptive submodularity (Golovin, Krause and Ray 2010; Golovin and Krause 2011) | known noise model p(y \| h); many tests | **Unnecessary** | The decision-region view is right: identify the licensed action, not the hypothesis. But cases have 2 hypotheses and at most 3 actions, so exact search is trivial and greedy guarantees add nothing. The known-noise assumption fails anyway. |
| Selective prediction, reject option (Chow 1970; Geifman and El-Yaniv 2017) | calibration data exchangeable with deployment | **Fits the refusal rule; fails across studies** | Refusal and deferral are selective prediction. Kamath, Jia and Liang (2020) found confidence-based abstention fails under domain shift. E-CAL1 shows the same at study level: a Platt recalibration fitted on one study gives observed-to-forecast ratios of 0.41-2.89 on the other. |
| Optimizer's curse (Smith and Winkler 2006) | value estimates with noise; the maximum is selected | **Observed** | Theory predicts that the chosen action's estimate is biased toward optimism. E-CAL1 matches: step-level wrong-elimination forecasts are 1.98-2.10x too low on the steps the belief planner **selected**, and 0.96-1.23x on the fixed order's steps, which no forecast selected. Remedy: shrink value estimates **before** selection. The planner's Jeffreys bound does shrink, but it is 12-20x the observed rate, so it is uninformative. |
| Model-based RL with uncertainty penalties (Janner et al. 2019, MBPO; Yu et al. 2020, MOPO) | enough transitions to estimate model error where the policy goes | **Fits the design, not the data** | "Use the model only where it is supported; otherwise fall back" is the `safe` arm's applicability gate and `plan_measurement`'s refusal. Estimating model error on the policy's own actions needs many labelled transitions. There are two studies and no premise references. |
| Learning to defer (Madras, Pitassi and Zemel 2018; Mozannar and Sontag 2020) | joint data on model and expert outcomes | **Fits the fallback** | The declared-template rule is the "expert"; deferring to it when the forecast is refused is the right structure. Learning the deferral rule needs outcomes of both, which do not exist for premise measurements. |
| Transportability (Pearl and Bareinboim 2014) | a selection diagram saying which mechanisms differ between contexts | **Names the audit field** | Using a phenocopy measured in HT29 for a K562 case is a transport claim. The forecast's "direct or analogous support" and "cell-context extrapolation" fields are declarations of such assumptions. The diagrams for cell lines are unknown, so the field stays `unknown`, not a number. |
| Conformal risk control (Angelopoulos et al. 2024) | exchangeable calibration and test data | **Not credible across studies** | A finite-sample guarantee on two development studies does not transfer to a third context. Allowed only as exploratory (gated plan). |
| Hypothesis-driven closed-loop science (King et al. 2004, Robot Scientist) | a closed hypothesis set and a trusted logical model | **Partial** | Same loop (hypothesise, choose a costed experiment, update). It assumes a complete model; here the explanation set can be exhausted, and `DecisionEngine` treats that as a contradiction, not a decision. |

**Citations resolved online in this block:**
- Heckerman, Breese and Rommelse 1995, *Communications of the ACM* 38(3):49-57.
- Smith and Winkler 2006, *Management Science* 52(3):311-322.
- Kamath, Jia and Liang 2020, *ACL*, pp. 5684-5696.
- Golovin, Krause and Ray 2010, *NIPS* 23.
- Chandrasekaran et al. 2024, *Nature Methods* 21:1114-1121, DOI 10.1038/s41592-024-02241-6.

Rainforth et al. 2024 was resolved in `research/protocol_v2/LITERATURE.md`. The others (Howard 1966; Lindley 1956;
de Kleer and Williams 1987; Golovin and Krause 2011; Chow 1970; Geifman and El-Yaniv 2017; Janner et al. 2019;
Yu et al. 2020; Madras et al. 2018; Mozannar and Sontag 2020; Pearl and Bareinboim 2014; Angelopoulos et al. 2024;
King et al. 2004) were **not re-resolved** here. Resolve them before publication.

## 4. What this block changed on the path

- **Evaluation boundary (protocol v2.1).** The menu comes from the study design; pools come from each fold's training
  compounds; the unit mean is primary (`research/protocol_v2/protocol_v2_1.json`).
- **Stage 1, two latent gaps now reported.** Neither changes a production default:
  - `SourceClusterIndex.independence` (`src/maestro/provenance.py`) keeps unregistered sources as dependence-unknown,
    not independent (audit E3).
  - `PublicCase.unsited_engagement_premises` (`src/evaluation/cases.py`) names engagement premises without a sample
    site. Every engagement_v1 case has one, so a same-context lysate grant of the same quantity would meet it
    (audit E5; `tests/test_evidence_audit_prerequisites.py`).
- **Stages 2-4: nothing built.** The link needs a qualified task and a forecaster with data behind it. Neither exists
  (README sections 3 and 5). Building the arm now would produce an untestable component. The brief forbids
  simulating that result.

## 5. The smallest link, specified for when data exist

1. **`PremiseOutcomeForecaster`** (research only). For a capability action and the case's hypothesis pair, it
   returns an `OutcomeForecast` over {engaged, not engaged, QC-failed, uninterpretable}.
   - Each branch is built from references whose premise state is known independently, in the same context:
     direct support. Anything else is analogous support, recorded as such.
   - The measured false-positive rate enters the "not engaged under H" branch.
   - Sensitivity is `unknown` until measured on positive controls. While it is unknown, the forecast is refused.
2. **Consumer.** The existing contingent value (`evaluation/contingent.py`) is run with those probabilities in
   place of declared outcomes. The agent computes the value from:
   - hypothesis discrimination;
   - the follow-up licensed decision;
   - cost in wells and days;
   - failure probability;
   - the wrong-decision loss (-2).
3. **Fallback.** On refusal, the declared-template rule chooses, and the experiment stays on the menu.
4. **Minimum data.**
   - At least 20 references per hypothesis branch with independently known engagement, in the task context.
   - At least 30 target-gene clusters of cases.
   - Positive controls for sensitivity. The concordant-support pairs are candidates: 420 PRISM cases, 27 genes,
     where an active drug and a strong selective dependency agree.
