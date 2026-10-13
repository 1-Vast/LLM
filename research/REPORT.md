# MAESTRO Repository Consolidation Report

## Current research update: orbit-contrast evidence admission, 2026-10-13

The English [orbit-contrast report](orbit_contrast_20261013/README.md) answers Brief 6. The
question: is there a general inference rule that credits and uses knowledge only for what it says
about an entity's identity? The candidate is OCEA. It splits each knowledge route's prediction
into its mean over 16 stratum-preserving relabellings of the knowledge (generic) and the residual
(identity), and admits the residual per query through a gate trained on held-out identity
contrasts.

The study was pre-registered and frozen (21 files). It was then validated once on two exposed
L1000 tasks: cold-start compound responses (A′: 392 compounds, 805 active cells) and unseen-gene
shRNA knockdowns (B: 3,481 genes).

* **Controls.** The self-knockdown positive control is detected (+0.0998, p < 0.0001). End-to-end
  relabelled knowledge earns nothing (mean −0.0002 in both tasks).
* **A′ (H1 passes).** Knowledge carries identity-specific value: Δ_id +0.0104 [+0.0074,
  +0.0140], p < 0.0001.
  * Its orbit-mean (generic) part adds only +0.0010.
  * The value is mechanism-class membership: removing `know` loses +0.0099. Removing the signed
    knockdown route loses +0.0005 (CI includes 0).
  * Flipping target signs reverses the knockdown route's identity contrast (+0.0291 → −0.0303).
    That signal is real but redundant with mechanism class.
* **B (H1 fails at power 1.00).** Pharmacology, co-targeting and ESM knowledge carry no identity
  value (+0.0005, p 0.15).
* **The rule.** It is worse than the unconditional residual in A′ (−0.0045 [−0.0071, −0.0019])
  and equal to an accuracy-trained gate (+0.0001). The identity gate predicts the realised
  contrast no better than the accuracy gate on any route.

**Frozen verdict: IDENTITY_WITHOUT_METHOD, so there is no methodological originality.** The
functional-genetic claim is MECHANISM_CLASS_ONLY.

**Task C** (exploratory, hashed addendum) was target triage at 10 assays per compound on 1,148
compounds. It is NOT_SUPPORTED.

* Signature-to-knockdown connectivity is near random: 0.017 hits@10 against 0.012.
* Orbit calibration adds nothing.
* Training-annotation degree reaches 0.43, and chemical-neighbour target transfer 0.98.

**Integrity work, kept separate from the science:**

* The freeze validator now authenticates the `sha256` and `files` schemas, which it had silently
  skipped, and refuses others.
* An asset-free CI workflow (Python 3.11–3.13) was added but not pushed.
* An [evaluator audit](evaluator_audit_20261013/README.md) of the frozen knowledge-reality
  confirmation evaluator found test-batch normalisation, outcome-derived eligibility and
  unfrozen identity metadata. It proposes corrections C1–C7.

**Deviation D4.** The frozen S2 entry crashed in its controls step before writing anything. A
one-call wrapper reran it, deterministically.

**Recommendation.**

* NO-GO for OCEA as a method, and for any agent or LLM layer on it.
* Keep the orbit decomposition as an evaluation device.
* Brief 5's M3 − M1 question is INSUFFICIENT EVIDENCE: it needs the 218.3 MB DepMap Achilles
  file, not authorised. Confirmation on sealed PRISM 24Q2 is NO-GO until a protocol adopts
  C1–C7.

**Status.** Nothing promoted. Cost: 0 wells, 0 provider calls, no downloads. Default suite: 858
passed. The study's verification passes a 73-claim audit.

## Previous research update: knowledge reality, 2026-10-13

The English [knowledge-reality report](knowledge_reality_20261013/README.md) asks whether
provenance-qualified, relation-typed, biological-context-conditioned knowledge adds
drug-specific information for strict cold-start compounds (T0: no response of the compound in
any input). The outcome is the selective killing profile in PRISM 19Q4 viability, not
expression.

