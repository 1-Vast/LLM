# Local verification protocol

The repository's own tests run anywhere. Three things do not, and they are exactly the three that
carry the most unverified risk:

1. **The TypeSafe Jev field contract.** `agent/typesafe.py` was written against documentation the
   build environment could not reach, so every uncertain field is an alias that fails closed with
   a diagnostic. Whether those aliases match the live API is **unverified**.
2. **The live planner.** How often a real model violates the plan contract, and whether the single
   bounded back-prompt recovers it, is a property of the model, not of the code.
3. **The suite with local assets present.** `data/`, `log/` and `dataset/` are git-ignored, and
   `anndata`, `h5py`, `sklearn`, `torch` and `rdkit` are optional. A machine that has them runs
   tests no clean checkout can.

This protocol runs those three, in cost order, and produces a report in a fixed shape so two runs
can be diffed. Phases 0–3 cost nothing and cannot reach a provider. Phases 4–7 spend money.

## Two rules

**Never paste a key, and never paste a raw `.env`.** Every script here reports configuration by
name, presence and length only. `probe_typesafe.py` additionally passes all of its output through a
redactor, so even a provider that echoed the key back could not leak it into the report.

**Fix nothing while collecting.** A failure is the finding. Record it and move to the next phase;
a repair mid-run makes the report uninterpretable.

---

## Phases 0–3 — free, offline, hermetic

```bash
git fetch origin && git status --porcelain    # expect: no output
git rev-parse HEAD origin/main                # expect: the same hash twice
pip install -e ".[test]"
python research/local_verification/run_offline.py
```

This records the environment, runs the suite, drives one full agent loop from the fixture pack in
[`fixtures/`](fixtures), and asserts eleven invariants on the loop's own trace. It writes
`outputs/local_verification/{report.md,report.json,junit.xml,pytest.txt,trace.json}`.

The loop runs with `--planner-template`, `--virtual-cell none` and `--decision-critic off`, in a
throwaway workspace whose provider settings point at a closed local port, with the provider block
overridden in the subprocess environment. **A failure in this phase is a defect in MAESTRO**, not a
provider's behaviour, and no key is needed or read.

The fixture catalogue is built so the answers are known in advance: a four-deep supplier chain
(`engagement_shift` 2, `proximal_activity` 3, `viability_readout` 4), one action whose premise
nothing supplies (`orthogonal_rescue`, which must be reported as a capability gap and never
substituted), and two complementary measurements inside a one-unit budget.

**Suite counts.** Compare your failing set against
[`baseline_without_local_assets.json`](baseline_without_local_assets.json) — 1136 passed, 53 failed,
1 collection error, 19 skipped on a clean checkout with no local assets. Your machine has `data/`
and `log/`, so the set should be **smaller**. The interesting quantities are therefore:

- ids that fail locally but are **absent** from the baseline → a real finding, report in full;
- ids in the baseline that now pass → which local asset or package unblocked them;
- `tests/test_repository_shape.py::test_log_*` → these two read `log/INDEX.md` and its day folders,
  so they are the only two the repository cannot satisfy on its own.

## Phase 4 — the Jev live contract (highest value)

```bash
python research/local_verification/probe_typesafe.py \
  --report outputs/local_verification/jev_probe.json
```

One small evaluation: a yes/no question, a choice whose options are action identifiers, and a 1–5
score. It prints the endpoint it resolved, the response's **shape** (keys and value types), the raw
body, and then the same response as the agent reads it. If the transport fails it does not retry
the request a second time through the parse path, and it reports the HTTP error body, which is
usually the field the provider rejected.

Add `--discover` if it fails: that asks the configured host for `openapi.json` at three locations
and POSTs the same body to five candidate paths, reporting each status. Use it only on failure —
it is five extra requests.

What decides the outcome:

| Result | Meaning | What to send |
|---|---|---|
| Three usable answers | The aliases are right. The integration is verified. | the probe report |
| `response_without_answers;keys=…` | The top-level envelope differs. | the `keys=` list |
| `noul_without_probability_or_boolean;keys=…` | The per-answer field names differ. | the `keys=` list and the raw body |
| `choice_outside_the_declared_options:…` | The model answers with free text, not a listed option. | the value it returned |
| HTTP 404 | The evaluate path is wrong. | the `--discover` table |
| HTTP 401/403 | The key or the auth scheme is wrong. | the status and body only |

