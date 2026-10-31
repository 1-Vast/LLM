# Initial mechanism framing, before scout exposure

2026-10-31. Mechanism-development role. Requested Astra/MAX; effective runtime model/effort metadata unavailable. Written before opening `scout/handoff.md`. This is a reasoning artifact, not independent review or empirical evidence. Only the episode brief, root questions, investigator findings, and original Lenkeit, U1C and Ishigami article passages informed this framing. No outcome table, workbook, counts, fitted result, notebook output or protected outcome was opened. No HTTP, model call, author-code execution, fit or simulation occurred.

## What must be explained

The useful question is whether an RNA-drug team can predict an unmeasured exon response after a defined human cellular regulatory change, using a restriction that expresses something biological beyond a baseline-conditioned response curve. Merely rediscovering a U1C-by-drug interaction, a newly responsive exon, or a change in the apparent plateau is insufficient.

The source facts sharply constrain the opening:

- Lenkeit already alters U1 pairing while holding the target splice-site sequence fixed and changes drug-responsive exons; bulge-compatible structure, pairing and baseline inclusion already enter its scientific account and prediction. Original XML nodes 797, 834, 904, 918, 1060, 1104, 1228, 1250, 1279 and 1303.
- U1C2026 already observes loss of drug response, dose shifts, and targets unmasked after U1C knockdown. Its biochemical preparation supports a role for U1C and Helix H in branaplam action, while risdiplam is inactive in that preparation. Its proposed conformational explanation of class III remains unresolved. Original nodes 296, 392, 439, 455, 538, 549, 594, 601 and 683–706.
- Ishigami2024 already separates context strength from drug effect, gives quantitative sequence-dependent drug-action models and a two-interaction-mode account of branaplam, and shows why a dose shift can follow a context-strength change without a changed drug interaction. Original nodes 405, 697, 754, 926 and 932. Its kinetic-proofreading discussion is explicitly a hypothesis (node 950).

Thus neither a scalar latent strength, a second conformer, a sequence energy model, nor an ordinary interaction term is a new operative principle by itself. An endpoint fit cannot identify affinity, transition rates, occupancy or the number of conformers.

## Alternative biological objects to compare

**Drug-compatible U1-complex availability.** A regulatory intervention could change which U1–RNA structures are accessible and thereby alter compound action at a fixed RNA sequence. This is biologically plausible and source-owned as a proposed explanation. A proposed restriction would have to say how an independently known change in structure predicts another event or drug, without fitting an unconstrained event-by-context drug coefficient. Two drugs, one depletion and endpoint RNA do not themselves supply that mapping. A low-dimensional factorization can describe these observations without identifying structural populations.

**Competition among complete splice choices.** A reported cassette-event PSI is a ratio over paths, not a direct readout of target-complex occupancy. Regulatory depletion may weaken a competing splice choice and expose a drug-compatible target without changing the drug's local molecular action. The scientific object would be the joint distribution of mutually exclusive splice paths rather than a collection of independent binary PSI values. A local conservation/competition restriction could predict consequences for an alternative path with no direct drug motif. This is a different causal account from direct changes at the drug-compatible U1 complex. However, ordinary multinomial choice already implements the simplest version, and for a single target versus one aggregate alternative it reduces exactly to the existing context-strength/odds model. A genuinely additional prediction requires a measured multibranch choice set, authenticated exclusivity and a defined intervention that separates the competitors; event coordinates and marginal PSI do not establish those facts.

**Specificity preserved under compensating sequence/regulator changes.** If a target and a U1 change preserve the drug-recognized molecular complex, drug action could transfer between them even when sequence labels change. Lenkeit's compensatory structure experiments already motivate and partly realize this idea. A new predictive scope would require a prespecified, independently testable equivalence criterion for the full cellular complex. Equal H-bond score or a predicted bulge is not that criterion. This cannot currently be promoted by adding an RNA embedding.

## Constructive opening and limit

A restricted competition model has a transparent constructive case: if a finite set of genuinely mutually exclusive splice paths has baseline probabilities p_j and a drug multiplies a known subset's productive weights by factors a_j, then the predicted treated probabilities are p'_j = a_j p_j / sum_k(a_k p_k). Measuring a context's untreated path distribution and transporting source-learned a_j would predict all paths, including an unmeasured alternative's suppression. This is a symbolic thought experiment, not a fitted or validated model. Its enabling assumption is context-invariant, path-specific drug action within a closed choice set.

The same formula exposes the principal novelty and validity threat. With one drug-responsive path against all others, it is ordinary context-strength transport; with arbitrary path- and context-specific a_j it is unrestricted multinomial regression. U1C directly affects the drug-compatible complex, so invariance of a_j is particularly questionable for the available intervention. Treatment-dependent degradation and incomplete path detection also break the mapping from productive splice choice to mature RNA abundance.

The concrete missing step is therefore not an architecture. It is a justified, measurable biological restriction that decides *which part of a regulatory intervention changes the competitive denominator and which part changes local drug action*, and makes a new prediction when those parts are separated. The present sources motivate this distinction but do not identify it. A later scout lead may offer a better operative principle; no candidate is selected here.

## Present data boundary

Root reports an acquired U1C Supplementary Data 2 workbook with identities, sequences and group-condition PSI columns; the actual header check does not authenticate per-replicate PSI columns. No independent event-universe, junction-support or multibranch-path qualification has been established to this role. A larger table is not evidence that the above distinction is measurable. Lenkeit figure source data remain unsuitable as a complete counterfactual response panel without resolved contrasts, missingness and ascertainment.
