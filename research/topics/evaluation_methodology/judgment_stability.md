# Reproducibility as an admission test for a judgment source

What a decision model's influence should depend on before any biological outcome exists.
Labels: **implemented**, **partial**, **design**, **measured**.

---

## 1. The problem the live run exposed

The typed decision model answers the same unchanged state differently each time. First seen on
one pair, then measured properly: twelve identical calls to `jev-1.13.0` on one unchanged state,
2026-09-25. **Measured.**

| Question | Kind | Verdict | Agreement | Answers over 12 calls |
|---|---|---|---:|---|
| `decision_separation` | noul | stable | 1.00 | `True` twelve times, p from 0.88 to 0.90 |
| `evidence_sufficiency` | score | stable | 1.00 | level 2 twelve times |
| `best_separating_action` | choice | **unstable** | **0.41** | `orthogonal_rescue` 7, `proximal_activity` 4, `engagement_shift` 1 |

Three things follow, and the third was not expected.

**The instability is specific.** Two of three scopes reproduce perfectly. A gate that fired on
everything would be useless; this one fires on the one question that can change which action is
bought, and on nothing else.

**The rate is far from the threshold.** Agreement 0.41 against a gate at 0.60, so 0.59 of
decisions consulting this question would not reproduce. Not a borderline call.

**The model's reported distribution is not its sampling distribution.** The captured call
reported `{orthogonal_rescue 0.31, proximal_activity 0.30, engagement_shift 0.28, none 0.08,
rna_low 0.03}`, whose collision probability is 0.27. The measured agreement over twelve calls
was 0.41 — half again as concentrated. §5 listed this as an assumption that might not hold; it
does not. **A source's own probability vector cannot stand in for reproducibility, and the only
way to know how often an answer repeats is to ask again.**

The architecture's answer to an unreliable source is the judgment ledger: score its probability
forecasts by Brier against later measurements, down-weight, then revoke. That answer has a gap
this case falls straight through:

1. **Grading needs outcomes, and outcomes are the scarce thing.** The whole system exists to buy
   few measurements. A scope may wait indefinitely for the five graded records the ledger needs.
2. **Until then the scope has full influence.** `JudgmentLedger.summarize` returns
   `weight = 1.0, provisional = True` below `minimum_records`. That is influence granted, not
   earned, and it contradicts the guarantee the README states.
3. **A Brier score over an irreproducible source is itself irreproducible.** What would be
   estimated is a property of a distribution of answers, not of an answer.

A separate defect turned up while checking this: `JudgmentLedger.weight()` is called by tests
and by nothing in `src/`. Only the binary `is_revoked` is consulted, so the graded band between
`maximum_brier` and `UNINFORMATIVE_BRIER` has never affected anything. **Measured** by reading
every call site.

## 2. What instability costs, exactly

Fix a state. Let the source return probability `P`, random over its own sampling; let the
outcome be `Y` with `P(Y=1) = q`, a property of the world and independent of that sampling.
Write `mu = E[P]`, `sigma^2 = Var(P)`. Then

```
E[(P - Y)^2]  =  q(1-q)   +   (mu - q)^2   +   sigma^2
                 irreducible   miscalibration   instability
```

Three sources of error, cleanly separated. Verified as an identity to 4e-16 over 4,000 random
sources and Monte Carlo at 4·10^5 draws:
[`analysis/judgment_stability.py`](analysis/judgment_stability.py).

**The third term needs no outcome.** It is a property of the source alone, and repeating one
call measures it.

### 2.1 Repetition is a remedy, not only a diagnosis

Answering with the mean of `n` independent calls leaves the first two terms and divides the
third:

```
E[(P_n - Y)^2] = q(1-q) + (mu - q)^2 + sigma^2 / n
```

So repetition buys a Brier reduction of exactly `sigma^2 (1 - 1/n)`, known before any outcome
arrives. Verified at `n = 1, 2, 3, 5, 10` to within Monte Carlo error. This is why a repeated
yes/no answer is **averaged** rather than taking the last call: the average is the estimator the
identity rewards. A choice or a score is not a quantity to average — the mean of option three
and option five is not an opinion — so those take the modal answer. **Implemented.**

### 2.2 The Brier floor is sufficient, and weak

Since `E[Brier] >= sigma^2` for every `q` (checked on 20,000 random cases, zero violations), an
estimated `sigma^2` above the ledger's revocation threshold guarantees revocation whatever the
outcomes turn out to be. But `sigma^2 <= 0.25` for any variable in `[0,1]`, and
`UNINFORMATIVE_BRIER = 0.25`, so the floor fires only for a source alternating between
near-certain yes and near-certain no. A source swinging `+/-0.3` has `sigma^2 = 0.09` and the
floor says nothing. **The floor is a backstop, not the gate.**

## 3. The gate that works: agreement on the decision-relevant value

For a ranking the operative question is not Brier at all. It is whether the *selected option*
changes between identical calls, because that is the fraction of decisions that would not
reproduce. That is measurable with no outcomes and no model of `q`.

- **Compare what can change a decision.** The decided boolean, the chosen option, the integer
  level — never a raw float. Two yes answers at 0.94 and 0.77 agree about everything that acts.
- **Estimator.** The chance two independent calls agree is `sum_v p_v^2`, and
  `sum_v c_v (c_v - 1) / (n(n-1))` is exactly unbiased for it from `n` repeats. Verified against
  its closed form over 300 random distributions. The weight *is* this number: a source that
  reproduces 0.7 of the time counts 0.7, with no tuning constant standing in for it.