Each refusal names the actual keys it saw, which is all that is needed to correct the aliases. A
refusal is a **successful** probe: it is a measurement of the real contract.

Then run the loop with the critic live, and confirm the boundary holds:

```bash
python -m agent "Resolve the genetic-pharmacological discrepancy" \
  --actions research/local_verification/fixtures/actions.json \
  --profile research/local_verification/fixtures/profile.json \
  --hypotheses research/local_verification/fixtures/hypotheses.json \
  --rules research/local_verification/fixtures/rules.json \
  --results research/local_verification/fixtures/results.json \
  --planner-template research/local_verification/fixtures/planner_template.json \
  --virtual-cell none --decision-critic auto \
  --case-id lv-critic --budget 1 --max-rounds 2 \
  --state-directory outputs/local_verification/critic-state \
  --trace outputs/local_verification/critic-trace.json
```

Then compare `critic-trace.json` with the phase-3 `trace.json`, which ran the same inputs with the
critic off. The review is advisory, so the difference must be confined to the `decision_review`
block. `compare_critic_trace.py` beside this file does exactly that comparison and prints a verdict:

```bash
python research/local_verification/compare_critic_trace.py \
  --without outputs/local_verification/trace.json \
  --with outputs/local_verification/critic-trace.json
```

**Reproducibility.** The typed model is not deterministic, so also run the review with repeats
and report what agreement it shows. This is the measurement that decides whether a ranking may
influence anything, and it needs no biological outcome:

```bash
python -m agent "Resolve the genetic-pharmacological discrepancy" \
  --actions research/local_verification/fixtures/actions.json \
  --profile research/local_verification/fixtures/profile.json \
  --hypotheses research/local_verification/fixtures/hypotheses.json \
  --planner-template research/local_verification/fixtures/planner_template.json \
  --virtual-cell none --decision-critic auto --decision-repeats 12 \
  --case-id lv-repeats --budget 1 \
  --state-directory outputs/local_verification/repeats-state \
  --trace outputs/local_verification/repeats-trace.json
```

Twelve repeats is the point at which a three-way-random source is caught 0.946 of the time while
a 0.95-stable source is never falsely revoked; below eight the gate has no power. The cost is
twelve evaluations, about 6,200 input tokens at the rate the probe measured. Report each scope's
`agreement`, `flip_rate` and `verdict` from `decision_review.stability` in the trace.

Three things must hold, and each is a boundary defect if it does not:

- **The check block is identical.** The critic may not change `prerequisites_satisfied`,
  `missing_prerequisites`, `discriminable`, `decision_separating`, `outcome_separated` or `reasons`.
- **Every judgment reads `evidence_kind: model_prediction`.** No other value is legal here.
- **The selection is unchanged**, or the difference is a tie between equally ranked actions and the
  judgment ledger has graded that scope. A judgment moving the selection while ungraded is the
  single most important thing this protocol can find.

The invariants behind this — that a judgment can never satisfy a premise, eliminate an explanation
or become a measurement — are enforced in `maestro/judgment.py` and pinned by tests rather than
written into the trace, so the trace is checked for their *consequences*, as above.

## Phase 5 — the live planner

Drop `--planner-template` **and replace the request string**. The short request used above works
only because the reviewed template hard-codes a well-formed triage; a real interpreter reads it,
finds no target, intervention, context, endpoint or existing observation, and stops at
`no_executable_action` before the planner is ever reached. That is the interpreter working
correctly, and it tests nothing about the plan contract. Use a request that carries what the
fixtures describe:

