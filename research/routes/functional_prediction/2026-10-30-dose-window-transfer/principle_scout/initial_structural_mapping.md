# Candidate-unexposed structural map

Date: 2026-10-30. Written before source acquisition or reading prior scout findings. Exposure: supplied brief, source-scout instructions, and parent structural description only; no current candidate draft, HTS003/031 treatment counts, or model fitting. Requested configuration inherited; effective model/effort/cost unknown.

## Observation and decision

An observation is background b, compound j, concentration c, elapsed time t, technical well r, and a cell count N, with a corresponding vehicle trajectory. The prospective user needs a compound choice in a specified in-vitro concentration window for a new background or intervention. A usable prediction is an ordering or pairwise growth-unit difference at matched concentration/time support, with selection loss against observed alternatives. Technical wells are not independent cultures; labels do not certify culture independence. Count changes alone cannot identify cell death.

The unresolved issue is which information is available for a new background: baseline measurements/vehicle only, measured responses to a fixed calibration panel, or a partial curve of the queried drug. These define different learning tasks and costs. A background identifier alone cannot support an unseen-background effect without some exchangeable population assumption or observed descriptor. Unseen compound transfer additionally needs a compound descriptor, calibration observations, or an explicitly restricted shared pharmacology assumption.

## Principle hypotheses before donor inspection

1. Learn a task-specific function from a small observed context set, then predict unobserved dose/time queries. A latent family shared across backgrounds could borrow information, but ordinary hierarchical curves, kernel regression, Gaussian processes, or low-rank completion may already implement the useful operation. The intervention panel must be fixed using development information only; its acquisition cost must be charged.
2. Separate what is stable across environments from what changes, using measured perturbations to identify transferable response relations. This needs either known environment shifts or sufficient calibration; causal invariance does not follow from background labels, and compound/dose changes are interventions with potentially different mechanisms.
3. Learn decisions directly from comparisons in the supported dose window, using a surrogate tied to wrong compound selection. Rank crossings mean global drug order or dose-averaged area may erase the actual decision. Ordinary pairwise or utility-weighted regression remains a direct rival.
4. Infer dynamics from controlled trajectories. Vehicle normalization can express net growth inhibition, but sparse count trajectories and unobserved cell states make a mechanistic state model non-identifiable. State observability and excitation, rather than a dynamics architecture name, determine transfer credibility.
5. Use uncertainty and support to abstain where a window is unmeasured or the background lies outside calibration. This can change deployment decisions even without an accuracy gain, but conformal guarantees need exchangeability at the biological grouping level and do not create new independent cultures.

## Success and decisive failures

Any donor must change a concrete input, comparison, endpoint, stopping rule, or test. Evaluate against ordinary curves with the same prospective information, support, training sources, and calibration cost. Freeze whole-background/compound grouping before outcomes. A useful result requires lower held-out compound-selection loss, with headroom over ordinary interpolation and stable direction across genuinely distinct held-out units. A renamed factorization or an accuracy gain caused by extra calibration is not a distinct learning mechanism.

Decisive generic falsifier: under a matched-cost, whole-background split and fixed supported concentration/time windows, a source-only selected donor mapping fails to improve compound-selection loss over the best ordinary hierarchical/kernel/curve baseline, or its gain disappears when its extra calibration information is supplied to that baseline. This supports ordinary modeling as the usable operation and stops a mechanism claim.

## Search intent and budget

Reuse the prior episode transfer/scout_notes.md and the project source library. Inspect original method passages for the few closest operative principles; favor relevant 2025-2026 originals already available. At most one narrow donor query/direct follow-up, six new source requests and 5,000,000 completed response-body bytes shared within pass 7. No model fitting, new dataset download, shared-index edits, or external messages.
