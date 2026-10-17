# MAESTRO: current evidence and repository simplification

Programme revision (2026-10-17): MAESTRO studies transfer of research methods
across drugs and cellular contexts in complete early discovery campaigns.
Candidate discovery and context selection/failure analysis are primary tasks;
selectivity and molecular mechanism claims require their respective comparison
and distinguishing measurements. The [research programme](../log/RESEARCH_PROGRAM.md)
asks when a previous procedure applies, what check can reveal failed transfer,
and whether feedback-based revision improves future decisions over strong simple
workflows at the same total cost. Decision-relevant response correction is its
model-level foundation. MT-P0/MT-P1/MT-P2 are new programme stages, not a revival
of PRESAGE P1-P3. No new biological method or cross-task learning result is claimed.

The [2026-10-17 synthetic audit](../log/program_review_20261017/LOOP_AUDIT.json)
reproduces static A -> B -> C choices under opposite feedback on both committed
HEAD and the preserved working copy. Sixteen same-label observations produce
17/18 support share; eighteen reach 0.95. These are heuristic counts, not a
likelihood posterior. The default loop does not automatically update future
predictions/action values. Runtime and existing study files are preserved.

The revision reconstructed the saved indication-triage development totals:
395 vs two-stage 293 simulated matrix events, +2.615/campaign over 39 campaigns,
saved campaign CI [1.667,3.615]. This is a development lead, with same-profile
simulated probes, pooled assay units, separate budgets and non-nested policy
tuning. It does not establish independent discovery, new model-repair value or
Agent benefit. See the [reuse audit](../log/program_review_20261016/REVIEW.json).
The draft indication-triage study, its results and its sealed tier are preserved.

2026-10-17: [Context transfer with verified bridges](context_transfer_20261017/REPORT.md)
is **CONFIRMED** once on Beat AML 2.0 primary patient samples (520 samples, 479 patients, 16
wells). The frozen claims hold, but they are narrower than the label:
* The gain is bridge feedback. The source-verified agent chose to measure the Virtual Cell's top
  four inhibitors first and re-rank the rest (5/5 folds). This gave +0.073 hits per sample over
  the Virtual Cell alone and +0.229 over pilot matching.
* The basal-expression prior beat nearest-context transfer but not the context-free item prior.
* The agent matched, and did not beat, the standard exploit-first design.
* The development procedure it rejected (lookahead) carried a baseline defect that only uneven
  measurement exposes. It is corrected post hoc in `agent.bridge_design`, as development-grade.
* The LLM arm added nothing.

2026-10-16: [Anchor-purchase qualification and development diagnostic](anchor_purchase_20261016/REPORT.md)
completed with **BLOCKED_INDEPENDENT_ENDPOINT**. PRISM shared preprocessing and
unqualified culture starts/bundle costs prevent Q1 confirmation; Q2 was not fit.
On 794 selected secondary-screen drugs / 343 grouped components, inner selection
chose context means (1,113 known top-4 technical hits). Unpriced full X1 reference
gave 1,357 (+0.307/drug [0.231,0.385]), but missing-outcome bounds cross zero;
this is neither small-anchor value nor independent biological confirmation.
Offset-only information loses after cost. Keep the audit/controls, stop policy
expansion, and preserve the original PRESAGE NO-GO. No core scientific promotion.

New exposed-data development result (2026-10-16):
[PRESAGE-inspired target-pathway transfer](presage_transfer_20261016/REPORT.md)
fails P0. On 4,528 compound-held-out PRISM 19Q4 drugs / 568 identified lines,
pathway fusion Pearson is 0.1161 vs chemistry 0.1450; gain over chemistry+MoA
is +0.0028 [-0.0020,+0.0083]. Correspondence exceeds 20 stratified feature
permutations but adds no useful improvement over strong baselines. Top-3
nomination hits are 1,903 vs ungated neighbours 2,223. Stop P1-P3/LLM expansion;
no scientific model promoted. Tested thin-loop scope/support/identity and
retained-lineage-field guards are engineering repairs, not scientific gains.
Static scores, label-count inference and absent local ledger authentication remain
explicit limitations. Prior freezes and sealed outcomes were not changed.