### 3.1 How many repeats

Revoking at agreement below 0.6, over 20,000 simulated runs per cell:

| repeats | false revocation of a 0.95-stable source | detection of a three-way random source |
|---|---|---|
| 3 | 0.003 | 0.221 |
| 5 | 0.001 | 0.371 |
| 8 | 0.000 | 0.737 |
| 12 | 0.000 | 0.946 |

Three repeats are safe and blind. Eight is the smallest usable gate, twelve is comfortable.
Below eight the verdict is `insufficient` and says so, rather than reporting a number as though
it were settled. **Implemented** (`maestro/stability.py`, `RELIABLE_REPEATS = 8`).

**Cost.** The measured call was 517 input and about 112 output tokens, so a twelve-repeat review
costs roughly 6,200 input tokens. Reproducibility is not free, and the default asks once.

## 4. Two rules that follow, and one that does not

1. **A scope that can change which action is bought is held stricter than one that comments.**
   `ACTION_RANKING` must show reproducibility before it may move a selection;
   `PLAN_CRITIQUE` may speak while unmeasured. **Implemented** as `DECIDING_SCOPES`.
2. **Calibration and reproducibility fail independently, so the weaker governs.** A source can be
   well calibrated on average while answering differently each time, and perfectly repeatable
   while repeatably wrong. `effective_weight = min(calibration, stability)`. **Implemented.**
3. **Not asking twice is not a finding.** The rule that an unmeasured ranking must be silent was
   written, tested and **withdrawn**: it converted absence of evidence into evidence of
   unreliability, and it dropped information silently, which is the failure this architecture
   names elsewhere as its own. An unchecked preference is still said, and carries
   *"Reproducibility unchecked: this preference was asked once, and the source is not
   deterministic."* Only a **measured** disagreement withholds it.

## 5. What this does not establish

The decomposition assumes the source's randomness is independent of the outcome, which is what
lets `E[PY]` factor. That holds for a model judging a fixed state and fails if the same
randomness drives both the answer and the world — not a case that arises here, but the identity
is not general.

Agreement measures reproducibility, not correctness. A source that returns the same wrong answer
every time scores 1.0 here and is caught only by the Brier ledger, which is why both run and the
weaker governs. Neither measures whether the question was worth asking.

The reported probability vector and the sampling distribution are different objects, now
measured to differ by half again (§1). The reported vector still belongs in the record: it is
what the Brier ledger grades, because Brier scores a stated belief against an outcome. It is the
*stability* weight that must come from repetition and never from the model's own numbers.

## 6. Acceptance tests

1. Two identical calls returning different options revoke the ranking scope, with no outcome
   recorded and the Brier ledger still reporting `provisional`.
2. Three agreeing calls report `insufficient`, not `stable`.
3. Two yes answers at different probabilities agree; the probability spread is still reported.
4. A repeated yes/no judgment carries the mean probability; a repeated choice carries the mode.
5. One evaluation behaves exactly as before and records no stability.
6. An unmeasured ranking finding still reaches the planner, labelled unchecked.

All six: [`../tests/test_judgment_stability.py`](../tests/test_judgment_stability.py).

## 7. The falsification test, run

Two ways this construct could have been worthless were written down before it was measured.

**"The gate never binds."** If repeated calls agreed at or above 0.95 across scopes, the cost
would buy nothing. **Refuted**: agreement 0.41 on the ranking scope, against 1.00 on the other
two. The gate binds, and it binds selectively.

**"The ranking has no influence to earn."** If the deterministic layer overrides the ranking
anyway, the question should be removed rather than gated. **Open.** In the one measured critic
run the selection was `rna_high` with the critic on and off, so on that case the ranking changed
nothing — which is the boundary holding, not evidence that the ranking never matters. Settling
it needs cases where the deterministic check leaves a genuine tie.

A third possibility went unwritten and is now the more interesting one: §8.

## 8. What the unstable arm actually chose

Over twelve calls the model selected `orthogonal_rescue` seven times, `proximal_activity` four
and `engagement_shift` once. In the fixture menu those are, respectively, the action whose
premise **nothing supplies**, and actions three and two supplier steps from executable. The one
executable decisive action, `rna_low`, drew a reported probability of 0.03 and was never chosen
— **0 of 12 selections were executable.**

The state the probe sends does not carry the supplier topology. The state the critic sends does,
and the same question there returned `rna_low`. Two different states, one draw each, so nothing
is established: this is a hypothesis with an obvious confound, not a result.

`local_verification/topology_ablation.py` runs it properly — one contrast, one menu, one
question set, repeated in both arms, with the topology block as the only difference. It reports
the share of selections the agent could execute and the agreement in each arm, because *what* is
recommended changing and *how stably* it is recommended are different findings. Predictions
worth recording before it runs:

- If the executable share rises with the topology present, reachability in the state is doing
  work, and the design claim that the model should see the action graph is supported.
- If agreement also rises, the instability is partly a symptom of an underdetermined state
  rather than of the model, and the cheaper fix is a better state, not more repeats.
- If neither moves, the model is not reading the block, and putting it there is cost without
  effect — which would be worth knowing before more is written into that state.

An executable action is one the agent can run, not one worth running. This measures neither
biological quality nor correctness.
