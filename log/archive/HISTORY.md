# Archived research directions

These are historical decisions, not instructions to execute another experiment.
Current scientific closures remain in ../../research/REPORT.md and ../../research/EVIDENCE.md.
The only current execution handoff is [the dated brief](../20261020/NEXT_RESEARCH_PROMPT.md).

The five former direction/programme/cost/failure/register documents are consolidated below.
Original bytes, literature extracts and all three review packages are retained at
`D:/MAESTRO_maintenance_backups/20261020_deep_cleanup/log_original/`.
The full transfer review is `transfer_review_20261017/REVIEW.md` there. The programme
review packages contain source receipts and the synthetic loop audit, not new biological evidence.
For historical reproduction, restore the required files to their original `log/` paths first;
the archived audit_loop.py determines the workspace from that original location.
Frozen study documents may still name historical log paths; their bytes are intentionally preserved.
File-by-file original hashes and recovery paths are in [the maintenance receipt](../20261020/CLEANUP_FILES.json).


---

## Original DIRECTIONS.md

# Research Directions

Historical direction ledger; reconciled 2026-10-20. The next task is defined only by [NEXT_RESEARCH_PROMPT.md](../20261020/NEXT_RESEARCH_PROMPT.md). Later study audits and [research/REPORT.md](../../research/REPORT.md) override stale proposed continuations here.

Revised 2026-10-17. The [research programme](HISTORY.md) defines the
scope, existing evidence, novelty boundaries, task matrix and next study gates.

## Continue

1. Study complete early drug-discovery campaigns: biological objective,
   candidate/assay choices, measured feedback, bounded response-model correction,
   functional confirmation and an evidence-qualified progression decision.
2. Make candidate discovery/repurposing and cellular-context selection with
   failure analysis the two primary tasks. Selectivity needs comparison assays;
   molecular mechanism needs appropriate distinguishing measurements.
3. Focus technical work on transfer of research methods: learn applicability,
   negative-transfer risk, useful checks and permitted feedback-based revisions.
   Response differences that affect decisions supply the model-level foundation.
4. Reuse scoped RKT, conventional/context predictors, fixed designs, conditional
   models, acquisition and evidence contracts. Audit the existing indication-
   triage signal before implementing another low-rank model.
5. Keep source identity, dependence, training-only fitting, unknown-result bounds,
   outcome seals and the full campaign denominator. Separate method benefit,
   Agent increment, cross-task experience, source transfer and confirmation.
6. Recompute remaining predictions and action values after qualified feedback.
   Compare with static scores and ordinary adaptive design; record model and
   procedure versions. Heuristic label counts are not a scientific posterior.

7. Context transfer with verified bridges (`research/context_transfer_20261017`,
   confirmed once on Beat AML 2.0): keep bridge feedback (measure the model's
   top few items, then re-rank) and source-verified procedure choice, within the
   scope in the promoted docstrings. The basal-expression prior did not beat the
   item prior there; a new context-transfer claim must beat `item`, not only
   nearest-context transfer. The corrected batch lookahead needs its own fresh
   confirmation before any claim, ideally on a domain with uneven measurement.
8. Feedback attribution (`research/feedback_attribution_20261017`, development):
   * The confirmed gain is item-specific functional feedback. It is not the basal-RNA prior,
     procedure selection or overall-sensitivity calibration.
   * A drug-specific ridge on the same basal PCs is the strongest one-round comparator, and every
     future feedback claim must beat it.
   * Gate G1 ran (`research/beataml_g1_20261017`, development, $0) and **failed**: the frozen candidate
     (coherent score, exploit-first probes, k chosen on source patients) beats the ridge by +0.098
     [+0.045, +0.153], but the lower bound net of 0.05 per extra round is -0.005 (needs > 0.05). The probe
     round adds +0.125 to the low-rank model and +0.083 to a ridge; ridge-plus-feedback is within +0.015
     [-0.036, +0.066] of the candidate; the low-rank prior without observations is -0.027 [-0.065, +0.011]
     against the ridge. **Stop the low-rank state-model branch** on Beat AML.
   * Keep the feedback design pattern on the strongest prior, with the ridge as comparator (k = 8 is
     the post hoc best). Confirmation needs an unexposed, powered domain; none is local. The PRISM 24Q2
     metadata check needs authorisation.

