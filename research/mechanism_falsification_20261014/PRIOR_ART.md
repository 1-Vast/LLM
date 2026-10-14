# Prior art, assumptions and novelty

**Verification levels, stated because they differ.** `RECALLED`: from background knowledge of the literature, not
re-fetched in this session; the claim is stable and well known but the citation details should be checked before
any external use. `ABSTRACT`: confirmed from a search result or abstract page this session; full text was not read
(several publisher pages were paywalled or redirected). `LOCAL`: confirmed in this repository. One related method
named in the brief (PIE) could not be located and is **not assessed**. Nothing here was read in full text, and no
novelty claim below should be stronger than that.

## 1. Techniques, what each assumes, and where it breaks here

| Technique | Source | Level | Assumes | Where it does not hold in this problem |
|---|---|---|---|---|
| Conformal selection | Jin and Candès, JMLR 2023 | RECALLED | calibration and test units exchangeable; selection by conformal p-values + BH controls FDR for the *test* null set; PRDS holds for the p-values (Bates et al., Ann. Stat. 2023) | compounds cluster by mechanism family; family shift is the point of the test; pairs of one compound are correlated |
| Weighted conformal selection | Jin and Candès 2023 (covariate shift) | RECALLED | P(Y\|X) identical in calibration and test; density ratio known or well estimated | a new mechanism family changes P(Y\|X); weights on X cannot repair that (see the simulation) |
| Weighted conformal prediction | Tibshirani et al., NeurIPS 2019 | RECALLED | same | same |
| Split-conformal intervals | Vovk et al.; Lei et al. 2018 | RECALLED | exchangeability; gives marginal coverage per unit | coverage is not FDR: selecting on interval position has no FDR theorem |
| Benjamini-Hochberg | 1995; Benjamini-Yekutieli 2001 | RECALLED | independence or PRDS | clustered units |
| Knockoffs | Barber and Candès, Ann. Stat. 2015 | RECALLED | model-X knockoffs need the feature distribution | not applicable: units are not features |
| Provenance model | W3C PROV-O (2013) | RECALLED | `wasDerivedFrom` chains are honestly recorded | the chain is the registrant's assertion; bytes are authenticated, meaning is not |
| Evidence typing | Evidence and Conclusion Ontology (ECO) | RECALLED | evidence type is assigned by a curator | a type string is not an assay |
| Packaging with digests | RO-Crate (Soiland-Reyes et al., Data Sci. 2022) | RECALLED | manifest lists files with checksums | RO-Crate does not say whether an asset is authentic upstream |
| L1000 / CMap | Lamb 2006; Subramanian et al., Cell 2017 | RECALLED | signatures are reproducible within cell line and time; connectivity is a similarity score | knock-down at 96 h or later and compound at 6/24 h are different points of the response |
| Signature embeddings | FRoGS (Chen et al., Nat. Commun. 2021) | ABSTRACT | gene-function embedding improves signature matching | an embedding is a similarity model; it does not supply independent truth about engagement |
| Perturbation-prediction benchmarks | Ahlmann-Eltze et al., Nat. Methods 2025 | RECALLED | simple baselines can match deep models | supports building a baseline arm into every comparison, as this repository does |
| Knowledge-graph perturbation models | TxPert (2025 preprint), MAP-type KGs | ABSTRACT | graph edges carry mechanism information | edges come from the same curated databases as the Hub annotations (see census): not independent evidence |
| Target validation by genetic loss | Lin et al., Sci. Transl. Med. 2019 | RECALLED | removing the putative target should not change sensitivity if the drug acts off target | needs the sensitivity readout *after knockout*; none is local |
| Biophysical engagement | CETSA (Molina 2013), TPP (Savitski 2014), PISA (Gaetani 2019), kinobeads (Bantscheff 2007) | RECALLED | measures binding or stabilisation in a lysate or cell | assets for these are staged but empty locally (census) |
| Strong inference | Platt, Science 1964 | RECALLED | an experiment that can exclude an alternative | the idea the strict policy encodes (`exclude_alternatives`) |
| Negative controls | Lipsitch et al., Epidemiology 2010 | RECALLED | an outcome the exposure cannot cause detects confounding | the matched-null and decoy ideas |

## 2. Novelty matrix

Four classes: **E** established (published and well known); **D** domain adaptation (known method, applied to a
setting where its assumptions are checked and found to hold or fail); **I** integration or engineering (existing
ideas combined into a working, tested system); **U** unresolved question (needs data that is not available).

| Item | Class | Basis |
|---|---|---|
| Conformal p-values with BH for selection | E | Jin and Candès 2023 |
| Weighted p-values under covariate shift | E | same |
| Showing clustering plus family shift breaks the assumption on CTRP-style data | D | CONFORMAL_SIM, CONFORMAL_TRIAGE; exploratory, an application of known theory |
| Structural power limit `n >= m/(q k)` | E (arithmetic of the BH procedure) applied to this pool | CONFORMAL_TRIAGE |
| Hash-bound evidence receipts with lineage and prediction taint | I | PROV-O and ECO ideas, tested in `evidence_registry` |
| Independence groups computed from upstream experiment, unknown as one shared group | D | known issue of dependent evidence, enforced here |
| A decision that refuses GO until every *required* prediction has a measurement and a human approval is bound to the evidence digest | I | `strict_decision_review` |
| No-signal NO_GO only through a registered rule, an authenticated receipt, context and prediction match | I | same |
| Evaluator contract C1-C7 as executable functions | I | converts a prior audit into code |
| Evidence-boundary benchmark with a provider-free scorer | I | `benchmark.py`; conformance test of a specification, not a scientific measurement |
| Does knowledge-graph-conditioned reasoning falsify wrong mechanisms better than not using it, with independent mechanism truth? | **U** | needs measured positive and negative mechanism references; none local |
| False-rejection rate of a mechanism-falsification rule on true mechanisms | **U** | same; at least 29 independent positives for a zero-failure 10 percent bound |
| Whether compound-to-genetic-perturbation signature agreement carries mechanism beyond class membership | **U** | earlier MAESTRO blocks found class membership explains the gain |

## 3. What this study does and does not add

It adds repaired contracts and a refusal-first benchmark. It adds no new inferential method and no new claim about
mechanisms. The only candidate for a scientific contribution, a calibrated mechanism-falsification rule, sits in
the **U** rows, and the census shows why it cannot be studied here.
