# Independent census recount and edge-cover review

2026-10-22. Independently read **only** `az_design/CENSUS.json`, `DESIGN_MATRICES.jsonl`, root's census/edge code and protocols, the edge result/test manifests, and the previously retained primary XML for its exact crop description. This auditor did **not** open/read/hash the source ZIP, inspect a CSV data row, read/convert a target value, fit a model, issue GET or make an API request during this review. The projected JSONL contains only the frozen design fields and derived counts.

Audit code: `research/intervention_program_renewal_20261022/data_census_audit.py`; machine output: `CENSUS_REVIEW.json`; full run: `CENSUS_REVIEW_RUN.txt`. It imports neither root's summary function nor a ZIP reader, and independently recomputes from projected records. The projection SHA256 matches `fd776ee030f5d39f94fc18c44a577fe0e4ad1c18c65cc2ba76e53cd4502ec8f4`; source census code/projection-protocol hashes match their recorded bindings. Every projected record/metadata/dose field matches its allowed schema.

## Recomputed findings

| Quantity | Independently reproduced |
|---|---:|
| Released projected well rows |3,915,245|
| Unique `(member,PROJECT_ID,BARCODE,cmatrix)`keys |84,055|
| MASTERcell models |755|
| `(MASTER,CELL_ID)`stock expansions |1,175|
| Distinct source drugIDs |46|
| Unordered source-IDpairs |109|
| Unique `(MASTER,pair)`units |68,816|
| Within-matrix identity conflicts |0|
| Repeatedpositions / dose coordinates |0 /0|
| Nonrectangular dose supports |0|
| Top64coverage-selected pairs' commonMASTERmodels |705|

The 705-model intersection is a **descriptive metadata selection**, not a frozen experimental panel, a common single-stock rectangle or 705 independent research runs. Multiple stocks/plates of the same MASTER remain related. The 46 source IDs are not 46 authenticated chemical entities; without the drug dictionary they must not be silently merged into the paper's 37 compounds or interpreted as target families.

| Released surface | Matrices |
|---|---:|
|7×7|70,920|
|5×7|2,703|
|7×5|8,476|
|5×5|1,956|

The weighted rows are exactly `70920×49+11179×35+1956×25=3915245`. Matrix positions and dose-pair multiplicities agree with row counts. Short-axis patterns are metadata findings: all 11,179 rectangular 35-well surfaces have a five-point axis for **source drug ID 2436**, tagged D3–D7; the other axis retains seven points. All 1,956 25-well surfaces are in Sandpiper, with five-point D1–D5 axes involving source IDs 1705, 1735, 2093 and 2095. No drug-name mapping is inferred from those numbers.

| Source | Models | Matrices | Pair–MASTERunits | Shape summary |
|---|---:|---:|---:|---|
|GDSC007|733|22,239|18,022|16,817×49;5,422×35|
|GDSC008|736|24,941|20,567|22,277×49;2,664×35|
|GDSC009|737|22,870|19,208|21,110×49;1,760×35|
|GDSC010|376|12,049|10,139|10,716×49;1,333×35|
|Sandpiper1|737|1,956|1,474|1,956×25|

Within each source-scoped matrix key, the recorded cell/drug/layout metadata is consistent. Across each MASTER, this audit also found no conflicting model names, COSMIC IDs, tissue or cancer-type labels. This does not authenticate all biological synonyms or prove new-source independence.

The source-wise pair–MASTER counts sum to 69,410 but their union is 68,816: **594 net cross-source duplicate memberships**. The 84,055 matrix keys include 15,239 additional instances beyond unique pair–MASTER units. These are multiplicities, not new independent tasks; do not call all of them technical repeats without authentic occasion/run relationships.

## Clarification of my earlier5×5statement

My frozen `INDEPENDENT.md` said AZD1775-containing matrices were reduced to 5×5. That followed the primary narrative literally, but was **too broad as a statement about the released raw geometry**. I do not rewrite the original independent draft. The retained primary paragraph P55 says:

> During the course of screening it was decided that the top two highest concentrations for the wee1 inhibitor AZD1775 were too high to give biologically-relevant results, and so for these combinations the 7 x 7 matrix was cut down to 5 x 5, removing the two highest doses of both drugs for AZD1775-containing combinations only.

