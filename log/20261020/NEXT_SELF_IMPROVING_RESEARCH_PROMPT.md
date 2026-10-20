You are implementing a bounded research prototype for MAESTRO in D:/MAESTRO.

The flagship objective is a self-improving virtual-cell scientific agent for drug discovery, with open-ended evolution as a research ambition. Deliver a working prototype, a bounded experiment, and an evidence-based decision. Do not stop at a literature review or a new architecture document.

The proposed contribution is:

When the current virtual-cell representation cannot distinguish intervention responses that matter for drug selection, can an agent learn a reusable experimental procedure that resolves that distinction, refine the functional representation accordingly, and inherit or compose that procedure to improve later drug-discovery campaigns?

This is a hypothesis to test, not an instruction to obtain a positive result. It is permissible to conclude that ordinary active learning, matrix completion, meta-learning, or program search explains the entire benefit.

1. Establish the scope and preserve the completed work.

Use D:/MAESTRO/.venv/Scripts/python.exe. Read the applicable instructions, the current Git status, log/20261020/PREPARATION.md, data/INVENTORY.md, and the relevant entries of data/ASSETS.json. Do not print the entire asset manifest, which contains large nested records. Preserve the existing uncommitted preparation work and concurrent presentation files.

Read research/functional_rule_revision_20261020/REPORT.md, PROTOCOL.md, FREEZE.json, RESULTS.json, CHALLENGE_TRACE.json, PARTITION.json, PROVENANCE.json, and the relevant implementation. Treat that study as closed. Do not rerun its stages, regenerate its frozen artifacts, reopen its G/F outcome files, reset its vault, or overwrite log/20261020/NEXT_RESEARCH_PROMPT.md. That older prompt is a consumed provenance input.

The prior run found no observed advantage for its selected edit over same-data refitting: the raw held-out utility difference was approximately -0.000543, and every retained procedure fell back to the refit. Its edit was a cell-invariant module-pair component from a finite 16-edit dictionary, with only three final pairs in scope. It did not test inherited experimental skills, a changing acquisition policy, or multi-generation capability growth. Its failure neither establishes nor refutes the new flagship hypothesis.

Add a concise prior-study clarification to the new report after checking these issues against the code:

- The pair resampling routine applies unique() to bootstrap draws, reducing the candidate pool before recomputing top-k. Its percentiles are not an established confidence interval for the original fixed-size nomination problem. Preserve the descriptive negative result and original recorded decision, but do not repeat the claim that a useful population-level gain has been reliably excluded.
- The full-dictionary comparator uses ridge penalties; sparse feature storage does not make it sparse structure learning.
- Some saved coefficient summaries are insufficient to reconstruct an executable model. New artifacts must serialize all parameters and transformations.
- Observed headroom and a heuristic precision calculation do not identify the unique cause of failure.

Do not spend this task repairing the closed study or rerunning its final evaluation. Keep the clarification additive, and do not silently rewrite historical evidence.

2. State the algorithmic contribution and challenge its novelty.

The application for this prototype is adapting to a cell background that is new to the prototype's training history, using a limited number of parallel drug/combination measurements to prioritize combinations for subsequent confirmation. Select this generalization axis explicitly. Do not simultaneously claim new drugs, unseen drug pairs across all backgrounds, patient efficacy, acquired resistance, or treatment sequencing.

Define functional state as an experimentally grounded summary of responses that is useful for a specified intervention set, dose regime, and endpoint. Drug-response measurements can support this limited state definition. They do not establish molecular state identity, cell dynamics, causal mechanism identity, or a state that can be therapeutically manipulated.

Compare the proposed method with the closest verified primary sources, including:

