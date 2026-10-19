# Conditional pharmacological action units: report

2026-10-19. Mandate: "Counterexample-Driven Discovery and Compositional Synthesis of Pharmacological Action Units". Data:
Jaaks et al. 2022 GDSC anchored combination screen (CC BY 4.0, figshare). This dataset was exposed by MAESTRO in October,
so **all evidence here is development evidence**. No LLM or paid call, no sealed tier opened, nothing committed.

## Decision: NARROW

The programme as briefed is **STOP**. That covers learned action units that transfer to unseen implementations, an
agent that designs diagnostic experiments, and dual-core compositional redesign. None of the steps those claims need
passed on this data.

**What survives** is narrow, and on exposed data:

- **(a)** Substitutability between same-target drugs is a reproducible, **partner-conditional** property, not a
  context-conditional one. One counterexample with a partner corrects predictions for that partner in other lines.
- **(b)** For the interaction endpoint, the annotated same-target sibling (PHAROS-style mechanism matching) is **not**
  a better reference for an unseen drug than functional similarity. Functional similarity beats it (post hoc).

Neither result changes an equivalence decision at the pre-registered margin.

## Results in the brief's priority order

| # | Question | Result | Evidence |
|---|---|---|---|
| 1 | Reproducibility | **CONDITIONALLY QUALIFIED.** Swap contrasts reproduce across seeding dates, but the reproducible part is partner-specific, not partner x line. | REPRO.json, DECOMP.json |
| 2 | Learnable beyond baselines | **No** for interaction (NOT_BEYOND_BASELINE); **inconclusive** for efficacy. | LOFO_*.json |
| 3 | Generalises to unseen implementations | Only through functional similarity or potency, which baselines already provide. A learned substitution model adds nothing. | LOFO_*.json, POSTHOC.json |
| 4 | Refinement value | **Prediction yes, decision no.** Partner-specific counterexample refinement cuts interaction error by 17% but flips equally many decisions right and wrong. | REFINE_*.json |
| 5 | Agent value | **Bounded at zero** for the pre-registered decision: even probing every unit gives no accuracy gain on interaction. Not run (no paid-call authorisation). | REFINE_*.json design block |
| 6 | Dual-core synergy | **Not testable**: no component has decision value to combine. | none |

### 1. Reproducibility (PLAN_P1, written before any response column was read)

- **Units and replicates.**
  - Library-side units are dose-matched: same anchor and concentration. Anchor-side units match the anchor's own
    concentration rank.
  - Replicates are separate seeding events (`DATE_CREATED` from the raw plate file), split alternately within each line.
- **Interaction S** (`SYNERGY_DELTA_AUC`, primary), target-overlap swaps:
  - Unit reliability r = 0.31 (line-bootstrap CI 0.25 to 0.51, drug-pair CI 0.23 to 0.43; 1,568 units including the
    composite-anchor deviation, 1,027 without).
  - Reproducible SD 0.029 against a per-half noise SD of 0.042.
