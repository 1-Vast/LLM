# Evidence Register

| Study | Status | Question | Result | Limitation | Reproduction path |
|---|---|---|---|---|---|
| Engineering closure | `VERIFIED_CONTRACT_ONLY` | Does the operational agent-to-measurement loop preserve request, budget, result and restart contracts? | Two-round execution, feedback and durable CaseStore behavior pass the asset-free contract suite. | Operational correctness does not establish biological validity or agent advantage. | `python -m pytest`; this is software contract evidence. |
| STATE zero-shot RNA prediction | `HISTORICAL_RESULT` | Does pretrained STATE improve RNA response prediction on checkpoint-held-out contexts? | M0 error 14.37 versus M2 error 8.50 (x10^-4), about 41% lower; all three evaluation contexts improve. | Only three context units; exposed later; RNA is not functional phenotype or mechanism. | Recover `research/astra/zeroshot_context_20261007/` from Git history at `540bc85`; source assets and receipts are not in this release. |
| Boundary acquisition | `RECORDED_RESULT` | Does boundary-aware acquisition improve the equal-budget result over KG? | M2 boundary, residual, design and no-stop all match KG: mean B utility 0.15966294 at 65 simulated profiles; no savings. | Five previously exposed contexts; simulated RNA endpoint, not independent cultures or phenotype. | Tracked packet at `research/astra/boundary_acquisition_20261007/packet2/`; recorded replay receipts are part of the source history. |
| MAP released-weight/native-forward audit | `BLOCKED/ASSET_MISSING` | Can the released checkpoint support an authenticated native STATE-SE RNA comparison? | A prior audit recorded strict tensor loading and a finite native forward; no response comparison was produced. | External weights, source, compatibility packages and Tahoe metadata are absent from a clean checkout; output order and training-time semantics remain unresolved. | `research/astra/map_release_test_20261008/ASSET_MANIFEST.json`; full replay requires the listed external assets. |
| STATE readout repair | `BLOCKED/ASSET_MISSING` | Does a drug-shared readout gain improve prediction and final selection? | Recorded development result: reference outer MSE improves 2.17%; five-target MSE improves 7.84%; final equal-budget selections match M2. | Development only; contexts previously exposed; Tahoe feature-name metadata is missing in a clean checkout. | `python -m tools.research_validation --verify`; requires the ignored result output and missing Tahoe metadata. |
| STATE joint-feedback repair | `RECORDED_RESULT; OUTPUT_REQUIRED` | Does joint A/B error feedback help prediction and acquisition? | Recorded result: matched-information reference utility rises 5.10%; adaptive target utility falls 0.87%; target posterior MSE improves descriptively. | Exposed targets and overlapping pretraining; no independent transfer or decision benefit; generated results are ignored. | `python -m tools.research_validation --verify`; current frozen trial chain is hash-pinned. |
| Decision value / no-screen | `RECORDED_RESULT; OUTPUT_REQUIRED` | Does screening earn its cost versus no-screen under strict complete-context LOO? | Recorded result: Joint KG is 0.0000544 above no-screen and uses eight additional measurements; strict EVSI refuses purchases. | RNA-only utility, 43 evaluable reference contexts, no independent model-risk or cost contract; generated results are ignored. | `python -m tools.research_validation --verify`; packet at `research/astra/boundary_acquisition_20261007/packet2/`. |
| Risk-calibration failure | `BLOCKED/ASSET_MISSING` | Can the fixed policy certify useful marginal and conditional decision risk? | Recorded result: no conditional threshold is certified; marginal coverage is 2.6% to 3.4%, below the 20% gate. | Exposed, class-stratified units do not establish the IID deployment assumption; prepared inputs are ignored local outputs. | `research/viability_contrast/run10.py`, `verify10.py`; clean-checkout prepared inputs are unavailable. |
| MAP-KG knowledge-layer content | `VERIFIED_CONTENT_ONLY` | Does the cached knowledge representation retrieve known targets better than structural controls? | Knowledge hit@5 is 11/44; molecule encoder 9/44; Morgan fingerprints 13/44; identity permutation 1/44. Explicit-mode hit is knowledge 6/30 and Morgan 6/30. | Graph exposure during encoder pretraining is possible; unknown annotations are not negatives; protein shared-space, RNA utility and agent benefits are not tested. | `research/knowledge_layer_validation_20261009/`; requires pinned public tables and the two ignored released feature/identity caches. |
| MAP feedback replacement and scarcity | `VERIFIED_DEVELOPMENT; GATE_FAILED` | Does knowledge-conditioned feedback improve matched-budget RNA selections, including sparse historical labels? | Full-history knowledge mean B is 0.164912 versus empirical 0.164965. With eight histories, knowledge exceeds empirical by 11.17%, but does not reliably exceed molecule, Morgan, shuffled knowledge or no-screen. | Unchanged pretrained STATE cache; exposed RNA development units; repeats grouped within backgrounds; reduced harmful updating is not knowledge-specific biology or net information value. | `research/map_module_replacement_20261009/`; response/scarcity verifier receipts require local ignored inputs and outputs. |
| MAP agent source acquisition | `VERIFIED_PROTOTYPE; REPLACEMENT_NOT_SUPPORTED` | Does typed context improve source qualification and bounded tool choice under missing records and noisy priors? | Easy task: all arms 12/12. Hard task: lexical 27/72 exact, typed 26/72, deterministic 72/72. Typed improves positive card/mode fields but schema and routing failures remain. | Repeated twelve exposed source cases; most violations are null Boolean fields under an underspecified prototype prompt; no measured engagement or whole-agent advantage. | `research/map_module_replacement_20261009/agent_trial/`; 456 retained actual provider calls, independent raw-source/output verification. |
| Released MAP protein and relation content | `VERIFIED_CONTENT_ONLY; PRIMARY_GATE_FAILED` | Does original shared-space and ordered fusion recover source-known targets better than simple controls? | Plain molecule/protein hit@5 is 3/44. Generic outgoing relation hit is 5/32, equal to structural votes and below popularity 6/32; incoming is 12/32. Canonical name anchors reach 25/32 and 26/32. | Possible graph pretraining exposure; target-enriched gallery; directions fixed and reported separately; native RNA decoder remains unauthenticated. | `research/map_module_replacement_20261009/asset_audit/`; genuine released tensor subsets, pinned text tokenizer and independent numerical verification. |

