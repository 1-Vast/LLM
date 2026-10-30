# record_m1_stage2_prep —— R204-M1 Stage2 高维近似设计准备执行记录

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/设计者。
**任务：R204-M1-STAGE2-PREP（设计，不运行效果）。** 只写 `research/2026-10-28-m1-stage2-prep/` 与 tmp/；未改 M1 预注册/M1 Stage1/M2/M3/N1/A-B-D/旧门槛/旧判定/代码；未运行效果/训练/真实数据/湿实验；Stage2/3 未执行。

## 0. 时间线

| 时间（Asia/Shanghai） | 事件 |
|---|---|
| — | 读 task-163、M1 Stage1 report/JSON（B2 等价→一步投影撤）、M1 v0.2、R204 BRIEF/report、R203 decision/power、ERRATA |
| — | 新建 `2026-10-28-m1-stage2-prep/`；先写 `stage2_m1_schema.json`（定位/高维设置/G1–H3/基线/端点/失败/caps） |
| — | 写 `stage2_m1_plan.py`：链核验、Stage1 B2 撤回确认、结构单测、规划算术、pilot 计时；运行通过 |
| — | 两独立进程 result JSON 逐字节 `CD15CF33…E29ECDA5`；写 PROBLEM/DESIGN/report/record/usage |

## 1. 输入（只读）

| 文件 | 用途 |
|---|---|
| `m1-stage1/report_m1_stage1.md` / `m1_stage1.json` | C208：B2 等价、rename_maxent、一步投影撤 |
| `m1-executable-gen-prereg/{PROBLEM_M1_v0_2.md,DESIGN_M1_v0_2.md}` | M1 形式/三阶段/边界 |
| `deep-coupling-redesign/{report.md,BRIEF_R204.md}` | M1 定位/边界 |
| `2026-10-28-decision-power-scope/{PROBLEM_DECISION.md,power_scope.json}` | δ/headroom/MDE/6,282 |
| ERRATA C197/C199/C201/C207/C208 | 6,282 Fisher-z、预算、一步投影撤 |

## 2. 做了什么

- **定位**：Stage1 B2 `rename_maxent_detected=true`、`m1_increment_claimed=false`；一步投影主算法撤；Stage2 只做高维/未知/受限候选设计。
- **高维设置**：d_X=64、A=4、d_Y=4；Pθ 混合/条件异方差/Student-t 未知核；r_g 有界；τ∈{.5,1}；π0 full/constrained；train 4096/eval 2048；target 样本不作标签、Doob 非药。
- **检查**：Stage1 保留 G1/G2/G4/G5/G6；Stage2 新增 G3/H1/H2/H3（近似随 d/N、Sinkhorn 收敛、planning quality vs exact small case）。
- **等预算**：B1–B5 规格；同数据/信息/cap/调参≤20；等效→rename_maxent/撤；未执行比较。
- **Stage3 端点**：δ=.05、headroom/MDE/cluster、6,282 仅 Fisher-z；data_unavailable。
- **单测**：形状/有限性/支持/seed/Sinkhorn/内存 cap 全 PASS。
- **两跑**：result JSON 逐字节 `CD15CF33394327302F5D35A245414310655C8E5C6097D11DC98AEAC2E29ECDA5`；timing 单独。
- **pilot**：2.9322e-04 s/rep；projected .002932 s；full wall .051557 s；caps 1800s/2h/8GB；0 wells。
- **未执行效果/训练/方法比较/真实数据**；未输出 decision utility/regret/top-k。

## 3. 产出

| 文件 | 说明 |
|---|---|
| `PROBLEM_M1_STAGE2.md` | 定位/高维设置/检查/基线/端点/失败/边界 |
| `DESIGN_M1_STAGE2.md` | Stage2 执行设计（不运行） |
| `stage2_m1_plan.py` | 规划/结构单测/计时；不跑效果 |
| `stage2_m1_plan.json` | 规划结果（两跑一致；无 telemetry） |
| `stage2_m1_schema.json` | schema/失败模板（先写） |
| `timing_m1_stage2_prep.json` | canonical timing |
| `report_m1_stage2_prep.md` | 报告 |
| `record_m1_stage2_prep.md` | 本记录 |
| `usage_m1_stage2_prep.json` | 命令/SHA/attestation，最后写出 |

## 4. 未做/边界

- 未运行 Stage2/3/真实数据/湿实验；无效果/增益/方法比较；无训练/拟合。
- 未改 M1 预注册/Stage1/M2/M3/N1/A-B-D/旧门槛/旧判定/代码；不晋升代码；不恢复停止实验；不拼 ΔEMAX；技术重复≠独立培养。
- 不称药理/真实决策/迁移/机制/新颖性；一步投影已撤，不写 M1 增量；B2 等价是 rename_maxent 证据；M1 与 M2/M3 不混同；N1 no_increment 不作 M1 Stage2 证据。
- Stage2 执行须另立预注册+独立挑战+Lead 批准；Stage3 需合格真实功能数据（当前 data_unavailable C203/C205）。
