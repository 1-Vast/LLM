# MAESTRO execution prompt: evidence-driven revision of functional transfer rules

Updated after the two-pass workspace preparation review on 2026-10-20.
This is the executable revision of the user's supplied research brief. The core research question,
allowed structural edits, and decisive comparators are preserved. Changes concern verified input
availability, reproducible execution, measurement semantics, and the user's new API authorization.
The experiment itself has NOT been run by the preparation/readiness review.

You are implementing the next bounded research study for MAESTRO.

Workspace: D:\MAESTRO

Execute the study described below. Produce runnable code, actual results, and a research decision. Do not stop after writing another proposal or data-audit report.

PRIMARY QUESTION

Given identical cumulative observations, can one bounded revision of conditional functional transfer rules improve the selection of entirely held-out drug pairs, compared with fixed-structure refitting and standard structure learning?

Application: preclinical combination prioritization within a known compound library.

This is an internal development experiment on previously exposed O’Neil data. A newly hidden evaluation partition does not make the dataset independently unexposed.

The scientific object is a conditional functional prediction rule. Do not interpret it as an identified molecular mechanism, a validated cellular trajectory, or an established pharmacological equivalence class.

Keep the connection to the reviewed proposals explicit:
- EvoPharm-WM supplies the hypothesis that feedback should change WHERE experience transfers.
- The critical EvoPharm review supplies the restricted edit language, same-information comparisons,
  and requirement to improve decisions for unmeasured combinations.
- The DBP review distinguishes information about the measured candidate from transfer to other
  candidates. Its Potter experiment remains a separate task and is not started here.

The minimum auto-research loop is:
scoped functional model -> frozen challenge observations -> diagnosis of failed sharing -> one
executable rule revision -> one retention decision -> nominations of unseen drug pairs.
The Virtual Cell component supplies scoped response predictions and shared functional components;
the Agent manages the challenge, admissible revision, retention, and nominations. This is a
functional model of drug response in cell contexts, not a validated whole-cell simulator.
Do not replace this experiment with an ordinary prediction benchmark or a prose-only agent demo.

1. Scope and operating boundaries

Read applicable AGENTS.md instructions, inspect the current Git state, and read the relevant historical conclusions before editing.

Start with log/20261020/PREPARATION.md (the latest readiness section supersedes historical caveats),
data/INVENTORY.md, data/ONEIL_SOURCES.json, data/ONEIL_STRUCTURE.json, research/REPORT.md,
research/EVIDENCE.md, and research/STUDIES.json. Do not restart general cleanup or dataset hunting.
The reviewed checkout is on codex/workspace-preparation at f4e37615, with substantial UNCOMMITTED
preparation changes and new files. Preserve them; do not reset, switch them away, stage them
indiscriminately, or assume that HEAD alone captures the input state. Record a targeted working-
tree manifest of the files this study consumes, excluding secrets and unrelated artifacts.

Use D:/MAESTRO/.venv/Scripts/python.exe, Python 3.11.16. Its installed versions match
requirements-preparation.lock and pip check passes. Core tests passed in this environment after
the second cleanup. The old .build-1024-reposition test blocker has been archived and is resolved.
Do not recreate the healthy environment, switch to global Python 3.14, or install Torch/CUDA for
this CPU pilot. Use modest grids and at most four numerical worker threads on this 16 GB machine.

Preflight commands from D:/MAESTRO in PowerShell:

    & 'D:/MAESTRO/.venv/Scripts/python.exe' -B -m pip check
    & 'D:/MAESTRO/.venv/Scripts/python.exe' -B -m tools.datasets.oneil_sources --verify-only

The review already ran the full default suite: 940 tests passed. Run it after implementation,
along with the new scientifically relevant tests. Keep test fixtures in a new uniquely named
external temporary directory; never reuse a pytest basetemp containing user or recovery files.
The generic research preflight has no active released study and may report ASSET_MISSING;
that historical global status is not a reason to stop a qualified, separately registered pilot.

Use a new, isolated research directory, such as:
research/functional_rule_revision_20261020/

Preserve unrelated changes and historical study artifacts. Keep changes local and reviewable.

