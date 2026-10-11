# Actual configured-provider engineering audit

The configured `deepseek-flash` client passed four actual HTTP requests at earlier interface stages. Their responses were replayed without new API requests as the contract gained hypothesis and interpretation bindings. All ten scenario executions passed, comprising **four historical real provider calls and six offline replays**. The final interpretation-bound schema is covered by three offline replays of authentic provider responses; it has no new live request. The provider-reported totals remain 3,238 prompt tokens and 1,658 completion tokens, totaling **4,896 tokens**. Monetary API cost is unavailable because no authenticated billing receipt or price contract was supplied.

| Execution | Provider calls | Offline replays | Outcome |
|---|---:|---:|---|
| Historical initial live receipt interface | 3 | 0 | LLM proposed `flat`; informative selection chose `useful`; all-flat and external-shift scenarios submitted no action |
| Historical hypothesis-bound interface replay | 0 | 3 | The same authentic responses produced the same decisions; replay context matched the original request |
| Historical hypothesis-bound live request | 1 | 0 | LLM proposed `flat`; the frozen value policy selected `useful` |
| Final hypothesis-and-interpretation-bound interface replay | 0 | 3 | All three authentic responses retain their decisions under the final complete reading-rule and table-setting bindings |

The interpreter returned a fixed declared `TaskIntent`. Only `MechanismContrastPlanner` used the actual configured `MAESTROSettings` and `DeepSeekChatClient`. Every run supplied exactly hypothesis identifiers `a` and `b`, and the registered full definitions: `a` proposes `CONTINUE`, `b` proposes `REVISE_INTERVENTION`. The final replay receipts bind the canonical full definitions using `decision_hypotheses_binding`; planner wording cannot reassign their meaning. They additionally bind every registered `OutcomeRule` field and the table settings using `decision_interpretation_binding(RULES, time_tolerance_hours=1.0, require_context_match=True)`. The verifier recomputes final-schema choices directly with the same complete rules, settings and outcome consequences.

Each actual request used an output limit of 1,600 tokens and a 45-second timeout. The planner's contract retries and both repair mechanisms were disabled. A temporary, process-local override bounded the existing client's transport attempts to one; core source files were not changed. Exact request JSON bodies, complete decoded provider response envelopes, provider-reported usage and file hashes are retained under each live run's `provider/` directory. Authorization headers and credentials are never recorded. Protocol or transport failures would remain failures rather than trigger unbounded repair or retry; none occurred in these four calls.

The action preference is intentionally forced toward the registered `flat` proposal to exercise authority separation. The informative synthetic likelihood gives `useful` a modeled net terminal-loss reduction of 0.86 and gives `flat` a net value of -0.1. With all-flat likelihoods, the gate refuses purchase. With a shifted external admission, it refuses before even requesting forecast work. The ledger kept measurement spend at zero, persisted no measured results, created no terminal evidence state and marked no profile fields as measured. The informative scenario records a pending plan, not an executed laboratory experiment.

These are **synthetic engineering fixtures**. Their `calibrated` labels and declared support counts are artificial inputs for exercising the contract and do not certify any biological model. The historical live calls demonstrate provider compatibility; final-schema replay demonstrates bound hypothesis and interpretation semantics and enforcement of the execution gate for those authentic responses. The audit establishes neither biological decision gain nor an independent LLM contribution.

The original live records remain in `runs/20261011T064049Z/`, including `DRIVER_AT_LIVE_RUN.py`. The historical hypothesis-bound replay and live request remain in `runs/20261011T064444Z_replay_final/` and `runs/20261011T064500Z_fresh_final/`; the original directory names are preserved even though these are no longer the current schema. The final interpretation-bound replay is separately recorded in `runs/20261011T065522Z_replay_interpretation_bound/`. No historical receipt or response was overwritten or reclassified as current-schema live evidence. [AUDIT_SUMMARY.json](AUDIT_SUMMARY.json) links and authenticates all four result packets and counts only the four actual HTTP requests for token usage.

Run the independent artifact verification without calling an API:

```powershell
& 'D:\anaconda\envs\maestro\python.exe' research/dual_core_scientific_20261011/api_audit/verify_provider_smoke.py
```

To reproduce the final-schema replay without a provider call:

```powershell
& 'D:\anaconda\envs\maestro\python.exe' research/dual_core_scientific_20261011/api_audit/run_provider_smoke.py --replay-from 'D:\MAESTRO\research\dual_core_scientific_20261011\api_audit\runs\20261011T064049Z'
```

`--fresh-final` requests one additional provider completion and is not needed for artifact verification.
