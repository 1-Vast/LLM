# Dual-core engineering repair and exposed-data replay

**The repaired execution path works; an innovation gain is not established.**
Actual molecular/functional queries now update a private virtual-cell model and
the next agent decision sees fresh predictions. A DGM-inspired archive retains
and executes non-winning ancestry. Neither API search arm found a program worth
deploying over its initial procedure. The original scientific STOP is retained.

This is an engineering repair with a complete public-data development/regression
run, not a new confirmatory experiment. All final outcomes had already been
exposed. The virtual cell remains the narrow original width-16 PPODE; this work
does not establish that virtual-cell models or self-improving agents in general
are ineffective.

## What was repaired

| Defect | Executed repair and evidence |
| --- | --- |
| Seed set after initialization | Seed before construction, deterministic torch configuration. Two complete 30-epoch CUDA trainings on 430 development conditions gave bitwise-identical parameters. |
| Candidate could overwrite evaluator or budgets | Parent owns outcomes, payments, updates and score. Fresh restricted child receives public JSON and returns one action. Errors, duplicate/illegal actions and timeouts are invalid, never zero-score evidence. |
| Scores could be paired with a different source/model/task | Source hash, episode digest, initial model/input state and update configuration bind every evaluation. Archive insertion and promotion enforce paired context. |
| Agent queries did not update the world model | Paid observations alone enter `FeedbackBackend`. All 35 updates in the adaptive functional arm and all 35 in the molecular-first arm changed model hashes and unqueried predictions. |
| Only greedy incumbent replacement | Archive retention and deployment promotion are separate. Actual inherited parents were `p0 -> p1 -> p2`; the final child is `p3`. Inferior branches were genuinely used as parents. |
| Repeated deterministic prompts and incomplete evidence | Temperature 0.7; three distinct prompts within each arm; full public prompts, replies, usage and checked evidence hashes saved. The initial prompt is intentionally shared across matched arms. |
| Interrupted runs could repeat spending | Resume reuses checked archive evidence and recorded API replies. Invalid generations are checkpointed; inconsistent checkpoints refuse execution. |

The runner is a restricted Python action interface, not an OS sandbox for
arbitrary repository-editing agents. There is no general filesystem, network or
host-memory containment claim. World-model adaptation resets between episodes;
cross-task persistent world-model evolution is not implemented or demonstrated.

DGM source was inspected at commit
`a565fd2d1dca504ef5104a7cc0f3bdc4ab9b4fd2`, Apache-2.0.
[DGM_REFERENCE.md](DGM_REFERENCE.md) maps actual upstream functions to the repair.
This is a small independently implemented adaptation, not a DGM benchmark replica.

## Complete replay

Training uses the original five development lineages. Program selection uses
six stocks from five other lineages, with stock-weighted selection means. The
regression uses seven old-final lineages. The training allocation yields a
20-drug contested pool, rather than the original final study's 14-drug pool.
The new and original numerical results therefore are not paired performance
comparisons. Only complete-case single-drug conditions are eligible; pair-label
semantics remain unauthenticated. Molecular observations cost a hypothetical
0.5 functional units and functional observations cost 1, with total budget 5.

| Procedure | Mean confirmed positives, seven regression backgrounds |
| --- | ---: |
| Fixed baseline-similarity prior B1 | 3.286 |
| B1 with conventional kernel feedback | 3.429 |
| Frozen PPODE predictions | 2.571 |
| PPODE updated after functional queries | 2.714 |
| One molecular query, then adaptive functional queries | 2.429 |
| Archive-selected inherited agent + updating PPODE | 2.714 |
| Restart-selected agent + updating PPODE | 2.714 |
| Conventional selection: 0.5 current PPODE + 0.5 B1 | 3.714 |

The update-versus-frozen gain is **0.143 hits [0, 0.429]**, one additional hit in
total across seven backgrounds. Updating PPODE is **-0.714 [-1.571, 0.143]** below
kernel updating. Inherited-versus-restart and inherited-versus-initial are zero
by construction: both searches deploy `p0`. Those zeros do not establish that
all possible inherited procedures are equivalent.

In a supplemental descriptive contrast, the conventional blend exceeds B1 by
**0.429 [0.143, 0.714]** and the inherited
procedure by 1.0 hits. That is a useful *development signal for a simple
comparator*, not evidence for agent evolution. The blend includes the world
model; these data do not justify saying that the world model contains no useful
information. Its molecular trajectory contribution, versus ordinary score
combination, has not been isolated.

