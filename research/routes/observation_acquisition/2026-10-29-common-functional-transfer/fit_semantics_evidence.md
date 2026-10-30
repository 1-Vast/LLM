# Local fitted-endpoint semantics evidence (C4; no functional-value consumption)

2026-10-29. Scope: existing local official code/documentation only. No network, package installation, author-code execution, functional CSV/fixture/data/RData read, raw assay read, or sealed/confirmation access. No protocol or endpoint choice changed. This is source inspection, not new experimental evidence.

## Provenance and version boundary

Original existing archive: `D:\MAESTRO\tmp\data2_github\CancerRxGene_gdscIC50_tarball.tar.gz`, **1,207,161 B**, SHA256 `66b1c464b754146d352c317cf7cf819752a4b4a41fcff4ce9b9f629bfbee23e6`, freshly rehashed, matches `research/2026-10-28-az-download-verify/data3_manifest.json`. Recorded official source `https://github.com/CancerRxGene/gdscIC50`. Tar root identifies commit prefix **34d8422**. `DESCRIPTION:1-3` identifies gdscIC50 **0.99.4**; `:10-17` describes sigmoid nonlinear mixed-effects curve fitting and the Vis 2016 method. `README.md:5` says this library and gdsctools generate website dose-response data/statistical analysis. **This does not establish that commit/version produced the 25Feb20 CSV.** No timestamp/lock/export mapping from that CSV to this package was located in this bounded inspection.

Source-only copies with original line numbering: `sources/fit_code/`; PDFs were text-extracted to `sources/fit_docs/`. Experimental `data/`, fixture/example contents, and `R/data.R` were not extracted. Source roxygen examples only reference example datasets; none were loaded. `sources/fit_source_receipt.json` records identity/read scope.

## Exact source evidence

All R file paths below are relative to `sources/fit_code/`. Short source excerpts are verbatim. Functions were read, never executed.

### 1. Concentration transform and IC50

`R/nlme_fit_prep.R:667-677`, functions `setMaxConc` / `setXFromConc`:

```r
mutate_(maxc = ~ max(CONC))
mutate_(x = ~ (log(CONC / maxc) / log(2)) + 9)
```

The maximum is over the function's `drug_specifiers` groups (`:669`); the default caller distinguishes dilution series using `DRUGSET_ID` and `lib_drug` (`:710-723`), with optional grouping of concentration ranges. Documentation `:687-689` explicitly describes maxc and screening concentration as **micromolar**, with maximum dose x=9.

`R/nlme_fit_stats.R:234-249`, function `getConcFromX`, documentation and implementation:

```r
#' to micromolar concentration
#' @param maxc the maximum micromolar concentration used in the dose response experiment.
xc <- maxc * 2 ^ (x - 9)
```

`R/nlme_fit_stats.R:63-67`, function `calcIC50`:

```r
IC50 = ~log(getConcFromX(xmid, maxc)))
```

Thus **this implementation's IC50 output is the natural log of the numeric concentration in µM**, computed as ln(maxc × 2^(xmid−9)). It is not the normalized log2 coordinate xmid. `R/nlme_fit_stats.R:364-367` additionally labels the plotted IC50 using `log[e]` and `mu*M`. The CSV name `LN_IC50` is consistent with that implementation but a release-specific export mapping was not found.

`R/nlme_fit.R:148-160` defines `logist3` as `1/(1 + exp(-(x - xmid)/scal))`, so xmid is the fitted half-response coordinate; `:89-105` explicitly requires y to mean relative kill **1−viability**.

### 2. MIN_CONC/MAX_CONC and extrapolation/censoring

**Proven in the inspected code:** maxc is max(CONC) within the specified grouping; x maps physical concentration logarithmically and makes maxc correspond to 9. `calcIC50` converts fitted xmid using the unrestricted expression above. `fitModel` calls `nlme::nlme` for xmid/scal (`R/nlme_fit.R:107-126`) with no observed-range bound in these calls; the inspected `calcIC50` applies no clipping to observed min/max. Its algebra permits xmid above/below the observed x interval, therefore an out-of-range fitted concentration is possible. This is a **source-logic inference**, not an observed dataset property.

