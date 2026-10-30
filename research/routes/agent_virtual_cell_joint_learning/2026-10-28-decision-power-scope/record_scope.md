# record_scope —— R203-P1 决策终点/可达空间/配对功效/两本账 执行记录

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A 同一独立审计/设计员（endpoint-auditor）。
**任务：R203-P1（设计，不运行效果）。** 只写 `research/2026-10-28-decision-power-scope/` 与 `tmp/`；未改 A/B/D1/D3 产物、旧门槛、旧判定、代码；未运行效果/未拟合/未读响应或功能数据。

## 0. 时间线

| 时间（Asia/Shanghai） | 事件 |
|---|---|
| 10:17 | 读 task-128、用户复核报告 §1–§6、`ERRATA_R201_R202.md`（C197/C199）、T1 JSON、A.1 qualify/PROBLEM、D3、R201 BRIEF |
| 10:17–10:24 | 写 `power_scope.py`（仅规划算术：T1 可达性、Fisher-z-only、连续/二值配对功效、30-cell 等价、端点/两账/建议） |
| 10:24 | 运行 `power_scope.py` → `power_scope.json`；核对 T1=501/500、max_gain=.098、Fisher n 6283/1573、net utility n=126 等 |
| 10:24–10:26 | 写 `PROBLEM_DECISION.md`/`DESIGN_SCOPE.md`/`report_scope.md`/本记录/`usage_scope.json`；核对 SHA；确认未运行效果 |

## 1. 输入/依据（只读）

| 文件 | 用途 |
|---|---|
| `research/2026-10-28-blocked-conclusion-review/report.md` | 用户复核 §3 T1 可达性、§4 6,282 修正、§1 A 线范围、§5 AZ 导出覆盖 |
| `agent-cell-colearning/ERRATA_R201_R202.md` | C197/C199 修正；T1 partial；6,282 通用门撤；机制/药理分账 |
| `agent-cell-colearning/dual_budget/t1_main/t1_main.json` | T1 p0=.902、π_dual=.912、n=500、δ=.10、H_B partial |
| `agent-cell-colearning/mechanism_A/{qualify_A.py,PROBLEM_A_v0_2.md,DECISION_R201_A_CLOSE.md}` | 6,282 来源、静态 S-add 停止对象、决策不可认证 |
| `direction-mechanism-expansion/d3_feedback/` | 单 anchor MDE/30 cells 精度边界（背景） |
| `2026-10-27-innovation-round-r200/BRIEF.md` | R200 纪律/边界 |
| 用户复核 `arithmetic_check.json`/`independent_check.md` | 算术/独立核对（只读） |

## 2. 修改/产出

- **PROBLEM_DECISION.md**：端点清单/定义、独立单位/配对/cluster、可达性公式+T1、配对功效、Fisher-z-only、30 cells 边界、两本账、N1/N2。
- **power_scope.py**：仅规划算术，不读响应/不拟合；输出 `power_scope.json`。
- **DESIGN_SCOPE.md**：未来独立研究的预注册模板（预检→端点→功效→两账→预算/停止）。
- **report_scope.md**：结论摘要/数字/建议。
- **record_scope.md**：本记录。
- **usage_scope.json**：命令/输出 SHA/attestation，最后写出。

## 3. 关键算术

- T1：`p0=451/500=.902`；`max_gain=.098`；`δ=.10`；`ceil(500×1.002)=501>500` → **unreachable_gate**；保留 partial，不降 δ。
- Fisher-z-only：`N_req=2×(2.801585/δ)²+3` → δ=.05 6283、δ=.10 1573；n=30 MDE=.7625；**不是通用决策门**。
- 连续配对：`n=ceil((2.801585×SD(D)/δ)²)`；SD=.20/δ.05→126；SD=.30→283；cluster6/ICC.5→441；regret SD=.15→71。
- 二值配对：p10=.20,p01=.10,δ=.05→911；top-k .15/.05→597。
- 30 cells 连续可检 SD 上限：δ=.05→.0978；δ=.10→.1955（无 cluster inflation）；典型 net utility/regret SD .15–.30 → 30 不足。
- 两本账：机制（合成/计算）vs 药理（实测/预算/独立培养）；decision endpoints 属药理账；合成不得升级。

## 4. 下一项建议（未运行）

- **N1（机制账）**：合成 state/sequence-dependent 非静态 S-add + plan-pair conflict/unified revision；primary decision regret（δ=.05）；等 compute/query 基线；headroom/MDE preflight；失败 stop；**非静态 S-add 改名**。
- **N2（药理账）**：新合格实测功能资源的 net utility（δ=.05）；独立培养/细胞背景；同 wells/compute 基线；当前 data_unavailable；不拼 ΔEMAX；无功能/暴露/独立培养/功效→stop。
- 顺序：N1 + AZ 2024 记录覆盖审计；N2 有资源后再立项；均不运行。

## 5. 未做/边界

- **未运行效果/未拟合/未读响应/功能数据**；只做规划算术/结构/文档。
- 未降旧门槛、未改旧判定（T1 partial、A.1 静态 S-add stop 保留）、未晋升代码、未恢复已停止实验、未做 A.2.3。
- 不称新颖性/机制/迁移/决策收益/独立确认；合成≠药理；技术重复≠独立培养；6,282 仅 Fisher-z；不拼 ΔEMAX。
- 未改其它目录/INDEX/git；只写本目录与 `tmp/`。