Intervals are descriptive paired lineage bootstrap intervals on exposed data,
conditional on this fixed drug pool and trained model. They are not independent
confirmation and do not include training-seed or novel-drug variability.
No superiority threshold was retuned on this regression.

Separate transfer checks exclude both reserved support drugs from target
evaluation. Mean Brier improvements were **-0.016465 functional**, **+0.0003105
molecular**, and **-0.065476 combined**; all precision@5 changes were zero.
Thus probabilities can change while useful decision improvement is absent,
and this naive feedback rule can worsen probability accuracy.

## What happened during evolution

All three inherited candidates were retained but not promoted: mean selection
hits were `3.000` for the root, then `2.667`, `2.167`, `2.000`. The first API
response hit its output limit and was invalid JSON. Its slot used the declared
conventional molecular-first fallback (`p1`); the two later API programs really
inherited that fallback. Do not attribute that first program to the API.

Restart proposals always used `p0`; their selection scores were `2.167`,
`2.333`, `2.167`. Each arm had three candidate slots and 24 episode evaluations
including the root. Conventional menu selection also had three candidates and
24 episode evaluations. No failed execution entered proposer evidence as zero.

There were **6 HTTP attempts, 18,043 provider tokens, 5 valid API programs and
1 truncated response**. Inherited/restart tokens were 10,620/7,423. Evaluation
counts and request counts match; token cost, query mix and wall time do not.
No monetary cost is asserted. The archive demonstrates executable ancestry,
not sustained open-ended evolution or a causal inheritance advantage.

External scoring also caught poor generated procedures. One candidate calls
the lexicographically last queried drug the "recent" failure; other rationales
describe maximizing `abs(p - 0.5)` as seeking uncertainty. Some spend on molecular
queries after insufficient budget remains to confirm another functional hit.
These are retained proposer failures, not validated scientific reasoning.

## Validation and integrity

- **89 repair tests pass**, including adversarial actions, real synthetic PPODE
  feedback, source/context mixing, ancestry, persistence, and recovery without
  repeated API calls or evaluations.
- The original **11 tests and 43 verifier checks pass**. All **161 original
  frozen files** remain byte-identical.
- The maintained repository suite reports **1,066 pass / 1 failure**. The sole
  failure is the existing `.build-1024-dgm-revision` directory; it was not altered.
- All seven raw CSVs match the original source receipts. Both expression and
  perturbation caches match their source CSVs element-for-element at cache dtype.
- All 63 regression episodes finish without program/runner errors. The repair
  verifier checks scores, budgets, paid support, prediction refresh, paired
  contrasts, source freeze, API ledger and archive resource counts.
- **The stricter claim that the whole original directory stayed unchanged fails.**
  Concurrent cleanup removed 16 nonfrozen aborted CPU intermediates and revised
  `REPORT.md` / `RESOURCES.json`. Its log documents that cleanup. This repair made
  no writes or deletes in the original folder. See
  [CONCURRENT_CLEANUP_DRIFT.json](CONCURRENT_CLEANUP_DRIFT.json).

`verify.py` deliberately returns **exit 2** after its repair checks pass while
the original full-directory snapshot differs. It does not silently waive that
failure. Its post-run reporting correction is recorded in
[VERIFICATION_AMENDMENT.json](VERIFICATION_AMENDMENT.json), with the earlier
verifier preserved. The original regression freeze and evaluation code were
not rewritten. This package is therefore not an all-green repository/integrity
certificate.

## Interpretation and next boundary

The demonstrated repair is an agent-query -> measured observation -> world-model
update -> new prediction -> next action loop, with real program ancestry and an
external evaluator. What remains unproved is whether this loop improves drug
discovery decisions enough to justify its costs.

Keep the conventional blend as a strong comparator for any subsequent design.
The current bottleneck is model/update quality and useful measurement selection,
not missing archive plumbing. Before spending more on code evolution, require a
development comparison that preserves the same candidate pools, labels,
molecular supervision and budget, and isolates the molecular-state contribution
against direct predictors and simple blending. Further results on these same
exposed backgrounds remain development evidence. Independent confirmation needs
a genuinely new evaluation asset or prospective laboratory measurements.

[AMENDMENT.md](AMENDMENT.md) separately corrects the original report's molecular
denominator, feedback-path explanations, confounded ablation and overstrong
headroom/verification claims. [REPAIR_HISTORY.md](REPAIR_HISTORY.md) records the
execution fixes and recovery. Outputs, model, chosen code, traces and source
freeze are in `RUN/`; [RESOURCES.json](RESOURCES.json) records resource limits.
