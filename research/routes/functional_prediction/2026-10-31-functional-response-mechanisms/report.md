# Functional intervention updates: what the current observations can test

2026-10-31. **The current cheap endpoint table does not authenticate the state transitions or drug schedules needed to test a portable intervention update.** A useful conditional opening remains: measure a functional state before and after one intervention, then test whether that change predicts a subsequent intervention in a reserved background. No such state or qualified matched challenge was established here. No model was fitted, no empirical mechanism benefit was demonstrated, and no result was promoted to `src/` or `tools/`. The overall research objective remains **ACTIVE / NOT_ACHIEVED**.

This is an observation and identification boundary for a specific candidate, not evidence that Virtual Cells fail or that static response prediction is useless. The algebra below is classical or elementary, not a new algorithm or biological discovery. The independently reviewed question is preserved in [I002.v1](operator_question_v1.md) and its [original freeze](operator_question_freeze.json); the freeze admits scientific qualification only, not numerical fitting.

## The useful question

For a drug-discovery analyst, the proposed output is a prediction of how A changes susceptibility to B in a background or treatment history whose combination response has not been measured. The intended benefit would be fewer justified assays for selecting a follow-up regimen, or better selection at the same total assay cost. That benefit is proposed, not observed.

The smallest proposed restriction is:

```text
z_after_A = U_A(z_before_A)
conditional_effect_B_after_A = h_B(z_after_A)
```

The scientific content is **closure and transport**: the measured state must contain the information about A, background and history that matters for the controlled B challenge, and the update/readout must remain valid in the declared target range. An embedding, a low-rank matrix, a sparse parameter change or fast adaptation does not establish either condition. Generic controlled state-space learning, causal representation learning and dynamical pharmacology already address related objects. An exact new methodological difference has not been established.

All proposed rivals must receive the same state assays, response panel, doses, histories and target feedback. Diagnostic combination outcomes used for calibration cannot also be untouched evaluation targets. An unrestricted direct predictor can represent a finite update algorithm's input/output computation; literal non-representability by every direct predictor is therefore not a useful acceptance criterion. A falsifiable biological restriction and a useful capability or cost advantage are the relevant targets.

## What was actually audited

The existing Rhaister/Emerald Bay Parquet summary is 52,053 bytes, SHA256 `3b4b9e451eab1106b7e47aac1b68d5181f0e684c021c88fc63f0dca01d7cc5c9`. The root projected **only `cell_line` and `condition`** in the existing maestro environment. The fresh challenger independently repeated that projection. Neither audit deserialized `growth_rate` values.

| Metadata observation | Actual support |
|---|---|
| Cell lines / condition identities | 52 / 93 |
| Noncontrol single-drug conditions / drug names | 44 / 19 |
| Combination conditions | 41 pairs, 3 triples, 3 quadruples |
| Combination drug-name families | 16 |
| Pairs with both exact-dose constituent singles | **17 of 41** |
| Higher-order conditions with every exact single dose | 0 |
| Rows / unique line-condition keys | 4,992 / 4,836 |
| Sequence, preparation or independent-culture fields | Absent from this three-column summary |

The root [audit](root/pooled_design.json) and independent [verification](challenge/metadata_verification.json) agree. Canonicalizing each condition as unordered produces 93 identities too: this file has no extra condition identity supplied solely by reversing tuple order. Tuple order is not a dosing schedule. Missing schedule fields do not establish that actual administration was simultaneous. Four endpoint DMSO rows per line do not certify independent drug-treatment repeats. The 17 matched pairs are dose identities, not 17 replicated surfaces. Pairwise contrasts among 52 lines have at most 51 independent coordinates per condition; they are not 1,326 independent experiments.

Under the conditional observation model in the owning [readout contract](../2026-10-30-drug-discovery-capability/evidence/readout_contract.md), write `S[c,p] = log2(g[c,p]) - k[p]`. Stable line-specific recovery allows:

