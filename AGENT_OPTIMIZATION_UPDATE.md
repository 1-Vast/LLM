# Agent optimization update: literature-grounded streamlining

Updated: 2026-09-25. Branch: `claude/sharp-bardeen-q4yt0t`. This record covers two
commits on top of `79e07c1`: the agent/virtual-cell integration commit (`4ffe7c4`) and
the streamlining pass described here. The agent is the primary core and the
virtual cell is the secondary core. Nothing here is a biological result. Every
number below is a software measurement on constructed fixtures.

## 1. Literature consulted and what each one changed

The search covered LLM agents for planning, self-correction, tool use, efficiency and
scientific discovery. A paper counts here only if it changed a decision in the code
or explains why a technique was not adopted.

| Work | Finding used | Where it shows up |
|---|---|---|
| [LLM-Modulo (Kambhampati et al., 2024)](https://arxiv.org/abs/2402.01817) | LLMs generate candidates; sound external critics verify them and feed failures back as a back-prompt, with a bounded number of iterations | The planner's generate-test-critique loop (`agent/planner.py`): the parser is the hard critic and the new `critique` is the soft critic |
| [CRITIC (Gou et al., ICLR 2024)](https://arxiv.org/abs/2305.11738) | Self-correction works with *external* (tool) feedback and adds little without it | Feedback text always comes from a deterministic check, never from asking the model to review itself |
| [Reflexion (Shinn et al., NeurIPS 2023)](https://arxiv.org/abs/2303.11366) | Verbal feedback kept in episodic memory improves later trials | Already present (`reflect_on_result`). Not extended to predictions; see section 4 |
| [WebDreamer (Gu et al., TMLR 2025)](https://arxiv.org/abs/2411.06559) | Simulate each candidate action's outcome with a world model before committing | Per-action virtual-cell rows now reach the LLM repair planner as a planning-only briefing (`agent/world_model_briefing.py`) |
| [LLMCompiler (Kim et al., ICML 2024)](https://arxiv.org/abs/2312.04511) | Dispatching independent function calls in parallel cuts latency and cost | Per-action virtual-cell queries run concurrently when the backend is declared thread-safe (`max_parallel_predictions`) |
| [ToolCacheAgent](https://openreview.net/forum?id=tX3YcbNa5w), [Agentic Plan Caching](https://arxiv.org/abs/2506.14852) | Cache tool results with explicit cacheability and invalidation rules | `virtual_cell/cache.py`: only supported, contract-valid predictions are cacheable; the key is the model inputs; abstentions are never cached |
| [SWE-agent ACI (Yang et al., NeurIPS 2024)](https://arxiv.org/abs/2405.15793) | Concise, informative observations and guardrails improve agent reliability | Compact catalogue rendering; critic messages name the exact field and the registered alternatives |
| [BioProAgent (ACL 2026)](https://arxiv.org/abs/2603.00876) | A deterministic design-verify-rectify loop plus symbolic grounding reduces tokens (about 6x) and raises compliance | Same pattern: symbolic menu and contrast by identifier, and a deterministic verifier before adoption |
| [Reducing cost of LLM agents with trajectory reduction (2025)](https://arxiv.org/abs/2509.23586) | Most agent cost comes from redundant context that keeps growing | The repair prompt no longer repeats the full plan action inside the contrast |
| [BioDiscoveryAgent (Roohani et al., ICLR 2025)](https://arxiv.org/abs/2405.17631) | Closed-loop perturbation design with prior results placed in the prompt | Confirms the existing design, where revealed results enter context as evidence. No change needed |
| [Biomni (2025)](https://www.biorxiv.org/content/10.1101/2025.05.30.656746v1), [Coscientist (Nature 2023)](https://www.nature.com/articles/s41586-023-06792-0) | Broad tool spaces and code execution for biomedical agents | Out of scope: MAESTRO deliberately keeps a registered menu |
| [VCWorld (ICLR 2026)](https://arxiv.org/abs/2512.00306), [CellForge (2025)](https://arxiv.org/abs/2508.02276) | Interpretable, stepwise virtual-cell predictions; agentic design of virtual-cell models | The briefing keeps the model's own validation status and uncertainty next to each value instead of a bare number |
| [KnowNo (Ren et al., CoRL 2023)](https://arxiv.org/abs/2307.01928) | Calibrated uncertainty tells a planner when to ask for help | Already present as explicit deferral and abstention. Unchanged |
| [Autonomous Research Agents: the verification gap (2026)](https://arxiv.org/abs/2608.05179) | Claims from agents are harder to verify than their code is to run | Every correction, critic finding, reuse and parallel dispatch leaves a named record in the run log |

## 2. What changed in this pass

### Agent core

- **Critic back-prompting.** `MechanismContrastPlanner` now accepts a soft critic
  alongside the hard parser. For the contrast planner, the critic names an
  `action_identifier` outside the registered menu (or a missing one), and two
  model-authored hypotheses that do not propose two distinct development actions.
  Only the planner can fix these. The deterministic repair cannot repair a
  non-separating hypothesis pair. For the repair planner, the critic names an
  unregistered replacement action. Soft means that after the shared retry budget
  (`contract_retries`, default 1) the last answer is returned unchanged, and the
  controller's check and repair handle it exactly as before. Registered hypothesis
  definitions are never critiqued. Findings are logged as `planner_critic_feedback`.
- **Compact prompts.** `render_catalogue` omits null and empty fields but keeps every
  boolean and number, because `context_bound: false` is a declaration.
  `render_contrast` names the plan by identifier.
- **Phase extraction.** `MAESTROOrchestrator.run` delegates to `_query_world_model`
  (returns `WorldModelQueries`) and `_check_and_repair` (returns `RepairOutcome`).
  Behaviour is unchanged.

### Virtual-cell integration

- **Deduplicated, optionally parallel dispatch.** `_predict_many` answers reused
  queries first, runs at most one inference per distinct query in a round, and
  with `max_parallel_predictions > 1` (CLI `--parallel-predictions N`) dispatches the
  distinct misses concurrently. Recording and logging happen on the calling thread
  in request order, so the run record does not depend on the dispatch mode.
  Parallelism is opt-in because a backend must be safe to call from several threads.

### Streamlining

- `FunctionalInterventionProfile.is_measured` / `.unmeasured` and
  `EvidenceAction.required_premises` replace ten hand-written premise checks across
  `maestro/contrast.py`, `selection.py`, `acquisition.py`, `composition.py`,
  `agent/orchestrator.py` and `evaluation/baselines.py`. The orchestrator's private
  `_prerequisites_satisfied` is gone.
- `agent/storage.connect` replaces three copies of `_connection`. It commits on
  success, rolls back on error, and closes the connection. Before, `with
  sqlite3.connect(...)` committed but left each connection open until garbage
  collection. On the Windows workspace an open handle locks the database file.
- The prediction-to-request lineage check is one function (`_answers`) instead of two
  inline copies. The CLI parses `SystemContext` in one place. The audit logger uses
  `collections.abc.Mapping`: in the profile, `typing.Mapping` isinstance checks took
  about a third of the logger's redaction time.
- Dead code removed: unused imports in `maestro/selection.py`, `acquisition.py`,
  `composition.py`, `agent/orchestrator.py`, `agent/memory.py`; an unused
  assignment in `check_contrast`; unused exception bindings in `agent/llm.py`; a
  loop variable that shadowed `dataclasses.field`. `src/agent` is now pyflakes-clean.

## 3. Measurements

| Quantity | Before | After | How measured |
|---|---|---|---|
| Action catalogue JSON (3-action biological fixture) | 2,558 chars | 1,971 chars (-23%) | `render_catalogue` vs `json.dumps(asdict(...))` |
| Contrast JSON in the repair prompt | 1,545 chars | 522 chars (-66%) | `render_contrast` vs `json.dumps(asdict(contrast))` |
| Structured repair-prompt payload (contrast + catalogue) | 4,103 chars | 2,493 chars (-39%) | Sum of the two rows above |
| Virtual-cell inferences, 4 actions with 3 distinct queries, one round | 4 | 3 | `test_distinct_queries_run_concurrently_once_each_and_log_in_request_order` |
| Wall time for those 3 inferences at 0.15 s each | 0.46 s sequential | 0.16 s with 3 workers | Same fixture, sequential vs parallel |
| Virtual-cell inferences over R rounds x A actions with unchanged inputs | R x A | A (from the first commit) | `test_a_second_round_reuses_the_first_rounds_inference` |
| `MAESTROOrchestrator.run` length | 266 lines | 209 lines | Line count |
| Test suite (`--ignore=tests/test_learned_response.py`) | 787 passed | 813 passed | Same 53 failures before and after; see section 5 |

Local compute for a three-round constructed loop is about 75 ms, and about half of
it is SQLite commits. In a real run, provider latency and State inference dominate.
That is why this pass targets prompt size, LLM call count and inference count
rather than local CPU. Switching SQLite to WAL mode was measured and rejected: 1.41
ms per commit against 1.12 ms for the default journal on this filesystem.

## 4. Deliberately not adopted

- **Tree search or tournaments over plans** ([LATS](https://arxiv.org/abs/2310.04406),
  [Co-Scientist](https://www.nature.com/articles/s41586-026-10644-y)). Each multiplies
  paid calls, and task.md requires one complete evidence-bounded design to work
  before a larger multi-agent system is built.
- **Writing prediction feedback into memory** (a Reflexion-style extension). The
  reliability ledger already reaches the repair planner each round through the
  briefing. A memory entry that pairs a predicted value with a measured one would
  blur the rule that a prediction never becomes evidence through context or memory.
- **Consulting the world model before the contrast planner** (the full WebDreamer
  pattern). Requests carry the contrast identifier as tracking metadata, and moving
  the query ahead of planning would change request lineage that existing contract
  tests pin. The cross-round cache makes a later pre-planning query cheap if this is
  revisited.
- **Critiquing the choice of a non-covering plan.** The deterministic selector and
  repair already fix it without an extra paid call.

## 5. Verification status

- Offline test suite: 813 passed, 19 skipped. The same 53 tests fail before and
  after, because they need `data/evaluation/...`, `data/raw/...` and `log/` files
  that are not in this repository. `tests/test_learned_response.py` needs `torch`
  and was not run.
- No real provider call and no real State inference was made in this pass. The
  prompt-size numbers are character counts on constructed fixtures, not provider
  token counts.
- Behaviour that evaluation arms rely on is unchanged. A planner contract violation
  that survives the retry still raises and is recorded as a lost case. A critic
  finding that survives is handed to the unchanged deterministic check.
