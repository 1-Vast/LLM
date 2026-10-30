# PROBLEM_M3_v0_2.md —— R204-M3.1 决策反馈信用分数（DR/TMLE 支撑）预注册（M3-C1 三项必改落实；**不运行效果**）

2026-10-28。对象：R204 **M3/D3 支撑机制**——同一组决策反馈分数连接功能均值修订与实验分配。本文件修正 v0.1（`PROBLEM_M3.md`，保留不改），落实 M3-C1 挑战 3 必改：**标准基线补 optimal_experimental_design/decision_AL**、**失败类别补 nonidentifiable/two_run_mismatch**、**Fisher-z 标注为非 gate 连续规划参考**。依据：`2026-10-28-deep-coupling-redesign/{report.md,BRIEF_R204.md}`、ERRATA C197/C199/C201/C207、R203 decision/power、M1 v0.2、M2 v0.2、N1 `report_n1_effect.md`（N1 `no_increment` 仅其 own primary，**不作 M3 证据**）。
**状态：预注册设计草案 v0.2；未运行效果比较、未拟合真实/响应数据、未声称增益；机制账 only、compute-only 0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；M3 Stage1 执行须另立执行预注册+独立挑战+Lead 批准。**

## 0. M3-C1 三必改落实

| # | 挑战问题 | v0.2 落实 |
|---|---|---|
| ① | 标准基线漏 `optimal_experimental_design`/`decision_AL`；JSON/schema/Stage2–3 arms 未显式 | **`standard_baselines.baselines_required` 加入 `optimal_experimental_design`、`decision_AL`**；**`schema_M3_v0_2.json` 同步**；**Stage2 arms 显式含二者；Stage3 arms 显式含二者**；写明 M3 分配主张与最优设计/决策 AL 直接重叠，必须同信息/同反馈/同调参≤20/同 caps/同合法实验包比较；**标准 DR/TMLE+最优分配等预算复制/超过 → `no_increment`/撤** |
| ② | 失败类别漏 `design_invalid: nonidentifiable`、`design_invalid: two_run_mismatch` | **failure category 全集/schema/失败模板补全**；Stage1 共线/分离/无有限解→`design_invalid: nonidentifiable`；两跑不一致→`design_invalid: two_run_mismatch`；失败只写类别、不报效果 |
| ③ | Fisher-z 6,282.1038/1,572.7759 标注不清 | 标为**仅 Fisher-z 连续规划参考**：非整数、非通用决策门、非 paired DR 公式；schema/report 给 **round/ceil** 并标 **"非 gate"**；决策仍用 **MDE80=.047982685 / n_req_cluster=278 / headroom / cluster**（独立培养/背景/任务），不用 6,282 做 M3 推断 |

保留：DR/截断/ε root/共线/分配二阶项/π=b/两跑/pilot/caps；形式化/更新/边界；三阶段；data_unavailable（C203/C205）；支撑研究/机制账；N1 不作 M3 证据；旧判定/门槛不变。

## 1. 定位（写死）

- M3 是**支撑研究候选**：同一份决策反馈分数同时用于（i）功能均值修订方向、（ii）下一批实验分配方向；**不是**成熟第三主算法，**不冒充细胞动力学兼容更新**。
- 一步 DR 是标准 DR/重要性校正/最大熵型倾斜的重述；**不据名称声称新意**。
- **同预算强基线（尤其 optimal_experimental_design、decision_AL、DR/TMLE+最优分配）复制/超过 → 撤主算法主张（`no_increment`）**，保留等价支撑/边界结果。
- N1 `no_increment` 仅其 own primary，不作 M3 正/负证据。

## 2. 一步形式化（冻结；仅诊断/规划）

- `h` 已知背景/历史；`Y∈[0,1]` 独立功能读数；`b(a|h)` 已知实际随机分配；`π_k(a|h)` 冻结候选策略；`mθ(h,a)` 功能均值。
- `H_k(h,a)=π_k(a|h)/b(a|h)`；`δ_k=E_{h,a∼b}[H_k(Y−mθ)]`；策略值 `V_k=E_h[Σ_aπ_k mθ]+δ_k`。
- **DR 正确性条件**：b>0 覆盖 π 支持；**评价样本独立于 mθ 拟合与 π_k 选择**（否则 `leakage`）；mθ 可错仍有双稳健性（标准结果；不称新）。
- 更新：`logit m_{θ,ε}=logit mθ+Σ_k ε_k H_k`；独立真实反馈拟合 ε 使分数趋零；**预定概率/权重截断**；共线/分离/无支持→不保证有限唯一解→`design_invalid: nonidentifiable`/`inconclusive`；不得用任意大 ε 掩盖。
- **只更新功能均值头**；未建立细胞状态/轨迹核兼容性，不能称细胞规律改变；无完整序贯历史/propensity/删失，不宣称序贯 DR/TMLE。

## 3. 共享分数与实验分配（待验证）

- 同一组 H/δ 也用于设计下一批 b；冻结 m 时单个策略二阶项：
  `Σ_h p(h)Σ_a π_k(a|h)^2 [Var(Y|h,a)+(E[Y|h,a]−mθ(h,a))^2] / b(a|h)`。
- 错设时 `(E−mθ)^2` 非零且未知；**不能只按 Var 分配**；须用估计/保守上界（冻结 b_min/截断/最坏情况目标）。
- 约束：b 概率单纯形、b≥b_min、动作支持、随机化记录；零支持/极端权重→`support/positivity`；分配设计不得复用评价结果选 b（`leakage`）。
- **M3 分配主张与 optimal_experimental_design、decision_AL 直接重叠**；二者必须作为显式强基线；同预算复制/超过→`no_increment`/撤；不声称分配新颖性。

