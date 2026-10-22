# State-refinement nearest-prior source authentication

2026-10-22. **The proposed state-refinement core has directly relevant established prior art; the two requested arXiv ID/title pairs are authenticated.** This finite audit establishes source identity and abstract-level operation overlap, not full algorithms or a proof that every possible refinement extension lacks novelty. No new model/dataset experiment was run.

After `PROTOCOL.md` registration, exactly two sequential requests returned HTTP200, no truncation, consuming **9,847 bytes** (arXiv 4,557; Crossref 5,290). Source bodies, headers/status/URL/UTC/hash, projections and freezes are retained here. No retry, replacement query, paper PDF/fulltext, numerical dataset or matrix acquisition occurred.

| Exact source | Actual returned title/authors | Evidence level |
|---|---|---|
| [arXiv cs/0406011v1](https://arxiv.org/abs/cs/0406011v1) | *Blind Construction of Optimal Nonlinear Recursive Predictors for Discrete Sequences*; Cosma Rohilla Shalizi, Kristina Lisa Shalizi; arXiv publication 2004-06-06 | Official author-provided paper abstract, primary abstract evidence; full methods not read |
| [arXiv 1207.4167v1](https://arxiv.org/abs/1207.4167v1) | *Predictive State Representations: A New Theory for Modeling Dynamical Systems*; Satinder Singh, Michael James, Matthew Rudary; arXiv publication 2012-07-11 | Official author-provided paper abstract, primary abstract evidence; full methods not read |
| [DOI 10.1016/0890-5401(87)90052-6](https://doi.org/10.1016/0890-5401(87)90052-6) | *Learning regular sets from queries and counterexamples*; Dana Angluin; Elsevier BV; publisher-deposited date 1987-11 | Crossref bibliographic metadata only; **abstract=null**, no full methods |

Both arXiv identifiers match the expected titles; no ID/title mismatch was silently corrected. The PSR source actually returned Singh/James/Rudary; authors from other familiar PSR papers are not substituted. arXiv upload dates are recorded as such and do not establish original proceedings publication dates.

## Exactly supported operational correspondences

**Predictive definition of state.** The PSR abstract explicitly says state is “a set of predictions of observable outcomes of experiments one can do in the system.” This directly precedes the candidate's idea of distinguishing current states through their future experiment-conditioned responses: using experiment-outcome predictiveness to define a dynamical state is already an explicit prior principle. The abstract also names a system-dynamics matrix and says PSRs can be derived from it. It does not give this audit the matrix construction, a sample-efficient discovery algorithm, controlled identifiability assumptions or an active experiment acquisition policy; those remain unverified at full-method level.

**Learning recursive predictive states from sequences.** The CSSR abstract explicitly introduces nonlinear prediction of discrete random sequences, construction of optimal predictors as hidden Markov models, and an algorithm named **Causal-State Splitting Reconstruction** that approximates the ideal predictor from data. It reports comparison with variable-length Markov and cross-validated HMM approaches. Thus recursively constructing/splitting predictive states from sequence data cannot alone serve as the candidate's new core. However, the abstract does **not** expose the exact state-splitting statistical test, suffix bookkeeping, minimality proof, action-conditioned/control extension, continuous morphology treatment, finite-sample guarantee or inherited feature procedure. The candidate's exact action-conditioned two-history counterexample rule is a correspondence to investigate, not an algorithm step proven identical by this abstract alone.

**Queries and counterexamples.** Angluin's exact title and authorship authenticate that learning regular sets “from queries and counterexamples” is a concrete established primary-paper topic, predating the candidate. This is legitimate bibliographic support for treating counterexample-guided learning as an existing comparison class. Since Crossref returned no abstract, this audit cannot claim it verified L* membership/equivalence queries, observation-table updates, counterexample handling steps, complexity or oracle assumptions. Those familiar details require a primary-method source before being cited as inspected evidence.

## What the audit does and does not resolve

These sources defeat a novelty claim based solely on “predictive state”, “history-sensitive state splitting”, “recursive predictor”, or “queries/counterexamples.” They do **not**, at abstract-only scope, prove an exact equivalence between every candidate implementation and CSSR/PSR/Angluin, nor validate a special continuous, noisy, controlled bacterial adaptation. Any advocate must identify an explicit additional operation and why its assumptions/data access differ materially; rebranding existing state reconstruction with a research-agent wrapper is insufficient.

The present candidate still owes evidence that it detects repeatable biological history aliasing beyond context/run and size+slope, that same-information full-history direct models or recurrent/state-space models do not explain a benefit, and that paid experiment choice/ordinary structure search cannot explain any gain. Neither source abstract mentions the candidate's program inheritance or common-start improvement-strategy evaluation; **absence in these short abstracts is not evidence that no broader literature covers those mechanisms**. This block provides no RSI novelty or performance result.

Useful next review questions, without authorizing further HTTP or implementation in this block:

1. Which precise candidate operation differs from a controlled predictive-state learner with ordinary feature/structure search and active system identification?
2. Does the operation exploit a real, measured intervention menu or merely improve a lossy chosen encoder?
3. What is inherited beyond weights, retrieved examples and fixed state distinctions, and how would common-start equal-budget tests isolate the improvement strategy itself?

Finite decision: preserve these three exact priors in the adversarial review and stop this two-request source block. Deepening the candidate is not justified by combining their names; root must decide from the distinct technical operation, suitable data and fair controls.

`VERIFICATION.json` records **18 PASS checks**: frozen protocol/acquisition hashes unchanged, two source status/length/hash/byte totals, faithful reparsing of stored abstracts, both expected arXiv ID/title pairs and exact Angluin DOI/title with absent abstract. These checks establish provenance and honest evidence scope, not scientific novelty or algorithm correctness.