Do not reopen stopped AURKA, Beat AML low-rank, Jaaks substitution, or unrestricted program-revision branches.

Do not open the ALMANAC vault, use sealed historical evaluation assets, contact authors, or purchase experiments.
The user now explicitly permits API testing. The bounded API experiment in section 8A supersedes
older blanket prohibitions on paid model calls; it does not authorize an open-ended LLM campaign.

Do not implement a large knowledge graph, latent cellular dynamics, an evolutionary population,
a mechanism archive, unrestricted LLM proposal generation, or a self-modifying research policy.

The first study permits:
- One challenge acquisition batch.
- One candidate structural revision per arm.
- One acceptance decision per arm.
- One final development-test evaluation.

Use deterministic research policies initially.

DBP/Potter 2021 is a separate early-readout prediction problem. Do not combine it with O’Neil, require DBP success before this study, or switch to DBP after seeing unfavorable O’Neil results.

2. Starting evidence and reusable components

Inspect these existing components before deciding what to reuse:

- tools/datasets/combination_screens.py
- src/virtual_cell/combination_world.py
- tools/evaluation/discovery_replay.py
- tools/evaluation/costs.py
- research/observable_state_20261018/masked_interface.py
- research/REPORT.md
- research/program_revision_20261017/REPORT.md
- research/eg_rpt_20261019/PROTOCOL.md

Known limitations to verify and accommodate:

a. build_oneil() aggregates dose observations and batches into pair-by-cell labels.
b. Its single-agent lookup can fall back to another batch and interpolate concentrations.
c. CombinationWorld builds history from other cell lines. This is incompatible with globally held-out drug pairs unless explicit observation masks are introduced.
d. The existing discovery replay budgets candidate counts and summarizes costs afterward. Do not assume it enforces the new experiment’s acquisition costs.
e. Existing “certified” names do not establish independent biological confirmation.

Reuse parsing, identity handling, numerical components, and access-control ideas where appropriate. Do not refactor the existing production path just to support this study.

Relevant methodological references:

- O’Neil original study:
  https://doi.org/10.1158/1535-7163.MCT-15-0843
- comboFM:
  https://www.nature.com/articles/s41467-020-19950-z
- BATCHIE:
  https://www.nature.com/articles/s41467-024-55287-7

Do not launch an open-ended literature review. These references establish that combination interactions and adaptive screening already have strong precedents.

3. Resolve the data route once, then proceed

The original response workbooks have now been downloaded and fully authenticated. Use the
RAW ROUTE unless an actual, newly discovered structural incompatibility prevents the task.
Do not repeat the old empty-directory diagnosis or redownload healthy originals.

Canonical directory: D:/MAESTRO/data/raw/oneil2026_qualification/

Combination response:
15357163mct150843-sup-156849_1_supp_1_w2lrww.xls
Official article/file: 22503133 / 39962566
https://api.figshare.com/v2/articles/22503133
https://ndownloader.figshare.com/files/39962566
38,829,879 bytes; published MD5 d1b914b83d7ef475795731bec1d1e36e.

Single-agent response:
15357163mct150843-sup-156849_1_supp_0_w2lh45.xlsx
Official article/file: 22503127 / 39962560
https://api.figshare.com/v2/articles/22503127
https://ndownloader.figshare.com/files/39962560
1,678,111 bytes; published MD5 26c8ccbe68837d9c3bba967bb421e9fd.

Data legends:
15357163mct150843-sup-156849_1_supp_1_g2lr29.xlsx
Official article/file: 22503130 / 39962563
https://api.figshare.com/v2/articles/22503130
https://ndownloader.figshare.com/files/39962563
10,430 bytes; published MD5 6992447cee5b60ee9f15efa209cc3bfe.

Published sizes, MD5, local SHA-256 receipts, and OOXML ZIP integrity all passed. The combination
file is OOXML despite its .xls extension. Reuse tools.datasets.combination_screens.iter_xlsx_rows;
if using openpyxl, pass a binary handle for the mislabeled file. Preserve original row locators.

