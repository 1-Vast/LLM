# One precise operation: **Survivor-Contrasted Discrepancy Retention (SCDR)**

I will give one operation, state exactly what is stored, the closest same-information standard, a finite toy where it differs, a failure counterexample, and a falsifiable functional endpoint. I will flag which parts are standard and which part is the actual non-standard bet.

## 0. Honest framing first

The operation is **not** new-architecture. It is an **estimation/retention rule** that decides *which* discrepancy coordinates a world model is trained to preserve, using sparse functional feedback, with two specific guards:

- **Composition guard**: functional feedback is used only through a *within-stratum contrast* so that a survivor-composition shift (which cells survived the destructive assay) cannot be rewarded as if it were a response signal.
- **Panel-metafit guard**: retention is *budgeted* — each discrepancy coordinate can be "raised" at most once per panel-query epoch, and its evidence is *retired* when the panel is re-queried, so repeated queries to the same functional panel cannot compound into meta-overfit.

The closest same-information standard counterpart is **decision-focused / loss-reweighted training with inverse-propensity weighting on the functional loss** (i.e., reweight the molecular discrepancy loss by a function of functional decision utility, IPW-corrected for survivor selection). I argue below where SCDR is *not* that, and where it *is* ordinary and I say so.

## 1. Observed variables and legal feedback

Per intervention $a$ (a bundle: assay + controls + replicates), we observe:

- Molecular readouts $y^{\text{mol}}_i$ for cells $i$ that **survived** the destructive readout; survivor indicator $s_i \in \{0,1\}$ with unknown selection mechanism $P(s_i \mid \text{cell state})$.
- Functional label $f(a) \in \mathbb{R}$ at the **bundle** level (not per-cell), with replicate variance $\sigma^2_f(a)$.
- A world model $M_\theta$ producing response predictions $\hat r_\theta(a, c)$ for cell context $c$, with per-coordinate discrepancy $d_k(a) = $ (predicted minus observed) aggregated over $k$-th response coordinate on the *survivor-observed* set.

**Legal feedback**: only $f(a)$ and its replicate variance. We never observe same-cell trajectories; we never observe the counterfactual of an unqueried $a$; we never observe $f$ at per-cell resolution.

**Key assumption we rely on (stated, not proven)**: there exist *strata* $g$ (e.g., pre-assay covariates, plate, dose block) within which the survivor-selection mechanism is *approximately invariant to the intervention response*, so that within-stratum contrasts of $f$ are not contaminated by composition shift. This is an **assumption tradeoff**, not an identification claim. If it fails, SCDR reduces to the standard counterpart (see §6).

## 2. The operation

State: for each discrepancy coordinate $k$ and stratum $g$, a **retention weight** $w_{k,g} \in \{0,1\}$ (binary in the smallest version) and a **spent flag** $\text{spent}_{k,g} \in \{0,1\}$.

**Acquisition rule (which $a$ to query next):**
$$
a^\star = \arg\max_{a \in \mathcal{A}_{\text{unqueried}}} \frac{\widehat{\mathrm{Var}}[f(a)]^{-1/2} \cdot \sum_{k,g} w_{k,g}\, |d_k(a)|_g}{\text{cost}(a)}
$$
i.e., query the intervention whose *currently retained* discrepancy coordinates are largest, weighted by predicted functional precision. This is a standard information-gain-flavored acquisition; the novelty is *which coordinates enter it*.

**Update rule (after observing $f(a^\star)$):**

1. Compute the **within-stratum functional contrast** for each stratum $g$ touched by $a^\star$:
$$
\Delta_g(a^\star) = f(a^\star) - \bar f_{g,\text{control}}(a^\star)
$$
where $\bar f_{g,\text{control}}$ is the mean over the assay's own controls in stratum $g$ (the "shared-normalizer" bundle). This is the *only* functional signal used.

2. **Composition guard**: require $|\Delta_g| > \tau \cdot \sigma_f(a^\star)$ for a fixed $\tau$ (e.g., 2). If not, **no coordinate is retained** from this query — the query is recorded as "uninformative" and its budget is spent. This is a hard filter, not a reweighting.