9. Program revision (`research/program_revision_20261017`, method not supported) and its repair
   (`research/seed_attribution_20261017`, development):
   * The frozen evaluation was not one contract and its development bench trained on the reserved query
     outcomes. Corrected seed minus strong model: policy +0.356 [-0.088, +0.856], I2 +0.117 [-0.026,
     +0.248], I1 +0.283 [-0.065, +0.699]; all NOT_CONFIRMED. The earlier +0.21/+0.45/+0.44 are superseded.
   * A fixed textbook library of observably gated programs has a positive but unconfirmed effect on future
     lines (concentrated in BRAF/NRAS-mutant skin lines; negative on gate-negative lines). It exceeds all 20
     matched permutations, and a ridge on the same ten scope-by-gate features matches it: the information is
     in the pairings, not in capacity, per-drug loadings or uncertainty estimation.
   * Autonomous revision, stepwise search and the LLM add nothing to it. The primary LLM library equalled
     the fixed seed library; residual-coefficient sign disagreement (20-23% of LLM candidates) is not a
     measured biological error rate; seeded-arm ablations do not cover every empty-start program;
     same-screen future strata are not independent confirmation.
   * Do not run revision against within-lineage support/query arenas: the gates that pay in new
     lineages are rare there. A further attempt needs lineage-disjoint arenas, a pooled gate-count
     floor, and curated (non-LLM) proposals as the comparator for any LLM role.
   * In complete campaigns use exploit-first feedback, not up-front probes; the comparator for any
     new library claim is the seed library *and* a ridge on its features, not the strong model alone.
   * Any new replay must mask the reserved pool before every upstream fit and reveal outcomes only through
     the acquisition interface (`replay.MaskedBench`); keep shared historical data, incremental research,
     deployment, rounds, compute/curation and logical queries as separate cost accounts.

10. Feedback propagation (`research/feedback_propagation_20261018`, development, exposed PRISM folds 2-4):
   * The indication-triage utility is a re-read of probed cells (394/395 and 293/293 hits on probed pairs);
     grade only nominated unmeasured pairs. Use pool wells as the read unit and keep costs hypothetical.
   * Ridge-plus-feedback adds +1.06 events per 64 compounds over the structure prior at 3 pools (none at
     16 logical lines). The kNN-analogue repair (+0.14 [-0.58, +0.87]) and a leave-one-pool-out diagnosis
     (AUC 0.59-0.63; gate +0.28 [-0.17, +0.78]) add nothing reproducible; a second synthetic-noise draw moves
     the contrast by six-fold. **Do not launch a program search for the update rule.**
   * Any new claim must beat ridge-plus-feedback *and* kNN on unmeasured pairs, from independent, physically
     costed measurements (plate/well map, real replicates). Greedy value-based acquisition loses to the
     fixed A-optimal design on this utility.

11. Acquisition programs (`research/acquisition_program_20261018`, development): with probes unable to reveal target entries, a one-step
   posterior lookahead and an agent-searched value program do not beat the fixed A-optimal second pool on held-out groups (−0.106
   [−0.262, +0.022]; agent vs lookahead +0.008). The choice has only +7% hindsight headroom held-out. Keep ridge-plus-feedback with
   the fixed design as the reference; a future acquisition claim needs richer decisions (more adaptive steps, other utilities) and
   independent measurements, not more proposals on these ten features.

12. Observable-state discovery (`research/observable_state_20261018`, development, exposed PRISM 19Q4): 136 MoA families, one typed edit per
   family per arm, confirmed on held-out compounds x held-out lineages. Confirmation rates: random 0.051, enumerator 0.059, target-gene rule 0.088,
   deepseek-flash agent 0.081, identity-masked agent 0.059. Agent - enumerator +0.022 [-0.022, +0.074]; agent claim and typed-edit thesis withdrawn
   for this arena (not a project-wide STOP). Only live lead: knowledge-informed state variables (target-gene rule - random +0.037, unadjusted p 0.028).
   Agents stated p about 0.45 against 0.08 observed. Decision-level secondary (S2) not run. See `REPORT_OBS.md`.
   * Interpretation: this withdraws the Agent and typed-edit claims for this closed-vocabulary, one-bet-per-family arena; it does not test
     other edit primitives or decision utility. Treat target-gene state as an unconfirmed exploratory lead only. Do not start another Agent
     proposal search on the same exposed arena; independent, powered validation and a decision-level estimand are prerequisites for revival.

