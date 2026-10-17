# Context transfer with verified bridges (study `context_transfer_20261017`)

The question: can a dual-core research system bring what it learned in one biological context to
a new one, under a small well budget? The two cores are a Virtual Cell response model and a
research agent. In the new context, the agent may measure a few bridge items first and verify
the transfer. It then nominates the rest.

The method is developed on PRISM 19Q4 cell lines. That asset is already exposed, so it is
development grade only. The frozen method is then applied once, unchanged, to Beat AML 2.0
primary patient samples, which MAESTRO had never used before.

* `PROTOCOL.md`: the question, domains, endpoint, arms, hypotheses, verdict rules and costs. §9
  lists every design choice taken from development.
* `log/transfer_review_20261017/REVIEW.md`: the literature review that motivates the design.
  §10 adds the npj Drug Discovery 2026 perspective on agentic autonomy.

## Result (one shot, Beat AML 2.0, 2026-10-17)

**CONFIRMED** under the frozen definitions (C1–C4). `REPORT.md` has the full results; `verify.py`
prints `VERIFIED`. In short, per patient sample at 16 wells (520 samples, 479 patients):

* **The agent's choice.** The source-verified agent chose exploit-first bridging in all five
  folds: measure the Virtual Cell's top four inhibitors, then re-rank the other twelve.
* **What it beat:**
  * the Virtual Cell alone, by +0.073 hits [+0.025, +0.127];
  * pilot matching, by +0.229;
  * the PRISM development procedure carried over unchanged, by +0.108.
* **Virtual Cell prior.** It beat nearest-context transfer (+0.075) but not the context-free
  item prior (−0.008).
* **What did not hold up:**
  * The agent matched the standard exploit-first design but did not beat it (P2 is 0, and P5
    holds trivially).
  * The pre-registered expectation (decline to bridge, PARTIAL) was wrong.
  * The LLM bridge picker added nothing (0.2768 USD).
* **Post hoc.** The rejected development procedure, the lookahead bridge, lost because of a
  baseline defect in its greedy batch step, not because of its design (`REPORT.md` §5). The
  defect is corrected in `src/agent/bridge_design.py`, with the frozen rule kept as
  `lookahead_v1`. The correction is development-grade.
* **Process report.** Its `maestro` wasted-well figure is a reporting error (`DEVIATIONS.json`).
* **Claims amendment.** `CLAIMS.json` (`claims.py`) separates the CONFIRMED protocol label from
  what is established. Only the functional-feedback gain is supported, under the replay; C3/C4
  as frozen do not test adaptivity or superiority. A "well" here is one archived AUC query, and the
  analysed matrix has 165 inhibitors. Follow-up: `research/feedback_attribution_20261017`.

## Files

| File | Role |
|---|---|
| `common.py` | paths, endpoint (`selective_events`), folds, paired cluster statistics |
| `vc.py` | Virtual Cell: low-rank Bayesian response model with a basal-expression prior |
| `agent.py` | bridge rules (random, exploit, panel, information, decision lookahead), verification and repair |
| `procedure.py` | source-verified selection of the Virtual Cell rank and the agent's procedure (rules `evidence`, `max`, `hybrid`) |
| `procedure_variant_a.py` | superseded selector, kept so its disclosed proxy runs reproduce |
| `RULE_CHOICE.md`, `rule_choice.py` | pre-declared criterion for the frozen selection rule, and its application (`RULE_CHOICE.json`) |
| `replay.py` | equal-well replay of every arm on held-out contexts |
| `llm_arm.py` | secondary arm: deepseek-flash chooses the bridge from a shortlist (cached ledger) |
| `data_prism.py` | development domain (PRISM 19Q4 + CCLE expression) |
| `census.py` | confirmation-domain census: design columns only, written before the freeze |
| `data_beataml.py` | confirmation domain loader; reads AUC, so only `confirm.py` calls it |
| `develop.py` | named PRISM development configurations, rank check, LLM pilot, `DEVELOPMENT.json` |
| `power.py` | design and power check on a PRISM proxy shaped like Beat AML, `POWER.json` |
| `parity.py` | shows the promoted `src` modules reproduce this study's code (`PARITY.json`) |
| `freeze.py` | writes `FREEZE.json` once |
| `confirm.py` | one-shot confirmation; refuses on a freeze mismatch or an existing `RESULTS.json` |
| `verify.py` | recomputes reported numbers from cached records and checks the freeze |
| `REPORT.md` | results of the one-shot confirmation, secondary analyses, process report and post-hoc diagnosis |
| `posthoc_availability.py` | post hoc: lookahead and exploit with each target's measured pairs known (`POSTHOC_AVAILABILITY.json`) |
| `claims.py` | post-run scientific-claims amendment: evidence levels, claim-mapping audit, units (`CLAIMS.json`) |
| `posthoc_lookahead.py` | post hoc: corrected lookahead in the promoted modules against `lookahead_v1`, with parity to the study records (`POSTHOC_LOOKAHEAD_<domain>.json`) |

## Running

All commands run from this folder, with the `maestro` conda environment
(`D:\anaconda\envs\maestro\python.exe`).

```
python -B develop.py <config>      # one development configuration
python -B develop.py --summary     # DEVELOPMENT.json
python -B power.py <config>        # one proxy configuration
python -B power.py --summary       # POWER.json
python -B rule_choice.py           # RULE_CHOICE.json
python -B parity.py                # PARITY.json
python -B freeze.py                # FREEZE.json, once
python -B confirm.py --llm         # once, after FREEZE.json (the LLM arm is gated, PROTOCOL.md s7)
python -B verify.py
python -B posthoc_availability.py      # post hoc, after the confirmation
python -B posthoc_lookahead.py beataml|prism_line|prism_lineage
python -B claims.py                    # CLAIMS.json, after the confirmation
```

Caches and per-context records live in `tmp/context_transfer_20261017/`.