Metadata-only review established:
- 16,752 single-agent rows and 368,832 combination rows; 38 drugs and 39 named cell lines.
- Primary batches 1 and 2 jointly cover all 583 unordered pairs x 39 cells = 22,737 groups.
- Every primary pair-cell group occurs in exactly one primary batch and has a complete 4x4
  concentration grid: 16 distinct dose combinations, 363,792 primary response rows in total.
- Batch 3 contains 5,040 rows for 21 selected pairs and 15 cells. Exclude it from the primary
  analysis; it is a selected repeat, not independent confirmation. Preserve global pair roles
  for it too. Do not make it an automatic second test after seeing F.
- Every combination row has both single-agent curves in the same batch and cell, with the
  combination doses inside those curves' concentration ranges.
- Only 23,595 of 363,792 primary rows match BOTH single-agent doses within relative tolerance
  1e-7 and absolute tolerance 1e-12. Most dose-matched reference values require interpolation.
- The assay duration is 96 hours and concentrations are micromolar. Six single-agent and four
  combination viability columns are technical repeats, not identified independent cultures.
- Plate, well, control, culture-stock, and acquisition-bundle identifiers are not supplied.

These checks inspected identity/dose structure, not response effects or favorable subsets.
They qualify an internal functional prediction/selection experiment, not physical-cost or
independent biological claims. Outcome validity and missingness still need the frozen handling
rules below; structural completeness alone does not certify every response value.

Do not download the entire DrugComb archive.

Before examining response values to choose a task, inspect identities, experimental design, provenance, missingness indicators, and available grouping fields.

Select one of these predefined routes based on resource structure, not model performance:

RAW ROUTE:
Recover original dose-level observations and preserve their provenance. Conduct the model experiment below. Permit the optional policy comparison only if legitimate acquisition bundles and cost accounting can be established.

AGGREGATE ROUTE:
If original files cannot be recovered or cannot support the required observation structure, use the existing O’Neil cache for the same narrow model question.

The aggregate route is a fixed-data comparison of structure-learning methods on archived aggregate functional labels. It does not establish reproducible experimental counterexamples, matched dose-level contrasts, physical acquisition costs, or Agent policy gain.

A positive aggregate result cannot promote the project to biological discovery or experimental-efficiency claims.

Do not change datasets because results are negative. If neither route supports a valid prediction task, document the precise incompatibility and stop dependent work.

Keep qualification documentation short. Once a route qualifies, continue to implementation and evaluation without requesting routine confirmation.

4. Define the task and freeze the information boundary

Primary generalization claim:
New unordered drug pairs composed of drugs already represented in the source data, evaluated in known cell backgrounds.

Do not simultaneously claim unseen-cell, unseen-compound, or patient generalization.

Create disjoint partitions by canonical unordered drug-pair identity:
- S: source fitting and internal tuning.
- C: challenge observations eligible for acquisition.
- G: development acceptance and retention evaluation.
- F: final internal development test.

All cells, doses, orientations, batches, and repeats belonging to one drug pair must remain in the same partition.

Choose partition proportions from identity and coverage information. A reasonable starting allocation is 60/15/10/15 percent for S/C/G/F. Adjust only for documented structural coverage requirements before response-based evaluation.

Ensure constituent drugs in C, G, and F have adequate representation in S.

Within S, use grouped internal validation for tuning. Freeze:
- Eligibility and exclusions.
- Endpoint transformations.
- Feature construction.
- Candidate rule dictionary.
- Challenge budget.
- Hyperparameter search limits.
- Revision acceptance criteria.
- Primary metric and uncertainty analysis.
- Conditions governing the optional policy stage.

Target-response-derived similarities, feature selection, normalization parameters, and uncertainty calibration must use only legally visible fitting data.

Any single-agent information available initially must be identical across methods. Record its provenance and its common initial-information cost.

The complete, pre-existing monotherapy panel may be common initial information for these known
drugs/cells. This does not permit reading held-out COMBINATION outcomes. Fit any learned feature
scales and thresholds within legal training folds. Preserve and record batch-specific provenance.

Freeze search spaces, budgets, and grouped validation procedures before C is disclosed. If the
revision selects an edit using S+C, permit the fixed sparse and standard-learning comparators
comparable model-selection opportunities on S+C within their frozen spaces. Do not handicap
baselines by leaving their regularization tuned only for the smaller initial dataset. G and F
remain unavailable to all such fitting/selection.