- DreamCoder: https://arxiv.org/abs/2006.08381
- POET: https://arxiv.org/abs/1901.01753
- Darwin Godel Machine: https://arxiv.org/abs/2505.22954
- AlphaEvolve: https://arxiv.org/abs/2506.13131
- Open-Endedness is Essential for Artificial Superhuman Intelligence: https://arxiv.org/abs/2406.04268
- BATCHIE: https://www.nature.com/articles/s41467-024-55287-7
- BioDiscoveryAgent: https://arxiv.org/abs/2405.17631
- Co-Scientist: https://arxiv.org/abs/2502.18864
- Active Feature-Value Acquisition: https://doi.org/10.1287/mnsc.1080.0952
- Virtual-cell state/perturbation models relevant to the actual implementation, including VCLMU if applicable: https://arxiv.org/abs/2610.04475

Check relevant active feature acquisition, active matrix completion, meta-learning, counterexample-guided abstraction refinement, and program-learning methods. Distinguish checked method details from abstract-only evidence. Do not treat this seed list as an exhaustive novelty search. Keep the review focused enough to proceed to implementation.

Explain exactly what is different from a functional fingerprint plus an adaptive predictor. The proposed distinguishing mechanism is a measured, transferable witness for refining an abstraction: jointly learn when another measurement is needed, what it should measure, how it changes the state representation, and which downstream responses may still share a prediction rule.

A new coordinate is not new information. A new measurement supplies information. A program can improve how that information is acquired, represented, searched, and reused. Every one of those contributions requires its own comparison.

If this mechanism is already subsumed by a close method, implement the appropriate close comparator and present the work as a domain adaptation or benchmark contribution unless an experimentally distinguishable difference remains. Do not invent a new acronym to substitute for that difference.

3. Implement the smallest executable evolution loop.

Use a small typed program language rather than unrestricted agent-written repository modifications. A reusable program should include:

- Q: a legal measurement plan, potentially conditional on measurements already available;
- phi: an executable transformation from observed responses to a functional state coordinate;
- f: a conditional numerical response model that predicts both prospective probes and downstream interventions, with uncertainty or an explicit uncertainty limitation;
- Omega: observable applicability conditions, unknown conditions, measured support, counterexamples, and version dependencies.

Q, phi, and f must execute without reading an evaluation target. Include complete coefficients, normalization, feature schemas, identity mappings, and source/version information in serialization. A saved program must reload and reproduce its predictions.

The loop is: identify a decision-relevant failure on legitimately acquired observations; propose competing programs; obtain their predictions before querying; choose a legal measurement whose possible outcomes could change a downstream decision; acquire a real recorded result; update support and state; nominate interventions; and evaluate whether the resulting procedure transfers to later tasks.

Allow composition, refinement, replacement, and removal of programs within declared syntax and resource limits. Do not restrict the experiment to selecting an ID from the old 16-edit dictionary. The initial grammar still defines a computable search space; composition beyond the initial library is not proof of an unbounded new function class.

The agent must be able to report that neither competing program explains an observation, or that direct candidate confirmation is more valuable than another diagnostic experiment. It must not reinterpret every possible result as support for its proposal.

Maintain a small versioned library. Separate provisional exploration candidates from programs with demonstrated transfer. A bounded exploration archive may retain stepping stones for later composition, but archive size, text novelty, and program complexity are not success metrics. Acceptance and retirement rules must be stated before the measured comparison.

A program's inheritance should change what a later task can measure, infer, or propose. Saving a model checkpoint or appending a narrative to memory is insufficient. Test composition and inheritance explicitly; if the implementation only improves state features while its experimental procedure remains fixed, label the result accordingly.

Use at most a few focused modules in a new study package. Reuse existing numerical readers and clients where their contracts fit. Do not build a new orchestration framework or train a large foundation model.

4. Construct a development environment with a defensible information boundary.

O'Neil is exposed internal-development data. It can support a bounded retrospective intervention-response environment. It cannot become independent confirmation through a new random split.

For this task, use only old S outcomes and the actual C panel already disclosed in the completed study. Recover the exact purchased C pair IDs from the stored trace/ledger; do not equate the entire C partition with the acquired panel. Never open old G/F outcomes or unrelated sealed ALMANAC/PRISM outcomes.