Historical research is intentionally reduced to Git-history recovery at baseline `540bc85`; it adds no independent support to these canonical claims.

## MAP-KG knowledge-layer audit — 2026-10-09

Fresh official-source inspection confirms MAP-KG revision
`2a9af1bd2645fef86fab495b85a1b08a52356e26` and MAP source
`629ebdc1617eaf89825185a1512d772eccc3dc7e`. The new experiment restores about
67.8 MB of drug nodes, drug-gene relations, gene nodes and pinned Tahoe drug
metadata. It verifies published LFS hashes where supplied and records byte
identities for every asset. The filtered release has 187,088 drug rows, 420,364
drug-gene rows and 22,923 gene rows; these are release counts, not substituted
paper counts. Gene rows contain 22,694 unique ENSG IDs; one-to-many mappings stay
explicit. All `ESM` entries equal gene symbols, not protein sequences or vectors.
The restored drug-gene table contains only Gene ID, Drug ID and relation text:
it lacks standardized dose, time, potency and per-edge citation fields. Some
original assay prose contains conditions and remains available verbatim.

Exact PubChem identity plus complete canonical isomeric structure matches 79 of 111
menu drugs (108 of 146 drug-dose candidates); 44 drugs have relations. All 111 structures
remain in the gallery, with dose duplicates removed and 37 component-containing
structures preserved. Original relation text, source asset hashes, row numbers
and gene-node matches stay bound to each assertion. Bind, inhibit, activate,
agonist and antagonist do not become equivalent or measured cell responses.
The frozen five-predicate parser deliberately leaves other phrasing unparsed,
including many explicit binding/inhibition descriptions. Its 91.46% global
`unknown` fraction describes limited parsing, not absent biological knowledge.