F labels are accessible only to the final evaluator. They cannot influence features, edits, acquisition, model selection, continuation decisions, or thresholds.

G is a consumed development validation resource, not independent confirmation. Each arm gets one acceptance query after its candidate is fixed. Do not repeatedly revise after seeing G.

5. Preserve measurement semantics

For the raw route, retain available:
- Drug and cell identifiers.
- Drug orientation and both concentrations.
- Units, exposure duration, endpoint and normalization.
- Batch, plate, and replicate identifiers where actually supplied.
- Original row locators.
- Single-agent and control provenance.
- Whether each value is measured or derived.

Do not fabricate missing replicate identities or equate technical repeats with independent cultures.

Use matched controls for claims requiring matched functional contrasts. Do not silently borrow controls from another batch.

Interpolation may be an explicitly labeled derived reference. It is not an additional observed treatment or purchasable feedback point.

Do not reuse the old processed hit label as the new scientific endpoint without checking its definition.

Prefer a prespecified decision utility that considers actual combination activity and a named combination reference. Keep absolute activity separate from HSA, Bliss, or other interaction scores.

Concrete default for this pilot: rank pair-cell regimens by A = 1 - mean(X/X0), averaging all
16 published primary-grid points with equal weight. Nominate k=5 pairs per eligible cell from
the same held-out pool; use macro-cell mean activity of that shortlist as the primary utility.
This describes prioritization under the published drug-specific dose grids, not optimized doses,
clinical exposure, selective killing, or synergy. Do not clip values or reinterpret X/X0 as a
literal survival probability. The raw viability columns and derived X/X0 must remain distinct.

Report a secondary named reference-adjusted measure on the same frozen shortlists. For example,
use same-batch log-concentration interpolation to construct a multiplicative X/X0 reference and
subtract observed X/X0 before fixed grid aggregation. Label it as an interpolated functional
reference residual; do not silently equate it with validated Bliss synergy. Never extrapolate,
borrow another batch, or count an interpolated value as a new observation. If the reference is
scientifically unsuitable, document that before C and retain activity plus a justified reference.
Do not replace the primary endpoint after inspecting C/G/F effects. A different utility requires
an explicit pre-C rationale and frozen definition; it must still test the same transfer-rule idea.

Use an explicit development decision margin. A default is 0.02 units of the normalized activity
utility; label this a research screening threshold, not a clinically validated effect size.
Justify or adjust it using source-side precision and utility reasoning before C. Predeclare
missing-value handling, tie handling, coverage/abstention, the retention harm tolerance, and
how uncertainty and multiple comparisons affect each decision. Do not silently drop missing F
outcomes or replace unavailable shortlisted outcomes with convenient alternatives.

Freeze dose-grid aggregation or any response-region definition before evaluating F. Do not select each candidate’s best-looking dose after seeing final outcomes.

If only the aggregate cache is usable, retain the documented aggregate endpoint and explicitly limit the task to prioritization on that endpoint. Do not reconstruct unsupported biological claims from it.

6. Implement the smallest meaningful revision model

Start with a competitive, simple combination-response model.

Represent a candidate rule by:
- Its drug, context, dose, and endpoint scope.
- A numerical functional prediction component.
- A condition observable before the decision.
- The observations that could challenge its transferability.
- The future candidate predictions affected by the rule.

Permit only:
A. One split of a shared component using a predefined observable condition; OR
B. One additional restricted interaction shared across multiple drug pairs.

The rule must predict more than the measured exception that motivated it. Do not add a separate free parameter or exclusion clause for every failed drug pair.

Do not infer combination compatibility from single-agent similarity alone.
Do not propagate a counterexample for one partner to every other partner.
Do not treat an unknown condition as satisfied.
Do not impose transitivity on approximate functional similarity.

Freeze a small candidate dictionary using metadata and S only. Use an explicit finite search budget; defaults of at most 16 candidate edits and 12 tuned configurations per model are sufficient unless a smaller design is appropriate.

A possible implementation is:
prediction = base_prediction + beta * context_gate * shared_pair_feature

