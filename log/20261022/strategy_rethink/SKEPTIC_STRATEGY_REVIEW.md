# Independent strategy review: do not manufacture a new core

2026-10-22. Read-only reasoning review; no assay outcomes were opened, no fitting/API call was performed, and this document is a proposal rather than a frozen or executed experiment. Read `research/REPORT.md`, current CAF `DECISION.md`/`DEBATE_DISPOSITION.md`/`CONTINUATION_WORK.md`, `research/EVIDENCE.md`, and the RKT README/loading/pooling source. All historical STOPs remain intact. TG later14/AZ413 reserve were not accessed.

## Judgment

I cannot substantiate a new scientific update rule from the available evidence. The reviewed pool variants do not supply one. Naming a test memory, a mutation prior, a low-rank correction, a transport residual or a learned acquisition rule would not fix this; each has an ordinary comparator that implements its operative content.

The source-specific CAF STOP is justified. The research strategy nevertheless risks an avoidable circular requirement: require an original, useful world-model operator before allowing an improver experiment, while requiring later-task improver gains to justify studying that operator. A bounded study of the improver can hold a previously supported static world fixed. It need not first establish another world-model gain. This is not permission to count a conventional learner as new or to reopen stopped configurations.

Likewise, a single useful experiment need not establish all five programme claims. A C4-only experiment is valid if it is reported as such; a positive result is not a drug-discovery or joint-world/agent result. The strongest evidence presently available is still that feedback and fixed transfer can help while additional planning often does not.

## One concrete alternative: C4 opportunity experiment on retained RKT prediction updating

Use the retained, supported molecular-transfer component rather than a stopped BeatAML/PRISM/O'Neil/STACK/CAF configuration. Application is **improving cross-cell-line transcriptional prediction after profiling a compound**, not viability discovery. This is an exposed-data development experiment, conditional on seven existing lines, and cannot establish population generalization or independent biological confirmation.

Actual local inputs already exist:

- `data/external/lincs_l1000_gse92742/derived/blockq_phase1.npz`, loaded by RKT `dev_common.py`, contains phase1 compound/line response and vehicle arrays.
- `research/knowledge_transfer_20261012/cache/dev_routes.npz` is 395,824,740 bytes and contains truth, compound, line, fold, route availability/support/predictions, regime and activity fields used in the archived nested-fit implementation.
- `research/knowledge_transfer_20261012/cache/dev_generic.npy` and `cache/dev_pool.npz` are also present.
- Do **not** import legacy modules with writers/cache creation during the new trial. Read these artifacts in an isolated script, verify their schema, and write only under the new phase. Their historical fitted routes can be treated as a fixed exposed background; they cannot be claimed fully cross-fitted for a newly invented partition.

Before performance work, inspect only identifiers/schema and check that source/probe/evaluation compound groups can be kept disjoint within each outer split. Reuse the recorded five compound folds for outer assessment rather than inventing seven independent line tasks. The line groups and outer folds remain dependent; no five-fold binomial significance or pseudo-replication claim.

### What is changed and measured

Keep route vectors and the generic direction fixed. A solver program is a *route-certificate update procedure*, not an experimental planner: given a small labeled calibration set, it outputs route weights and specific-response shrinkage for unmeasured compounds. Initial solver S0 is the same ordinary ridge-based calibration for every improver arm. Define a tiny, explicit, finite grammar of **ordinary** edits (for example intercept correction; per-route rescaling; one line-by-route interaction; route disagreement as one extra calibration feature). Give ridge/refit all features present in the grammar in a full-dictionary baseline. These edits are not claimed novel.

Create deterministic compound-disjoint calibration episodes from phase1. Each episode has 16 calibration compounds, 16 development-score compounds and a disjoint 32-compound evaluation slice, selecting by identifiers before reading numerical results. Read all their existing measured expression responses; do not invent assay outcomes. A program evaluation consists of actually fitting the candidate update on its 16 calibration compounds and returning mean centered cosine on the 16 development compounds. Final score is centered cosine on its never-returned 32-compound slice, averaged by compound, including all eligible queried cells. Normalize using the training slice only. The task is prediction, so no fabricated assay-cost or hit-discovery utility.

