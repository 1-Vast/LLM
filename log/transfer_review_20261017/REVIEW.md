# Transferring research experience across biological contexts

Literature review and framework adjustment for MAESTRO, 2026-10-17.

* **Status.** This is a design review.
  * No experiment was run and no outcome file was opened.
  * 0 wells, 0 provider calls, no downloads.
* **Relation to the research programme.** It builds on the
  [research programme](../RESEARCH_PROGRAM.md) revised earlier today. §8 lists where it agrees with
  that programme and which changes it recommends; none of those changes is applied here.
* **Sources.** Access levels are recorded in [SOURCES.json](SOURCES.json).
  * Numbers quoted from 2026 papers come from their official abstracts unless marked otherwise.
  * They are author-reported, not reproduced.

## 0. The answer

Adopt the pivot toward an autonomous research system that transfers research methods across drug
and cellular contexts. Change three things.

1. **Name what is transferred.** "Research experience" mixes four kinds of knowledge (§1.2), and
   they transfer very differently.
   * Across LLM agents, robotics and computer vision, and in MAESTRO's own record, two kinds
     transfer reliably:
     * *verification knowledge*: which checks show that something will not work here;
     * *response knowledge reached by retrieval of close analogues*.
   * Whole procedures and learned predictions of their value transfer worst, and their negative
     transfer is concentrated on the hard cases.
   * Make verification the core learned object.
2. **Make the bridging experiment decide between transfers, not learn biology.**
   * The most valuable few wells in a new context are *paired reference measurements*: compounds
     already measured in the source contexts.
   * They should be placed where the candidate transferred methods disagree about the decision.
   * This is active model selection (vision) and data analogies with system identification
     (robotics), applied to wells.
3. **Give the Virtual Cell two falsifiable jobs.**
   * A *control variate* that reduces the wells needed for a valid estimate (prediction-powered
     inference).
   * A cheap *evaluator* that must rank research procedures the way measured data do (the
     ranking-fidelity criterion from simulated robot-policy evaluation).
   * A virtual cell that fails both tests is not used for that decision.

**Recommended application domain: context transfer in phenotypic early drug discovery.**

* **What it means.** Carry a campaign's knowledge and methods from cheap, well-measured contexts
  into a new, expensive one with a small well budget, and recognise when they do not apply.
  * Cheap sources: cancer cell lines, L1000 profiles, pooled viability screens.
  * Expensive targets: a new lineage, a primary or patient-derived model, a new assay, dose or
    exposure time.
* **The analogy.** This is the drug-discovery form of sim-to-real and cross-embodiment transfer.
* **Why it is broad.** Every programme meets new contexts.
* **Why it is valuable.** The cost of wrong transfer is paid in the units MAESTRO already counts:
  wells and turnaround days.

**Strongest prior against the plan: our own data.**

* On two readouts, the orbit-contrast identity gate was no better than a plain accuracy gate.
* The vision result "accuracy on the line" predicts that failure prediction may reduce to source
  accuracy.
* The first study (§6) is designed to settle this cheaply before anything is built on top of it.

## 1. The proposal against the current literature

### 1.1 What is already established

| Component of the proposal | Already shown by | Consequence |
|---|---|---|
| An LLM proposes hypotheses, selects experiments and revises from results | Co-Scientist and Robin (Nature 2026); Kosmos (2025) | A longer autonomous loop is not a contribution |
| Real experimental feedback improves an agent's discoveries | Wainrib et al. 2026 | Any feedback claim needs a permuted-feedback arm |
| An experiment-selection policy learned from past campaigns transfers to new ones | AssayLoop (Edwards et al. 2026) | "Learning from past campaigns how to choose experiments" is not open in general |
| Refusing when the model library is inadequate | CARTOGRAPH (ICML 2026 AI for Science workshop) | Refusal by residual misfit is prior art |
| Learned acquisition for perturbation discovery | TDAL (2026) | Acquisition-function learning is crowded |
| Retrieval as the zero-shot response predictor | LGR (MLGenX at ICLR 2026, Tahoe-100M) | Retrieval is a mandatory baseline, and likely a component |

Notes on the evidence behind the table:

