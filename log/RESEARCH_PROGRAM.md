# MAESTRO research programme

Revised 2026-10-17. Programme design, not a scientific release or a frozen
experiment. The main research object is transfer of research methods across
drug and cellular contexts. Decision-relevant response correction is one
component of this problem. Historical protocols and verdicts retain their scope.

## Purpose and research object

**MAESTRO is an autonomous research framework for contextual early drug
discovery, studying when research methods transfer across drugs and cellular
contexts, how to check their applicability, and how real feedback can repair
failed transfer.** A campaign starts with a biological objective and candidate library
and ends with candidate/context decisions, supporting measurements, unresolved
explanations, and a justified next experiment or stop decision.

The research object is a complete early discovery campaign:
biological question -> intervention hypotheses -> candidate and assay selection
-> measured feedback -> bounded response-model correction -> confirmation and
context assessment -> evidence-qualified research conclusion.

The central research question is:

> Can experience from previous research tasks predict when a research procedure
> will help or harm a new drug/context decision, identify a useful applicability
> check, and use its outcome to revise the model and procedure, improving future
> discovery decisions over strong conventional workflows at the same total cost?

The shared domain is intervention x cellular context x dose x exposure time ->
measured response and research decision. A task includes a question, endpoint,
candidate/context population, legal actions, information history and resource
cap. Transfer means a frozen procedure or value rule learned on source tasks
improves decisions on held-out target tasks. Remembering another compound name,
adding JSON fields or fitting the target response again does not establish this.

Current validation is mainly in oncology cell models and small-molecule libraries,
including repurposing. The architecture can represent other diseases and genetic
perturbations, but this is not evidence of cross-disease efficacy. De novo
chemistry, clinical success and full preclinical development are not first-stage
deliverables. Developability measurements can constrain progression when present.

## Scope, deliverables and current capability

| Discovery task | Output and functional objective | Current support | Programme decision |
|---|---|---|---|
| A. Candidate discovery and repurposing | Unique compounds satisfying a predeclared functional criterion in a specified model, with confirmation and the full candidate denominator | Viability data, chemistry/context baselines and nomination code exist; evidence is assay-specific, historical or simulated | First primary task; do not count the same drug repeatedly across lines as distinct candidates |
| B. Context selection and failure analysis | Candidate-context pairs meeting functional criteria, with measured comparisons when selectivity is claimed; identify where transfer fails | Context transfer exists; PRISM residual events are a development proxy, not a matched selectivity assay | Second primary task. Explicit comparison assays establish cell-background selectivity; therapeutic window needs qualified normal-tissue controls |
| C. Discriminating explanations | Competing explanations, different measured predictions, a distinguishing experiment and an updated conclusion | Evidence/review contracts exist; measured positive/negative mechanism references are absent locally | Connecting case after data qualification; otherwise deliver a concrete test plan and `ASSET_BLOCKED`, not mechanism discovery |
| D. Dose, exposure and combinations | Measured condition choice or combination benefit against an explicit reference | Condition fields exist; active response models do not establish general dynamics or synergy | Extend one axis after A/B succeed; no dynamics claim from a static matrix; compare combination work against BATCHIE-class methods |
| E. Research allocation and progression | Choose screen, characterise, confirm, distinguish explanations, continue or stop | Budgets, acquisition, lineage, refusal and restart exist | Shared decision problem across A-C; evaluate downstream utility, not generated ideas or eliminated hypothesis counts |

First-stage breadth comes from completing A and B with a reusable method and an
honest C connection. B can test context choice and transfer failure without
calling every activity difference selectivity. A/B sharing a source is cross-objective evaluation within
that source, not independent cross-platform replication. Missing C data does not
erase an A/B result; it limits any claim of mechanism reasoning. Known cell-line
activity is not a disease indication or patient-response result.

## Response differences and model applicability

Use a small statistical model before considering architectural expansion:

`response(d,c) = context_mean(c) + drug_activity(d) + context_loading(c) * drug_response(d) + error(d,c)`.

