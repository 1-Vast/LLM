# record_m1_stage2_run —— R204-M1 Stage2 合成诊断执行审计记录（不报效果）

2026-10-28 · 角色：ON1/ON2/ON2.2/ON3 执行者（非提案者）。任务：R204-M1-S2-EXEC（按 Lead `DECISION_R204_M1_S2_EXEC.md` 执行 Stage2 合成诊断一次；仅机制账、compute-only、0 new wells）。**未执行 Stage3/真实数据/湿实验；未报告效果/decision utility/regret/top-k/方法比较；不称 M1 增量、不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；N1 不作证据；data readiness open（C203/C205/C210）。**

## 1. 时间线

| 时间（本机） | 事件 |
|---|---|
| 12:48–12:50 | 读 task-170、DECISION_R204_M1_S2_EXEC、PROBLEM/DESIGN/exec_plan/schema、Stage1 状态；核对 12 文件链 |
| 12:50–13:00 | 建 `2026-10-28-m1-stage2-run/`；先写 `schema_m1_stage2_run.json`；实现 Pθ/C-MDN/H1/H2/H3/G1–G6 |
| 13:00–13:20 | 初次执行：发现 Pθ 截断采样 rejection 极慢 + 标量 σ 索引错误；改为按截断质量重归一化 + inverse-CDF 采样；修复 C-MDN NaN（梯度裁剪）与 H3 y_dim |
| 13:20–14:00 | H1 初次 TV 偏高（Pθ 参数尺度未冻结导致 C-MDN 欠拟合）；固定 canonical Pθ 尺度（c .05/M .005/d .05）并按 H1 容差检查；H1 16/16 PASS、H2 5/5、H3 .01244 |
| 14:00–14:47 | 两跑（同 seeds、独立进程）结果 JSON/诊断/CSV 逐字节一致；冻结 telemetry；写 report/record/usage |
| 14:47–14:55 | 核对 SHA；完成 |

## 2. 输入（只读；执行时链核验）

- **12 文件链**（`exec_plan_m1_s2.json → frozen_inputs`）SHA 全匹配，`chain_pass=true`、`mismatches={}`：
  - M1 Stage2 v0.2：PROBLEM `63C0C228…`、DESIGN `642C3108…`、plan.py `482E254F…`、json `73B8C025…`、schema `9C4DF027…`、timing `488C8EF6…`、report `BCE5DE11…`、record `CBA86C88…`、Lead 接受决定 `6EC860D2…`；
  - M1 Stage1/C208：`m1_stage1.json` `EF701C66…`、report `E3701DA8…`、Stage1 决定 `EEA8CE76…`。
- Lead 执行决定 `DECISION_R204_M1_S2_EXEC.md` 存在；Stage1 `no_effect_results=true`、`failed_gates=[]`；B2 max-ent 等价已撤、`m1_increment_claimed=false`。
- 执行 seeds：Pθ param/train/eval **20261301/02/03**；H1 **20261310–25**；H2 **20261326–30**；H3 **20261331–32**；two-run **20261340–49**；与禁用区间 overlap=[]、unique=true。

## 3. 输出（本任务；只写 Stage2 run 目录与 tmp/）

| 文件 | SHA256 |
|---|---|
| `run_m1_stage2.py` | `9ED4042CD6E8B613A006B2AA7BC2073272C9076E4FB3EA6BEB1022F4A9650613` |
| `m1_stage2.json`（两跑一致） | `90DE7498C75710CC944A8617D3812F08F728EDC5C97734289533021177422C57` |
| `m1_stage2_diagnostics.json` | `B2F39E915EA6CC819272F2526A3ED9D6DB5B0BDC84D6020C8290EEE207AF4CA5` |
| `m1_stage2_checks.csv` | `D0341E1E9724F0D740D78651AE092652B8784BF9049D5CDD46749DBE7C001AC0` |
| `schema_m1_stage2_run.json` | `C1EC42FAB31C95CA1455241E818C83BAF2A9BDEA0B5919E3AED1971F05E4A459` |
| `timing_m1_stage2_run.json` | `D4B2A028AA9B0B5BB991C7F12C76DC22A8461E5F13BCAB66E803889A1AE8F18E` |
| `report_m1_stage2_run.md` | 见 usage/复核方 |
| `record_m1_stage2_run.md` | 本文件（SHA 见 usage/复核方） |
| `usage_m1_stage2_run.json` | 最后写出（SHA 见复核方） |

## 4. 实现披露（重要）

- **Pθ 参数尺度**：冻结链只规定 c/M/d 形状（(4,3,4)/(4,3,4,64)/(4,3,64)）未规定抽样分布；本执行固定 canonical `c~N(0,.05²)`, `M~N(0,.005²)`, `d~N(0,.05²)`（param_seed 20261301）。未改 H1 容差表/顺序/seed、C-MDN 结构/epochs、G1–G6 阈值。
- **σ**：按冻结 d 形状实现为**每分量标量** σ=.1+.4sigmoid(dᵀx)（对角协方差 σ²I），与冻结形状一致；无 Student-t。
- **截断采样**：按截断质量重归一化分量 + inverse-CDF 精确采样；避免 rejection 无穷等待；仍为截断 GMM。
- **C-MDN 数值稳定**：NLL/Adam lr1e-3/wd1e-5/batch256/epochs200 不变；训练中使用 y 标准化与梯度裁剪（≤10）防止 NaN；不改网络结构/输出头。
- **H1**：16 cell 顺序固定；TV 256-bin；容差表未改；16/16 PASS。
- **H2**：log-domain Sinkhorn，ε{.1,.25,.5,1,2}，maxiter2000、tol1e-8；5/5 converged；τ=1.0 固定；target Q 用 GL64/dim。
- **H3**：small-case d2/A2/Y2；oracle GL128/dim；候选 C-MDN target-action vs oracle TV=0.0124368294≤.05；仅 small-case 诊断，非高维 oracle。
- **未输出效果/增益/方法比较**；B1–B5 仅规格。未改冻结公式/阈值/端点/seed 救结果。

## 5. 两跑/预算/边界

- **chains**：12/12 PASS；Stage1 PASS；seeds overlap=[]/unique=true。
- **pilot 实测**：2 reps，wall **116.36 s**（129.90/102.82），main run **98.33 s**，CPU **322.66 s**，mem **0.056 GB**；caps **1800 s/2 h/8 GB/0 wells** PASS；结果 JSON 无 telemetry。
- **两跑**：`m1_stage2.json`、诊断 JSON、checks CSV 逐字节一致 SHA `90DE7498…`；G5 PASS。
- **G1–G6**：全 PASS；失败类别 none；未触发 design_invalid。
- **边界**：机制账 only；不执行 Stage3/真实数据/湿实验；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；M1 不与 M2/M3 混同；N1 不作证据；data readiness open（C203/C205/C210）。Stage3 须另立预注册+独立挑战+Lead 批准；本任务不批准/不执行。