## 4. 与标准方法的边界（同信息/同预算；必须显式比较）

| 基线 | 必须固定的同信息 | 备注 |
|---|---|---|
| 普通全历史重训 | 同特征/历史/初始数据/反馈/调参≤20 | 一步线性可能复制 |
| 重要性加权（IW） | 同 b/H/评价样本 | 偏差-方差对照 |
| DR/TMLE targeting | 同 m 初始化/ε 拟合/截断/评价独立 | 直接强基线 |
| value-aware model learning | 同功能目标/反馈 | loss 改写可能等价 |
| 层级 GP | 同先验信息/批量/反馈 | 不确定性分配对照 |
| BATCHIE 适配 | 同批量/模型后验/反馈 | 批量选择强基线 |
| **optimal_experimental_design** | 同 b 支持/成本/查询/合法实验包；同信息/反馈/调参/caps | **与 M3 分配直接重叠；必须显式同预算比较；复制/超过→no_increment/撤** |
| **decision_AL** | 同上；同决策相关采集规则/反馈/调参/caps | **与 M3 分配直接重叠；必须显式同预算比较；复制/超过→no_increment/撤** |

**共同合同**：同特征/知识/反馈、同调参预算（每方法≤20 configs）、同计算 caps **1800 s/2 h/8 GB**、同初始数据/随机化记录/合法实验包、只比较预注册 DR/决策端点；不得只胜错误基准。
**一步线性退化**：π=b→H=1，score-tilt=加权残差；保留等价、撤"深世界模型创新"。
**序贯**：无完整序贯历史/propensity/删失，不称序贯 DR。
**功能 vs 细胞**：只更新功能均值 ≠ 细胞动力学兼容更新。

## 5. 最小验证三阶段（预注册；不运行）

### Stage 1：一步合成/已知真值（仅诊断）

- 已知 `p(h),b(a|h),μ(h,a),π_k` 有限离散系统；检查 DR 恒等/双稳健、截断、零/低支持、错设、共线/分离、分配二阶项。
- **失败类别显式**：共线/分离/无有限解 → `design_invalid: nonidentifiable`；两跑不一致 → `design_invalid: two_run_mismatch`；零支持/极端权重 → `design_invalid: support|positivity`；截断/校准 → `design_invalid: calibration`。
- 不比较方法效果、不报告增益；只输出检查/诊断。

### Stage 2：固定更新器，比较实验分配

- 固定同一更新器/反馈预算/特征/调参/caps/合法实验包；**arms 显式含**：shared-score、random、GP/uncertainty、**decision_AL**、**optimal_experimental_design**、DR+MLE 最优分配。
- 只测分配贡献；标准 DR/TMLE+最优分配等预算复制/超过→`no_increment`；超 cap→`compute_budget_exceeded`；无支持→`support/positivity`；当前不运行。

### Stage 3：固定反馈，比较学习，再闭环计成本

- 固定同一批反馈；**arms 显式含**：candidate vs full-history retrain、IW、DR targeting、TMLE targeting、**optimal_experimental_design**、**decision_AL**（标准分配基线；同预算）。
- 主端点：独立功能下的实际决策效用/后悔；**δ=0.05 normalized**；先 headroom/MDE；cluster=独立培养/背景/任务；**6,282.1038/1,572.7759 仅为 Fisher-z 连续规划参考（非整数；schema/report 给 round/ceil；非 gate、非 paired DR 公式）**；**决策用 MDE80=.047982685、n_req_cluster=278、headroom、cluster**。
- 次端点：预测校准、DR 分数误差、RNA 误差（不替代主端点）；最后闭环计成本。
- 当前不运行；真实数据 **data_unavailable（C203/C205）**。

## 6. 失败类别/停止/预算/数据

- **失败类别全集**：`design_invalid: support`、`design_invalid: positivity`、`design_invalid: propensity`、`design_invalid: leakage`、`design_invalid: calibration`、`design_invalid: compute_budget_exceeded`、`design_invalid: nonidentifiable`、`design_invalid: two_run_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- **停止**：标准 DR/TMLE+最优分配等预算复制/超过→撤/`no_increment`；极端权重/零支持→未识别；评价样本复用选策略→`leakage`；超 caps→stop；CI 不能排除无实用收益→`inconclusive`；功能头校准不得升级为细胞规律。
- **预算**：合成 compute-only、**0 wells**；caps **1800 s/2 h/8 GB**；不运行真实效果/湿实验。
- **数据**：独立功能读数（apoptosis/caspase/viability/regrowth 等）、随机化/倾向记录、独立培养/板/背景/任务、剂量/时间/readout、评价与策略选择分离、计数保留；当前 `data_unavailable`（C203/C205）；不得合成/RNA/预测替代独立功能决策。

## 7. 边界

支撑研究/机制账 only；不称药理/真实决策/迁移/机制/新颖性；合成≠药理；一步公式非新意；不晋升代码；不改旧判定/门槛；不恢复停止实验；M3 Stage1 执行须另立执行预注册+独立挑战+Lead 批准；功能头校准不得称细胞规律改变。

## 8. 产物

`PROBLEM_M3_v0_2.md`（本文）、`DESIGN_M3_v0_2.md`、`formalism_M3_v0_2.py/json`、`schema_M3_v0_2.json`、`report_M3_v0_2.md`、`record_M3_v0_2.md`、`usage_M3_v0_2.json`、`timing_M3_pilot_v0_2.json`；v0.1 产物保留不改；未运行效果。