The response vector is not a mechanism or a true cellular state. Dose/time enter
only where measurements support them. Provenance is needed to distinguish batch
effects from biological residuals. A common activity correction can change which
drug is selected in A, while cancelling from a within-drug context contrast in B.
The anchor study's offset failure therefore does not establish that activity
information is useless for candidate discovery. Conversely, good full-profile
prediction does not show that affordable observations resolve the contrasts in B.

Within a fixed linear model, let `H` map response coefficients to a legal assay
bundle and `C` map them to task contrasts. If `H w = 0` while `C w != 0`, the
observations alone cannot identify that contrast without additional assumptions.
With a prior and noise, posterior contrast variance describes model-conditional
support, not biological identifiability. This is standard linear inference, not
the novelty claim. A coarse group recommendation cannot count as an accurate
individual-cell recommendation when the frozen endpoint requires the latter.

Response correction supplies three prerequisites for procedure transfer:

1. **Diagnosis:** a training-fitted estimate of supported task contrasts predicts
   where feedback improves held-out decisions beyond activity, uncertainty and
   general prediction-error scores.
2. **Correction:** using the same observations, a small predeclared correction
   improves raw terminal utility over simple conditional regression and the
   strongest conventional workflow. Lower profile error alone is insufficient.
3. **Feedback:** update the permitted response component from actual observations,
   then recompute the remaining admissible experiments and their values. A
   different history need not always change an action, but the implementation
   must be capable of changing it when model predictions and values change.

The method claim additionally requires experience learned on earlier tasks to
improve later tasks. Low rank, residual learning, VOI, uncertainty, abstention and
LLM orchestration are established ingredients. If ordinary conditional regression
or standard design explains the gain, retain that workflow and reject the extra
method claim.

## Research procedures and transfer value

A research procedure is a small executable plan with a scientific objective,
competing observable predictions, required inputs and assay conditions, legal
steps, a feedback-dependent update rule and an explicit failure/stop rule. Its
record includes supporting and failed runs, provenance/dependence groups and
observed costs. Start with existing activity correction, conditional residual
transfer, fixed sparse design and source-restriction/check procedures; freeze
the eligible set in development. A new name or a different prompt is not a
different scientific procedure.

The proposed learned quantity is

`F_phi(procedure, predecision_history) = (expected_terminal_gain, transfer_failure_risk, total_cost, applicability_check)`.

Expected gain is relative to a specified conventional workflow under the same
total budget. Failure must be a frozen observable event, such as negative
transfer in terminal utility or an invalid assay execution, reported separately.
Cost includes the check, subsequent measurements, failures, controls, computation
and waiting, with resource units separated where appropriate. The check is chosen
from the legal action menu and may be omitted if proceeding directly is better.
An estimated risk is not a calibrated probability or an out-of-domain guarantee.

The first implementation should use a small regularised value model or table,
not train a new foundation model. Its features are available before the choice:
task objective, identity/structure, measured pre-treatment context, protocol,
source support, training-only model diagnostics and legally purchased outcomes.
Unknown dose/time/context metadata remains unknown. Hidden target profiles,
post-outcome subgroups and final success labels cannot be features. A target
L1000 perturbation profile is acquired information, not a zero-observation input.

Training labels require paired procedure outcomes on qualified source tasks, or
an explicitly identified policy-value estimator. A log containing only one
chosen procedure does not reveal what an unchosen procedure would have done.
If complete retrospective replay is used, disclose its coverage and selection;
if logged actions are used, audit action support and the estimator assumptions.
Otherwise value comparisons are unidentifiable: report `VALUE_LABELS_UNQUALIFIED`
and stop the learned transfer claim. Masked episodes do not create new independent
tasks or culture units. Procedures, response models and value models must all be
fit inside the source/outer training partition.

The central falsifiable claim is that this value-and-check rule improves future
drug decisions and reduces negative transfer beyond unconditional reuse, a
simple applicability gate, raw-history retrieval and standard adaptive design.
The old orbit gate lost to unconditional residual transfer; that result makes
both mandatory baselines. Cross-task data must show a real excess benefit before
adding learned routing, program generation or language-based memory.

