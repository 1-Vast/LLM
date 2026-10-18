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

2026-10-17: [Seed attribution](seed_attribution_20261017/REPORT.md) repairs the PRISM evaluation
contract and asks what explains the fixed-seed benefit. It is **development** on the same exposed
PRISM 19Q4 strata (`verify.py` VERIFIED; nothing frozen was edited; no sealed tier opened).
* The earlier evaluation was not one contract: score reference `(X2+X3)/2` (NaN for single replicates) against
  labels on the mean of available replicates, 100 source drugs with no frozen threshold (24 remain
  undefined and are refused by name), a fit cache that ignored the data, and a Gaussian crossing score
  that ranks well (AUROC 0.834) but is not shown to be a calibrated probability of the complete
  qualified-hit event.
* The frozen development bench is not a prospective replay: every fold trains on 74-101 of the 103
  reserved query lines, and scrambling query outcomes changes the fold means, residuals, probe design,
  proposals and diagnosis. The masked bench (`replay.MaskedBench`) is exactly invariant. Query hits
  for the seed library fall from 4.41 to 3.87 per line (I2) once the query lines are masked.
* **Corrected evidence statement.** Seed minus strong model: I2 +0.211 [+0.097, +0.340] frozen, **+0.117
  [-0.026, +0.248]** repaired; I1 +0.445 -> +0.283 [-0.065, +0.699]; exploit-first campaign +0.437 ->
  **+0.356 [-0.088, +0.856]**. All three registered primary tests are NOT_CONFIRMED (Holm p 0.29-0.31).
  Point estimates stay positive; the gain is concentrated in skin (82% of the policy gain) and
  BRAF/NRAS-mutant lines, with a loss of -0.32 hits/line on gate-negative lines.
* Attribution: the seed pairing exceeds all 20 capacity- and support-matched permutations at every layer
  (the smallest possible exact p, 1/21) but the matched contrast is only supported at I2 (lower bound
  +0.001, Holm p 0.22). Extra capacity, per-drug loadings and uncertainty estimation add nothing; a plain
  ridge on the same ten scope-by-gate features matches the library (B - C1 -0.004 [-0.198, +0.166]); a
  ridge given all 72 products does not find the pairings (+0.093 [-0.018, +0.191]).
* Cost units are now six separate accounts. Part 4 (small-menu opportunity diagnostic) was not run: no
  primary test had a positive lower bound.

2026-10-17: [Beat AML gate G1](beataml_g1_20261017/REPORT.md) (development, exposed data, frozen before
the run, `verify.py` VERIFIED) **FAILED**. The frozen candidate (coherent score, exploit-first probes,
k chosen on source patients) beats the ridge by +0.098 [+0.045, +0.153] total hits per sample; the
registered gate needs the lower bound minus 0.05 per extra round to exceed 0.05 (it is -0.005).
* The probe round, not the low-rank model, carries the gain: it adds +0.125 to the candidate and +0.083
  to a ridge; ridge-plus-feedback is within +0.015 [-0.036, +0.066] of the candidate, and the low-rank
  prior without observations is no better than the ridge (-0.027 [-0.065, +0.011]).
* The confirmed two-round engine is not shown better than the one-round ridge (+0.019 [-0.033, +0.073]);
  the candidate beats it by +0.079 [+0.032, +0.127].
* Registered consequence: **stop the low-rank state-model branch**; keep the feedback pattern on the
  strongest prior with the ridge as comparator. k = 8 is best post hoc (+0.131 over the ridge, not
  passing the strict gate).

2026-10-18: [Feedback propagation](feedback_propagation_20261018/REPORT.md) (development, exposed folds
2-4 of PRISM 19Q4; frozen before the comparison; `verify.py` VERIFIED; no sealed tier opened) asks whether
observed feedback can identify and repair a failure in how responses propagate to *unmeasured* pairs.
**STOP; no program search.**
* Audit: the saved indication-triage totals reproduce (395 vs 293) and 394 of 395 (and 293 of 293) of those
  hits are pairs the arm itself probed, so that task never tested propagation. Unmeasured-pair nominations
  are the primary utility here; pool wells (about 24 lines) are the physical read unit and costs stay
  hypothetical (no plate/well map). Secondary equal-lineage seed-attribution interval corrected (erratum).
* Ridge-plus-feedback does propagate at pool cost: +1.056 [+0.626, +1.526] events per 64 compounds over the
  structure prior (2.64 vs 1.58), not at 16 logical lines (+0.167 [-0.108, +0.451]).