**Not proven:** the exact CSV export definitions of `MIN_CONC` / `MAX_CONC`, whether these are per-curve or per-drug, any downstream release cap, censor flag, fit rejection policy, or confidence interval. A bounded text scan of non-data, non-test gdsctools source/docs found no `LN_IC50`, `MIN_CONC`, or `MAX_CONC` identifiers to close that mapping. No corresponding numerical values or missingness pattern was inspected. Do not equate fitted IC50 with a dose actually delivered; do not label this CSV unconditionally uncensored or infer that a fitted IC50 was experimentally reached.

### 3. AUC and fit quality

`R/nlme_fit_stats.R:70-81`, `calcAuc`, groups by CL/drug and uses xmin=min(x), xmax=max(x):

```r
auc = ~1 - (getIntegral(xmax, xmid, scal) -
             getIntegral(xmin, xmid, scal)) / (xmax - xmin)
```

`R/nlme_fit.R:224-238`, `getIntegral`, integrates the logistic function in transformed x; its expression is `b*log(exp(a/b)+exp(x/b))-a`. In this implementation the analytic auc is the **mean fitted viability over the represented log-concentration interval**, using y as relative kill. It is dimensionless and range-dependent. `calcAucTrap` (`stats.R:84-90`) separately returns `AUCtrap` by a trapezoidal calculation of 1−yhat. `calcNlmeStats` (`:127-137`) produces both. **Which output populates uppercase AUC in the 25Feb20 CSV has not been tied by an export contract.** Do not conflate fitted analytic AUC and trapezoidal AUC merely because both exist.

`R/nlme_fit_stats.R:93-100`, `calcNlmeFit`:

```r
yhat = ~ logist3(x, xmid, scal)
yres = ~y - yhat
RMSE = ~sqrt(mean(yres ^ 2))
```

RMSE is the root mean squared residual in the normalized response scale for that grouped CL/drug in this implementation. It is neither an IC50 standard error nor biological-repeat uncertainty, and it does not alone certify that 50% response lies within tested concentrations. No release-specific RMSE pass threshold was established. `Z_SCORE` semantics were not resolved in this bounded read.

## Existing official docs: corroboration with explicit scope limits

These four existing PDFs were identified through the local data3 manifest and read as documentation only; none is a release-specific dictionary for the 25Feb20 single-agent CSV:

- `tmp/data1_gdsc/Matrix_glossary.pdf`, page 1, extracted page-text lines 46-56: lib1_conc is highest screened concentration in µM; lib1_RMSE describes distance of data from the single-agent curve fit; lib1_IC50_ln is natural-log IC50; lib1_IC50_uM is µM. This supports conventions in a **matrix/combination release**, not automatic identity with the CSV.
- `tmp/data1_gdsc/glossary.pdf`, page 1, extracted lines 61-74: library RMSE, normalized log2 XMID, trapezoidal AUC versus integral fAUC are distinct fields. These are different field names/scales from LN_IC50; do not transplant without mapping.
- `tmp/data1_gdsc/Screening_documentation.pdf`, page 2, extracted lines 10-14: combination curves use a model with replicate nesting, exclude RMSE >0.2, and report Emax/IC50 from fitted curves. Page 3 lines 11-13 includes a combination synergy rule requiring combo_IC50 below twice highest screened concentration. This shows those docs contain **task-specific derived decision rules**, not a blanket censoring definition for the single-agent CSV. Neither the RMSE threshold nor twice-max rule is adopted here.
- `tmp/data1_gdsc/Matrix_documentation.pdf` offered no matching single-agent release export/units/censoring contract in the bounded term scan.

The extracted PDF text preserves page boundaries; line numbers above are per-page extraction line numbers, not native PDF line identifiers. Original PDFs remain untouched.

## Contract status for root

This read substantially supports the **package convention** natural-log µM IC50, log2 internal coordinate, model-derived AUC and response-residual RMSE. It does **not** close: exact 25Feb20 exporter/version, CSV MIN/MAX grouping and units, downstream censoring/capping, actual 50% reachability, or release-specific AUC/RMSE rules. HOLD is not automatically removed by finding an official fitting package. Root retains the protocol and scientific judgement; no functional values were consumed to resolve these gaps and no new endpoint is proposed.
