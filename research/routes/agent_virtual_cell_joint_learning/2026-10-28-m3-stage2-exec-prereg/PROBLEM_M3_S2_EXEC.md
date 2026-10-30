# PROBLEM_M3_S2_EXEC —— R204-M3 Stage2 合成执行预注册草案（固定更新器分配比较；不运行）

2026-10-28。对象：R204-M3（支撑研究：决策反馈信用分数 → 功能均值修订 + 实验分配）。依据：M3 v0.2 链、Lead `DECISION_R204_M3_STAGE1.md`（`9743CF2E…`）、M3 Stage1/C209（`60845EFA…`，19 checks PASS）、R204 BRIEF/report、ERRATA C197/C199/C201/C207/C209/C210、R203 decision/power。
**状态：执行预注册草案；未运行 Stage2 训练/效果/真实数据；仅规划/算术/骨架单测；支撑研究/机制账 only；compute-only、0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；M3 不与 M1/M2 混同；N1 不作 M3 证据；data readiness open（C203/C205/C210）。**

## 0. 定位

- M3 是**支撑研究候选**：同一组决策反馈分数（H/δ）同时用于功能均值修订方向与下一批实验分配方向；**不是成熟第三主算法**；**一步 DR 是标准方法重述，不称新意**。
- Stage1（C209）已 PASS：DR 恒等 gap 0、截断 bias −0.026407185629、ε root −0.562633036711、共线 rank 1、π=b→H=1、分配二阶项 ratios 1.21722846/1.16686763、19 checks PASS、两跑逐字节、pilot .00016347 s/rep。
- **本预注册仅 Stage2 合成分配诊断**：固定更新器，只比较实验分配；**不输出 decision utility/regret/top-k/学习效果比较**；标准 DR/TMLE+最优分配等预算复制/超过→`no_increment`/撤的判定**留给后续 Stage3**；本轮只登记规格与可复现性。

## 1. 链核验（执行前；不匹配→stop）

`exec_plan_m3_s2.py` 本地只读核验 **17 文件 SHA**（chain_pass=true、mismatches=0）：
- M3 v0.2 八件：PROBLEM `15DFE82C…`、DESIGN `033D67CB…`、formalism py `3E709B81…`、formalism json `299E5B03…`、schema `E2E641BC…`、timing `BA261FA7…`、report `039B1A98…`、record `47042AD6…`；
- **Lead 决定 `9743CF2E…`**；
- Stage1/C209 八件：`m3_stage1.json` `60845EFA…`、diagnostics `D0816802…`、checks.csv `2E6E3C8F…`、schema `B0DC56A8…`、timing `7432135D…`、report `3FCAC827…`、record `EDB0AC38…`、usage `7F8E2E6A…`。
- 不匹配 → `design_invalid: chain_mismatch`、不报结果；执行时重核。

## 2. 独立执行 seeds（不得复用）

| 用途 | seeds |
|---|---|
| Stage2 合成数据/环境 | **20261401** |
| 6 个 allocation arms | **20261410–20261415** |
| 两跑 replicate | **20261420–20261429**（10 个） |

- **禁复用**：M3 Stage1 算术 seed 20261200；M1 Stage1 20261112/20261113；M1 v0.2 20261201/02/03；**M1 Stage2 执行 20261301–20261349**；M2 Stage2 20261200–20261239；M2 Stage3 20262100–20262139；N1 gate/dev 20261030/61/62/63。
- 本地 **overlap=[]、unique=true**；两跑同 seeds、独立进程、结果 JSON 逐字节、telemetry 单独；**执行时不得改 seed**。

## 3. Stage2 合成设置（冻结）

### 3.1 一步 DR 环境（h/Y/b/π_k/mθ）

- H=3 contexts、A=3 actions、Y∈[0,1] 二值功能读数；`p(h)=[.3,.4,.3]`；μ=[[.20,.50,.80],[.40,.60,.30],[.10,.70,.50]]；b=[[.20,.30,.50],[.40,.40,.20],[.25,.35,.40]]；π_1 确定性置换、π_2 冻结混合策略。
- `H_k=π_k/b`；`δ_k=E_{h,a~b}[H_k(Y−mθ)]`；`V_k=E_h[Σπ_k mθ]+δ_k`；`logit m_{θ,ε}=logit mθ+Σε_kH_k`；独立反馈拟合 ε。
- **已知真值**：m_true=μ；m_wrong=.5；正支持主例；**零支持诊断**（b=0 且 π mass=1→未识别）；**截断 C_H=20**；**共线诊断**（H 列 rank<2）；**分离诊断**（全 Y=0 且正 H→root 在 −inf，非有限唯一）；π=b→H=1 退化。
- **评价独立**：δ 计算样本独立于 mθ 拟合与 π_k 选择；target 样本不作标签；评价不得用于选 b。

