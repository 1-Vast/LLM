# Failures and Blockers

- **Agent synergy did not replicate:** matched pilot and GCP transfer did not exceed deterministic baselines; retain the data and negative conclusions.
- **Closed-loop P2 was not confirmed:** MAESTRO_LOOP 23 vs CONV_LOOP 18, p=.18; do not claim a closed-loop advantage.
- **Knowledge gain was mechanism-class confounding:** gene relabelling reproduced the gain, while target/context/provenance routes added none.
- **Prediction-as-evidence:** writing predictions into evidence caused 15 false NO-GOs; decisions must pass measured-evidence admission.
- **Endpoint unit error:** historical test viability was incorrectly divided by 100 as a percentage; fixed to read metadata/fixed units, preserving the excluded run and deviation note.
- **Mechanism truth is missing:** the local 61,413 annotation pairs have no measured positive/negative reference; the benchmark cannot substitute for scientific validation. Status: `ASSET_BLOCKED`.
- **Weak cold-start generalization:** transfer gains depend on declared source/assay/context and must not be generalized to drug discovery overall.
- **Batch-lookahead baseline defect (2026-10-17):** after its first greedy pick the lookahead bridge shrank the covariance but kept the prior hit chances as the baseline, biasing every later candidate low; weighted by measurement rate, the bias chose rarely measured items (29% of Beat AML bridge wells measured). Uniform measurement on PRISM (q about 0.975) hid it during development. The source-verified selector rejected the procedure in all folds. Fixed in `agent.bridge_design` (rule `lookahead`; frozen rule kept as `lookahead_v1`); the fix is post hoc and unconfirmed.
- **Process-report field not swapped (2026-10-17):** `confirm.py` replaced `maestro` hits with the selected procedure's but kept the lookahead's wasted-well count (4.81 vs the correct 2.53). Descriptive only; recorded in the study's `DEVIATIONS.json`.
- **Wrong pre-registered expectation (2026-10-17):** AML-shaped PRISM proxies predicted the agent would decline to bridge and the verdict would be PARTIAL; on real patient samples it bridged and the verdict was CONFIRMED. Proxies built from another domain did not predict which procedure pays.