13. EG-RPT policy transfer (`research/eg_rpt_20261019`, DRAFT protocol, no result): first gate is a split-noise reliability test of policy-selection headroom,
   because the campaign-level best-of figure (131 vs 100) is what Gaussian noise of the observed SD would produce (mean |d| 1.86 vs 1.95; predictor hit counts correlate 0.27).
   Only if headroom is reproducible are non-LLM meta-selectors, a Virtual Cell reliability gate and then an agent compared on a generated PRISM task panel. The 13
   study-level records (4 dependence groups, 6 units) cannot train a transfer model. Not frozen; needs review.

14. MAESTRO-FAR (`research/maestro_far_20261019`, ran 2026-10-19): FAR_NOT_SUPPORTED in the PRISM x L1000 x ECFP arena. Failure signatures AUROC ~0.5 (select/test/vault);
   FAR slice choice does not beat exploit-first (test +0.006 [-0.003, +0.018], threshold 0.010); assay + repair itself helps (+0.04) but not FAR-specifically. Reproducible slice value
   exists (split-line oracle +0.059 over random) but nothing pre-assay predicts it. Agent/2x2/transfer phases not run per frozen rule. Next only with a new frozen protocol and fresh
   data: what predicts slice value (MoA/target knowledge is the untested information source).
   Audit (`research/maestro_far_20261019/audit_20261019/REPORT.md`): original-environment replay matches, but search/select/test references are not strictly isolated,
   four slices have unequal drug counts, and secondary MoA labels cross folds. Correct these contracts and pin runtime dependencies before opening a new feature branch.
   Working entry: `research/maestro_far_20261019/README.md`; redundant driver code/duplicate files removed, read-only verification and early overwrite guards tested.

15. RSD (`research/replicate_decisions_20261019`, ran 2026-10-19): REVISE. A Virtual Cell posterior whose signal/noise geometry is identified from replicate plates
   of reference compounds (Noise2Noise-style cross-replicate covariance, reference-only selection) improves within-compound context selection on new classes
   (+0.118, equals a second read at half the wells, holds on the primary-screen run) and removes 94% of selected-candidate optimism, but does not improve
   cross-compound progression, its selected-pair intervals are too narrow (0.675 at 80%), KG escalation ties exploit-first and the chemistry prior hurts.
   Next: heavy-tailed pair-noise posterior, frozen on this arena, then tested on an unopened tier (other HTS002 doses for development; PRISM 24Q2 needs authorisation).

16. Decoupled RSD calibration (`research/decoupled_calibration_rsd_20261019`): the filesystem contains `FREEZE.json` and `DEV_RESULT.json`.
   This is completed development readout, not independent confirmation. Keep Gaussian RSD decisions fixed; do not reopen any tier.
   The earlier pre-freeze status was stale. See the saved result and protocol for the exact calibration-only scope.

## Next bounded step

**Programme-wide prerequisite: MT-P0.** Qualify a compact A/B task, lineage, action,
cost and dependence manifest before fitting any cross-task procedure-value rule. Start
with unseen compound groups and known contexts; qualify new-context and joint holdouts
separately. Keep a small procedure library, ordinary conditional regression,
unconditional residual, simple gate and standard design. A logged unchosen procedure has
no observed counterfactual utility.

For the observable-state lead, do not run further proposals on exposed PRISM families. First
qualify whether any independent, powered source can test the target-gene state and define a
decision-level endpoint. If neither is available, retain the lead as exploratory and do not
promote it; S2 from the current study was not run.