* **Wainrib et al.**
  * Setup: Cell Painting, 800 replicated runs.
  * Feedback raised discoveries per feature by 53.4%, and the gain disappeared when hit/miss
    labels were permuted.
  * Learning from feedback appeared only after a model upgrade.
* **AssayLoop.**
  * Trained on 1,389 CRISPR screens.
  * About 5.67× enrichment over random on temporally held-out screens.
  * Transferred to phenotype categories excluded from training.
* **CARTOGRAPH.**
  * Its refuse guard flagged all 4 A-Lab claims that later reanalysis found inconclusive.
  * It passed 32 of 36 confirmed claims.
* **LGR.** The authors conclude that retrieval quality, not predictor complexity, drives zero-shot
  accuracy.

The proposal's own critique is therefore right, and stronger than stated. What remains open is
narrower (§7):

* predicting *negative* transfer of a drug-context decision before paying for it;
* choosing the few wells that decide between candidate transfers;
* doing both against the strongest simple workflow, at equal wells.

### 1.2 Four kinds of "research experience"

| Layer | Example | How it transfers in the literature | MAESTRO's record |
|---|---|---|---|
| **R. Response knowledge** | Compounds of this class kill lines of this lineage | Through retrieval of close analogues: REGENT, LGR, paired data analogies | Transfers, but reduces to chemistry and mechanism class |
| **M. Model choice** | Which predictor to trust in this context | Model rankings are mostly stable across shifts ("accuracy on the line"); generalisation methods do not beat ERM under honest model selection (DomainBed) | Training-only context means were inner-selected in all five folds of the anchor study; the identity gate matched an accuracy gate |
| **P. Procedures** | Which workflow or acquisition policy to run | Task-level skills fall below the no-memory baseline and raw trajectories hinder (2026 agent-memory studies); configuration surrogates fail on new microscopy tasks. AssayLoop is the counterexample, within one assay family | Block Q planner lost to the fixed sparse design at N; feedback showed no validated gain on Jaaks (−1.1% [−4.0, +1.4]); hub-line memory gave 0 map utility; LLM agent arms were null or harmful |
| **V. Verification** | Which checks reveal non-applicability; failure signatures | Validation routines are what transfers across coding domains; abstract insights are safer than traces; residual refuse guards | The decision changes that held came from verification-type fixes |

Details for the MAESTRO-record column:

* **Response knowledge.**
  * RKT was confirmed on the sealed GSE70138 tier.
  * Knowledge-graph value on cold-start compounds equals mechanism-class membership.
  * In target triage, chemical-neighbour transfer finds 0.98 annotated targets per 10 nominations;
    signature connectivity finds 0.017, and random picks 0.012.
* **Verification fixes:**
  * the endpoint scale correction (55 → 77 of 141 per-line hits);
  * the sign-flip control;
  * the interval rule adopted after the MEASURE-gate false positive;
  * the evaluator-audit corrections C1–C7.

**Planning consequence.**

* Build around V.
* Obtain R by retrieval.
* Keep P a small, fixed library.
* Treat per-context M selection as a hypothesis that will probably reduce to "use the globally best
  source procedure". That makes the globally best procedure the main baseline.

## 2. Lessons by field

### 2.1 Computer vision

**Transfer structure can be measured.**
* Taskonomy (CVPR 2018) estimated a transfer matrix among 26 vision tasks and used it to allocate
  supervision.
* For MAESTRO: measure the source-context → target-context transfer matrix by complete replay. It
  is an empirical object, not an assumption.

**Ranking stability.**
* "Accuracy on the line" (ICML 2021): out-of-distribution accuracy is close to a linear function of
  in-distribution accuracy across many models.
* "Agreement on the line" (NeurIPS 2022): where agreement between models follows the same line,
  target accuracy can be estimated without target labels.
* For MAESTRO:
  * The applicability baseline to beat is source accuracy.
  * Label-free disagreement among candidate methods is the signal worth testing.

**Model selection is part of the method.**
* DomainBed (ICLR 2021): under fair model selection, ERM matched the domain-generalisation
  algorithms.
* Test-domain "oracle" selection was much better. That gap is the value a few target labels could
  have.
* For MAESTRO: every transfer arm carries its own selection rule. Target-label selection is
  reported as a ceiling, never as a result.

