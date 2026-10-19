# Protocol: implementation identifiability, gates G0 and G1

Reference date 2026-10-19. Repository HEAD at start 59c1c7bd, working tree clean.
Status: **completed, exploratory known-case study. Not pre-registered.** The sources were read
before these rules were written, so nothing here is a frozen confirmation (see DEVIATIONS.md).
G2-G5 below are a conditional specification and were not executed.

## Question

For an experimentally supported genetic vulnerability, a defined cellular context, candidate
pharmacological implementations, legally available evidence and a finite action menu, does the
evidence allow explanations to be separated by a legal measurement in a way that would change which
implementation is advanced? This is preclinical cellular pharmacology only.

## Preserved stop decisions

These branches stay stopped and are not restarted under new names: Beat AML low-rank bridging
(`beataml_g1_20261017`, G1 FAILED), `BridgedTransferModel` rank, prior, scorer and probe rules, Jaaks
same-family substitution (`action_substitution_20261019`, `biological_residual_gate_20261019`,
UNDERPOWERED/STOP), kinobeads similarity kernels (`kinobeads_substitution_20261019`, NOT_SUPPORTED),
unconstrained program revision (`program_revision_20261017`, `feedback_propagation_20261018`).
No frozen record was edited. No thresholds from those studies are reused.

## Hypothesis labels

`H_E`, `H_M`, `H_C`, `H_O` are not defined anywhere in the repository (README, research registry,
reports, protocols, logs, source). They are not used and not redefined. Study-local explanation
names are used and no mapping to the earlier labels is claimed:

| id | sufficient-cause explanation for loss of viability or apoptosis after JB170 |
|---|---|
| `EX_PROTEIN_LOSS_SCAFFOLD` | loss of AURKA protein (a non-catalytic role) is needed |
| `EX_CATALYTIC_INHIBITION` | loss of AURKA catalytic activity is sufficient |
| `EX_CRBN_DEPENDENT_OFFTARGET` | CRBN-dependent effect not routed through AURKA |
| `EX_WARHEAD_OFFTARGET_BINDING` | off-target kinase binding by the alisertib-derived warhead |
| `NONE_OF_THE_CURRENT_EXPLANATIONS_IS_SUFFICIENT` | returned when every listed explanation is refuted |

Explanations may coexist. The surviving set is the unrefuted set, not a probability distribution.

## Four levels kept apart

intervention method (chemical, siRNA, engineered mutant) -> pharmacological implementation
(molecule, mode, dose, time) -> proximal effect (engagement, abundance, activity) -> terminal
functional outcome (viability, apoptosis, cell cycle). JB211 is a CRBN-null AURKA binder control;
it is never labelled pharmacologically inactive. Degradation is not catalytic inhibition. Evidence
types (annotation, observed result, model prediction, mechanistic reference, independent
confirmation) are separate record types.

## G0 rules (applied to metadata only, never to outcome values)

Unit: a coherent relationship with scientific task, genetic reference, implementations, proximal and
terminal readouts, discriminating controls, lineage, provenance, access status and costs
(`records.py`, `UNITS`). Binding (`idlib.bind_conditions`): identical cell, genotype, time and readout
are required, otherwise the records are refused; a dose difference binds descriptively only.

| level | rule |
|---|---|
| 1 ANNOTATION_ONLY | no observed matched contrast |
| 2 PARTIAL_PAIRED_EVIDENCE | at least one condition-bound contrast between two implementations |
| 3 QUALIFIED_IMPLEMENTATION_UNIT | all of: L3a every implementation shares a dose-matched primary terminal endpoint; L3b every implementation shares a strict proximal readout; L3c discriminating controls and a genetic reference present; L3d numeric values with uncertainty extracted for primary and proximal records; L3e lineage reported to batch or plate; L3f genetic reference on the primary terminal endpoint |
| 4 INDEPENDENT_CONFIRMATION_UNIT | level 3 plus an exposure ledger showing the outcomes were never read before freeze |

Counts exclude wells, technical replicates, repeated extractions and seeds. Decision: any level 3
-> QUALIFIED_FOR_RESEARCH only if a power parameter justifies it, else UNDERPOWERED; level 2 only
-> QUALIFIED_FOR_LOGIC_TEST; none -> ASSET_BLOCKED. Only one complete case or fewer means logic tests
only and no general implementation model.

## G1 definition

