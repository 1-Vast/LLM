# Frozen metadata projection scope

2026-10-31, before metadata values beyond headers. This is design qualification, not a numerical model protocol.

ProteinTalks: TableS2 A_Metadata columns A-L are sample/condition/time/dose/instrument/replicate metadata. TableS8 A_metadata projects A-F and H, excluding G Efficacy. TableS1 C_Efficacy and TableS7 B project only A/B identities, excluding their functional labels. No protein-matrix values, model tables, drug efficacy values or selected validation effect values are interpreted. Dose numbers are metadata; missing dose units remain unknown. Declared sample types do not alone authenticate longitudinal cultures or independent errors. Joins initially use exact stored identity strings; no inferred biological identity from convenient matches.

DNA-repair: data1 raw_data and calculated_relative_data project A-D only (compound ID/name/concentration/solvent), excluding all read counts, response fractions and survival. Data3 Raw_data and Relative_data project A-E only (plate/ID/name/solvent/dose); Controls projects A/B identity/solvent only. Header names repl1/repl2 are not certified preparation identities. No new cross-locus/background inference is made from this schema. Source-owned aggregate effects discussed in the primary article are exposed, while workbook response values remain uninspected.

Return design counts, exact key overlaps, declared repeat labels and missing required fields. Such counts do not admit a learning mechanism or establish drug benefit. Any response analysis still needs a concrete scientific claim, complete numerical freeze and independent review.