```bash
python -m agent "In NCI-H596 at 24 h, compound_A at 0.5 uM reduces viability while knockout of \
TARGET_A does not. Decide whether the transcriptional response to compound_A is realised at this \
exposure, and choose the next measurement. Endpoint: transcriptome shift against a matched \
vehicle control." \
  --actions research/local_verification/fixtures/actions.json \
  --profile research/local_verification/fixtures/profile.json \
  --hypotheses research/local_verification/fixtures/hypotheses.json \
  --rules research/local_verification/fixtures/rules.json \
  --results research/local_verification/fixtures/results.json \
  --virtual-cell none --decision-critic auto \
  --case-id lv-planner-1 --budget 1 --max-rounds 2 \
  --state-directory outputs/local_verification/planner-1 \
  --trace outputs/local_verification/planner-1.json
```

Run it **three times** with a different `--case-id` and `--trace` each time. If a run still stops at
`no_executable_action`, report the interpreter's `missing_information` list verbatim — that is a
finding about the interpreter's admission rule, not a failure to work around by padding the
request. What matters is not whether it succeeds but what it does when it fails:

- how many of the three produced a contract violation, and whether the single back-prompt recovered
  it (`CONTRACT_VIOLATION` and `CRITIC_FEEDBACK` appear in the trace's planner events);
- whether the three runs selected the same action, and if not, whether the difference is a tie;
- whether any run invented an action identifier that is not in the catalogue — it must be refused
  by name, never silently mapped to the nearest one;
- `provider_usage` in each trace: the tokens the provider charged that run, and `calls`.

## Phase 5b — does reachability in the state change the recommendation?

Twelve identical calls on a state without the supplier topology selected a non-executable action
every time. The critic's state carries that block and answered differently. Two different states,
so the comparison has to be run properly:

```bash
python research/local_verification/topology_ablation.py --repeats 12 \
  --report outputs/local_verification/topology_ablation.json
```

One contrast, one menu, one question set; the topology block is the only difference between the
arms. Report the executable share and the agreement in each arm. Both arms are paid: 24 calls.

## Phase 6 — the virtual cell on real assets

Only if `data/virtual_cell/registry.json` exists locally. Add to the phase-5 command:

```bash
  --virtual-cell state --state-template <your template>.json --parallel-predictions 4 \
  --artifact-directory outputs/local_verification/artifacts
```

Check in the trace that each `action_predictions` entry has `planning_only: true`,
`is_measurement: false`, and an `artifact_ref` whose file hashes to its recorded
`artifact_sha256`; that an out-of-domain query **abstains** rather than extrapolating; and that the
loop still reaches a decision when it abstains. Then re-run identically and confirm the prediction
cache serves the repeats — the second run should issue strictly fewer provider queries.

## Phase 7 — the evaluation arms

Only if `data/evaluation/cases/real/` exists locally.

```bash
maestro-evaluate --public-cases data/evaluation/cases/real/public \
  --private-results data/evaluation/cases/real/private \
  --mode decision --policy ablation --run-id lv-$(date +%Y%m%d)
```

Report the four arms side by side. If repair-disabled or equal-budget-random matches the repairing
policy, the repair is not what produced the difference, and that is the result.

---

## What to send back

Measured runs are recorded in [`2026-09-25-maestro.md`](2026-09-25-maestro.md) and
[`2026-09-26-maestro.md`](2026-09-26-maestro.md). Their raw reports remain machine-local
under `outputs/`.

The short version is three files plus the numbers:

```
outputs/local_verification/report.md          # phases 0-3, already in the right shape
outputs/local_verification/jev_probe.json     # phase 4 — the one that unblocks the most work
outputs/local_verification/critic-trace.json  # phase 4, or the phase-5 trace if you got that far
```

Plus, in prose:

1. **Suite** — counts, and the ids that fail locally but are not in the baseline.
2. **Jev** — which row of the phase-4 table you landed on. If it refused, the `keys=` list verbatim.
3. **Planner** — of three live runs: violations, recoveries, agreement, token usage.
4. **Anything that surprised you**, including a passing check you expected to fail.

Redact nothing else. Traces contain no secrets by construction — but if you are unsure about a
file, say so instead of pasting it.

## What this protocol cannot establish

It tests the machinery, not the biology. The fixture pack is synthetic: its numbers are invented to
exercise the topology and the evidence invariants, and no result from it supports any claim about a
target, a compound or a mechanism. Phases 6 and 7 use real assets but still measure only whether
the system's own contracts hold under them.
