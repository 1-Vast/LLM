# record_m3_stage2_run —— R204-M3 Stage2 合成分配诊断执行记录

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/实现者。
**任务：R204-M3-S2-EXEC（支撑研究/机制账、compute-only、0 wells；不报效果）。** 只写 `research/2026-10-28-m3-stage2-run/` 与 tmp/；未改 exec prereg/M3 Stage1/M1/M2/N1/A-B-D/旧门槛/旧判定/代码；未运行 Stage3/真实数据/湿实验；0 wells。

## 0. 时间线

| 时间（Asia/Shanghai） | 事件 |
|---|---|
| — | 读 task-178、Lead DECISION、v0.2 exec plan/schema、M3 Stage1、ERRATA |
| — | 新建 `2026-10-28-m3-stage2-run/`；先写 `schema_m3_stage2_run.json`（17+决定链/13 字段/13 失败/G1–G6/caps） |
| — | 实现 `run_m3_stage2.py`：链核验、final pilot 2 reps、main R=10、六 arms、per-arm 字段、G1–G6、两跑/timing |
| — | pilot 实测 wall .100688/CPU .078125/mem .001249；main .204259/.203125/.001293；caps PASS |
| — | 两独立进程 result/CSV/diagnostics/schema 逐字节一致；写 report/record/usage |

## 1. 输入（只读）

| 文件 | 用途 |
|---|---|
| `DECISION_R204_M3_S2_EXEC.md` | Stage2 批准范围/边界 |
| `PROBLEM/DESIGN_M3_S2_EXEC_v0_2.md` | 样本语义/13 字段/G1–G6/失败 |
| `exec_plan_m3_s2_v0_2.json` | 环境/arms/chain/预算 |
| `schema_m3_s2_exec_v0_2.json` | 13 字段/失败/caps/forbidden |
| M3 Stage1 | C209：19/19+S1 PASS；仅支撑/机制账 |
| ERRATA C197/C199/C201/C207/C209/C210 | Fisher-z/预算/边界 |

## 2. 执行结果

- **链核验**：17 文件 + Lead 决定全部 match；`chain_ok=True`。
- **Pilot**：2 reps×6 arms×300 alloc；wall .100688s、CPU .078125s、mem .001249GB；PASS。
- **Main**：R=10；wall .204259s、CPU .203125s、mem .001293GB；PASS。
- **样本**：21,000 total units；18,000 allocation/feedback；每 arm 300/300/tuning 0/合法包。
- **per-arm**：60/60 pass；13 字段齐全；H/δ finite；clipping n=0（max raw H=1.6667<C_H=20）；allocation_Q full≥noise；equal budget PASS。
- **G1–G6**：G1–G4/G6 PASS；G5 两跑外部 PASS；无失败类别。
- **两跑**：result `36C4DF12…46CE7FE`；CSV `ACAF4635…28E5A1`；diagnostics `4A742BA0…BD8176`；schema `0E46DEC0…A2F499`；timing 单独。
- **未输出** decision utility/regret/top-k/方法比较/学习效果。

## 3. 产出

| 文件 | 说明 |
|---|---|
| `run_m3_stage2.py` | Stage2 实现（合成分配诊断） |
| `m3_stage2.json` | 结果（两跑一致；无 telemetry） |
| `m3_stage2_per_arm.csv` | 60 arm records ×13 字段 |
| `m3_stage2_diagnostics.json` | 链/G/失败/payload SHA |
| `schema_m3_stage2_run.json` | schema/失败模板（先写） |
| `timing_m3_stage2_run.json` | pilot+main canonical timing |
| `report_m3_stage2_run.md` | 报告 |
| `record_m3_stage2_run.md` | 本记录 |
| `usage_m3_stage2_run.json` | 命令/SHA/attestation，最后写出 |

## 4. 边界

- 支撑研究/机制账 only；不执行 Stage3/真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；M3 不与 M1/M2 混同；N1 不作 M3 证据；data readiness open（C203/C205/C210）。
- 分配诊断不解释为学习效果/决策收益；DR/TMLE+最优分配等价判定留 Stage3；不得用合成/RNA 替代独立功能决策。
- 标准 caps 1800s/2h/8GB/0 wells；两跑逐字节；JSON 无 telemetry。
