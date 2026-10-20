You are executing the next bounded innovation-validation study for MAESTRO.

Workspace: D:/MAESTRO
Interpreter: D:/MAESTRO/.venv/Scripts/python.exe

Your task is to determine whether the proposed innovation works. Complete implementation, run the permitted experiments, and deliver a defensible SUPPORT / NO_SUPPORT / INCONCLUSIVE decision for each claim. Do not stop after a proposal, literature review, or another audit package. A well-supported negative result is a successful completion of this task; obtaining a positive result is not a requirement.

The flagship goal remains a self-improving virtual-cell scientific agent for drug discovery, with open-ended evolution as a longer-term research objective.

The precise innovation hypothesis to test is:

When an existing cellular response representation aliases intervention responses that require different drug-selection decisions, an agent can discover a diagnostic measurement procedure, use measured feedback to refine that representation, and inherit or compose the procedure to improve later campaigns beyond competitive learning and search methods given the same information and resources.

The current application is combination prioritization in a new cell background using a limited number of parallel measurements. A functional state is a summary of experimentally observed responses for a defined intervention set, dose regime, and endpoint. Do not interpret it as molecular mechanism identity, longitudinal cell dynamics, acquired resistance, patient efficacy, or treatment sequencing.

1. Preserve previous evidence and establish what is actually being tested.

Read the applicable workspace instructions and inspect Git status. Preserve existing uncommitted work and concurrent presentation outputs.

Read:

- log/20261020/NEXT_SELF_IMPROVING_RESEARCH_PROMPT.md
- research/self_improving_virtual_cell_20261020/REPORT.md and PROTOCOL.md
- that package's FREEZE.json, SUMMARY.json, stored results, serialization receipts, and relevant implementation
- research/functional_rule_revision_20261020/REPORT.md
- the relevant preparation and dataset inventory entries, without dumping the entire large asset manifest.

Both previous studies are closed. Preserve their source files, frozen records, original results, prompts, and vault state. Do not repair them in place, rerun their stages, or silently replace their decisions. Create the new study under research/innovation_validation_20261020/, adapting the date only if the actual execution date differs.

The current prototype's main real-data contrast was approximately -0.0009. Synthetic compositional improvement over its fixed refit was approximately +0.009, but conventional acquisition methods performed better and inheritance was not established. These findings motivate a targeted mechanism test, not immediate expansion to a wet-lab screen.

Acknowledge that the earlier implementation did not fully instantiate the proposed mechanism: its witness rule selected by scopes and historical variance without comparing competing predictive explanations, and its acquisition predictions were not refreshed within the probe loop. Its result concerns that implementation, not every possible self-improving virtual-cell system.

2. Repair only the defects needed for a valid new experiment.

Implement the corrected behavior in the new package, reusing suitable components without modifying pinned predecessors. First reproduce the following issues with small synthetic or stored-record checks, then add focused regression tests for the corrected behavior:

- Program identity: canonicalization sorts phi while conditions refer to coordinate positions. Two different executable programs can share a key. Preserve semantic ordering or use correctly remapped stable identifiers; do not deduplicate or cache behaviorally different programs together.
- Headroom: stage_headroom averaged method utility across seeds but used the last seed's oracle. Compute paired oracle-minus-method quantities on exactly the same cells, pools, and seeds. Do not retroactively change the old criterion or classify the old trial with a new threshold.
- Verification: missing mandatory evidence must fail. The previous verifier returned success even when its evidence directory was empty. Require the declared artifacts, arms, tasks, budgets, and result dimensions for each completed stage. An incomplete package must be marked incomplete.
- Inheritance comparison: inherited and restarted searches must receive the same released observations, candidate evaluation opportunities, validation/retirement procedure, and cumulative resource envelope. The old no-inheritance arm skipped validation used by its competitor.
- Promotion: zero gain or ties do not demonstrate usefulness. Distinguish valid software, provisional exploration, noninferiority, and demonstrated transferable utility. A bounded archive may retain unproven stepping stones without counting them as acquired capabilities.
- Checkpoints: evaluation must use the actual deployed program after validation and rollback. The old last-generation curve could still use a rejected incumbent.
- Serialization: save the actual fitted models and programs at prediction time, for the actual contract, seed, legal mask, and history used. The old serialization stage refitted contract E although the primary result used T. Save all decisive arms and enough feature/identity metadata to reproduce their stored predictions without refitting.

Also verify that latent-coordinate use across different fitted bases does not silently change program meaning. If a coordinate is unknown because its required measurement is absent, retain that missingness instead of treating zero as established evidence.

Keep the repair report brief. These corrections restore test validity; they are not the innovation and do not imply that the scientific result will improve.