On 1,460 active compounds in MoA-family folds, chemistry plus knowledge raised the
per-compound selective-profile r from 0.0786 to 0.0842 (+0.0056 [+0.0028, +0.0085],
p < 0.0001). The gain beats all 40 degree-preserving and set-permuted null graphs, so the
true drug-target pairings carry information.

The registered gate still FAILED (G2). Relabelling the genes within degree, expression-variance
and mutation strata keeps which drugs share a target but destroys the targets' biology, and it
reproduces the gain exactly (null mean +0.0057, empirical p 0.95). The signal is
mechanism-class membership, already captured by plain Hub-annotation neighbours (0.0836) and
block Q's RKT route (0.0839). The new elements add nothing: relation typing, provenance
weighting, the target-context route (r 0.009 alone) and cell-engagement (T1) edges. There is
also no gain for compounds whose targets are new (26 compounds, p 0.39). After a primary
screen on a quarter of the lines (r 0.20), knowledge adds +0.0004 (p 0.063).

The confirmatory protocol on sealed PRISM 24Q2 REP.1M (1,229 compounds new by core, name and
connectivity; time-matched Hub 2020 snapshot) is frozen but not run. The gate failed, and the
tier would give about 52% power: 762 active compounds needed, about 396 expected.

Recommendation: NO-GO for confirmation, for promoting the knowledge routes and for any LLM
layer, under the brief's stop rule. Promoted: `maestro.information_tier` only, a contract that
refuses T1 or outcome-proximal inputs under a T0 claim. The study's verification passes a
123-claim audit. Cost: 0 wells, 0 provider calls and 2.4 MB of metadata; the 24Q2 outcome file
has not been downloaded. Default suite: 848 passed.

## Earlier research update: selective hit triage and decision review, 2026-10-13

The English [selective hit triage report](selective_hit_triage_20261013/README.md) is the
first drug-discovery decision study. PRISM 19Q4 primary screen hits were triaged for
selective (compound, line) sensitivities, at 16 confirmation curves and 4 follow-up
dose-responses per 16-compound campaign, and scored against sealed CTRP v2 dose-response
outcomes on 128 test compounds split by mechanism family. The protocol and choices were
frozen before opening; the claim level is retrospective independent-platform
confirmation. MAESTRO's context-aware triage beat the strongest deterministic rule (P1:
22 vs 12 validated selective hits, +10 [+4, +18], p 0.004), but its closed loop did not beat
a conventional two-stage workflow (P2: 23 vs 18, p 0.18), and a gradient-boosted
classifier on screen and context features found 38 hits without buying any follow-up
(post hoc +15 over MAESTRO_LOOP, p 0.004). The success criterion (beat strong non-agentic
workflows at equal or lower cost) is NOT met. Development had misled the design: one
56-compound kinase-inhibitor family held 82% of its validated signal. A Scientific Decision
Review inspired by Co-Scientist added no hits, but its evidence rule mattered: admitting
virtual-cell predictions as measured evidence produced 15 false NO-GOs against 3 (R2
CONFIRMED); measured-evidence vetoes were directionally right but not significant (R1).
The frozen outcome reader divided test viabilities by 100 (a unit guess); the registered
endpoint was restored after opening and disclosed. Promoted contracts only:
`maestro.decision_review`, `maestro.claim_audit` (claims checked against a manifest of
succeeded, negative, failed and excluded runs) and `maestro.hit_triage`. The LLM arms are
frozen but NOT_RUN pending authorisation (about 0.47 USD). Cost: 0 wells, 0 provider calls.
Default suite: 843 passed; the study's verification passes its 82-claim audit.

## Earlier research update: collaboration limits, 2026-10-13