Updated 2026-10-17. This is the current decision summary; [EVIDENCE.md](EVIDENCE.md)
keeps the numerical historical register. [STUDIES.json](STUDIES.json) registers the
retained studies. Each study keeps its protocol, results, deviations, source
identities, paid-call records and verifier. Software tests do not establish scientific validity.

## Auto-Research infrastructure (implemented thin core, 2026-10-16)

MAESTRO now has a small replayable research loop in `maestro.research_loop`. It
implements a testable replay mechanism for supplied hypothesis/action scores.
The loop accepts
two competing hypotheses, scope-qualified forecasts, a costed action menu and an
execution adapter. It selects expected information per cost, refuses forecasts outside
scope, spends budget only on admissible actions, binds outcomes to the planned action,
retains failures/QC failures, and serialises a deterministic receipt digest. Its
admission fields require source/context and a declared positive independent-unit
count; the thin loop does not authenticate source bytes or independence itself.
It uses label frequencies, not model likelihoods, and does not automatically
recompute remaining forecasts after feedback. Unknown outcomes
stop the loop as `invalid_observation` and remain visible in the receipt.

This is a thin orchestration layer, not a second agent framework: existing
`CaseStore`, `run_case_loop`, `select_expected_coverage`, evidence registry and strict
review remain the production paths. Multi-agent roles are therefore typed and narrow:
coordinator/state writer, forecaster, experiment designer and auditor; no role may
turn a forecast into evidence. High-risk execution and publication still require the
existing approval boundary.

Its proposed scientific value remains a **falsifiable hypothesis**, not a claimed
innovation or a validated discovery method. Required ablation before promotion:
independent-trial assumption vs dependency groups; raw vs
support/domain-shift-abstaining forecast; ledger-gated vs unconstrained update. Compare
against strong conventional/fixed and standard adaptive workflows on the programme's
qualified A/B tasks, keeping menus, total cost and randomness comparable. Primary metrics
are terminal decision utility/net benefit, false elimination, calibration and useful
information per cost. Any failed evidence-integrity or calibration gate yields
`NO_DEVELOPMENT_SIGNAL`; passing software tests is not an Auto-Research result.

## What deserves continued work

1. **Transfer of research procedures across discovery tasks.** Prioritise candidate
   discovery and context selection/failure analysis. Learn when procedures help,
   what checks reveal negative transfer and how feedback changes the plan. Keep
   unconditional updates, a simple gate and mature fixed/adaptive workflows as
   baselines; frozen future-task gains must exceed raw-history/text retrieval.
2. **Measured functional outcomes and scoped reuse.** Keep RKT, fixed sparse
   profiling, the GCP endpoint decoder and explicit refusal within their validated
   scopes. Their certificates do not transfer automatically to viability. Charge
   information, comparisons and confirmation against the same experimental cap.
3. **Dual-core contribution and honest evaluation.** Test response updates and
   procedure revision separately, then their interaction on a frozen utility
   scale. Separate shared-history component tests from closed-loop policy tests.
   Keep source-byte verification,
   measured lineage, source dependence, cold-start tiers, training-only normalisation,
   outcome seals and evidence-bound experiment approval. These are engineering
   safeguards; their effect on scientific decision quality still needs testing.

Do not add another agent, debate, memory or knowledge gate merely to increase
framework sophistication. The retained studies have not established Agent/LLM
incremental benefit over strong conventional workflows. A new experiment first
needs measured truth, a strong baseline, independent units, a frozen endpoint and
budget, and a predeclared useful net-benefit threshold.

## Evidence and stop decisions

