# Independent STACK source and observation audit

2026-10-22. Written before reading any other current-stage draft. **The primary supports real multi-compound longitudinal marker-density screens and a narrower functional-readout forecast. It does not yet authenticate file/run/replicate joins, cumulative death events or independent future research tasks.** No new GET, workbook access, assay response conversion or fit occurred in this audit.

Source: Forcina et al., *Systematic Quantification of Population Cell Death Kinetics in Mammalian Cells*, Cell Systems 2017, DOI 10.1016/j.cels.2017.05.002, PMC5509363. Retained complete XML: log/20261022/functional_dynamics_gate/functional_auditor/RESPONSE_05_05_primary_efetch.body, 153,889 bytes, SHA256 fc96e1bc0ef59d9155e42a286a782f2a791eba04925984e41e1dcfdea6be974f. The source was hash-checked before and after extraction and left unchanged.

Precise paragraph locators below use P001–P076: count every XML `<p>` element in document order, including abstract and captions. PRIMARY_PARAGRAPHS.json records exact text, global ordinal and ancestor section IDs/titles. SCREEN_AND_FORMULA_EVIDENCE.json preserves additional exact screen/caption paragraphs, the original MathML formula and unrepaired QC lists. These are primary text projections, not numeric workbook observations. Published aggregate outcomes and selected-compound names were already exposed in the retained article; no literature-blind or cryptographically sealed claim is made.

## Measurement meaning and unit

| Source locator | Authenticated statement | Bound on interpretation |
| --- | --- | --- |
| P008, Results S3 | Nuc::mKate2 marks the live-labeled nuclear population; Sytox Green uptake (20 nM) marks dead-labeled objects. Imaging follows perturbagen addition. | Marker-defined populations, not a complete measured cellular state. |
| P034, S13 | Reporter populations are polyclonal lentivirally generated and puromycin-selected. | Not single tracked lineages; reporter populations are assay backgrounds. |
| P037, S17 | IncuCyte Zoom, 10× objective; phase/green/red images at fixed intervals, acquisition under2s per well. | A well is a population observation; frames are repeated measures, not independent assays. |
| P038, S18 | Cell-line-specific segmentation; mKate2 loss can depend on nuclear import/permeability/proteolysis. Objects are exported as **objects/mm²**, confluence as percent. | Not whole-well absolute cell numbers or integer event counts. Do not apply an integer-cell branching likelihood to densities without its area/observation assumptions. |
| P010 and P040, S19 | SG signals can disappear from old corpses; persistent SG+/mKate2+ double positives can underestimate death under LF scoring. | Raw dead stock and its running maximum are not cumulative death-event counts; no Δdead→death or Δlive+Δdead→birth conversion. |

P038 explicitly gives different segmentation settings for T98GN versus U-2 OSN and other lines. Cross-line transfer therefore changes genetic background, medium (P033) and measurement processing together. Good cross-screen prediction is not proof that a latent biological parameter transfers independently of assay calibration. The paper reports that widespread pre-death detachment was not observed (P038); this is supportive assay evidence, not a universal per-trajectory guarantee of mass conservation.

The scoring formula in source section S19, disp-formula FD1, is:

`LF(t) = 1 − L(t)/(max_{0<=s<=t} D(s) + L(t))`.

The maximum is retrospective only up to the time being scored. A legal early LF prefix must not use later dead values, full-trajectory LFmax/AUC, fitted DO/DR or future-fit success. LF is a defined dye/object readout summary; it does not repair missing death events or establish an individual-cell survival probability. LFmax and AUC summarize outcomes; LED parameters are fitted summaries with ambiguous fits excluded in the original analysis (P041–P042). None is an independent observed mechanism truth.

## Three screens, actual actions and time origin

P015 identifies a 1,833-member bioactive library at fixed5 μM. P043 identifies Selleck L1700 and reformatting from96- to384-well plates; exact library records/duplicates remain for root's manifest/schema qualification. P044 (S23, Data collection) says cells were seeded the day before at1,500 cells/well in40 μL across five384-well plates, drugs added the following day, then imaging began immediately. P035 gives the general Day−1/Day0 schedule and a starting confluence target below50%.

| Screen identity from primary | Actual intervention/context | Planned temporal design |
| --- | --- | --- |
| U-2 OSN library screen | Each library compound5 μM, DMSO controls | Every2h through118h |
| T98GN library screen | Each library compound5 μM, DMSO controls | Every4h through96h |
| T98GN+TMZ library screen | Library compound5 μM in medium containing TMZ400 μM | T98GN4h/96h schedule |

Sources: P016; P019 explicitly calls the TMZ comparison the previous T98GN dataset without TMZ versus a new TMZ experiment; P044 states “In one experiment with T98GN cells” compounds were added to TMZ-containing medium; P056 and caption P070 name the deposited screens. P070 says its +DMSO class results reuse Figure3D; the reused baseline is not another independent run.

The primary anchors nominal experiment time0 near drug addition/first scan. It does not authenticate workbook time cells, per-plate addition/scan offsets, timestamp units, or exact matches of nominal time labels across the three files. Until headers identify them, use a declared relative acquisition-time readout rather than assert exact simultaneous dosing for every well. There is no washout, sequential intervention program or multi-dose HTS action menu in these three screens. The paper's10-point dose series and three-replicate MEF studies (P013/P051/P068/P071) are other experiments; do not silently import their design into these deposited library screens.

