# E. faecalis dynamic source: authenticated identities and limits

2026-10-22. **OFFICIAL_S1DATA_ACQUIRED; MAIN_CLONE_IDENTITIES_AND_CRO_POPULATION_DAY_IDENTITIES_QUALIFIED; FINITE_FUNCTION_VALUES_NOT_EVALUATED.** The source is Maltas, Huynh and Wood, *Dynamic collateral sensitivity profiles highlight opportunities and challenges for optimizing antibiotic treatments*, PLoS Biology2025, DOI10.1371/journal.pbio.3002970, PMC11709278. No model, DeepSeek call, performance, novelty, inheritance or RSI experiment was run.

## Acquisition, preservation and exposure

Original exactly-one-GET publisher block is sealed separately in `../REPORT.md`: PLOS returned302, zero body, with an explicit publisher-storage Location. A separately authorized/frozen followup made **one GET** to that exact Location, HTTP200, **164,331 bytes**, with no retry/redirect/third download. Source host=`storage.googleapis.com`, basename=`pbio.3002970.s001.xlsx`, Location SHA256=`485d91988f47a927c8847605491c583fd399f648ea19d9970589e616be94553a`. The signed query is kept only in local NETWORK provenance and is omitted here. These two blocks total two GET/164,331 body bytes. The workbook remains byte-identical; there is no rewrite, export, rendering or recalculation.

Nine corrected synthetic projection tests passed in maestro before acquisition; the initial `Class A` regex failure and correction are retained. The source-schema protocol/code and inputs were frozen before each request. The followup's eight frozen files plus workbook hash pass verification. A separately frozen numerical identity/design census subsequently interpreted only **275 explicitly enumerated coordinates** (80 main dates and195 Fig4B ID/day/challenge-dose metadata cells), with nine synthetic tests and all12 frozen-file hashes unchanged. The original source projector is unchanged; later helpers read approved JSON/coordinate metadata and the authorized primary Table1 rather than broadening numerical response scope.

**Exposure is not perfectly outcome-blind.** The guard withheld finite numeric strings, numerical cell bodies, formulas/caches and recognized Yes/No/CR/CS/neutral/qualitative outcomes. But S3 contains **240 nonfinite string markers** which were emitted because the numeric regex missed them. They were seen by auditor/root and must be treated as exposed derived-statistical boundary information. `EXPOSURE_CORRECTION.md` preserves the failure; original outputs remain unchanged, while `SAFE_WORKING_SCHEMA.json` masks those markers for later use. Unknown pure strings, analysis annotations, statistical section labels and all literal schema are explicitly design/exploration-exposed. No finite IC50/OD/AUC response array was interpreted or exported. Neither tests nor post-exposure masking retroactively make the first projection sealed evidence.

## Exact workbook and principal identity objects

There are **eleven visible sheets**, no Fig4C sheet: Fig1B, Fig2ABC, Fig3BC, Fig4B, Fig5ABC, S1, S2, S3, S4, S5, S6ABCD. Earlier short progress text that suggested a separate Fig4C is corrected in `SCHEMA_CORRECTION.md`. Fig4B contains its own embedded AUC and Relative IC50 regions. `SHEET_INVENTORY.json`, internal `XLSX_MANIFEST.json` and original type/string coordinate projections preserve structure. Sheet names and cell types do not by themselves authenticate numerical validity or semantics.

### Main five-drug experiment: clone assays after serial passage

Primary Table1 authenticates ceftriaxone=CRO, ciprofloxacin=CIP, daptomycin=DAP, doxycycline=DOX and linezolid=LZD. Primary Methods say frozen evolution stocks were plated and **a single colony selected for IC50**. Thus the phenotype measured at a date is a sampled clone; it is not automatically a census of the continuing mother population's full state distribution.

`Fig1B` has dimension A1:M86. A2=`Replicate`, B2=`Time (Day)`. The safe A strings encode selecting drug plus lineage1–4. The separately allowed B-date census verifies **exactly80 unique keys = five selecting drugs ×four lineage labels ×days{2,4,6,8}**. C2:G2 and I2:M2 enumerate CIP/DAP/DOX/CRO/LZD; D1=`Testing Drug (Mean)`, J1=`Testing Drug (Sem)` are merged heading anchors. Main body mean/SEM columns were not decoded. Coordinate-only checks find all400 expected mean slots and400 SEM slots have numeric type/value nodes, but this does not establish finite validity, normalization, missingness or curve-fit success.

Qualified minimal assay unit is `(selecting drug, evolution lineage, sampling day, challenge drug)` with a mean/SEM functional summary. There are20 trajectory labels and repeated dates, not400 independent populations or tasks. Technical dose-response replicates are3–4 in Methods, but the workbook mean/SEM table does not expose their per-curve identity/cost. A causal state-transition claim must account for clone sampling and adaptive CRO/other-drug selection concentrations; actual daily selecting-dose histories were not authenticated by this workbook identity block.

### Fig4B: independent twenty-population CRO selection with sampled DOX challenge

Primary Results/caption explicitly describe a **separate experiment**: twenty independent E.faecalis V583 populations selected in escalating CRO for14days; daily diluted samples were cultured for24h across DOX concentrations. This distinguishes it from the main four-lineage clone-assay experiment. Same small integer labels across experiments are not a cross-experiment sample join. There is no source evidence here that a DOX-challenged branch then continues evolving and repeatedly switches drugs.

`Fig4B` has dimension B2:AY48. Its seven top raw normalized-OD panels have string labels at **days2/4/6/8/10/12/14**. The Replicate columns and raw-response columns are:

