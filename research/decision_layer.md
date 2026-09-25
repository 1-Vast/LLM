# The decision layer: belief state, action space, value of information

Formal record of what the agent believes, what it may do, and how it chooses. Labels:
**implemented**, **partial**, **design**.

---

## 1. Belief state

For a case with registered explanation set `H`:

```
B = (C, M, S)
    C ⊆ H              explanations still compatible with admitted evidence
    M = {(f, q, e, u, c, t)}   measured premises: field, quantity, entity, units, context, time
    S : fields → scope  strongest scope each field has earned
```

`scope ∈ {plan_limitation, measurement_feasibility, intervention_implementation,
mechanism_contrast}`, ordered. **Implemented** as `EvidenceState` plus admitted-scope tracking.

### 1.1 Why a set and not a posterior

No component may invent an unmeasured probability. A posterior over `H` would require a prior
and a likelihood that nothing in the system has measured; the numbers would then propagate as
though they were evidence. A set is weaker and honest: it says which explanations remain live.

The cost is that `C` cannot express "mostly `h₁`". That cost is accepted. Where a calibrated
probability genuinely exists — a prediction interval scored against measurements, or a typed
judgment graded by the judgment ledger — it enters as a **ranking input under §3**, never as a
belief over `H`.

### 1.2 Update

Given a result `r` interpreted by rule `ρ`:

```
if  r.quality_passed  and  conditions_match(r, ρ)  and  ρ.scope = mechanism_contrast:
        C ← C \ ρ.eliminates
else:   record the update with its narrower scope; C unchanged
M ← M ∪ ρ.admitted_premises(r)      only when replication ≥ ρ.minimum_independent_units
```

Terminal readings of `C`:

| `C` | Meaning | Response |
|---|---|---|
| `|C| ≥ 2` | Still indiscriminable | Buy a separating measurement, repair the contrast, or defer |
| `|C| = 1` | One explanation survives | A decision may be licensed if its evidence requirement is met |
| `C = ∅` | Contradicted | Revise the premise. **Not** a licence to pick the nearest label |

**Hypothesis-space change.** If a later round presents different explanation identifiers, the
compatible set is rebuilt and the migration is logged; prior updates stay as history, never as
standing conclusions. This prevents a renamed hypothesis inheriting an elimination it never
earned. **Implemented.**

---

## 2. Action space

```
A = A_evidence ∪ A_repair ∪ A_terminal
```

### 2.1 Evidence actions

Each is typed (**implemented**, `maestro/models.EvidenceAction`):

```
a = ( identifier, kind, prerequisites, supplies, interpretation_gate,
      cost, lab_cost(wells, days), distinguishes, expected_outcomes,
      detection_power, context, time, units, quantity )
```

`prerequisites` make the action illegal until measured; `interpretation_gate` leaves it legal
but uninterpretable. Both are obstacles a supplier resolves, so both enter feasibility together
as `required_premises`.

### 2.2 Feasibility from the topology

```
open(a | B)      = { f ∈ required_premises(a) : f ∉ M }
Feasible(a | B)  = open(a) = ∅  ∨  ∃ bounded supplier chain ending at a
```

The supplier graph has an edge `a → s` when `s` supplies one of `a`'s open premises. From it
(**implemented**, `maestro/topology.py`):

- **executable frontier** — actions with no open premise;
- **steps_to_executable** — shortest supplier-chain length, by breadth-first search over
  reversed edges from the frontier; `∞` means no registered chain exists;
- **capability gaps** — open premises no registered action supplies;
- **supply cycles** — strongly connected components where actions only supply each other.

`steps_to_executable` lower-bounds any chain the depth-bounded, no-revisit search can return, so
it prunes that search exactly: only branches that could not succeed are cut. Measured on
adversarial layered menus: expansions fell from 111,112 to a handful, 311 ms to 0.5 ms.

A capability gap is **named, not worked around**. Substituting a weaker action that does not
supply the premise is the failure this construct exists to prevent.

### 2.3 Repair operators and terminal decisions

`A_repair = {keep, local, switch}` — keep the plan, edit within the current plan's
neighbourhood, or switch to a different response pattern before searching. These are **search
operators over the plan**. They are not identified biological causes and must never be reported
as such; the historical `repair_realization` / `repair_hypothesis` labels map onto `local` and
`switch` for comparison only.

`A_terminal` = continue, revise intervention, change intervention mode, preserve or remove a
multi-target activity, revise attribution, defer, stop — applied to the current program only.

---

## 3. Value of information

### 3.1 Objective

For budget `b`:

```
maximize   Σ_{h ∈ C} P(X answers h)  −  λ · cost(X)
subject to cost(X) ≤ b,   Feasible(x | B) ∀ x ∈ X
```

`P(X answers h)` is built from each action's **declared** `detection_power`, with actions
sharing a source cluster contributing once. **Implemented** as exact expected-coverage selection
over small pools, with dependence groups and per-candidate rejection reasons reported.

### 3.2 Three rules that keep it honest

1. **No self-reported probabilities.** A language model's stated confidence is not an input.
   Calibrated probability may enter only from a source the judgment ledger has graded against
   measured outcomes, and only at the weight that grading currently allows.
2. **No assumed submodularity.** Complementary evidence can have zero individual value and high
   bundle value, so greedy information-per-cost ranking is invalid by default. Small pools are
   solved exactly; larger pools report the objective, feasibility, timeout and optimality gap.
3. **Deferral is priced.** It costs its own loss and is never a licensable requirement, so
   always-deferring cannot be the cheapest policy.