**Beat AML question: G1 is done.** It failed and the low-rank state-model branch is stopped (see item 8).
The only conditionally permitted continuation is a confirmation of the exploit-first feedback pattern on
a new, independent, powered domain, with ridge-plus-feedback as comparator and the round value declared in
advance. No such domain is local, so this is blocked, not scheduled.

**PRISM question: NO-GO for autonomous applicability-boundary revision.** The opportunity gates did
not pass (no primary seed test has a positive lower bound under the corrected contract), so no revision
protocol is drafted and no revision, LLM-proposal or grammar-search campaign starts. A later attempt needs
a masked replay, lineage-disjoint arenas that meet the pooled gate-count floor, curated non-LLM proposals
as the comparator and a practical target of at least +0.10 hits per line with a positive lower bound under
the preregistered multiplicity rule. PRISM 24Q2 REP.1M remains sealed until access is authorised and
independence is verified; public-metadata checks may proceed within existing authorisation and must record
access status, provenance, prior exposure, overlap and task compatibility separately. Same-screen future
strata are not independent confirmation.

The [synthetic loop audit](D:/MAESTRO_maintenance_backups/20261020_deep_cleanup/log_original/program_review_20261017/LOOP_AUDIT.json) reproduces
static A -> B -> C ordering under opposite feedback in both HEAD and the working
copy. It is an engineering diagnosis, not new biological evidence or a repaired
adaptive loop. MT-P1 tests procedure transfer; MT-P2 tests dual-core contribution,
selected-candidate risk and qualified external transfer. These stage names do not
reopen PRESAGE P1-P3. No sealed tier is opened by this plan.

## Defer

- LLM-generated procedures or model changes: first show a deterministic method
  gain, then compare with templates, simple search and text-playbook retrieval.
  Match source experience, tools, experimental/compute budgets and legal inputs.
  Use shared histories for component isolation and separate cost-matched closed
  loops for total acquisition effects.
- Mechanism inference: first obtain measured competing predictions, engagement,
  rescue or other appropriate distinguishing evidence.
- Dose/time or combinations: extend one supported condition axis after the main
  tasks; compare with established batch-design methods.
- New diseases, patient response, safety and therapeutic-window claims: qualify
  the relevant populations, controls and functional endpoints first.

## Stop

- Preserve PRESAGE P0 **NO-GO**; do not restart P1-P3 or pathway tuning.
- Preserve anchor-study **BLOCKED_INDEPENDENT_ENDPOINT**; do not generalise
  offset-only ranking failure to every discovery task or every anchor model.
- Keep the thin Auto-Research loop as infrastructure. Static information scores,
  hypothesis-label counts and software receipts are not discovery utility.
- Stop an added method that loses to simple conditional/fixed workflows; stop
  an Agent claim that disappears under a matched no-LLM comparison.
- Stop learned procedure-value claims if labels or action support are unqualified;
  do not call larger memory, a programme schema or masked episodes new learning.
- Stop development of the low-rank bridged state model on Beat AML (G1 failed); stop revision,
  stepwise, LLM-proposal and grammar-search work on the PRISM seed arena; the earlier reported
  PRISM seed gains are superseded by the corrected contract.
- Stop covariance-inflation repair and model averaging of the bridged prior
  (harmful or neutral in development, neutral on Beat AML) and the LLM bridge
  picker (no gain over exploit-first or the corrected lookahead).
- Stop additions of agents, memory, tools or datasets without a distinct,
  testable scientific question. Predictions and annotations are not measurements.
- Stop same-family drug-substitution work on Jaaks 2022 (2026-10-19: `action_substitution_20261019`
  NARROW, `kinobeads_substitution_20261019` NOT_SUPPORTED, `biological_residual_gate_20261019`
  UNDERPOWERED with Gate 3 FAIL): learned action units, target-annotation or binding features beyond
  functional similarity, and Agent/Virtual Cell layers on this task. The reproducible selection
  opportunity among alternatives (0.012 ECB-like units) is below the useful minimum (0.02). Keep the
  functional-similarity kernel as reference and feedback on the strongest prior. A new attempt needs a
  different action space; the AstraZeneca 2024 matrix screen (figshare 163378, unopened) is the only
  qualified candidate and needs approval plus a protocol whose first endpoint is the reproducible opportunity.