The English [collaboration-limits report](collaboration_limits_20261013/README.md)
examines why the Scientific Agent and the Virtual Cell have not yet produced measurable
synergy. It was frozen before three never-opened GCP target lines (A549, NPC, Astrocyte)
were downloaded, and run once. The largest defect sat in the decision layer between the
two cores: the frozen decoder ranked follow-ups by the largest standardised prediction,
while a hit needs a raw 0.5 log2 mean with every replicate agreeing. Ranking by calibrated
P(hit) on the same forecast raised per-line hits from 55/141 to 77/141 (+15.6 points
[+9.2, +22.7], p 5e-5), and calibrated P(hit) at least 0.5 hit 81% of the time against
38% below it. Most of the gain is the raw scale (+20); the uncertainty model adds
calibrated abstention. `maestro.endpoint_decision` is promoted with seven contract tests
and decision-for-decision parity with the frozen code.

The other questions resolve into measured limits. The earlier 14-versus-12 agent gap
reversed on the fresh lines (no-agent 7/20, integrated 9/20), so it was decoder instability
and sampling noise. Agent-selected pharmacological donors carried less response
information than anchor-phenotype similarity on every tier (fresh differences negative,
intervals include zero). On the exposed L1000 tier, the same compound measured in
another line carries specific cosine 0.81, against 0.48 for rare close structural
analogues and 0.13 for shared targets: without an anchor, transfer hits an
identifiability ceiling. Production memory has no outcome-to-reference pathway. In
simulation, single-line sparse measurements cannot feed cross-line transfer (map utility
exactly 0). One campaign is worth at most +0.003 to +0.005 cosine, and self-training
improves zero-shot agreement while lowering decision utility. No agent role or memory
loop is promoted. Cost: 0 wells and 0 provider calls. The default suite passes 822
tests, and both study verifications reproduce every recorded result.

## Earlier research update: evidence-conditioned GCP transfer, 2026-10-13

The English [evidence-conditioned histone transfer report](evidence_transfer_20261013/README.md)
tests a new measured proteomic source with connectivity-separated 66/27/20
reference/development/test compounds. Source-aware normalization uses LVL3 and
same-plate DMSO controls, avoiding held-out-treatment dependence in LVL4 medians.
The development-selected deterministic blend finds 14/20 directional hits; the
integrated evidence agent and matched conventional agent each find 12/20, and the
agent-only donor method finds 10/20. Integrated-minus-deterministic is -10 percentage
points (paired bootstrap 95% CI [-30, +10]); integrated-minus-conventional is zero
(CI [-15, +15]). The predeclared synergy gate fails. The new scientific selector
remains in research, and the existing RNA RKT certificate is not extended to GCP.

The production profiling runner now supports opt-in CaseStore persistence with
condition/model/source/axis binding, exact accepted-receipt recovery and refusal
to repeat unresolved actions. These are engineering improvements only. All 815
default tests pass in the requested maestro environment; both earlier frozen study verifications pass. Python file count
remains 189 after consolidating related transfer-metric tests. The 120-call source
qualification experiment preserves raw usage, source receipts, frozen choices,
negative results and deterministic replay checks.

## Earlier research update: context discrimination, 2026-10-13

The English [context-discrimination report](context_discrimination_20261013/README.md)
audits Block Q and tests a new decision endpoint on development-exposed GSE70138 data.
With two recorded profiles per compound, RKT follow-up finds 158/702 transcriptional
activity discordances versus 133 for a reference-derived fixed pair; strict-margin
counts are only 38 versus 35. In a matched 84-compound DeepSeek pilot, the integrated
agent finds 10 discordances, versus 16 fixed, 15 deterministic RKT, 14 agent without
RKT and 12 conventional LLM with RKT. Operational interaction is -11.90 percentage
points; agent benefit and dual-core synergy are not demonstrated. No new scientific
component is promoted and no fresh confirmation is claimed. Source hashes, protocols,
negative results, cached reasoning and replay verification are retained in that study.