```text
D[c,d,p] = S[c,p] - S[d,p] = log2(g[c,p] / g[d,p])
J[c,d,A,B] = D[c,d,A+B] - D[c,d,A] - D[c,d,B]
```

`D` is relative selectivity. With exact constituent doses, `J` is differential departure from a multiplicative fold reference. Neither identifies absolute synergy, cell killing, healthy-tissue safety or clinical benefit. Treatment-dependent differential recovery can invalidate even the relative contrast. The exact released-column transformation remains unqualified; these equations do not silently certify that `growth_rate` has this scale. No `D` or `J` values were computed.

Rhaister already owns economical prediction from measured query-response panels using ridge and an additive fallback. Its inspected Emerald Bay sensitivity evaluation filters to single-drug conditions. A combination-target extension could be useful incremental work, but would not by itself test this state-update mechanism. We did not substitute that benchmark merely to obtain scores.

## Two limited mathematical boundaries

### A common scalar law with independent unknown offsets

Let a shared differentiable pointwise function `F` of two scalar inputs obey, on a connected open domain, for all input pairs and all locally admissible independent shifts:

```text
F(x+a,y+b) - F(u+a,v+b) = F(x,y) - F(u,v).
```

Differentiating at zero shift makes the gradient equal at every point, so `F(x,y)=alpha*x+beta*y+gamma`. Additional justified zero-exposure identities can recover the ordinary additive-log reference; zero measured effect is not a zero-exposure identity.

This only restricts this common local function class and the specified two-dimensional offset family. It does not exclude nonlinear prediction from full contrast vectors, drug/dose/context inputs, calibrated absolute folds or independently measured states. Under only `a=b`, nonlinear `phi(x-y)` remains admissible. Finite observed support does not establish the open-neighborhood premise. A qualified absolute anchor for each constituent condition removes the particular input-offset ambiguity; it does not identify dynamics or make ordinary nonlinear response-surface estimation novel.

### Even ideal concurrent trajectories need not determine order

For a symbolic control-system witness, start at `(x,y,z)=(0,0,0)` and let:

```text
x' = u,  y' = v,  z' = a*u*y + b*v*x.
constant u,v for time t: z = (a+b)*u*v*t^2/2
A then B, integrated exposures U,V: z = b*U*V
B then A:                            z = a*U*V
```

Consider two backgrounds c,d. In world 1, `(a_c,b_c)=(0,2)` and `(a_d,b_d)=(1,1)`; in world 2, use `(2,0)` for c and keep d unchanged. With `log2(g)=-z`, every constant-coadministration absolute and corresponding pooled trajectory agrees between worlds. Nevertheless, at `U=V=1`, the A-then-B cross-background log-fold contrast is **-1 versus +1**. All folds are positive and at most one. Equal component exposures and total observation time can be used in both worlds.

This demonstrates nonidentification over this stipulated family even with richer, noiseless concurrent observations. It is not a fitted biological model or proof of order effects in the actual cultures. It does not refute prediction of the concurrent surface. The common initial state and observation family matter: varied known initial states can supply information separating a and b. A single pooled ordered contrast identifies a coefficient difference across backgrounds, not both backgrounds' individual coefficients. An absolute anchored endpoint plus the stipulated family and known sums can identify an individual coefficient; arbitrary biological dynamics remain unqualified.

The source principle is classical noncommuting control. LaValle's *Planning Algorithms* (2006), chapter 15, section 15.4.2, Example 15.10/Eqs.15.83-15.85, gives the nonholonomic integrator `a=-1,b=1`. The nonnegative fixed-sum pair of worlds above is an elementary derivation using that structure, not a new book theorem or an imported cellular controllability result. No inverse drug controls are assumed for the two forward schedules.

## A constructive measured-state opening, with a direct failure test

For illustration only, suppose an independently observed state `q` lies in `(0,1)` and:

