# AMENDMENT_R197-004 —— R197 v2 结果 telemetry 与确定性解耦（2026-10-27，**最终 verdict 落盘之前**）

> 依据：AMENDMENT_R197-003 §4 要求把实际 wall/CPU 写入 `r197_v2.json` 与 `usage_r197_v2.json`；但 PROTOCOL_R197 §9 / AMENDMENT-002 §2 / 任务要求核心结果 JSON **无时间戳、双跑逐字节一致**。运行时长天然不确定，二者冲突。本修订在**最终 verdict 落盘前**预注册解耦，不改变任何统计量/门槛/判定规则/预算门本身。

## 1. 修订（只改 telemetry 存放位置）

- **核心结果 `r197_v2.json`（确定性产物）**：`budget` 块只写**确定性字段**：
  `budget_seconds=1200`、`budget_gate_passed`（本轮两次实测均 <1200 → true）、`budget_rule`（含 wall>1200 ⇒ mandatory inconclusive 的规则原文）、`stage_cache_paths`（固定相对路径）、`wall_and_cpu_where_recorded="usage_r197_v2.json + record_r197_v2.md"`。
  **不写** `wall_seconds_total`/`cpu_time_seconds_total`/`budget_exceeded` 的实测数值（它们会随运行波动，破坏逐字节一致）。
- **`usage_r197_v2.json`（telemetry，非确定性产物）**：写实测 `wall_seconds_total`、`cpu_time_seconds_total`、`budget_seconds`、`budget_exceeded`、分步缓存路径、环境；该文件**不参与**逐字节一致性比较（与 R190-A0 usage 同一惯例）。
- **`record_r197_v2.md`**：记录两次全量运行的实测 wall/CPU 与预算门结论（可审计）。
- **预算门的执行不变**：程序仍以实测 wall 判定；若实测 wall>1200 s，`r197_v2.json` 的 `budget_gate_passed=false`、design_check 追加大项失败、verdict 强制 `inconclusive`（规则同 AMENDMENT-003 §4），只是 wall 数值本身不写入核心 JSON。
- **确定性验收口径（写死）**：`r197_v2.json`、`r197_v2_rows.csv` 连续两次全量运行**逐字节相同**；`usage_r197_v2.json` 只要求字段结构一致（wall/CPU 可变）。

## 2. 影响面

- 不改变：任何统计量、模型、设计、门槛、δ_min、type-I CP 规则、配对 bootstrap、判定规则、预算门逻辑。
- 改变：telemetry 字段的存放位置（核心 JSON 去时间相关值）；新增本文件作为 determinism 预注册说明。