---

## Original RESEARCH_PROGRAM.md

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

The synthetic [loop audit](D:/MAESTRO_maintenance_backups/20261020_deep_cleanup/log_original/program_review_20261017/LOOP_AUDIT.json) executes both
the committed HEAD and the preserved working copy. In both, all-H1 and all-H2
fixtures choose A -> B -> C despite opposite support counts. At 16 identical
labels the smoothed share is 17/18; it reaches the default 0.95 threshold only
at 18. These are heuristic label shares, not likelihood posteriors. The source
already documents that limitation. Lowering the threshold would not supply
calibrated inference or feedback-driven replanning. The audit is engineering
diagnosis only; it opens no biological outcomes and changes no runtime code.

## Prior work and the novelty test

Official access and receipts are in the
[2026-10-16 review](D:/MAESTRO_maintenance_backups/20261020_deep_cleanup/log_original/program_review_20261016/SOURCES.json) and
[2026-10-17 review](D:/MAESTRO_maintenance_backups/20261020_deep_cleanup/log_original/program_review_20261017/SOURCES.json).
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

The numerical register remains [research/EVIDENCE.md](../../research/EVIDENCE.md).
This revision reconstructed all saved arm totals and the primary campaign
interval in indication triage without refitting or opening new responses.
Receipt and preservation hashes are in
[program_review_20261016/REVIEW.json](D:/MAESTRO_maintenance_backups/20261020_deep_cleanup/log_original/program_review_20261016/REVIEW.json).

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


---

## Original FAILURE_MODES.md

# Failures and Blockers

