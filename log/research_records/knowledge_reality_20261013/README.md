# Knowledge reality: does real biological knowledge add drug-specific information for unseen compounds?

Study folder: `research/knowledge_reality_20261013/`.

* **Status.** The development gate was run once and **FAILED** (G2). The confirmatory protocol is
  frozen but not executed. The sealed PRISM 24Q2 tier stays sealed: no response value has been
  downloaded.
* **Recommendation: NO-GO** for confirming, extending or putting an agent on top of
  knowledge-conditioned prediction on this task.
* **Cost.** 0 wells and 0 provider calls. 2.4 MB of release metadata was downloaded.

## 0. The answer

On 1,460 active strict cold-start compounds (PRISM 19Q4, exposed, exploratory), adding knowledge
to chemistry raised the per-compound selective-profile r from 0.0786 to 0.0842.

* **Not annotation frequency.** The gain is +0.0056, 95% CI [+0.0028, +0.0085], family-cluster
  sign-flip p < 0.0001.
  * It beats every degree-preserving and every set-permuted null graph (20 seeds each). On those,
    the gain is −0.0001.
  * The true drug–target pairings carry information.
* **Not biology.** Relabelling the genes within degree, expression-variance and mutation-frequency
  strata destroys every target's identity and cellular biology, but keeps which drugs share a
  target. It leaves the gain unchanged: +0.0057 on average, true gain at empirical p 0.95.
* **Not new.**
  * Plain Hub target/MoA neighbours already reach 0.0836 (`annot_full`), and block Q's RKT route
    0.0839.
  * Relation typing, provenance weighting, the biological-context route and T1 engagement edges
    add nothing measurable.
  * For the 26 active compounds whose targets no training compound shares, the gain is +0.0007
    (p 0.39).

The registered reading of G1 passing and G2 failing applies: the gain comes from **annotation
structure**, in the sense of mechanism-class membership, **not from biological relationships of
the targets in their cellular context**.

Two further facts make the confirmatory stage a poor use of the sealed tier:

* At the development effect size it would need 762 active compounds; about 396 are expected
  (power ≈ 52%).
* A single primary-screen measurement on a quarter of the lines (T1) reaches r 0.20. Knowledge
  adds +0.0004 on top (p 0.063).

## 1. Skeptical novelty assessment

Read from the abstracts and the records gathered by earlier blocks
(`research/context_discrimination_20261013/literature_sources.json`). The full texts were not
reviewed in this session, so "not reported" below means "not reported in what we read".

| Method | Perturbation | Output | What it implements | Knowledge source | Evaluation regime |
|---|---|---|---|---|---|
| PRESAGE (Littman et al., bioRxiv 2025) | genetic (Perturb-seq) | expression change | gene embeddings from many knowledge sources, attention aggregation; functional metrics (effect size, phenocopy, gene-set scores) | best source is cross-system Perturb-seq, i.e. measured perturbation responses | unseen genetic perturbations; source ablations, saturation with training size |
| TxPert (Valence Labs, arXiv 2505.14919; Nat Biotech 2026) | genetic | expression change | latent transfer over several gene-gene graphs | database graphs plus graphs built from perturbation screens (best combined) | unseen single and double perturbations, unseen cell lines |
| PIE (Verma, Adduri, ..., Roohani, bioRxiv 2026-10) | genetic (Replogle-Nadig CRISPRi) | DE genes, expression change | population-level effects from external knowledge, baseline expression and observed responses | external knowledge plus observed perturbation responses | unseen contexts, perturbations, datasets |
| MAP (Feng et al., Nat Mach Intell 2026) | chemical | single-cell expression | MAP-KG (14 sources, 694k drug-gene relations) aligned with structure, protein and text; conditions a single-cell foundation model | curated databases and ChEMBL assay descriptions | unseen cell type-drug pairs and unprofiled drugs (top-50 DEG Pearson delta); retrospective in-silico screen ranking 4 of 5 approved drugs in A549 |
| MAESTRO RKT (block Q, 2026-10-12) | chemical | L1000 landmark expression | typed transfer routes (context, phenotype, chemistry, knowledge), per-query certificate, named refusal | Hub targets and MoA, signed MAP-KG edges | sealed GSE70138; confirmed with one profiled line; never-profiled gain +0.050 over generic, knowledge route alone below generic |

