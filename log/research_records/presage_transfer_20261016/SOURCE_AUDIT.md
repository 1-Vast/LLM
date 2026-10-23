# Source, representation and prior-art audit

## Access depth and preserved bytes

The DOI identifies one paper. Official code was inspected at commit
`2c7b231c60cf110c4aab0acf8ecd2c2b3268fffb`, including model, data module,
training, evaluator, tutorial and download scripts. The original full-text URL
returned HTTP 429; Europe PMC records `isOpenAccess=N`, `hasPDF=N`. Consequently
no numerical paper finding, ablation effect or learning-curve sample size is
claimed verified. README/abstract statements about source dominance and early
saturation are author-reported, not independently reproduced here.

Source URLs, successful payload sizes/hashes and failed attempts are retained in
`source_review/RETRIEVAL.json`. Third-party code is retained for review under its
included Genentech non-commercial license; none is imported into MAESTRO runtime.
MDA and Centaur HTML were read for method/budget sections; TxPert was read at
abstract depth; MAP comparison uses the existing local literature/source record.

## What the PRESAGE implementation actually does

| Topic | Verified implementation | Implication for MAESTRO |
|---|---|---|
| Representation | `presage.py:512` prepares a tensor of gene embeddings. `read_and_embed` always computes training-response-transpose and training-coexpression embeddings, then appends configured external sources. | A source-labelled model can still use measured training responses; distinguish annotation priors from external perturbation responses. |
| External embeddings | `presage.py:648` reads pickle features, removes zero-variance columns, adds small random noise, centres/scales, fits PCA to the transposed matrix, and stores gene components. | This uses all shared embedding genes. Removing a held-out row afterward does not undo the geometry. Label-free annotation transduction may be permissible, but external response sources need full overlap audit. |
| Architecture | Per-source MLPs, configurable pooling (mean/vector/GAT), item MLP, optional trainable PCA decoder. Output PCA and response-derived embedding paths use training data. | Test source information with small linear adapters first; attention weights do not establish mechanisms. |
| Preprocessing | `datamodule.py:309`: filter genes/cells, total-normalise to 10,000, log1p, select 5,000 HVGs plus perturbed genes. Control-centred expression or pseudobulk is produced. | Feature selection precedes split setup in the visible path; full-dataset feature-axis assumptions must be declared. This is a code-path observation, not proof of outcome leakage in every paper configuration. |
| Splits | Split JSON supplies train/val/test perturbation labels; control cells accompany subsets. Visible dataset configs include K562, RPE1, HepG2 and Jurkat. Actual split JSON is distributed outside this Git tree. | No verified exact paper proportions, seed list or strict zero-shot overlap census. |
| Evaluation | `evaluator.py` implements top-DE Pearson, effect/virtual-screen, phenocopy and gene-set metrics. `perturb_geometric_preprocess` fits PCA/sphering on train+test ground-truth profiles for some geometric evaluations. | These are retrospective expression geometry metrics. Do not use them as an independent functional decision certificate or prediction-time normaliser. |
| Ablations / curves | Mean and weighted pooling and multiple sources are configurable. The Git tree does not supply the paper's complete numerical ablation/learning-curve outputs. | Source dominance and saturation remain qualitative author reports. No extrapolation from genetic response to drug viability. |

Zenodo API confirms `cache.tar.gz` is **3,392,114,905 bytes** and the distribution
contains derived `data`, `splits`, `pathway_embeddings` and `other_embeddings`.
A 2,000,000-byte HTTP 206 prefix was inspected without unpickling or extracting:
it starts with `cache/other_embeddings/A549_CP186.pkl` (248,228,466 uncompressed
bytes). The compressed stream ends inside that member. This is explicitly an
incomplete inventory. No 3.4 GB download, upstream all-dataset script, cache model
execution, or external-response feature was used.

## Sources admitted and refused