Three domains: `source` (development evidence), `query` (initial evidence, stripped legal menu,
budget), `evaluator` (unpurchased outcomes, vault). The decision process runs in a child interpreter
with a working tree of source, query, policy and state only; the vault path is never given. Tests
check that changing evaluator outcomes leaves the pre-purchase proposal byte-identical, that no
outcome-bearing record id or canary appears in the proposal or the tree, and that one purchase
releases exactly one observation and one ledger event. This is process-level isolation, not a
sandbox; an LLM run needs OS-level controls and was not performed.

Explanations map to admissible outcomes per assay, with premises where an assay is only readable
under an assumption (JB211 inhibits the kinase). An assay is informative when some outcome refutes
some but not all compatible explanations; decision-relevant when outcomes map to different
terminal labels (`advance(degrader)`, `switch(alisertib_class_inhibitor)`, `stop`, `unresolved`,
`still_indistinguishable`). The menu for replay contains only bundles whose real published outcome
exists. Other bundles are proposed missing evidence. Replay-menu selection by outcome availability
is itself a retrospective-design limitation.

Section 9.4 criterion (met only if all hold): a qualified (level 3) unit, two compatible
explanations, a legal assay that separates them, different terminal decisions, and the realised
legal outcomes resolving the pair. Engineering and biological results are reported separately.
No outcome probabilities are used; none are supported by the records.

## Conditional specification G2-G5 (not executed, not authorised)

**Entry conditions.** G2 needs a G0 result of QUALIFIED_FOR_RESEARCH with a justified power
parameter, a G1 biological pass on level 3 units, and all parameters below frozen before any outcome
is opened. G5 needs separately qualified independent evidence never read by the design.

**Parameters to fill and freeze (none are filled; none may be borrowed from Jaaks, the 0.03
substitution margin or Beat AML utilities):** functional_success_threshold, minimum_useful_gain,
false_progression_margin, assay_budget, sample_budget, turnaround_budget, API_compute_budget.
Missing parameters mean outcomes stay closed.

**Primary endpoint.** Independently functionally confirmed effective implementations per qualified
task under a fixed budget; at most one advancement per task; wells and repeats are not discoveries;
full denominator of eligible tasks retained; benefit on candidates whose own outcome was not
purchased reported separately.

**G2 information value.** Does a legally acquired proximal observation improve held-out functional
judgments? Shared-history ablation, I0 masked vs I1 available.

**G3 representation.** M0 regularised same-input conditional or hierarchical model vs M1
implementation-aware factorisation p(m,y|u,c,D)=p(m|u,c,D)p(y|m,u,c,D) with the direct dependence on
u kept and proximal uncertainty integrated when m is not acquired. M1 need not be a neural network;
if M0 matches it, keep M0. Online updates limited to task-posterior beliefs and prespecified
parameters; no free rewriting against a frozen test set.

**G4 Agent.** One research Agent, deterministic evidence validator, numerical predictor,
deterministic selector, restricted executor; at most one proposal and one critique; actions only
advance, switch, measure, stop, unknown; zero or one acquisition round at first; numbers only from
validated model outputs or observations. Comparators with equal information, menu and cost: fixed
expert panels, retrieval plus templates, deterministic constraint search, standard Bayesian design
and expected value of information, direct confirmation, random choice, Agent without critique. The
conventional policy may measure or confirm directly. Value Q(a|D,B)=E_z[V(D u {a,z}, B-c(a))]-V(D,B)
with V allowing the strongest no-measurement decision and cost entering once through the budget.

**Factorial design.** Information (hidden/available) x Model (M0/M1) x Policy (conventional/Agent), eight
conditions; interaction contrast U111-U110-U101+U100 reported with the full-system advantage over the
strongest conventional policy and model. Positive total gain without positive interaction is a
system-level improvement, not dual-core synergy. Two modes (shared-history ablation; independent
closed loop) never share a cost ledger. Actual expenditure and simulated acquisition are separate
ledgers.

**Statistics.** Lower 95% bound of paired utility gain above the minimum useful gain; explicit
non-inferiority on incorrect advancement; familywise 0.05; power 80% when feasible; grouped or
hierarchical inference over target families, implementations, batches and shared controls; wells and
seeds are not independent units.

**G5.** One stated generalisation claim at a time (unseen implementation, target family, cell
context, batch or laboratory). Any dataset used to build hypotheses, choose measurements, tune or pick
endpoints is exposed for that claim. If no qualified resource exists: DEVELOPMENT_SUPPORTED and
CONFIRMATION_BLOCKED.

Failed gates are labelled ASSET_BLOCKED, UNDERPOWERED, NOT_SUPPORTED or OUT_OF_SCOPE. Missing
resources do not prove a hypothesis false.
