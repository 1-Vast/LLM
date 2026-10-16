# Failures and Blockers

- **Agent synergy did not replicate:** matched pilot and GCP transfer did not exceed deterministic baselines; retain the data and negative conclusions.
- **Closed-loop P2 was not confirmed:** MAESTRO_LOOP 23 vs CONV_LOOP 18, p=.18; do not claim a closed-loop advantage.
- **Knowledge gain was mechanism-class confounding:** gene relabelling reproduced the gain, while target/context/provenance routes added none.
- **Prediction-as-evidence:** writing predictions into evidence caused 15 false NO-GOs; decisions must pass measured-evidence admission.
- **Endpoint unit error:** historical test viability was incorrectly divided by 100 as a percentage; fixed to read metadata/fixed units, preserving the excluded run and deviation note.
- **Mechanism truth is missing:** the local 61,413 annotation pairs have no measured positive/negative reference; the benchmark cannot substitute for scientific validation. Status: `ASSET_BLOCKED`.
- **Weak cold-start generalization:** transfer gains depend on declared source/assay/context and must not be generalized to drug discovery overall.
