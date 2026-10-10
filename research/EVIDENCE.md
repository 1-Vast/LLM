# Evidence Register

## Measure or predict across platform and time — 2026-10-10

**Primary results:**

* A frozen STATE forecast of the 24 h state does not transport to an independent platform.
* The development gate's call to measure early instead was a false positive.
* For one time-course drug, information about 5-day fate appeared at 24-48 h.

Block K asked whether a virtual cell's forecast of the early (24 h) cell state can replace
measuring it for a 5-day viability decision. The decision is three-way:

* `ADMIT_WORLD_MODEL` if adding the forecast to the best cheap prior gains at least the minimum
  useful benefit (0.05 r);
* `MEASURE_EARLY` if only the measured early state does;
* `USE_PRIOR` otherwise.

**MIX-Seq** (pooled scRNA-seq, 24 h, a platform STATE never saw; 5-day PRISM outcome;
DepMap-scale CCLE prior):

* On 24 development lines: measurement +0.139, forecast -0.150, so the gate said MEASURE_EARLY.
* On 48 confirmation lines: measurement -0.021 [-0.109, +0.078] (M1 fails) and forecast -0.091
  [-0.182, -0.005] (transport refusal confirmed).
* Top-10 line selection: measurement policy minus prior -0.061 [-0.165, +0.169] (M3 fails).
* A post hoc paired re-analysis that corrects an unpaired estimand found by verification leaves
  every verdict unchanged.
* STATE's line-specific RNA skill is about 0; trametinib reaches 0.059 [0.032, 0.082], against a
  split-half ceiling of 0.35-0.79.
* Observed Tahoe and MIX-Seq responses of the same lines agree at r of 0.13 or less. The same
  MIX-Seq lines agree across two MIX-Seq experiments at r 0.65.

So the learned line-specific response is bound to its platform.

**Trametinib time course** (24 lines):

* Response magnitude predicts 5-day viability at r 0.21 (3 h), 0.25 (6 h), 0.31 (12 h), 0.56 (24 h)
  and 0.68 (48 h).
* Only the 48 h measurement adds to the prior (+0.16 [0.01, 0.36]).
* STATE's 24 h forecast best matches the observed 12 h response.
* A phase-snapshot kinetic readout does not predict the next interval's abundance change (r 0.11
  [-0.04, 0.24]).

**Tahoe 24 h to PRISM 5-day:**

* The early state does not add to the CCLE prior (-0.107 [-0.155, -0.059]; USE_PRIOR confirmed).
* G1 accumulation marks relative sparing for the top-variance drugs (+0.136 [+0.002, +0.254]). For
  trametinib it marks sensitivity (r -0.59 at 24 h).

**Post hoc:** the development gate's interval was [-0.049, +0.298]. The promoted
`maestro.world_model_value.plan_measure_or_predict` therefore acts only on interval lower bounds
and otherwise returns `ABSTAIN`. This is a conservative correction motivated by one failure, not a
validated improvement. Cross-time and cross-assay bridges are no longer refused outright. They are
admitted only through this interval rule, with the late endpoint measured in its own assay on
reference units.

Also promoted:
* `tools.evaluation.increment.paired_increment`, which computes the paired estimand by
  construction;
* `tools.analysis.platform_identity.identity_test`. In this block it passed 18 of 18 lines while
  responses did not transport, so passing it does not imply response transport.

**Limits:**
* six drugs, one time-course drug, and 35-60 cells per line and condition;
* PRISM is a different assay from both single-cell platforms;
* the STATE gene order is supported, not certified by lineage;
* the Tahoe zero-shot PRISM tier was not opened.

Packet: `research/astra/kinetic_horizon_20261010/`. Receipt: `log/20261010/KINETIC_HORIZON.json`.

## Phenotype-anchored dual core — 2026-10-10

**Primary result: null for STATE on Tahoe relative-survival selectivity; the cheap basal-context
prior wins, and the registered world-model gate's refusal held.**