## Feedback and research state

Keep the biological response distribution separate from the research state:

`p_theta(readout | pre-treatment_cell_context, drug, dose, exposure, sourced_prior, observed_history)`

`history_next = Update(history, chosen_action, measured_outcome)`.

Reading different wells changes knowledge; it is not a trajectory of one cell.
Without qualified longitudinal measurements, predict conditional responses
rather than continuous cellular dynamics. Joint candidate errors or contrast
distributions matter for selection; independently reported variances alone can
misstate ranking uncertainty when errors are correlated.

After each admissible outcome, update the bounded response component and the
procedure state, validate scope, and recompute remaining values. Begin with one
feedback round and at most one additional round if the first earns a useful
development gain. Reanalysis can produce a derived result but no new biological
measurement. Failed execution and missing outcomes consume declared resources
without becoming support for a biological explanation.

Let `V_B(history)` be the best terminal allocation without another information
action. Compare it with
`Q_B(check) = E_outcome[V_(B-check_cost)(Update(history, check, outcome))]`.
The remaining budget already charges the check. Do not subtract that assay cost
again from utility. Additional delay/monetary penalties need explicit units and
must not repeat a cost already included. This is standard decision theory; the
research challenge is estimating value when a response model or transferred
procedure may be misspecified, not introducing the formula itself.

## Dual core and implementation boundary

| Core | Research responsibility | Reuse and concrete gap |
|---|---|---|
| Virtual Cell | Endpoint and contrast distributions, observable differences between explanations, support/mismatch and permitted feedback updates | Reuse `virtual_cell.interface`, scoped RKT and study-local models. RNA/GCP certificates do not transfer to viability. Procedure applicability and value require task-level learning, not a transported certificate. |
| Scientific Agent | Propose/select/revise an executable research procedure; decide whether to reuse, check, restart or stop | Reuse planning, execution, budgets, review, CaseStore and recovery. New procedure/value logic starts in research. The thin loop currently has no automatic feedback-based refitting or replanning. |

Evidence authentication is shared infrastructure, not a third scientific core.
Extend existing records only when a study requires it. New scientific models and
policies stay in `research/` until scientifically validated. No parallel agent
platform, memory graph or data lake is needed for this programme.

Each proposal must name its claim, assay/context, prediction before the test,
competing prediction, distinguishing observation, failure condition, permitted
correction and cost. Initially use deterministic proposals: activity offset,
supported context correction, source restriction or refusal. A structural change
requires repeatable training/inner-development residual signal and a new frozen
evaluation; it cannot edit the success rule. Engagement, rescue, resistance or
other appropriate measured evidence is required for a mechanism statement.

Keep biological measurements separate from procedural experience. CaseStore may
retain when a workflow failed and what would allow reopening it. Generated data,
predicted fills and repeated text do not increase the experimental denominator.
Neither memory nor LLM value is presumed.

The joint learning object is procedure applicability and the feedback needed to
repair transfer. The Agent proposes and revises the plan; the Virtual Cell
constrains its predicted consequences and updates the response model. Shared
evidence can inform both updates without counting the same measurement twice.
This is not a third core or proof that either core has contributed independently.

The synthetic [loop audit](program_review_20261017/LOOP_AUDIT.json) executes both
the committed HEAD and the preserved working copy. In both, all-H1 and all-H2
fixtures choose A -> B -> C despite opposite support counts. At 16 identical
labels the smoothed share is 17/18; it reaches the default 0.95 threshold only
at 18. These are heuristic label shares, not likelihood posteriors. The source
already documents that limitation. Lowering the threshold would not supply
calibrated inference or feedback-driven replanning. The audit is engineering
diagnosis only; it opens no biological outcomes and changes no runtime code.

## Prior work and the novelty test

Official access and receipts are in the
[2026-10-16 review](program_review_20261016/SOURCES.json) and
[2026-10-17 review](program_review_20261017/SOURCES.json).
These are checked boundaries, not an exhaustive decision-focused design review.

