# record_m3_stage1 —— R204-M3 Stage 1 合成诊断执行记录

2026-10-28 · 角色：ON1/ON2/ON3/D1/D3/D5/A/B 线同一独立审计/实现者。
**任务：R204-M3-STAGE1（支撑研究、仅机制账、compute-only、0 wells；不报效果）。** 只写 `research/2026-10-28-m3-stage1/` 与 tmp/；未改 M3 预注册/M1/M2/N1/A-B-D/旧门槛/旧判定/代码；未运行效果比较/训练/真实数据/湿实验；Stage2/3 未执行。

## 0. 时间线

| 时间（Asia/Shanghai） | 事件 |
|---|---|
| — | 读 task-162、DECISION、M3 v0.2 PROBLEM/DESIGN/formalism/schema/timing、ERRATA |
| — | 新建 `2026-10-28-m3-stage1/`；先写 `schema_m3_stage1.json`（链/19 checks/S1/失败模板/臂） |
| — | 实现 `run_m3_stage1.py`：链核验、只读 import v0.2 `run_core`、19 checks、S1 诊断、基线/臂、两跑/timing |
| — | canonical 跑通：chain_ok=True；19/19 checks + S1 全 PASS；failure=null |
| — | 两个独立进程 run1/run2：result/checks/diagnostics/schema 逐字节一致；写 report/record/usage |

## 1. 输入（只读）

| 文件 | 用途 |
|---|---|
| `DECISION_R204_M3_STAGE1.md` | Stage1 批准范围/边界 |
| `PROBLEM_M3_v0_2.md` / `DESIGN_M3_v0_2.md` | 一步 DR/自检/19 checks/基线/阶段 |
| `formalism_M3_v0_2.py/json` | 冻结 DR/clip/score/alloc/planning 算术（只读 import） |
| `schema_M3_v0_2.json` | failure_categories/failure_template/Fisher-z/arms/caps |
| `timing_M3_pilot_v0_2.json` | v0.2 pilot 参考；本实现重新测 canonical |
| ERRATA C197/C199/C201/C207 | 决策/6,282 边界；N1 不作 M3 证据 |

## 2. 结果摘要

- **19/19 checks PASS**：DR identity gap 0；support counterexample；clip bias −.0264071856287；score root −.562633036711；collinearity rank1；allocation full≥noise；MDE .047982685≤.05；n_req278≤300；π=b H=1；optimal/decision_AL 在 baselines/Stage2/Stage3；failure nonidentifiable/two_run_mismatch 存在；Fisher-z 非门/非 paired DR。
- **S1 诊断全 PASS**：ratios 1.2172284644/1.1668676321；zero support identified=False；MDE/n_eff/n_req；Fisher-z labels。
- **基线/arms**：Stage2 6 arms、Stage3 7 arms；optimal_experimental_design/decision_AL 均列；仅规格登记，未执行比较。
- **两跑**：result `60845EFA…84F052D`、checks `2E6E3C8F…3FFDFBE`、diagnostics `D0816802…A4C4DFD8`、schema `B0DC56A8…A489D1BC` 一致；timing 单独。
- **pilot**：1.6347e-04 s/rep；projected .001635 s；full wall .007137 s；caps 1800s/2h/8GB；0 wells。
- **失败类别**：null；无 design_invalid；未报效果/增益。

## 3. 产出

| 文件 | 说明 |
|---|---|
| `run_m3_stage1.py` | Stage1 实现（合成/检查性） |
| `m3_stage1.json` | 结果（无 telemetry；两跑一致） |
| `m3_stage1_checks.csv` | 19 checks + S1 行 |
| `m3_stage1_diagnostics.json` | 详细诊断 |
| `schema_m3_stage1.json` | schema/失败模板（先写） |
| `timing_m3_stage1.json` | canonical telemetry |
| `report_m3_stage1.md` | 报告 |
| `record_m3_stage1.md` | 本记录 |
| `usage_m3_stage1.json` | 命令/SHA/attestation，最后写出 |

## 4. 未做/边界

- 未运行效果比较/训练/真实数据/湿实验/Stage2/3；未输出 decision utility/regret/增益/top-k。
- 未改 M3 预注册/M1/M2/N1/A-B-D/旧门槛/旧判定/代码；不晋升代码；不恢复停止实验；不拼 ΔEMAX；技术重复≠独立培养。
- 不称药理/真实决策/迁移/机制/新颖性；只更新功能均值≠细胞动力学；无完整序贯 history/propensity/删失不称序贯 DR。
- 标准 DR/TMLE+最优分配等预算复制/超过→撤 M3 算法主张；Stage2/3 需合格数据（当前 data_unavailable C203/C205）+ 独立挑战 + Lead 批准。
