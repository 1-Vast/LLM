# Dual-source conditional feedback transfer

This research-only study implements P0 provenance/transfer audits and P1 dual
A/B conditional means with truly crossfitted residual transfer. It preserves
STATE caches, the old pairwise experiment and the full candidate menu.

`PROTOCOL.json` distinguishes the transfer gate from MAP-specific attribution.
The public-state reference uses all45 basal vectors without response labels and
is explicitly transductive. Ridge penalty10 and conservative feedback grids are
registered before effect scoring. Covariance probabilities remain diagnostics;
no calibrated conditional risk or monetary information value is implied.

Run in the maestro environment from the isolated worktree root:

    python -m research.decision_value.pairwise_v3.run --pilot --out outputs/decision_value/pairwise_v3_pilot
    python -m research.decision_value.pairwise_v3.run --out outputs/decision_value/pairwise_v3
    python research/decision_value/pairwise_v3/verify.py --out outputs/decision_value/pairwise_v3
    python -m pytest research/decision_value/pairwise_v3/test_v3.py

Each run uses immutable prepare/commit/evaluate phases (`--phase`). Paid policies
see only one charged A query; B is scored after saved commitment hashes. The
supplementary pre-buy-stop policy skips A when training selects alpha0. Broader
adaptive/LLM acquisition requires the registered transfer gate; production
requires untouched qualified units and functional utility/cost evidence.

## Completed result

The full study and independent verifier both pass arithmetic reconstruction:
387 episodes, 3,870 rows, 43 backgrounds, ten arms. The registered transfer and
MAP-specific gates fail. At the primary eight histories, feedback improves
terminal B over its own mean model by only +0.0000128654, nominal 95% CI
[-0.0000130981,+0.0000388290], Holm p=0.48456. No-update is slightly better;
old/refitted empirical/MAP residual banks select the same terminal sets.
Mean-relative feedback flips are one corrected, zero harmful, with 0.0861%
coverage. One event cannot certify safety.

Stopping before A preserves all matched-arm predictions and selections while
reducing primary A purchases from 129 to 35. Profile cost is 680 versus 774;
no-update costs 645. This verifies avoidance of unused purchases, not beneficial
active acquisition. The producer's formulas and outputs remain frozen. Only
the independent verifier's oracle reduction order was amended after scoring;
see `VERIFICATION_AMENDMENT.json` and the preserved first attempt.

`p0/P0REPORT.md` records separately frozen source and training transfer audits.
`data_availability/SOURCE_RECOVERY_PLAN.json` records 20 actual authenticated
metadata range reads (5,083,146 bytes) and exact future ranges for 250 control
cells (2 MB RNA). RNA extraction is blocked by gene-axis authentication;
no expression or treated outcomes were fetched. This does not block cached replay.

The canonical result is in `log/20261009/PAIRWISE_V3.json` and
`research/EVIDENCE.md`. Local outputs are under
`outputs/decision_value/pairwise_v3/`. The portable bundle and its hash receipt
are under `outputs/decision_value/`; a separate extracted replay reproduces all
21,672 pre-A arrays, 3,870 prediction arrays and phase JSON records exactly.
The extracted independent verifier also passes. This is cached CPU reproduction
in the same Windows maestro environment, not raw pretrained inference or
independent biological confirmation. No old freezes or production modules are
replaced. Producers refuse to overwrite existing outputs: use a fresh output
path for a new replay and pass that path to the independent verifier.

Software checks: 653 default tests, 21 focused old/new research tests, and 11
new tests from the extracted standalone bundle pass. The research tests include
actual model selection and prepare/commit/evaluate with B absent at commitment
and A absent at evaluation.
