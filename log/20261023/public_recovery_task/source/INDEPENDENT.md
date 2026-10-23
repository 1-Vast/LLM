# Independent fixed-repository and assay-contract qualification

2026-10-23. **PUBLIC_SOURCE_FILES_AUTHENTICATED / NUMERIC_FORECAST_NOT_YET_QUALIFIED.** The exact author-declared repository contains public experimental-input CSV file identities and a readable processing program at a fixed commit. However, the originating experiment's “cell numbers” are CellTiter-Glo assay outputs, not authenticated direct cell counts; same-well early/late tracking and independent replicate structure remain unqualified. The author processing also uses all four weekly continuous-treatment endpoints to normalize derived short-challenge growth rates, which would leak future calibration into an early-prefix test if reused unchanged.

## Scope, independence and actual retrieval

Full goal remains applicable and was reread in the preceding immediately connected source task; read public_recovery_task/START.md and the original supplied 2026 primary XML independently. At parent's direction subsequently read supplied experimental_primary.body, the actual underlying experiment PMC8944661, DOI10.1073/pnas.2113535119 (2022), without another request. No same-phase peer report or conclusion was read before this seal. No outcome CSV, MAT, XLS, image/video, simulation dataset, author code execution, RNA resource, paid API or fitted model was obtained here. Author primary text contains published response descriptions and selected numbers; these are source-exposed and not blind project outcomes.

Exactly three purposeful GETs, with original URL/status/time/hash bodies in REQUESTS.jsonl:

1. GitHub public commits endpoint for SJHamis/phenotype_adaptation, HTTP200,4421bytes. Pinned commit **b21335969c76c25a36678db5af19e2d74571abad**, committer timestamp2025-05-03T21:08:08Z, message “Wolfram Mathematica Notebook added”. This current repository snapshot predates the supplied2026 primary but is author-linked; commit date is not evidence of experiment date or data independence.
2. Fixed tree **b834d104c62d8e0114a1b4c29d9e3af412558c71**, recursive=true, HTTP200,10781bytes, truncated=false. Its complete file identity list was inspected; no listed outcome file was followed.
3. One original fixed-commit source file: generate_fitnessmatrix_and_fig1/invitro_data/ProcessData.m, HTTP200,5520bytes, SHA25603b149653dafe3fe2562af8f4afff333ba8de32cd0e47895e74b9e3d6ea7e048. Git blob f4ffd5a20621c2aa6f2a36c39e74286c2d1025db. Raw source contains numerical algorithm/index/settings literals, which were downloaded. First a number-redacted projection was inspected, then the original relevant processing lines were read. The source reads measurements from separate CSVs; no individual measured count array is hardcoded in the inspected processing source. The redacted projection is not a security or blinding guarantee, and the literal outlier threshold is author-selected information.

Neither README, DownloadData.m, figure programs nor fit programs were fetched, preserving the three-GET limit. Therefore code that fetches underlying source data and exact figure-specific hardcoded inputs is not authenticated by this review. No second repository or source was pursued.

## Public experimental-input file identities

All paths below are under generate_fitnessmatrix_and_fig1/invitro_data/ at the pinned commit:

| File | Tree bytes | Git blob identity | Meaning authenticated here |
|---|---:|---|---|
| kavran_28day_treatments.csv |1384|613153aef9afe902d9f3406ba50543f9d0882397| ProcessData explicitly reads it as four-week treatment input |
| kavran_3day_cellcounts.csv |3431|d3a03c2c92c01bd1d6f01f6c4e9fa7fdefdb3fbb| ProcessData explicitly reads it as short dose-challenge fold-change input |
| growth_rates.csv |34067|165dc95902f2de3b51db62c2227e56d16b0573fe| Derived output written by ProcessData, not an independently acquired assay |
| DownloadData.m |601|df1220788037bd98d8f5c69d55dce6b30428095b| Invoked by ProcessData, content not fetched |

The public nontruncated Git tree and the corresponding readtable calls authenticate real source-file availability/identity, not just a prose assertion that data exist. Actual CSV headers, all row values, checksums of downloaded CSV bytes, replication membership and normalization numerators were not inspected. Dataset names are not substitute measurements. Other MAT workspaces and simulation files in the tree are not biological replicate banks.

## Exact processing schema and future-calibration problem

For the28day input the program selects data_gr.sample='V600E' and data_gr.schedule='Continuous'. It takes columns5:end as a numeric matrix and pairs it with day_mat=repmat(7:7:28,6,1). This establishes the author's assumption of six rows crossed with days7/14/21/28, but not physical well continuity or six independent biological preparations. The identities/meanings of columns1–4 are not all inspected. There is no explicit dose-column restriction in this processing block; the code alone does not authenticate both300nM and500nM four-week biological cohorts.

The program excludes cell_counts_vec>=7000 for regression and replaces matrix entries>7000 withNaN for plotting; equality7000 is handled differently in those two operations. This is an author implementation detail, not a project-validated exclusion rule. It fits log output versus day using all retained weekly endpoints to derive lambda_cont. No claim that a removed point is erroneous is licensed without assay evidence.

For the3day input it references sample and rep_number, interprets columns3:end header names as dose strings, and converts their entries to fc. It assigns day/treatment through the ordered unique sample list and fixed arrays [0,0,7,14,14,21,21,28,28] and nil/continuous/intermittent labels. This mapping depends on the actual sample ordering and cannot replace an inspected manifest. Short-challenge growth is log(fc)/3 under the author's exponential interpretation. The mean continuously adapted300/1000nM short-challenge rates are linearly interpolated to500nM, and the program then computes:

    growth_rate = growth_rate_unnormalised - interpolated_short_challenge_500nM + lambda_cont