The actual released design contains 5×7/7×5 surfaces and separate Sandpiper 5×5 surfaces as above. The narrative may describe an analysis-specific crop or differ from the deposited well geometry; this metadata cannot resolve that editorial/source-history question. In particular, do **not** assert that all 35-well surfaces or Sandpiper 25-well surfaces are AZD1775 without an authenticated ID dictionary. The executable menu must use the actual deposited coordinates, not the universal 5×5 description. Do not reconstruct removed high-dose outcomes.

The same issue affects descriptions in my earlier `CROSS.md`/census-plan shorthand; this clarification supersedes their raw-geometry interpretation while preserving those records of what was known when written.

## What happened to the3246coverage gap?

The independently derived released-design union is **exactly 68,816**, matching the paper. This resolves whether the public well release can reproduce the reported pair–model count under its actual source ID keys. The nominal arithmetic `82×755+27×376=72062` still exceeds this union by 3246; the projected metadata does not identify why every nominal slot was absent. There is no QC flag or target-usability inspection in this gate. Do not retroactively label the 3246 as QC failures, censoring, biology or missing outcomes. Counts of deposited design rows and actual usable numeric targets remain different qualifications.

## Endpoint-dose cover: corrected criterion and algorithm review

I accept root's correction to my earlier triangle shorthand. An AC/BC triangle is a sufficient example, **not a necessary condition**. Paid AC and BD bundles with different partners can also cover the A/B reference axes of an unpurchased AB target. Lack of triangles cannot stop the pilot. The necessary practical question is whether legal non-AB paid edges cover both endpoints' dose coordinates at the specified information/cost scope; the two-bundle gate is one sufficient restricted design, not all possible multi-bundle designs.

Read `AZ_EDGE_COVER_PROTOCOL.md`, `az_edge_cover.py`, `test_az_edge_cover.py`, `EDGE_COVER.json` and `EDGE_TEST.json`. Independent code/protocol hash checks match the recorded edge output. The retained test manifest reports 4/4 pass for nontriangle acceptance, missing-dose rejection, wrong-stock rejection and AB-repeat exclusion. I did not repeat the full edge scan or present its counts as an independently rerun result.

The algorithm implements the stated scope correctly:

- Groups are `(member,PROJECT_ID,MASTER_CELL_ID,CELL_ID)` and, in the stricter version, additionally `BARCODE`.
- Target support uses actual finite nonnegative **Decimal µM** coordinates, rather than dose tags alone, a tolerance, imputation or an inferred common grid.
- For each endpoint, a witness must cover its **entire target axis**. All matrices of the same unordered source-ID AB pair, including repeats, are excluded from both witnesses. A different neighbor for A and B is allowed.
- Lexically first compatible witness selection is deterministic and metadata-only. A single witness cannot secretly supply both axes: a two-drug matrix containing both A and B would be the excluded AB pair.
- A missing full-axis witness at this two-bundle restriction does not prove that several partial curves could not cover the axis at a larger budget. No such rescue is silently performed here.

Reported scope-qualified results:

| Scope | Eligible matrices | MASTERmodels | Source-IDpairs | Pair–MASTERunits |
|---|---:|---:|---:|---:|
|Sameplate|50,687|749|64|41,889|
|Samestock acrossplates|69,306|749|89|57,333|

Sandpiper has zero eligible matrices under both scopes. This stops the **exact two-other-bundle** design there, not every legitimate use of its response data. Same-plate counts establish structural opportunities without assuming cross-plate reference transport; even the same-plate scope does not certify that fitted monotherapy values originate solely from that exact plate. Across-plate counts remain conditional on a later reference-transport justification. The 749 models and 41,889/57,333 pair–model units are not independent later experiments or a selected final task partition.

These results qualify a dose-exact **source ID graph**, not chemical aliases, numerical response availability, fitted monotherapy provenance, effect-space overlap/injectivity, replicate measurement reliability, a new mechanism or RSI. The unpurchased AB rows' attached mono_y/yhat remain unavailable; only paid witness references can form inputs in a later oracle. Every baseline must receive the same purchased information and bundle costs. Exact drug identity and exposed Jaaks overlap still need metadata qualification before an independent biological claim.

## Decision

There is **no substantive unresolved disagreement** with root's census/edge-cover interpretations at the above scope. FSI/CCIP remain stopped; the release now has a concrete, source-qualified static functional action space. A plain shared `h_AB(u,v)` law is a possible future falsifiable empirical hypothesis, not yet a novel operator or an RSI result. Any development-only numerical test needs its own hypothesis, task partition, complete paid-input definition, baselines and useful-gain/stop criteria before target access. No further metadata scan, GET or fit is needed for this audit.