* The registered repair (kNN-analogue prior plus ridge residual update) is not distinguishable from
  ridge-plus-feedback (+0.139 [-0.579, +0.870]; development had +0.81) or from kNN (+0.083 [-0.279, +0.437]);
  its prediction error is lower in every fold (0.265/0.296/0.243 vs 0.287/0.327/0.255) without a decision
  gain. A leave-one-pool-out diagnosis identifies the better rule per compound only weakly (AUC 0.59-0.63);
  a perfect choice would add +0.53 [+0.06, +1.05]. A second noise draw gives +0.86 for the same contrast.
* Value-greedy closed-loop acquisition is below the fixed A-optimal design at the same 3 pools (R1 2.25 vs
  2.78), because it measures the pairs it would nominate.

2026-10-18: [Acquisition programs](acquisition_program_20261018/REPORT.md) (development, exposed PRISM 19Q4, whole-pool target set so probes never
reveal target entries; frozen incumbents before held-out; `verify.py` VERIFIED). Predecessor hindsight clarified: campaign-level best of
ridge/R1 lists gives 131 vs 100 hits (unavailable diagnostic; the old per-compound selector chose by squared error).
* Held-out (folds 2-4, five fresh paired noise draws, events per 64 compounds): fixed design 1.822; one-step posterior lookahead 1.717
  (−0.106 [−0.262, +0.022]); agent-search incumbent 1.725 (+0.008 [−0.033, +0.054] over the lookahead); conventional random search
  accepted nothing in 12 proposals. A development lead (+0.100 [−0.003, +0.199]) did not transfer; the unavailable ceiling of the
  acquisition choice is +7% held-out (+34% in development). Lookahead probabilities rank but overstate levels about tenfold.
  Candidate failures are recorded; ridge-plus-feedback and the fixed design remain the reference.

2026-10-17: [Program revision](program_revision_20261017/REPORT.md) is a pre-registered study on
PRISM 19Q4 (freeze 12:55:48Z, future strata opened once at 13:09:54Z; `verify.py` VERIFIED). It asks
whether MAESTRO's agent improves future decisions by revising a shared library of executable,
observably gated response programs on top of a strong low-rank model. It does not.
* A 10-program textbook seed library helped on 247 future lines under the **frozen** contract: +0.21
  hits/line with 8 probe wells (H1, Holm p 0.004), +0.45 with none, +0.44 in exploit-first campaigns.
  **Superseded by the corrected contract above**: +0.12, +0.28 and +0.36, no interval excluding zero.
  The gain is larger on unseen lineages (+0.25 vs +0.10 at I2, frozen).
* Revision adds nothing: editable minus fixed library 0.000 (H4), vs stepwise search +0.008 (H2),
  LLM vs enumeration +0.004 (H3). The 0.000 reflects that the primary LLM library **equalled** the
  fixed seed library (no revision-added program survived), not a measured difference between two
  different libraries. Programs learned from an empty start give +0.05 in the seeded-arm ablations,
  which do not cover every empty-start program; every revision-added program has ablation value <= 0.
  Joint measurement edits changed nothing.
* About 4,300 logical development wells per arm bought no gain over the free seed; the cost is never
  repaid. These are per-pair logical charges, not plate wells (the cost-unit accounts are separated in the
  seed attribution).
* Post hoc: the within-lineage development arena would reject most useful seed programs (6
  BRAF-mutant query lines vs 37 in future lineages). For 20-23% of the LLM's candidates the sign of the
  residual coefficient disagreed with the stated direction; that is a sign disagreement in a fitted
  residual, not a measured biological error rate. The development bench itself trained on the reserved
  query outcomes (see the seed attribution above), so its development numbers were not prospective.
* Shared loadings do not transfer to unseen drug structure groups. In 28-well campaigns, 8 probes
  lose to exploit-first feedback (-0.38). AFA beats a fixed design (+0.22) at 10 rounds.
* No independent confirmation: same-screen future strata are not independent. Cost: 0 purchased wells
  (archived outcomes), deepseek-flash 0.287 USD.

2026-10-17: [Feedback attribution](feedback_attribution_20261017/REPORT.md) is a
pre-registered **development** study on the same, exposed Beat AML data. Its audit is in
`AUDIT.md`. It confirms nothing.
* All groups share four population-chosen probes. With them, the low-rank update helps without RNA
  (H1 +0.096), RNA adds once readouts arrive (H2 +0.065), and the update beats an
  overall-sensitivity-only update (H4 +0.081). Deranged readouts are worse than none (D - F
  +0.115). All four are Holm-positive, but none clears the 0.05 minimum useful effect at its lower
  bound.