Prefer the existing metadata cache and role-specific outcome artifacts under tmp/functional_rule_revision_20261020. Create a separate export without mutating the old vault. If the C file also holds unpurchased values, use an allowlisted export that accesses only the acquired indices, for example by memory mapping, and ensure no other C values enter learner-visible arrays. If a safe export cannot be produced, use S alone and disclose the limitation. Do not reparse the entire raw response workbook as a shortcut around the boundary.

Define campaigns by cell background, with background membership fixed from metadata before scoring. Train prototype models from the authorized development subset; do not import fitted models that have already consumed a campaign's hidden combination outcomes. Public identities do not make this an independent holdout.

All methods receive the same realistically available initial information, including the monotherapy information assumed available by this application. Do not hide known monotherapy curves to manufacture probe value. Record their common information/cost status explicitly.

Use separate contracts for two experiments:

- Transfer of a functional abstraction: a probe set and an unqueried target set are disjoint by canonical unordered drug pair within the new background, including all associated doses and repeats. Test whether the probe-derived state improves decisions on those unqueried targets.
- End-to-end discovery: all strategies share the same legal action menu and nomination pool. Allow direct confirmation of promising candidates as a legitimate competitor; do not exclude its queried candidates from utility just to favor diagnostic probes. Any stricter unqueried-target score is a separate endpoint, not a hidden disadvantage imposed on this baseline.

When independent repeat measurements are unavailable, call the latter comparator direct-measurement replay and its score realized published-outcome utility. Reusing a noisy recorded result both to choose and to score a candidate can reward selection noise. Disclose this limitation; it is not independent confirmation. Any prespecified noise sensitivity analysis remains secondary.

Never impute unavailable outcomes and call them experimental feedback. Only genuinely recorded actions are queryable. Preserve source conditions and observed-versus-interpolated distinctions. Do not treat interpolated monotherapy references as additional measurements.

Use a full pair-by-cell dose grid as a clearly defined logical query unit when that is the available artifact. Count repeated reads of the same observation once as information acquisition; count additional computation separately. Do not translate these units into wells, independent cultures, physical experimental savings, or money without the required metadata.

If a program uses matched functional contrasts, verify the dose, time, scale, and source-reference contract. Correlation between contrasts sharing a monotherapy anchor is not evidence of transferable combination structure. Supply the same anchors to every baseline and use a control that retains shared-anchor effects while breaking the claimed combination-specific relationship.

Do not let missing physical acquisition costs block a logically budgeted retrospective comparison. Do let missing outcomes or invalid probe-to-target matching block unsupported biological interpretations.

5. Freeze a finite protocol and use meaningful controls.

Before comparative real-data scoring, write one protocol specifying the application, endpoint, campaign roles/order, query budgets, program grammar, search limits, baseline tuning, acceptance criteria, seeds, checkpoints, and decision rules.

The primary practical endpoint should remain absolute functional shortlist utility at a fixed query budget, with a prespecified shortlist size and common nomination pool. A utility-versus-budget curve may measure efficiency. Prediction error, reference residuals, synergy, scope coverage, and program count are secondary diagnostics. Do not move the main objective to whichever metric improves after seeing results.

Choose the useful-gain criterion from the intended screening decision and authorized source-side development information. Report both its value and remaining headroom. Do not reuse 0.005 automatically, repeatedly lower a threshold, or restrict candidates to an advantageous subgroup after observing scores. If the intended task has no useful remaining decision opportunity, report that and stop effectiveness claims for this task.

Separate the following attribution questions:

A. Same-history improvement. Give the evolved model/library and controls exactly the same cumulative observations and allowed feedback. Compare fixed-structure refitting, a competitive nonlinear or multitask response model, a functional fingerprint/latent-factor model, and program/structure search without inherited programs. Include an adequate interaction model; a weak factorization machine with no context-specific combination term is not sufficient by itself.

