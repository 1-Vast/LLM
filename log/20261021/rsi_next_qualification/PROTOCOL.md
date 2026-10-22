# Bounded qualification before another virtual-cell / RSI campaign

Recorded 2026-10-21 (Asia/Shanghai), before this package's numerical analysis.
User mandate: autonomous multi-agent research; code/tests in research/, all new
exploration, decisions, sources, failures and numerical artifacts in log/.

## Scope and exposure

PTV-1 is already exposed development data, including every old final outcome.
No partition of these data can restore independence. The original scientific STOP
and all old freezes remain unchanged. This is an attribution diagnostic, never
an independent confirmation or a claim of RSI. Do not access PRISM 24Q2, ALMANAC
or other sealed outcomes. Newly discovered source outcomes remain unread until
a separate qualification and evaluation protocol exists.

## Questions in order

G0a: Does the old world-model score add more to B1 than a score from a direct
predictor or the old no-trajectory model, under the SAME training split, available
drug pool, top-five decision and mixing search budget? The positive repair blend
used a different training allocation and a 20-drug pool; its value must not be
paired with the original study's 14-drug-pool value.

Use original study cached selection/final world-model probabilities, not repair
probabilities. Original full=M1, no_traj=M2. Compare B1, original direct logistic
and HGB predictors, M1, M2, and B1 mixtures with each of these four predictors.
The same information and training scopes apply to every direct score. Reproduce
the historical direct feature pipeline (input-only PCA over known baselines),
disclose its transductive preprocessing, and make no independent-evaluation claim.

Mixing weights w in {0, .25, .5, .75, 1} denote weight on the added score.
Select each predictor's w using selection-lineage macro precision@5; average
multiple stocks within lineage first; ties prefer lower w. Also report fixed
equal-weight mixtures without selecting w. All four searches have five slots.
No use of old-final labels for weight selection. Evaluation is conditional on
old trained models, two saved final training seeds, and seven old-final lineages.
The selection models use saved checkpoint epoch 30 for full and no_traj, matching
the original selected/final setting. B1 and direct models use the same records
and available pools as the corresponding cached predictions. Exclusions and
lineage counts are retained. Scores must join 1:1 by stock+drug, labels must agree,
and no drug with a missing label can be treated as a negative.

Primary estimand: difference in macro precision@5, B1+M1 versus the strongest
B1+non-world comparator (M2, logistic, HGB), each selected on the selection data.
Secondary: versus B1; fixed-half mixture contrasts; Brier; AUROC. Paired lineage
bootstrap (10,000 draws, seed 20261021) is descriptive and conditional on models.
Training seeds are reported separately, never counted as extra biological units.
Practical margin is the original 0.09 precision@5, not retuned to these results.

G0a continuation: only a gain >= .09 over the best selected non-world mixture
in BOTH saved seeds and a descriptive lower bound >0 warrants a same-supervision,
matched-capacity non-ODE control on this asset. Otherwise stop further PTV
architecture and program search. A positive G0a STILL cannot attribute an ODE
mechanism: M1/M2 differ in head capacity and molecular supervision. No new model
training is authorized by a numerical tie or a probability-only gain.

G0b (conditional, not assumed run): real measured molecular state must improve
functional decisions beyond a direct predictor and simple mixture, then paid
support measurements must transfer to unqueried drugs in unseen lineages.
Same-drug post-measurement readout is only a diagnostic information test. It is
not cross-drug feedback, a causal mediator, or a world-model contribution.

## Broader advancement contract

Only after G0 and an independently held-out measured endpoint qualify:
world model versus same-supervision direct model; static versus adaptive agent;
ordinary batch retraining and online/continual updating; conventional active
learning; simple mixture; equal-budget conventional procedure search.
Evaluate 2x2 world x procedure contribution and interaction. Procedure inheritance
versus restart uses identical total prior+current evaluations/observations/tokens.
Meta-strategy inheritance is transplanted into a common task agent/model at a
fixed checkpoint. Measure fresh-task improvement per proposal/evaluation/token
and the full improvement-vs-cost curve, with fixed-meta, restarted-meta and random
search controls; include meta-training cost. Reusing a better incumbent is not
evidence that the improvement operator improved. Numerical and biological units,
null margins, multiplicity and a one-shot opening must be frozen first.

## Resource boundary and stop rules

This qualification block: <=45 minutes elapsed; <=4 CPU threads per process;
<=8 GiB main-process RAM target; no GPU or new large training; <=100 MB new
downloads; <=20 primary-source pages per agent; no required DeepSeek call.
API is authorized without a user monetary cap, but call count cannot repair
missing biological information or independent units. Initial API use is zero.
Pause new computation at the boundary, preserve failures and incomplete work;
continue the overarching goal with the next explicit bounded block if warranted.
New model/program search stops if G0 fails or a simple comparator explains it.
Never change the endpoint/margin to rescue a failure.

## Integrity and reproducibility

Snapshot all original-study FREEZE listed bytes and every file in its repair
before analysis; verify afterward. Existing working-tree changes predate this
block and are not ours. Python -B prevents new import bytecode in old studies.
Use requested D:/anaconda/envs/maestro/python.exe (3.11.16). Save exact file hashes,
versions, commands, elapsed/CPU/RSS, all candidate weights and individual lineage
decisions under this log directory. No edits to src/, tests/ or old study data.

Three independent agents: mechanism proposal, skeptical methods/novelty audit,
and primary-source/data qualification. Their records go in agents/ here. The
coordinator decides the continuation from all three and the measured diagnostic.
