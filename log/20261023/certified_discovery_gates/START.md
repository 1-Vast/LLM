# Certified-discovery Gate 0 / Gate 1: start record

2026-10-23. **The owner's request:** run Gate 0 (headroom) and Gate 1 (validity) on exposed Jaaks 2022 and the exposed AZ2024 MASTERs, as specified in `log/20261023/forward_perspective/PERSPECTIVE.md` sections 5.2–5.3. Pre-register first, and touch no reserve.

## Locations

- **Code:** `research/certified_discovery_gates_20261023/`. The folder is untracked, so it is not registered in `research/STUDIES.json`. Registering an untracked folder would break `tests/test_repository_shape.py`, which compares the registry with git-tracked folders.
- **Evidence:** this directory.
- **AZ archive location.** Between the census and the protocol, a concurrent maintenance session moved the AZ archive.
  - From: `log/20261022/intervention_program_renewal/az_design/`
  - To: `data/external/research_sources/20261022/intervention_program_renewal/az_design/`
  - Its SHA256 is unchanged (`e8cb50f6…3259`), so `CENSUS.json` describes the same bytes. `census.py` now points at the new path.

## What had been seen before this protocol

- **Jaaks 2022 is fully exposed.** Earlier MAESTRO studies used it:
  - certified-discovery feedback test, 10-03;
  - reproducible allocation (verify-hits +17.7% over 5 rounds), 10-04;
  - confirmation campaign (stopping saves 20%; two-orientation history +13.4%), 10-04;
  - biological residual gate, 10-19;
  - action substitution, 10-19.

  This session has not looked at validation-screen synergy values.
- **AZ2024 GDSC_007, exposed cells.** The 2026-10-22 paid-reference study (`log/20261022/az_paid_reference_gate/`) converted inhibition values for 320 exposed MASTER cells: 160 train, 64 validation and 96 test. Its policy-level MAE and utility numbers have been read in this session. This session has not looked at Bliss_excess distributions.
- **Metadata census.** `CENSUS.json` was produced by `census.py` before this protocol was written. It reads identity and layout fields only and converts no response field. It established the structure below.

## Structure found by the census

**AZ (exposed cells only).**
- 602,357 reserve rows were discarded by MASTER_CELL_ID before any field was used.
- 9,030 matrices: 6,814 are 7x7 and 2,216 are 7x5 or 5x7.
- 7,864 (cell, pair) units.
- Plates per unit: 7,478 units on 1 plate, 281 on 2, 55 on 3, and 50 control combinations on 14–17 plates.
- No unit has two matrices on the same plate.
- The file holds combination wells only: there are no negative-control wells.

**Jaaks.**
- Original screen: 3,106 plates and 215,973 (line, anchor, anchor concentration, library) units, of which 184,488 sit on a single plate.
- Validation screen: 454 plates and 9,719 units, with no barcode shared with the original screen.
- 9,152 units are in both screens with at least 2 validation plates; 3,127 of them have at least 3.

**Jaaks raw wells (original screen only).**
- Each plate has exactly 114 NC-1 negative-control wells.
- Library-alone wells: 4 replicates per dose. Anchor-alone wells: 5 replicates.
- Raw wells for the validation screen are not on disk.