* The registered "RNA prior has independent value" (H3) is against the model's own population
  state. That comparator is broken by an incoherent event score. Against the empirical item prior
  the RNA prior gives -0.017, and a drug-specific ridge on the same PCs beats it (-0.065).
* The confirmed two-round engine is not shown better than that one-round ridge (+0.023
  [-0.029, +0.077], post hoc).
* A coherent event score adds +0.04 to +0.08 per group but is not calibrated (Gaussian tails too
  thin). Eight probes beat four (+0.065), and the reference planner only ever chose eight.
* Tuned exploit-first is not beaten by any selector (hybrid -0.031, calibrated -0.065).
* Cost: 0 wells, $0.

2026-10-17: [Context transfer with verified bridges](context_transfer_20261017/REPORT.md)
is **CONFIRMED** once on Beat AML 2.0 primary patient samples (520 samples, 479 patients, 16
archived AUC queries, about 112 treatment wells). That label records protocol execution. The
[claims amendment](context_transfer_20261017/CLAIMS.json) supports only the functional-feedback
gain under the replay, as workflow transfer within Beat AML. The frozen claims hold, but they are
narrower than the label:
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

## Integrated assessment and decision

The strongest recent signal is **functional feedback within a defined replay**: on Beat AML,
measuring a few high-scoring inhibitors and updating rankings improved later choices over the
Virtual Cell alone. This supports a bounded workflow result within Beat AML, not an independent
biological replication or an Agent/LLM advantage. The exposed-data attribution study narrows the
interpretation: readouts carry useful drug-specific information, but the RNA prior does not beat
the empirical item prior or same-feature drug-specific ridge; no procedure selector beats tuned
exploit-first. Its coherent score is promising for ranking, but remains uncalibrated. Gate G1 then ran
(2026-10-17) and failed: the probe round carries the gain, a ridge given the same round is within +0.015
of the low-rank candidate, and the candidate's lead over the one-round ridge (+0.098 [+0.045, +0.153]) does
not clear 0.05 net of a round. The functional-feedback result stands as a workflow result; the low-rank
state model adds nothing to it on this domain.

The PRISM program-revision study is a separate result. A fixed textbook library helps on future
lines within that screen, especially unseen lineages, but autonomous revision, conventional search,
LLM proposals and joint measurement edits add no value; the revision cost is not recovered. This is
prior-knowledge use, not learned discovery, and it does not transfer to unseen drug structure
groups. Its same-screen future strata are not independent confirmation. The seed attribution then
showed that the frozen evaluation contract and development bench were inconsistent and non-prospective;
under the repaired contract the seed gain is positive but unconfirmed (+0.12 to +0.36), concentrated in
BRAF/NRAS-mutant skin lines, and matched by a ridge on the same ten features. The shared cross-study
lesson is to test against the strongest simple comparator and align development arenas with the
target strata; it does not make the Beat AML and PRISM effects one pooled finding.

The 2026-10-18 feedback-propagation study further separates **feedback value** from **learning a
better update rule**. On exposed PRISM folds, ridge-plus-feedback improves nominations of unmeasured
pairs over the structure prior at a hypothetical pool-read cost, but the analogue-anchored repair is
not distinguishable from ridge-plus-feedback or kNN; a feedback-only diagnosis identifies the better
rule weakly, and value-greedy closed loops lose to fixed A-optimal design. The old indication-triage
totals mostly re-read measured pairs and are not evidence of propagation. No reproducible repair or
Agent/LLM search is justified. Together with G1, the current evidence supports scoped feedback as a
workflow component, while learned model correction, procedure selection, and autonomous revision
remain unsupported or unconfirmed. PRISM results are exposed-data development, not confirmation.

One secondary seed-attribution interval was also too narrow because repeated lineage draws were
collapsed in its bootstrap; the separate [erratum](seed_attribution_20261017/ERRATUM_20261018.md)
corrects the interval without changing the registered primary tests or decisions.