What this leaves untested, and what is not new:

* **Not new.** Multisource embeddings (PRESAGE, MAP), knowledge graphs (TxPert, MAP), context
  conditioning (PIE, TxPert unseen lines), typed routes with refusal (RKT), and agent orchestration
  (blocks N, P, Q and the triage, all null or harmful). The target-context route built here is
  also a classic idea: target expression and mutation as sensitivity biomarkers.
* **Genetic is not pharmacological.** Three of the four published methods perturb genes. Then the
  identity of the perturbation is the gene, and knowledge about the gene is knowledge about the
  perturbation. A drug's link to its targets is itself uncertain knowledge: polypharmacology,
  partial inhibition, off-targets and exposure. Their results do not transfer to drugs by
  assumption.
* **Expression is not function.** All five predict expression. None predicts a measured viability
  or selective-killing outcome. MAP's screen is a pathway enrichment of predicted expression,
  scored against approved drugs: a retrospective ranking, not a confirmed discovery.
* **Outcome-derived knowledge.** The strongest sources in PRESAGE and TxPert are built from
  perturbation screens. For a strict cold-start claim, those are measured responses of the same
  modality. MAP-KG holds ChEMBL cell-based assay edges, including growth and viability readouts.
  The census removed 58 such edges from PRISM compounds and kept 969 cell-engagement edges for
  the T1 arm only.
* **Knowledge reality.** As far as we read, none reports degree-preserving, coverage-matched or
  annotation-density controls. The closest is edge shuffling in the PrimeKG++ perturbation model
  (arXiv 2512.22251). RKT reported none.

**The open question this study can own** is narrow. Does typed, provenance-qualified,
context-conditioned knowledge carry drug-specific information about a *functional* outcome for
*strict cold-start* compounds? That means beyond structure, beyond degree- and coverage-matched
null graphs, and on independently released compounds with a decision endpoint. The contribution
would be the falsification design and its answer, not an architecture.

## 2. Information tiers, data feasibility and leakage audit

### Tiers (`src/maestro/information_tier.py`)

| Tier | May read | May claim |
|---|---|---|
| T0, strict cold start | structure; curated and cell-free knowledge; cell lines' basal state; *other* compounds' responses | zero-shot prediction for unseen compounds |
| T1 | adds legal primary-screen or other already-observed responses of the compound | screen-informed triage, which still needs independent confirmation |
| T2 | adds measurements bought during the campaign, costed in wells and turnarounds | campaign results |

* **Per-arm admission.** Every arm declares its inputs, and `require` checks them before anything
  is fitted. It refuses with three named reasons:
  * `TIER_VIOLATION`: a T1 input under a T0 claim;
  * `OUTCOME_PROXIMAL_INPUT`, at every tier: for example, a ChEMBL growth or viability assay of
    the compound when the endpoint is viability;
  * `UNDECLARED_INPUT`: an input the registry does not know.
* **Tests.** Five tests in `tests/test_information_tier.py`.

### Inventory

| Source | Date | Assay or content | Licence | MAESTRO exposure | Role here |
|---|---|---|---|---|---|
| PRISM 19Q4 primary | 2019-12 | pooled barcoded viability, 5 days, 2.5 µM, log2 FC | CC BY 4.0 | exposed (blocks N, P, triage) | development outcome |
| PRISM 19Q4 secondary | 2019-12 | 8-dose AUC | CC BY 4.0 | exposed | development secondary confirmation |
| CCLE 19Q4 expression and mutations | 2019-12 | basal RNA-seq, mutation calls | CC BY 4.0 | context only | line state (T0) |
| Repurposing Hub drugs file | 2020-03-24 | curated targets and MoA | **non-commercial use only** (file header) | used by N, P, Q, triage | curated knowledge (T0) |
| MAP-KG (Feng et al. 2026) | 2026 | 14 aggregated sources; ChEMBL assay descriptions | per-source terms (DrugBank CC BY-NC, ChEMBL CC BY-SA); research use | block Q (signed edges) | typed, provenance-classed knowledge |
| PRISM 24Q2 REP.1M | 2024-05-31 | same platform, 2.5 µM, ComBat-corrected log2 FC | CC BY 4.0 | **sealed**: metadata only | confirmation tier |

