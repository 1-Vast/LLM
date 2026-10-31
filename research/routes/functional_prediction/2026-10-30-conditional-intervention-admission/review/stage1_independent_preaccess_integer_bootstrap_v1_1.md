# Independent verifier v1.1: pre-access integer-bootstrap correction

2026-10-30 UTC. This numerical clarification was made after the coordinator relayed independent static-review C5, before any outcome access or verifier execution. Overall goal remains ACTIVE / NOT_ACHIEVED.

The original verifier bootstrapped floating per-compound P@20 differences. Although this is mathematically equivalent to call-count arithmetic, summing floating differences can turn an exact-zero numerator into a tiny nonzero value and affect the strict lower-bound-above-zero check. The original verifier and both original freeze notes are preserved byte-identical.

The versioned verifier first computes each compound's integer recovered-call-count difference between the selected chemistry model and frequency. It sums these integers within each scaffold group. Every unchanged seeded bootstrap draw sums sampled integer group differences and divides once by `20 * sampled_compound_count`. The linear percentile interval and strict lower-bound `> 0` rule are unchanged. This correction changes numerical evaluation only; no scientific endpoint, identity, fold, selection rule, resampling RNG/order, schema or gate was changed.

Current verifier: `review/verify_stage1_independent_v1_1.py`.  
SHA256: `7dc11bfb045fcb8b51de64b8761e744f81c2f30645ab3b91cef65658e6be57af`.

Current machine freeze: `review/stage1_independent_preaccess_freeze_v1_1.json`. It preserves all initial metadata hashes and adds the original own source/notes as immutable provenance. Scientific protocol v1.1 still hashes to `f0ac8bdc5e0e219c5ae4b9a8abf8474c9fbceb2c201f80486b24f447a2b2b480`.

Only the verifier's own initial source/notes and the previously permitted metadata were read for this correction. The new source passed syntax-only AST parsing. No root implementation, labels, ranks, root output JSON, source hit rows, CGI/GI/dose values, synthesis or protected outcomes were read. Neither verifier has been executed and no model was fitted. The original arithmetic-only boundaries remain in force.

Current command after the coordinator requests execution:

```powershell
& 'D:/anaconda/envs/maestro/python.exe' 'D:/MAESTRO/research/routes/functional_prediction/2026-10-30-conditional-intervention-admission/review/verify_stage1_independent_v1_1.py' --compare-root
```
