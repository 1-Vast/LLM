# ASRG frozen experiment protocol

Everything below is **proposed**. Nothing here has been run. The protocol is written so that
it can be frozen, digested and registered before any hidden outcome is revealed, in the same
style the repository already uses for replay cases.

## 1. Freezing order

1. Write `asrg_protocol.json`: objective coordinates, weights `W`, acceptable loss `τ`,
   splits, arms, query budgets, metrics, ablations, rejection criteria, random seeds. Record
   its SHA-256 and the runner's SHA-256.
2. Rebuild the pilot table from the public asset; record asset digest, row counts, refused
   conditions and measured wall time.
3. Fit coordinates, predictor, κ and conformal bands on **training folds only**.
4. Write `public_plan.json`: task identifiers, candidate menus, goals, the initial action per
   task, budgets, and digests of every fitted artifact. This is what the policies see.
5. Only then compute outcomes. Reveal is per-query through the replay view; final scoring
   happens after all plans are frozen.

A plan that cannot be reconstructed from step 1's digest is not a result.

## 2. Splits

| Split axis | Rule | Claim it licenses |
|---|---|---|
| Molecular identity | All doses of one compound in one fold | Held-out compound |
| Bemis–Murcko scaffold | Analogues in one fold | Held-out chemistry |
| Cell line | Leave-one-line-out as a **separate** task family | Held-out context (explicit extrapolation) |
| Plate and replicate | Never split across; they are the independent-unit key | Replicate stability |

Two task families are reported separately and never pooled: **in-distribution** (held-out
compounds in trained contexts) and **held-out context** (a cell line with no adequate training
support, which is an extrapolation test, not an interchangeable coordinate system).

## 3. Goals

A goal must be computable by every arm from public information and must never come from the
hidden outcome of a candidate in that task's menu. Two admissible constructions:

- **Reference-action goal.** The measured response of a reference condition that is excluded
  from the menu and from the anchor. Its identity is public; its vector is public.
- **Program-score goal.** A prespecified target in the objective coordinates (for example:
  reduce a proliferation score, hold a stress score, raise a differentiation score), with `W`
  fixed in the protocol.

`W`, `τ` and the objective coordinates are fixed at step 1 and never tuned against outcomes.

## 4. Arms, at matched information and matched budget

The candidate generator, the scorer's inputs, the query cap and the final selector are held
fixed across arms. Only the named component changes.

| # | Arm | Anchor | Notes |
|---|---|---|---|
| 0 | `keep` | — | Do nothing; the floor every arm must beat |
| 1 | Random legal candidate | — | Seeded; the other floor |
| 2 | Tanimoto retrieval, nearest predicted | predicted | Non-parametric; strong per the 2026 unseen-chemistry preprint |
| 3 | Fixed PCA + nearest predicted | predicted | Connectivity-Map-style matching; **equals the analytic-gain rule by identity** |
| 4 | Ridge predictor + nearest predicted | predicted | The mandatory linear baseline |
| 5 | Small conditional network + nearest predicted | predicted | Same inputs as 4 |
| 6 | Cheap full enumeration | predicted | Feasible: the library is finite |
| 7 | ASRG-A | measured, κ=1 | Unshrunk anchor |
| 8 | **ASRG-B (primary)** | measured, κ̂ shrinkage + `tr(WΣ)` penalty | The claim under test |
| 9 | ASRG-C | as 8 + reachability certificate | Adds abstention |
| 10 | ASRG-D | as 9 + learned operation-value model | Only if 8 already wins |
| 11 | Ordinary same-budget search | measured | Greedy by predicted loss, **no** shared-error update |
| 12 | LLM controller (optional) | measured | Identical numeric table; cannot add candidates, change `W`, or see reveals |
| 13 | E0-DIR | — | Runs only if its prerequisites hold; they currently do not |

Arm 3 is included precisely because arms 7–10 must be shown to beat it; an ASRG result that
merely reproduces arm 3 is a null result.

Provider-backed arms get one format-only retry; a provider failure is recorded as one lost
case with its reason, not a lost run, reusing the existing runner behaviour.

## 5. Budgets

Query budgets `K ∈ {0, 1, 2, 4}` expensive measurements per task, identical across arms.
Report per arm: laboratory cost in wells and turnaround days (shared controls charged once),
provider spend, and compute. An action with no declared price refuses the sequence by name
rather than being counted as free.

