## (1) Single candidate

**Proposal — “Paired-Endpoint Sign-Disagreement Frontier” (PESDF) for probe selection and terminal nomination.**

Core claim, stated as a narrow structural constraint rather than a new predictor:

> Because RCN and RCF share the malignant numerator but have different denominators, their *disagreement pattern* across a probe set carries information about whether a drug's apparent depletion is denominator-driven (control composition artifact) or numerator-driven (cancer-count reduction). This disagreement is not recoverable by fitting a bivariate model to (RCN, RCF) alone at the nomination stage, because the useful object is the *conditional sign pattern* of the disagreement given the charged DMSO composition overlap, and it must be fixed *before* the target control composition is revealed.

This is a candidate, not a proven win. It is the only operation I can defend as structurally distinct from the rejected list, and its value is testable with the described budget. If the falsifier in (6) fires, the honest verdict is “no viable new core.”

## (2) Exact small state, update, terminal decision

**Notation.** Patient group $g=1..95$; drug $d=1..65$; probe set $P$ fixed before target control composition; shortlist $S$, $|S|=k$ fixed, $P\cap S=\varnothing$. Observed per probe: $\mathrm{RCN}_{gd}$, $\mathrm{RCF}_{gd}$ (raw, paired). Charged DMSO composition vector $c_g \in \{0,1\}^{13}$ (overlapping parent/subtype categories — treat as multiset indicators, not disjoint fractions).

**State (small, explicit).** For each drug $d$ define only two scalars per patient group and two pooled scalars:

- Disagreement sign: $s_{gd}=\mathrm{sign}(\mathrm{RCN}_{gd}-\mathrm{RCF}_{gd})\in\{-1,0,+1\}$.
- Magnitude: $\delta_{gd}=|\mathrm{RCN}_{gd}-\mathrm{RCF}_{gd}|$.

Pooled per drug: $\bar s_d=\frac{1}{|G_d|}\sum_g s_{gd}$, $\bar\delta_d=\frac{1}{|G_d|}\sum_g\delta_{gd}$.

**Composition conditioning (new line).** Fit *only* a 13-coefficient logistic on probe-patient groups:
$$\Pr(s_{gd}\neq 0 \mid c_g)=\sigma(w^\top c_g + b),$$
with $w,b$ estimated by plain maximum likelihood on probes. This is a *nuisance* model of whether disagreement is composition-associated; it is not a biological latent. No latent biology is invented: $w$ is only “does charged DMSO composition predict nonzero disagreement.”

**Residual disagreement score (the new operation, marked):**
$$\boxed{\;\rho_d=\bar s_d-\hat{\mathbb E}[s_d\mid c]\;}\quad\text{(NEW)}$$
where $\hat{\mathbb E}[s_d\mid c]$ is the probe-estimated composition-expected sign. This is a *composition-adjusted sign residual*, not a shrunk mean, not a kernel, not isotonic, not a mixture.

**Update rule.** Probes only: estimate $(w,b)$ once; compute $\rho_d$ for all 65 drugs. No refit after reveal beyond the single nuisance logistic on probes. This is deliberately minimal to avoid a hidden full-refit reduction.

**Terminal decision.** Nominate
$$S=\operatorname{TopK}_{d\notin P}\ \rho_d,\qquad k \text{ fixed a priori.}$$
Tie-break by $\bar\delta_d$ ascending (prefer small-magnitude disagreement, i.e., more stable sign). No threshold calibration is claimed; K is fixed, not tuned on target.

**Inherited-improver object (if pursued).** The only inheritable object is the *pair* $(w,b)$ of the composition-nuisance logistic plus the fixed sign convention. A fresh equal-budget test of “improved ability to discover further improvements” would be: on a held-out source patient-group split, does the probe-estimated $(w,b)$ from split A improve the *ranking* of nominate-vs-not decisions on split B relative to an untrained $w=0$? That is a discovery-ability test, not a predictor test. I flag it as a secondary, conditional claim; the primary candidate does not require it.

## (3) Required observations and which exist