Not available locally: DepMap CRISPR (Chronos) gene effects. Fetching them is a large download
that needs authorisation, and the portal showed bot verification. Without them, the "genetic
dependency of the target" route that PRESAGE- or TxPert-style knowledge would suggest could not be
built.

### Edge provenance

| Provenance | Edges | Compounds | Tier |
|---|---|---|---|
| curated Hub | 10,654 | 3,347 | T0 |
| curated mechanism (MAP-KG) | 10,675 | 2,621 | T0 |
| aggregate binding (MAP-KG) | 3,920 | 1,252 | T0 |
| biochemical assay (ChEMBL via MAP-KG) | 6,769 | 942 | T0 |
| cell-based target engagement | 969 | 462 | T1 only |
| growth, viability or death readouts | 58 | n/a | removed (outcome-proximal) |
| metabolic (substrate, carrier, cofactor) | 21,972 | n/a | removed (not a target relation) |

### Leakage findings (`LEAKAGE.json`)

* **Aliases.** No structural alias unit and no name alias group spans folds.
* **Mechanism overlap.** Folds are by MoA family. Even so, 74–88% of annotated test compounds
  share a T0 target gene with training, and 35–56% share an MoA string.
  * The annotation graph is one 91% giant component (4,029 of 4,449 units).
  * "Unseen mechanism family" is therefore nearly impossible on this library. Only about 107
    annotated compounds have no target gene in common with training (`strict_new_target`).
  * Every development gain is a *seen-target* result unless it holds on that stratum.
* **Outcome-derived curation.** A keyword screen flags 3 Hub annotations whose killing mechanism
  was reported from PRISM itself (SLC26A2, metallothionein, ABCB1). Most outcome-derived curation
  cannot be found mechanically.
* **Time.** No edge carries a date. The Hub file postdates PRISM 19Q4, and MAP-KG postdates
  everything. A time-matched control is impossible on 19Q4 (`TIME_STAMPS_UNAVAILABLE`). The sealed
  design contrasts a snapshot that predates the outcomes with one that postdates them.
* **Sealed-tier identity.** 49 of 1,278 REP.1M compounds are in 19Q4: 23 by core, 11 by name and
  15 by connectivity. They are refused, and are kept only for the replication ceiling. The 2024
  file's target annotations agree with the Hub 2020 file for every eligible compound.

## 3. Minimal research architecture

The smallest mechanism-aware extension that the brief permits, built so that each element can be
ablated or randomised.

1. **Typed, provenance-qualified edges.**
   * Each edge is (drug, gene, relation ∈ {inhibits, activates, binds}, provenance group ∈
     {curated, measured, engagement}, source). MoA strings are tokens.
   * Engagement edges are T1 and appear only in the labelled T1 arm.
2. **`kn_typed`.** A kNN over weighted Jaccard similarity of (gene, relation, provenance) tokens.
   Curated tokens weigh 1.0 and measured tokens 0.5. It transfers neighbours' observed selective
   profiles.
3. **`tc`: target context, the biological-context component.** For each (compound, line), it pools
   five statistics of the compound's targets in that line, per relation and provenance group:
   mean and max expression z, expressed share, hotspot and deleterious mutation.
   * One ridge, shared across compounds, maps these features to the selective residual.
   * It encodes "a drug kills where its targets are present or mutated", and it can predict in
     lines no training compound saw.
4. **Refusal and uncertainty.**
   * Compounds without a T0 target get no `tc` prediction, and compounds without a token
     neighbour get no `kn_typed` prediction. These are named refusals, counted, and scored as r = 0.
   * A logistic calibrator fitted on inner predictions gives P(selective event).
5. **Stack.** Non-negative weights on inner grouped CV. A knowledge route that carries nothing gets
   weight 0, so `know_full` cannot fall far below `chem_full`.
6. **Controls built in.**
   * Three null-graph generators (`develop.control_edges`) take the same arguments as the true
     graph.
   * One annotation-density arm.
   * A zero arm.

No LLM, retrieval or agent component exists in this architecture. The brief's stop rule forbids
one until structured knowledge shows reproducible incremental value.

## 4. Development gate (exploratory, exposed PRISM 19Q4; registered in `DEV_PLAN.md`)