## 6. Metrics, reported separately

Never averaged into one score.

1. **Perturbation-effect error** against matched control: gene-level MSE, and
   **perturbation-specific** error after removing the per-context mean shift, because common
   metrics reward systematic perturbed-versus-control variation.
2. **Ranking**: Spearman correlation over the menu; top-1 and top-5 hit rate.
3. **Decision quality (primary)**: measured regret
   `L_W(selected) − min_a L_W(measured a)` over the menu, on the **actual selected candidate
   against its hidden measured response** — never a latent target scored by the model that
   produced it.
4. **Efficiency**: regret reduction per expensive query; total compute and API cost.
5. **Calibration and support**: conformal coverage of the loss band; support coverage;
   abstention rate; abstention precision (of tasks flagged unreachable, how many really were).
6. **Stability**: variation across true replicates, while dose, time and context effects are
   preserved. A rule that flattens a real dose response is a failure, not a robust rule.

**Analysis unit:** the compound cluster (molecular identity, and scaffold for the chemistry
claim). Intervals are cluster bootstraps on paired per-task differences, in the style of the
repository's existing `paired_interval`. Cells are not replicates.

## 7. Leakage guards, checked by assertion

- Coordinates, predictor, κ̂ and conformal bands fitted on training folds only.
- Gene or feature selection from training rows only.
- Normalisation refitted on training compounds for the external branch (the released
  spherized profiles were fitted across all plates).
- L1000 landmark genes only; inferred genes are model outputs.
- The treated response of a held-out candidate never enters its own prediction. Assert this by
  running the predictor with the candidate's row removed and comparing digests.
- The goal is never derived from a menu candidate's hidden outcome.
- Identity assertions before any arithmetic: feature schema, gene order, basis identifier,
  preprocessing, control-pool identifier. Equal vector length is not compatibility.

## 8. Diagnostic ablations

| ID | Manipulation | Expected if the claim is true |
|---|---|---|
| A1 | Scramble predicted effect **directions**, preserve magnitudes | Gain collapses to the random arm. If it does not, the metric is magnitude-driven — stop and fix the metric |
| A2 | Change the available action set, hold the initial error fixed | Selection and the certificate track the menu; regret changes with what is reachable |
| A3 | Propose a subgoal no registered candidate supports | Abstain with `insufficient_support_in_library`; never silently pick the nearest candidate |
| A4 | Permute plate and batch labels | No gain survives; a surviving gain is batch-driven |
| A5 | Supply `e0` from a different task | The anchored arms lose their advantage. If they keep it, the "anchor" is not doing what is claimed |
| A6 | Force κ = 0 and κ = 1 | Brackets arm 8 between arms 3 and 7 |
| A7 | Remove the top generic response axis | Separates a generic-axis effect from compound-specific geometry |
| A8 | Replace the measured anchor with the predicted anchor | Arm 8 reduces **exactly** to arm 3; a code-level identity check |

## 9. Prespecified rejection criteria

The claim is rejected, and the recommendation reverts to simple ranking, if any of these holds.

- **H1**: the cluster-bootstrap 95% interval for regret(arm 8) − regret(best of arms 2–6)
  includes zero, or favours the baseline, at K = 0 and at every tested K.
- **κ̂**: its bootstrap interval includes zero. Prediction errors are then candidate-specific,
  the anchoring mechanism is absent, and arm 7 is expected to be actively harmful.
- **H2**: false escalation by the certificate exceeds 10% of flagged tasks.
- **H3**: the shared-error update gives no interval-separated improvement over arm 11 at any
  K ≥ 1.
- **H4**: action-predictable coordinates do not beat fixed PCA at equal rank; then keep PCA.
- **Learned policy**: arm 10 does not separate from arm 9 at equal real cost; then drop it.
- **Enumeration dominance**: if arm 6 with a measured anchor matches arms 8–10 at equal real
  cost, recommend enumeration and do not claim an agent advantage.
- **A1 or A5 fails**: the result is an artifact; report it as such and stop.

## 10. What no outcome of this protocol licenses

A passing result licenses exactly one sentence: at equal candidate sets and equal query
budget, measurement-anchored, support-certified selection lowered the measured regret of the
selected action relative to nearest-signature ranking with the same cheap predictor, in the
tested contexts. It does not license a claim about target engagement, mechanism, efficacy,
biological reachability, or transfer to an untested cell line, assay, time point or modality.
