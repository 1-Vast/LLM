# State evidence metric audit

**Date:** 2026-10-30  
**Scope:** four historical MATLAB v5 MAT payloads formerly under `data/external/state_evidence_20261001/sources/`. No current repository consumer was found outside the source set.

## Structural checks

Each payload was inspected with scipy.io.whosmat and numeric variables were loaded without rewriting source bytes.

| Payload | PhaseMAT | dimEXP | initTP | smplngTM | inputLEVELS | trackedCELLS | removedCELLS |
|---|---|---:|---:|---:|---|---:|---:|
| FIG4_fghij_RefOsc_I.raw | 1×500 struct | 500 | 50 | 2 | 500 finite 0/1 values, mean 0.656 | 1,005 | 13,981 |
| FIG4_pqrst_RefOscG.raw | 1×500 struct | 500 | 50 | 2 | 500 finite 0/1 values, mean 0.760 | 1,045 | 3,612 |
| SFIG8_abcde_RefOsc_II.raw | 1×500 struct | 500 | 50 | 2 | 500 finite 0/1 values, mean 0.656 | 950 | 10,988 |
| SFIG8_fghij_RefOsc_III.raw | 1×500 struct | 500 | 50 | 2 | 500 finite 0/1 values, mean 0.710 | 760 | 13,240 |

cropRECT had four finite coordinates in every file. No NaN or Inf was found in the checked numeric scalar/vector fields. These checks establish file readability, dimensions, binary input encoding, and unit-scale consistency only.

## Formula checks

The retained MATLAB/Python source files define the auditable control path: phase threshold 0.4×2π, nominal period 105 time units, angular frequency 2π/T, smplngTM conversion, a sign decision from sum(sin(Theta−Theta_r)×(Theta<Theta_c)), and a reference ODE with omega_r=2π/105 and gamma=1. The implementation contains no stored independent ground truth, randomized replicate design, or endpoint-to-function validation. Therefore the historical control effect and any biological mechanism remain **unverified**.

## Deletion decision

The four MAT payloads had no current consumers and were not required by the current Agent × virtual-cell routes. They were deleted from the project after full SHA-256 copies were written to `D:\MAESTRO-organization-20261030\state-evidence-recovery\DELETION_MANIFEST.json`. The seven small formula/protocol source files remain in `data/external/state_evidence_20261001/` so metric definitions and historical provenance are recoverable. Recovery files are not scientific validation or a license claim.