* **Run.** `develop.py` ran once (2,535 s) on 4,528 compounds and 561 lines in five MoA-family
  folds. 1,460 compounds are active; 1,207 of them have a T0 target.
* **Metric.** Per-compound Pearson r between the predicted and the observed selective residual.
* **Statistics.** Family-cluster sign-flip test with 10,000 draws; 95% intervals from a cluster
  bootstrap. Output: `DEVELOPMENT.json`.

### Arms (active compounds)

| Arm | Tier | Mean r | Specificity | Hits / 1,000 nominations | Secondary-confirmed / evaluable |
|---|---|---|---|---|---|
| zero (generic sensitivity) | T0 | n/a | n/a | 15 | n/a |
| `chem_full` | T0 | 0.0786 | 0.0500 | 142 | 108 / 532 |
| `density_full` | T0 | 0.0759 | 0.0431 | 121 | 108 / 561 |
| `annot_full` | T0 | 0.0836 | 0.0552 | 161 | 154 / 579 |
| `rkt_full` | T0 | 0.0839 | 0.0554 | 152 | 149 / 569 |
| **`know_full`** | T0 | **0.0842** | 0.0556 | 143 | 141 / 572 |
| `know_only` | T0 | 0.0589 | 0.0471 | 87 | 104 / 482 |
| `know_untyped` (ablation) | T0 | 0.0845 | 0.0559 | 142 | 143 / 572 |
| `know_full_t1` (adds engagement edges) | T1 | 0.0842 | 0.0556 | 145 | 143 / 571 |
| `t1_base` (chem + screen on 25% of lines) | T1 | 0.2016 | 0.2984 | n/a | n/a |
| `t1_know` (`t1_base` + knowledge) | T1 | 0.2020 | 0.2971 | n/a | n/a |

* **Hits.** Selective events (residual robust z ≤ −3 and LFC ≤ −1) among 200 nominations per
  fold, at most 3 per compound.
* **Secondary-confirmed.** The PRISM secondary AUC residual has robust z ≤ −2, where a secondary
  curve exists.
* **Caveats.** The decision columns are descriptive; no test was registered for them. The T1
  rows score only the hidden 75% of lines and carry no decision columns.

### Knowledge controls (20 seeds each, whole graph, within fold)

| Quantity | True | Degree null mean / 95th pct | Set-permutation null | Gene-relabelling null |
|---|---|---|---|---|
| `know_full` r | 0.0842 | 0.0785 / 0.0787 | 0.0785 / 0.0786 | 0.0843 / 0.0844 |
| gain over `chem_full` | +0.0056 | −0.0001 / 0.0000 | −0.0001 / −0.0000 | +0.0057 / +0.0057 |
| `know_only` r | 0.0589 | 0.0161 / 0.0179 | 0.0106 / 0.0130 | 0.0587 / 0.0590 |
| specificity | 0.0556 | 0.0495 / 0.0497 | 0.0497 / 0.0499 | 0.0557 / 0.0557 |
| empirical p of the gain | | 0.048 (the minimum with 20 seeds) | 0.048 | 0.95 |

* **Degree and set-permutation nulls.** On randomly wired graphs the non-negative stack gives
  knowledge zero weight, and `know_full` falls back to chemistry.
* **Gene relabelling.** It keeps the graph isomorphic, so token-similarity routes (`annot`,
  `rkt_know`, `kn_typed`) are unchanged by construction: `annot_full` is 0.0836 under every
  relabelling. Only the target-context route sees different biology, and its absence changes
  nothing.

### Gate

| Criterion | Result | Verdict |
|---|---|---|
| G1: `know_full` − `chem_full` > 0, p < 0.05 | +0.0056 [+0.0028, +0.0085], p < 0.0001; 821 compounds favour, 593 oppose, 531 clusters | pass |
| G2: true r and gain above the 95th percentile of every control | above degree and set-permutation; **at the mean of relabelling** | **fail** |
| G3: specificity gain > 0, p < 0.05 | +0.0056 [+0.0030, +0.0083], p < 0.0001 | pass |
| Overall | | **FAIL** |

### Ablations, strata and single routes