The improver's action is to nominate an executable grammar edit after seeing the same current program, program scores and calibration descriptors. It gets exactly four candidate evaluations and one deployment choice. It may retain S0. Log ordered proposals, duplicate nominations, fits and CPU. This creates new executed fit/feedback trajectories; it is not a reread of archived policy scores.

Old and new checkpoints belong to the SAME proposal-distribution class over grammar edits. The old checkpoint is its fixed initial distribution. On source episodes, the new checkpoint updates that distribution from proposal outcomes; freeze it before later outer-fold episodes. Both begin every later episode with identical S0 and identical calibration/development data, and receive four evaluations. The primary C4 contrast is terminal evaluation score(new checkpoint) minus terminal score(old checkpoint). This is a finite learning-to-improve question, not arbitrary recursive capability growth.

Mandatory same-information, four-evaluation comparators: random search without replacement; fixed cyclic enumeration; a conventional contextual bandit/proposal model trained on the exact same source edit outcomes; a fixed best source edit; a full-dictionary refit; and an oracle over the finite grammar reported only as an upper bound. Include checkpoint restart and source-history permutation. Source training cost and later cost must both be reported; old checkpoints get access to the same source records at inference when testing the extra value of the learned representation versus history retrieval. Refitting S0 on the same calibration data is mandatory, because fitting its coefficients already exploits feedback.

This is intentionally a **known-method opportunity diagnostic**. It asks whether any learned search distribution helps over a very cheap conventional search at a fixed starting solver. If the contextual bandit matches the new checkpoint, report ordinary meta-learning, not new RSI. If four evaluations exhaust the useful grammar, stop: no proposal-improver opportunity exists in this arena. Do not expand the grammar after observing that result.

### Cheapest scope and stop

Register the grammar, proposal learner, deterministic split, budget and scoring before outcomes. Limit the initial computation to one source/development partition and one later partition; this is a screen, not confirmation. Execute all comparator trajectories. Stop this arena if the finite-grammar oracle has no positive mean score difference from S0, if old/new checkpoint proposals become identical, or if the learned checkpoint has no positive terminal difference against either old or strongest conventional comparator. A positive difference only licenses a second predeclared partition, not a core promotion. Report exact paired differences and uncertainty sensitivity; with one later partition do not claim significance, useful application value or general RSI.

The numerical sample sizes above are a proposed computational cap, not a power calculation. They may be reduced **before** response evaluation if schema coverage makes them infeasible. No arbitrary 10% world-gain threshold is needed to run this small programme-level screen; an application-usefulness threshold would be necessary for eventual drug-discovery promotion.

## Support, strongest objection and unresolved issue

Support: RKT has a retained molecular prediction signal, accessible actual route/response arrays and a clear intervention (replacing an update procedure) with real held-out measured responses. Holding it fixed separates improver capability from another unsupported biological model. The proposal requires only hundreds of small fits.

Strongest objection: the proposed learned proposal distribution **is ordinary meta-learning / algorithm selection**, and a finite grammar is likely exhausted by ordinary enumeration. I agree. That is why it is a diagnostic of whether the current research strategy has room for a C4 subproblem, not a candidate innovation. Passing C4 against old alone is not enough to promote it. If the project requires a new core before even this bounded diagnostic, I have no evidence-based experiment to recommend; I do not recommend fabricating novelty to satisfy that gate.

Unresolved: phase1 route precomputation may contain indirect dependence across the proposed task partition. Source inspection must distinguish an explicitly conditional exposed-background experiment from genuinely new-compound transfer; recomputation would be required for the latter and is outside this cheapest proposal. This cannot be fixed by simply hashing a new split. Also, transcript prediction is not a measured drug-discovery functional endpoint. A positive screen would still leave that transfer unestablished.

Do not claim: new biological mechanism; new world model; strong direct-predictor superiority; prospective drug discovery; agent planning advantage; inheritance beyond the checkpoint; joint effect; self-modifying strategy beyond a fixed learner; or full RSI. No such finding exists in this review.