- **Where the reproducible variance sits** (S, composites excluded):

  | Component | Covariance |
  |---|---|
  | **Partner-specific** | **0.00052** |
  | Pair mean | 0.00009 |
  | Line-specific | 0.00008 |
  | Partner x line | 0.00007 (CI −0.00008 to +0.00014) |

  - Conditional share 0.08 (CI −0.09 to 0.15), below the pre-registered 0.25, hence CONDITIONALLY QUALIFIED.
  - The swap is partner-conditional (A' substitutes for A with some partners, consistently across lines) but not
    context-conditional.
- **Annotation helps but does not make drugs equivalent.**
  - Target-overlap swaps have about half the reproducible SD of unrelated swaps (0.029 vs 0.049 per unit).
  - 25% of partner-level target swaps still fail at epsilon = 0.03 AUC.
- **The interaction swap is not potency.** The half-1 single-agent difference explains R² 0.015 of the half-2 swap
  contrast.
- **Efficacy E** (`SYNERGY_OBS_AUC`) is mostly potency: R² 0.49 from the single-agent difference, more than the half-1
  contrast itself explains (0.33).

### 2-3. Learnability and unseen implementations (PROTOCOL_P2, frozen before prediction)

- Design: leave one implementation out. 27 evaluable held-out drugs and 1,950 partner-level units. Each held-out drug
  keeps its single-agent profile but none of its combinations.

| MSE (partner-level Delta) | B0 sibling copy | B1 partner mean | B2 potency-matched | B4 cold-start ridge | B5 functional kernel | **M learned substitution** |
|---|---|---|---|---|---|---|
| Interaction S | 0.000855 | 0.000775 | 0.000953 | 0.000715 | **0.000601** | 0.000894 |
| Efficacy E | 0.00591 | 0.00526 | 0.00127 | 0.00120 | 0.00422 | **0.00106** |

- **S verdict: NOT_BEYOND_BASELINE.**
  - M is 49% worse than the best baseline, B5 (CI −85% to −22%).
  - Partner-specific features add nothing (M-noP − M CI −0.000002 to +0.000012).
  - Partner-level noise ceiling: half-split r = 0.69.
- **E verdict: INCONCLUSIVE.**
  - M is +11.5% better than B4 (CI −15% to +30%).
  - Partner-specific features help (CI +0.00003 to +0.00032).
  - Equivalence AUROC: B2 0.85, M 0.84. Decision accuracy: B2 0.78, M 0.76.
- **Validation screen** (38 units, 15 implementations; a separate measurement but exposed): INCONCLUSIVE on both
  endpoints. The ordering matches: B4 is best on S; M and B2 are best on E.
- **POST HOC** (POSTHOC.json; not in the protocol), interaction endpoint:
  - The functional kernel beats sibling copy: B0 − B5 = +0.00025 (CI +0.00011 to +0.00042), better in 20 of 27
    implementations.
  - Sibling copy does not beat the identity-free partner mean: B0 − B1 = +0.00008 (CI −0.00012 to +0.00031).
  - **Heterogeneity.** Within tight families (EGFR/HER2: Lapatinib, Sapitinib, Afatinib) sibling copy is the best
    method (MSE about 0.0002-0.0003). Within loose multi-kinase "families" (Sorafenib, Dasatinib) it is the worst
    (0.0017-0.0025).
  - So the annotation-overlap definition of an action unit is too coarse. Whether a measured binding profile (e.g.
    Klaeger 2017 kinobeads) separates the tight cases is the open question.

### 4-5. Counterexample refinement and design (PROTOCOL_P3, frozen before any phase-2 result existed)

- Design: one probe line per (implementation, partner); the target is the mean swap over that partner's remaining lines.
- Shrinkage: w = tau² / (tau² + sigma_w²), with both variances estimated from training sibling swaps.

| Arm (prior B0 = annotation equivalence) | S MSE | E MSE |
|---|---|---|
| R0 no refinement | 0.000857 | 0.00592 |
| **R1 probe the same partner** | **0.000713** | **0.00404** |
| R2 probe a different partner (generic control) | 0.000948 | 0.00505 |
| R3 pooled probes of all other partners | 0.000984 | 0.00631 |

- **Interaction S: PARTNER_SPECIFIC_REFINEMENT.**
  - The same-partner probe beats no probe (C1 +0.00006 to +0.00024), a different-partner probe (C2 +0.00017 to
    +0.00032) and pooled probes (C3 +0.00014 to +0.00044).
  - The result holds with the potency-matched prior.
  - A different-partner probe is *worse* than no probe. The counterexample carries partner-specific information, not
    a generic offset.
- **No decision value.**
  - Accuracy at epsilon 0.03 goes 0.751 → 0.752. Right flips (1.3%) about equal wrong flips (1.2%).
  - In the budgeted design, the deterministic ambiguity designer (0.749) does no better than random (0.750), no probes
    (0.750) or probing every unit (0.750).
  - So no designer, LLM or otherwise, can add decision value to this decision on this data. That is the agent-value
    bound.
- **Efficacy E.**
  - Refinement helps only against the annotation prior (GENERIC_REFINEMENT_ONLY; accuracy 0.42 → 0.59).
  - Against the potency-matched prior it is NO_REFINEMENT_VALUE and costs accuracy (0.78 → 0.75).
  - Single-agent potency already carries what a probe adds.

## What this does and does not show

- **Shows, on exposed data:**
  - Same-target substitution is a reproducible partner-conditional relation on the interaction scale.
  - One measured counterexample sharpens that partner's prediction.
  - For unseen drugs, functional similarity and potency matching are the baselines to beat, and annotation-based
    mechanism matching is not one of the strong ones.
- **Does not show:**
  - A decision benefit of any kind.
  - Transfer of learned substitution boundaries to new implementations (the frozen M failed).
  - Context-conditional action units.
  - Level M (mechanistic) equivalence.
  - Agent or dual-core value.
  - Independent confirmation. **BLOCKED**: the only untouched candidate, Vis 2024 Data S1, is not local, has 19
    combinations and would need download permission.
- **Novelty, against PRIOR_ART.md:**
  - The tested relation (equivalence margins, partner-conditional failures, counterexample refinement) is not in
    PHAROS or the other verified prior work.
  - The positive part, partner-specific refinement, is a prediction-level effect only.
  - The learned-boundary part failed, consistent with MAESTRO's earlier null on program revision.

## If anyone continues (NARROW scope only)

1. **Level M test.** Download Klaeger 2017 kinobeads affinities (needs permission). Pre-register whether binding-profile
   similarity predicts which same-annotation pairs substitute: tight EGFR vs loose multi-kinase. This is the one open
   question with a clear falsifier.
2. **A decision that binds.** At this noise level, epsilon = 0.03 equivalence calls do not move. A useful endpoint would
   be a combination-redesign choice (pick A' for a partner when A is unavailable) with a pre-registered utility. It
   needs untouched data.
3. Do not build agent or dual-core layers on this until one component shows decision value.

## Files

- **Protocols:** PLAN_P1.md, PROTOCOL_P2.md, PROTOCOL_P3.md.
- **Freezes:** FREEZE.json, FREEZE_P3.json.
- **Disclosures:** DEVIATIONS.md.
- **Results:**
  - CENSUS.json (design only);
  - REPRO.json (gate);
  - DECOMP.json (secondary);
  - LOFO_*.json and lofo_units_*.csv (phase 2);
  - REFINE_*.json (phase 3);
  - POSTHOC.json.
- **Prior art:** PRIOR_ART.md.
- **Verification:** `python verify.py` (ALL OK), or with `--data` to also check the source MD5.