## Library, QC and outcome-selected populations

P001 says1,819 bioactive compounds across two human cancer lines; P015/P043/P044 describe the1,833-member starting library. P016 reports1885 retained U-2 OSN conditions=79DMSO+1806test compounds, and1906 retained T98GN conditions=87DMSO+1819test compounds. Caption P070 also uses1819 for QC-passing interaction comparisons. These are distinct library/quality-screen/condition counts. Do not assume1819 distinct compounds occur in every file, that1833 means1833 unique chemical identities, or that missing rows are unmeasured zero effects. The file roster must reconcile the units.

Four different response-dependent operations are stated in the source:

1. P038 censors a count more than10-fold different from the immediately preceding count; the authors report this affects less than0.001% of counts. The deposited “raw” workbook may therefore contain image-processed/censored exports; its exact pre/post-censor status is not established by that adjective.
2. P045 visually removes apparent green-background compounds using starting SG>50objects/mm² at0 or4h together with live-marker judgment. It also removes wells with starting mKate2<50 or>400objects/mm², then applies a ROUT outlier check. This is assay readout/QC information, not metadata-only drug identity.
3. P046 selects lethal compounds by plate/DMSO-based LFmax thresholds and a minimum LFmax>0.5. This uses the future outcome and cannot define a general prospective forecast cohort without explicitly changing the estimand to a previously selected cohort.
4. P042/P047 exclude ambiguous LED fits; P047/P050 manually assign DO=1h to certain near-instantaneously lethal compounds. Fit success and such assignments cannot be prefix features or unbiased event-time labels.

**Preserved primary discrepancies, not repaired:**

- P045 says “Eight” excluded fluorescent T98GN compounds, but lists nine named entries: PHA-665752; idarubicin HCl; TSU-68; quinacrine2HCl; Ro31–8220 mesylate; daunorubicin HCl; sunitinib malate; SU11274; nintedanib. Do not choose eight or nine as a benchmark mask from prose alone.
- P045 says seven U-2 OSN compounds, but prints `nintedanib PHA-665752, TSU-68, idarubicin HCl, SB216763, SU11274 and Ro 31–8220 mesylate`. There are six comma/final-and-delimited entries; seven would require treating the unseparated first two names as two compounds. Preserve the punctuation ambiguity rather than silently inserting a comma.
- P047 says80 high-confidence common compounds, whereas P001/P016 and caption P069 use79. Fit-qualified versus initial-lethal sets may differ, but a membership reconciliation is not supplied by these sentences. Do not invent one or select the set that yields favorable modeling.
- P001 points to data DOI version.2; P056 points to version.1. Current root protocol has authenticatedv1 and identifiesv2 as soft404. This auditor has not requested either. The original textual difference remains recorded; it does not authorize guessed version equivalence.

The differences1833→1806/1819 are not fully accounted for by the inconsistent fluorescent-compound lists alone. Starting-density exclusions, duplicate library entries or other export handling could contribute, but are not authenticated explanations here. No missingness/QC decision array has been inspected. Later study must explicitly preserve source availability masks, prespecify whether original QC is descriptive or eligibility, and prevent outcome-derived selection from leaking into train/test construction.

## Experimental identity and valid narrower uses

P055 states “Except where noted, all data represent mean ± S.D of three biological replicates.” This is positive author-reported replication evidence and must not be erased. It does **not** provide per-screen run IDs, well-to-biological-start mappings, per-replicate arrays, or proof that three deposited screens are the three replicates. P067/P068/P071 explicitly tie three independent biological replicates to named MEF/validation experiments. Actual raw-file replica mapping remains open. A workbook may contain individual wells, per-run averages or already averaged biological replicates; only its authenticated schema can decide the observation unit.

Five assay plates distribute a library; they are not five repeats of every compound. Multiple DMSO wells are controls, not dozens of independent background experiments. Time points, imaged cells and compound wells must not be promoted into independent biological runs or future RSI tasks. The two cell lines and the TMZ condition are meaningful contexts/actions, but three screens alone cannot provide many independent history/validation/future laboratory-task streams. Distinct compounds also share target classes (P049), so ordinary held-out-chemical prediction is not automatically novel-mechanism extrapolation.

If exact files/headers support it, a compound-group-held-out early-marker→later-readout forecast is legitimate within these fixed screens. Keep each chemical identity together across wells/screens for an unseen-compound estimand, retain the original whole trajectory as the observation bundle, and distinguish same-compound cross-context transfer from unseen-compound transfer. A retrospective acquisition oracle may reveal existing compound/screen trajectories at declared costs; it cannot answer new concentrations, sequential treatments, new physical experiments or independent repeats that were never measured. Missing independent-run keys restrict external confirmation/RSI claims; they do not automatically prohibit an explicitly conditional within-screen experiment.

Current audit outcome: **primary observation semantics and intended screen map qualified; exact raw schema/unit/replica/QC joins pending root's bounded file qualification.** No new algorithm, causal D→L effect, inferred molecular mechanism, world-model advantage, agent improvement or inherited/recursive research benefit follows from availability. Do not transplant the failed HCT116 nonnegative subtraction field as an assumed STACK channel construction; qualify these exports independently and register any later readout/transform before values.