3. Implement the missing mechanism as a minimal executable algorithm.

Maintain a small set of competing numerical response programs. Each program must specify its legal measurement requirements, state transformation, downstream response predictions, observable applicability conditions, and evidence dependencies.

Before selecting a diagnostic probe, record:

- the competing programs and the visible evidence supporting them;
- their different predictions for the same legal probe;
- which downstream nominations could change under plausible probe outcomes;
- the acquisition score or explicitly documented approximation used to choose that probe.

After the measurement, update the support assigned to the competing programs and their predictions before choosing the next probe. Permit an outcome to contradict every available program; record an unresolved mismatch rather than always accepting an explanation.

Use a tractable approximation to expected downstream decision value or decision-relevant hypothesis discrimination. A variance-only rule may be a baseline, but must not be renamed a discriminating experiment. If a probe cannot distinguish the competing programs or cannot affect the target decision, the system should prefer an alternative action or stop.

An inherited skill must be an executable reusable measurement/state procedure, not just a new coefficient or a saved model checkpoint. Later tasks must be able to invoke it, adapt its inputs within a declared scope, or compose it with another validated procedure. Record actual calls and dependencies. A mutation of one incumbent is not automatically evidence of a reusable program library.

Use a small typed language and a bounded search. Add only the operations needed to test the hypothesis. A fixed grammar can still support compositional learning; do not claim that generating a new syntax tree creates an unrestricted new function class.

Keep one fixed external evaluator. Programs cannot change the endpoint, candidate pool, eligibility rules, or evaluator. Simulator predictions may guide search but may not count as experimental truth.

Provide a worked example with two competing explanations, the same prospective probe, and two possible feedback outcomes that lead to different posterior support and downstream decisions. The example must execute. An explicitly synthetic example is acceptable. Two different real cells observed after the run are not a substitute for this branching example.

4. Freeze one study with separate, decisive attribution questions.

Use the following questions:

H1 — Diagnostic acquisition:
Does decision-relevant discrimination improve downstream drug selection over competitive conventional acquisition at the same measurement budget?

H2 — Inherited capability:
Does reuse of learned executable procedures improve later tasks over a strong learner/searcher with the same cumulative observations and resources?

H3 — Joint mechanism:
Is there an additional benefit from coupling diagnostic acquisition with representation/program refinement?

H4 — Drug-discovery utility:
Do these benefits appear on measured pharmacological outcomes in the intended application?

H5 — Sustained capability growth:
Across the finite task stream, are new useful capabilities retained and composed while old capabilities remain usable?

Report each separately. Do not collapse them into a single success flag. H5 can support bounded capability accumulation; this experiment cannot establish indefinite open-ended evolution.

Use two complementary experiment contracts:

- Fixed-observation comparison: all methods receive exactly the same cumulative history and probe observations. This isolates representation, program reuse, and search efficiency.
- Adaptive-acquisition comparison: methods may acquire different observations, but share initial information, legal actions, measurement budgets, target pools, and total resource accounting.

For diagnostic transfer, keep the probe and target drug pairs disjoint within a background, including their doses and replicates. For end-to-end discovery, allow direct measurement of promising candidates and allow these candidates to remain in the nomination pool. Do not impose a restriction on that baseline merely to favor diagnostic probes.

The primary drug-selection endpoint is absolute functional shortlist utility at a fixed measurement budget and common pool. Preserve the declared assay scale. Fix the shortlist size, primary budget, and useful-gain margin before comparative scoring, with an explicit decision rationale. An engineering threshold is acceptable if clearly labeled; it is not automatically a clinically meaningful margin.

Do not set the useful-gain margin as a convenient fraction of observed oracle headroom. Headroom is a task diagnostic, not a device for making a result pass. Do not change the primary endpoint to synergy, residual prediction, or a favorable subgroup after observing results.

Budget-versus-utility curves, measurements needed to reach a fixed utility target, model error, search time, and retained capabilities are useful secondary endpoints. Search efficiency alone supports a computational contribution, not automatically a biological or sample-efficiency contribution.

5. Give the innovation strong and fair competitors.

At minimum include:

- a no-additional-probe prior and a fixed-structure refit;
- a competitive functional-fingerprint/latent-factor response model with conventional active acquisition;
- a competitive nonlinear or contextual interaction model with a conventional acquisition policy;
- search over the same program language without inherited learned subprograms;
- the inherited-program method;
- direct measurement of promising candidates in the end-to-end contract.

The inherited and non-inherited searchers must see the same history and have comparable compute, caching, proposal counts, validation feedback, and retirement rules. The restarted baseline may use all prior raw evidence; do not make it forget data.

