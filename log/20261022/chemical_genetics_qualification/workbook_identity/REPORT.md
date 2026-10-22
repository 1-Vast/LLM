# Chemical-genetics workbook structure qualification

2026-10-22. Decision: **OFFICIAL_WORKBOOKS_ACQUIRED; STRUCTURE_QUALIFIED; EXACT_IDENTITY_ROLES_NOT_YET_QUALIFIED.** This report completes the original conservative structure block. It does not amend the previous source report or claim that masked labels/identity fields are absent.

## Acquisition and preservation

Exactly one GET to the preregistered Europe PMC supplementaryFiles endpoint returned HTTP200, application/zip, **7,549,137 bytes**. No redirect, retry, alternate host, model API or FASTQ acquisition. Raw response, request timestamps/status and SHA256 are in `NETWORK.json`; complete central-directory entries are in `ZIP_MANIFEST.json`. Only the two exact whitelisted XLSX members were extracted. Other images/PDFs/workbooks remain unextracted inside the retained original ZIP.

The protocol, frozen acquisition/projector code, tests and old parent report were hashed before the request (`FREEZE.json`). Nine revised synthetic tests passed in maestro. The initial 8-test run is also retained; `PREACQUISITION_REVIEW.md` documents the pre-exposure correction of an overly permissive parenthetical-header rule. Post-read `VERIFICATION.json` confirms every frozen hash, the old report hash and both original workbook hashes unchanged. No workbook rewrite, rendering, import into a recalculating engine, or recalculation occurred.

## Observed structure

| File | Sheet | Declared dimension | Merged ranges | String cells | Numeric cells |
| --- | --- | --- | --- | ---: | ---: |
| MOESM3 | SuppTable1_Chemical_genetics | A1:AO3905 | none | 3,945 | 156,160 |
| MOESM7 | Fig.3bcd | A1:M234 | none | 2,109 | 932 |

These are XML type counts and declared worksheet dimensions, not outcome statistics. Each workbook has one visible sheet. No formulas or other cell types were observed. MOESM3's shape is consistent with the Methods' 3,904 × 40 deletion-strain screen; the initial assumption that Supplementary Table1 was simply a small drug/dose lookup is not established by its actual shape. MOESM7's 234 declared rows do not establish 233 biological units or independent tasks.

## First-30-row string projection and exact candidate locations

`STRUCTURE_AND_LABELS.json` retains every inspected string-cell coordinate and withholding reason. The strict generic-label allowlist admitted no labels. This is **filter-induced non-identification**, not evidence that source identity fields are absent. All unknown strings, including exact drug/gene entities or abbreviations, were conservatively withheld. Numeric cells, numeric strings, formulas/caches and suspected response-category text were not exported.

- MOESM3: `A1:AO1` are all strings; `A2:A30` are strings. Candidate next scopes are `A1` for row-axis label, `B1:AO1` for column-axis identities and `A2:A3905` for row identities, contingent on a separately declared entity-value scope. The body `B2:AO3905` is not requested. No exact gene/drug identity is exposed by this block.
- MOESM7: row1 string positions are `B1:M1`; `E1:F1` were suspected-response text, other row1 strings unknown. Within rows2–30, `C`, `D`, `F`, `I`, `J`, `K` hold unknown strings; `G:H` hold suspected-response text; `L` holds numeric strings. These are exact candidate **positions**, not certified roles. A header-only followup is necessary before selecting identity columns or numeric lineage/day fields. Nothing establishes that every one of those candidate columns is an identity.

No uniqueness, pair counts, lineage/day equality, cross-file joins, feedback-menu size or trajectories were computed from source values. Counts of 70/634 and experimental lineages remain literature/design-exposed Methods information from the previous stage.

## Limits and next step

The raw files contain endpoints. Internal XML parsing for type/coordinate projection is not evidence of an outcome evaluation. The guard cannot prove that no unknown string encodes an endpoint; its conservative withholding also prevents useful schema interpretation. Exact entity values and more flexible literal schema headers therefore require an explicit later scope; the frozen projector is not silently broadened.

The parent has now authorized a separate offline identity followup, including MOESM9 for Fig5 longitudinal data, from the already retained ZIP. That work will have its own protocol and exposure statement; it is not retroactively part of this original frozen block. Source qualification remains distinct from method, world-model, agent or RSI experiments.