- **Agent synergy did not replicate:** matched pilot and GCP transfer did not exceed deterministic baselines; retain the data and negative conclusions.
- **Closed-loop P2 was not confirmed:** MAESTRO_LOOP 23 vs CONV_LOOP 18, p=.18; do not claim a closed-loop advantage.
- **Knowledge gain was mechanism-class confounding:** gene relabelling reproduced the gain, while target/context/provenance routes added none.
- **Prediction-as-evidence:** writing predictions into evidence caused 15 false NO-GOs; decisions must pass measured-evidence admission.
- **Endpoint unit error:** historical test viability was incorrectly divided by 100 as a percentage; fixed to read metadata/fixed units, preserving the excluded run and deviation note.
- **Mechanism truth is missing:** the local 61,413 annotation pairs have no measured positive/negative reference; the benchmark cannot substitute for scientific validation. Status: `ASSET_BLOCKED`.
- **Weak cold-start generalization:** transfer gains depend on declared source/assay/context and must not be generalized to drug discovery overall.
- **Batch-lookahead baseline defect (2026-10-17):** after its first greedy pick the lookahead bridge shrank the covariance but kept the prior hit chances as the baseline, biasing every later candidate low; weighted by measurement rate, the bias chose rarely measured items (29% of Beat AML bridge wells measured). Uniform measurement on PRISM (q about 0.975) hid it during development. The source-verified selector rejected the procedure in all folds. Fixed in `agent.bridge_design` (rule `lookahead`; frozen rule kept as `lookahead_v1`); the fix is post hoc and unconfirmed.
- **Process-report field not swapped (2026-10-17):** `confirm.py` replaced `maestro` hits with the selected procedure's but kept the lookahead's wasted-well count (4.81 vs the correct 2.53). Descriptive only; recorded in the study's `DEVIATIONS.json`.
- **Wrong pre-registered expectation (2026-10-17):** AML-shaped PRISM proxies predicted the agent would decline to bridge and the verdict would be PARTIAL; on real patient samples it bridged and the verdict was CONFIRMED. Proxies built from another domain did not predict which procedure pays.
- **Incoherent event score (2026-10-17):** the promoted `BridgedTransferModel.event_prob` sets each threshold from the median of the *predicted* mean and divides by sd(Y_d), ignoring the uncertainty in G. The target event therefore moves with every update and the score is not a martingale (counterexample 0.163 -> 0.000178 after any readout; Beat AML top-50 expected drift -0.0067). On the model's population state it ranks by total variance, including overall sensitivity that the endpoint removes (A 0.312 vs empirical item prior 0.402). A coherent scorer (fixed event, Var(Y_d - b_d G)) is development code in `research/feedback_attribution_20261017/coherent.py`; it improves ranking but not calibration.
- **Thin Gaussian tails (2026-10-17):** the low-rank model's own exact-endpoint probability for a z <= -3 event is too low (0.015 vs observed 0.021), and its EVSI under-states realised feedback gains by 1.5-1.9x. Coherence does not fix calibration.
- **Claim mapping misaligned with tests (2026-10-17):** in the context-transfer confirmation, "agent adaptivity" was decided by a trivially met non-inferiority test (P5) and "beats fixed pipelines" passed through a contrast against a defective comparator (P6); Holm-positive results were reported without the minimum useful effect. Claims are now graded separately (`context_transfer_20261017/CLAIMS.json`).
- **Weak comparators inflate attribution (2026-10-17):** contrasts against the low-rank model's own population state or Virtual Cell prior look large (+0.07 to +0.10) because those comparators are poor; against the empirical item prior or a drug-specific ridge on the same PCs, the RNA prior shows no gain and the confirmed two-round engine is not shown better (D - S_ridge +0.023 [-0.029, +0.077], post hoc). Always include the strongest simple static model.
- **Descriptive count error (2026-10-17):** post-run prose gave 166 inhibitors; the analysed matrix has 165 (census count vs RNA-seq-matched matrix). Recorded in the study's DEVIATIONS.json; no result affected.
- **Misaligned development arena (2026-10-17):** in `program_revision_20261017` the frozen acceptance rule ran its distinguishing experiments on query lines of the same source lineages. The gates that carried the seed library's gain on unseen lineages were rare there (BRAF-mutant 6 vs 37, PIK3CA 12 vs 30), so the rule would have rejected RAF x BRAF and PI3K x PIK3CA, and revision accepted almost nothing. Development arenas must sample the strata the claim is about.
- **LLM direction errors (2026-10-17):** 20-23% of deepseek-flash program proposals committed the wrong sign (e.g. MDM inhibitor x TP53 mutation as sensitising). The committed-direction check caught them; keep direction commitments in any proposal contract.
- **Lost acceptance digest (2026-10-17):** `evaluate_edit` returned the commit dict instead of (commit, digest) after a measurement edit, crashing the next step; the smoke run missed it because its budget ran out first. Fixed before the freeze (PROTOCOL.md section 0).
- **Baselines inheriting the method's inner choice (2026-10-19):** when reference-only selection switched the RSD chemistry prior off, `vc_only` became a zero matrix and `fusion` collapsed onto scalar shrinkage because both read the chosen model's prior. Caught on the search block before the freeze; baselines now keep their own definitions (`replicate_decisions_20261019`).
- **Bootstrap duplicates corrupt kNN priors (2026-10-19):** cluster-bootstrap refits with duplicated reference compounds filled the kNN neighbour sets and depressed refit utility (D1 +0.008 to +0.023 vs +0.043 unresampled). Use subsamples without replacement for training-variability refits of neighbour-based models.
- **Heredoc broke an escape (2026-10-19):** a Bash heredoc turned the escaped CR-LF bytes literal (backslash-r backslash-n) into a raw line break, so a stage crashed on import. Write Python files with the Write/Edit tools, not heredocs.
- **Empty panel column (2026-10-19):** PRISM 19Q4 HTS002 lists ACH-001192 (pool P933) with no 2.5 uM read for any compound; its reference mean is NaN, which made an exact-equality isolation test fail. Use NaN-aware comparisons; 480 of 481 lines are informative.
- **Too-wide adequacy band (2026-10-19):** the agent's posterior-predictive check (mean z^2 in [0.67, 1.5]) raised no flag while 80% intervals covered only 0.675 of selected pairs. Check adequacy on the selected candidates, not on all purchased reads.
- **Composite drugs as annotation siblings (2026-10-19):** Jaaks 2022 lists the pre-combined anchor "Afatinib|Trametinib" (5,527 colon rows) as a drug; target-set overlap made it a "sibling" of every EGFR and MEK drug and inflated the gate's target class (1,568 vs 1,027 units). Exclude names containing "|" before building drug families (`action_substitution_20261019`).
- **Annotation overlap is a coarse family (2026-10-19):** "shares an annotated target" groups tight EGFR/HER2 inhibitors (sibling copy is the best predictor) with promiscuous multi-kinase drugs such as Sorafenib/Dasatinib/Axitinib (sibling copy is the worst). Pooled over families, the sibling is no better than ignoring drug identity; report per-family results.


