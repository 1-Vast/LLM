# Invalid development run (kept as a failure receipt)

Run at 2026-10-03 about 18:05 +0800, 468 DeepSeek calls, USD 0.1823 (`spend.json`).

A scripted string replacement in `llm_agent.py` silently failed to apply, so:

- the `blind` mode sent exactly the `named` prompt (model scores visible, ranked order). Its
  0.998 round-1 agreement with the world model exposed the defect;
- every mode asked for the full batch size in the final round, where only `k = batch - 1`
  experiments remained, so every final round was recorded as `LLM_INVALID_SELECTION` and
  repaired from the world-model order.

No result from this directory is reported as evidence. The corrected prompts are checked by
assertion before the rerun, `dev_llm_20261003_v2`.