| Study | Result worth preserving | Operating decision |
|---|---|---|
| [RKT / Block Q](knowledge_transfer_20261012/README.md) | On 702 sealed compounds, one-anchor pooled centred cosine 0.529 vs generic 0.287; gain over best single route +0.033. Fixed sparse design beat exhaustive design +0.181 (11/11 campaigns). | Keep scoped transfer and fixed design. Decision-planner superiority was not confirmed; no LLM override benefit. |
| [Context discrimination](context_discrimination_20261013/README.md) | RKT follow-up 158/702 discordances vs fixed 133. Matched 84-compound LLM pilot: integrated 10 vs fixed 16; interaction -11.90 percentage points. | No Agent synergy or fresh confirmation. Keep source receipts and negative results. |
| [GCP evidence transfer](evidence_transfer_20261013/README.md) | Deterministic blend 14/20 hits; integrated and conventional agents each 12/20; integrated-minus-deterministic CI [-30, +10] percentage points. | Synergy gate failed. No extension of the RNA certificate to GCP. |
| [Collaboration limits](collaboration_limits_20261013/README.md) | Same-forecast endpoint ranking raised hits 55/141 to 77/141 (+15.6 points, p=5e-5). P(hit) >=0.5 hit 81% vs 38% below. | Keep GCP endpoint ranking within its declared scope. Agent donor selection and simulated memory transfer did not earn promotion. |
| [Selective hit triage](selective_hit_triage_20261013/README.md) | Context triage 22 vs deterministic 12 hits; closed loop 23 vs conventional 18 (p=0.18); post-hoc non-agent classifier 38. Predictions admitted as measurements caused 15 false NO-GOs vs 3. | Agent success criterion not met. Keep identity/QC/seal and measured-evidence contracts. Disclose the post-opening unit correction; LLM arms remain NOT_RUN. |
| [Knowledge reality](knowledge_reality_20261013/README.md) | Chemistry+knowledge r 0.0842 vs 0.0786, but gene relabelling reproduces the gain (p=0.95). Novel biology/context/provenance routes add nothing. | G2 failed: mechanism-class membership only. No sealed PRISM 24Q2 confirmation or LLM layer. |
| [Evaluator audit](evaluator_audit_20261013/README.md) | Historical confirmation evaluator has test-batch normalisation, outcome-derived eligibility and unfrozen identity metadata. | Adopt C1-C7 in a new protocol before any confirmation; do not rewrite the historical evaluator. |
| [Orbit contrast](orbit_contrast_20261013/README.md) | Identity contrast +0.0104 in compound response; no gene-task identity value. Gate worse than unconditional residual (-0.0045); target triage unsupported. | IDENTITY_WITHOUT_METHOD / MECHANISM_CLASS_ONLY. Keep orbit decomposition as an evaluation device, not a promoted method. |
| [Mechanism falsification](mechanism_falsification_20261014/README.md) | 61,413 annotation pairs, zero measured positive or negative mechanism references. Strict benchmark 21/21 vs historical 6/21. Exploratory conformal FDP 0.26-0.70. | ASSET_BLOCKED. Contract conformance is not scientific improvement. Stop algorithm development without measured truth. |
| [Context transfer](context_transfer_20261017/README.md) | One-shot Beat AML 2.0: source-verified exploit-first bridging 0.850 hits/sample vs Virtual Cell alone 0.777 (+0.073, Holm p 0.0075), pilot matching 0.621, frozen lookahead 0.742. Virtual Cell prior vs item -0.008. P2 0, P5 trivial. | Keep bridge feedback and source-verified choice within the docstring scopes. Corrected lookahead needs a fresh confirmation. No LLM increment; repair/averaging stopped. |

Earlier supported results remain in [EVIDENCE.md](EVIDENCE.md): Block P's +17
unexpected hits [+11,+23], and Block N's scoped transcriptional transfer gains.
These are source/assay/endpoint-limited results, not a general drug-discovery claim.

## Smallest maintained architecture

| Area | Responsibility and retained boundary |
|---|---|
| `src/agent/` | Planning, tool execution, budget, durable CaseStore and restart. Model advice never becomes a measurement. |
| `src/maestro/` | Shared evidence types, admission, decisions, acquisition, repair and experiment authority. |
| `src/virtual_cell/` | Scoped prediction, model/data/axis identity, applicability, uncertainty and named refusal. |
| `tools/` | Explicit offline data preparation, audit and evaluation. No production dependency on study code. |
| `research/` | Registered immutable scientific records and replay code, separate from default software tests. |
| `tests/` | Behavior and regression protection; asset-dependent suites run only when explicitly requested. |