| Contrast (active compounds) | Δr | 95% CI | p (one-sided) |
|---|---|---|---|
| `know_full` − `rkt_full` (prior MAESTRO route) | +0.0003 | [−0.0007, +0.0014] | 0.27 |
| `know_full` − `annot_full` (plain Hub neighbours) | +0.0007 | [−0.0009, +0.0024] | 0.20 |
| `know_full` − `know_untyped` (relation and provenance typing) | −0.0002 | [−0.0004, −0.0001] | 0.995 |
| `know_full` − `know_curated_tc` (measured edges in the context route) | −0.0000 | [−0.0001, +0.0000] | 0.83 |
| `know_full_t1` − `know_full` (cell-engagement edges, T1) | −0.0001 | [−0.0002, +0.0001] | 0.80 |
| `know_full` − `density_full` | +0.0083 | [+0.0051, +0.0119] | < 0.0001 |
| `density_full` − `chem_full` (annotation counts alone) | −0.0027 | [−0.0043, −0.0013] | 0.9999 |
| `know_full` − `chem_full`, strict new target (26 compounds) | +0.0007 | [−0.0024, +0.0044] | 0.39 |
| `t1_know` − `t1_base` (knowledge after a primary screen) | +0.0004 | [−0.0001, +0.0009] | 0.063 |

Single routes, mean r on active compounds:

* Chemistry: kernel ridge 0.0738; Tanimoto kNN 0.0522, refusing 20% of compounds.
* Knowledge neighbours: `kn_typed` 0.0588; Hub neighbours 0.0572; RKT 0.0576.
* Target context: 0.0090.
* Annotation density: 0.0440.

**Calibration.** The Brier score is 0.0069 for every T0 arm. ECE is 0.0014 for chemistry and
0.0017 for `know_full`. Knowledge does not improve the probability of a selective event.

## 5. What the knowledge signal is

* **Real.** Knowledge helps through *who a compound's neighbours are*. Compounds annotated with
  the same targets or MoA kill similar lines, and borrowing their observed profiles adds about
  +0.005 r over structure. It is
  * not annotation density (`density_full` is worse than chemistry);
  * not graph degree or bundle size (the nulls are flat).
* **Not biological context.**
  * The route that conditions on the targets' expression and mutation in each line reaches
    r 0.009 alone.
  * The same route on a gene-relabelled graph does exactly as well. Its small signal comes from
    the *kind* of gene (degree, variance and mutation class), not from the specific target.
  * A pooled, cross-compound model of "drugs kill where their targets are high or mutated" does
    not describe this library.
* **Seen mechanisms only.** The neighbour signal needs annotated neighbours. With no shared
  target gene the gain vanishes, and 74–88% of annotated test compounds share one. So
  "unseen-drug" here means unseen compound, seen mechanism.
* **Small, and overtaken by measurement.** The whole T0 stack explains about 0.7% of the selective
  profile's variance (r² ≈ 0.08²). A primary screen on a quarter of the lines reaches r 0.20, and
  knowledge then adds nothing.
* **Decisions (descriptive).**
  * `know_full` nominated as many primary selective events as chemistry: 143 against 142 of
    1,000.
  * Every knowledge arm nominated more pairs that the secondary screen confirms: 141–154 against
    108 for chemistry.
  * Plain Hub neighbours (`annot_full`) did best on both counts: 161 events and 154 confirmations.
  * None of this was a registered test.

## 6. Frozen protocol and why it is not run

`PROTOCOL.md` fixes stage 2 on the sealed release. `FREEZE.json` hashes it together with the
code, the census, the development results and the power calculation.

* **Release.** PRISM Repurposing 24Q2 REP.1M: 1,229 compounds new by core, name and connectivity,
  each with a Hub 2020-03-24 structure.
* **Snapshots.**
  * The time-matched snapshot is Hub 2020. It predates the outcomes by four years, which supplies
    the time-matched control impossible on 19Q4.
  * MAP-KG 2026 is the sensitivity contrast.
* **Hypotheses.**
  * H1: `know_full` beats `chem_full` on per-compound r and beats every null.
  * H2: in campaigns of 64 compounds with 32 wells each, `know_full` nominates more selective
    events than chemistry, reported beside the zero arm.
* **Separate reports.** Strata, calibration, a context shift to 285 new lines, and a replication
  ceiling from the 48 compounds screened in both releases.
