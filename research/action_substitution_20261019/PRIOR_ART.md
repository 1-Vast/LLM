# Prior art and internal novelty: conditional pharmacological action units

2026-10-19. Each external claim below was checked against the primary source (full text, or abstract plus PMC record)
unless marked **unverified**. The question it answers: is "learn when drug A' can substitute for drug A, with partner B,
in context c, and refine the boundary with counterexamples" new? If it is, which parts are?

## External work

| Work | What it does | Overlap with this study | What it does not do |
|---|---|---|---|
| **PHAROS** (Bezney, Ruggeri, Borra, Qi, Buffa, Steinmetz; bioRxiv 10.64898/2026.09.08.749477, posted 2026-09-10) | Frozen STATE/Tahoe perturbation model, chained one drug at a time, beam search toward a target cell state (optimal-transport distance), with an admissibility check (support, separability). | **Closest.** Hypothesis mode replaces an out-of-vocabulary drug with "mechanism-matched alternatives" (same annotated MoA) and reports the best-performing proxy per pair, chosen post hoc by final OT distance. The authors note that compounds sharing an annotated mechanism "can induce distinct transcriptional responses", and mechanism-matched recovery was "less consistent" (82-100% against random). | Treats substitutability as a fixed annotation lookup. It never tests whether a substitution holds, never learns where it fails, never refines classes from failures, and never uses efficacy or interaction endpoints (transcriptional state only). Proxy choice is post hoc, not predicted. |
| **Yang et al. 2020**, target functional similarity (npj Syst Biol Appl; PMC7265486) | Learns target-pair functional similarity from single-drug response plus basal expression; synergy is enriched at very high or very low similarity. | Functional (Level F) similarity of targets learned from response data, and a functional-neighbour baseline. | Similarity between targets, not conditional substitutability of drugs given a partner and context. Combination r of 0.27-0.5. |
| **TranSynergy** (Liu & Xie, PLoS Comput Biol 2021, e1008653) | Transformer over drug-target profiles diffused on a gene network plus cell-line dependency, to predict synergy. | A mechanism-level (Level M) representation that could transfer to unseen drugs that have target profiles. | No substitution relation; standard regression benchmark (O'Neil); target profiles are fixed inputs, never refined. |
| **Klaeger et al. 2017** (Science 358:eaan4368) | Kinobeads binding of 243 clinical kinase inhibitors. | A measured target-affinity space, the strongest available Level M evidence for kinase families such as EGFR, mTOR, Aurora and CDK4/6. | No response data. Not downloaded here (needs permission). |
| **BATCHIE** (Tosh … Tansey, Nat Commun 16, 2025) | Bayesian active learning for combination screens (about 4% of 1.4M experiments; PARP+TOP1 in Ewing sarcoma). | Experimental design over combination space, a strong design baseline. | Drug identities are embedded but never related as substitutes; no counterexample refinement. |
| **UniPert-G2CP** (Cell, 2026-07-24) | Genetic perturbation pretraining, fine-tuned for chemical perturbations. | Maps a drug to its targets' genetic-perturbation effects, the Level M route to unseen implementations. | Single-agent transcriptional prediction; no combinations, no substitution boundaries. |
| **ProteinTalks / PTV-1** (Nature, 2026-09-09) | Neural-ODE proteomic virtual cell. | Mechanistic dynamic model. | Not a substitution or combination-boundary method. |
| **CellForge** (arXiv 2508.02276 v3, 2026-10-14) | Multi-agent system that designs virtual-cell model architectures. | Agent plus virtual cell. | Builds models; does not test equivalence or design discriminating experiments. |
| **Causal abstraction** (Geiger et al., JMLR 26(83), 2025) | Formal criteria for when a high-level variable faithfully abstracts low-level mechanisms (interchange interventions). | **Conceptual template.** An "action unit" is a candidate abstraction, and a swap A -> A' is an interchange intervention. Exact abstraction corresponds to Delta_swap = 0 for all (B, c). | Not applied to pharmacology; assumes interventions are cheap and noise-free. |
| **CEGAR for robot planning** (Luckeneder, Hoch, Kaindl, arXiv 2505.22982); **PoE-World** (Piriyakulkij … Ellis, arXiv 2505.10819) | Counterexample-guided abstraction refinement; compositional world models as products of program experts. | Template for "refine the abstraction when a counterexample breaks it". | Deterministic domains, where a single counterexample is decisive. In a noisy assay, one discordant well is not a counterexample. That is the methodological problem here. |
| MAP, CoPISA, CellBox | **Unverified**: MAP's Nature page redirected to sign-in; CoPISA and CellBox were not fetched. | CellBox (mechanistic ODE on perturbations) is a potential baseline. | Not assessed. |

### The external gap, stated narrowly

No verified prior work does any of the following:

1. Treats "A' substitutes for A" as a **testable, conditional relation** on a measured efficacy or interaction endpoint,
   with equivalence margins.
2. **Estimates where it fails**, across partners and contexts.
3. **Predicts the failure for an implementation never measured in combination.**
4. Uses failures to **revise the grouping**.

PHAROS uses mechanism matching as a substitution heuristic and reports its unreliability, but leaves it untested. The gap
is real but narrow. A positive result needs to beat the obvious baselines (same target, potency matching, single-agent
similarity), because those are what a reviewer would propose first.

## Internal history (MAESTRO, from studies already run)

| Study | Relevant finding | Implication here |
|---|---|---|
| Certified discovery (2026-10-03, NCI-ALMANAC) | Combination prediction binds a decision (+2.58 hits/line). | Combination outcomes can carry decision value. |
| Feedback validation / reproducible allocation / confirmation campaign (2026-10-03 to 10-04, Jaaks) | Feedback gave no validated gain. Two-orientation history +13.4%. Verify-hits +17.7% but costs 5 rounds. | Jaaks was opened then, so **this study is development evidence only**. Orientation (anchor vs library) matters, and history in the other orientation is the strongest known signal, so it must be a baseline. |
| Mono pretraining (2026-10-05) | Single-agent pretraining gave no combination gain. About 19% of the within-line residual reproduces across orientations. | Reproducible conditional structure is small. Expect a low ceiling. |
| Knowledge reality / orbit contrast (2026-10-13) | Knowledge-graph and "identity" gains were mechanism-class membership; gene relabelling reproduced them. | A substitution model must beat class membership itself (the same-target and same-pathway baselines). |
| Program revision / seed attribution (2026-10-17/18) | A seed library of hand-written programs looked useful (+0.21/+0.45). Revision, stepwise and LLM edits added nothing, and with the contract repaired the seed gain was not confirmed. | **"Counterexample refinement" of rules was effectively tried and gave 0.** A new refinement claim must show what differs: here the refined object is a substitution relation tested against equivalence margins, not a gating program. It must also beat no-refinement on held-out data. |
| Mechanism falsification (2026-10-10, 10-14) | Conformal MoA falsification was valid on average but failed on active drugs. No measured mechanism truth (ASSET_BLOCKED). | Level M claims cannot be validated with local assets. Keep this study at Level F (functional substitutability on measured endpoints). |
| All LLM arms (blocks N-Q, 2026-10-11 to 10-18) | Null or harmful. | The agent arm needs a deterministic counterpart and no presumption of value. |

### The internal gap

MAESTRO has never measured whether **drug-swap contrasts reproduce across independent seeding events**, or whether
their partner x context structure exceeds noise. Every earlier combination study modelled outcomes, not equivalences.
That is the first question (PLAN_P1.md), and it decides whether anything downstream is worth building.