It writes sample,rep,day,treatment,dose,log_dose,fc,growth_rate_unnormalised,growth_rate to growth_rates.csv after removing Vector Control.

Because lambda_cont incorporates day7–28 outcomes of the continuous cohort, using that derived growth_rates.csv or a fitness matrix based on it as supposedly early/source-only calibration in the same four-week forecast would introduce future information unless that calibration is explicitly treated as independently available source knowledge for every comparator. The author2026 paper separately states that its500nM parameters fit continuous and intermittent full trajectories together. Such author model/data agreement is not held-out500nM forecasting. Any project prefix test needs an actual source-only calibration and equally informed direct controls; it cannot silently inherit the published full-trajectory fit.

## Independent audit of the originating experimental observation

The actual2022 primary Fig2 describes WM239A cells with induced BRAF V600E or empty vector in96-well plates,500nM encorafenib/LGX818 for four weeks. The intermittent schedule is seven days on then seven days off: drug on weeks1/3, off weeks2/4; media changes on days3,5,7 of each week. At weekly endpoints “cell numbers” are quantified using **CellTiter-Glo** and normalized to the initial number seeded. BRAF panel n=5or6 and empty-vector panel n=6 are reported. These are the original methods, not inference from the2026 model's “cell count” terminology.

CellTiter-Glo is an ATP luminescence viability assay; no independent direct-count calibration or invariant ATP-per-cell conversion was authenticated here. Therefore a legal numerical outcome would initially be a normalized CTG assay response, not measured physical population counts, actual death fraction, or a birth/death rate. The2026 model maps net growth signs to individual division/death probabilities, but CTG curves do not independently validate those biological rates or phenotype transitions.

Weekly CTG endpoints do not authenticate a nondestructive continuous record of the same well. The assay is destructive; absent an experimental layout/replicate-lineage manifest, a CSV row with multiple weekly columns must not be claimed to be the same tracked physical culture or six independent longitudinal biological tasks. It could represent paired replicate design or endpoint replicate indexing; the current code/primary text does not settle that. Earlier sibling wells could still be lawful source information at a group-level landmark, but their dependence and allocation must be stated.

Fig3A/B is a separate experiment: cells in10cm dishes undergo continuous/intermittent500nM exposure; at each weekly endpoint cells are trypsinized, reseeded into96wells and challenged for72h at varying doses, with n=4. These dose-response FCs are not continuous measurements of an unchanged Fig2 well. Fig3A/B explicitly share baseline/vector/BRAF and week1 data for visual comparison, so two displayed curves are not independent duplicated experiments. Fig3C measures PI-positive cell fractions in another10cm-dish assay across five weeks, with n=2 independent experiments and collection of adherent/nonadherent cells. It supports actual death observations in that separate experiment, but there is no authenticated per-well join to the repository's four-week CTG endpoints. The RNA sampling assay is yet another context and is not used.

The supplied2026 primary overlays six experimental replicates on300/500nM model plots. The2022 actual primary methods and the inspected processing block authenticate500nM continuous/intermittent protocols; they do not yet establish an independent300nM four-week biological cohort. No direct outcome file or figure code was fetched to resolve this difference, so it remains explicit and unresolved. Do not equate simulated300nM trajectories with a verified new biological condition.

## Qualification, strong controls and stop conditions

**Positive:** a fixed public author repository with small experimental-input CSVs is genuine; an exact processing schema and actual500nM on/off protocol are authenticated. This is a stronger source result than an image/software-only release. Older underlying experimental data are allowed and do not disqualify the2026-method application.

**Not yet qualified:** actual CSV column headers/row memberships, physical replicate independence and cross-time pairing, all-data versus selected-data coverage, original CTG normalization/calibration, and the claimed300nM cohort. Thus do not start a count/death/phenotype forecast, a same-well adaptation test, or an independent300→500 transfer experiment from these metadata alone.

A next separately authorized bounded header/layout check could support a small explicitly CTG-response forecasting diagnostic, with an honest development/exposure designation, if legitimate independent units and past-only measurements exist. The narrow test does not require complete RSI generations. Freeze original assay outcome, landmark, eligible groups, source-only normalization, full exclusion policy, endpoint, and ordinary comparisons before numeric fit. Relevant strong controls include same-information current-level/log-slope prediction, regularized schedule/history regression, ordinary parsimonious on/off state-space or mixture refit, sequential/continual updates, direct assay response prediction, and equal-total-cost updater/program selection. A fixed two-schedule observation does not authenticate arbitrary schedule counterfactuals or a large intervention menu for an active agent.

Success would require practical held-out assay-response/decision improvement beyond those controls at the correct independent-unit level; counts or death claims additionally need direct assays. If only correlated technical endpoint replicates or only one condition pair exist, report the narrower conditional diagnostic rather than later-task inheritance. Stop if future-calibrated growth_rates is needed to obtain the apparent gain, if code-defined row pairing lacks experimental support, or if ordinary same-history controls explain it. Novel update operation, world contribution, agent contribution, updater inheritance, joint gain and improved-improver efficacy remain unestablished. Full goal ACTIVE / NOT_ACHIEVED.