**Label-free performance estimation.**
* Representative work: LogME (ICML 2021), ATC (ICLR 2022), STAMP (2026).
* These methods rank candidate models well; absolute values are less reliable. STAMP, for example,
  reports a rank correlation of 0.984 with ObjectNet across 27 ImageNet models using source data
  only.
* For MAESTRO: predict relative failure risk and the ordering of candidates. Do not promise
  calibrated probabilities.

**Active model selection.**
* Active testing (ICML 2021) and CODA (ICCV 2025) label the points that best separate the leading
  candidates. CODA reports up to 70% fewer labels to identify the best model.
* For MAESTRO: this is the direct template for decision-discriminating bridge wells (§4.3).

### 2.2 NLP and LLM agents

**Experience memory.**
* Systems: ExpeL, Voyager, ReasoningBank and ACE store insights, skills or evolving playbooks.
* They improve performance mostly within a benchmark family.

**Transfer studies of 2026.**
* *Experience reuse* (Hu et al.):
  * raw trajectories tend to hinder transfer, while abstract insights are safer;
  * negative transfer falls disproportionately on cases the agent cannot already solve.
* *Cross-task skills* (Feng et al.):
  * task-level skills mostly fall below the no-memory baseline;
  * subtask-level skills rise above it;
  * text skills transfer better than code skills.
* *Coding agents* (Kim et al.):
  * cross-domain memory gave +3.7% on average;
  * what transfers is meta-knowledge such as validation routines;
  * low-level traces hurt.

**Audits of autonomous science.**
* BoxingGym: experimental design combined with model discovery remains hard for LLM agents.
* Microscopy-agent benchmark (2026):
  * 105 configurations, 1,949 runs;
  * surrogate models of configuration performance did not predict performance on new tasks.
* Luo et al. (arXiv 2025; listed in PNAS):
  * internal reward mechanisms selected experiments using test results;
  * the flaws were invisible in the finished manuscript.
* Bisht et al. (2026) argue that current AI scientists are built for co-science rather than
  discovery. Their reasons:
  * problems are chosen for measurability;
  * failure and tacit knowledge are missing from training;
  * benchmarks lack physical feedback.

**Falsification frameworks.**
* POPPER uses sequential falsification with error control.
* CARTOGRAPH selects, resolves and refuses.

**For MAESTRO:**
* Store verification knowledge at subtask granularity: check, condition, outcome.
* Report negative transfer on hard cases separately.
* Require permuted-feedback arms.
* Audit full run logs, not only reports.
* Treat a learned predictor of procedure value across heterogeneous tasks as the riskiest
  component.

### 2.3 Robotics

**Pooling versus composition.**
* Open X-Embodiment showed positive transfer from pooled multi-robot data.
* Two later results qualify that:
  * high-quality single-embodiment pretraining can transfer as well as multi-embodiment
    pretraining (Shi et al., 2025–26);
  * morphology shifts gain little from unstructured diversity but gain from *data analogies*, paired
    demonstrations aligned across embodiments. Changing only the data composition improved
    real-world transfer by 22.5% on average (Yang, Finn and Sadigh 2026).

**Scaling.**
* Generalisation follows a power law in the number of distinct environments and objects.
* Demonstrations per environment saturate quickly (Lin et al., ICLR 2025).

**Adaptation.**
* RMA estimates latent environment parameters from a short history of recent states.
* Online system identification (RSS 2025) gives guarantees under stated model assumptions.

**Grounding.**
* SayCan multiplies the language model's relevance score by a learned feasibility value in the
  current state.

**Retrieval.**
* REGENT adapts in context to unseen environments by retrieval.
* A plain nearest-neighbour baseline is already strong.

**Learning from experience.**
* π*0.6 (RECAP) learns from its own rollouts and corrections through advantage conditioning.
* Fleet-scale variants followed in 2026.

**Evaluation.**
* SIMPLER showed that simulated evaluation can track real-world policy *rankings* once the visual
  and control gaps are controlled.
* Ranking fidelity, not visual realism, is the criterion.

**For MAESTRO:**
* Experience should maximise *distinct contexts*, not depth within a context.
* Bridging data should be paired references.
* The context latent is estimated from those references (RMA). The anchor study shows a scalar
  offset is the wrong latent: it cannot change within-drug context ranks.
