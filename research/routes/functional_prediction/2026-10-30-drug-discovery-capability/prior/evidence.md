# Closest-prior evidence: effect-coordinate surface portability

Date: 2026-10-30 Asia/Shanghai (request receipts use 2026-10-29 UTC). Frozen question: `review/paired_surface_question_v1.md`; version and ancestry unchanged. This is a bounded scholarly check, not a novelty clearance or admitted scientific test.

## Findings first

1. **An exact mathematical restatement is invariance of the entire interaction-residual surface at matched component effects**, relative to any common reference function of those effects. On an independently justified normalized survival/viability scale where the Bliss null is `N(u,v)=u*v`, the frozen restriction is exactly `H_R(u,v)-u*v = H_P(u,v)-u*v`. This is a direct algebraic deduction, not a claim that the inspected paper introduced parental-to-resistant transport. Equality of one summary synergy score or synergy at the same nominal doses is insufficient.
2. **A nontrivial ordinary MuSyC subfamily already expresses the restriction exactly.** In the published four-state model, setting both potency modifiers and both cooperativity modifiers to one gives product-state occupancy. Shared state-effect values `E0,E1,E2,E3` then give an identical surface in component-effect coordinates even when Hill potencies/slopes change. `E3` can differ from the Bliss-null value, so this overlap includes efficacy interaction rather than only a no-interaction special case. The derivation below follows the inspected original equations. It limits mathematical/model novelty; it does not establish empirical portability in the selected HPAC derivative.
3. **The broad assertion “shared MuSyC interaction parameters equal the frozen restriction” is unsupported.** The raw component-effect coordinate depends on monotherapy baselines/asymptotes as well as potency and slope. Equal alpha/beta/gamma labels alone do not establish equal `H`; a shared-parametric comparator needs its actual predicted `H` checked under the stated constraints. Conversely, arbitrary empirical monotone axis registration is more flexible than a finite-dimensional Hill model. Neither model contains the other without qualifications.
4. **Loewe dose equivalence and between-state axis calibration are different restrictions.** Pure horizontal potency scaling transports a Loewe null surface, but arbitrary monotone remapping need not. Ordinary single-agent nulls and a shared parametric surface are mandatory comparators, subject to endpoint and information compatibility.
5. **The specific empirical parental-to-resistant prediction was not verified as an existing published protocol in this search.** Only one selected original method paper was read. The search was too narrow to exclude earlier pharmacodynamic transport, differential-interaction or response-surface work. A new algorithm, biological mechanism, resistance-cause transfer or Agent advantage is not supported. The next decision remains a separately controlled metadata/admission inquiry; no outcome test has been done here.

## Inspected evidence and its limits

**P1, selected original full-text reading:** Wooten DJ, Meyer CT, Lubbock ALR, Quaranta V, Lopez CF. *MuSyC is a consensus framework that unifies multi-drug synergy metrics for combinatorial drug discovery.* Nature Communications 12 (2021), DOI `10.1038/s41467-021-24789-z`, PMCID `PMC8322415`. Original JATS received as `request03-musyc-primary.body` from Europe PMC's full-text service. Read selected body paragraphs Par3,5–11,38–43,49,51,58–61,64; Tables 1–2; Box 1/Eqs. 10–16; selected reference entries. Figure captions were extracted as text in the initial broad excerpt; images, supplements and author software were not read or run. This is selected original reading, not an exhaustive reading of all article components.

Decision-relevant passages:

- **Par6 and Table 1:** one-drug parameters distinguish baseline/asymptote, potency `C` and Hill slope `h`; two-drug parameters distinguish synergistic efficacy `beta`, directional potency `alpha12,alpha21` and cooperativity `gamma12,gamma21`. Table 1 defines beta using `E0`, the stronger monotherapy asymptote and `E3`. Therefore equal beta is not a universal statement that the same absolute combined endpoint is retained when monotherapy asymptotes change.
- **Box 1, Eqs. 10–16:** the one-drug Hill curve is `E=E1+(E0-E1)/(1+(d/C)^h)`. The four-state model specifies transitions among unaffected, each singly affected and doubly affected states, and calculates their endpoint-weighted mean. It supplies the exact subfamily calculation below.
- **Par8:** Bliss's multiplicative survival principle concerns independent survival probabilities. This paper states additional endpoint/parameter constraints for reducing MuSyC to that null. A percentage label alone does not establish that the HPAC CTG estimand is a survival probability.
- **Par9, Table 2:** Loewe/DEP concerns dose substitution and isoboles. This article's statements about equivalence to MuSyC are conditional, not universal.
- **Par38–43:** the authors describe geometric pharmacological interpretations and explicit model limitations, including Hill-shaped marginals/surfaces and concurrent administration. These are not established features of every empirical monotone response surface.
- **Par58:** Bliss/Loewe/HSA scores depend on concentration; a combination can change classification across concentrations. Matching a scalar score does not identify a full response surface.
- **Par60–64:** the article describes Zimmer's Effective Dose Model, Schindler's Hill PDE and GPDI as ordinary neighbors. These descriptions are evidence about what this MuSyC article reports; their original articles were not acquired in this batch.