The new fixed top-five test uses authenticated cached official molecule256 and
knowledge1024 vectors at full dimension. It compares cosine retrieval with
Morgan2048 and a fixed whole-identity permutation, without training or RNA
outcomes. In this fixed gallery, knowledge produces 11/44 known-annotation hits,
versus 9/44 for the molecule tower, 13/44 for Morgan and 1/44 for permutation.
These are descriptive content-retrieval results. Matching
pharmacologic mode plus target is 6/30 for both knowledge and Morgan; source assertions with opposing
modes also occur among knowledge neighbors. Similarity does not authorize a
relation sign or make an unknown edge a negative. A posthoc annotation-ceiling
audit finds 18 of 44 gene queries and 20 of 30 typed queries lack any labeled alternative
in the entire gallery; denominators and models are not changed after this finding.

Six behavior checks and six independent verification groups pass. The verifier
reconstructs 146 identities, 176 queries, 880 neighbors and all metrics, reproduces
the prior strict-identity/relationship sets, verifies dose-vector bindings and
exactly repeats the scientific content audit. Previously saved target response
comparisons are also checked: all selected knowledge corrections remain disabled,
with final forecasts and decisions equal to M2. These local caches are generated
assets; a clean checkout must restore them rather than claim a new encoder run.
At this initial audit, the full weights, protein vectors and matching source
installation were absent. The subsequent module study below restores genuine
protein and relation subsets and tests them without substituting random weights.
The initial blocked receipt remains an accurate record of that earlier scope.