Tahoe-100M pools 50 lines in spheroids for 24 h. Relative survival (line share against same-plate
DMSO with a reference-line denominator) and phase log-odds shift are derived from per-cell obs
codes in the same spheroids as RNA. Absolute survival is not identified because spheroid totals
do not replicate. Five undercounted contexts are refused as `CONTEXT_UNDERCOUNTED`.

On 40 qualified reference lines, the perfect-RNA-oracle ceiling improves mean within-line r by
only 0.003 over basal-similarity transfer, below the preregistered 0.05 minimum useful benefit;
the gate returns `WM_CEILING_BELOW_MUB`. On five checkpoint-held-out lines, STATE vs basal
transfer is delta r -0.226 (95% CI [-0.266, -0.156], 0/5 better). Basal transfer beats generic
potency ranking by +0.558 top-10 log2 utility (95% CI [0.235, 0.819], 5/5). The observed-profile
oracle also fails to beat basal transfer on held-out lines. STATE's distinct held-out signal is
predicted-cell G1 composition (+0.254 r on E2); this RNA-derived endpoint is not viability.

The study promotes a same-unit bridge and value-ceiling admission contract, Tahoe phenotype
construction, and scope-labelled basal transfer. Admission permits forecast evaluation; it does
not certify the forecast. Cross-assay, cross-dose and cross-time bridges are refused, as are
contexts below the declared count. No STATE readout, bridge or LLM policy is promoted. Limits:
five held-out lines whose RNA was exposed in earlier blocks, reference overlap with STATE
pretraining, 24 h relative share, and no claim of apoptosis, efficacy or mechanism.

Study packet: `research/astra/phenotype_anchor_20261010/`. The frozen receipt records identities,
gate, held-out results, deviations and verification: `log/20261010/PHENOTYPE_ANCHOR.json`.
Run `python research/astra/phenotype_anchor_20261010/verify.py` to verify; study and promotion
parity tests are registered under the research scope.