**P2, metadata/abstract only:** Meyer CT et al., *Quantifying Drug Combination Synergy along Potency and Efficacy Axes.* Cell Systems 8 (2019), DOI `10.1016/j.cels.2019.01.003`, PMCID `PMC6675406`. Europe PMC record in `request02-targeted-search.body`. The abstract already claims decoupled potency/efficacy and uses MuSyC to examine a correlate of BRAF-inhibitor insensitivity. No claim about its exact transport protocol or its results beyond this abstract is made.

**P3, metadata/abstract only:** *Combined doravirine and islatravir cooperate to inhibit NRTI and NNRTI resistant HIV-1 in vitro.* Antiviral Research (2025), DOI `10.1016/j.antiviral.2025.106157`, Europe PMC MED `40254262`. The abstract describes monotherapy susceptibility and ZIP/MuSyC analysis across resistant variants. It establishes an existing application neighborhood involving resistance and interactions, not the exact frozen parental-surface prediction or an empirical refutation of it. Full original not read.

Reference leads recovered from P1, not independently read: Yadav et al., *Searching for drug synergy in complex dose-response landscapes using an interaction potency model* (ZIP), DOI `10.1016/j.csbj.2015.09.001`; Zimmer et al., *Prediction of multidimensional drug dose responses based on measurements of drug pairs*, DOI `10.1073/pnas.1606301113`; Schindler, *Theory of synergistic effects: Hill-type response surfaces as 'null-interaction' models for mixtures*, DOI `10.1186/s12976-017-0060-y`; Twarog et al., *BRAID: a unifying paradigm for the analysis of combined drug action*, DOI `10.1038/srep25523`; Wicha et al., *A general pharmacodynamic interaction model identifies perpetrators and victims in drug interactions* (2017; full identifier not verified here). They are bounded residual checks, not verified exact equivalents.

## Exact overlap and non-equivalence

### Whole-surface residual invariance

Let `N(u,v)` be any one fixed, justified reference in the same endpoint coordinates for both states. Define `S_b(u,v)=H_b(u,v)-N(u,v)`. Then `H_R=H_P` if and only if `S_R=S_P` on their qualified common domain. This identity means that describing the frozen question as preservation of the full effect-matched interaction surface adds no mathematical novelty. It does not say that a conventional reported synergy statistic is the entire function `S`, or that a reference written in doses becomes state-independent after remapping.

For Bliss, `N(u,v)=u*v` only under the requisite scale interpretation and common normalization. For HSA on a common decreasing response scale, `N(u,v)=min(u,v)` gives the same algebraic equivalence. These two residual definitions differ as synergy concepts, but equality of their full residuals across states has the same frozen content because each subtracts the same common function. This is not permission to call the unresolved CTG endpoint survival.

### An exact ordinary MuSyC subfamily

This is a symbolic deduction from P1 Box 1, not a data analysis or an attribution that P1 proposed the frozen transport test. With `alpha12=alpha21=gamma12=gamma21=1`, each drug's transition is independent of the other's state. Let its affected-state probability be `q1` or `q2`. The four state weights are `(1-q1)(1-q2)`, `q1(1-q2)`, `(1-q1)q2`, and `q1*q2`. Their measured endpoint is

`Y = E0*(1-q1)*(1-q2) + E1*q1*(1-q2) + E2*(1-q1)*q2 + E3*q1*q2`.

The monotherapies obey `u=E0+(E1-E0)*q1` and `v=E0+(E2-E0)*q2`. If `E0,E1,E2,E3` are common across parental/resistant states and the required inverses exist, substitute `q1=(E0-u)/(E0-E1)` and `q2=(E0-v)/(E0-E2)`. The resulting function contains no state-specific potency or Hill-slope parameter. It is exactly the same `H(u,v)` in both states, even if the dose-to-occupancy curves differ. An arbitrary shared `E3` permits synergistic/antagonistic efficacy relative to the applicable null.

This is sufficient, not necessary. Empirical `H` equality could occur outside this subfamily or only locally. The frozen empirical surface need not fit any Hill equation. Equal MuSyC beta/alpha/gamma with state-specific endpoint ranges is not this derivation. Do not silently equate sharing parameter names with sharing the exact function.

### Loewe and potency shifts

