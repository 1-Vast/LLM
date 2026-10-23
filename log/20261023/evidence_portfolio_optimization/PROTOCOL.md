# Paid scout feedback: exposed Jaaks feasibility diagnostic

Question: does adaptive allocation improve the number of pairs positive on both purchased validation plates at the same total well proxy cost?
Rule: scout-based ranking must improve by at least 20% over fixed ranking with the same scouts, with a positive paired SIDM-bootstrap difference, and outperform direct final acquisition at equal total cost.
Result: pending execution; this file and code are frozen before this study converts response fields.
Decision: developmental feasibility only; no protected asset opening.
Does not show: latent true hits, FDR control, clinical utility, world-model necessity, agent value, inheritance or RSI.

## Data and isolation

Use only the fully exposed Jaaks original and validation fitted CSVs. No AZ numeric data or reserve is read. Units are SIDM, anchor ID, float-normalized scalar anchor concentration and library ID. Exclude missing/invalid identity fields or multi-anchor pipe-delimited IDs/concentrations as metadata-only out-of-scope records. Metadata-only eligibility requires an original row and distinct validation plates in both roles. Assign each validation BARCODE globally to scout or final by SHA256(`portfolio-role-v1:` + BARCODE), modulo 2. Within each unit/role choose the minimum SHA256(`portfolio-read-v1:` + unit + `|` + BARCODE), without reading outcomes. Require no original/validation barcode overlap and one SIDM per validation plate.

The original score is the mean original SYNERGY_DELTA_EMAX, first averaging finite duplicate rows per unit/plate, then averaging plates. Nonfinite scores rank last. Only selected scout responses are converted before choices are persisted. Final response conversion occurs after immutable choices are saved. Duplicate rows at a selected unit/plate are finite-averaged; all-missing selected reads count as no observed positive, remain charged and are never replaced.

## Fixed policies and cost

Let K be the metadata-eligible pool, S = floor(0.4 K), F = floor(0.2 K). All scout policies pay for the same S units ranked by original score. They then purchase F final reads from those scouts, ranked by:

- fixed: original score;
- feedback: scout score;
- mix (descriptive): equal average of ordinal original/scout ranks;
- random (descriptive): a fixed hash order.

The strong cost comparator (direct) purchases both scout-role and final-role reads for the top D = floor((S + F)/2) units ranked by original score, without using scout feedback for its choices. An odd leftover read is charged as a scout-only read on the next original-ranked unit. Every policy pays exactly S + F reads at seven combination wells/read, including missing reads. This is a well proxy: shared controls, plate capacity and turnaround overhead are not modeled, so it does not demonstrate executable wet-lab campaign economics. In the archive, source processing may share monotherapy fits across screens; barcode separation does not prove independent cultures or normalization.

## Endpoints and inference

Primary utility is repeat-positive count, requiring BOTH purchased scout and final SYNERGY_DELTA_EMAX > 0.10, per 1,000 planned proxy wells. The threshold is fixed before conversion in this study and is not an assertion of clinical significance. Also report repeat-positives at > 0, final-only positive count, repeat-positive fraction and missing reads descriptively. Missing either purchased read is no observed repeat-positive. Scout positives alone are not confirmed outcomes. No likelihood, e-value or fitted model is used.

Use one fixed plate-role split, no outcome-dependent seed/threshold/budget search. Report paired 95% percentile-bootstrap differences over whole SIDM clusters (2,000 draws, seed 20261023), retaining all units and outcomes in each sampled cluster. This is uncertainty conditional on the exposed, validation-selected candidate pool and fixed choices; it is not prospective policy uncertainty or cross-drug external validation. SIDM clusters do not address all shared-drug dependence. No replays count as new biological tasks.

Pass only if feedback/fixed primary count >= 1.20, feedback-minus-fixed lower interval > 0, feedback primary count exceeds fixed pair acquisition and feedback-minus-direct lower interval > 0. Otherwise stop this scout budget/ranking configuration. This does not reject other allocations or the evidence-portfolio family. A structural upper bound is F repeat-positives for any scout policy; report it against the direct arm, without treating hindsight final labels as an allocation oracle. No reserve opening or production promotion follows automatically from a pass.

The initial final-only acquisition design was mathematically set-dominated and rejected before freeze or response conversion. This protocol defines a different, explicit two-read repeatability task; see [pre-freeze revisions](PRE_FREEZE_REVISIONS.md). It cannot support a claim that feedback beats direct acquisition on single-read positive counts.

## Storage

Code and tests: `research/evidence_portfolio_optimization_20261023/`. Metadata selections, detailed choices and outcomes: `data/processed/evidence_portfolio_optimization_20261023/`. Key reports, result summaries, hashes, reviews and decisions: this `log/` directory. See the independent statistical, evidence and primary-source reviews and cross-discussion records here.
