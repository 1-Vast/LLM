# record_m1_s2c_run —— R204-M1-S2c 候选规划比较执行记录

2026-10-28 · 角色：独立实现者（endpoint-auditor）。
**任务：R204-M1-S2C-EXEC（机制账、compute-only、0 wells；不报真实效果）。** 只写 `research/2026-10-28-m1-s2c-run/` 与 tmp/；未改 prereg/H1b/C216/C217/M1 设计链/M2/M3/N1/A-B-D/旧门槛/旧判定/代码；未执行真实数据/湿实验。

## 0. 时间线

| 时间（Asia/Shanghai） | 事件 |
|---|---|
| — | 读 task-198、Lead DECISION、v0.2 PROBLEM/DESIGN/headroom/schema、H1b/C222、C216/C217/C208 |
| — | 新建 `2026-10-28-m1-s2c-run/`；先写 `schema_m1_s2c_run.json`（链/headroom/六比较/失败/caps） |
| — | 实现 `run_m1_s2c.py`：链核验、执行时 headroom、Pθ/C-MDN、6 baselines、known-truth regret、Holm、pilot/main |
| — | 首跑发现 selected one-sided p 方向写反（负改善被算成 p≈1）；修正为 lower-tail p 后重跑 |
| — | 修正后结果：headroom full .220878/constrained .254295≥.10；primary mean D −.055231、Holm 4.83e-16→PASS；两跑 result `4977B74E…` 逐字节一致 |
| — | 写 report/record/usage |

## 1. 链/环境

- v0.2 7 文件 + Lead 决定 SHA match；chain.pass=True；无 chain_mismatch。
- Pθ 同 H1b：c .5²/M .1²/d .1²；σ=.1+.4sigmoid(dᵀx)；box[-2,2]^4；K=3/[.5,.3,.2]；param/train/eval 20261301/02/03。
- X~N(0,I_d)，d=64 主/d=16 次；A=4；r=wᵀy−λ||y||²；π0 full/constrained；S=4096/动作；known-truth 解析独立。
- 数据 20261921；eval 20261922；cells 20261931–54；headroom 20261901–20；两跑同 seeds。

## 2. 执行结果

- **headroom 执行核对**：full .22087767 CI [.21898153,.22277381]；constrained .25429506 CI [.25258376,.25600636]；均≥.10；未触发 unreachable_gate。
- **pilot 20 reps**：wall 347.687 s、CPU 712.156 s、memory .67076 GB；caps PASS。
- **main 20 reps**：wall 326.841 s、CPU process cumulative 1400.953 s、memory .67147 GB；caps PASS。
- **六比较**：primary mean D **−.055231** CI [−.068569,−.041892] Holm **4.83e-16** PASS；max-entropy −.121548；conditional_density_MC 0；constrained_SB −.156064；random −.156421；softmax −.102394。
- **等价审计**：candidate vs empirical-mean/max-entropy 动作逐点不等价；P_conditional_density_MC 与 candidate 共用 C-MDN（D=0）。
- **verdict planning_comparison_pass**；failure None；旧 C216/C217/H1b/C208 不变。
- **两跑** result `4977B74E…`；replicates CSV `E9C3D012…`；diagnostics `83588098…`；timing 单独；JSON 无 telemetry。
- **未输出**真实数据/效果/药理/真实决策/迁移/机制/新颖性；机制账 only。

## 3. 产出

| 文件 | 说明 |
|---|---|
| `run_m1_s2c.py` | S2c 实现 |
| `m1_s2c_result.json` | 两跑一致结果（无 telemetry） |
| `m1_s2c_replicates.csv` | 20 reps×6 baselines raw/D/pass |
| `m1_s2c_diagnostics.json` | 链/headroom/比较/失败 |
| `schema_m1_s2c_run.json` | schema/失败模板（先写） |
| `timing_m1_s2c_run.json` | pilot/main canonical telemetry |
| `report_m1_s2c_run.md` | 报告 |
| `record_m1_s2c_run.md` | 本记录 |
| `usage_m1_s2c_run.json` | 命令/SHA/attestation，最后写出 |

## 4. 边界

- 机制账 only；合成 compute-only、0 wells；不执行真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210/C214）；用户 public-only。
- 旧 C216 0/16、design_invalid: projection、C217 归因、H1b 密度-only、一步投影撤（C208）全部不变；未改旧文件/旧容差/旧判定。
