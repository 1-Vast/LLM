# Header/glossary review for the root's metadata-only row scan

2026-10-22. Read only root's preregistered`AZ_DESIGN_PROTOCOL.md`,`az_design/HEADERS.json`, and`az_design/GLOSSARY.txt`. NoGET, noCSVdata rows, no target conversion. Root's new241MBacquisition is governed by its separate protocol and explicitly counts as source-response-byte contact. This review does not expand access.

## Whitelist verdict

The enumerated list is **21fields**, despite a message calling it22:

`PROJECT_ID PROJECT_NAME BARCODE DRUGSET_ID CELL_LINE_NAME MASTER_CELL_ID COSMIC_ID CELL_ID TISSUE CANCER_TYPE POSITION lib1 lib1_dose lib1_drug_id lib1_conc lib2 lib2_dose lib2_drug_id lib2_conc treatment cmatrix`

All21occur in the five47-columnCSVheaders. They are appropriate design metadata. Parse IDs/tags as exact strings and declaredµMconcentrations only as explicitly allowed design numbers. `POSITION`may be a numeric well index; its magnitude is not a response. Keep the exact textual form alongside any canonical numeric dose if necessary to detect formatting aliases. No content-driven fallback or automatic additional columns.

Exclude`INTENSITY`,`inhibition`,`lib*_y`,`lib*_yhat`, all HSA/Bliss fields,`xmid/scal/x/IC50/auc/RMSE/maxc`and`lib1_drug/lib2_drug`from the fit-information portion. In this glossary`lib*_drug`identifies monotherapy fit provenance; that is distinct from the genuine treatment's`lib*_drug_id`. Do not obtain source-fit identity by reading through excluded fields. This leaves a **real gap**: metadata cannot certify that attached monotherapy fits are from exactly the desired stock/occasion or usable at the target dose. Report it, do not infer it away.

`treatment`is documented alwaysC. Count its design values to detect source divergence; do not call those rows a mixed S/Cwell pool. Matched monotherapy response columns do not expose raw physical monotherapy/control wells with their own well IDs. There are no authenticated carrier/positive-control action rows in this file. Therefore the current source cannot directly instantiateFSI's control-versus-drug query menu.

## Keys that must retain their source meanings

- `MASTER_CELL_ID`: unique cell model. Use it as the primary source context/group key; different stocks of one model are related, not new independent cancer backgrounds.
- `CELL_ID`: stock expansion. Count separately and retain its nesting within the model. This is a real improvement over treating all repeats as untyped, but expansion identity alone is not an authenticated occasion/day/independent-donor key.
- `COSMIC_ID`: where available. It can support a later Jaaks join, with conflicts/missingness reported. It does not imply that the new raw file hasSIDM, nor thatMASTER_IDequalsSIDM.
- `BARCODE`: screening plate. Scope by source/project unless global uniqueness is demonstrated from metadata.
- `DRUGSET_ID`: **layout**, not laboratory occasion. `cmatrix`: layout matrix ID, not globally unique matrix experiment. `lib1/lib2`: layout tags, not drug names.
- `lib*_drug_id`+`lib*_conc`: treatment compound andµMdose. Canonicalizing a pair requires swapping its linked dose/tag axes consistently. Identical drugIDsneed an explicit self-combination flag, not silent pair collapse.

No drug-name/clinical-exposure dictionary is present in this whitelist. Exact37drugnames and all Jaaks aliases remain unverified by this raw scan; no same-family substitution or clinically achievable dose restriction can be asserted from numeric IDs alone.

## Minimum output counts in one streaming pass

1. **Member/project census:** row count, distinct source/projects, drugsets, plates, treatment tags; actual header match and column-count errors sanitized to row numbers. No target availability/min/max/type check.
2. **Lineage census:** model count; stocks/plates perMASTER; mappings to names,COSMIC,tissue/cancer type and conflicts. Keep all appearances of one model in one eventual role. Count absent identity fields without interpreting absent target fields.
3. **Physical matrix census:** use scoped`(member/project,BARCODE,MASTER_CELL_ID,CELL_ID,cmatrix,canonical drugIDpair)`. Count row/wellposition duplicates, unique linked dose coordinates and their cardinality distribution25/49/other; preserve true source units/tag↔µMmapping and pair-axis reversal. Do not assume every header-described7×7matrix has49releasedrows or that any non49isAZD1775without a drug dictionary.
4. **Pair-context coverage:** per screen and all-screen union counts of unique`(MASTER,pair)`and`(MASTER,CELL_ID,pair)`; repeated matrices/stock expansion/plate multiplicities and cross-screen overlaps. Compare genuinely different granularities to the reported68816rather than subtracting arbitrary raw row counts. Nominal72062minus68816is3246, but without QCflags/summary qualification fields it may remain an unresolved publication-definition gap. No target-value criterion may be introduced to make it match.
5. **Legal menus:** record measured pair menus and exact dose support for each context/stock; coverage perpair and intersection distributions. Derive whatever genuine common menu exists, and separately task-specific measured-action masks available identically to all arms. Do not impose my earlier16cancer-type threshold as a universal qualification rule.
6. **Pair-graph/mono-cost feasibility:** construct vertices from actualdrugIDsand edges from measuredpairs. For a target unboughtABedge, determine whether other paid edges could cover both A/B at matching declared doses and compatible stock. This is a structural possibility only. It does not authorize reading the targetABrow's attached mono_yhat or releasing all monotherapies free. Without physical mono provenance keys, cost accounting must explicitly choose whole-matrix-plus-matched-reference bundles and acknowledge what that synthetic offline oracle represents.

Full projected design keys may be saved under the phase log to support independent auditing; no unprojected data rows or parser tokens should appear in output. The scan should keep only metadata needed for these counts, not repeatedly decode the archive for speculative analyses.

## What this scan cannot certify

The whitelist cannot determine usable numeric targets, missing/nonfinite response masks, raw control actions, sourceQCthresholdpass, matching monotherapy-fit origin, early molecular state, original run dates or all cell-line synonym equivalences. Missing those fields does not invalidate every static task; it limits exactly which oracle and independence claim can be made. A later response protocol may audit availability but must explicitly label that access.

For the advocate's proposed ordinary`h_AB(u,v)`transport pilot, this census can qualify paid drug/dose graph coverage and stock relationships. It cannot establish shared mono-effect support, injectivity of mono curves, replicate measurement noise or residual stability. Those are falsifiable numerical questions for a later development-only protocol, with same information/cost for strong direct, Bliss, shared ordinary residual and refit controls. It remains a plain structural hypothesis, not a new core or RSI result.

Recommendation: accept the21-field scan after its explicit schema freeze, keep the gap/lineage limitations, and stop at source-design results. Do not acquire the8MBsingle-GDSC010summary merely to avoid saying that the241MBarchive contains target bytes; the archive is already acquired and sufficient for this permitted metadata scope.