```text
U_A(q) = q + theta_A*q*(1-q),  theta_A in [-1,1]
ell_B(q) = -beta_B*(1-q).
```

The update stays in `(0,1)`. An exact interior pre/post-A observation identifies the toy `theta_A`; qualified B contrasts across distinct known states identify `beta_B`. With matched A-only schedule controls, the conditioned cross-background contrast is:

```text
D[c,d,A_then_B] - D[c,d,A_only]
  = beta_B*(q_c-q_d)*[1 + theta_A*(1-q_c-q_d)].
```

Equal initial state differences can thus yield different conditioned contrasts when the state sums differ. A reserved background provides a falsifying prediction. This is algebraic identification inside a specified toy family, not a real sample-size result, an identified defense pathway or a recommendation to fit this equation to the current table. Noisy or near-boundary measurements can be poorly informative. Ordinary nonlinear prediction given the same states and transitions can express the equation exactly.

The hidden-state rival must preserve **every observed transition and B challenge**, not just baseline inputs. For example, let an unobserved persistent history marker be absent on all observed training histories and affect B only after an unobserved target history, without changing measured q or its observed transitions. Two models can then agree on all legal observations and disagree at that target. A generic added term that changes observed training challenges is not an observationally equivalent counterexample.

A decisive closure challenge is a controlled **same-measured-state, different-history** B response. A reproducible difference rejects q-only sufficiency within those conditions. Agreement supports only the tested range. For stochastic biology, the claim concerns the relevant conditional response distribution: equal population mean q can hide different mixtures or selection. Dose, elapsed time, carryover/washout, preparation and measurement must be controlled. Order effects alone establish neither state sufficiency nor mediation. Independent manipulation of the proposed state would strengthen a mediation claim.

## Prior work and archive decisions

Original sources were read at selected-passage level (P), not as a complete survey. The exact scope is in the [scout record](scout/initial_independent.md), [citation-edge followup](scout/citation_edge_addendum.md), [control followup](scout/control_order_addendum.md), [developer analysis](developer/mechanism_analysis.md) and [independent initial review](challenge/initial_review.md).

