# Static check of the single reserved implementation-failure repair

Date: 2026-10-30. Overall goal: ACTIVE / NOT_ACHIEVED.

Reviewed corrected script SHA-256 `5dcda7fccc7a4b15fa5054261ba019bf00992296912b952b2aca09f2ceab7f4d`, corrected hard launcher SHA-256 `94d1463a4a0e9cbbb80010dcc896857e1fbfaca05c7089327b0a02b340d82411`, current input-freeze SHA-256 `842b3809debced5b1d37ba062b22d6e08f679909e4166e0ca951e246dae4a1ee`, and `implementation_correction.md`.

## Disposition

**PASS for the one predeclared implementation-failure rerun through the corrected hard launcher, writing only to `stage1_corrected`.** The repair implements the original frequency/nearest-five means and lexical tie contract. It makes no scientific setting change. This does not accept the first run's scores, promise a favorable corrected result, authorize a third matrix, or release any held-out outcome. Independent frozen arithmetic verification is still required after the corrected run.

## Exact-count repair

I compared the complete current script and launcher with the preserved original versions. The script differences are confined to the corrected output directory, removal of the unused floating frequency-weight matrix, direct frequency/nearest call sums before division, and correction provenance in the receipt. The launcher differs only in its output directory.

For frequency, `y.sum(axis=0) / len(train)` is broadcast to queries. Although `y` is represented as floating point, its values are exact zeros and ones and at most 231 are summed. Every intermediate integer is exactly representable in this range. There is no multiplication by the inexact reciprocal before accumulation. Thus equal call counts produce identical numerators and the same single division, implementing exact count ties for the stable canonical-gene sort.

For nearest-five, each positive donor weight selects the same previously frozen neighbor indices; the corresponding binary rows are summed before one division by `np.count_nonzero(weight)`. These small integer-valued sums are also exact. The denominator is the actual selected donor count, preserving the existing fewer-than-five fallback. All selected donors have equal positive weights; no outcome-dependent donor choice or reweighting is introduced. Removing clipping for these two means is algebraically harmless because binary counts divided by their source/donor count are already in [0,1]. Ridge's prediction and clipping path is unchanged.

The same corrected `evaluate` branches are used for both aligned and every coherently reassigned null truth. The change is not restricted to the observed baseline, and there is no selection between old and corrected scores.

## Unchanged design and preservation checks

The complete diff leaves the fixed genes, source-only eligibility, fingerprints, source standardization, Tanimoto neighbor selection and compound-ID ties, Ridge fits/alphas/intercepts, scaffold folds, profile reassignment strata, 49 mappings/seeds/RNG order, primary P@20, recall/oracle, integer model selection/null-tail comparison, integer bootstrap, gate and held-out prohibition unchanged. Existing access filtering, hash preflight, checkpoints, failure receipts, 1,800-second hard timeout and no-replay guards remain intact.

All 19 current frozen entries match their files. Comparing old and new input freezes shows the same pinned path set; only `stage1.py` and `run_stage1.py` hashes changed. All pinned scientific input/protocol/descriptor/metadata/source hashes are unchanged. Both corrected Python files passed AST parsing without execution. The corrected output directory was absent at this check.

The preserved original script, launcher and input freeze match the prior reviewed hashes and the saved preservation manifest:

- original script: `1ac2ae94a41b1384179248322a5ef857a408fab2ba0ba02b613cc619fa6e07f7`;
- original launcher: `1348609aae6c6e40e5dded1ed7a24748f59c58e489371b72cb74d93145e2df7b`;
- original input freeze: `de4ae12e8c774322b0636db32c19caa5033f06f092063eec9f5b872c0b43e0b5`.

The corrected paths do not write into the original `stage1` result directory. Original numerical output preservation is reported by the coordinator; this code-only check did not open or independently hash those output arrays. All prior PASS/HOLD records and the missed-tie failure note remain unchanged. The correction freeze occurs after the first authorized development exposure; it is not a new unexposed scientific preregistration or a reset of the experiment budget.

## Evidence boundaries

This is a bounded static repair check. I did not read original or corrected outcome arrays, first-run winning methods/gains, new labels or held-out calls; no real-data model or additional synthetic test ran. No validation code was changed. Public traffic: **0 HTTP attempts / 0 completed response-body bytes / 0 known partial bytes**. No installation, delegation, source-library/index/core edit or external model bridge occurred.

My earlier static PASS missed the within-profile floating tie issue; the preserved record and independent verifier failure remain part of the evidence. This repair PASS does not substitute for the frozen verifier's check of the actual corrected frequency/neighbor ranks, all methods, mappings, metrics, completeness and decisions.

All scientific limits remain: one selected fixed processed-call panel, conditional block exchangeability, source-selected/adaptive regimens, shared controls, unknown preprocessing scope, non-calls rather than demonstrated biological negatives, and limited scaffold transfer. No physical-effect, prospective label-construction, external-biology, practical-benefit, mechanism, agent or novelty claim follows. Even a validated positive development gate can support only a separately specified later protocol. The 63 held-out compound outcomes remain unread and unreleased. Overall goal remains ACTIVE / NOT_ACHIEVED.
