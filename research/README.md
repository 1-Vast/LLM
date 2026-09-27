# Research record

Latest: [MAESTRO v2 audit and gated research plan](gated_plan/README.md) (audit and plan only; nothing
registered or promoted). The historical numbers describe a transcriptomic MoA proxy task, not the agent's
prerequisite-repair claim. On the one real prerequisite task (6 engagement cases), directed repair adds nothing
over a selector given the same capabilities. The production repair path and the research belief planner are not
connected. Protocol v2's legal menu moves with an outcome (12 SciPlex3 conditions dropped for low cell counts).
The fixed order reaches 63.3-99.4% of the oracle's correct decisions; the earlier "99.6%" does not reproduce.

Previous: [protocol external-validation-2](protocol_v2/README.md). It covers immutable registration,
truth-free execution with fail-closed scoring, task headroom and power gates, a baseline-safe
planner, cross-study calibration, and the virtual-cell and feedback decision gates. No MAESTRO
policy meets its success criteria. The fixed order already reaches 63-99.6% of the oracle's
correct decisions, and 76-82% of L1000 episodes cannot be decided from the menu. A confirmatory
test needs an unopened study with 345-813 label-compatible units. Protocol-v1 evidence is
archived in [experiments/](experiments/README.md).

Previous: [belief-space planning with a virtual-cell world model, and the first locked external test on GSE70138](belief_planning/README.md). The agent did not beat the fixed expert order on 38 new compounds (INCONCLUSIVE; a +0.02 gain is excluded), and the virtual-cell and feedback contributions were rejected.

Previous targeted follow-up: [sparse-reference measurement value, cost curves and regression proof](sparse_value/README.md).
The fallback continuation defect is repaired; 186,420 real-data records compare the new conditional
reference policy at seven acquisition prices. Results support a local L1000 benefit, not general promotion.

Designs, protocols and analysis for MAESTRO, synchronized as work proceeds. The claim and its
formal decision layer are in [`../Innovation.md`](../Innovation.md); the runnable surface is in
[`../README.md`](../README.md); the task gates are in [`../task.md`](../task.md).

## Contents

