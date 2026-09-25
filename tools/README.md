> **File summary**
> - **Path**: `tools/README.md`
> - **Purpose**: describes the manifest-scoped local dataset tool convention.
> - **Core points**:
>   - Each manifest-carrying subdir is one executable, manifest-scoped tool.
>   - The agent selects a bounded sequence of registered tools and sees prior receipts.
>   - `shared/` is support code with no manifest, so discovery never offers it.
>   - Tool output is observation, never a mechanism conclusion.
> - **Interfaces / data**: `*/manifest.json`, `*/tool.py`, `data_profile/`, `column_summary/`, `table_filter/`, `shared/`
> - **Depends on**: `src/agent/tool_runtime.py`

# MAESTRO Local Tools

Each subdirectory is one executable, manifest-scoped local data tool. The agent discovers `*/manifest.json`, asks the configured LLM to choose successive applicable registered tools for datasets supplied by the user, validates that selection, and executes only that folder's `tool.py`. Results enter the context as dataset-derived observations with their source and limitations; they never become a mechanism conclusion by themselves.

Available tools:

- `data_profile/`: CSV, TSV, and JSON schema, sample, and missingness inspection.
- `column_summary/`: bounded descriptive statistics for one named numeric column.
- `table_filter/`: one declarative filter with a bounded matching-row sample.
- `evidence_bundle_optimize/`: exact declared coverage with source-dependence bounds and explicit costs.
- `multimodal_alignment/`: paired scalar QC with explicit information visibility and acquisition cost.
- `virtual_cell_query/`: the State adapter behind applicability and endpoint gates; returns prediction or named refusal.

Structured payloads and receipts enter planning without being converted into measurements.
Manifest requirements and qualification states are in [`task.md`](../task.md) section 6; the
negative-condition contract a tool description must carry is in
[`research/agent_architecture.md`](../research/agent_architecture.md) section 2.3.

The initial tools use only the Python standard library. New tools must be placed in their own folder with `manifest.json`, `tool.py`, and a concise `README.md`; they must not accept shell commands, arbitrary code, arbitrary file paths, or infer causal biological claims. All tool output is validated as observation, not evidence of a mechanism contrast.

## Shared support code: `shared/`

`tools/shared/` carries the machinery that tools, offline runners and tests all need,
and it deliberately has **no** `manifest.json`. Discovery globs `tools/*/manifest.json`,
so the package is never offered to the selecting model and can never be executed as a
tool; `tests/test_repository_shape.py` pins that.

- `stub_client.py` -- `StubClient`, a deterministic stand-in for the language-model
  client. It returns a declared response and records what the caller sent, so an
  offline test exercises the caller without a provider, a key or a paid request. It
  replaces eleven near-identical copies that used to live in the test modules.
- `state_fixture.py` -- builds the smallest virtual-cell fixture the real entry point
  accepts: a synthetic AnnData asset, its registration, a checkpoint placeholder with
  a perturbation map, and a query bound to them. A caller that wants to test a
  *refusal* passes the field that should be refused. Nothing it builds is a
  measurement, and the registration says so in its `source` field.

Neither module asserts anything about biology: a fixture can make the entry point
accept a query, and it can never make a claim true.