* Applicability is relevance × feasibility (SayCan), which here means retrieval similarity × the
  failure detector.
* The virtual cell is the simulator. It is trusted for a decision only if it ranks procedures as
  measured data do.

### 2.4 Causal inference and statistics

**Transportability (Bareinboim and Pearl).**
* A finding transfers when the mechanisms that differ between contexts are not on the path the
  finding depends on.
* z-transportability asks which limited target experiments make a finding transportable.

**Transportability of perturbation effects.**
* Qi and Chapfuwa (bioRxiv 2026, v3 dated 2026-10-08; abstract only) report that cross-context
  generalisation is governed by shared causal mechanisms, not distributional similarity.
* In their semi-synthetic Perturb-seq simulator, lower cross-context concordance of
  transcriptome-wide effects tracked larger transfer gaps.

**Invariance.**
* Invariant causal prediction tests which relations stay invariant across environments.
* Meinshausen et al. (PNAS 2016) validated it on gene-perturbation data.

**Prediction-powered and active inference.**
* Model predictions plus a few labels give valid estimates.
* The estimates are narrower when the model is good and still valid when it is not.
* The active variant chooses which items to label.

**Selection.**
* Selecting candidates by prediction shifts the distribution: conformal selection, feedback
  covariate shift.
* MAESTRO has already seen conformal BH exceed its nominal FDP on exposed triage data.

**For MAESTRO:**
* The applicability check is a concordance or invariance test on paired references.
* The virtual cell enters estimation as a control variate.
* Error control on selected candidates needs its own guarantee.

### 2.5 Drug discovery and virtual cells

**Baselines are hard to beat.**
* Virtual Cell Challenge 2025: most models did not beat a mean baseline on MAE, and the single
  narrow metric invited optimisation against it.
* Virtual Cell Challenge 2026: zero-shot prediction in six unseen cell contexts, given only basal
  non-targeting cells, scored on six metrics.
* Ahlmann-Eltze et al. (Nature Methods 2025): linear baselines matched or beat deep perturbation
  models.
* Heo (2026), on drug-blind sensitivity prediction:
  * global Pearson mostly reflects drug potency;
  * for within-drug ranking, no drug encoding beat cell-only features;
  * the paper proposes mechanism-stratified training and *response matching from pilot
    observations*.
* Two further 2026 papers report that metric choice flips model rankings and that leakage inflates
  accuracy.

**Decision-level evaluation.**
* Bereket and Leskovec (bioRxiv 2026, abstract only) propose PerturbHD, which scores virtual cells
  by their use in hit discovery.

**Few-shot transfer to patient models.**
* TCRP (Nature Cancer 2021) tuned cell-line models with a few patient-derived samples.
* A reusability report found the published numbers hard to match, though the method still beat
  baselines.

## 3. Six regularities across fields

1. **Abstract verification knowledge transfers; raw experience and whole procedures do not.**
   * Evidence: the agent-memory studies of 2026, CARTOGRAPH, and MAESTRO's verification fixes.
2. **Rankings of methods are more stable than per-context selection can exploit.**
   * Evidence: accuracy on the line, DomainBed, the microscopy surrogates, and the orbit gate.
   * Per-context gains concentrate where the candidates disagree.
3. **Bridging works through paired correspondences, not unpaired volume.**
   * Evidence: data analogies, concordance tracking the transfer gap, and response matching from
     pilot observations.
   * MAESTRO's own data: in the anchor study a full X1 reference profile gave +0.307 known hits per
     drug (unpriced), while a scalar offset lost.
4. **Generalisation scales with the number of distinct source contexts.**
   * Evidence: robotics scaling laws, and AssayLoop improving with more historical screens.
   * Independent units are contexts, and power counts contexts.
5. **Simulators earn trust by preserving decisions, and can be used safely as control variates.**
   * Evidence: SIMPLER, prediction-powered inference, PerturbHD, and the challenge's metric lessons.
6. **Automation hides selection.**
   * Feedback claims need permuted-feedback arms.
   * Metrics and model selection are frozen before outcomes are seen.
   * Logs are audited, not only reports.