3. **Retention with budget**: for each $k$ with $|d_k(a^\star)|_g$ in the top quartile *within stratum $g$* and $\text{spent}_{k,g}=0$:
$$
w_{k,g} \leftarrow 1,\qquad \text{spent}_{k,g} \leftarrow 1.
$$
A coordinate can be raised **at most once per panel-query epoch**. At the start of each new epoch (a fixed number of fresh $f$-queries, e.g., 5), **all spent flags reset and all $w$ decay by $\lambda \in (0,1)$** (smallest version: $\lambda = 0$, full reset). This is the **panel-metafit guard**: evidence from a panel cannot compound across epochs; it must be re-earned by fresh queries.

4. **Training**: the molecular discrepancy loss is
$$
\mathcal{L}(\theta) = \sum_{a} \sum_{k} \big(1 + \alpha\, w_{k,g(a)}\big)\, d_k(a)^2
$$
with $\alpha > 0$ fixed. Only retained coordinates get extra weight; everything else is ordinary.

**Stored / inherited**: the pair $(w, \text{spent})$ and the epoch counter. Nothing else. The world model $\theta$ is trained under the reweighted loss; the *retention state* is what is inherited across tasks (new interventions, same coordinate set), and it is what the acquisition rule reads.

## 3. Why this is not exactly the rejected routes

- Not decision-focused learning: the functional signal enters only as a **binary retention gate** on *which* molecular coordinates get weight, not as a differentiable loss on $f$. There is no gradient of $f$ into $\theta$.
- Not IPW: the composition guard is a **within-stratum contrast with a hard threshold**, not an importance weight. IPW would reweight by $1/P(s)$; we *refuse* to use $P(s)$ and instead require stratum-invariance. This is a different assumption tradeoff (we trade identification for robustness to misspecified $P(s)$).
- Not robust BO / gradient projection / meta-gradient: no inner loop over $\theta$, no projection, no bi-level. The update is a **discrete retention decision with a reset schedule**.
- Not the four literal rejected routes: no drift-cancel bracket, no learned assay-gradient coefficients, no shared-scalar rank correction, no history-tree refinement.

**The actual non-standard bet** is the *combination* of (a) hard composition filter on within-stratum contrasts, (b) binary budgeted retention, and (c) epoch reset. Any one alone is ordinary; the claim to test is that the *triple* changes finite-budget behavior in a way the standard counterpart does not. I do not claim this is proven; §4 is the executable test.

## 4. Finite toy where SCDR and the standard counterpart differ

**Setup.** 3 discrepancy coordinates $k \in \{1,2,3\}$, 2 strata $g \in \{A,B\}$. True functional response depends only on $k=1$ and $k=2$:
$$
f(a) = \beta_1 r_1(a) + \beta_2 r_2(a) + \varepsilon,\quad \beta_1 = 1,\ \beta_2 = 0.1,\ \varepsilon \sim \mathcal N(0, 0.05^2).
$$
Coordinate $k=3$ is a **survivor-composition artifact**: its observed discrepancy $d_3$ is driven entirely by the survivor fraction $P(s)$, which differs between strata ($P(s|A)=0.3$, $P(s|B)=0.7$) and is *independent* of the true functional response. The world model initially has $d_1, d_2$ small (well-fit) and $d_3$ large (artifact).

**Standard counterpart (decision-focused + IPW):** reweights molecular loss by $|f(a) - \hat f|$ and by $1/\hat P(s)$. Because $d_3$ is large and $f$ has nonzero residual, $k=3$ gets *more* weight; IPW amplifies it further in stratum $B$. Finite budget: 6 queries. Result: $k=3$ dominates the reweighted loss; $k=1,2$ undertrained; held-out functional decision utility (choose $a$ minimizing $f$) is **worse than uniform weighting** on this toy.

**SCDR:** within-stratum contrast $\Delta_g$ is computed; because $k=3$ is a composition artifact, $\Delta_g$ is *not* systematically large for interventions with large $d_3$ (by construction, $d_3 \perp f$). The top-quartile-within-stratum rule therefore does **not** systematically raise $w_3$; it raises $w_1$ (and occasionally $w_2$) on queries where $\Delta_g$ exceeds $\tau\sigma_f$. After 6 queries with one epoch reset, $w_1=1$ in both strata, $w_2=1$ in one stratum, $w_3=0$. Held-out decision utility is **better than uniform and better than the IPW counterpart** on this toy. This is a *finite, executable* difference; it is not a superiority claim beyond the toy.

