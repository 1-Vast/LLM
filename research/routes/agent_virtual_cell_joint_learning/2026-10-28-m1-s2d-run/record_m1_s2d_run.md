# record_m1_s2d_run —— R204-M1-S2d 错配/背景漂移规划比较执行记录

2026-10-28 · 角色：独立实现者（endpoint-auditor）。
**任务：R204-M1-S2D-EXEC（机制账、compute-only、0 wells；不报真实效果）。** 只写 `research/2026-10-28-m1-s2d-run/` 与 tmp/；未改 prereg/S2c/H1b/C216/C217/M1 设计链/M2/M3/N1/A-B-D/旧门槛/旧判定/代码；未执行真实数据/湿实验。

## 0. 时间线

| 时间（Asia/Shanghai） | 事件 |
|---|---|
| — | 读 task-205、Lead DECISION、v0.3 PROBLEM/DESIGN/headroom/schema、S2c/C223、H1b、C216/C217/C208 |
| — | 新建 `2026-10-28-m1-s2d-run/`；先写 `schema_m1_s2d_run.json`（链/三 targets/headroom/六比较/caps） |
| — | 实现/修正 `run_m1_s2d.py`：源 Pθ 训练、T1/T2/T3 目标解析、source/adapted/5 baselines、60 cells、headroom、Holm、pilot/main |
| — | 执行时 headroom T1 .485465/T2 .564308/T3 .396520 均≥.10；T1 primary PASS；两跑 result `20DD8347…` 逐字节一致 |
| — | 写 report/record/usage |

## 1. 链/环境

- v0.3 7 文件 + Lead 决定 SHA match；chain.pass=True；无 chain_mismatch。
- 源 Pθ 同 H1b/S2c；T1 c'~N(0,1²) seed20262001（主）；T2 M'~N(0,.2²) seed20262002；T3 X'~N(0,1.5²I)。
- X d=64、A=4、r=wᵀy−λ||y||²、π0 full；S=4096/动作；known-truth 目标解析。
- 候选仅源 Pθ 训练；目标数据只评价+adapted baseline（3584 source+512 target/动作）；未用目标数据训练/调参。
- seeds：headroom 20262011–30；data 20262031；eval 20262032；T1 20262041–60；T2 20262061–80；T3 20262141–60；**20262100 未用**；T2 valid_eval_rows **4093**。

## 2. 执行结果

- **headroom execution**：T1 .485465；T2 .564308；T3 .396520；均≥.10；未触发 unreachable_gate；未降 δ/换 seed/环境。
- **pilot 60 cells**：wall 419.491 s、CPU 971.531 s、memory 1.08057 GB；caps PASS。
- **main 60 cells**：wall 411.332 s、CPU process cumulative 1950.0 s、memory 1.08124 GB；caps PASS。
- **T1 primary**：mean D **−.147824** CI [−.163759,−.131890] Holm **2.11e-73** → **PASS**；raw candidate .485031 vs source baseline .632855。
- **T1 secondary**：adapted +.018718、maxent +.109666、conditional 0、random +.112661、softmax +.079249；**candidate 不如 maxent/random/softmax/adapted**，如实登记。
- **T2**：source D −.006979 CI 跨 0；adapted D −.015901 Holm .77；T2 主比较不通过；**不 pool T1**。
- **T3**：source D −.084667 Holm 9.78e-18；T3 内多个 secondary 显著；**主成功仅 T1，不写迁移/机制**。
- **等价审计**：candidate 与 source empirical/ max-entropy 逐点不等价；conditional 共用 C-MDN D=0；未用目标数据训练/调参。
- **两跑** result `20DD8347…`；replicates CSV `33D6E75D…`；diagnostics `E87059AC…`；timing 单独；JSON 无 telemetry。
- **verdict planning_comparison_pass_T1**；failure None；旧状态不变。

## 3. 产出

| 文件 | 说明 |
|---|---|
| `run_m1_s2d.py` | S2d 实现 |
| `m1_s2d_result.json` | 两跑一致结果（无 telemetry） |
| `m1_s2d_replicates.csv` | 60 cells×6 baselines raw/D |
| `m1_s2d_diagnostics.json` | 链/headroom/targets/primary |
| `schema_m1_s2d_run.json` | schema/失败模板（先写） |
| `timing_m1_s2d_run.json` | pilot/main canonical telemetry |
| `report_m1_s2d_run.md` | 报告 |
| `record_m1_s2d_run.md` | 本记录 |
| `usage_m1_s2d_run.json` | 命令/SHA/attestation，最后写出 |

## 4. 边界

- 机制账 only；合成 compute-only、0 wells；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open；用户 public-only。
- T2/T3 不合并/不 pool；主成功仅 T1；T2/T3 次级不豁免 CI；不用规划 MDE 当功效。
- 旧 C216 0/16、design_invalid: projection、C217、H1b 密度-only、C208 一步投影撤全部不变。