This is an implementation suggestion, not a requirement to use that exact formula.

State explicitly that the proposed advantage concerns finite-data learning, search efficiency, or reduced negative transfer within a controlled function family. It does not arise from claiming that ordinary models cannot represent the same functions.

Save executable before/after rule records: numerical expression or component, observable gate,
shared parameters, scope, supporting S/C observation IDs, unknown-condition behavior, and the
unmeasured candidate IDs whose predictions it changes. The edit must alter sharing across more
than one drug pair; a fresh coefficient for the challenged pair alone is not eligible.
Record predictions before challenge disclosure so a claimed counterexample is a failure of a
previously made prediction. Source-side grouped residual calibration may assess the discrepancy;
technical repeats cannot establish independent biological reproducibility.

Demonstrate the distinction between a legal structural edit and ordinary parameter refitting in
code. A textual explanation, new memory record, renamed model, or retrained coefficients alone
cannot count as the proposed innovation. A single study-local runner and typed rule representation
are sufficient; do not build a new general agent platform.

7. Run the decisive same-observation comparison

Choose one fixed challenge panel using S and design metadata. Give every model exactly the same acquired C observations.

Mandatory comparators:

1. Frozen initial model, as a descriptive reference only.
2. Fixed-structure model completely refitted on the same accumulated S+C data.
3. Fixed sparse supermodel containing ALL allowed gates and interactions, with the same accumulated data and comparable tuning/search budget.
4. Competitive conventional structure learning on the same inputs: tune a small nonlinear
   model and an interaction-capable model/factorization or functional-interaction model within
   the frozen budget. Select a conventional champion using legal S/C grouped validation only.
   Do not call a home-built approximation a faithful comboFM or BATCHIE reproduction.
5. The bounded revision procedure.

At least one comparator must capture combination interactions. Beating only a linear or non-updating baseline is insufficient.

Use the same preprocessing, available functional information, candidate pool, and evaluation utility across methods.

Select the candidate revision using S and acquired C only.

Accept it on the single G evaluation only if the frozen criteria show:
- Sufficient improvement relative to same-data fixed-structure refitting.
- Acceptable degradation in the predefined prior applicability range.
- Compliance with complexity and search limits.

If it is rejected, the revision procedure returns the fixed-structure refit. Record that outcome without constructing another exception.

The fixed sparse supermodel and standard comparator must receive comparable model-selection opportunities. Do not give only the proposed method access to additional validation information.

The same one-shot G retention/fallback opportunity must be available to eligible conventional
updaters, using frozen candidates and the same refit fallback. Record raw candidate and deployed
procedure results separately. Never pick the best edit, model family, or API answer by searching G.
A G rejection means fallback to the fixed-structure refit; it does not authorize another edit.
Provided integrity is intact, complete the already frozen F evaluation and record that rejection
as part of the procedure's result. Do not stop at a G report or condition the presence of F results
on whether G looked favorable.

Evaluate the finalized methods once on F.

The primary result should concern candidate selection, such as fixed-shortlist decision regret on F. Report predictive error and negative transfer as supporting diagnostics.

Report group-level effects and uncertainty that respect repeated drug pairs, shared drugs, and cell backgrounds. Do not treat every dose or technical repeat as an independent research task.

Predeclare primary contrasts against same-data refitting, the full-dictionary model, and the
conventional champion. For a promising internal-development verdict, require the registered
useful-gain condition and uncertainty criterion against these decisive controls, with multiplicity
handled explicitly. Beating only the frozen initial model is information-update benefit.

Resample whole pair groups with all their cells when estimating selection-utility uncertainty,
and account for the selection/ranking functional rather than bootstrapping only favorable selected
rows. Add a predeclared sensitivity to shared constituent drugs and variation across cells.
These intervals do not establish independent biological replication. Assess achievable precision
using S only; if the design is too weak for a strong verdict, label it an estimation pilot before
C and retain an inconclusive outcome when warranted. Do not manufacture power from 363,792 rows.

Freeze all methods, nominations, continuation choices, and code/configuration hashes before the
single F evaluation. Run all registered primary and secondary analyses within that evaluation;
subsequent integrity verification must use stored outputs rather than reopen F for new analyses.

