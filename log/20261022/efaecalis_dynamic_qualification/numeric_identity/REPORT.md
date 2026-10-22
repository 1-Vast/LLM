# Day / population / dose identity census

2026-10-22. **IDENTITY_DESIGN_CENSUS_COMPLETE.** Only275 preregistered finite numeric design/identity cells were decoded:80 Fig1B dates and195 Fig4B replicate/day/concentration cells. All response values remained outside the allowlist.

- Fig1B:80 unique `(selection drug,lineage,day)` keys, complete five-drug×four-lineage×days{2,4,6,8} product.
- Fig4B seven even-day top panels:each contains IDs1–20, unique and in identical order across days2/4/6/8/10/12/14. Embedded D34:W34 matches those IDs exactly.
- Embedded C35:C48 day metadata is1–14. AUC-summary D31:R31 day metadata is0–14; no AUC summary contents or individual AUC trajectories were decoded.
- C4:H4 DOX challenge-design doses are0,0.05,0.1,0.2,0.4,0.8. Primary caption independently identifies nonzero0.05–0.8 µg/mL. These are assay design/prior-feedback-exposed, not CRO evolution-dose histories.
- Nine synthetic tests passed;12 frozen inputs remained unchanged. No HTTP/API call, response arrays, workbook editing, rendering or recalculation. `CENSUS.json` preserves exact allowlist/accessed metadata, source hash and comparisons.

Date/population/dose identities can be sealed, but **Relative IC50 normalization/formula/units and actual finite response validity remain unqualified**. Numeric type/value-node presence alone cannot prove that a measurement is finite or nonmissing. Prior240 nonfinite strings in S3 were exposed by the separate string projection and remain explicitly documented; this census does not undo that failure. Main single-clone and independent twenty-population challenge designs remain distinct. No method, performance, independence inflation, inheritance or RSI conclusion is made. Full interpretation and provenance gaps are in `../redirect_followup/REPORT.md`.