### 3.2 仅比较分配（6 arms；同 learner/updater）

| arm | 角色 | 分配规则 |
|---|---|---|
| **S_shared_score** | 候选 | shared-score `Q_k(b)` 分配（H/δ/mθ） |
| **S_random** | 基线 | 随机合法分配 |
| **S_gp_uncertainty** | 基线 | GP/不确定性分配 |
| **S_decision_AL** | **显式等预算强基线** | decision active learning |
| **S_optimal_experimental_design** | **显式等预算强基线** | optimal experimental design |
| **S_DR_MLE_allocation** | 标准基线 | DR+MLE 最优分配 |

- **同信息/反馈/调参≤20/caps/合法实验包**；只测分配贡献；**不输出 decision utility/regret/top-k/学习效果比较**。
- 标准 DR/TMLE+最优分配等预算复制/超过→`no_increment`/撤的判定**留给后续 Stage3**；本轮只登记规格与可复现性。

## 4. G1–G6 / 失败类别

- **G1 支持/程序**：b>0 on π support、b≥b_min、动作支持、随机化记录；失败→`support/positivity`。
- **G2 截断**：预设 C_H=20；clipped 估计≠精确 policy value；报告 bias/bound；失败→`calibration`。
- **G3 分配二阶项**：`Q=Σ_h p(h)Σ_a π_k(a|h)^2[Var(Y|h,a)+(E[Y|h,a]−mθ)^2]/b`；full≥noise；错设 bias² 非零/未知；不能只按 Var 分配；失败→`calibration`。
- **G4 无泄漏**：评价样本独立于 mθ 拟合/策略选择；target 不作标签；分配设计不复用评价；失败→`leakage`。
- **G5 两跑**：结果 JSON 逐字节；telemetry 单独；失败→`two_run_mismatch`。
- **G6 schema/预算**：schema 先写；caps 1800 s/2 h/8 GB/0 wells；失败→`compute_budget_exceeded`。
- **失败类别**：`design_invalid: support|positivity|propensity|leakage|calibration|compute_budget_exceeded|nonidentifiable|two_run_mismatch|chain_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。

## 5. 预算/两跑/schema

- caps **1800 s/2 h/8 GB/0 wells**；**执行前用最终实现实测 pilot 并冻结 canonical timing**（文档/JSON 同一 snapshot；不得混用旧 pilot）；结果 JSON 无 telemetry；失败只写类别。
- Stage1 pilot 参考（仅参考，执行必须重测）：per-rep **.00016347 s**、projected **.001635 s**、full Stage1 wall **.007137 s**（SHA `7432135D…`）。
- `schema_m3_s2_exec.json` 先写：top/arm/checks/forbidden fields（decision utility/regret/topk/method comparison/learning effect/gain/pharmacology/real decision/transfer/mechanism/novelty/real data/sequential DR claim）；两跑逐字节。

## 6. 停止/边界

- **停止/分类**：π=b→H=1 退化（保留等价、不称新意）；共线/分离/无支持→`design_invalid: nonidentifiable`；零支持/极端权重→`support/positivity`；截断 bias→`calibration`（clipped 非精确 policy value）；评价复用→`leakage`；两跑/链/预算失败→对应类别；**任何失败不改旧判定/门槛**；不放宽容差/改阈值/换端点。
- **只更新功能均值 ≠ 细胞动力学兼容更新**；无完整序贯 history/propensity/删失→**不称序贯 DR/TMLE**。
- 机制账 only；**不执行 Stage3/真实数据/湿实验**；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定；不恢复停止实验；**M3 不与 M1/M2 混同**；N1 不作 M3 证据；data readiness open（C203/C205/C210）；Stage2 执行须另立独立挑战+Lead 批准；Stage3 另立预注册。