**Work order.** First, MT-P0 qualifies the compact A/B task, action, cost and dependence manifest;
this is a programme-wide prerequisite for learning procedure value. G1 is complete and failed: do not
develop further variants of the low-rank state model on Beat AML; keep the exploit-first feedback pattern
with a ridge as the mandatory comparator. **Conditionally permitted:** a confirmation of the feedback
pattern only on a new, independent, powered domain, with ridge-plus-feedback as the comparator and the
round value declared in advance; none is local, so it stays blocked. **NO-GO:** an autonomous
applicability-boundary revision study on PRISM. The opportunity gates did not pass (no primary seed test
has a positive lower bound under the corrected contract), so no such protocol is drafted here and no
revision, LLM-proposal or grammar-search campaign is started. Any later PRISM question needs
`replay.MaskedBench`, lineage-disjoint arenas, the pooled gate-count floor and curated non-LLM proposals as
comparator, and PRISM 24Q2 REP.1M stays sealed until access is authorised and independence is verified.
Public-metadata checks may proceed within existing authorisation; they must record access status,
provenance, prior exposure, overlap and task compatibility separately and must not read sealed response
outcomes. Neither development analysis establishes confirmation; if no qualified independent domain is
available, keep the broader claim blocked.

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
| [Context transfer](context_transfer_20261017/README.md) | One-shot Beat AML 2.0: source-verified exploit-first bridging 0.850 hits/sample vs Virtual Cell alone 0.777 (+0.073, Holm p 0.0075), pilot matching 0.621, frozen lookahead 0.742. Virtual Cell prior vs item -0.008. P2 0, P5 trivial. | Keep exploit-first bridge feedback within the docstring scopes. Cell-state prior, procedure selection, LLM and cost advantage are not established (CLAIMS.json). Corrected lookahead needs a fresh confirmation; repair/averaging stopped. |
| [Feedback attribution](feedback_attribution_20261017/README.md) | Development on exposed Beat AML. Common-probe attribution: update without RNA +0.096, RNA with feedback +0.065, structure vs overall-sensitivity update +0.081, deranged control -0.115. RNA prior vs item prior -0.017; drug-specific ridge beats the RNA prior (+0.065) and is not beaten by the two-round engine (+0.023, CI crosses 0). Coherent score +0.04 to +0.08; 8 probes beat 4 (+0.065); no selector beats tuned exploit-first. | G1 has run and failed (see below). Independent confirmation blocked: no unexposed domain; PRISM 24Q2 independence unverified. |
| [Program revision](program_revision_20261017/README.md) | PRISM 19Q4, 247 future lines. Seed library +0.211 hits/line at I2 (Holm p .004), +0.445 at zero observation, +0.437 in exploit-first campaigns. Editable vs fixed 0.000; vs stepwise +0.008; LLM vs enumeration +0.004. No transfer to unseen drug groups. | Method not supported; revision wells never repaid. Seed library is knowledge use, not discovery. Frozen numbers superseded by the corrected contract (next row); revision NO-GO. |
| [Seed attribution](seed_attribution_20261017/REPORT.md) | Development on exposed PRISM 19Q4. Contract repaired (single endpoint, out-of-sample variance, data-keyed cache); frozen bench trained on reserved query outcomes (masked bench exactly invariant). Seed minus strong: policy +0.356 [-0.088, +0.856], I2 +0.117 [-0.026, +0.248], I1 +0.283 [-0.065, +0.699]; all NOT_CONFIRMED. Seed beats all 20 matched permutations (exact p 1/21) but only I2 passes the reading rule; ridge on the same 10 features matches it (-0.004 [-0.198, +0.166]); capacity, per-drug loadings and variance add nothing. | Seed library kept as an optional scoped component, exploratory effect; comparator for any library claim is a ridge on its features. Revision, LLM proposal and grammar search stopped; opportunity diagnostic not run. |
| [Beat AML G1](beataml_g1_20261017/REPORT.md) | Development on exposed Beat AML, frozen before the run. Candidate minus ridge +0.098 [+0.045, +0.153]; strict gate lower bound -0.005 net of a round. Probe round: +0.125 (low-rank), +0.083 (ridge); candidate minus ridge-plus-feedback +0.015 [-0.036, +0.066]; low-rank prior without observations -0.027 [-0.065, +0.011]. | G1 FAILED: stop the low-rank state-model branch; keep exploit-first feedback on the strongest prior with the ridge as comparator. No confirmation domain. |
| [Feedback propagation](feedback_propagation_20261018/REPORT.md) | Development on exposed PRISM 19Q4 folds 2-4, frozen before the run. Ridge-plus-feedback +1.06 events/64 compounds over the structure prior on unmeasured pairs; analogue-anchored repair vs ridge +0.14 [-0.58, +0.87], vs kNN +0.08 [-0.28, +0.44]; diagnosis AUC 0.59-0.63; old triage hits are 99.7% probed pairs. | STOP: no program search; ridge-plus-feedback with kNN comparator stays the reference. |

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