| Work | Actual access in this revision | Overlap and implication |
|---|---|---|
| [Robin, Nature 2026](https://www.nature.com/articles/s41586-026-10652-y) | Official abstract and workflow/experiment passages | Literature, hypothesis, experiment suggestions and analysis with a repurposing case exist. A longer autonomous workflow is insufficient novelty; isolate same-budget decision gains. |
| [Co-Scientist, Nature 2026](https://www.nature.com/articles/s41586-026-10644-y) | Official abstract; published 19 May 2026 | Evolving competing hypotheses and biomedical experimental case studies are established; isolate useful plan revision from hypothesis-ranking improvement. |
| [AssayLoop, arXiv:2609.11877v1](https://arxiv.org/abs/2609.11877v1) | Official abstract, date and task description | Learned acquisition across historical **CRISPR** screens plus LLM priors and reported phenotype transfer. Relevant prior art, not small-molecule viability validation or proof of an unoccupied gap. |
| [MDA, arXiv:2608.09696v5](https://arxiv.org/html/2608.09696v5) | Reused cached text; model expansion, Bayes-risk design and patient-specific evaluation passages checked | Task-related VoI and residual-guided model expansion already exist. Glucose learners are fitted per virtual patient, not tested on unseen patients; that specific limitation does not prove all research-method transfer is new. |
| [LACE, Nature Machine Intelligence 2026](https://www.nature.com/articles/s42256-026-01307-8) | Official abstract/preview; published 1 October; subscription full text not audited | Complementary executable heuristic portfolios and bounded algorithm search exist. Biological applicability and negative-transfer control require a separate test. |
| [ACE, arXiv:2510.04618v3](https://arxiv.org/abs/2510.04618v3) | Official abstract; metadata identifies ICLR 2026 | Incremental strategy playbooks and experience accumulation exist. Use a matched text-playbook control; do not relabel stored context as learned biological applicability. |
| [GOLLuM, Nature Machine Intelligence 2026](https://www.nature.com/articles/s42256-026-01283-z) | Official abstract; published 28 August | Experimental feedback and Bayesian objectives already adapt LLM representations. No new embedding training is justified before small-model comparisons. |
| [MAP, Nature Machine Intelligence 2026](https://www.nature.com/articles/s42256-026-01286-w) | Official abstract; published 26 August | Knowledge-enhanced unprofiled-drug response prediction is a prior/baseline, not evidence of procedure transfer or functional benefit. Preserve the failed local pathway adapter verdict. |
| [PIE, Arc Institute](https://arcinstitute.org/news/pie) | Official 5 October 2026 announcement and linked preprint description; full paper not audited | Population response readouts and unseen perturbation/context tests motivate scoped prediction outputs. Author-reported molecular generalisation does not establish viability or research-method transfer. |
| [TxPert, Nature Biotechnology 2026](https://www.nature.com/articles/s41587-026-03113-4) | Official abstract; published 1 May | Multi-graph genetic perturbation response prediction is relevant prior art. Drug effects and knockdown are not interchangeable. |
| [BATCHIE, Nature Communications 2025](https://www.nature.com/articles/s41467-024-55287-7) | Official abstract and batch-design passages; publication date checked | Bayesian batch design and prospective combination screening exist. Actual batch/pool granularity and adaptivity are requirements, not novelty by themselves. |
| [ReDRAW, PMLR 331 (2026)](https://proceedings.mlr.press/v331/lanier26a.html) | Official proceedings abstract | Latent dynamics residual adaptation motivates limited corrections. Trajectories and a simulator do not justify one-assay biological identification. |
| [Token-World, arXiv:2610.00575v2](https://arxiv.org/abs/2610.00575v2) | Official abstract and version/date | Policy-facing compression motivates preserving decision information. Robotics findings do not establish biological sufficiency. |
| [ExecCritic, arXiv:2609.09133v1](https://arxiv.org/abs/2609.09133v1) | Official abstract | Qualified frozen tests before revision exist for code agents. Biological tests additionally need valid measurements and independent evaluation. |
| [DINO-WM, ICML 2025](https://proceedings.mlr.press/v267/zhou25t.html) and [Semantic World Models](https://arxiv.org/abs/2510.19818) | Official proceedings/arXiv abstracts | Planning in useful feature/semantic spaces exists. Biological features must correspond to measured readouts; label invention cannot supply a mechanistic endpoint. |
| [Online System Identification, RSS 2025](https://www.roboticsproceedings.org/rss21/p121.html) | Official proceedings abstract | Active parameter identification has guarantees under specified models/noise. Those assumptions do not establish biological safety or identifiability. |
| [R-IDeA, AISTATS 2026](https://proceedings.mlr.press/v300/tang26d.html) | Official proceedings abstract | Robust acquisition under misspecification already addresses representativeness/information/error amplification. Include an appropriate conventional robust design; information quantity alone is insufficient. |
| [Recoverable resolution preprint](https://www.biorxiv.org/content/10.64898/2026.09.30.755756v1) | Official page returned HTTP 429; supplied account remains unverified here | A literature lead, not verified support or an exclusive novelty claim. Do not use inaccessible numerical/method details. |
| [Autonomous Science Bench v0.1](https://arxiv.org/abs/2610.18449v1) | Official abstract/date | Separates discovery from held-out ranking; not a ready-made drug-discovery validation standard. |
| MAESTRO RKT, orbit contrast, indication triage and anchor studies | Local protocols, code and saved results | Transfer, residual correction, sparse design and adaptive acquisition exist. Refit versions alone are not new research; test contrast support and decision gains. |

TTSP and additional procedural-memory/model-call suggestions remain optional
leads. The required comparison now includes procedure portfolios, contextual
algorithm selection, meta-learning, transfer BO and off-policy evaluation as
well as Bayesian design. An applicability-value regressor alone may reduce to
a contextual bandit or algorithm selector. The distinctive claim must survive
those simple reductions and include useful checks or corrections on new tasks.
No claim of first method or established publishable novelty is made here.

## What existing evidence supports

The numerical register remains [research/EVIDENCE.md](../research/EVIDENCE.md).
This revision reconstructed all saved arm totals and the primary campaign
interval in indication triage without refitting or opening new responses.
Receipt and preservation hashes are in
[program_review_20261016/REVIEW.json](program_review_20261016/REVIEW.json).

| Existing result | Carry forward | Claim not established |
|---|---|---|
| RKT/Block Q: RNA prediction gain; fixed sparse design beat VOI | Scoped transfer and mandatory fixed-design comparator | General viability transfer or Agent superiority |
| GCP endpoint ranking: 55 -> 77/141 hits | Raw functional criteria and separate probability calibration | Transported calibration or mechanism/efficacy |
| PRESAGE P0: pathway 1,903 vs ungated-neighbour 2,223 hits | Preserve **NO-GO**, frozen failures and strong baselines | Revival of the pathway adapter or failure of every response model |
| Anchor: full X1 reference 1,357 vs context baseline 1,113 known hits | Observed profiles contain signal; offset cannot repair within-drug ranks | Affordable recoverability or independent purchasing value; **BLOCKED_INDEPENDENT_ENDPOINT** stands |
| Indication triage: simulated loop 395 vs two-stage 293 over 39 campaigns; +2.615/campaign, saved CI [1.667,3.615] reconstructed | Development lead and reusable implementation | Independent utility, new repair method, unique-candidate yield, LLM gain or strictly isolated policy test |
| Mechanism feasibility: zero measured mechanism references | Measured-truth requirement | Mechanism falsification from annotations or code contracts |

Indication triage observes a published response plus simulated noise and grades
the same profile. Probed pairs may be nominated; assay values are pooled/collapsed
and probe/follow-up budgets are separate. Tuning-fold model fits include later
estimation-fold labels, so the policy-selection test is not strictly nested.
Matrix-relative selectivity is not a measured target/control contrast. These
limitations constrain interpretation without rewriting that unrelated draft or
its `PASS` development gate. A new protocol needs isolated outer fitting, honest
action units, unknown bounds and all-in costs. Existing power calculations do
not transfer unchanged when endpoints, actions or dependence change.

## Validation stages for research method transfer

New scientific experiments are **DRAFT / NOT_RUN**. The 2026-10-17 executed
work is source review and synthetic control-flow diagnosis. Use the namespace
MT-P0/MT-P1/MT-P2 below; these stages do not reopen PRESAGE P1-P3 or its NO-GO.

| Stage | Question and bounded comparison | Gate and deliverable |
|---|---|---|
| MT-P0 Information and task qualification | Define A/B campaigns, actual bundles, observable contrasts, controls and missingness. Inner-select strong context/structure models, conditional residual and fixed/standard adaptive design. Test whether cheap inputs contain decision-relevant signal beyond these baselines. | Deliver a compact task/lineage manifest, frozen utility/cost assumptions and negative controls. Stop duplicated questions or unqualified value labels. Independent-endpoint failure limits claim level rather than forbidding every historical diagnostic. |
| MT-P1 Transfer of research procedures | Freeze a small procedure library. Learn value, failure boundaries and a check rule on source tasks; compare unconditional reuse, simple gate, retrieval and standard contextual selection. Update response and procedure only from legal feedback and replan. | Deliver the value model, complete histories and held-out source/target comparisons. Require useful future-task terminal gains, not just correct procedure labels. Stop if unconditional/simple methods match or beat it, or if value labels cannot be identified. |
| MT-P2 Dual core and qualified transfer | Freeze model/procedure/experience snapshots. Run A/B at one primary total budget; isolate model updates, procedure revision and cross-task experience, then qualify an external functional task and independent confirmation separately. | Deliver method/Agent/transfer/reliability verdicts with paired group intervals, costs and failures. Broad method claim requires A/B, and synergy requires the predeclared interaction test. No runtime promotion solely from synthetic checks. |

MT-P0 is the immediate scientific step. Preserve unseen compound connectivity
groups and known contexts first; create separate unseen-context and joint
unseen-compound/context partitions when they are supportable. Fix target and
comparison contexts from the biological objective and metadata. A pool/panel is
one acquisition action; scalar actions and prices remain hypothetical when no
authentic acquisition unit exists. Initially hold the response model and feedback
menu fixed to isolate whether contrast support predicts the value of a procedure.
At most two small representation sizes may be chosen in inner training.

The compact data plan is cached PRISM for functional development, scoped L1000
for molecular-response or acquired-information tests, and at most one
provenance-qualified external functional source. CTRP is already historically
exposed and its old raw archive is unavailable locally; GDSC2's fitted cache is
empty in the last audit. Neither becomes fresh confirmation by reacquisition.
Do not silently bridge unmatched doses, times or endpoints. A new cross-platform
functional task can be valid on its own terms after a new freeze, without
claiming a same-condition independent repeat or clearing the old anchor block.

## Comparators and contribution tests

Run staged comparisons rather than one large grid. First select the strongest
eligible context/structure predictor and fixed sparse workflow in inner
development, including strong ML+context where appropriate. Compare standard
BOED or robust acquisition and a fixed small procedure library under the same
information and all-in experimental cap. Noisy posterior gains are not evidence
that the selected action is useful.

Then isolate cross-task learning with five distinct experience conditions:
no cross-task experience, raw-history retrieval, an ACE-style text playbook,
conditional procedure transfer, and one predeclared permutation of procedure
applicability conditions within justified strata. Match available source runs,
context length or computation and experimental budgets. A text-playbook
implementation is an adaptation, not an ACE reproduction. Use task/identity
groups, not masked episode counts, as independent units. Freeze all tested
experience snapshots and evaluate them once; do not select the best snapshot
on confirmation tasks. Method-only comparisons can precede paid LLM baselines.

A same-model ordinary research loop and an MDA-style per-task discovery baseline
are relevant when their legal actions match. Freeze executable adaptations or
report `NOT_IMPLEMENTED`; do not claim superiority over paper names or unequal
tools. Retain unconditional residual and a simple gate in method attribution.
LLM-proposed programs must beat matched templates/simple search before an LLM
contribution is claimed.

For the two cores, use a predeclared 2 x 2 comparison: response update off/on
crossed with research-procedure revision off/on. A fixed recorded observation
history shared by all four cells isolates update and analysis-revision effects.
A separate closed-loop comparison permits different purchased observations at
the same cost and menu, measuring the total effect of experimental selection.
Do not simultaneously require identical histories and interpret that comparison
as the full acquisition-policy effect. Disabling a component must not allow
another component to implement the same update under another name.

On a frozen additive utility scale, interaction is
`U11 - U10 - U01 + U00`. Report paired independent-group intervals and the
predeclared multiplicity treatment. Full-system superiority to U00 is not
evidence of positive interaction. Distinguish deterministic plan-revision
benefit from LLM reasoning and from the value of the response model itself.

Report unseen compounds, unseen cell contexts and joint novelty separately, as
well as zero new observations versus few-observation adaptation. Context holdout
must exclude that context's outcome and procedure-value labels from source
training, not just remove its identifier from a split file. Freeze knowledge
timestamps and record unknown model pretraining exposure. Calibration/risk on
all candidates is not selected-candidate risk: separately report erroneous
progression, erroneous exclusion, refusal coverage and outcomes on actually
chosen candidates. Predeclared strong-activity/source-shift subgroups are useful
diagnostics; they do not justify post-hoc success claims or distribution-free
guarantees when exchangeability is absent.

Each protocol must define campaign, metadata eligibility, endpoint, observation
timing, bundles, replicate/control/failure costs, maximum rounds and the full
denominator including abstention. Missing, failed and inactive differ; report
unknown bounds. Count unique candidates in A and qualified pairs in B; charge
every required comparison-context assay. Functional differences are not molecular
mechanisms.

Use one cap for information plus confirmations and report actual spend, compute
and time separately. If only assay units are available, predeclare a small cost
grid without claiming dollar savings. Set minimum useful gain from campaign
throughput/cost before fitting. The old 0.10 hits/drug threshold does not transfer
automatically to unique candidates or selectivity. Freeze thresholds with an
attainable group-precision assessment before new evaluation, or report
`INCONCLUSIVE`. A/B primary claims require multiplicity handling and paired
independent campaign/family intervals. Profile error is secondary. Method,
Agent, transfer and independent-confirmation verdicts remain separate.

## Immediate operating decisions

Keep the dual core, scoped predictors, strong conventional/fixed workflows,
source verification, real measurements, negative results and bounded costs.
Do not reopen PRESAGE P1-P3, failed memory routes or an unqualified mechanism
algorithm. A wider programme does not reopen a stopped module automatically.

The missing asset for confirmed A/B discovery value is a provenance-qualified
set of compound/context measurements with authentic feedback bundles and
distinct functional confirmations, comparison contexts for selectivity claims,
and all attempted assays. Procedure transfer also needs identifiable source-task
value labels and enough independent source/target task groups. If those assets
are unavailable, specify one independent pilot and its costs, or retain an
explicitly limited development study. More datasets or a larger platform do not
substitute for them.

The first-stage deliverable is a reusable discovery method and campaign dossier:
candidate/context decisions, measured support, permitted model changes, falsified
or unresolved explanations, costs and follow-up requirements. Scientific strength
depends on measured gains over strong simple workflows and qualified transfer
and confirmation, not the breadth of the diagram or number of agent calls.

## Reproduce the engineering diagnosis

From the repository in the existing maestro environment:

```powershell
Set-Location D:\MAESTRO
& 'D:\anaconda\envs\maestro\python.exe' log/program_review_20261017/audit_loop.py --verify
```

This checks the saved synthetic audit and hashes of the preserved study/runtime
files. It does not fit a value model, establish biological applicability, test
an adaptive replacement loop or open a sealed dataset. The next scientific
experiment remains MT-P0, after a frozen task and procedure-value audit.