## 4. Adjusted framework

### 4.1 Research object

MAESTRO learns, from completed campaigns, three things:

1. which signals predict that a transferred research procedure will fail in a new drug-context
   setting;
2. which few paired measurements best decide between the candidate transfers;
3. when to adopt, repair or refuse.

It is judged by terminal discovery decisions at equal wells, against the globally best transferred
procedure and against no transfer.

### 4.2 Domain and order of context axes

Context transfer in phenotypic early drug discovery, extended in this order:

1. new cell context (line → lineage → primary or patient-derived cells);
2. new readout or assay (pooled viability → plate viability → transcriptional profile);
3. new dose or exposure time;
4. combinations.

Each axis opens only after the previous one has a supported result. Target discovery from knowledge
graphs and mechanism claims stay deferred: MAESTRO has no measured mechanism truth locally.

### 4.3 The loop

| Step | What happens | Learned or fixed | Agent | Virtual Cell |
|---|---|---|---|---|
| 1. Retrieve | Assemble candidate transfers for target task T from the procedure library and analogous source campaigns | Fixed library; retrieval by context and chemistry similarity | Builds the candidate set | Supplies predictions per candidate |
| 2. Screen for failure | Score each candidate's negative-transfer risk from label-free signals (below) | **Learned** across source tasks: the failure detector | Drops candidates above a frozen risk threshold, with a named reason | Supplies support and coverage features |
| 3. Bridge | Buy k paired reference wells in T where the surviving candidates disagree most on decision-relevant outputs, weighted by similarity to T's candidates | Rule fixed; weights optionally learned | Proposes the bridge within the well budget | Control variate for estimating each candidate's value |
| 4. Decide | Adopt the best candidate; apply one bounded repair fitted on the bridge wells; or refuse | Repair menu fixed and small | Chooses, or refuses with a named reason | Re-predicts after the repair |
| 5. Record | Write back verification knowledge: which signals flagged failure, which bridge resolved it, the outcome | Stored as check → condition → outcome | Maintains the record | None |

The label-free signals used in step 2:

* concordance of already-measured paired references between source and target;
* disagreement between candidates on the top-k decision;
* source accuracy (the baseline signal);
* the target's distance from source coverage;
* virtual-cell support.

### 4.4 What is learned, and from what

* **Failure label.**
  * NT(p, T) = U(p, T) − U(b, T) < −δ.
  * U is terminal utility (confirmed hits per k slots).
  * b is the no-transfer, context-only arm.
  * δ is frozen before fitting.
* **Identifiable labels.**
  * Complete retrospective replay runs every library procedure on every source task, which gives
    the full counterfactual table.
  * This avoids the programme's `VALUE_LABELS_UNQUALIFIED` problem for retrospective tasks.
  * Replay of one measured matrix is a technical replay, not independent biology.
* **Features.** Only quantities available before the decision. Hidden target profiles, outcome
  subgroups and terminal labels are excluded.
* **Learner.** A small regularised classifier or ranker. No new foundation model.

### 4.5 Virtual Cell tests

* **Control variate.** At equal wells, prediction-powered estimates of each candidate's value must
  have:
  * coverage at least nominal;
  * narrower intervals than wells-only estimates.
* **Procedure evaluator.**
  * The rank correlation between virtual-cell-simulated and replayed procedure values across target
    tasks must exceed a frozen bar.
  * It must also exceed source accuracy alone.
* **Failing both.** Then the virtual cell is excluded from steps 2–4 for that axis. It may still
  serve as a predictor in step 1 if retrieval beats it.

### 4.6 Agent role and LLM boundary

* **What the Agent does.** It maintains the candidate set, enforces refusals with reason codes,
  composes the bridge within the budget and keeps the record.
* **What stays deterministic.** All of the above is deterministic first.
* **When an LLM may be added.** After a deterministic gain exists, and only if it beats matched
  templates and simple search at the same tools, budget and source experience.
* **Model.** Model calls use deepseek-flash, as the project already requires.

## 5. Hypotheses, comparators and stop rules