| Source | Version, upstream and permitted use | Responses, overlap and coverage | Preparation / cost |
|---|---|---|---|
| PRISM primary + metadata | Existing 19Q4 Broad Repurposing release, source paths/hashes in SOURCE_MANIFEST; existing repository source census records CC BY 4.0. Released replicate-collapsed log2 fold change, 2.5 uM. Exact per-row time not authenticated here. | Measured viability responses; previously exposed to MAESTRO studies. All same-connectivity compound responses withheld from training. 4,528 drugs, 568 authenticated-ID line rows; 2.57% missing responses. | Reuse existing local bytes; no response download. Broad-core aggregation collapses overlapping HTS/MTS upstream rows rather than counting them as independent trials. |
| PRISM targets / MoA | Metadata in same historical release; candidate annotations, not target engagement. Timing of original annotations relative to screening is not independently authenticated. | Labels, not new measured engagement. 1,795 target symbols. MoA/target overlap remains across folds; family and scaffold novelty cannot be assumed. | Tokenise only. Chemical/identity baselines see matching annotations. |
| Reactome_2022 | Enrichr gene-set-library derivative, byte-pinned response retained with URL. Original Reactome content is CC0; Enrichr derivative transformations/exact release are not independently rebuilt, and direct Reactome/license hosts returned 403. Research use only in this exploratory gate, no redistribution or commercial clearance claim. | Non-response functional membership; 1,818 sets. 1,528/1,795 target genes covered; 3,118/4,528 drugs have covered targets. Predates current study but postdates 19Q4; retrospective annotation availability declared. Does not contain PRISM outcomes. | 778,913 public bytes. Fixed random projection, individual row normalisation; no fitted all-entity PCA, feature selection or measured-response construction. |
| Retained compound census | knowledge_reality/compounds.csv; previously generated connectivity, family and fold metadata; byte-pinned. | No response values. Connected families sharing a connectivity unit are forced into one fold. Original giant-component family fallback allows target/MoA overlap. | Reused, no new cost. SPLIT.csv records actual components/folds. |
| Existing ESM cache (refused) | PROTEIN_FEATURES.npz, 1,241 genes, 5,120-dimensional ESM and 1,024-dimensional protein fields, historical SHA `9c16c362...` in orbit freeze. | Structural features nominally non-response, but exact checkpoint/sequence versions, pooling, upstream construction and potential MAP alignment are not fully authenticated by local receipts. | Already cached; sunk construction cost unknown. No predictive experiment uses its values. Do not infer qualification from the field name. |
| PRESAGE cache (not admitted) | Official Zenodo record; embeddings CC BY-NC 4.0, underlying response datasets largely CC BY 4.0, code non-commercial. | Includes measured perturbation representations and derived outcomes/splits, not just structural priors. Cross-system measurements of the same gene change the generalisation tier. Coverage and exact outcome overlap are unaudited. | Only bounded prefix and metadata inspected. Full download/storage/preparation/inference costs not incurred. |
| MAP/CCLE/text features (not admitted) | Existing snapshots and historical studies inspected. | No additional MAP response/target-text edge, PCA, CCLE normaliser or potentially phenotype-containing text representation enters this experiment. | No construction or paid inference. |

Label-free access to all query gene memberships, chemistry and MoA is transductive
metadata availability, declared in advance; no fitting on test responses occurs.
Training imputation/normalisation is fold-local. Gene-permutation controls move
98.1–99.3% of covered feature rows while preserving degree/count bins, missingness,
target sharing and MoA. A consistent renaming would leave predictions unchanged;
this experiment instead holds gene identities/edges fixed and moves their features.

The 568-cell-line menu excludes ten barcode controls **and ten failed-STR rows**
without DepMap IDs, entirely from metadata. Amendment A1 was motivated by an early
assertion involving controls; the full impact of its metadata rule is reported here.
This qualification is not an outcome-dependent observed-activity filter.

Independent-unit limits: family/connectivity clustering is used for uncertainty,
not as proof of independent culture starts. Processed PRISM values share pools,
batches and upstream processing. No same-assay reused release becomes a new
independent measurement. Drug ranking is a retrospective functional diagnostic.

## Novelty boundary

| Comparator | Overlap / legitimate comparison | Boundary |
|---|---|---|
| PRESAGE | Modular sources, small source-specific transforms, source ablations, functional expression evaluation. | Genetic expression, not a direct viability model. This linear drug adapter uses the same Reactome features as its matched controls, not the paper's cache/checkpoint. No reproduction claim. |
| TxPert | Genetic networks, latent transfer, unseen gene/cell tests. | Inputs/tasks mismatch PRISM viability; no artificial leaderboard comparison. |
| MAP | Chemical structure, protein/text/KG representation; unprofiled-drug expression. | Drug task motivation is relevant; expression and KG source permissions do not establish viability utility or engagement. |
| RKT / ungated transfer | Existing route parameters and neighbour primitives are reused; chemical+target/MoA neighbour averaging is run. | RKT's calibrated RNA certificate is out of scope and is not presented as a faithful viability RKT reproduction. |
| MDA, arXiv:2608.09696 | LLM proposes mechanistic models; Bayesian structure/parameter inference; design uses mutual-information VoI; posterior variance enables small-menu enumeration. | Neither proposals, Bayesian design, memory nor revision is individually new. This P0 does not show an Agent advantage over MDA. |
| Classical goal-oriented design | Expected terminal utility and outcome-dependent updates already exist in Bayesian experimental design and MAESTRO acquisition. | Joint observation/update selection is only a specific testable biological-transfer application; priority or broad novelty is not established. |
| Centaur, arXiv:2603.24647 | Shares CMA-ES state with an LLM; classical fixed-space HPO outperforms pure agents in its reported setting. | Hybrid numerical/LLM design is not novel. Its 24-hour training budget excludes LLM inference overhead; any future MAESTRO comparison must include all proposal/compute costs. |

The narrow candidate difference is a policy over a joint **observation and
evidence-conditioned transfer-revision rule**, judged by independent terminal
viability benefit at a matched resource budget. The falsification experiment is
specified in PROTOCOL. P0 fails, so this contribution remains unimplemented and
unvalidated. The outcome is a negative feasibility result, not a new named method.