A solver optimum is optimal for the declared finite problem. It is not a statement about the
biological value of information.

### 3.3 Measurement-anchored ranking (design, gated)

When the current action has already been measured — the ordinary situation in a repair — the
anchor residual `e₀ = y_obs(a₀) − ŷ(a₀)` is informative about other candidates' prediction
errors *if* those errors are shared within a context. The proposed correction shrinks it by the
out-of-fold error correlation:

```
ỹ(a) = ŷ(a) + κ(a, a₀) · σ²_e / (σ²_e + σ²_m) · e₀
```

With a *predicted* anchor the analytic gain reduces exactly to nearest-predicted ranking, so
that variant is a baseline, not a method. With a *measured* anchor the ranking genuinely differs.
Whether `κ > 0` on real data is the open question and the decisive gate. Derivations and checks:
[`analysis/algebra_checks.py`](analysis/algebra_checks.py); protocol and gates:
[`asrg/`](asrg/00_index.md).

### 3.4 Reachability certificate (design)

Let `S` be the span of predicted changes `δ_a` over the menu and `P` its `W`-orthogonal
projector. Then

```
min_a ‖r − δ_a‖²_W  ≥  max(0, ‖P⊥ r‖_W − max_a ‖P⊥ δ_a‖_W)²
```

If that bound exceeds the acceptable loss, no library action can reach the goal, and the agent
reports insufficient support **before** spending a query. Verified on 3,000 random instances.
Its usefulness is conditional: if candidate effects span the coordinate space the complement is
trivial and the bound is zero. Cheap pre-check — inspect the singular-value spectrum of the
menu's predicted changes; if it is flat, drop the certificate rather than report a bound that
never binds.

---

## 4. Calibrated critics as inputs

Two graded sources may influence ranking, each revocable:

| Source | What it supplies | Grading | Revocation |
|---|---|---|---|
| Virtual cell | Conditional prediction with an applicability domain | Declared intervals against later realized values | Consecutive interval misses revoke that readout and context |
| Typed decision model | Calibrated answers to typed questions | Brier score against measured outcomes | A scope no better than chance is down-weighted, then revoked |

Both are `model_prediction`. Neither can satisfy a premise, eliminate an explanation, or become
a measurement. A revoked source still produces records; it produces no influence.
**Implemented** for both.

### 4.1 Grading is not the only test, and it is not the first one

Brier grading needs measured outcomes, which are the scarcest thing here, and below
`minimum_records` the ledger returns `weight = 1.0, provisional`. That is influence granted
rather than earned, and it cannot see the failure the live run actually found: a source that
answers the same state differently each time.

Reproducibility is measurable with no outcome at all. For a source returning probability `P`
against an outcome with `P(Y=1) = q`,

```
E[(P - Y)^2] = q(1-q) + (mu - q)^2 + sigma^2
```

so instability is a separate error term, charged to the source, and answering with the mean of
`n` calls removes exactly `sigma^2 (1 - 1/n)` of it. For a ranking the operative quantity is
the chance two identical calls select the same action, estimated without bias by
`sum_v c_v (c_v - 1) / (n(n-1))`. A scope that can move which action is bought must show that
agreement before it may break a tie; a scope that only comments may speak while unmeasured,
labelled as unchecked. Calibration and reproducibility fail independently, so the effective
weight is the smaller of the two. **Implemented** (`maestro/stability.py`); derivation,
thresholds and cost: [`judgment_stability.md`](judgment_stability.md).

---

## 5. Error accumulation

### 5.1 Statement

Let `ε_k` be the probability that step `k` introduces an unresolved defect. A constant-`ε`
independence model gives `1 − (1 − ε)^K`, but real errors correlate: a premise assumed early
conditions everything after it. So the quantity to control is not per-step accuracy but whether
an unresolved item can propagate **silently**.

### 5.2 Controls

| Control | Effect |
|---|---|
| Deterministic re-check before adoption | A defect cannot enter the plan by confident assertion |
| Bounded back-prompt naming the violation | One correction attempt, then a recorded failure |
| Named open premises and capability gaps | An unresolved item cannot be absorbed into a summary |
| Calibration ledgers with revocation | A drifting source loses influence rather than compounding |
| Adopted ≠ worked in the repair ledger | An unverified edit cannot read later as a success |

### 5.3 Metrics

- **Per-step admissibility** — fraction of steps the deterministic layer accepts unrepaired.
- **Drift** — per-step admissibility against step index within a case. A declining curve is
  accumulation; a flat curve at equal regret is not.
- **Decision regret** — measured loss of the selected action minus the best in the menu.
- **Revocation events** — how often a source is withdrawn, and whether decisions improved after.

---

## 6. Acceptance tests

1. A judgment or prediction, at any confidence, leaves `M` unchanged and `C` unchanged.
2. Exhausting `C` routes to premise revision, never to a nearest-label decision.
3. An action whose open premises nothing supplies is reported as a capability gap and is never
   silently replaced by a weaker action.
4. Topological pruning returns exactly what the unpruned search returned — verified on 300
   random menus at every depth from 0 to 6, including cycles, gates, negative costs and
   duplicate identifiers.
5. A bundle of individually useless but complementary actions is selectable within budget.
6. Always-deferring does not win the scoring contract.
7. A revoked calibrated source changes no decision, while its records remain readable.
8. A source that answers one unchanged state differently twice is revoked for ranking with
   no outcome recorded, while the Brier ledger still reports `provisional`.
