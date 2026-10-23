# Response-free protocol metadata clarification

After the initial method seal, source read PROTOCOL_METADATA.json, which contains dispensing identities/concentrations/locations but no cell-count responses. Root separately reports 228 unique non-DMSO mapped wells,19 anonymous labels,6 concentrations and two row regions, without conflicting non-DMSO well assignments. This review does not inspect numeric outcome data.

All19 labels can remain anonymous dose-curve identifiers for a within-line forecasting diagnostic. The paper's18 HDAC inhibitor description is not a license to infer that Drug00 is a control or to delete one label. Unknown chemical identity limits mechanism/HDAC-family interpretations; it need not prevent predicting that fixed anonymous curve's future measurements.

“DMSO normalization” dispensing records include co-dispenses into drug wells and records for vehicle-only wells. Their202 rows are not202 independently measured untreated controls. Removing DMSO **metadata rows** while mapping each physical well to its unique non-DMSO label is legitimate for the anonymous-drug task; it does not mean the entire physical well or its drug exposure should be deleted. Unmapped wells can be recorded separately, without silently assuming their role as authenticated controls for normalization.

The 19*6*2 layout and count-header C–H versus I–N regions are consistent with different cell-line regions rather than two biological replicates of the same line. Do not treat two matching dose/label positions in distinct line regions as within-line replicate wells. Until metadata proves otherwise, use actual file/line/well identities and do not invent a replicate count; one well per line/label/dose is possible. Shared vessel names and a protocol Plate27 label do not prove independent experimental plates or batches.

These metadata issues constrain biological inference but do not veto a frozen anonymous within-line72→120h forecasting diagnostic. They require no chemical-identity search, new GET or outcome-dependent exclusion. The original independent review and seal remain unchanged.