| Day | Replicate identity scope | Response scope, not decoded |
| ---: | --- | --- |
| 2 | B9:B28 | C9:H28 |
| 4 | J9:J28 | K9:P28 |
| 6 | Q9:Q28 | R9:W28 |
| 8 | X9:X28 | Y9:AD28 |
| 10 | AE9:AE28 | AF9:AK28 |
| 12 | AL9:AL28 | AM9:AR28 |
| 14 | AS9:AS28 | AT9:AY28 |

The exact numerical identity census confirms each panel has **IDs1–20, all unique and in the same order**. These are twenty population trajectories, not two replicates. All840 expected top-panel OD slots have numeric type/value-node presence according to coordinate-only metadata. Contents, finite validity, normalization and technical replication are not checked.

Below C3=`Concentration DOX`, the exact allowed **C4:H4 dose grid is0,0.05,0.1,0.2,0.4,0.8**. Primary Fig4 caption identifies the nonzero endpoints0.05–0.8 µg/mL; this is a DOX challenge-assay design, not a record of CRO selection concentrations. Zero is a candidate no-drug well, but a grid alone does not authenticate actual no-drug/ancestor normalization or per-plate control mapping. Dose design and published timing choices are designer/prior-feedback-exposed; all later comparisons must share them.

### Daily functional-menu identities exist within Fig4B

The embedded region has C34=`strain`, **D34:W34=IDs1–20**, matching the top-panel IDs/set/order. B35=`Day`; **C35:C48=days1–14** exactly. B39=`Relative`, B40=`IC50s` identify the adjacent matrix as the candidate daily relative-IC50 source. The280 expected D35:W48 positions have numeric type/value-node presence; none of those response values were decoded. Exact formula, logarithm/reference normalization, units, fit provenance, bounds and control definition remain **unqualified** until author source I/O is checked. Generic Methods IC50 definitions do not automatically settle the meaning of this specific `Relative IC50s` matrix.

At C31=`Days`, **D31:R31=days0–14**. C32=`AUC`; the15 adjacent summary-value positions D32:R32 are numeric-present but unread. This is a scalar summary per date in the workbook schema, **not authenticated individual-population AUC trajectories**. AUC individual recovery would need the raw curve provenance/code, and only even-day top curves are present here.

Thus a daily **twenty-ID×fourteen-day functional menu has authenticated identity metadata**, while normalized finite response semantics/quality remain pending. The seven top raw-curve panels and fourteen-day candidate IC50 menu must be distinguished. Absence of odd-day raw curves in this workbook does not justify discarding legitimate even-day assays, and daily IC50 labels do not prove daily raw-curve availability.

## Other source structure and remaining provenance

`Fig3BC` (A1:AS216) includes LZD-CRO, CRO-DOX and CIP-CRO blocks with Strain/Replicate/conc/OD-measurement labels and days2/4/6/8. Their numerical lineage/technical-replicate/concentration identities were not opened in this block. Their exact relationship to the Fig1B clone table, fitting units and control rows remains for author I/O inspection. `Fig2ABC`, supplementary trend/correlation sheets and `Fig5ABC`/S6 simulation sections are not independent empirical tasks; derived statistics and policy simulations cannot be substituted for a true continuation experiment or a validation source.

The official code record/repository is already authenticated by root/scout (`jamaltas/Temporal_Collateral_Sensitivity`,v1.0, Zenodo14064964). This auditor makes no additional download. Root's assigned source-I/O review can resolve Relative IC50 definitions, OD normalization/control curves, biological/technical replication, actual selecting-dose history and model transition construction. Any insufficient evidence is a provenance gap, not evidence that data are absent.

## Legal query / state / function and dependence conclusion

- **Query:** after response semantics and numerical scope are frozen, query a main-clone drug assay or a population/date DOX curve/IC50 assay in the actually measured menu. The query cost should cover required concentration/technical-replicate bundle, not treat every concentration well as a new independent experiment. Full-profile means and raw curves have different acquisition granularity.
- **State:** prior observed phenotypic resistance/history can form a partial dynamical state; this source has no authenticated evolved genome/transcriptome state. Earlier collateral profiles and observed sample history are available only when their assay cost/time is paid. Main single-clone snapshots do not by themselves prove a sufficient Markov state of the continuing population. The original paper already models phenotypic resistance vectors, time-dependent transitions and dynamic policies.
- **Function:** main five-drug clone phenotype summaries and timed DOX susceptibility of CRO-adapting populations are real functional objects. Fig4 supports prediction/selection of **when to assay/challenge DOX**, not arbitrary multi-switch treatment continuations. A next-agent action does not have a measured next-world continuation for every drug choice.
- **Independence:** main four lineages per drug and separate twenty CRO populations supply within-regime replication. Dates, curve doses, technical replicates and multiple drug measurements on a clone are dependent observations. Twenty Fig4 populations do not establish twenty independent research programs or cross-task inheritance. Independent experiments differ in clone/population sampling and cannot be pooled as exchangeable tasks without explicit design.

## Gate and next decision

The earlier individual-AUC gate remains **unexecuted**. No finite outcome has been used to choose a gate. A legitimate even-day raw-curve gate could use day2/4/6 history to predict day8/10/12 outcomes, but this must be explicitly preregistered as a schema-driven amendment before response access. The existing daily IC50 identity menu may instead allow an odd/every-day gate, only after author code authenticates its target definition. Neither route should be silently substituted for the other or for individual-AUC data.

Proceed only to source-I/O/finite-response-semantics qualification and a separately frozen evaluation design. Existing direct history predictors, original static/dynamic MDP, ordinary retraining/continual/active learning and equal-budget search must receive the same exposed priors, timing/design and assay costs. No performance, world-model value, agent value, joint benefit, transferable improver or RSI claim follows from this successful identity block.
