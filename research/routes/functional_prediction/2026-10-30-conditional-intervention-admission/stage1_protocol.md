# Stage 1: does chemistry add information about conditional sensitization?

Status: frozen initial pre-label proposal, 2026-10-30; requires independent challenge before outcome access. This is a development-only information test, not an exceptional-benefit claim or a new algorithm. No primary held-out drug outcomes are released by this protocol.

## Scientific question and native endpoint

Can a compound's pre-existing molecular structure prioritize its native published chemical-genetic sensitization calls beyond the history of frequently called genes? This tests a prerequisite for predicting conditional vulnerabilities without measuring a new compound's genetic-response panel. It does not identify a direct target or a causal pathway, and does not establish drug-combination efficacy.

Use the author's Table S1E calls: FDR <0.05 and CRANKS score <0. Negative scores mean sensitizing/synthetic-sick-lethal calls. The outcome is recovery of an author's significant call; a non-call is not a demonstrated biological negative. CRANKS is a dimensionless essentiality-matched rank-tail contrast, not a four-term log-fitness effect. No actual-viability-gain or calibrated false-positive claim follows.

Author Table S2 applies an incompletely documented chromosome-7p artifact correction; a milder 21q artifact is also described. The primary diagnostic excludes both arms using an existing public HGNC annotation and unambiguous symbol/previous-symbol identities, fixed before labels. This conservative mask is not the author's unknown correction list and does not certify absence of global preprocessing leakage. The fixed processed-label diagnostic cannot establish prospective label-construction independence; that remains a separate admission limitation.

## Fixed identity and information contract

`identity_freeze.json` and `identity_split.tsv` were produced from author identity/structure metadata only. There are 374 eligible single-compound molar screens from rounds 0–8; one deterministic first round/screen per compound supplies 294 representatives. Structure-standardized Bemis–Murcko groups ignore chirality, keeping all acyclic compounds together. A salted group hash fixes 231 development compounds in181 scaffold groups and63 untouched held-out compounds in59 scaffold groups. Development has three fixed scaffold-group folds (70/97/64 compounds). All related compound IDs, doses and co-cultured sequencing samples remain grouped; they do not become independent extra examples. Round9 hypothesis-driven screens and co-treatments are excluded.

Only development-compound call rows may be decoded or used. Other doses/screens of those development compounds may support descriptive exact-dose repeat checks, but not extra model examples. The63 held-out compounds' calls and numerical S2 values remain unread/unscored. Header/identity projection and bytes/hashes are already exposed; this is controlled numerical access to public files, not secure blinding.

Admissible features are fixed source SMILES Morgan radius2/1024-bit fingerprints with chirality; standardization/grouping precedes outcome access. Primary test uses structure only. Dose is a known identity/eligibility field, not a post-treatment phenotype feature. All target screens used author-selected proliferation-inhibiting regimens, so success would apply to those assay conditions rather than arbitrary doses. Compound classes/subclasses, post-treatment doubling counts, hit counts, CRANKS2 and annotations inferred from CGI profiles are not features. No gene-target, expression or costly assay embedding is added.

## Fixed lightweight comparison

Train one binary called-sensitizer profile per compound over matrix gene identities outside the fixed artifact mask. Gene eligibility and rarity are source-fold-only: at least one training call and calls in no more than10% of training compounds. The evaluation predicts previously seen gene identities for a new scaffold; it does not test unseen genes. If fewer than20 eligible genes exist in any fold, stop before fitting and report inadequate support.

Primary metric: P@20 for recovering rare called sensitizers, macro averaged over representative compounds, with source-derived gene eligibility fixed in each fold. Ties use lexical source gene identity. A held-out development drug with zero eligible calls stays in the denominator. Also retain per-compound counts, oracle P@20, all-call recall, concentration/round support and the number of source-eligible genes. These are call-recovery statistics, not physical sensitization magnitude.

Methods receive identical source compounds/calls and query structure:

- Historical gene-call frequency, with no query chemistry.
- Mean profile of the five nearest source compounds by Tanimoto fingerprint similarity (or all source compounds if fewer than five); ties use compound ID.
- Full-rank multioutput ridge on training-standardized fingerprints, with an intercept and alpha in {1,10,100}; predict binary calls and clip only to[0,1]. No low-rank bottleneck, module or network is introduced. Alpha selection is exploratory source-development selection, not a test result.

No method sees target response labels or a response probe. No unavailable LightGBM installation is requested. No dose-specific or biological-mechanism advantage is presumed.

## Conditional negative control and interpretation

Use49 predetermined permutations (NumPy default_rng seed20261030). Within each training fold and screening round, permute whole compound call profiles among compounds, keeping all genes in a profile together. Keep validation labels, features, folds, eligible genes and the frequency baseline fixed. Refit/predict the identical neighbor/ridge settings for each permutation; compare the maximum aligned-model gain over frequency against the maximum permuted-model gain. Report (1 + null maxima >= observed maximum)/50. This conditions on source-fold/round exchangeability, shared data and the selected model family; it is not a biological randomization experiment.

Bootstrap paired per-compound gains by complete scaffold group (2,000 draws, seed20261031). The selected model uses these same development folds; intervals are conditional exploratory summaries with selection and shared-training dependence, not population coverage certificates. Do not count genes or screens as independent drug experiments.

Stage1 can justify a later protocol only if the aligned maximum P@20 gain is positive and exceeds this conditional null at p<=0.05. Also report whether the paired exploratory interval excludes zero; an interval crossing zero prevents a robust-benefit claim even if the null is passed. No uniform exceptional-gain threshold is applied here. Use development baseline, oracle headroom, observed repeat support, candidate count and actual assay-cost gaps to plan a separate practical threshold before any63-drug held-out access. Missing physical-effect/noise or cost evidence limits that plan and may stop admission. The diagnostic may end negatively without a new model or a replacement route.

## Execution and retention

One bounded development comparison in direct maestro, maximum four threads and30minutes; no packages, test-score tuning, protected outcomes or core promotion. Metadata preparation's first RDKit call failed because FragmentParent lacked initialized ring information; explicit sanitization fixed it before identity freezing. That was a metadata-only correction, not a model rerun. Preserve the initial protocol, independent initial objections, pre-score amendments, source hashes, actual run/configuration/usage and all outcomes. Overall goal remains ACTIVE / NOT_ACHIEVED.