B. Acquisition improvement. With a fixed response-model family, compare the proposed diagnostic strategy against coverage/random sampling, a competitive active-learning or active-matrix-completion strategy, and direct confirmation of promising candidates. Histories may differ; initial information, legal actions, and query budgets must match.

C. Full-loop attribution. Implement the four conditions of representation/library evolution on or off crossed with experimental-procedure adaptation on or off. Include at least one strong conventional joint acquisition-and-response baseline. Name approximations honestly; do not call a home-built heuristic a reproduction of BATCHIE.

D. Inheritance. Preserve raw history while deleting newly learned programs; transfer a learned program into a baseline solver; compare a frozen library, parameter-only updating, and search without program inheritance. Include a strong capacity control able to express the eventual programs. Do not leak future-discovered programs into earlier checkpoints; a hindsight superset is only a labeled diagnostic.

Control cumulative training, search, inference, evaluator feedback, and API resources, not merely the last few calls. Allow conventional learners comparable caching and continual updating. Report initial program-discovery cost separately from reuse cost and include both in cumulative totals.

Freeze the external campaign definition and evaluator. The agent may generate internal questions or challenges from acquired evidence, but it may not rewrite success criteria or certify itself using predictions from its own virtual cell.

Development validation used to select programs is adaptively consumed information. Record it and include it in information/cost accounting. A final development scoreboard should not feed back into program generation. If later campaign labels are released for training, that release must be explicit and available to the relevant same-history controls.

Evaluate checkpoints on common anchor tasks and later tasks; do not interpret scores on an increasingly difficult task stream as directly comparable. Repeated splits, seeds, contrasts, and technical repeats do not create new independent biological units.

If reporting uncertainty for a nonlinear shortlist metric, first define the population/finite-pool estimand and dependency unit. Do not reuse the old unique-bootstrap interval or treat duplicated nominations as distinct candidates. Use a justified method, or report paired task-level descriptive effects and sensitivity without a confidence claim. Do not inherit the old heuristic MDE as a calibrated power calculation.

6. Execute a bounded prototype rather than an unlimited search.

First run synthetic environments containing:

- no transferable extra structure, including a shared-anchor confounding case;
- structure that ordinary active learning or a conventional interaction model can learn;
- compositional transferable structure that can benefit from a reusable diagnostic procedure, with nuisance variation and noise.

These are software/method controls, not biological evidence. Test several fixed instances rather than designing one world that guarantees the proposed algorithm wins. A positive control should demonstrate that the system can discover, serialize, reuse, and retire procedures; it need not force superiority over a sufficiently capable baseline.

Then run one bounded real-data development pilot if the authorized observation contract is valid. If real-data task capacity is inadequate, still finish and test the synthetic prototype, and identify precisely which additional measured units are required for the real test.

Default resource ceiling for this first prototype: at most three evolution generations after the initial version, twelve evaluated new program candidates per generation, three fixed run seeds, and 120 minutes of comparative experiment compute after implementation. Downscale these limits from task capacity or a timing-only synthetic benchmark before the measured pilot. Record the resulting schedule. Do not increase it in response to disappointing scores.

At the compute limit, save all completed checkpoints. Compare only prespecified tasks and budgets completed by all required arms; do not compare averages over different task sets because some methods are slower. Label missing comparisons incomplete rather than claiming superiority or extending the budget.

Use enough later distinct development backgrounds to distinguish invention from reuse; seek at least two later backgrounds per promoted program when feasible, while explicitly assessing whether the effective task count supports any uncertainty claim. If this is infeasible, report a single-transfer or engineering result rather than continual capability acquisition.

One documented repair cycle is allowed for software or protocol defects discovered by controls. Preserve failed runs. Do not repeatedly redesign synthetic worlds, endpoints, or real-data partitions until a desired biological result appears.