In standard Loewe notation, a combination effect `w` satisfies `d/m_b^{-1}(w) + a/n_b^{-1}(w)=1` where the required inverse levels exist. In component-effect coordinates its expression uses `m_b^{-1}(u)/m_b^{-1}(w)` and `n_b^{-1}(v)/n_b^{-1}(w)`. Under pure multiplicative dose scaling, each state-specific scale cancels in these ratios, so a common Loewe null transports. Under general nonlinear monotone remapping, ratios need not be retained. Thus being Loewe-additive in both states is not a general proof of effect-coordinate surface equality. Likewise one-direction interaction-potency parameters are established concepts but not a verified exact alias for arbitrary axis remapping.

## Adequate ordinary comparisons and next decision

| Comparator or alias | Relation to frozen question | Information condition |
|---|---|---|
| Deterministic parental surface readout after calibrated axis mapping | Exact implementation of the restriction; not an independent scientific model | Same parental matrix, marginals and interpolation/uncertainty procedure |
| Shared function of component effects | Exact mathematical description | Do not claim an established canonical literature name from this search |
| Entire effect-matched interaction-residual invariance | Exact algebraic equivalent for a common valid reference | Full residual function, not scalar differential synergy |
| Single-agent nulls: HSA, scale-qualified Bliss, qualified Loewe | Tests whether historical joint measurements add useful prediction | Same marginals; disclose scale/inverse restrictions |
| Constrained/shared MuSyC surface | Established parametric ordinary explanation; an exact subfamily overlaps | Estimate sharing constraints from parental data/calibration, never held-out resistant outcomes |
| State-specific or hierarchical surface; ZIP/BRAID/GPDI if appropriate | Ordinary alternatives, not verified exact aliases | Resistant diagnostics used for fitting must be charged and excluded from evaluation |
| Direct target assay; fixed panel; ordinary adaptive allocation | Required practical/policy rivals if later claims concern resource savings or Agent value | Same total information, assay cost and decision horizon |

Proceed only to the frozen question's source-schema/admission gate if independently authorized. A later test can determine whether empirical effect-coordinate reuse works locally and whether it improves multiple resistant decisions under equal costs. It cannot establish new dose-equivalence mathematics. Before any algorithm-novelty claim, inspect originals for targeted pharmacodynamic transport/differential-interaction leads; that is a separate bounded batch, not an inference from the absence of a hit here. “Differential synergy” is not verified as a method name for this exact restriction: the exact-phrase query mostly returned unrelated meanings. No new hypothesis, ancestry change or hypothesis co-design occurred.

## Search, access and resource accounting

Local reuse: searched `reference/papers.tsv` and README for MuSyC, differential synergy, dose equivalence, BRAID, Schindler, Hand, Zimmer and potency/efficacy. No matching relevant method record was found; an unrelated author named Zimmerman was returned. Library metadata reuse was read-only; its absence is not a claim about the literature.

Exact request URLs, HTTP headers, body hashes, byte counts and UTC timestamps are in the three JSON receipts. Original received body bytes are preserved alongside them.

1. `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=TITLE_ABS%3A%28MuSyC%20OR%20%22differential%20synergy%22%20OR%20%22dose%20equivalence%22%29&format=json&resultType=core&pageSize=25` — HTTP 200; 172159 actual body bytes; 247 reported hits, 25 returned, only selected relevant records used. Broad query was diluted by clinical dose equivalence; no further pages requested.
2. `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=TITLE%3A%28MuSyC%29%20OR%20TITLE_ABS%3A%28%22differential%20synergy%22%29%20OR%20TITLE%3A%28%22Quantifying%20drug%20combination%20synergy%22%29&format=json&resultType=core&pageSize=30` — HTTP 200; 77459 bytes; 9 reported/returned records; relevant method titles/abstracts inspected, music-trial and other irrelevant results excluded.
3. `https://www.ebi.ac.uk/europepmc/webservices/rest/PMC8322415/fullTextXML` — HTTP 200; 248158 bytes; selected original reading above.

**Actual batch totals:** 3 logical HTTP requests including redirects (3 successful responses; 0 redirects, 0 failures), **497776 actual read body bytes** of 6000000 permitted, no automatic retries, no bypass, 25-second requested timeout per request, actual elapsed times 2.853/2.383/3.973 seconds. Each request had a 2000000-byte read cap; every body completed below that cap. No further request was made. Date-bounded novelty coverage, comprehensive citation following and an independently read differential-synergy original were not completed; the three-request ceiling was reached.

No raw source outcomes, numerical target matrices, source archives, experiments, scientific tests, author-code execution, installations, charged APIs, other-agent dispatches or shared-report/library writes. Authored files are confined to this directory: this evidence note and the source/receipt files. Requested subagent configuration was gpt-6.1-sol / high with fork_turns none, as confirmed by the parent tool invocation; effective runtime configuration, token count and monetary cost are not exposed, so I do not certify them. Source download is not experiment replication or empirical validation.
