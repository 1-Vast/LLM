# Program revision: protocol (frozen before the development arms and before any future outcome)

Study: `research/program_revision_20261017`. Written 2026-10-17 after Stage A, which read source development data only (`STAGE_A.json`). After `freeze.py`, a change to any file it hashes is a deviation and goes in `DEVIATIONS.json`.

## 0. Decisions taken in Stage A, before this freeze (source development data only)

- Endpoint: "both replicates required" was replaced by "at least one of X2/X3", because the former left 38% of pairs unknown.
- Strong model: rank 20, λ 2, chosen by development query hits per line among ranks 5/10/20/30/40 and λ 1/2/5/15.
- Diagnosis screen: the hierarchical composition screen (12 strongest atoms) became a full screen with a redundancy filter and a diversity filter. Reason: S4c. The S4 controls were rerun under the final screen; `STAGE_A.json` holds the final run.
- Bugs fixed:
  - after an accepted edit, the committed-prediction record lost its digest, so the next evaluation failed;
  - the planted-effect oracle double-counted, and was replaced by the generating-mean ceiling.
- Identifiability and semantic-duplicate refusals were added after S2/S3 design review.
- Disclosure: before this freeze, two code checks ran on development data only.
  - A smoke run of all eight arms: 1 round, ≤ 12 candidates each, 30 unique deepseek-flash calls, USD 0.088 upper bound.
  - A dry evaluation on development query lines with the smoke libraries.
  - In the dry evaluation, exploit-first feedback (4.39 hits/line) beat fixed-probe feedback (4.24) and AFA (4.33) on development lines.
  - These checks saw development outcomes only. No novel-drug or held-out-line outcome was opened. Cached LLM responses whose prompt digests recur are reused, not re-sampled.

## 1. Question

Can MAESTRO improve future decisions by autonomously revising shared executable intervention-response programs whose applicability is identified by affordable measurements?

A program counts only if it changes predictions or actions **and** earns value on held-out observations. Writing a program is not a result.

The concrete test has three parts:

- On PRISM, does a library of conditional response programs improve nomination decisions on future cell lines and future lineages, beyond a strong inductive multitask model with ordinary Bayesian updating?
- Is that library built by the MAESTRO loop: counterexample diagnosis, committed predictions, a distinguishing experiment, then accept or reject?
- Does the gain hold beyond conventional search over the same language, beyond a fixed pre-specified library and beyond conventional adaptive acquisition, at equal measurement budgets?

The loop and the LLM are assessed separately.

Four questions are kept apart throughout:

- repairing a defect;
- improving the predictor;
- improving decisions;
- the LLM's contribution.

Stage A had already shown, on development data, that measurement dominates the decision ladder. 8 probe wells add +1.33 hits per line over the DNA panel. 32 probe wells add +2.4. The textbook seed programs add +0.04, not significant. Synthetic planted programs that are linear in legal features are absorbed by the strong model. The question is therefore whether revision finds structure that the strong model plus measurement does not already capture.

## 2. Data, unit, endpoint, costs

