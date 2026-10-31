# Mechanism-development handoff

2026-10-31. Full analysis: `developer/mechanism_analysis.md`. Initial pre-scout framing: `developer/initial_mechanism_framing.md`. Requested Astra/MAX; effective settings unknown. This is development, not independent review. No HTTP, response-value inspection, author-code execution, fit, simulation or external model call.

## Precise conditional question for independent assessment

Can a biologically specified class of human RNA regulatory changes preserve **relative drug effects among competing splice choices**, so that source drug responses and target untreated choice frequencies predict the target treated distribution? The intended output is a new context/combination for a previously measured choice set, not a previously unmeasured exon, unseen drug, affinity or kinetic rate.

The candidate biological object is a closed local set of mutually exclusive alternative donors at a common acceptor. Arbitrary cassette-event PSIs are not such a distribution. The substantive unknown is whether an intervention class can be specified independently of the held responses for which a common relative drug-action vector is valid. U1C depletion acts on the drug-compatible complex itself, so it does not automatically satisfy that condition.

## Constructive case and exact equivalences

Let `p` and `p'` be source untreated and treated choice distributions, and `q` the target untreated distribution. If the drug's relative choice-weight multipliers `a_j` remain fixed across contexts, then

`q'_j = a_j q_j / sum_k(a_k q_k)`, with `a_j` proportional to `p'_j / p_j` wherever source support allows.

For one drug-responsive choice T with multiplier `lambda` and two reference alternatives A and B:

`q'_T = lambda q_T / [1 + (lambda - 1) q_T]`;

`q'_A/q_A = q'_B/q_B = 1/[1 + (lambda - 1) q_T]`;

`q'_A/q'_B = q_A/q_B`.

Thus backgrounds with identical untreated A but different T can have different predicted suppression of A. This supplies an extra *joint* prediction beyond A's own baseline. It is a symbolic construction, not an observed outcome.

With T against one aggregated alternative, the rule is exactly `logit(q'_T) = logit(q_T) + log(lambda)`: the existing context-strength account. With several choices, it is exactly shared multinomial odds/compositional reweighting, not a new algorithm. Any one source pair admits such factors; only their transport supplies a testable restriction. A flexible ordinary predictor must receive the same entire choice-set information. Improvement over an isolated-exon model cannot establish the proposed biological law.

For any possible positive target treated distribution `r`, context-specific factors proportional to `r_j/q_j` reproduce it. Source responses plus target controls therefore leave the held response unidentified unless the invariant-factor premise is justified. Zero/unsupported source probabilities add a genuine estimation limit. A change of local drug action under U1C depletion is a concrete biological counterexample.

## Source-owned facts and strongest novelty threat

The original sources, directly read, are:

- **Ishigami2024**, `investigator/sources/ishigami2024.xml`, nodes 319–332: explicitly assumes sequence-specific drug effect E independent of other context factors, estimates allelic manifolds and notes significant contextual deviations. Nodes 405 and 697–754 already supply two branaplam interaction modes and context-strength/dose modeling. This already owns simple local-drug-effect transport.
- **U1C2026**, `investigator/sources/u1c2026.xml`, nodes 392, 439, 455, 538–601, 683–706: complex requirements, drug-by-U1C dose responses and newly unmasked targets already established; class-III suppression mechanism unresolved. Endpoint curves do not identify molecular affinity or rates.
- **Lenkeit2026**, `reference/papers/doi-10.1038-s41467-026-74594-9/supp-scsp_fulltext.xml`, nodes 797, 834, 904, 918, 1060, 1228, 1250–1284: U1 complementarity/structure, U1-mutant-by-drug target changes and XGBoost already established.

The strongest novelty threat is existing context-strength transport plus ordinary competitive/multinomial splicing models. No broader target novelty search was undertaken in this no-HTTP role. A restricted biological law might still be useful with ordinary inference, but current sources do not establish this law or its usefulness.

## Observation contract and smallest next distinction

The workbook's safe schema has 22 group-condition PSI columns, without explicitly replicate-numbered PSI fields. Root later acquired sample-labelled junction counts; no response rows were opened by this role. Historical DEDSeq text aggregates inclusion/skipping junctions into binary margins and unions junctions across samples; it does not authenticate a closed multibranch choice set or the paper-specific pipeline modifications.

First qualify a local choice set and treatment-independent support using identities and processing provenance. If that fails, the extra joint prediction cannot be tested. If it succeeds and a separate numerical protocol is reviewed, the smallest transport test withholds the entire target treated distribution while fixing multipliers from source vehicle/drug and using target vehicle. A selective competitor alteration that leaves the target recognition sequence unchanged would discriminate the competition account more directly than U1C depletion; such an experiment is not currently authenticated or authorized for execution. A successful endpoint prediction still would not identify a binding mechanism.

The development recommendation is to preserve this **incomplete scientific opening**, not to fit a learner now. The reviewer can assess whether a useful biological restriction remains beyond the exact ordinary equivalent, whether the proposed inputs identify its prediction, and what smallest observation could establish its applicability. The scout's scalar monotone rank test can falsify one null but cannot resolve those questions by itself.
