# Plan

Scope of this assignment: G0 (unit qualification) and G1 (identifiability and hidden-outcome logic).
G2-G5 are specified in PROTOCOL.md and not executed.

| step | artefact | status |
|---|---|---|
| repository audit | HEAD 59c1c7bd, clean tree, 28 registered studies, stop decisions preserved | done |
| source verification | `records.py` (S1 PMC7610535, S2 PMC12833858, XML digests) | done |
| unit manifest, eligibility, dependence, missing evidence, splits | `build_g0.py` -> `evidence/` | done |
| isolation and replay | `isolation.py`, `g1_policy.py`, `run_g1.py` | done |
| tests A-H | `tests/test_g0_g1.py` | done |
| gate decisions and report | `results/`, `REPORT.md`, `CLAIMS.json` | done |
| verification at four levels | `verify.py` (`--online` re-checks source digests) | done |

Not built on purpose: `models.py`, `policy.py` (numerical), full replay infrastructure, any Agent service,
any new knowledge store. Reusable existing infrastructure noted for later gates only:
`maestro.evidence_registry` (receipts and independence groups), `maestro.information_tier`
(visibility tiers), `maestro.strict_decision_review` (required measured support), `maestro.claim_audit`
(claim-to-run binding), `maestro.evaluation_contract` (settlement and well accounting). None is imported
here so the study stays self-contained; no incompatibility with them was found.
