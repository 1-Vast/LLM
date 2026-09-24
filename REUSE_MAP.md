# E0-DIR reuse map

| E0 concern | Existing MAESTRO surface | Decision |
|---|---|---|
| Request validation and fail-closed prediction | `virtual_cell.interface.safe_predict` | Reuse |
| Model/asset/gene-order identity | `virtual_cell.state_adapter`, `artifacts` | Reuse |
| Hidden result separation | `evaluation.cases`, `runner` | Reuse concept; E0 observation type is independent |
| Repair ledger | `maestro.repair` | Do not reuse semantics; E0 has `DIRRepairBranch` |
| API completion | `agent.llm.DeepSeekChatClient` | Reuse text completer; locally validate E0 JSON |
| API cost | `evaluation.provider_spend` | Reuse and harden numeric parsing |
| Tool execution | `agent.tool_runtime` | Reuse receipts only; not treated as OS isolation |
| DIR data contract | none | New `src/e0_dir/core.py` |
| Single-step E0 controller | none | New `src/e0_dir/controller.py` |