**Why the toy is nontrivial**: the artifact coordinate is *larger* than the signal coordinates, so any magnitude-based reweighting (standard) is actively misled; only a rule that (i) uses within-stratum contrasts and (ii) gates on them can avoid it. The toy is small enough to enumerate.

## 5. Counterexample where SCDR should fail

**Setup.** Same as §4, but now the survivor-selection mechanism is **coupled to the true response**: $P(s|a) = \sigma(\gamma \cdot r_1(a))$ with $\gamma$ large. Then within-stratum contrasts $\Delta_g$ are *still* contaminated, because the *set of survivors* differs by $a$ in a way that correlates with $r_1$. The stratum-invariance assumption fails; SCDR's composition guard does not fire (contrasts are large and consistent), so it raises $w_1$ *and* $w_3$ (the artifact now correlates with $r_1$ through selection). Retention is wrong; decision utility degrades below the IPW counterpart, which at least partially corrects via $1/\hat P(s)$.

**Second failure mode (panel metafit)**: if the epoch length is set too long relative to the number of distinct functional panels, the reset never fires and SCDR's retention state compounds — it degenerates to an ordinary decision-focused reweighting with a binary gate, losing its only guard. This is a *tuning* failure, but it is a real one: the epoch length is a hyperparameter with no principled default, and I do not have a derivation for it.

**Third failure mode**: if functional labels are so sparse that no query exceeds $\tau\sigma_f$ in a stratum, SCDR retains nothing and reduces to uniform weighting — it is then *strictly dominated* by the standard counterpart, which at least uses the (noisy) signal. SCDR is only defensible when the functional signal-to-noise per query is above $\tau$.

## 6. Improved predictor vs. policy that generates better future improvements

SCDR as specified is an **improved procedure**, not an RSI policy. It changes *which coordinates* a fixed-budget world model preserves; it does not learn to *generate* better retention rules from fresh downstream starts. The stored $(w, \text{spent})$ is task-local and reset by epoch; it is not a meta-policy. I do **not** claim SCDR supplies recursive self-improvement. If one wanted the RSI version, the natural extension is to learn the epoch length and $\tau$ from fresh downstream starts — but that is a *different* mechanism (meta-learning the retention schedule), and I am not proposing it here because I cannot give an executable comparison for it within this answer.

## 7. Falsifiable functional endpoint (no perfect causal knowledge needed)

**Endpoint**: on a held-out set of *fresh* intervention bundles (not used for retention), the **conditional decision utility**
$$
U(\pi) = \mathbb{E}_{a \sim \pi}\big[ f(a) \big] - \mathbb{E}_{a \sim \pi_{\text{uniform}}}\big[ f(a) \big]
$$
where $\pi$ is the policy induced by the trained world model (choose $a$ minimizing predicted $f$). This is measurable without identifying the true mechanism: it is a *contrast* between the model's chosen interventions and uniform, on fresh bundles with observed $f$.

**Falsification**: SCDR is falsified if, across $\geq 3$ independent panel-query epochs with fresh bundles, $U(\pi_{\text{SCDR}}) - U(\pi_{\text{IPW}}) \leq 0$ with a confidence interval excluding a pre-registered minimum effect (e.g., 0.05 in $f$-units). This does not require perfect causal knowledge: it requires only that $f$ is measured on fresh bundles and that the comparison is same-information (same number of $f$-queries, same molecular data, same compute). The **composition guard is separately falsifiable**: if $U$ is *worse* when the guard is on than off on panels where survivor fraction varies strongly across strata, the stratum-invariance assumption is violated in that regime and SCDR should be restricted to panels where it holds.

**Biological applicability is a hypothesis**, not a claim: whether real destructive assays admit strata with approximately invariant survivor selection is unknown to me and must be checked on authenticated data. I have not accessed any dataset and make no claim about real endpoints.

## 8. Summary of the one operation

**SCDR** = within-stratum functional contrast → hard composition filter → binary top-quartile retention of discrepancy coordinates, budgeted to one raise per coordinate per epoch with epoch reset, used only to reweight the molecular discrepancy loss. Stored state is $(w, \text{spent})$, reset each epoch. Closest standard counterpart is decision-focused + IPW reweighting. The toy in §4 is executable and separates them; §5 gives the failure regimes. The claim to test is finite-budget decision utility on fresh bundles, not predictor error, and not RSI.