# Literature survey: agents, world models and virtual cells (2026-10-08)

> **File summary**
> - **Path**: `log/20261008/LITERATURE_SURVEY_20261008.md`
> - **Purpose**: Verified literature base for the protocol-6 reformulation (two-class
>   e-process contrast) and for the framework's decision-mechanism register. Two citation
>   groups are kept apart per the evidence discipline: verified by retrieval on
>   2026-10-08 versus reproduced from prior project registrations.
> - **Core points**: (1) Anytime-valid e-process theory is the load-bearing reference
>   for a statistic the acquisition cannot game; (2) belief-exposure world-model
>   interfaces (BB-WM) support exposing predictive uncertainty to the policy rather
>   than point simulations; (3) selective foresight supports a revocable world
>   channel; (4) recent virtual-cell work keeps improving prediction while
>   strengthening the evaluation-fidelity warnings this project already carries.
> - **Interfaces / data**: consumed by `research/viability_contrast/protocol6.json`
>   and the design register section of `log/20261008/README.md`.
> - **Depends on**: `log/20260928/VIABILITY_CONTRAST_V5.md`,
>   `log/20260928/VIABILITY_CONTRAST_V5B.md`.

## 1. Verified by retrieval (2026-10-08)

### 1.1 Anytime-valid inference (the protocol-6 statistic)

- Ville (1939), *Etude critique de la notion de collectif*: the maximal inequality for
  nonnegative supermartingales; the reason a likelihood-ratio threshold of log(1/alpha)
  controls adaptive-stopping error at alpha.
- Wald (1945), *Sequential tests of statistical hypotheses* (Ann. Math. Stat. 16(2)):
  the SPRT; the two-threshold form (+/- log(1/alpha)) used in protocol 6.
- Ramdas, Grunwald, Vovk, Shafer (2023), *Game-theoretic statistics and safe
  anytime-valid inference*, Statistical Science 38(4):576-601: the canonical synthesis;
  every sequential test is an e-process under some betting strategy; LR processes are
  the simple-null case.
- Howard, Ramdas, McAuliffe, Sekhon (2021), *Time-uniform Chernoff bounds via
  nonnegative supermartingales*, Probability Surveys 18:257-317.
- Clerico (2026), *Sequential testing of conditionally constrained hypotheses*
  (arXiv:2606.06769): complete-class result - every e-process for conditional
  hypotheses is dominated by a predictable product of one-step e-variables; supports
  the stat_world variant's conditional-predictive construction.
- Shafer and Vovk (2019), *Game-Theoretic Foundations for Probability and Finance*.

### 1.2 World-model interfaces for agents

- Kumar, Kumar, Ahuja, Jha (2026), *Towards a Belief-Based World Model for LLM Agents*
  (arXiv:2609.00455): simulation alone is an incomplete interface under partial
  observability; exposing what is KNOWN and UNCERTAIN (a queryable belief) improves LLM
  decisions and is complementary to simulation. Direct support for stat_world exposing
  a per-line predictive mean AND variance to the acquisition, and for the abstention
  semantics.
- Zhang, Zhang, Ng, Deng (2026), *Self-Evolving World Models for LLM Agent Planning*
  (arXiv:2606.30639): selective foresight - filter low-confidence predictions before
  they enter the agent context, since unreliable foresight can degrade decisions.
  Supports the revocable/applicability-bounded world channel (a refused world channel
  is better than a confident wrong one).
- Zuo et al. (2026), *Qwen-AgentWorld: Language World Models for General Agents*
  (arXiv:2606.24597): environment simulation as a decoupled service and as policy
  warm-up; the simulation-before-execution paradigm at foundation scale.
- Zhang et al. (2026), *Internalizing the Future* (arXiv:2606.27483): plan-conditioned
  verbalized rollouts and success estimates; the format-capability gap warning -
  mimicking the FORM of foresight without predictive grounding fails. Directly relevant
  to the Phase-B LLM arm: the LLM's stated confidence is not a calibrated probability.