This is the canonical cross-study result table. [REPORT.md](REPORT.md) states current conclusions; [INDEX.md](INDEX.md) routes to frozen protocols and detailed study reports; [SCIENTIFIC_STATUS.json](SCIENTIFIC_STATUS.json) provides machine-readable gates, units and costs. This consolidation introduces no new experiments or scientific claims.

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
| Conditional pairwise correction | `VERIFIED_DEVELOPMENT; GATE_FAILED` | Can condition-bound knowledge and one shared A observation improve frozen boundary comparisons? | At eight histories, knowledge+feedback regret 0.00653089 versus no-update 0.00640195; 43 corrected/51 harmful flips. All 6,192 policy rows independently reconstructed; portable cached replay exact. | Exposed RNA development, STATE overlap and no independent cultures. Four-history support gate structurally disables feedback. Sixteen-history mean-only signal remains descriptive. | `research/decision_value/pairwise_20261009/`; canonical receipt `log/20261009/PAIRWISE_CORRECTION.json`; portable input bundle 1.51 MB. |
| Dual-source residual transfer v3 | `VERIFIED_DEVELOPMENT; GATE_FAILED` | Does one A observation add decision value after correcting both conditional means and refitting their residual dependence? | All 3,870 rows independently reconstructed. At eight histories, feedback adds 0.0000128654 over its mean-only model, nominal CI includes zero; no update remains slightly better. Prebuy stop saves 94/129 A purchases with unchanged matched-arm actions. | Previously exposed RNA units, transductive public-state geometry, insufficient feedback coverage and no independent risk or knowledge-specific benefit. | `research/decision_value/pairwise_v3/`; canonical receipt `log/20261009/PAIRWISE_V3.json`; exact isolated cached replay and separate independent verification. |
| Observation reliability P0.5 | `VERIFIED_AUTHENTICATION_ATTEMPT; AXIS_BLOCKED` | Can control-only source comparisons authenticate the 39 endpoint coordinates before a scalar-noise audit? | 448 DMSO cells; 27/39 unique matches in c40 and 34/39 in c44. Offline reconstruction passes; the complete identity certificate fails and 250 noise cells remain unopened. | Sparse/all-zero coordinates are unidentifiable, not contradicted. No endpoint variance, full-axis/checkpoint certification or A/B cause is established. | `research/decision_value/observation_reliability/axis/`; canonical receipt `log/20261009/OBSERVATION_RELIABILITY.json`. |
| Source-time/repeat qualification P0.6 | `VERIFIED_PROVENANCE; DESIGN_ONLY` | What source timing and repeat units are actually supported, and which cheap diagnostic channel should be proposed? | Tahoe methods authenticate global 24 hours and author-described plate6/14 biological repetition; exact sample joins pass. The revised six-treatment c44/c45 proposal needs 6.144 MB future RNA. | Pooled line partitions are dependent; per-sample timestamps and a third confirmation source are absent. No treated expression, channel gain or LLM advantage tested. | `research/decision_value/observation_reliability/literature/SOURCE_QUALIFICATION.json`, `P06_DESIGN.md`. |
| Public ordered-axis search P0.5R | `CORROBORATED_CANDIDATE; LINEAGE_UNPROVEN` | Is an authoritative ordered axis available for the precise filtered dataset and checkpoint? | Official static 2,000 list agrees with all 39 historical positions and earlier unique matches; pinned checkpoint metadata names 62,710 full genes but omits the ordered subset. | List agreement is not exact release lineage, per-file identity or decoder certification. | `research/decision_value/axis_recovery_20261010/authority/`; zero-network source audit. |
| Informative paired-axis recovery P0.5R | `VERIFIED_RECONSTRUCTION; AXIS_BLOCKED` | Can expression-guided source conditions make all 39 coordinates uniquely identifiable in c44/c45? | First pool lacks support; supplement screens 3,354 QC cells and reads 74 paired cells. All endpoints meet two/one nonzeros, but only 16/39 c44 and 23/39 c45 uniquely match. Combined calibration 24,533,272 known body bytes. | Remaining trajectories are nonunique, not contradicted names. Adaptive cell-level holdout is not culture independence; no gate relaxation or P0.6 release. | `research/decision_value/axis_recovery_20261010/calibration_v2/`; independent `design/CALIBRATION_V2_VERIFIED.json`; `log/20261010/AXIS_RECOVERY.json`. |
| Direct-name control observation P0.5R | `VERIFIED_EXPLORATORY_CHANNEL` | What does gene covariance do to a separately named 39-gene control scalar? | 224 retained c44 controls, 28 groups, actual n=8; full/diagonal variance ratio median 1.473, range 0.709–3.731; independent vectors/bootstrap reproduced. | Only one unadjusted interval wholly exceeds one; no culture-level noise, old endpoint equivalence, treated reliability or decision gain. | `research/decision_value/axis_recovery_20261010/named_channel/`; independent `design/NAMED_VERIFIED.json`. |
| Axis selection diagnostic | `OFFLINE_DIAGNOSTIC; NOT_CERTIFICATION` | Did positive-coverage allocation omit identifying zero contrasts? | Full retained support patterns are unique for all 39 genes per file; a heuristic adds 11 discovery rows per file, with fixed holdout and projected paired cost 340,068 bytes. | Binary presence need not equal numerical nonzero; this closed diagnostic reads no extra RNA, its numerical gate remains failed, and its row count is not proven minimal. | `research/decision_value/axis_recovery_20261010/calibration_v2/diagnosis/`; separate post-result freeze. |
| Measure or predict (block K) | `CONFIRMATORY; M1_M3_FAILED; TRANSPORT_REFUSAL_CONFIRMED` | Can a frozen virtual cell's 24 h forecast replace measurement for a 5-day decision, and is any failure a ceiling, transport or timing failure? | MIX-Seq, 48 lines: measurement over the DepMap prior -0.021 [-0.109, +0.078]; STATE -0.091 [-0.182, -0.005]. Same-line cross-platform response r 0.13 or less versus within-platform 0.65. Trametinib 5-day information appears at 24-48 h (+0.16 at 48 h). Tahoe early state below the prior (USE_PRIOR confirmed). | Six drugs; one time-course drug; small cell counts; unpaired evaluator estimand (verdicts unchanged when paired); candidate gene order supported, not certified. | `research/astra/kinetic_horizon_20261010/`; `log/20261010/KINETIC_HORIZON.json`; `run_sealed.sh` then `verify.py`. |
| Historical union and targeted axis extension | `VERIFIED_FILE_LOCAL_ENDPOINT39; P06_UNFROZEN` | Can exposed c44 bytes and eleven explicitly discriminating c45 rows complete the data-coordinate gate cheaply? | Both files pass 39/39 unique matches among all 62,710 genes at 1e-5. c44 adds 0 bytes; c45 receives exactly 133,564. Separate logical-slice/blockwise reconstruction agrees; 3,334 protected old files unchanged. | Historical/adaptive coordinate evidence; exposed consistency is not fresh validation. Initial parser failure preserved with a zero-download offline amendment. Full 2,000/checkpoint axes and P06/P2 execution remain unqualified. | `research/decision_value/axis_extension_20261010/QUALIFIED_CERTIFICATE.json`; canonical receipt `log/20261010/P05R_EXTENSION.json`; standalone offline replay. |