Research folders are now explicitly registered in `STUDIES.json`; the historical
two-document-only shape assertion has been replaced by registration checks. The
default suite passes 808 tests. The earlier consolidation inventory below describes
its historical revision, not the current research-folder count.

## 1. Final architecture

Agent owns plans, actions, bounded memory, CaseStore, execution, budget and restart. Maestro owns the evidence/decision contract between the two cores. Virtual Cell owns model/source/condition/axis identity, prediction, uncertainty, applicability and refusal. Tools own explicit reusable offline checks and evaluation. Research owns historical scientific evidence and future explicitly frozen protocols. Tests own software behavior and architecture boundaries.

## 2. Retained production capabilities

NumPy is now declared as the existing required runtime dependency; isolated installed import exposed the previous missing declaration. Heavy research/plotting packages remain optional.

Typed evidence and measurement authorization; source/condition binding; prediction caching and refusal; scoped memory; durable reservation, actual-spend accounting, idempotency and restart; handoff/repair; receipts; paired terminal evaluation. These are ENGINEERING_ONLY until independently qualified biological and decision endpoints support a narrower claim.

## 3. Promoted research capabilities

Consolidation promoted no new scientific policy or fitted model. Block Q (2026-10-12, routed knowledge transfer) then promoted three modules, with no fitted weights shipped. `virtual_cell.knowledge_transfer` is the RKT virtual cell. It keeps four typed routes: context ridge maps, phenotypic, structural and knowledge analogues. Each route carries its own certificate of expected specific cosine; the routes are pooled; refusals are named (`NO_TRANSFER_ROUTE`, `SPECIFIC_DIRECTION_UNSUPPORTED`); `VALIDATED_SCOPE` is L1000 landmark responses at 10 uM / 24 h. `maestro.transfer_value` holds the confirmed fixed coverage design (`sparse_transfer_design`, the default) and the secondary certificate value-of-information planner. `agent.profiling.run_profiling` is the measure-only campaign runner, reporting wells and turnarounds. `tools.evaluation.transfer_metrics` holds specific cosine, AURC and compound-clustered tests. Parity with the frozen study code is float32 rounding for predictions and identical cell selections for the design (12 of 12 campaign-budget pairs). The 2026-10-13 collaboration-limits study promoted `maestro.endpoint_decision`. It ranks a follow-up by its calibrated probability of meeting a raw-threshold, replicate-agreement hit, and refuses by name below a caller's threshold (`HIT_PROBABILITY_BELOW_THRESHOLD`). Its `VALIDATED_SCOPE` is GCP histone peptides at 24 h with an A375 anchor. The 2026-10-13 selective-hit-triage study promoted three engineering contracts with no fitted model or scientific rule: `maestro.decision_review` (competing falsifiable explanations, measured-only evidence admission, GO/NO_GO/NEED_MORE_EVIDENCE with named reasons and digests, exploration rankings that refuse probability use, human approval for experiments), `maestro.claim_audit` (report claims against a manifest of succeeded, negative, failed and excluded runs) and `maestro.hit_triage` (compound identity, assay-context binding, curve QC admission, budget ledger, outcome seal, split-leak refusal). Existing scoped transcriptional transfer remains in virtual_cell; campaign budgets, decision receipts, interval-based measure-or-predict, platform identity, paired increments, exact cluster sign-flip and coordinate/variance diagnostics remain tested production capabilities. Their engineering admission does not certify cross-platform transport or new biological validity. Duplicate completed research implementations have been retired.

## 4. Research conclusions

