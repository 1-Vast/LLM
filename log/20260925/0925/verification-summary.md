# Verification summary, 2026-09-25

The earlier reports are `research/local_verification/2026-09-25-maestro.md`,
`research/local_verification/2026-09-26-maestro.md`, and the prior local
`outputs/local_verification/latest-findings.md`. This record incorporates the
user-supplied 12-call analysis and a new verification at commit `555f5f7`.

| Finding | Earlier measurement | Current status |
|---|---|---|
| Jev field contract | Three usable Noul, Choice and Score answers; no refusal | Verified against the live API; `criteria`, `noul` and zero-based score parsing are in the repository |
| Generic action-choice stability | 12 calls: `orthogonal_rescue` 7, `proximal_activity` 4, `engagement_shift` 1; agreement 0.409 | Unstable in the generic probe; none of those 12 choices was executable |
| Critic boundary | Five `model_prediction` judgments; deterministic check and `rna_high` selection unchanged | Verdict: `the critic stayed advisory on this case` |
| Live planner | Three runs, zero contract violations, all selected `rna_high`; 2356, 2389 and 2407 tokens over two calls each | Back-prompt recovery remains unmeasured because no run violated the contract |
| Offline driver | A reused output directory once caused 9/11 checks | Upstream fix verified twice in one directory: 12/12 each time |
| Critic comparison | Empty baseline once implied a false moved selection | Upstream fix refused that baseline with `VERDICT unusable` |
| Live topology ablation | Generic probe omitted topology, critic included it | 12/12 `rna_low` in each arm; executable share 1.0 and agreement 1.0 in both arms |
| Full suite | Previous local run: 1181 passed, 53 failed, 1 skipped | Final run: 1184 passed, 51 failed, 0 errors, 1 skipped |

The 51 current failing IDs are all in the no-local-assets baseline. The baseline
collection error `tests.test_learned_response` passes locally. Two prior
log-layout failures cleared after the missing index and dated records were added.
The remaining failures are not claimed fixed. Phases 6 and 7 remain unavailable because
`data/virtual_cell/registry.json` and `data/evaluation/cases/real/` are absent.

The surprising result is that the controlled critic-state ablation gave stable,
executable choices even **without** the topology block. The generic probe and
critic differ in more than topology, so the earlier contrast did not establish
that topology caused the improvement. Also, the real-result-import acceptance
check passed without `data/`, because the fixture supplies that result.

Reproduction: run `research/local_verification/run_offline.py --output
outputs/local_verification/0925-offline` twice, then run
`research/local_verification/topology_ablation.py --repeats 12 --report
outputs/local_verification/topology_ablation-0925.json`. The ablation used 24
paid evaluations. The full suite output is in
`outputs/local_verification/0925-final/report.md` and the machine-readable
arm results are copied to `topology-ablation.json`. No credentials are recorded.