| Prior | Decision-relevant ownership or condition |
|---|---|
| Rhaister, [DOI 10.64898/2026.06.09.731197](https://doi.org/10.64898/2026.06.09.731197), model/Emerald Bay sections | Measured-response ridge reconstruction and additive fallback are existing methods. New target labels do not establish a new update mechanism. |
| Bengio et al., [arXiv:1901.10912v2](https://arxiv.org/abs/1901.10912), section 2/Proposition 1 | Adaptation-regret representation learning is prior art. Its unchanged-module argument requires correct conditionals/parents and an actual unchanged mechanism. |
| Perry et al., [arXiv:2206.02013v2](https://arxiv.org/abs/2206.02013), assumptions/section 5 and protein-network application | Sparse mechanism-shift scoring already has a biological application. Required environment samples, common graph and sufficiency assumptions are not supplied by relabeling scalar endpoint rows. |
| Choi, [arXiv:2610.34204v1](https://arxiv.org/abs/2610.34204), Lemma 1/section 2.4 | Stable measurement requires appropriate injectivity for identification; identical target sensor laws can accompany distinct outcome shifts. A 2026 preprint, not peer-reviewed confirmation or a demonstrated baseline-RNA solution here. |
| LaValle, [author-hosted chapter 15](https://lavalle.pl/planning/ch15.pdf), section 15.4 | Ordered-flow/nonholonomic structure is classical. Its smooth observable control assumptions do not become cellular facts by analogy. |
| MuSyC, [DOI 10.1038/s41467-021-24789-z](https://doi.org/10.1038/s41467-021-24789-z), Box 1/Methods including Par43 | Shared nonlinear pharmacology and state-transition surfaces are prior art; concurrent versus staggered exposure matters. The previous episode already established exact ordinary-subfamily overlap. |

The archive investigator navigated all 49 registered study closures, the route inventory and 213 study-index finding rows, then selected full reports and primary passages. This is broad archive triage, not reproduction of all studies or reading of every original.

Two older leads remain **NOT_REOPENED**. For LeSavage matrix-response transport, the initial missing-original premise was stale: the author manuscript had already been recovered historically. The actual source crosses multiple regimens mainly in patient 1; FOI is a fixed mixture, and other donors have gemcitabine. A single request for the advertised 34KB workbook returned HTTP403/134 bytes; no new processed full-curve/replicate contract was obtained. For sparse even-cycle contrast transport, no independently fixed catalog, sparsity or transport observation changed the old failed premise. Ordinary regression under a renamed dictionary is not a reopening. See the preserved [initial assessment and explicit correction](investigator/initial_findings.md).

The preceding [RNA episode](../2026-10-31-rna-intervention-selection/report.md) also remains stopped: final rMATS rows depend on treatment counts, and an observed intersection cannot recover the frozen reference/control event universe. One new documented SCSP API attempt again failed TLS hostname validation. No bypass, equivalent retry or processed small-molecule splicing data followed. Access failure is not evidence of biological failure.

## ProteinTalks: improved source qualification, no admitted functional panel

Sun et al., *An operational perturbation proteomics-based virtual cell model*, Nature 2026, [DOI 10.1038/s41586-026-11001-9](https://doi.org/10.1038/s41586-026-11001-9), is not a new project source. A historical seven-lineage PTV1 replay already stopped its own ppODE/feedback configuration. That configuration-specific result does not veto a genuinely different question. The public reference-library abstract-only row incompletely summarizes historical project reading.

This round acquired the **publisher subscription preview**, not full main Methods, and the original Supplementary Information PDF. Selected original passages add concrete qualification:

- SI physical p2, S1C, describes 24h viability and three biological repeats; the binary threshold is deferred to unavailable main Methods. SI p2-3, S2, describes 11 protein time points over 0-60h in three TNBC lines and sample/plate/dose/time/replicate metadata. Molecular trajectories alone do not establish paired independent functional endpoints.
- SI p5, S7, removes inconsistent repeated efficacy labels. That is outcome-dependent selection, so the resulting matrix is not an unselected fully orthogonal panel.
- SI p6, S10, describes selected predicted drug-pair validations, fixed 1uM bosutinib in specified arms, triplicate wells and Bliss-based delta-Emax. Triplicate wells do not certify independent cultures.
- SI p8, S16-17, describes selected PALLD/control HCC38 validation with docetaxel and fixed carboplatin 10/40uM, with three independent biological repeats. SI p14's untreated-normalized `1-viability`, clipping to [0,1] and sigmoid fit applies explicitly to Fig.5G-I; it is not a universal label protocol.
- Public Extended Data 3D reports TYMS/control HCC1143 capecitabine curves with three independent cultures. Extended Data 1 distinguishes 2-4 biological protein samples per cell/drug/time from pools/technical runs. These are source-owned selected validations, not new held-out discoveries here.

The advertised 18-table ZIP has Content-Length **126,369,414 bytes**. Its body was rejected unread under the worker's bounded acquisition slice; this is not global inaccessibility or scientific disqualification. No sheets, schemas or treatment values were inspected. A bounded local inventory did not locate that exact package. The old 18,709-byte phenotype file was checked by hash only against its historical manifest, without parsing labels. Current repository metadata and a 1,058-byte README were acquired; no new code snapshot was executed or stored.

The [source check with superseding followup](investigator/proteomic_source_check.md) preserves exact passages, historical correction and accession/file links. It establishes a better route to a later schema decision, not an affordable authenticated matched-function panel or a new mechanism. We did not download the large package merely because no positive candidate emerged.

## Decision and the smallest useful next evidence

**Do not fit I002.v1 on the current table as an intervention-update experiment.** Preserve the measured-state question conditionally. Three different additions answer three different questions:

1. Qualified per-condition anchors address the scalar input-offset ambiguity. They do not test a sequence law.
2. Authenticated matched A-then-B/B-then-A schedules can test order sensitivity, with exposure/time/carryover and independent-preparation controls. They do not alone test closure.
3. An independently specified pre/post-A state, a controlled subsequent B challenge and matched schedule controls permit a state-update test. Multiple informative states, reserved backgrounds/histories and independent preparations are needed to assess shape, transport and uncertainty. No universal replicate count follows from the toy algebra.

If cheap existing processed observations meet item 3, freeze one minimal test before values: source transitions fit the shared update; an untouched background/history tests its prediction. Compare equally informed nonlinear conditional prediction, controlled state-space learning, response-panel ridge/covariance conditioning, matrix completion, additive and simple schedule rules. Use a dose-response/combination surface only where its observation requirements hold. Charge every state assay and probe to all arms; evaluate the closure prediction and useful regimen selection, not just embedding quality. Wrong predictions reject the specified restriction; ties leave its extra value unestablished. Better prediction alone does not prove mediation or novelty. Agent work still requires exceptional Virtual Cell value first.

## Review, actual activity and preservation

The fresh challenger received the frozen question, raw original extracts, metadata and allowed measurement contract before seeing developer/scout persuasive arguments. Its [initial review](challenge/initial_review.md) was saved first; the later [metadata check](challenge/metadata_followup.md) independently reproduced counts and freeze hashes. The report incorporates three refinements without rewriting the freeze: pooled coefficient differences versus absolute coefficients; hidden-state alternatives preserving all observed challenges; and mean state versus sufficient conditional population state. Final content review is recorded in [review/content_review.md](review/content_review.md).

Requested settings were investigator `gpt-6.1-sol/medium`, scout `gpt-6.1-sol/high`, developer `gpt-6-astra/max` and fresh challenger `gpt-6.1-sol/high`. The developer co-developed the candidate and is not its independent reviewer. Root synthesized and verified primary passages. Effective serving settings, native tokens, model cost and total tool cost remain unknown.

Actual extension use: **17 HTTP attempts / 5,947,468 known decoded body bytes**, counting receipt rows, redirects/errors and recorded bodies. Root used 1/0 bytes, investigator 9/1,974,355, scout 7/3,973,113 and challenger 0/0. The extension ceiling was 48 attempts/128MiB over three shared evidence passes. The prior RNA 95 attempts/256,840,201 bytes remains separate; together these two episodes use 112/144 attempts and 262,787,669/402,653,184 known bytes. Wire traffic is not certified. See [usage.json](usage.json) for actual ledgers and null telemetry.

There was no scientific-model fit, synthetic benefit experiment, weight acquisition, installation, author-code execution, protected-outcome numerical/semantic use, commit/upload, cleanup or core promotion. Source-owned selected findings and historical aggregate results were read/disclosed; they are not untouched validation. Metadata audit execution in `D:/anaconda/envs/maestro/python.exe` is distinct from model fitting. Byte-only preservation hashes are distinct from interpreting outcomes.

The library owner registered four identities and six reading files: four donor originals, the explicitly labelled partial publisher preview, and scientific SI. Final [owner verification](library_verify_final.json): **217 identities / 181 reading files / 23 code snapshots / 16 sources with official stored code**, errors/warnings/changed snapshots empty. Main-source states are 26 abstract-only, 89 HTML, 36 PDF, 57 pending and 9 restricted. ProteinTalks main Methods remains unavailable; a preview in a supplement-format technical slot is not full text or scientific SI. No new code snapshot was added. This is targeted acquisition with selected-passage reading, not an exhaustive 2025-2026 novelty survey.

The [process record](PROCESS.md), [integration receipt](review/integration_change_receipt.json) and [final preservation check](review/final_preservation.json) bind this round to its actual files. All old study records and pre-existing work are retained. This bounded episode closes an admission decision while the scientific goal remains unachieved.