| ID | Claim | Comparators at equal wells | Stop if |
|---|---|---|---|
| **H1** Verification transfers | A failure detector trained on source contexts predicts negative transfer in held-out contexts | Source accuracy alone; distance alone; uncertainty alone; concordance alone | It does not beat source accuracy alone. The learned-failure claim then stops |
| **H2** Decision-discriminating bridges | Disagreement-targeted paired bridges select the better procedure more often and give more confirmed hits | Random references; most uncertain; most similar to candidates; a fixed standard panel; response-information design; no bridge with the globally best procedure; the fixed sparse design | It does not beat both "no bridge, globally best" and the fixed panel |
| **H3** Virtual Cell as control variate | Valid intervals narrower than wells-only at equal wells | Wells-only; plug-in virtual cell (expected to under-cover) | Coverage fails, or there is no width gain |
| **H4** Accumulation | Detector and bridge value grow with the number of distinct source contexts, without loss on earlier contexts | Equal-size sources with fewer distinct contexts | No gain with added contexts |

Rules common to all four:

* A zero arm (no transfer) and an arm that predicts no change.
* Paired intervals grouped by context and lineage.
* Hard-case subgroups reported separately.
* Permuted-label controls for H1 and H2.

## 6. First study: an instance of MT-P0

* **Data.** PRISM 19Q4, local and already exposed, so the grade is development.
* **Units and split.**
  * Cell lines grouped by lineage, held out by lineage, which makes contexts the units.
  * Unseen compounds within known contexts are a secondary split. MAESTRO has studied that case
    repeatedly, and its answer there is mechanism-class retrieval.
* **Library.** Existing arms:
  * training context means;
  * chemical neighbours;
  * ungated chemical + target neighbours;
  * conditional ridge;
  * one residual-transfer arm.
* **Labels.** NT by complete replay.
* **Bridges.** Revealed measurements of reference compounds in the target context.
* **Metrics.** Hits per slot, negative-transfer rate, regret against the procedure oracle, and
  refusal correctness.
* **Molecular counterpart.** L1000 GSE92742 touchstone compounds give paired references across the
  core lines. That tier is also exposed.
* **External, expensive-context test.** A primary-cell ex vivo drug-sensitivity resource would test
  the cheap-to-expensive claim. It needs a separate authorisation and a licence and size check, and
  none was done here.
* **Sealed data.** PRISM 24Q2 stays sealed until a protocol adopts the evaluator-audit corrections.
  The GSE70138 tier has already been used once.
* **Cost.** Retrospective, 0 wells.
* **Pre-registration.** Freeze the library, δ, the signals, the bridge rule and the metrics before
  any replay outcome is computed.

## 7. Novelty boundary

| Area | Established | Open for MAESTRO |
|---|---|---|
| Learned acquisition across campaigns | AssayLoop (CRISPR hits); TDAL | Small-molecule, context-shift decisions with failure detection |
| Feedback-driven agents | Wainrib et al.; Co-Scientist; Robin | A permuted-feedback-controlled gain over the globally best transfer |
| Refusal | CARTOGRAPH; POPPER | A refusal rule learned across biological contexts and scored on decisions |
| Active model selection | CODA; active testing | Selection among transferred procedures with paired wells, scored on discovery |
| Transportability of perturbations | Qi and Chapfuwa (semi-synthetic) | A real-data test that concordance predicts decision-level negative transfer |

No first-method claim is made. The defensible gap is the combination in the right-hand column,
tested against the simple reductions of §5.

## 8. Recommended changes to the research programme (not applied)

1. Split `F_phi`: make failure risk the primary learned output and expected gain secondary.
2. Make unseen contexts the primary MT-P0 split, with unseen compounds secondary. This reverses the
   programme's current order.
3. Add "globally best source procedure" and "source accuracy" as mandatory comparators.
4. Define the applicability check as a paired-reference, decision-discriminating bridge (§4.3).
5. Use complete replay to identify value and failure labels on retrospective tasks.
6. Add the two Virtual Cell tests of §4.5.
7. Count independent units as contexts and lineages. Report hard cases separately.

## 9. What not to build

* A larger multi-agent platform, memory graph or data lake.
* Free-form LLM procedure generation before a deterministic gain.
* A new foundation virtual cell.
* Mechanism claims without measured distinguishing evidence.

