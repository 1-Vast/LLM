# MAESTRO: current evidence and repository simplification

Updated 2026-10-16. This is the current decision summary; [EVIDENCE.md](EVIDENCE.md)
keeps the numerical historical register. [STUDIES.json](STUDIES.json) registers all
nine retained studies. Each study keeps its protocol, results, deviations, source
identities, paid-call records and verifier. Software tests do not establish scientific validity.

## Auto-Research direction (implemented thin core, 2026-10-16)

MAESTRO now has a small replayable research loop in `maestro.research_loop`. It
implements the proposed high-value direction as a testable engineering mechanism:
**dependency-aware, evidence-authenticated hypothesis elimination**. The loop accepts
two competing hypotheses, scope-qualified forecasts, a costed action menu and an
execution adapter. It selects expected information per cost, refuses forecasts outside
scope, spends budget only on admissible actions, binds outcomes to the planned action,
retains failures/QC failures, and serialises a deterministic receipt digest. A
qualified outcome must identify its source and context and declare positive independent
units; it cannot update support merely because a model predicted it. Unknown outcomes
stop the loop as `invalid_observation` and remain visible in the receipt.

This is a thin orchestration layer, not a second agent framework: existing
`CaseStore`, `run_case_loop`, `select_expected_coverage`, evidence registry and strict
review remain the production paths. Multi-agent roles are therefore typed and narrow:
coordinator/state writer, forecaster, experiment designer and auditor; no role may
turn a forecast into evidence. High-risk execution and publication still require the
existing approval boundary.

The innovation is a **falsifiable hypothesis**, not a claimed scientific win. Required
ablation before promotion: independent-trial assumption vs dependency groups; raw vs
support/domain-shift-abstaining forecast; ledger-gated vs unconstrained update. Compare
against fixed sequence, cost-greedy, forecast-only, agent-only and hindsight oracle on
at least three independent tasks using the same menu, budget and seeds. Primary metrics
are terminal decision utility/net benefit, false elimination, calibration and useful
information per cost. Any failed evidence-integrity or calibration gate yields
`NO_DEVELOPMENT_SIGNAL`; passing software tests is not an Auto-Research result.

## What deserves continued work

1. **Scoped response transfer with a measured anchor.** Keep RKT, the fixed sparse
   profiling design and their uncertainty/refusal contracts. Qualify another source
   and endpoint before extending the L1000 certificate. Cold-start transfer remains weak.
2. **Decisions aligned with measured endpoints.** Keep calibrated raw-threshold
   ranking and explicit abstention within the validated GCP scope. Replicate
   agreement, dose, time and assay context must be declared.
3. **Authenticated evidence and honest evaluation.** Keep source-byte verification,
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