* **Guards.** `confirm.py` locks predictions before the outcome file can be read. It verifies the
  file's MD5 and refuses to run when:
  * the freeze has changed (`FREEZE_MISMATCH`);
  * outcome IDs do not match (`OUTCOME_ID_MISMATCH`);
  * the development gate failed (`GATE_NOT_PASSED`). The owner can override with
    `--despite-gate`, which is recorded in the lock and is a deviation.
* **Smoke tests.** Both steps were exercised on synthetic data. `evaluate` recovered a planted
  signal; `predict` ran with one snapshot and one control seed.

Not running it is the registered consequence of the gate. Two further reasons stand on their own:

* **Power.** The development effect needs 762 active compounds for 80% power (`POWER.json`).
  About 396 are expected, so H1 would most likely read `INCONCLUSIVE_UNDERPOWERED`.
* **Value of the tier.** A sealed release can be opened once. Spending it on an effect that
  development already attributes to mechanism-class membership, which RKT and annotation kNN
  capture, would buy no new knowledge.

## 7. Go / no-go

* **NO-GO: confirmation of this thesis on the sealed tier.**
  * Gate failed; underpowered.
  * The 72.5 MB outcome file is not requested.
* **NO-GO: promoting the knowledge routes.**
  * Typing, provenance and the context route add nothing over the existing RKT route.
  * Nothing from `research/` is promoted to `src/`.
* **NO-GO: stage 3 (LLM decision layer).**
  * The brief's stop rule applies: structured knowledge has not shown reproducible incremental
    value attributable to biology.
  * No LLM, retrieval or agent arm was built or called.
* **KEEP: `maestro.information_tier`.**
  * It is a contract, not a model. It makes "T1 inputs never support a T0 claim" and
    "outcome-proximal edges are refused" mechanical, with five tests.
  * It cost nothing to adopt, and it caught the cell-engagement and viability-assay edges that
    MAP-KG ships as ordinary drug–gene relations.
* **What would justify reopening.** A knowledge source with *gene-level functional content per
  cell line*. Example: DepMap CRISPR dependency of each target, a genetic–pharmacological
  concordance route.
  * It must be tested with the same gene-relabelling null, because that null is what separates
    biology from class membership.
  * It needs a large download (authorisation required) and a sealed tier with at least about
    760 active compounds, or a larger expected effect.

## 8. Data audit and deviations

* Sections 2 and 3 above give the tiers, inventory, edge provenance and leakage findings
  (`CENSUS.json`, `LEAKAGE.json`, `SEALED_CENSUS.json`).
* `DEVIATIONS.json` records ten disclosures. The ones that touch the registered run:
  * a smoke run 32 s before it, on the same plan hash;
  * `control_edges` generalised during it, with identical outputs verified;
  * the corrected Hub licence: **non-commercial use only**, from the file header;
  * the CXSMILES strip, applied only in the sealed census;
  * the 24Q2 metadata download.

## 9. Reproduction

Run in the maestro environment, Python 3.11, from this folder:

```bash
python census.py && python build.py && python leakage.py && python sealed_census.py
python develop.py
python power.py
python freeze.py
python verify.py
python verify.py --replay
```

* `develop.py` takes about 45 minutes; `verify.py --replay` reruns it.
* `verify.py` checks the following:
  * the freeze;
  * that the census, leakage, sealed census and power files reproduce byte for byte;
  * that `confirm.py predict` refuses with `GATE_NOT_PASSED`;
  * that every number in this README passes `maestro.claim_audit.audit` against the run manifest
    (`claims.py`, `CLAIMS.json`, `RUNS.json`). That manifest includes the negative and refused
    runs.
* The sealed metadata lives in `tmp/knowledge_reality_20261013/sealed_metadata/` and is checked
  by MD5.

| File | Content |
|---|---|
| `DEV_PLAN.md`, `PROTOCOL.md` | registered development plan; frozen stage-2 protocol |
| `sources.py`, `census.py`, `build.py` | sources, edge typing and provenance, tables |
| `models.py`, `develop.py` | routes, stacks, controls, development gate |
| `leakage.py`, `sealed_census.py`, `power.py` | leakage audit; sealed eligibility; power |
| `confirm.py` | stage-2 predict / evaluate (not run) |
| `freeze.py`, `verify.py`, `claims.py` | freeze, verification, claim manifest |
| `SMOKE_DEVELOPMENT.json` | the pre-run smoke output (excluded run; not evidence) |