SUPPORTED: Block P virtual-cell contribution +17 unexpected hits, interval [+11,+23], p=.00098, 38 campaigns/975 sealed compounds/1,216 screens per arm, annotation-relative novelty. Block N unseen-class transcriptional transfer +.116 against targets, +.100 against chemistry, secondary replication +.103, increment over 160-line partial screen +.049. Both remain assay/source/endpoint limited. Block Q, run once on a sealed tier of 702 GSE70138 compounds (7 lines, 1,105 active cells), confirmed the virtual-cell claim. With one profiled line, the pooled RKT prediction has centred cosine .529: against generic .287 the difference is +.218 [+.202,+.235]; against the best single route (context) it is +.033 [+.015,+.052], p=.0003. The certificate ranks errors better than applicability distance (AURC .347 vs .428). It is near-calibrated: expected .547, realised .529. For never-profiled compounds the gain is small (+.050 vs generic, +.025 vs a monolithic PRESAGE-style ridge) and 45% refuse. At one well per compound, the transfer-informed sparse design beat PRESAGE's exhaustive design by +.181 (11/11, p=.0005). The certificate planner beat activity-greedy by +.034 (10/11). Provider spend was $0.32. All other historical results, controls and limitations are in [EVIDENCE.md](EVIDENCE.md).

## 5. Failed, unsupported and blocked claims

NOT_SUPPORTED: independent Agent/LLM yield beyond conventional tool loops; STATE relative-survival improvement; active-tier mechanism coverage; adaptive/feedback superiority and fixed8 selection gain. Block Q decision claim NOT_CONFIRMED. The certificate planner lost to the fixed sparse design at one well per compound (-.044, 0/11), and did not beat a ReAct agent given the same virtual cell at the family-wise level (+.024, p=.029). A bounded LLM override did not help (-.014). The planner wins only at two wells per compound (+.053, 10/11, secondary). Pooling did not beat the context route when all lines were visible. EXPLORATORY: processed repeat audit, retrospective diagnostics and Block O feasibility reversal. ENGINEERING_ONLY: software tests and coordinate reconstruction. Selective hit triage (2026-10-13): MAESTRO's closed loop over a conventional two-stage workflow NOT_CONFIRMED (P2, +5, p 0.18); the agentic success criterion against strong non-agentic workflows NOT met (a context-aware learner with no follow-up found 38 hits against MAESTRO_LOOP's 23, post hoc); measured-evidence vetoes NOT_CONFIRMED (R1, p 0.045); decision-aware acquisition and re-ranking added no hits; LLM agent and debate arms NOT_RUN.

BLOCKED: full2000 and STATE checkpoint output axes; independent original primary repeat/QC/culture units and complete decision menu; new P0.6 protocol and distinct measured channel; authentic costs; external STATE/Tahoe, MAP and LINCS assets. Historical readout also lacks tahoe_c39_x_hvg_feature_names.json and had preexisting protocol-pin mismatches. Removing an old executable packet does not repair these gaps. Minimum release requires authenticated assets plus a fresh frozen protocol; no automatic download or paid execution is authorized here.

## 6. Removed and merged content

README, REPORT and EVIDENCE own usage, current conclusions and 32 compact historical evidence rows. Original unique tracked protocols, amendments and observations remain identified by their historical Git commit, without a replacement archive. No science was rerun. The read-only inventory tool shrank from 336 to 134 lines; hardcoded refactor history, speculative classifications and the full-worktree scanner were removed. Case-memory audit takes an explicit protocol freeze and defers optional scientific/plotting dependencies. Research preflight streams hashes, retains input/verifier pin refusal and never runs a scientific verifier implicitly.

The prior deletion-policy failure was resolved by individual file removal: each Remove-Item receives one file, without force or recursive deletion, and its result is checked. All 13,787 audited tracked candidates were deleted. One additional source module, agent/model_audit.py, had no import, CLI, manifest or test consumer and was deleted after reverse-reference inspection. Budget behavior and synthetic ALMANAC vault/hash checks remain; obsolete comparisons against retired research implementations were removed. Streaming SHA256/MD5 and content-change tests now target surviving reusable hash functions and enter the default suite.