Include a fixed broad-capacity comparator able to express the relevant structures. It may use a prespecified feature/program family or conventional nonlinear model. Do not supply future-discovered programs to an earlier checkpoint; label any hindsight capacity analysis separately.

Run the representation/library evolution on/off by diagnostic-policy adaptation on/off factorial. Where useful, reuse the same arms across comparisons to avoid building a redundant benchmark.

For any apparent inherited-skill gain, require:

- deletion of the new skill while retaining the same raw history;
- transplantation of the skill into a compatible baseline solver;
- a control that breaks the claimed witness-to-target relationship while preserving common monotherapy anchors or nuisance structure.

Judge the innovation against the strongest relevant conventional comparator. Beating the initial refit while losing to standard active learning is not evidence for a superior method.

Do not describe a home-built acquisition heuristic as a reproduction of BATCHIE. Check the methods of the closest program-learning, active feature acquisition, active matrix completion, and active drug-screening work sufficiently to distinguish the implemented mechanism. Effective performance and methodological novelty require separate conclusions.

6. First run a synthetic mechanism experiment that can genuinely reject the idea.

Construct a small family of task streams containing:

- no transferable residual structure, including shared-anchor confounding;
- ordinary low-rank/contextual structure that conventional learning can solve;
- repeated decision-relevant aliasing that a diagnostic probe can resolve and reuse across later tasks;
- a composition case in which previously learned procedures can support a later task, with nuisance variation and measurement noise.

Freeze the generators, task distribution, development instances, and evaluation instances before comparing methods. Keep the evaluation worlds' latent mechanisms inaccessible to learners. Include varied parameterizations; do not hand-code the correct skill into the proposed method or give it extra causal information.

An evaluator-only oracle may establish that a useful diagnostic opportunity exists. Ordinary baselines should be capable of learning the same relations. The question is whether the proposed learning and inheritance mechanism is more efficient, not whether competitors were denied the needed information.

A positive software control must establish that the system can discover, execute, serialize, reuse, and retire a procedure. It need not guarantee a win over a capable baseline. Winning a tailored example is not sufficient for an innovation claim.

Preselect a feasible sample of independent synthetic task streams using timing-only development runs. Aim for about 24 streams per primary mechanism condition; set the final count before scoring. Aggregate within each stream and compare methods on paired stream-level outcomes. Do not merge unrelated synthetic cells merely because they share the same string identifier.

For an inferential claim, define the estimand and use uncertainty across independent streams. Resample the paired stream-level contrasts, not individual nominated pairs or overlapping contrasts. Do not reuse the earlier unique()-bootstrap. Account for the prespecified primary comparisons or use an explicit hierarchical testing order.

A useful gain is supported when the prespecified uncertainty criterion excludes improvements smaller than the useful-gain margin. If the upper bound is below that margin, report no support for a useful gain. Otherwise report inconclusive. Do not equate a nonsignificant comparison with equivalence.

Report both average performance and failures across task families. A finite null experiment cannot prove universal absence of false positives.

Stop mechanism-effectiveness claims if ordinary methods match or exceed the proposed system, if inheritance contributes nothing under the controlled comparison, or if improvements appear only in the tasks that generated the skill. Do not redesign the synthetic worlds after scoring to make the method win.

7. Test measured-data relevance without recycling an independent holdout.

Asset qualification may proceed while the synthetic implementation is developed. Do not make every engineering task wait for a new dataset.

For internal development, the already authorized O'Neil export is available: old S plus the exact 60 acquired C pairs. Use only the new prototype's previously released H0/D1/D2/D3 backgrounds for any additional development replay. Select them through a restricted export; do not consume its A/T backgrounds again for tuning or a new effectiveness claim. Do not open the older G/F outcome files, unacquired C outcomes, or unrelated sealed ALMANAC/PRISM assets.

The existing O'Neil results are exposed development evidence. A new partition does not restore independence. A small corrected replay can test practical relevance and implementation behavior, but must be labeled as development.

For stronger measured-data evidence, qualify at most one external source, chosen by its observation structure before evaluating comparative performance. Inspect source receipts, historical project exposure, cell identities, actual measured action coverage, endpoint, dose/time conditions, replicates, and control dependencies. Existing empty directories and imputed responses are not data.

BATCHIE's measured screen is one candidate, not a prequalified benchmark. Sparse adaptive sampling may prevent complete policy replay; two doses alone do not invalidate every possible task. Restrict a replay to an explicitly defined, truly observed common action space when justified, and acknowledge the resulting selection bias. Never fill unobserved actions with a model and use them as ground truth.

Use all common monotherapy information that the intended workflow would actually possess. Do not manufacture the need for a probe by hiding otherwise available information.