The [MAP paper](https://www.nature.com/articles/s42256-026-01286-w) aligns molecular,
protein and text attributes within entities, then uses ordered relation-conditioned
head/tail fusion. It does not simply cluster all related entities or certify
causal drug activity from cosine similarity. Published tests concern RNA response
and simulated pathway screening. They do not supply MAESTRO's functional bridge,
EVSI price or independent decision-risk calibration. Static inspection of the
released paths finds gene-gene sampling, concentration use and gene-projector
integration differences from the paper; these are reproducibility questions,
not claims about the authors' actual training execution. Full methods, figures,
supplement and exact code anchors are in `SOURCE_AUDIT.json`.

Keep MAP-KG as a candidate source-typed prior and retrieval aid for the agent,
with raw source rows establishing what the source asserts, rather than independently
verified biological truth, and embeddings retrieving possible evidence.
For STATE, a conditional response adapter would still need cell state, dose/time,
actual intervention support and measured validation. Shared vectors alone do not
repair posterior calibration, selected-decision risk, functional utility or
the economics of information acquisition. Neither a general agent benefit nor
new biological validity is established. No production architecture is changed.
Code/source audit: `research/knowledge_layer_validation_20261009/`; results:
`outputs/knowledge_layer_validation_20261009/`; receipt:
`log/20261009/KNOWLEDGE_LAYER_VALIDATION.json`.

## MAP module replacement and hard-task tests — 2026-10-09

This subsequent study separates representation content, purchased-observation
feedback and agent evidence acquisition. Every scored experiment binds its
protocol, code and inputs before outcomes; provider answers are frozen before
evaluation. The source cases and RNA packet were previously exposed. These are
development tests, with no new independent biological confirmation. All work
remains in `research/map_module_replacement_20261009`; no production module was
replaced. The canonical execution receipt is
`log/20261009/MAP_MODULE_REPLACEMENT.json`.

### Matched-information feedback and sparse history

The fixed STATE M2 prior, 146 dose-bound candidates, eight purchased A responses
and five committed B outcomes are shared across empirical covariance, full
molecule256, knowledge1024, Morgan2048 and a whole-drug-identity permutation.
Only the residual association kernel changes. Hyperparameters and all residual
moments use training contexts within strict whole-background outer LOO. Forty-three
complete reference backgrounds are evaluable; incomplete backgrounds are not
filled with artificial outcomes. The signed 39-gene RNA endpoint remains RNA,
not apoptosis phenotype or viability. Screening costs thirteen profiles versus
five for no-screen; no currency or functional net-value interpretation is made.

| Full-history policy | Mean final B RNA score |
|---|---:|
| No-screen | 0.161981 |
| Empirical matched feedback | 0.164965 |
| MAP knowledge matched feedback | 0.164912 |
| Molecule matched feedback | 0.163653 |
| Morgan matched feedback | 0.163585 |
| Permuted-knowledge matched feedback | 0.166099 |

Knowledge minus empirical is -0.0000523, nominal paired-context 95% interval
[-0.005526, +0.005421]. Knowledge lowers posterior MSE by 1.076%, but permutation
does at least as well. The adaptive KG secondary gives knowledge 0.166616 and
permutation 0.169292; it does not establish a knowledge-specific decision gain.
The registered development gate fails. A fresh numerical repeat reproduces
264 model arrays, 48 prediction arrays, model choices, all 528 result rows and
the scientific summary exactly. Independent verification reconstructs all
3,840 purchased-A receipts and 44 fitted model scopes.

The harder follow-up restricts historical labels to 4, 8 and 16 backgrounds,
using three fixed sampling seeds and nested history prefixes. All centering,
covariances and tuning use only the sampled history; STATE pretraining is
unchanged. There are 387 episodes and 2,322 policy rows. Each interval averages
the three seeds within a held background first: 43 units, not 129 independent
replicates per history size.

| Historical backgrounds | No-screen | Empirical | Molecule | Knowledge | Morgan | Permuted knowledge |
|---|---:|---:|---:|---:|---:|---:|
| 4 | 0.150522 | 0.120206 | 0.150057 | 0.150629 | 0.149942 | 0.150093 |
| 8, registered primary | 0.157716 | 0.142186 | 0.157714 | 0.158071 | 0.157597 | 0.157066 |
| 16 | 0.159817 | 0.150971 | 0.159927 | 0.159598 | 0.159605 | 0.159810 |

With eight histories, knowledge exceeds empirical by 11.17%, absolute interval
[+0.007961, +0.023810]. However, its differences from molecule, Morgan,
permutation and no-screen all have intervals including zero. At sixteen
histories it falls below molecule and no-screen. The primary gate fails.
Empirical small-history feedback increases posterior MSE by 20.4%; knowledge's
posterior movement is about 15.4 times smaller and preserves the initial top-five
set in 110/129 episodes. The credible development lesson is to restrain noisy
feedback, not to attribute gains to correct biological graph semantics.
Independent verification reconstructs histories, factors, hyperparameters,
15 comparisons and all 15,480 purchased-A receipts.

### Actual agent calls under bounded, difficult conditions

ChEMBL 37 supplies 105 retained public requests, 779,427 raw bytes and twelve
fixed full-structure cases, including two identity blocks, family assertions,
assay metadata and a real MAP/ChEMBL opposing-mode assertion. Salt, parent and
name fallbacks are forbidden. All arms receive the same available source tools.
The easy same-cards task uses 24 actual `deepseek-flash` calls: lexical retrieval,
typed context and deterministic classification all score 12/12.

The follow-up hides source records and adds real other-drug/same-gene distractors
in a second condition. Each episode may buy at most two distinct inspections
from identity, mechanism, assay, target and reference. Three fixed presentation
orders expose order sensitivity. There are 72 episodes per arm, 216 total;
the LLM arms make 432 actual calls with no response errors or truncation.

| Hard-task result | Lexical + LLM | Typed MAP + LLM | Deterministic same tools |
|---|---:|---:|---:|
| Exact complete packages | 27/72 | 26/72 | 72/72 |
| Positive complete packages | 0/24 | 0/24 | 24/24 |
| Correct positive source-card field | 13/24 | 18/24 | 24/24 |
| Correct positive reported modes | 19/24 | 24/24 | 24/24 |
| Source inspections | 144 | 144 | 132 |

Both LLMs always select identity then mechanism, including blocked identities
and requests needing an assay. All identities are inspected; uninspected
identity/card assertions and cellular/independent biological overclaims are
zero in both arms. Most contract violations instead come from Boolean source
metadata returned as `null`: 36 baseline and 44 typed episodes have invalid
schemas. Both arms also mislabel unrelated family scope in six episodes and
miss every genuine conflict flag. The hard prototype prompt under-specifies
Boolean/false-versus-unknown semantics compared with the easy contract. This
limits attribution to the context method and prevents generalization to the
whole production agent. Typed context improves some positive source fields
and reduces prompt tokens by 22.37%, but does not improve complete-package
correctness or source-choice adaptation.

A separately frozen post-hoc research gate rejects invalid schemas and
unsupported affirmative claims; it never coerces `null` into biological false.
It admits 36/72 baseline and 27/72 typed packages, with severe positive coverage
loss. Admission alone does not repair acquisition. A distinct deterministic
renderer of already purchased evidence reaches 66/72 for each LLM trajectory;
the missing six Triclosan assay inspections remain unrecoverable. These are
offline corrections, not rescued LLM or MAP reasoning gains. Task-aware
deterministic routing already achieves 72/72 under the original two-tool cap.
Independent hard verification reconstructs all 216 answers, 420 actual source
inspections, 432 provider authorization packets and token/access metrics.

Across easy and hard tasks, actual recorded provider usage is 456 calls and
932,407 tokens. No authenticated tariff or provider price field is available;
monetary cost remains unknown. Reordered case repeats are robustness checks,
not additional biological samples. The source-qualification task does not
measure biological target engagement, RNA prediction or final campaign value.

### Genuine original molecule, protein and ordered relation encoders

Original gene/molecule projector storages and 1,241 released ESM vectors are
restored through bounded range downloads. Both projectors load strictly; the
molecule head reconstructs the original cached knowledge representation within
1.91e-6. Every raw member has a recorded source, size, CRC and local hash.
An additional 470.5 MB restores all 222 original fine-tuned BioBERT, text-head
and ordered GatedFusion tensors with a pinned tokenizer. No generic text model
or random projector replaces the released weights. Subset integrity does not
authenticate the SHA256 of a complete multi-GB checkpoint.

The fixed protein gallery has 241 unambiguous known menu targets and 1,000 global
distractors. Twenty-one unresolved target IDs remain in recall denominators.
Plain molecule/protein cosine gives 3/44 known-drug hit@5, below molecular-neighbor
votes 7/44 and query-excluded popularity 9/44. This narrower cosine assay is not
the full MAP objective, so a separate registered experiment uses original
relation-conditioned fusion, both prescribed directions and canonical name
anchors. Generic relation text contains no target names: 32 queries from thirty
drug identities. Macro averages group queries within drug identities.

| Generic relation arm | Query hit@5 | Drug-macro hit@5 |
|---|---:|---:|
| Outgoing molecule + relation to protein, primary | 5/32 | 16.67% |
| Incoming molecule to relation + protein | 12/32 | 40.00% |
| Outgoing canonical name anchors | 25/32 | 78.33% |
| Incoming canonical name anchors | 26/32 | 81.67% |
| Relation only | 1/32 | 1.67% |
| Permuted relation | 4/32 | 13.33% |
| Permuted protein | 0/32 | 0.00% |
| Molecular-neighbor exact-relation votes | 5/32 | 16.67% |
| Query-excluded exact-relation popularity | 6/32 | 18.33% |

The registered primary gate fails: outgoing modality composition ties structural
votes and falls below popularity. Incoming modality composition and especially
canonical name anchors give a legitimate positive known-graph content signal,
reported separately without selecting the best direction after scoring. They
do not establish new-edge generalization, molecular biological activity or
STATE/agent replacement. Name anchors can retain pretrained identity knowledge.
The generic relation permutation has one inhibitor fixed point, which is kept
and disclosed rather than rerolled; it limits this control for inhibition.

The separate exploratory task retains 258 verbatim relation queries, including
target-naming prose. Outgoing modality hits 161/258, relation-only 94/258;
answer-bearing prose contributes and these results are not pooled with the
generic primary. Independent verification recomputes all nine arms, 2,881,602
scores, 46,440 ranked top-twenty records, source truth and both macro/micro metrics.
The native MAP RNA output axis remains blocked: released metadata still has
`hvg_info: null`, without an authenticated 2,000-gene order or matched training
forward. Representation restoration does not resolve this separate requirement.

The resulting dual-core direction is concrete: let knowledge retrieve candidate
evidence, compile source-authorized assertions deterministically, choose source
tools according to the requested question, and constrain noisy downstream
feedback. A unified vector space provides useful content in some settings;
it does not by itself supply calibrated decision uncertainty, a functional
utility bridge or profitable information acquisition. None of these trials
justifies replacing the existing world model or promoting a new agent policy.
