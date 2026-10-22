# Functional dynamics: measured simple-updater gate and adversarial decision

2026-10-22. **STOP_THIS_SIMPLE_CONFIGURATION; NO_NEW_CORE_ESTABLISHED; KEEP_QUALIFIED_DATA.** This is progress on the active research goal, not its completion. The closed-form birth/death update is an exact ordinary empirical-Bayes operation. A separately preregistered real net-count experiment also fails its useful-gain gate. Neither result proves that every live/dead world model or every RSI mechanism fails. Historical STOPs and their frozen evidence remain unchanged.

## Concrete mechanisms and closest prior work

Three independent drafts and actual two-way cross-examination were completed before this decision: [advocate](advocate/INDEPENDENT.md), [scientific skeptic](skeptic/INDEPENDENT.md), [functional-data auditor](functional_auditor/DRAFT.md), with their CROSS/REPLY files. Independent [post-gate support review](advocate/POST_GATE.md) and [implementation/scientific review](skeptic/POST_RUN_REVIEW.md), followed by actual cross-examination, both stop this configuration. Their48-check non-fitting audit passes. No consensus vote substitutes for measured evidence.

The advocate proposed observing live L and cumulative death events K, using exposure E=integral Ldt to derive birth B=deltaL+deltaK and death D=deltaK, then inheriting two feedback trust parameters kappa_birth/death. Its update `(kappa*rate0+count)/(kappa+E)` is exactly a Gamma–Poisson posterior mean; historical tuning is ordinary empirical Bayes/meta-learning and same-program search. Thus **algorithm novelty is NONE** for this exact operation. A narrower cross-task empirical property (channel-specific feedback trust transfers) was not already answered merely by this mathematical equivalence, but is still untested here.