---

## Original COSTS.md

# Costs and Asset Boundaries

- Protocols, freezes, results, claims, deviations, artifacts, audit logs, and verification scripts at research roots are evidence and must be retained.
- `data/external/` (about 61 GB) contains original external data and models, not temporary caches; retain it.
- Large arrays and models in `research/knowledge_transfer_20261012/cache/` remain referenced by freezes, input audits, or replays and must not be removed wholesale.
- Dry-run caches and pytest temporary output are regenerable; before cleanup, record paths, sizes, hashes, and reference checks.
- Preserve provider calls, download states, and not-run states recorded in research materials; do not report an experiment as successful if no call occurred.
- 2026-10-17 `context_transfer_20261017`: Beat AML 2.0 release files (about 354 MB) in `data/external/beataml2_20261017/`, hashed by the study freeze; retain. deepseek-flash spend 0.2768 USD (confirmation LLM arm, 520 calls) plus 0.0156 USD (PRISM pilot); 0 wells purchased; 2,209 s confirmation run.
- 2026-10-17 `feedback_attribution_20261017`: 0 wells, 0 USD, no provider calls, no downloads; local compute only (registered runs about 18 min wall clock on 28 CPUs). Reads the confirmation's Beat AML domain cache and raw inhibitor file, already retained. Records and caches in `tmp/feedback_attribution_20261017/` are regenerable from the frozen code.
- 2026-10-17 `program_revision_20261017`: 0 purchased wells (archived PRISM 19Q4 outcomes; development wells are charged in the analysis, about 4,300 per revision arm and 167,722 for stepwise search), deepseek-flash 0.287 USD over 90 calls (0.088 pre-freeze smoke), no downloads. Reads `data/external/prism_19q4/raw` and DepMap features, already retained. Per-line records and the ledger are retained in the study's `records/`; the rest of `tmp/program_revision_20261017/` is regenerable.
- 2026-10-18 `observable_state_20261018`: 0 purchased wells; 272 deepseek-flash calls, token/USD cost not logged by the client; no downloads or independent data. One masked transfer read released 3,261 edit records from exposed PRISM 19Q4 (`ACCESS_LEDGER.jsonl`); retain the ledger and records as study evidence.
- 2026-10-19 `action_substitution_20261019`: 0 wells, 0 USD, no provider calls. One approved download: Jaaks 2022 figshare files (original and validation fitted data, raw-data zip, glossary; about 271 MB) into `data/external/gdsc_combinations/jaaks2022_figshare/`; retain (hashed by the study). Local compute about 1.5 h wall clock (phase 2 dominates). `cache/plates.csv` is regenerable with `plates.py`.
- 2026-10-19 `biological_residual_gate_20261019`: 0 wells, 0 USD, no provider calls, no downloads; about 17 min local compute (smoke plus one P0 run). Reads the Jaaks files and frozen action-substitution tables already retained. External datasets were checked at publication-metadata level only (no outcome file opened).


---

## Original EXPERIMENT_REGISTER.md

# Experiment register

The authoritative machine-readable registration is [research/STUDIES.json](../../research/STUDIES.json).
Questions, exposure, units, comparators, corrections and final stop/continue decisions are in
[research/REPORT.md](../../research/REPORT.md); estimates and evidence pointers are in
[research/EVIDENCE.md](../../research/EVIDENCE.md). Original study packages retain their detailed records.

The previous duplicate table and one-page `log/studies` reports were consolidated on 2026-10-20;
see [CLEANUP_MANIFEST.md](../20261020/PREPARATION.md) for exact restoration paths and hashes.
A `frozen` registry status is not a positive scientific verdict.