| Required | Exists? |
|---|---|
| Paired raw RCN, RCF per probe drug × patient group | Yes (released feedback) |
| Charged DMSO composition, 13 overlapping categories | Yes (stated) |
| Probe batch fixed before target control composition | Yes (design constraint) |
| Fixed shortlist disjoint from probes | Yes (by construction) |
| Patient grouping (95 groups) | Yes |
| Independent well labels | **No** — blocks any well-level variance/uncertainty claim |
| Known healthy survival | **No** — RCF is malignant depletion only; candidate must not claim healthy safety |
| Dose response / schedules / combinations | **No** — candidate stays at 10 µM, 24 h |
| Numeric outcomes decoded for this scout | **No** — candidate is stated symbolically only |
| Source-only threshold calibration / headroom | Future gate — not claimed |

The candidate is therefore *information-legal*: it uses only paired endpoints and composition, never invents healthy survival, never uses scaled extrema sheets, never assumes independent wells.

## (4) Closest conventional method and exact difference

Closest conventional: **fit a bivariate regression of $(\mathrm{RCN},\mathrm{RCF})$ on composition $c$, then rank by a predicted composite.** That is ordinary multivariate conditioning — explicitly rejected as a new-core claim.

Exact difference: conventional conditioning models the *joint mean* of the two endpoints and ranks by a fitted linear combination. PESDF instead (i) collapses each endpoint pair to a *sign of disagreement*, (ii) models only the *probability of nonzero disagreement* as a function of composition, and (iii) ranks by the **residual of the mean sign after subtracting its composition-expected value**. The distinction is structural: the target quantity is a composition-adjusted *sign residual*, not a conditional mean of either endpoint or of a linear composite. A conventional bivariate conditional-mean model does not, in general, reproduce $\rho_d$ because sign is a nonlinear functional of the pair and the nuisance is fit on sign, not on the means. If an implementation can be shown to reduce exactly to a bivariate conditional-mean ranker under the same information, the claim collapses — and I state that as a real risk, not a dismissal.

## (5) Primary 2025–2026 papers

I cannot verify with confidence any specific 2025–2026 paper that directly supports *this exact* composition-adjusted sign-residual operation for paired derived pharmacologic endpoints. I will not fabricate titles, arXiv IDs, or DOIs.

Honest status: **no high-confidence primary citation found for the exact operation.** The nearest genuinely relevant literature I can name without inventing identifiers is the general line on *sign/rank-based robust statistics for paired dependent endpoints* and on *composition/nuisance adjustment in pharmacogenomic screens*; I do not have verified 2025–2026 identifiers for either, so I mark them **unverified / not cited**. This absence is itself evidence relevant to the novelty assessment: the operation is plausibly new but also plausibly under-motivated by existing literature.

## (6) Smallest falsifier and demotion condition

**Falsifier (single, minimal):** On the *source* patient-group split only (no target reveal), compare PESDF's probe-estimated $\rho_d$ ranking against a plain bivariate conditional-mean ranker fit on the same probes and same composition features, using a held-out source criterion of “does the top-$k$ nominated set overlap the top-$k$ by an independent source endpoint aggregate.” If PESDF does not beat or at least differ systematically from the conventional ranker on source held-out groups, the new operation has no demonstrated decision value.

**Demotion trigger:** If (a) the falsifier shows no source-held-out advantage, **or** (b) a proof/construction shows $\rho_d$ is an affine or monotone transform of a bivariate conditional-mean score under the same information, **or** (c) the sign-disagreement is dominated by $\delta\approx 0$ (ties) so $\bar s_d$ is near-degenerate — then demote to “merely useful conventional study” or “no viable new core,” respectively.

I explicitly do **not** claim any imagined outcome as evidence. Numeric outcomes are undecoded here; the falsifier is a design, not a result.

## (7) Verdict

**Novel-core: conditional / unproven.** The composition-adjusted sign-residual is a genuinely additional exact operation not on the rejected list, and it is information-legal under the stated constraints. But:

- Its novelty is fragile: it may reduce to ordinary conditional-mean ranking under the same information (risk (b) above).
- Its decision value is untested and cannot be claimed from this scout.
- It does **not** by itself deliver “inherited improvement of the improver”; the inheritable object $(w,b)$ is small and its discovery-ability test is secondary and unproven.
- No verified 2025–2026 primary citation supports it.

Therefore the honest classification is: **candidate novel-core operation, presently unproven, with a named falsifier; not a confirmed advance, and not “presently impossible”** — it is testable with the authenticated information. If the falsifier fires, the correct outcome is **no viable new core** for MAESTRO under these constraints, and the remaining honest option is a useful conventional study of composition-adjusted paired-endpoint ranking, not a new mechanism.