- **Screen.** PRISM Repurposing 19Q4 secondary screen, HTS002, 2.5 µM. Replicates X1, X2 and X3 are ComBat-corrected log2 fold changes. Lines must pass STR, appear in the HTS002 pooling table, and have CCLE expression and mutation data (478 lines). One treatment per compound core (1,288 drugs).
- **Unit of decision.** One (cell line, campaign). Per line, nominate K = 10 drugs from the candidate set, which is the 966 source drugs (or the 322 novel drugs in the N strata).
- **Endpoint: a qualified hit for pair (d, c).** All four conditions must hold:
  - at least one of X2 or X3 is available;
  - every available confirmation replicate is below 0;
  - their mean is ≤ −1;
  - their mean is ≤ (median over SOURCE lines of drug d's confirmation mean) − 1.

  A pair with neither replicate is UNKNOWN: it is never counted as inactive and is reported separately. X1 never enters the endpoint; it is the probe readout.

  This endpoint replaced a "both replicates" rule during Stage A, before the freeze. Under the both-replicates rule 38% of pairs were unknown; under this rule 15% are (`STAGE_A.json` A0). Missingness is not outcome-related: P(X1 ≤ −1) is 0.330 among known pairs and 0.329 among unknown pairs.
- **Primary utility.** Qualified hits among the 10 nominations with known outcome, per line. Secondary measures:
  - unknown nominations per line;
  - erroneous progressions, i.e. known non-hits among nominations;
  - in Stage C, confirmed hits per 28 wells, rounds, and wells to 3 confirmed hits.
- **Costs.** All measurements are charged in wells and rounds:

  | Measurement | Cost | Turnaround |
  |---|---|---|
  | Probe (X1 of a source drug on the line) | 1 well | 1 round per batch |
  | Confirmation (X2 + X3 of a pair) | 2 wells | 1 round per batch |
  | Novel-drug pooled probe (one well on one PRISM pool of source lines) | 1 well per drug | — |
  | Targeted DNA panel (AmpliSeq Cancer Hotspot v2, 50 genes) | 1 assay unit | 0 wells |
  | RNA-seq (I3 only) | 1 assay unit | 0 wells |
  | Development knowledge acquisition: distinguishing experiment | 2 wells per newly revealed (drug, development query line) pair | — |
  | Development knowledge acquisition: measurement edit | 1 well per development query line | — |
  | Conventional stepwise search (reads all known query outcomes) | 2 wells per outcome | — |

  - A failed well or pair (missing value) is still charged.
  - Compute is reported in seconds. LLM spend is reported in USD from the token ledger: deepseek-flash, cap USD 1.00, at USD 0.30 input / 1.20 output per million tokens as an upper bound.

## 3. Splits and access rules

- **Drugs.** Structure groups are InChIKey connectivity merged with Butina clusters at Tanimoto distance 0.5 on Morgan radius-2, 2048-bit fingerprints. Whole groups are taken in salted-hash order into NOVEL until NOVEL holds ≥ 25% of drugs. This gives 966 source drugs and 322 novel drugs in 258 groups.
  - Max Tanimoto of a novel drug to the source set: median 0.316.
  - Novel drugs with a source analogue at Tc ≥ 0.6: 8.
  - Novel drugs whose MoA token is seen in source: 247. Whose target token is seen: 219.
- **Lines.**
  - Future lineages: breast, gastric, kidney, ovary, pancreas, skin, urinary tract (180 lines). These are the 7 lineages with 8–45 lines and the smallest salted hashes.
  - Future lines: 67 lines in the other lineages, with salted hash < 0.2.
  - Source: 231 lines.
  - Source lines are grouped into 10 development projects (lineages with ≥ 8 source lines, plus "other"). Within each, lines are support (hash < 0.5; 128 lines) or query (103 lines).
- **Access.**
  - `Domain(open_future=False)` replaces every novel-drug response and every non-source-line response with NaN at load time. Stage A, the development arms and all revision use only this view.
  - `evaluate.py` without `--dry` refuses unless FREEZE.json matches and all registered libraries exist. Its first opening writes ACCESS.json, which is write-once and records the LIBRARIES.json digest. It refuses later if LIBRARIES.json has changed.
  - Development query outcomes are reused across candidate edits. They are development data, never confirmation.
  - The future strata are opened once for the registered analysis. Any further look is exploratory and is labelled as such.
- **Independent confirmation.** None is available in this study: the future strata come from the same screen, platform and release. Section 10 names the confirmation set.

## 4. Models, language, agent loop (frozen constants)

- **Strong model (S).** y = a_d + b_c + U_d·V_c with rank 20 and ridge λ = 2, fitted by 12 ALS iterations on observed means of all available replicates. This was selected on development query lines over ranks 5–40 and λ 1–15.
  - New line: the line state [b_c, V_c] has a ridge prior from legal features, with a leave-one-out covariance. Probe readouts update it by Bayesian linear regression, and a probed drug's own readout is fused directly.
  - New drug: the drug state has a ridge prior on fingerprint plus MoA and target tokens. Pooled-probe readouts update it.
  - Drug-specific ridge on the same inputs is a second static comparator.
- **Information conditions for a new line.**

  | Condition | Inputs | Wells |
  |---|---|---|
  | I0 | lineage | 0 |
  | I1 | I0 + DNA panel | 0 (zero-observation) |
  | I2 | I1 + 8 probe wells (few-observation) | 8 |
  | I3 | I2 + RNA-seq PCs | 8 |

  The probe design is fixed: greedy A-optimal for S on all source lines, recomputed and checked by `evaluate.py`.
- **Program language.**
  - A program is a scope × a state.
    - Scope: `moa:TOKEN` or `target:GENE`. It needs ≥ 5 source drugs from ≥ 2 structure groups.
    - State: atom | and | andnot | mul, with ≤ 3 atoms.
    - Atoms: `mut:GENE` (DNA panel), `lin:TISSUE`, `probe:CORE` (a design probe readout), `b` (posterior line offset), and `expr:GENE` (I3 only).
  - Binary gates need ≥ 5 positive source lines from ≥ 2 lineages, and ≥ 5 negative lines.
  - Every interaction must be identifiable from drug and line offsets on the source observation pattern.
  - The library holds ≤ 12 programs.
  - No drug or line identifier exists in the language, so no lookup table can be written.
  - Loadings are fitted on cross-fitted (5 inner folds) out-of-sample residuals of S, with drug loadings shrunk toward a scope-shared loading (τ = 20). Novel drugs use the shared loading.
  - This is a conditional low-rank, mixture-of-experts-style correction with observable gates. It is not new as a model class.
- **Edits.**
  - add(scope, state);
  - retire(key);
  - split(key, gate) into an and/andnot pair, or a mul pair for a continuous state;
  - replace_state(key, state);
  - narrow(key, scope);
  - measure(key = design probe to drop, gate = new probe, optional scope and state). Joint arms only.
  - Refusals are named: UNKNOWN_PROGRAM, DUPLICATE_PROGRAM, NO_STRUCTURAL_CHANGE, SEMANTIC_DUPLICATE, NO_SEMANTIC_CHANGE, PROGRAM_TOO_COMPLEX, MEASUREMENT_NOT_IN_CONDITION, PROBE_NOT_IN_DESIGN, UNKNOWN_SCOPE, SCOPE_TOO_NARROW, UNKNOWN_ATOM, GATE_TOO_RARE, GATE_TOO_COMMON, GATE_NOT_BINARY, INTERACTION_NOT_IDENTIFIABLE, LIBRARY_CAPACITY, UNPARSABLE_*, PROBE_IN_USE, PROBE_ALREADY_IN_DESIGN, UNKNOWN_PROBE, llm_*.
- **MAESTRO loop.** It runs 2 rounds over the 10 projects (20 steps). Each step:
  1. **Diagnosis.** Compute standardised residuals of the current library on the project's support lines, which are predicted as new lines from the other source lines. Find scope-average residual associations with every legal atom and with all compositions: and/andnot pairs of every binary atom, and continuous × binary products. There is no main-effect hierarchy, because Stage A S4c showed that a hierarchical screen misses a pure interaction the rule would accept. A composition that correlates ≥ 0.95 with one of its parents is dropped. A cluster is skipped when an already-listed cluster has scope Jaccard ≥ 0.8 and state |r| ≥ 0.7. Joint arms also see unmeasured source drugs whose readout tracks a scope residual.
  2. **Proposal.** Up to 6 edits.
  3. **Validation.**
  4. **Commitment.** Commit predictions and nominations on all development query lines, and record a digest.
  5. **Distinguishing experiment.** It covers pairs whose nomination flips between the current and edited library, plus the 30 pairs with the largest standardised disagreement. Outcomes are revealed only after the commitment.
  6. **Acceptance.** All three conditions are needed: log-likelihood ratio ≥ 3.0; hits(edited-only) − hits(current-only) ≥ 1; and, for an add edit with a stated direction, a fitted shared loading with that sign. At most one edit is accepted per step: the largest hit gain, then the largest LLR.
  - Every candidate, refusal, digest, outcome summary and decision goes to `trajectories/<arm>.jsonl`.
- **LLM proposer (deepseek-flash only).**
  - It gets the same diagnosis packet: legal atoms, panel genes, lineages, probe names and MoA, allowed scopes, library with fitted signs only, top residual clusters, previous test outcomes (decision, reason, hit gain), and the grammar.
  - It never sees an outcome value, a held-out project or a coefficient value. It cannot set a number.
  - Malformed output is refused by name and that step proceeds with no LLM edits.
  - Responses are cached by full-prompt digest in `tmp/program_revision_20261017/llm_ledger.jsonl`.

## 5. Development arms (same bench, same budget: ≤ 6 candidates per step, ≤ 120 evaluated candidates)

| Arm | Start | Proposer | Loop | Measurement |
|---|---|---|---|---|
| seed_fixed | seed (10 textbook programs) | none | none | fixed |
| stepwise | seed | marginal screen of top-100 global clusters on ALL query outcomes, then forward additions under the same thresholds | conventional model selection | fixed |
| maestro_enum | seed | enumerative (clusters → add / split / replace / retire) | MAESTRO | fixed |
| maestro_llm (PRIMARY) | seed | deepseek-flash | MAESTRO | fixed |
| maestro_enum_empty / maestro_llm_empty | empty | as above | MAESTRO | fixed |
| maestro_enum_joint / maestro_llm_joint | seed | as above + measurement edits | MAESTRO | edited jointly |

The seed library is MEK×BRAF, RAF×BRAF, MEK×KRAS, MEK×NRAS, EGFR×EGFR, PI3K×PIK3CA, MDM×TP53, mTOR×PTEN, CDK×RB1 and AKT×PTEN, written before any program result. "Fixed vs editable" is seed_fixed vs maestro_*. "Response-then-measurement vs joint" is maestro_* vs maestro_*_joint.

## 6. Stage B: frozen decisions on future projects

- **Training.** All source drugs × all 231 source lines.
- **Targets.** future_line (67) and future_lineage (180), reported pooled and per stratum.
- **Settings.** Zero-observation (I0, I1) and few-observation (I2, plus I3 for the RNA comparison) are reported separately.
- **Libraries.** Each library is restricted to the programs whose measurement program is purchased under that condition: no probe atom at I1.
- **Arms.**
  - S (I0 to I3);
  - drug-specific ridge (I1, I2);
  - each library under its condition;
  - joint libraries with their own 8-probe design;
  - conventional adaptive acquisition (AFA): 8 probes, 1 per round, greedy decision-weighted variance reduction over the current top 30. Run with and without the primary library.
- **Primary family** (few-observation I2, pooled strata). The statistic is per-line paired difference in hits.

  | Hypothesis | Contrast |
  |---|---|
  | H1 method vs strong | maestro_llm − S |
  | H2 method vs conventional search | maestro_llm − stepwise |
  | H3 LLM value | maestro_llm − maestro_enum |
  | H4 editable vs fixed | maestro_llm − seed_fixed |

  - The interval is a cluster bootstrap with clusters = line lineage (17 lineages, 2,000 draws). p is a one-sided sign flip over cluster means, Holm-adjusted across H1–H4.
  - A contrast is CONFIRMED if mean ≥ +0.10 hits per line, the 95% lower bound > 0 and Holm p < 0.05. It is HARMFUL if the upper bound < 0. Otherwise it is NOT_CONFIRMED.
- **Program attribution.** Leave-one-program-out at I2 for maestro_llm, maestro_enum and stepwise: full library minus library without that program, on future lines.
- **Secondary contrasts.** Unadjusted and labelled exploratory: zero-observation versions; enum, stepwise and seed vs S; empty-start arms; joint vs sequential; AFA vs fixed design; library on AFA; RNA vs probes; probes vs panel; S vs ridge. All are reported per stratum.
- **N strata (unseen drug groups).** Per line, nominate 10 of the 322 novel drugs.
  - On known source lines (I2 contexts), and jointly novel on future lines (I1 and I2).
  - Each in two settings: zero-observation (structure and annotation only) and few-observation (one pooled well per novel drug on the source PRISM pool with the most source lines; that pool's lines are excluded from targets).
  - Arms: S, the additive potency-plus-sensitivity control (a_d + b_c), and each library with shared loadings.
  - Clusters are line lineage.

## 7. Stage C: complete policies under equal budgets (28 wells per future line)

- **Policies.** All are on the I2 fold with the same model.

  | Policy | Measurement | Confirmations | Rounds |
  |---|---|---|---|
  | fixed_probes_then_confirm | 8 fixed probes | 10, in one batch | 2 |
  | fixed_probes_feedback | 8 fixed probes | 5 + 5, each batch updating the line state | 3 |
  | exploit_first_feedback | none | 5 + 5 + 4 with feedback | 3 |
  | afa_probes_feedback | 8 adaptive probes | 5 + 5 | 10 |

- **Arms.**
  - S with every policy;
  - seed_fixed, stepwise, maestro_enum and maestro_llm with fixed_probes_feedback and exploit_first_feedback;
  - maestro_llm with afa_probes_feedback;
  - the joint libraries with fixed_probes_feedback using their own design.
- **Outcomes.** Confirmed qualified hits per line; unknown confirmations; rounds; wells to 3 confirmed hits.
- **Contributions.**
  - Structural contribution: the same policy with library minus without.
  - Total contribution: maestro_llm + fixed_probes_feedback minus each conventional policy (exploit-first feedback, fixed-probe feedback, AFA).
- **Knowledge-acquisition cost and payback.** Development wells × the baseline yield (hits per well of S + fixed_probes_feedback) / gain per line = the number of future lines needed to repay those wells. If the gain is ≤ 0, the cost is never repaid.

## 8. Synthetic and implementation checks (Stage A, reported, not re-run after freeze)

- **S1 state aliasing.** I1 has no access to a hidden state; I2 probes measure it.
- **S2 crossed design.** The interaction is not identifiable and the validator refuses it.
- **S3 null edits.** Exact and semantic duplicates are refused with zero credit. A null world tests the false-acceptance rate.
- **S4 planted programs.**
  - (a) linear in a legal feature;
  - (b) a conjunction;
  - (c) a conjunction orthogonalised against linear features: a positive control the strong model cannot absorb.

## 9. Verdicts reported separately

- **Method value:** H1 and H2, plus the Stage C structural contribution.
- **LLM value:** H3, plus maestro_llm_empty vs maestro_enum_empty. If the enumerative loop or stepwise search explains a gain, the LLM claim is withdrawn.
- **Transfer:** gain per stratum (future_line, future_lineage) and on N strata through shared loadings.
- **Independent confirmation:** NOT AVAILABLE in this study.
- **Mechanism:** no mechanism is claimed; programs are predictive abstractions.

## 10. Next confirmation set (named before outcomes)

A different screen release: PRISM 24Q2 REP.1M, already defined and sealed in `knowledge_reality_20261013`, with access authorisation pending. The frozen libraries would be applied unchanged, with lines and drugs not in 19Q4 HTS002.
