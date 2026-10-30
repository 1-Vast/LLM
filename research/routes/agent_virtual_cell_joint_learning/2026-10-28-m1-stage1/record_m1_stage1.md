# record_m1_stage1 —— R204-M1 Stage 1 合成检查执行记录

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/实现者。
**任务：R204-M1-STAGE1（仅机制账、合成检查、compute-only、0 wells；不报效果）。** 只写 `research/2026-10-28-m1-stage1/` 与 tmp/；未改 M1 预注册/M2/N1/A-B-D/旧门槛/旧判定/代码；未运行效果比较/训练/真实数据/湿实验；Stage2/3 未执行。

## 0. 时间线

| 时间（Asia/Shanghai） | 事件 |
|---|---|
| — | 读 task-158、DECISION、v0.2 PROBLEM/DESIGN/formalism/schema/timing、R204 BRIEF/ERRATA |
| — | 新建 `2026-10-28-m1-stage1/`；先写 `schema_m1_stage1.json`（链/G1–G6/S1/B/失败模板） |
| — | 实现 `run_m1_stage1.py`：链核验、Pθ 生成、Q/Rπ/π*、S1-a–e、B1–B5 规格复核、G1–G6、两跑/timing |
| — | 首跑发现 support 检查“full/constrained 同时要求”与 constrained π* grid 越界；修正为每版本独立 support、仅支持动作 grid/解析最优（未放宽阈值） |
| — | canonical 跑通：`chain_ok=True`，G1–G4/G6 PASS，G5 外部两跑；无失败门；full wall 21.323 s |
| — | 两个独立进程 run1/run2：result/rows/diagnostics/schema 逐字节一致；写 report/record/usage |

## 1. 输入（只读）

| 文件 | 用途 |
|---|---|
| `DECISION_R204_M1_STAGE1.md` | Stage1 批准范围/边界 |
| `PROBLEM_M1_v0_2.md` / `DESIGN_M1_v0_2.md` | 形式化/生成器/容差/G1–G6 |
| `formalism_M1_v0_2.py/json` | 反例/投影/支持/Doob 算术（只读 import） |
| `stage1_m1_schema_v0_2.json` | v0.2 schema/基线/生成器 |
| `timing_M1_pilot_v0_2.json` | v0.2 pilot 参考；本实现重新测 canonical |
| `deep-coupling-redesign/{report.md,BRIEF_R204.md}` | M1 定位/边界 |
| ERRATA C197/C199/C201/C207 | 决策/资源/边界；N1 no_increment 不作 M1 证据 |

## 2. 实现/结果

- **链核验**：v0.2 PROBLEM/DESIGN/formalism.py/json/schema/timing **全部 match**；`chain_ok=True`。
- **生成器**：X=4/A=3/Y=4；Pθ logits~N(0,.6²)+softmax seed 20261112；eval 20261113；r=y；τ=1；π0 full/constrained。
- **S1-a–e**：full maxTV .00545039；constrained .00156330；S1-b .00902615；S1-c 0/标签 true；S1-d exact；S1-e 解析 KL gap 0（grid 诊断 0；π*<legal uniform）。
- **B1–B5**：B2 `rename_maxent_detected=true`、diff 0；B3 maxSE .00836378、TV .00358422；B4 row/outcome errors ≤1.5e-13/1.1e-16；B1/B5 规格登记。
- **G1–G6**：G1–G4/G6 PASS；G5 外部两跑 PASS；无 `design_invalid`/失败门。
- **两跑**：result `EF701C66…1382EEAFF` 两跑逐字节；rows `3A6536F5…AA2728`、diagnostics `998406D1…E7B10`、schema `D5B84C48…036F3C` 一致。
- **pilot**：2.1e-05 s/rep；projected .0209 s；full wall 21.323 s；caps 1800s/2h/8GB；0 wells。
- **未报效果/增益/方法比较**；只做检查性诊断/规格复核。

## 3. 产出

| 文件 | 说明 |
|---|---|
| `run_m1_stage1.py` | Stage1 实现（合成/检查性） |
| `m1_stage1.json` | 结果（无 telemetry；两跑一致） |
| `m1_stage1_rows.csv` | Pθ/Q/π* 条件行 |
| `m1_stage1_diagnostics.json` | 详细诊断 |
| `schema_m1_stage1.json` | schema/失败模板（先写） |
| `timing_m1_stage1.json` | canonical telemetry |
| `report_m1_stage1.md` | 报告 |
| `record_m1_stage1.md` | 本记录 |
| `usage_m1_stage1.json` | 命令/SHA/attestation，最后写出 |

## 4. 未做/边界

- 未运行效果比较/训练/真实数据/湿实验/Stage2/3；未输出 regret/decision utility/增益/top-k。
- 未改 M1 预注册/M2/N1/A-B-D/旧门槛/旧判定/代码；不晋升代码；不恢复停止实验；不拼 ΔEMAX；技术重复≠独立培养。
- 不称药理/真实决策/迁移/机制/新颖性；B2 等价→rename_maxent，不写 M1 增量；N1 no_increment 不作 M1 证据。
- Stage2/3 需合格数据（当前 data_unavailable，C203）+ 独立挑战 + Lead 批准；本 Stage1 不构成效果/药理证据。
