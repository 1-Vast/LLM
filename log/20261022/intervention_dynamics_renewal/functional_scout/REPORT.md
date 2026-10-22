# Cancer-cell sequence/washout functional-data scout

Date: 2026-10-22 local. Reviewer: `/root/functional_auditor`.

**Decision: retain one concrete, small-file qualification lead; no numerical experiment or framework expansion is justified yet.** Five GET attempts used538,728 body bytes in total; every response stayed below3MB. One HTTP503 is preserved without retry. No outcome workbook, bulk dataset, or original data table was downloaded or opened. No model API or author contact was used. The previous E. faecalis STOP is unchanged.

The strongest lead is the 2026 primary paper [Systematic interrogation of drug sensitivities in melanoma reveals potent synergistic and antagonistic drug combinations with translational potential](https://doi.org/10.1038/s43856-026-01583-w), PMC13338063. Its accessible [full-text XML](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13338063/fullTextXML) and the authors' [Zenodo record](https://zenodo.org/records/18962045) support a specific intervention experiment, rather than an inferred sequence assembled from unrelated single-drug screens.

## Authenticated design and exact limits

| Component | Primary evidence | What is still missing |
| --- | --- | --- |
| Background | Fig4 is WM1366 melanoma; Methods specify RPMI1640 GlutaMAX,10%FBS,1%penicillin/streptomycin,37°C,5%CO2; line authentication described | Experimental batch/passages and per-run identifiers |
| Actions | Cladribine→abemaciclib and reverse order are explicit;24h scan followed by two fresh-medium washes and next treatment; imaging continues through48h | All exact durations/controls from graphical Fig4A; abemaciclib concentration is not present in the inspected text |
| Dose | Results prose explicitly gives cladribine0.2µM | Do not infer abemaciclib dose from another experiment or typical dosing |
| Observable state | IncuCyte scan at baseline and every3h; Cytotox Green plus total cell count; separate flow DNA content and γH2Ax | Actual exported early count/state columns; whether flow is pre-switch or terminal; availability of numerical flow state |
| Function | Fig4B relative cell death = Cytotox-positive cells/total cells, monitored across the experiment | Exact source-table layout, units and missingness remain unopened |
| Independent repetition | Flow methods explicitly state three independent experiments on different days; imaging methods mention biological replicates with three technical wells per treatment | Fig4B caption explicitly gives three technical replicates; it does not authenticate the number of independent WM1366 imaging runs or all-run availability |
| Source join | Paper Fig4B→SupplementaryData3→Zenodo `Suppl Data 03.xlsx` | Workbook condition/time/well/run headers and flow-to-imaging condition/batch join |

The generic full drug screen has three MeWo experimental replicates. Those do not establish three independent WM1366 sequence experiments. Likewise23 cancer cell lines in the simultaneous combination screen do not become23 independent sequence runs. Fig5D/E share simultaneously collected controls according to the paper, so their control curves must not be treated as new independent samples.

Different physical samples do not automatically invalidate a useful **matched-condition population-mean** task. If dose, duration, background and run correspondence can be authenticated, independently measured flow-state summaries could be joined to later death under the same experimental condition. That would not be a same-cell trajectory. Here that correspondence, the early timing of the flow state, and numerical state availability are still unverified. The live imaging itself may offer an early population state even if the destructive flow assay cannot be joined; it would then support an explicit count/death-history forecasting task rather than a molecular-state claim.

## Smallest next object

The minimum next object is the authors' [Suppl Data03.xlsx](https://zenodo.org/api/records/18962045/files/Suppl%20Data%2003.xlsx/content), size**13,994 bytes**, manifest checksum**md5:61e96850942060d93915800cd08946dc**. This object was not fetched. Its role is source data for Fig4B, confirmed independently by both primary-paper availability text and repository description. The exact manifest and every file's advertised size/checksum/URL are saved in `EVIDENCE.json`.

A separate design-only audit should first inspect workbook sheet names and header/label coordinates, keeping numerical responses unopened. It should identify time, drug order/dose, technical well and biological run labels, and determine whether the export contains individual trajectories or only aggregate means. Graphical Fig4A still requires inspection to authenticate abemaciclib concentration and measurement timing. No source file for Fig4C flow state is identified by name in the availability statement or manifest; this is a provenance gap, not proof that none exists.

The current Zenodo manifest contains16 files, including an additional interaction-plot archive; the article supplementary enumeration contains15 data objects. Reconcile the version/descriptions when qualifying file identities. Large combination archives are unnecessary for the next step and were not fetched. In particular, the ~515MB dose-response matrices and ~8.83GB plot archive are not a substitute for the small sequence table or its missing run labels.

## Falsifiable application and stopping boundary

The defensible application is narrow: **forecast the48h population death fraction of a specified WM1366 treatment sequence using only its authenticated action history and measurements through24h**, evaluating on held-out independent experimental runs if such runs exist. A matched-condition early flow summary may be added only after its time and batch join are established. This would inform which schedule warrants subsequent experimental verification; the current observational export alone would not establish a policy that selects the second drug for an individual cell.

A possible later information-value claim is that early state improves held-out-run forecasting over drug/order/time alone. Before opening numerical outcomes, freeze the split, endpoint and a practical threshold such as at least10% relative MAE improvement, compare with a strong direct prefix predictor and simple extrapolation under identical observed-data budgets, and stop if the threshold fails. This is a proposed follow-up criterion, not a registered performance experiment or a world-model innovation. It must be reviewed against the actual run/condition count before adoption.

Source qualification stops if action doses/timing cannot be authenticated or no state-to-function condition key exists. If only a single biological imaging run with three technical wells is available, the data may support within-run descriptive forecasting, but not held-out-run generalization or the user's broader inheritance/RSI evaluation. Do not inflate technical wells, time points or shared controls into independent tasks. A world-model/agent/RSI experiment would require additional independently evaluated action-conditioned tasks and explicit baselines; this scout supplies none of those capability results.

## Search boundary and records

The first EuropePMC query returned the first16 metadata records from19,510 hits; its broad terms are not a comprehensive targeted search. The second more focused query returned503 and was not retried. A later narrower washout/imaging query returned the first20 of159 hits, many involving contrast-agent washout rather than cellular drug washout. Its only retained secondary lead is the abstract of [Simultaneous targeting of KRAS and CDK4 synergistically induces durable growth arrest in pancreatic cancer cells](https://doi.org/10.1038/s41419-025-08362-w), PMC12847887, published2025-12-23. It describes washout response and mechanistic state measurements, but no full text, manifest or sample/run join was audited; it is not qualified.

| GET | Object | HTTP | Body bytes |
| --- | --- | --- | ---: |
| 01 | Broad primary-article metadata | 200 | 143,499 |
| 02 | Focused primary-article metadata query | 503 | 89 |
| 03 | PMC13338063 primary full-text XML | 200 | 223,540 |
| 04 | Zenodo18962045 metadata/file manifest | 200 | 9,994 |
| 05 | Washout/imaging primary-article metadata | 200 | 161,606 |

`REQUEST_01_*.json` through `REQUEST_05_*.json` preserve exact URLs, start/end UTC, HTTP status, body bytes and SHA256. `EVIDENCE.json` embeds the ledger, verbatim relevant methods, file manifest, authenticated facts and unresolved joins. Fetch/extraction code is under `research/intervention_dynamics_renewal_20261022/`. The scout stops at five requests because the next substantive step would be a separately scoped source-header/graphical-design audit, not another broad search.

Exposure record: discovery abstracts, methods, relevant published results prose and the Fig4 caption including published statistical summaries were read. These are designer-visible literature, not sealed test evidence. No source outcome tables or newly parsed response arrays were opened. This bounded search does not establish that better qualifying resources do not exist.
