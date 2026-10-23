# Supplement identity/header addendum

Date: 2026-10-22. Newly read only `WORKBOOK_HEADERS.json` and `IDENTITIES.json` from the current phase. Initial long displays were truncated; the relevant functional-sheet row-1 headers and complete identity summary were then extracted explicitly, including independent counts of Jurkat drugs and assay identities. No response numerical payloads, original workbook cells, new molecular matrix, fitted parameters or effect labels were read. This updates source qualification without editing the sealed independent/cross-review drafts.

## Newly established menu

The author supplement `TableS1 - Cpd via info` has an authenticated **condition-level functional menu**: 144 distinct Jurkat drugs, each represented once for Confluency, Cytotoxicity and Metabolic activity (432 rows). No duplicate drug/cell/assay keys are reported. Columns K:O are labelled Relative intensity at 1, 10, 100, 1000 and 10000 nM; J is Relative intensity 0. P:T are labelled Raw signal at the same five nonzero doses. The structural inventory reports J:T present and without workbook formulas, with no missing response cells. This is stronger than a highest-dose-only summary and removes the earlier specific uncertainty about whether the supplement exposes dose-indexed columns at all.

The other 24 rows are primary-T-cell conditions (12 CD4+ naive, 3 CD8+ naive, 6 CD4+ activated, 3 CD8+ activated). They are not extra Jurkat drugs or independent replicates of the main-screen conditions. They must remain excluded from the initial Jurkat task unless a separate contract explicitly introduces them.

**Qualification level: dose-indexed condition menu exists; independently measured local-feedback numerical semantics and molecular pairing are not yet fully qualified.** No molecular matrix was examined here. Therefore no molecular-functional drug/dose join has been completed or authenticated by this addendum.

## What labels and absence of formulas do not establish

"Raw signal" is an author column label. A stored numerical value with no Excel formula may still be an offline processed, field-averaged, time-aggregated, replicate-averaged, normalized or previously fitted/exported value. Neither that name nor the no-formula result proves an unsmoothed, single-well independent observation. Conversely, there is no evidence here that these dose-indexed values actually are fitted predictions. This distinction remains unresolved and must be recorded rather than guessed in either direction.

C:I explicitly contain slope, bottom, top, inflection, EC50, R2 and AUC; V is Effect. These are incompatible with a one- or two-dose feedback budget if computed from all doses, and must be excluded from limited-feedback support and independent observed-target claims. Their presence beside P:T does not prove P:T share that full-dose dependence.

## Remaining assay semantics

The saved original method already supports the following protocol-level account: main drug exposure is 18 h; protein lysis follows 18 h; functional aliquots are transferred for IncuCyte analysis over 3 h, while alamarBlue is read after 3.5 h. Confluency and metabolism are normalized to an average DMSO reference; cytotoxicity is first corrected for confluency and then normalized to DMSO. It does not identify all worksheet-export operations.

Specifically unresolved after this header review:

1. Whether Cytotoxicity/Confluency P:T represents the final imaging time, an average across hourly observations, an area/integral, or another Basic Analyzer summary; which operation averages the five imaging fields.
2. Whether P:T is before or after confluency correction for the Cytotoxicity rows; the exact correction formula and scale/units of all Raw signal columns.
3. Whether K:O is obtained by dose-local normalization against only controls, rather than additional all-dose transformations; whether J is an actual control aggregate, a constructed baseline, or something else. The name Relative intensity 0 alone does not authenticate raw DMSO values or their uncertainty.
4. Whether DMSO references are matched per plate/batch/drug, their retained individual values, and whether cross-dose shared normalization induces dependence. A control-normalized endpoint can still be a valid target when declared; it does not supply independent noise estimates automatically.
5. Independent well/biological repeat counts, any upstream averaging, batch/plate mapping, and precision of a given functional endpoint. No duplicate condition keys proves one exported row per key, not one original measurement or one biological repeat.
6. Molecular file identifiers, dose/unit mapping, background/protocol compatibility and drug aliases necessary to complete an authenticated condition-level join. Same-well identifiers are unnecessary for a properly limited condition-mean study but required for stronger individual-pairing/residual-noise claims.

## Consequence for continuation

Continue qualification of data provenance/export semantics and a source-only frozen numerical-access protocol. Do not apply the highest-dose-only STOP to this now-authenticated menu. If local measurement provenance remains incomplete, a clearly described study of the published dose-indexed endpoints may still be possible, but it must not claim verified unsmoothed experimental feedback or independently estimated functional noise. Numerical presence is not numeric validity, useful dynamic range, clinical decision value, or evidence for any novel update rule. Existing novelty STOPs and all protected boundaries remain unchanged.