[BESTDR, Cancer Research2026](https://doi.org/10.1158/0008-5472.CAN-25-1181), [retained primary](skeptic/BESTDR_PRIMARY.body), already models division/death/state transitions, stochastic count variance, measurement error, dead clearance, flexible dose-response and hierarchical sharing. Time-homogeneous kinetics, early drug delay and process/observation variance confounding are explicit limitations; common linear-chain/time-varying extensions are not new inventions. Same-information ordinary posterior/refit and these extensions are required future controls. The exact new candidate would need an empirical constraint or a distinctly implemented useful operator beyond naming residuals or sharing priors.

[Forcina/STACK2017](https://pmc.ncbi.nlm.nih.gov/articles/PMC5509363/) supports real live/dead kinetics across1819compounds and two cell-line contexts, but this scout stopped before authenticating exact raw-file objects. Its past-max-dead lethal fraction is not cumulative death events; future maxima must never enter an early prefix. [SpecRSI2026v1](https://arxiv.org/html/2610.16491v1) is retained as a current program/improver-method neighbor, not biological performance evidence. The bounded primary search is not exhaustive novelty certification.

## Authenticated data and application

Root acquired exact manifest-matching HTS001 and two HCT116 CSVs; full bodies/receipts/checksums are in root_scout/. HCT116 has live/dead stocks and spatial subregions, not authenticated cumulative death. Replicates file:5472rows,96wells times3images times19frames0–72h; dose-series:6624rows,96wells times3images times23frames0–88h. Its seed labels and independent biological-run mapping are not certified. Response values remain header/identity-only in this phase. See [measurement semantics](skeptic/BESTDR_MEASUREMENT_SEMANTICS.md).

HTS001 has7PC9-derived backgrounds,14noncontrol drugs,oneplate/background, no expt.id column in the actual8-column CSV. It is nuclei count/viability proxy, not a birth/death assay. After identity-only qualification, all1960noncontrol well trajectories qualified (no exclusions). Drug IDs were immutably split8train/3validation/3test, carrying all doses/backgrounds/wells together. Test drugs are dactolisib,osimertinib,temsirolimus;420test wells do not increase independent task n beyond3drugs. Background/plate effects and biological-run generalization are inseparable.

Registered application: early drug-response monitoring, using legal<=34h readouts to forecast same-well nuclei counts near60h, before the documented72h drug replacement. No drug-candidate ranking, wetlab acquisition utility, latent-rate truth or clinical efficacy was measured. The application and stop margins are defined in [the frozen protocol](HTS001_GATE_PROTOCOL.md), with [independent pre-run review](skeptic/PRE_RUN_REVIEW.md). Count target is log2(N+1); target time was selected using timestamps only. This is a literature-exposed, within-screen exploratory holdout, not blind confirmation.

## One measured experiment

Elementary world state s=log2(N+1), ds/dt=r. From the same fresh<=24h theta0 and identical24–34h feedback, compare fixed local refit psi0 and historically learned slope-mixing alpha psi1. No repaired target theta crosses tasks. Direct predictors get the same r0/r1/current state/horizon plus common prefix interpolation, concentration and background features. Fourteen Ridge/HGB/ExtraTrees configurations were validation-selected; selected ExtraTrees was refit ontrain+validation. Alpha searched11training-only programs; the same11-program ordinary search was independently evaluated. Full configuration/budgets/predictions were saved before test-target numerical access.

Primary test macro MAE, lower better (equal drug→background→dose→well):

| Method | MAE |
|---|---:|
| Persistence |0.886875|
| Frozen initial model |0.431830|
| New state readout, old rate |0.317892|
| Ordinary full-prefix rate refit |0.229256|
| Fixed local-window updater psi0 |0.303590|
| Inherited alpha=.5 updater psi1 |0.230026|
| Equal-budget same-program search |0.230026|
| Preset50/50 mixture |0.230026|
| Shared training-rate prior |0.300806|
| Half prior/local warm start |0.245843|
| Prior plus inherited alpha |0.245843|
| Validation-selected strong direct |0.179086|
| Direct/world half blend |0.178211|

The inherited update improves fixed local refit by0.073564MAE (24.2%) from identical starts/feedback. All three drug-specific descriptive gains are positive, but the frozen useful-gain condition required both >=0.10absolute and>=10%relative improvement. The absolute margin fails. It is also0.050940MAE worse than selected direct and0.000771worse than ordinary full-prefix refit. Preset.5mixture and conventional equal-budget search exactly duplicate every inherited prediction; thus this test does not establish that learned inheritance is necessary. The direct/world blend gains only0.000875MAE (about0.49%) over direct, far below the frozen useful margin, with no agent involved.

Saved [result](hts_gate/RESULT.json), [pre-target model freeze](hts_gate/MODEL_FREEZE_BEFORE_TEST_TARGETS.json) and [identity split](hts_gate/IDENTITY_SPLIT_BEFORE_RESPONSES.json) contain full trials and per-drug behavior. Three-drug conditional bootstrap is descriptive sensitivity; its bounds are not reliable independent-run inference. No endpoint/window/split/threshold was changed after outcomes. No second model fit was launched to repair a scientific failure.

## Attribution and what is still unverified

| User-required effect/comparison | Actual status |
|---|---|
| World-model contribution | This elementary net-growth configuration does not beat the selected direct predictor or full-prefix refit. This is not a result for full stochastic/live-dead/molecular world models. |
| Agent contribution | NOT_TESTED: no executable learned research/acquisition agent was added. |
| Procedure inheritance | Common-fresh-start future-update contrast measured; positive descriptive conventional meta-update, below absolute threshold and fully matched by preset mixture/search. No exclusive inherited gain established. |
| Weight/continual inheritance | Simple shared-rate prior/warm-start surrogate measured; full CL/replay framework NOT_TESTED. |
| World+agent joint gain | NOT_TESTED; a small predictor blend is not a world-agent joint experiment. |
| RSI: better later improvements | The minimal psi0/psi1 future-update contrast was executed; it yields ordinary slope mixing, not a distinct self-improving strategy. No learned revision of the improver-learning procedure or validated RSI core established. |
| Strong direct, ordinary refit, simple mixtures | Measured within the frozen scope. |
| Active learning / real experimental decisions | NOT_TESTED. No unobserved dose/schedule oracle or wetlab cost was invented. |
| Equal-budget program search | Exactly matched11alpha programs and data; identical predictions. General program-space search NOT_TESTED. |

Fairness limit: preregistered direct refits ontrain+validation; inherited alpha/prior use training only. This intentionally strong baseline has more pooled labels, so the numerical direct gap alone does not isolate an information/capacity-matched universal world effect. The equal-budget search/preset mixture identity and ordinary refit result do not depend on that asymmetry. Direct features include the candidate's sufficient r0/r1/state/horizon, but this is not a comprehensive comparison of sequence architectures or all drug representations.

## Action and stopping boundary

Stop expanding or renaming this net-growth/slope-shrinkage configuration. Stop claiming the exact closed-form birth/death kappa update as a new algorithm. Keep the authenticated real count assets and conventional updater observation. Do not retroactively call this test a validation of dual-channel feedback trust, molecular mechanism, clinical discovery or RSI.

An independently preregistered live+dead-stock study could still be legitimate, but requires calibrated stock/clearance/measurement semantics; live-only versus live+dead information controls; ordinary stochastic/clearance/noise models and refit/EB; same-information strong direct/mixture/search; and fresh-start later-update contrasts over actual drug/background/batch opportunities. First establish a useful new empirical property or distinct operator in independent opposing review; do not add an agent layer merely because this gate is negative. No particular followup is claimed executed here, and no new architecture is approved by this decision.

[Work/failures/exposures](WORK_AND_FAILURES.md) and [verification/resource ledger](VERIFICATION.json) preserve failures and accounting:26publicGET,5573807HTTP-body bytes,one11488-token DeepSeek logical completion,one measured gate,7synthetic tests,80root integrity/metric checks and48independent non-fitting audit checks passing. These counts overlap in subject matter and are not independent experimental replicates. New code/tests are only in research/functional_dynamics_gate_20261022/. The overall goal is still ACTIVE/NOT_ACHIEVED; the current turn is PROGRESS, not a repeated blocker and not a claim of completed discovery.