Use a clearly defined recorded measurement unit for query accounting. Include shared source-data releases, program-discovery measurements, validation feedback, and deployment measurements in the accounting, identifying what is common to all methods. Physical well/culture/cost savings require the corresponding source metadata.

If the same noisy published measurement is used both to select and score a candidate, report realized published-outcome utility rather than independent confirmation. Keep truly independent replicate evaluation separate when it exists.

If the synthetic mechanism test supports a useful incremental effect and the selected external source is qualified, freeze the measured-data protocol before opening its evaluation outcomes and execute the bounded comparison. Match the claim to the actual exposure and task structure.

If no suitable external data exist, finish the prototype and synthetic decision, optionally the allowed internal development replay, and report H4 as NOT_ESTABLISHED. State the exact missing measured unit and a minimal design to obtain it. Do not claim biological validation or automatically propose a large new wet-lab screen.

If the mechanism experiment fails, report that result and any already collected feasibility evidence. Do not search additional datasets for a positive outcome.

8. Keep execution finite and evidence auditable.

Default ceilings:

- up to four evolution generations;
- up to twelve evaluated new candidate programs per generation;
- up to 180 minutes of comparative experiment compute after implementation;
- an optional API arm with at most six HTTP attempts and 30,000 cumulative input-plus-output tokens.

Reduce the experiment matrix from timing-only development profiling if necessary, before scoring. Run a complete, prespecified set of paired comparisons within that schedule. At the time limit, compare only the common completed task/budget set and mark missing primary comparisons incomplete. Do not extend budgets because the result is disappointing.

API testing is authorized through the existing configured client. Use it only for a genuine typed-program proposal task after the deterministic mechanism works. Log the visible evidence, candidate validation, model, attempts, tokens, and outcome. Keep credentials private. Do not change billing/model settings or claim money figures without verified prices. API unavailability must not block the deterministic experiment.

Allow one documented repair cycle for objective implementation defects. Preserve pre-repair outputs, version the correction, and identify what comparisons were invalidated. A repair does not authorize changing the endpoint, task distribution, or success rule. Do not rerun closed biological evaluations to chase a preferred result.

Save the actual models, predictions, queried observation IDs, programme invocations, candidate decisions, library ancestry, complete checkpoints, and resource receipts as the experiment runs. Refuse accidental overwriting or a second evaluation of a completed stage.

The verifier must:

- fail when required evidence is missing or inconsistent;
- authenticate the declared code/configuration and artifact identities;
- check common task/arm coverage, actual query sets, unique nomination IDs, and resource totals;
- reproduce reported summaries from stored outputs;
- confirm checkpoint/rollback consistency and model identity for the actual evaluation contract;
- perform no refitting, API calls, or hidden-outcome decoding.

Test access isolation, semantic program identity, updates after feedback, equal validation rules, missing evidence failures, model reload equality, and skill reuse/ablation behavior. Synthetic fixtures must not load real exported outcomes implicitly.

9. Deliver a decision, not another research agenda.

Create one compact new study package containing the runnable method, focused tests, protocol, complete evidence artifacts, and one consolidated REPORT.md. Update the central study registry and report/evidence pointers minimally. Preserve all historical closures.

The report must answer:

A. Was the proposed diagnostic-refinement mechanism actually implemented?
B. Did it improve decisions over the strongest relevant conventional comparator?
C. Did inheritance add value with identical history and matched resources?
D. Did a learned procedure transfer or compose in later tasks, and did deleting it remove the advantage?
E. Did the effect survive the shared-anchor/nuisance controls and old-task retention checks?
F. Is the evidence synthetic, exposed measured-data development, or independent/prospective measured validation?
G. What part is methodologically new, and what part is established active learning/program search?
H. Which implementation or scientific hypothesis should continue, change, or stop?

Use separate verdicts for software correctness, diagnostic acquisition, inherited capability, joint mechanism, measured drug-discovery utility, and bounded capability growth. An incomplete implementation or invalid comparison is NOT_TESTED, not a negative biological result.

Do not claim that a program library's size, a longer prompt, or a final model outperforming an uninformed initial model demonstrates self-improvement.

If only computation is saved, report computational reuse. If only acquisition improves, report acquisition efficiency. If strong standard methods explain the result, withdraw the special mechanism claim. If measured validation is unavailable, state that boundary without withholding the completed method result.

Run appropriate focused tests and required checks. Report unrelated repository-shape failures without deleting active presentation files or weakening assertions. Do not commit, push, publish, contact authors, or initiate wet-lab experiments.

End with the actual verdict table, decisive numerical contrasts and uncertainty where justified, changed paths, commands and resources used, and one smallest next action warranted by the result.