| Category | Count | Meaning |
|---|---:|---|
| Retained | 177 | Remaining tracked source, configuration, test and document files |
| Newly promoted | 0 | No newly admitted scientific algorithm or policy |
| Merged | 3 | README, REPORT and EVIDENCE are the revised authoritative documents |
| Deleted | 13,788 | Tracked files removed from the 13,965-file baseline |
| Blocked scientific prerequisite areas | 6 | Section 5; no file-deletion blockage remains |

Research now contains only REPORT and EVIDENCE. Six ignored derived study outputs, 539 study bytecode files and regenerable root build/installation metadata were also removed individually. Empty study/build/log directories were removed after checking emptiness. An orphaned Bash shell from October 10 held one empty study directory; it had no scientific computation child, and closing it released the lock.

Counts concern the tracked code checkout. Ignored local data/reference assets, outputs and temporary source ledgers were not treated as newly deletable observations; they are not shipped by Git and do not load on production import/help. Local user configuration and ignored credentials were not copied into the isolated checkout or printed. The tracked release structure is distinct from this populated scientific workspace. External audit/install material was removed file by file, followed by its empty directories; no audit inventory, test XML, backup or archive remains from this task. Obsolete research-specific Git attributes were removed; current text and binary rules remain.

## 7. Validation results

Baseline: 785 default tests passed. Final default suite: 791 passed in 56.26 s, including final repository shape and scientific boundaries. Shape/integration subset: 63 passed. Explicit synthetic ALMANAC vault suite: 1 passed. Compileall, Agent/research/audit help, core/tools imports and git diff --check pass. Hash and sealed-vault tests preserve actual behavior rather than requiring a retired study directory. Reference checks find no broken tracked Markdown links, stale registered test paths, forbidden production imports or empty code directories.

The final fresh tracked-file checkout passed all 791 default tests in 58.46 s. Fresh offline installation and isolated installed imports/Agent help pass with the existing local NumPy distribution supplied; the installed package also verifies absence of the retired module. NumPy is declared as a runtime dependency. This is an offline local-dependency check, not fresh dependency resolution or biological validation. Research --verify remains BLOCKED/ASSET_MISSING without an explicit current frozen protocol; input/verifier hash tampering remains refused.

## 8. Efficiency results

Measured process times on this Windows checkout: core/tools import .7816 s, Agent help .8427 s, research help .2369 s, case-memory audit help .2562 s; all exit 0. No comparable speedup is claimed. Inventory scans are explicit. Plotting loads only for figures, with protocol input explicit rather than hidden in research.

Tracked working-tree content decreased from 490,668,246 bytes to approximately 2.58 MB. These are code-checkout measurements, excluding ignored scientific assets. The remaining tree has 155 Python files; source deletion does not imply a new algorithmic or biological performance gain.

## 9. Remaining risks and minimum next gate

REFACTOR_COMPLETE for the tracked release checkout: individual cleanup, final structure, package boundaries, default tests, explicit research refusal, fresh installation/import/help, references and temporary cleanup passed. No commit or push was performed. Scientific qualification remains BLOCKED where listed in section 5.

Qualify original primary repeated endpoints and the entire legal decision menu, then freeze independent units, controls, exclusions, source/model axes, acquisition costs and useful net benefit before any P0.6 or Agent-benefit experiment. Historical summaries are evidence records rather than immediately reproducible research packages. The three explicitly registered research suites comprise one synthetic ALMANAC construction/vault test and two evaluation suites requiring external source fixtures. Historical parity against retired research code is removed. Missing assets are never represented as scientific success.

Block Q addition: `tests/test_knowledge_transfer.py` covers the three promoted modules and passes (11 tests, plus 6 in `tests/test_transfer_metrics.py`). The default suite passes except `test_repository_has_one_scientific_report_and_no_retired_release_tree`. That test fails while the untracked study folder `research/knowledge_transfer_20261012/` remains; the folder is kept until it is committed and can be cited by commit.
