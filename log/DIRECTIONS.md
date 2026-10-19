# Research Directions

Revised 2026-10-17. The [research programme](RESEARCH_PROGRAM.md) defines the
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

16. Decoupled RSD calibration (`research/decoupled_calibration_rsd_20261019`): pre-freeze exploration. It keeps the frozen Gaussian RSD rankings for D1/D2 and tests whether
   compound-level heavy-tailed predictive intervals improve calibration without changing decisions. A smoke run and protocol draft exist; `FREEZE.json` and `DEV_RESULT.json` do not.
   Do not treat it as evidence or open a confirmatory arena; review and freeze the protocol before the planned development readout.

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

The [synthetic loop audit](program_review_20261017/LOOP_AUDIT.json) reproduces
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