- Peng et al. (2026), *Reinforcement World Model Learning for LLM-based Agents*
  (arXiv:2602.05842): sim-to-real alignment in embedding space; training-side, noted
  for completeness.

### 1.3 Experiment-design agents

- Roohani et al. (2024), *BioDiscoveryAgent* (arXiv:2405.17631): the mandatory prior
  baseline; closed-loop genetic experiment design, +21 percent over Bayesian
  optimization on hit identification; AI-critic tool; cost reporting conventions used
  in the protocol-6 Phase-B LLM arm.
- Chandra et al. (2026), *Hierarchical Experimentalist Agents* (arXiv:2606.29315):
  training-free in-context self-improvement via active experimentation; reusable skill
  library; current LLMs near 2 percent success unaided on the hardest levels.
- Muller et al. (2026), *La Agente Optima* (arXiv:2609.04564): LLM supervising Bayesian
  optimization campaigns with a persistent state, keeping every decision auditable and
  returning control to the agent only when interpretation is needed; ablation-driven.
  Matches this framework's separation of a decision core from executed campaigns.
- Smith (2026), *The Little Scientist* (arXiv:2608.16951): a Kuhn agent injecting
  paradigm-shifting conjectures at plateaus; a registered idea for escaping local
  acquisition optima, not adopted here.
- Safdar and Saadeldin (2026), *Long-Horizon Autonomous Architecture Research*
  (arXiv:2608.01995): workflow design at least as influential as model capability;
  commit-or-discard rules are isomorphic to greedy hill-climbing. Supports this
  project's protocol-registered stopping over ad-hoc agent judgment.

### 1.4 Virtual cell modelling

- *SCALE* (arXiv:2603.17380v2): conditional-transport virtual-cell foundation model;
  +12.02 percent PDCorr and +10.66 percent DE overlap over STATE on Tahoe-100M under a
  cell-level biologically meaningful protocol; explicitly criticizes
  reconstruction-heavy evaluation - aligned with this project's decision-value gates.

## 2. Reproduced from prior project registrations (not re-verified today)

- Virtual Cell Challenge 2026 (Cell 2026) and Cell-Eval; the 2026 empirical comparison
  (State about +26 percent over cell-mean, linear baseline close behind); VCBench;
  *One-hot news* (synergy models survive zero biological information); *Plausibility Is
  Not Prediction*; VCWorld (ICLR 2026; gains traced to the LLM backbone).
- MAST failure taxonomy (arXiv:2503.13657); agent reliability decaying like p^n with
  step count; AutoCog / auto-psych (arXiv:2606.26448, 2606.26460); AHOIS
  (arXiv:2606.26722).
- BATCHIE (Nat. Commun. 2025, doi:10.1038/s41467-024-55287-7): Bayesian active learning
  for screens; the MI objective family.
- Yan and Zhong (COLT 2026, arXiv:2602.06014): variance-inflated Thompson for valid
  adaptive inference.
- Shim et al. (NeurIPS 2018) and Bingham (medRxiv 2026, EIG-Cost): active feature
  acquisition.
- Kinome inhibition states (PLoS Comput. Biol. 2023, PMC9983880).

## 3. What entered the framework, and where

| Method | Source | Where it entered |
|---|---|---|
| LR e-process, fixed +/- log(1/alpha) thresholds, no calibration | Ville; Wald; Ramdas et al. 2023 | protocol6 statistic_e_process |
| Conditional (predictive) e-variables | Clerico arXiv:2606.06769 | protocol6 variant_stat_world |
| Belief exposure (mean + variance + abstention), not point simulation | arXiv:2609.00455 | stat_world interface; acquisition quadrature |
| Selective foresight / revocable world channel | arXiv:2606.30639 | world channel kept ablatable (marg vs world); abstention honest |
| Label-blind reading-only ceiling | v5b C3 (project) | oracle_reading arm |
| LLM cost/invalid-action accounting, blinded vs named arms | arXiv:2405.17631; Innovation.md | protocol6 conditional_unlock_llm_phase_B |
| Evaluation beyond reconstruction fit | arXiv:2603.17380v2 | gate_v6 is decision-level, not fit-level |
