# record_m1_stage2_rerun —— R204-M1-S2-RERUN 纠正性重跑记录

2026-10-28 · 角色：独立实现者（endpoint-auditor）。
**任务：R204-M1-S2-RERUN（按冻结尺度纠正重跑一次；机制账 only；compute-only；0 wells；不报效果）。** 只写 `research/2026-10-28-m1-stage2-rerun/` 与 tmp/；未改上次无效运行产物/设计链/M1 Stage1/M2/M3/N1/A-B-D/旧门槛/旧判定/代码；未执行 Stage3/真实数据/湿实验。

## 0. 时间线

| 时间（Asia/Shanghai） | 事件 |
|---|---|
| — | 读 task-179、Lead `DECISION_R204_M1_S2_RERUN.md`（C215）、冻结 DESIGN/PROBLEM 行锚、exec prereg、上次 invalid run |
| — | 新建 `2026-10-28-m1-stage2-rerun/`；先写 `schema_m1_stage2_rerun.json`（尺度行锚/上次偏离/12+决定/失败类别） |
| — | 基于冻结实现复制并修正 Pθ 尺度：`c .5²/M .1²/d .1²`；H1/H2/H3 容差/顺序/seed 全部保持；加 rerun 链/上次 invalid 披露 |
| — | final pilot（2 reps×H1 16 C-MDN/Q_g GL64/H3 GL128）实测 wall 159.69s/CPU 281.21s/mem .0714GB；main wall 158.05s/CPU 277s/mem .0717GB；caps PASS |
| — | corrected rerun 结果：H1 **0/16 FAIL**，H2 5/5 PASS，H3 .01340 PASS；G3 FAIL → **design_invalid: projection**；未改阈值 |
| — | 两跑 result/checks/diagnostics 逐字节一致；写 report/record/usage |

## 1. 冻结尺度（行锚）

- DESIGN_M1_STAGE2_v0_2.md **line 23**：`c~N(0,.5²)`、`M~N(0,.1²)`、`d~N(0,.1²)`。
- PROBLEM_M1_STAGE2_v0_2.md **lines 31/32/33**：同尺度；**line 34** σ=.1+.4·sigmoid(dᵀx)；**line 28** box [-2,2]^4；K=3/[.5,.3,.2]。
- 本次实现使用 **.5/.1/.1**；未使用 `.05/.005/.05`。

## 2. 上次无效运行披露

- 上次 task-170 结果 SHA **`90DE7498C75710CC944A8617D3812F08F728EDC5C97734289533021177422C57`**。
- **invalid_run: protocol_deviation**：使用 `.05²/.005²/.05²`（10×缩小），与冻结 `.5²/.1²/.1²` 不符；该次 H1/H2/H3/G/两跑全部不作证据，未登记 qualification_pass。
- 本次结果中 `previous_invalid_run` 显式记录该 SHA/偏离/不作证据；不删除/不改写上次产物。

## 3. 链/执行

- 12 文件 SHA + Lead `DECISION_R204_M1_S2_RERUN.md`（`6CF1256C…`）match；chain.pass=True；seeds overlap=[]、unique=true。
- Pθ：param/train/eval seeds **20261301/02/03**；train 4096/eval 2048；target Q GL64/dim；target 样本不作标签；Doob 不可执行。
- C-MDN：K=3/hidden 128/2 ReLU/NLL/Adam lr1e-3/wd1e-5/batch256/epochs200；y 标准化与 grad clip≤10 仅数值稳定，不改分布。
- H1 16 格 d/N 顺序与容差表未改；H2 ε/maxiter/tol 未改；H3 GL128/TV≤.05 未改。

## 4. 结果摘要

- **H1 0/16 PASS**（全部超冻结容差；TV 0.1284–0.3667 vs 0.07–0.18）→ **projection**。
- **H2 5/5 收敛**（max marginal error≤9.9e-9≤1e-8；iter 17–303）。
- **H3 TV 0.01340352≤.05**（small-case only）。
- **G1/G2/G4/G5/G6 PASS；G3 FAIL（H1）**；`verdict=design_invalid: projection`；**未写 qualification_pass**。
- **pilot** wall 159.6908s/CPU 281.2109s/mem .071407GB；**main** wall 158.0514s/CPU 277s/mem .071739GB；caps PASS。
- **两跑** `m1_stage2_rerun.json` 逐字节 **`B2CD01954F88F40111AFC286ECD7B67A45CB57E96B3D95C06E35936447B72107`**；checks/diagnostics 一致；timing 单独；JSON 无 telemetry。
- **未输出** decision utility/regret/top-k/方法比较/效果。

## 5. 产出

| 文件 | 说明 |
|---|---|
| `run_m1_stage2_rerun.py` | corrected Stage2 实现 |
| `m1_stage2_rerun.json` | 结果（两跑一致；无 telemetry） |
| `m1_stage2_rerun_checks.csv` | H1/H2/H3 检查表 |
| `m1_stage2_rerun_diagnostics.json` | H1/H2/H3/G 诊断 |
| `schema_m1_stage2_rerun.json` | schema/失败模板（先写） |
| `timing_m1_stage2_rerun.json` | pilot/main canonical telemetry |
| `report_m1_stage2_rerun.md` | 报告 |
| `record_m1_stage2_rerun.md` | 本记录 |
| `usage_m1_stage2_rerun.json` | 命令/SHA/attestation，最后写出 |

## 6. 边界

- corrected rerun 失败按设计登记 `design_invalid: projection`；未改尺度/阈值/顺序/预设救结果；不得把失败解释为效果/机制/药理阴性。
- 上次 invalid_run 仍无效；本次也不构成 qualification_pass；进一步重跑须另立预注册+独立挑战+Lead 批准。
- 机制账 only；不执行 Stage3/真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）。
