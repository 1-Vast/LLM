# Bounded final closest-prior refresh

Search date: 2026-10-31 Asia/Shanghai (receipt timestamps begin 2026-10-30 UTC). Purpose: check whether ordinary network prediction/completion precedents change the claimed contribution, and authenticate the soft-versus-hard matrix completion distinction. This is a directed refresh, not a domain survey or a proof of absence. Original responses and per-attempt receipts are retained beside this note. No downloaded code/model was executed.

## Sources and reading levels

1. **GiGCN: a network-based framework for uncovering synthetic lethal and viable genetic interactions**, Wang et al., 2026, DOI [10.1093/bib/bbag470](https://doi.org/10.1093/bib/bbag470), PMCID PMC13548324. Retrieved original XML from [Europe PMC](https://www.ebi.ac.uk/europepmc/webservices/rest/PMC13548324/fullTextXML), saved as `prior_gigcn_02.raw` (SHA256 `7fab8e97b889e022fea38fe4757061c69073e84f99793a4db7e7a7646c5db7b9`). Read Methods sec3–sec8 and section titles; did not read its result sections. Sec3.p6 uses gene biological-process similarity features; sec4.p1 frames signed GI link classification/ranking; sec5.p1 describes signed graph representation learning and a classifier. This is current primary evidence that neighborhood/topological prediction of GI classes is an established active family. It does not use A1's fixed raw drug/untreated contrast or establish an exact prior match to residual smoothing over untreated profiles. Dataset cardinalities and method settings in its Methods were visible; no EGI source result was exposed.

2. **Data Imputation in Epistatic MAPs by Network-Guided Matrix Completion**, 2015, DOI [10.1089/cmb.2014.0158](https://doi.org/10.1089/cmb.2014.0158), PMCID PMC4449711. Europe PMC metadata in `prior_search_04.raw` identifies a directly relevant older network/completion precedent. The fulltext request returned HTTP500; its 150-byte error body is retained as `prior_ngmc_06.raw`. No retry or alternate fulltext route was attempted. Reading level is metadata only; the title establishes that network-guided imputation/completion of genetic-interaction maps predates A1, but does not substantiate its equations, evaluation conditions or any exact equivalence.

3. **Spectral Regularization Algorithms for Learning Large Incomplete Matrices**, Mazumder, Hastie and Tibshirani, JMLR11(80):2287–2322, 2010. Read the original [JMLR abstract page](https://www.jmlr.org/papers/v11/mazumder10a.html), retained as `prior_softimpute_07.raw` (SHA256 `aa6528bf16794fc5c06b655dbb667713de6ce9698462e57791ae571d1887d299`). The abstract explicitly says SOFT-IMPUTE fills missing elements from a **soft-thresholded SVD**. This supports T4's nomenclature objection to v1 and supports the corrected “iterative hard-rank” label in v2. This source does not provide biological validation of A1.

## Query scope and limitations

All exact encoded URLs, statuses, timestamps, headers, hashes and body sizes are in `http_receipts.jsonl`.

- Attempt1: Europe PMC title/abstract phrase `genetic interaction` plus prediction and environment/context/network; first15 metadata records inspected (65 total returned matches).
- Attempt2: original GiGCN XML.
- Attempt3: exact phrase `differential genetic interactions` plus predict/network/matrix; both metadata matches inspected.
- Attempt4: `genetic interaction` plus predict/inference and kernel/`matrix completion`/profile; first20 metadata records inspected (32 total matches).
- Attempt5: environment plus `genetic interaction`/`differential interaction` and predict/network/completion, constrained to 2024-10-31 through2026-10-31; all13 metadata records inspected. The returned list includes irrelevant gene-association uses of the terminology and does not establish coverage of all conditional functional-screening work.
- Attempt6: NGMC XML, HTTP500.
- Attempt7: original JMLR abstract page, HTTP200.

No metadata record or unsuccessful search establishes absence of an exact baseline-neighborhood conditional-screening predecessor. Recent signed-network methods are related solving principles, not fair drop-in baselines under A1's restricted information contract. Adding them would expand the frozen experiment and is not requested.

## Consequence for the candidate

The refresh reinforces the protocol's claim that its computational ingredients are ordinary. It does not change the initial endpoint/noise objections, and it does not refute the narrow empirical question of whether this particular fixed smoother improves target-culture screening under this particular dense information budget. The only supported contribution after a favorable result would be incremental conditional screening evidence under that contract. No novelty PASS is issued.

## Actual HTTP use

7 counted attempts, 226,017 completed decoded body bytes, including the complete HTTP500 error body; 6 successes, 1 HTTP500, 0 redirect hops, 0 retries. No known partial body was recorded. These are completed decoded-body counts, not certified wire traffic. Same-origin attempts were sequential and at least one second apart. Unused challenger allocation: 3 attempts and7,773,983 bytes; only the coordinator may reallocate it. This review performs no further HTTP acquisition.