| File | Subject | Status |
|---|---|---|
| [`agent_architecture.md`](agent_architecture.md) | Knowledge base, memory registers and star topology, context compression, sub-agents, collaboration protocol, deep reasoning, judgment accuracy | Design; implemented parts marked |
| [`decision_layer.md`](decision_layer.md) | Belief state, action space, value of information, error accumulation, acceptance tests | Design; implemented parts marked |
| [`judgment_stability.md`](judgment_stability.md) | Reproducibility as an admission test: the Brier decomposition, the averaging law, and the gate that needs no outcome | Implemented and measured |
| [`dynamic_networks.md`](dynamic_networks.md) | Conditional regulatory structure, complementarity, structural redundancy, multimodal and multiscale use | Partial; conditioned retrieval and planning diagnostics implemented |
| [`framework_optimization.md`](framework_optimization.md) | Conditioned biological assertions, agent/Jev evidence context, modality contributions, costs and live verification | Implemented; biological utility remains unvalidated |
| [`agent_research_20260925.md`](agent_research_20260925.md) | Report verification, primary agent literature, task-state loss reproduction, bounded repair and paired API probe | Targeted research complete; context repair implemented and tested; scientific utility unvalidated |
| [`typed_decision_model.md`](typed_decision_model.md) | TypeSafe Jev integration, its boundary, and the live-verified HTTP contract | Implemented and verified |
| [`engineering_record.md`](engineering_record.md) | Literature-grounded optimization pass and the topological analysis of the action and package graphs, with measurements | Implemented and measured |
| [`asrg/`](asrg/00_index.md) | Action-Supported Repair Geometry: audit, data and cost matrix, frozen protocol, decision memo | Research design; go/no-go gates open |
| [`analysis/`](analysis/) | Executable checks: residual non-identifiability, gain identity, reachability bound, synthetic selection | Runs offline |
| [`local_verification/`](local_verification/README.md) | Protocol, fixtures and scripts for the checks that need a machine with credentials and local assets | Protocol; offline half runs anywhere |
| [`biological_depth/`](biological_depth/README.md) | Pre-registered test of whether the virtual cell and the agent carry perturbation-specific biology: literature anchors, systematic-shift-centered metrics, JEPA-style latent world models, an agent probe, and the SciPlex3 label-offset finding | Measured 2026-09-26; see its README |
| [`dynamic_world_model/`](dynamic_world_model/README.md) | Pre-registered test of whether scenario cards, a time-aware policy, a learned population transition model or language-model planners choose measurements that separate mechanisms better than the current magnitude tie-break; SciPlex3 24 h and 72 h, validator, case study and closed-loop replay | Measured 2026-09-26; negative for promotion, see its README |
| [`acquisition_link/`](acquisition_link/README.md) | Audit of the link from world-model prediction to measurement choice (priorities dropped on the power-aware path, per-hypothesis forecasts reduced to one number, borrowed exposure times, deleted low-support actions), the distribution-aware selector that repairs it, and its pre-registered evaluation on the block-2 episodes | Implemented (opt-in) and measured 2026-09-26; INCONCLUSIVE, not promoted |
| [`sequence_audit/`](sequence_audit/README.md) | Why the follow-up's contingent two-step policy stops early, a behaviour-matched replay of every comparator, one pre-registered revision (fixed-sequence fallback when the planner is uninformed), and its independent validation on L1000 6 h / 24 h in four lines | Measured 2026-09-26; SHADOW by the frozen rule with a negligible effect, opt-in, not promoted |
| [`external_validation/`](external_validation/README.md) | Evidence audit, external-validation firewall (sealed policy view, one-time vault, manifests), a frozen 14-rung baseline ladder, decision- and risk-focused evaluation, virtual-cell masked and permuted ablation, and the external-study candidate audit | Measured 2026-09-27 on development data: `maestro_vc` REJECTED under frozen gates; external test blocked by missing data |
| [`belief_planning/`](belief_planning/README.md) | Repository audit after a Codex session; belief-space planner (`src/maestro/planning.py`) with an empirical-Bayes virtual-cell world model; attribution controls (virtual cell masked or permuted, feedback withheld or permuted); GSE70138 external study behind a one-time vault | Measured 2026-09-27: external INCONCLUSIVE vs fixed order (-0.024 [-0.074, +0.011]); virtual-cell and feedback contributions REJECTED; development REJECTED in SciPlex3 A, INCONCLUSIVE elsewhere |
| [`protocol_v2/`](protocol_v2/README.md) | Protocol external-validation-2: evidence audit of the eight 2026-09-27 review reports, clean-tree registration and verification at the registration commit, fail-closed truth semantics and a whitelisted policy view, measurement states, task headroom and power gates, the baseline-safe (SPIBB-style) arm, leave-one-study-out calibration, virtual-cell and feedback decision gates, and the development screen | Measured 2026-09-27: `safe` SAFE_ON_DEVELOPMENT with no development signal; virtual cell and feedback REJECT_AS_DEFAULT; external confirmation blocked (no unopened study with enough units) |
| [`experiments/`](experiments/README.md) | Archived protocol-v1 experiments: digests, statuses and freeze verification of every original artefact | Archived 2026-09-27 12:04; read-only |
| [`gated_plan/`](gated_plan/README.md) | MAESTRO v2 repository-grounded audit and gated plan: requirement matrix, qualified historical claims, execution-path wiring table, contribution cards for the agent (AG), the world model (WM) and their combination (JOINT), data-flow and threat model, a real repair trajectory, the minimal implementation plan, dataset qualification and the registry for E-DATA1, E-CAL1, E-WM1, E-AG1, E-JOINT1 and EXT-1 with WM-G0-G4 and AG-G0-G3 | Audit and plan 2026-09-27 (block 4): AG-G2 INCONCLUSIVE (no additional algorithmic contribution identified), WM-G1-G3 FAIL, JOINT NOT_READY; nothing registered |

2026-09-26 follow-up: [targeted acquisition fixes and real-data dynamics](acquisition_followup/README.md)
records execution-gate and observed-history repairs, corrected elimination probabilities, a LINCS
6 h to 24 h population-transition analysis, and an exploratory two-step SciPlex3 comparison.
The new policies did not earn promotion; the live API smoke ended with a transport failure.

## Evidence labels

Every claim about the repository is labelled:

- **implemented** — present in `src/` and covered by a contract test.
- **partial** — a mechanism exists but does not yet cover the stated design.
- **design** — specified here, not implemented.
- **unverified** — depends on an external asset or service this environment could not reach.

A design file that asserts a capability without one of these labels is a defect in the file.

## Working rule

Research files are updated in the same change as the code they describe. A design that has
been implemented is re-labelled, not left as a proposal; a design that measurement contradicts
is corrected in place with the contradicting measurement recorded, rather than deleted.