8. Optional policy comparison: decide before opening F

CURRENT STATUS: NOT_RUN for this execution. The recovered files lack plate/control/acquisition
identifiers needed for an authenticated physical-budget comparison. This does not block the
same-observation model experiment. Do not spend the run trying to reverse-engineer missing costs.

The following defines a possible later study, not an additional task to implement now. That stage
is permitted only on the raw route when acquisition bundles and costs are recoverable, and only
under a continuation rule fixed using source-side evidence.

Its activation must not depend on final F results.

If permitted, freeze the entire comparison before opening F:
- Fixed versus revisable model.
- Standard decision-directed selection versus counterexample-directed selection.
- Fixed coverage and direct-confirmation baselines.

All policies receive the same legal action menu, information access, total budget, and final utility.

Counterexample selection must use predicted disagreement or expected decision improvement. It must not inspect unpurchased outcomes to identify the largest residual.

Keep the first study to one acquisition batch and one revision.

Use C for diagnostic acquisition. Final F recommendations must be fixed before their labels are revealed.

The direct-confirmation baseline spends no budget on diagnostic C measurements and allocates its available budget to final candidate confirmation. It must be allowed to win.

If implementing an approximation to BAX or BATCHIE, name it accurately. Do not claim a faithful reproduction without implementing the relevant algorithm.

For physical-cost accounting:
- Purchase actual experiment bundles, not free aggregate labels.
- Reconstruct whether an action includes a complete dose matrix and which repeats.
- Count matched controls and independent preparations.
- Deduplicate only genuinely shared, already purchased observations.
- Keep well counts, sample use, calendar time, and money separate.
- Charge final candidate confirmation.
- Report common initial-data costs and incremental costs separately.

Do not multiply every cached dose count by four and call it a verified physical budget.

Use final archived measurements as retrospective evaluation evidence. Without recoverable independent confirmation records, do not call them prospective or independent biological validation.

If this stage is unsupported, omit it and explicitly leave Agent strategy gain untested. Complete the model experiment.

8A. Bounded API integration and optional secondary proposer

The user explicitly authorizes API tests. Reuse agent.llm.MAESTROSettings and DeepSeekChatClient
where practical. Configuration exists in process variables/.env; read it internally without
printing keys, dumping environment files, or persisting authorization headers. Do not change
providers or global configuration. The readiness review already made one successful synthetic
JSON connectivity call to deepseek-flash (57 input + 11 output tokens, no scientific data).
Connectivity success is not evidence for any research hypothesis.

Keep the deterministic bounded-revision method as the primary experimental arm. Before C is
opened, register whether to include ONE LLM-assisted secondary arm. With the current working
provider, include it if a concise, well-defined edit-selection contract is implementable within
the following limits; otherwise record why it was omitted and finish the primary experiment.
Its activation must not depend on the deterministic result, G, or F.

The API sees only the same legal S/C evidence, frozen numerical feature definitions, and the
same finite edit dictionary used by the deterministic selector. Use opaque drug/pair/cell IDs;
do not send dataset names, old reports, G/F labels, hidden-label summaries, or whole workbooks.
Opaque IDs reduce obvious lookup opportunities but do not prove absence of pretrained knowledge.
Cap payloads and disclose any summarization; the deterministic selector must be able to use the
same summary. If the API receives additional scientific features, supply them to all relevant
comparators or explicitly exclude the comparison from a same-information claim.

Require one structured answer selecting an allowed edit ID or NO_EDIT, with cited legal
observation IDs. Never execute generated Python or treat generated explanations as measurements.
Compile and validate the selected edit locally, refit on the same S+C data, and apply the same
single G retention rule. Seal its F predictions before the common F opening. Invalid or failed
responses yield an explicit API-arm failure/fallback, not extra candidate search.