API testing is authorized. Use the existing configured client and keep credentials out of artifacts. Only enable the API proposer after the deterministic prototype and evaluator are working. Limit this pilot to six total HTTP attempts, including repairs/retries, and 30,000 cumulative input-plus-output tokens. Use lower limits if appropriate; do not change billing/model settings.

Give the API a genuine proposal task: emit a typed, executable candidate experimental/state program from the allowed visible evidence. Do not just ask it to select an already scored dictionary entry. Validate its output before execution; reject access to undeclared observations, evaluator state, files, or tools. Log exactly what evidence it received. Any external biological knowledge used by this arm must also be accounted for in comparator inputs.

Record model, attempts, tokens, latency, accepted/rejected candidates, and actual utility. Report money only with verified pricing. API validity establishes integration, not scientific gain. If the API is unavailable, complete the deterministic experiment and label the API arm NOT_RUN.

7. Decide what the results actually justify.

Keep these decisions separate:

- executable prototype and information-boundary tests;
- same-history representation/library gain;
- equal-query-budget acquisition gain;
- transfer and retention of newly learned experimental procedures;
- bounded multi-generation capability growth;
- independent biological or prospective confirmation.

If only acquisition improves, claim acquisition efficiency. If only search cost improves, claim computational reuse. If a conventional model explains all gains, withdraw the special representation/evolution claim. If programs only help the tasks that created them, do not call them transferable skills.

Do not call library growth or an improved final model evidence of open-ended evolution. The finite pilot can support bounded continual acquisition of useful capabilities, including composition and retention. It cannot prove indefinite open-endedness or establish new biological mechanisms.

Stop additional candidate search when the frozen pilot budget is exhausted or when the controls expose a failure that remains after the documented repair cycle. Do not use the ambition of open-endedness as a reason to extend an unsuccessful experiment indefinitely.

A future larger study requires observable program reuse, competitive same-information/equal-budget performance, acceptable old-task retention, and sufficient practical headroom. Development success only licenses the design of independent validation.

For that later stage, identify at most one external measured source or a concrete prospective experiment design, chosen for the needed observation structure before examining comparative scores. BATCHIE's public screen is a candidate to qualify, not a guaranteed complete replay matrix. An empty local source directory, imputed screen, or another release of already exposed data is not independent validation. Never treat unmeasured actions in an adaptively sampled screen as known outcomes.

8. Deliver concrete, reviewable artifacts.

Create one compact study package, preferably research/self_improving_virtual_cell_20261020/, adapting the date only if the actual execution date differs. Include:

- one consolidated REPORT.md covering the novelty boundary, prior-study clarification, exact method, a fully worked measured or explicitly synthetic example, results, failed hypotheses, and the decision;
- a protocol and machine-readable configuration/manifest;
- runnable source, complete serialized programs/models, version ancestry, and observation/resource receipts;
- focused tests for information isolation, dose/reference validity where relevant, serialization equality, budget accounting, no duplicate nominations, inheritance ablations, and the synthetic controls;
- a verifier that inspects saved evidence without refitting models, making API calls, or reopening hidden outcomes.

A worked example must show competing predictions before the probe, at least two possible feedback outcomes, how each changes the functional representation and recommendation, and what remains unknown. Do not invent named biological mechanisms to explain an observed statistical split.

Update research/STUDIES.json and the central report/evidence pointers minimally and accurately. Preserve historical closures and the consumed prompt. Do not create a proliferation of discussion reports.

Run the appropriate focused tests and required checks. Report existing unrelated repository-shape failures honestly; do not delete active presentation outputs, weaken assertions, or claim all tests pass without running them. Record before/after hashes for the prior frozen package and its consumed inputs.

Do not commit, push, publish, send messages to authors, or initiate wet-lab work. End with the actual changed paths, commands run, resource use, decision table, and the smallest next action warranted by the evidence. A negative or inconclusive but properly executed prototype is an acceptable completed task.
