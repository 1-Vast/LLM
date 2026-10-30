# DeepSeek auxiliary research workspace

This workspace stores the auxiliary-agent contract, task templates and handoff materials. The principal research agent owns scientific questions, hypotheses, metrics, experiment design, mechanism judgments and promotion decisions. Auxiliary agents perform only prescribed extraction, deduplication, field/unit checks, formula recalculation and formatting.

## Operating rules

- Every task under `tasks/` states inputs and versions, hashes where available, rules, budget, outputs and acceptance checks.
- An auxiliary output is administrative evidence until the principal agent independently checks its source, calculation and scope.
- Ambiguity is recorded and reported; the auxiliary agent does not select a scientific hypothesis, metric or method.
- New tasks are taken at small-step boundaries. Unrelated work continues when a task is blocked or awaiting acceptance.
- Historical snapshots and append-only coordination records are retained for provenance and are not live instructions.

## Files

- `PROMPT_MAIN_AGENT.txt` and `PROMPT_DEEPSEEK_ASSISTANT.txt` define the role boundary.
- `TASK_TEMPLATE.json` defines the required task packet.
- `tasks/` contains explicitly assigned work packets when present.
- `SOURCE_MANIFEST.json` records source identity and hashes; matching bytes do not establish scientific validity.

No model capability, scientific benefit or mechanism is established by the existence of these files or by a software check.