## Interpretation and audit rules

- Software contracts, numerical reconstruction, data-coordinate identity, biological reliability and decision benefit are separate outcomes. A passed replay does not convert a failed scientific gate into success.
- The endpoint is an equal positive `+1/39` RNA expression-change mean. It is not a signed apoptosis gene set, viability, protein activity or a validated functional utility.
- Historical/exposed backgrounds, cached predictions, adaptive cell selection and reordered agent cases are development evidence. Distinct arithmetic implementations are not independent biological confirmation or independent multi-agent research.
- Knowledge retrieval must retain source identity, direction, assay and condition limits. Missing annotations are unknown, not negative effects. Shared-space retrieval does not certify cell-specific response transfer.
- The extension qualifies only c44/c45 file-local endpoint coordinates. Original P0.5/P0.5R failures, parser failure and frozen amendments remain unchanged. Full dataset/checkpoint axes, P0.6 execution and P2 remain separately gated.
- Costs retain their units: bytes measure received payload, simulated profiles measure replay accounting, and provider calls/tokens are not authenticated monetary cost. The 60.7% extension saving applies only to planned new expression payload; 72.9% V3 saving applies only to A purchases relative to always-buy feedback.
- Nominal development intervals and Gaussian probability diagnostics are not deployment risk guarantees. Missing assets block replay; they are never replaced by invented outcomes.

Detailed methods, source hashes, deviations and immutable failure attempts remain in the linked study directories and dated receipts. Historical zero-shot sources require Git-history recovery at `540bc85`; their result is not rerun by current software tests.

<!-- Retained fragment targets for frozen study documentation. -->
<a id="state-readout-repair-20261009"></a>
<a id="map-released-weights-20261008"></a>
<a id="map-knowledge-pilot-20261008"></a>
<a id="map-knowledge-layer-audit--2026-10-09"></a>
<a id="map-module-replacement-and-hard-task-tests--2026-10-09"></a>
<a id="conditional-pairwise-correction-under-scarce-feedback--2026-10-09"></a>
<a id="dual-source-conditional-residual-transfer-v3--2026-10-09"></a>
<a id="observation-reliability-and-source-qualification--2026-10-09"></a>

Legacy detailed-section links now resolve to this consolidated register; use the table reproduction path for the original study-specific detail.