## 10. Addendum: the agentic-autonomy perspective (read in full, 2026-10-17)

Source: Zhao, Fang, … Hsieh, "The rise of agentic AI in drug discovery from static tools to
autonomous virtual scientists", *npj Drug Discovery* 3, 43 (published 12 October 2026),
doi:10.1038/s44386-026-00075-0. It is a perspective. It has no data or code of its own. The
user recommended it during the context-transfer study.

### 10.1 What it contributes

* **A six-level autonomy spectrum.**
  * L0: fixed tools.
  * L1: assisted pipelines. The LLM is a local component inside a classical search or decision
    algorithm.
  * L2: task controller.
  * L3: closed-loop researcher, with feedback-driven correction around a goal.
  * L4: self-evolving system, with cross-project optimisation of its own methods.
  * L5: virtual scientist. The authors state that no L5 system exists in drug discovery.
* **Reporting and ablation requirements.** The authors ask that empirical studies:
  * compare agent-driven planning with linear non-agent pipelines under the same models and tool
    access;
  * ablate memory, error recovery and multi-agent layers;
  * report the human intervention count with its severity;
  * report an autonomous error-recovery rate (corrected anomalies over runtime errors);
  * report sub-task completion rates;
  * report a standard error taxonomy (planning, tool, code and environment level);
  * report the full cost: tokens, money, wall-clock time and human effort.
* **On validation.** Retrospective "reproduction of discovery" is weakened by LLM data leakage
  and memorisation. Prospective in-silico validation depends on surrogate accuracy.
* **On resource-constrained decisions.** The DO Challenge is named as the paradigm for testing
  exploration versus exploitation under a budget. Bayesian, uncertainty-aware closed loops are
  named for borderline repeat-or-move-on decisions.
* **When an agent is needed.** The authors note that structured non-agent workflows are often
  more reliable for well-defined procedures. Decomposition pays only under conflicting signals.

### 10.2 What it changes in this framework

1. **Autonomy labels.** Every arm in the context-transfer study carries a level:
   * `vc0`, `knn`, `item`: L0.
   * `b_exploit`, `b_panel`, `match_panel`: L1, fixed two-stage pipelines.
   * `b_info`, `b_lookahead`: L2, a target-specific plan from the model state.
   * `maestro`: L3, decision-focused planning with verification and repair from the context's
     own feedback.
   * `llm`: an L1/L2 hybrid. The LLM proposes the bridge inside the deterministic loop.

   No arm is L4. Cross-context learning of the method is tested only by the transfer of the
   frozen method from PRISM to Beat AML.
2. **The ablation ladder is the primary design, not an afterthought.**
   * P1 removes the bridge, verification and repair.
   * P2 replaces the plan with the standard linear two-stage design.
   * P3 removes the Virtual Cell from the bridge pipeline.
   * The secondary contrasts remove repair alone and the LLM.
   * Permuted-feedback and permuted-context controls test that the gain comes from the
     context's own data.
3. **Error taxonomy and recovery rate, in the study's own terms.**
   * Error classes:
     * environment level: an unmeasured well;
     * model level: a transferred prior that fails, with fewer hits than the context-free prior;
     * planning level: an invalid LLM selection;
     * tool level: a provider or protocol error.
   * The study reports each class's rate.
   * Its recovery rate is the share of model-level failures where the full system recovers at
     least the context-free prior's hits.
   * Detection is reported as the AUROC of the bridge misfit.
4. **Leakage boundary.**
   * The primary claims rest on a deterministic core that cannot have memorised Beat AML.
   * The LLM arm is secondary. A positive LLM result would still be open to the memorisation
     explanation the authors raise, because the Beat AML release is public.
5. **Cost reporting.** Wells, assay rounds (each bridge adds one turnaround), API tokens and USD,
   wall-clock time, and a human intervention count. The count is 0 in replay and is reported as
   such.

### 10.3 Where this study goes beyond it

The perspective calls for domain-specific, process-auditable benchmarks of resource-constrained
decisions. It cites none for the cell-context transfer problem. This study is one: an
equal-well, pre-registered replay with a held-out patient domain, named refusals and an error
taxonomy. It does not test the perspective's L4/L5 claims, and it makes no claim about them.