Heavy scientific libraries remain optional; the runtime dependency is NumPy.
Existing orchestration, budgets, restart, scoped memory and evaluation behavior stay
covered by the same default test cases. Unused fitting helpers with scientific
value are retained: absence of a current caller alone is not sufficient to discard
model fitting or frozen replay support.

Strict scientific reporting uses `evidence_registry`, `strict_decision_review` and
`evaluation_contract`. The additional acquisition dependence flag, `tier_gate` and
`endpoint_decision.choose_validated` are opt-in repairs from the pre-existing work.
Permissive historical defaults have not been switched globally; using them is not
an authenticated strict decision.

## Actual cleanup on 2026-10-14

- Removed the entirely unreferenced `maestro.licence` (309 lines) and
  `maestro.pharmacology` (390 lines). Their useful concepts remain in the typed
  premise/admission contracts; exact original implementations remain in Git history. Neither module had source, tool, test, research or CLI consumers.
- Removed unused `make_policy_input`, `group_judgments`, `EvidenceObservation`,
  `scalability_profile` and `ProposalPolicy`. Direct typed construction and the
  current evaluator remain the active interfaces.
- Replaced generated module path/API/dependency inventories with concise purposes
  and scientific boundaries. No function bodies or test assertions were changed
  by this documentation cleanup. Frozen source files were excluded.
- Replaced the repeated list of default test filenames with automatic `tests/`
  discovery. Explicit asset-dependent scope declarations remain checked for
  missing files and overlap. New core tests are now discovered automatically.
- Moved the ignored `tmp/` tree (3,728 files, 2,916,446,727 bytes) out of the active
  repository, then deleted after reviewing its records. Experiment directions,
  outcomes, limitations and provider accounting are retained in EVIDENCE; raw
  temporary copies and presentation drafts are discarded.
- Moved 16 regenerable cache directories (309 files, 10,328,708 bytes) out of
  the active repository; the temporary retention area was subsequently deleted.
- Condensed this report and corrected README's obsolete claim that all completed
  study implementations had been retired. Detailed study reports and EVIDENCE
  remain authoritative for scientific records.

Maintained Python source and tests decreased from 56,503 to 54,922 lines
(1,581 lines removed), before configuration and report condensation. This is a maintenance reduction, not an algorithmic speedup.
There is no claim that the framework has become a new minimal scientific method:
its surviving contracts are consumed by tested execution paths or retained replay.

The temporary snapshot and all moved historical/cache material were deleted on
2026-10-14 after the user explicitly requested key experiment records without
backups. Additional historical directions, GDSC success/failure reasons, source
identity, unexecuted next steps and provider accounting were consolidated in
[EVIDENCE.md](EVIDENCE.md) before deletion. The external retention directory no
longer exists. Removed: 4,760 files, 2,952,169,169 logical bytes (about 2.75 GiB).
This is file-content size, not a measured filesystem allocation delta. Git history
was not rewritten, and active repository data and registered studies remain.

Content-pinned production files (`knowledge_transfer`, `profiling`,
`information_tier`, `decision_review`, evaluation `scoring`) remain byte-identical
to the starting checkout. All registered study files except this summary remain
byte-identical to the starting checkout. No freezes, outcomes or sealed files were
rewritten, and no study, download or provider call was run.

## Verification and remaining limits

Baseline before the Auto-Research loop: **903 default tests passed** in 60.21 seconds.
After adding the thin loop and seven contract tests: **910 passed** (the focused
repository-shape and loop subset passes 33 tests). The unconfigured research
preflight still refuses with `BLOCKED/ASSET_MISSING`; these are software checks,
not scientific validation. The three explicit research suites still collect 32
cases when named.
All maintained Python sources parse; `git diff --check` passes. The research
preflight correctly refuses with `BLOCKED/ASSET_MISSING` (exit 2).
No registered study result was rewritten by the Auto-Research change. No scientific
result was revalidated.
Default software success, explicit research asset verification and scientific
verdicts remain separate.

Full State/checkpoint output axes, independent repeated primary endpoints,
mechanism truth, complete legal decision menus and authenticated operating costs
remain unresolved where the studies report them. Source data, outputs, paid-call
caches, prediction arrays, frozen protocols and negative results are retained.
A historical freeze is not automatically a currently qualified release.