Bounds for this execution: at most four additional HTTP attempts INCLUDING retries, at most
two logical requests (an optional synthetic contract check and one scientific proposal), and
at most 2,048 requested output tokens per request. Keep each request within a conservative
6,000-input-token allowance, using provider token counting if available. Account for the
client's built-in retries rather than assuming one Python call means one HTTP attempt.
If provider prices are verified, additionally enforce a US$5 ceiling; otherwise report money
as unverified and enforce the request/token bounds. Transport failures may consume budget
without reported usage. Do not run a model sweep, repeated debate, prompt search, or semantic
repair loop. Temperature zero does not make an external model deterministic.

Record model, prompt hash, safe request/response artifacts, latency, token usage, attempts,
failures, and response validity. API failure must not block offline primary results.
Compare the API arm with the deterministic revision as a predeclared SECONDARY result.
One bounded proposer run tests integration and suggests a contribution; it cannot establish
robust LLM superiority, acquisition-policy gain, recursive self-improvement, or autonomous discovery.

9. Verification and reporting

Write targeted tests for scientifically consequential software behavior:
- Global drug-pair partition integrity.
- A/B identity and dose swapping.
- Unpurchased and final-label access restrictions.
- Invariance of pre-evaluation fitting, edit proposals, and nominations to hidden F labels.
- Invariance of pre-G models/proposals to hidden G labels; G may affect only the frozen retention decision.
- Validate these with synthetic poison/sentinel fixtures, not by opening real held-out outcomes early.
- One-edit scope, common S+C histories, full-dictionary coverage, and G fallback behavior.
- If the API arm is enabled: allowed-edit validation, failure/fallback, forbidden-label payload rejection,
  and request/attempt limits.
- Measured versus derived values.
- Missing or mismatched controls.
- Purchase and shared-control deduplication, if policy replay is implemented.

Synthetic fixtures are acceptable for software tests only. They do not provide biological evidence.

Run the new study and relevant affected checks. Do not rerun unrelated historical studies.

Produce a compact research package:
- PROTOCOL.md.
- Provenance, eligibility, partition, and frozen configuration manifests.
- The minimal adapter, models, and runnable entry point.
- Machine-readable results, per-pair predictions and nominations, a concise comparison table,
  executable before/after rules, and a single evidence-to-revision-to-decision trace.
- API receipt and secondary result when enabled; clearly separate connectivity, contract compliance,
  and held-out utility.
- REPORT.md with the research decision and reproduction command.

Register the completed study using repository conventions. Do not promote the method into the core product path during this experiment.

Use one package such as research/functional_rule_revision_20261020/, one concise daily record
under log/YYYYMMDD/, and pointers in research/REPORT.md, EVIDENCE.md, and STUDIES.json. Do not
recreate the scattered report structure that was just consolidated. Keep registered frozen
artifacts byte-identical. A read-only verifier should check manifests, saved results, and verdict
consistency without silently fitting models or rereading final labels.

Take action through implementation, tests, the frozen experiment, and the final research decision.
Routine implementation choices do not need renewed approval. If a scientifically invalid endpoint,
leakage, missing indispensable input, or an unfixable numerical failure prevents completion,
record the exact blocker and completed work. A negative effect, API outage, absent physical-cost
metadata, or stopped historical branch is not by itself a reason to leave the model study undone.
No new dataset, larger architecture, or second attempt is authorized to chase a positive result.

The report must separately answer:
A. Did new observations improve decisions?
B. Did bounded revision beat same-data fixed refitting?
C. Did it beat the fixed full-dictionary and standard structure-learning comparators?
D. Was there transferable benefit on F?
E. Was a policy comparison actually supported and executed?
F. Did the executable rule actually change cross-pair sharing, and where did predictions change?
G. Did the optional API proposer add anything beyond the deterministic selector under its declared budget?
H. What remains untested?

Use conclusions appropriate to the evidence:
- Unsupported.
- Inconclusive at this sample size.
- Promising internal development result.
- Standard structure learning sufficient.
- Experimental-cost claim not testable from available records.

Do not equate a non-significant difference with equivalence.
Do not treat passed software tests as scientific validation.
Do not change the endpoint, partition, or candidate dictionary after seeing F.

A negative result is a completed study. Do not respond by adding model layers, more Agent roles, or another dataset.

The desired outcome is a concrete decision about whether bounded, evidence-driven revision deserves further investment beyond ordinary feedback learning and standard structure selection.
