# DESIGN_M3_v0_2.md —— R204-M3.1 决策反馈信用分数支撑研究执行设计（M3-C1 三必改；预注册；不运行）

2026-10-28。依据：`PROBLEM_M3_v0_2.md`、`formalism_M3_v0_2.py/json`、`schema_M3_v0_2.json`、R204 BRIEF/report、ERRATA C197/C199/C201/C207、R203 decision/power、M1 v0.2、M2 v0.2、N1 report（`no_increment` 仅其 own primary）。本文件修正 v0.1（`DESIGN_M3.md`，保留不改）：补 **optimal_experimental_design/decision_AL** 强基线、失败类别 **nonidentifiable/two_run_mismatch**、**Fisher-z 非 gate 标注**。
**状态：预注册设计草案 v0.2；不运行效果、不拟合真实/响应数据；机制账 only；compute-only 0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛；M3 Stage1 执行须另立执行预注册+独立挑战+Lead 批准。**

## 0. M3-C1 三必改落点

| # | 修正 | 落点 |
|---|---|---|
| ① | 标准基线补 `optimal_experimental_design`/`decision_AL` | `formalism_M3_v0_2.json` 的 `standard_baselines.baselines_required` 含二者；`schema_M3_v0_2.json` 的 `baselines_required` 含二者；**Stage2 arms** 显式含 `decision_AL`,`optimal_experimental_design`；**Stage3 arms** 显式含二者；M3 分配与最优设计/决策 AL 直接重叠→同信息/反馈/调参≤20/caps/合法实验包比较；等预算复制/超过→`no_increment`/撤 |
| ② | 失败类别补 `design_invalid: nonidentifiable`、`design_invalid: two_run_mismatch` | failure 全集/`schema_M3_v0_2.json`/失败模板；Stage1 共线/分离/无有限解→nonidentifiable；两跑不一致→two_run_mismatch；失败只写类别不报效果 |
| ③ | Fisher-z 标注 | 6,282.1038/1,572.7759 = **仅 Fisher-z 连续规划参考**；`non_integer=true`、`not_a_gate=true`、`not_paired_DR_formula=true`；schema/report 给 `round=6282/1573`、`ceil=6283/1573`；决策用 MDE80=.047982685、n_req278、headroom、cluster |

## 1. 一步形式化（冻结；与 PROBLEM 一致）

- `h` 已知背景/历史；`Y∈[0,1]` 独立功能；`b(a|h)` 已知随机分配；`π_k(a|h)` 冻结策略；`mθ` 功能均值。
- `H_k=π_k/b`；`δ_k=E_b[H_k(Y−mθ)]`；`V_k=E_hΣπ_k mθ+δ_k`。
- **独立评价**：计算 δ 的样本独立于 mθ 拟合与 π_k 选择，否则 `design_invalid: leakage`；mθ 可错仍有双稳健性（标准结果；不称新）。
- `logit m_{θ,ε}=logit mθ+Σ_k ε_k H_k`；独立反馈拟合 ε 使分数近零；**预定截断**；共线/分离/无支持→非有限唯一解→`design_invalid: nonidentifiable`/`inconclusive`。
- 仅功能均值更新；不等同细胞动力学兼容更新；无完整序贯历史/propensity/删失，不称序贯 DR/TMLE。

## 2. 共享分数/分配（执行公式）

- `Q_k(b)=Σ_h p(h)Σ_a π_k(a|h)^2[Var(Y|h,a)+(E[Y|h,a]−mθ(h,a))^2]/b(a|h)`。
- 错设时偏差平方未知；分配不得只用 Var；须用估计/保守上界；b≥b_min、支持、随机化记录；评价数据不得用于选 b（leakage）。
- 分配与 optimal design/decision AL 直接重叠；二者显式强基线；同预算复制/超过→`no_increment`/撤；不称分配新颖性。

## 3. 标准基线边界（同信息/同预算；必须显式比较）

**共同合同**：同特征/知识/反馈、同调参≤20 configs、同 caps **1800 s/2 h/8 GB**、同初始数据/随机化记录/合法实验包、只比较预注册端点；不得只胜错误基准。

| 基线 | 同信息/预算要点 | 备注 |
|---|---|---|
| 普通全历史重训 | 同特征/历史/初始/反馈/调参 | 一步线性可能复制 |
| 重要性加权（IW） | 同 b/H/评价样本 | 偏差-方差对照 |
| DR/TMLE targeting | 同 m 初始化/ε 拟合/截断/独立评价 | 直接强基线 |
| value-aware model learning | 同功能目标/反馈 | loss 改写可能等价 |
| 层级 GP | 同先验/批量/反馈 | 不确定性分配 |
| BATCHIE 适配 | 同批量/模型后验/反馈 | 批量选择 |
| **optimal_experimental_design** | 同 b 支持/成本/查询/合法实验包/反馈/调参/caps | **与 M3 分配直接重叠；必须显式同预算比较；复制/超过→no_increment/撤** |
| **decision_AL** | 同上；同决策采集/反馈/调参/caps | **与 M3 分配直接重叠；必须显式同预算比较；复制/超过→no_increment/撤** |

**一步线性退化**：π=b→H=1→加权残差；保留等价、撤主创新。**序贯**：不称序贯 DR。**功能 vs 细胞**：功能均值更新≠细胞动力学。

## 4. Stage 1 已知真值诊断（冻结；不运行）

### 4.1 系统

| 项 | 冻结值 |
|---|---|
| 上下文/动作/结果 | H=3；A=3；Y∈{0,1}，`P(Y=1|h,a)=μ(h,a)` 已知 |
| p(h) | `[.3,.4,.3]` |
| μ | `[[.20,.50,.80],[.40,.60,.30],[.10,.70,.50]]` |
| b | `[[.20,.30,.50],[.40,.40,.20],[.25,.35,.40]]` |
| π_1/π_2 | 确定性置换 / 混合策略（冻结于 `formalism_M3_v0_2.py`） |
| 错设 m_wrong | 全 `.5` |
| 截断示例 | C_H=20；b[0,2]=1e-3（仅演示截断偏差） |
| seed | 20261200（仅算术/检查，无效果） |

### 4.2 Stage1 检查/容差/失败

| id | 检查 | 容差/判定 | 失败类别 |
|---|---|---|---|
| M3-S1-a | DR 恒等（m_true/m_wrong，两策略） | max abs gap ≤1e-12 | `design_invalid: calibration` |
| M3-S1-b | 零支持：H 未定义、policy value 未识别 | `identified=false` | `design_invalid: support|positivity` |
| M3-S1-c | 截断偏差：有界估计≠精确 | 报告 bias；不得称精确 | `design_invalid: calibration` |
| M3-S1-d | score-tilt 简单例 ε root；score≤1e-10 | root 存在且近零 | `design_invalid: nonidentifiable`（无解/非唯一） |
| M3-S1-e | 共线 H：rank<2 | rank=1 检出 | `design_invalid: nonidentifiable` |
| M3-S1-f | 分配二阶项 full≥noise；错设 bias²>0 | 数值/单调 | `design_invalid: calibration` |
| M3-S1-g | 评价独立/无泄漏（结构） | 独立评价声明 true | `design_invalid: leakage` |
| M3-S1-h | 两跑结果逐字节一致；telemetry 单独 | byte-identical | `design_invalid: two_run_mismatch` |

Stage1 不比较方法效果/不报告增益；只输出检查/诊断/失败类别。当前形式化算术 `all_checks_pass=true`（仅自洽，不证明效果）。

## 5. Stage 2：固定更新器比较分配（预注册；不运行）

- 固定同一更新器/反馈预算/特征/调参/caps/合法实验包。
- **arms 显式含**：shared-score allocation、random allocation、GP/uncertainty allocation、**decision_AL**、**optimal_experimental_design**、DR+MLE allocation。
- 只测分配贡献；标准 DR/TMLE+最优分配等预算复制/超过→`no_increment`；超 cap→`compute_budget_exceeded`；无支持→`support/positivity`；当前不运行。

## 6. Stage 3：固定反馈比较学习 + 闭环（预注册；不运行）

- 固定同一批反馈；**arms 显式含**：candidate score-tilt、full-history retrain、IW、DR targeting、TMLE targeting、**optimal_experimental_design**、**decision_AL**（标准分配基线；同预算）。
- 主端点：独立功能决策效用/后悔；δ=**0.05 normalized**；headroom/MDE 先检；cluster=独立培养/背景/任务；**6,282.1038/1,572.7759 仅 Fisher-z 连续规划参考（非整数；round/ceil 见 schema；非 gate、非 paired DR 公式）**；**决策用 MDE80=.047982685、n_req_cluster=278、headroom、cluster**。
- 次端点：预测校准、DR 分数误差、RNA 误差；不替代主端点。最后闭环计培养/板/对照/失败/重复/校准/计算/调参成本。
- 真实数据当前 `data_unavailable`（C203/C205）；本预注册不运行。

## 7. Schema/失败/预算/数据

- **Schema**：`schema_M3_v0_2.json` 定义 formalism 必需 sections、Stage1/2/3 结果 top keys/字段、`baselines_required`（含 optimal/AL）、Stage2/3 arms、failure categories、Fisher-z 标注（round/ceil/non-gate）、caps；结果 JSON 无 telemetry。
- **失败类别全集**：`design_invalid: support`、`design_invalid: positivity`、`design_invalid: propensity`、`design_invalid: leakage`、`design_invalid: calibration`、`design_invalid: compute_budget_exceeded`、`design_invalid: nonidentifiable`、`design_invalid: two_run_mismatch`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- **停止**：标准 DR/TMLE+最优分配等预算复制/超过→撤/`no_increment`；极端权重/零支持→未识别；评价复用→leakage；超 caps→stop；CI 不能排除无实用收益→inconclusive；功能头校准不得升级为细胞规律。
- **预算**：合成 compute-only 0 wells；caps **1800 s/2 h/8 GB**；真实 Stage3 须另立预算/资源批准；不运行效果/湿实验。
- **数据需求**：独立功能读数（apoptosis/caspase/viability/regrowth 等）、随机化/倾向记录、独立培养/板/背景/任务、剂量/时间/readout、评价与选择分离、计数保留；当前 `data_unavailable`（C203/C205）；不得合成/RNA/预测替代。

## 8. 边界

支撑研究/机制账 only；不称药理/真实决策/迁移/机制/新颖性；一步公式非新意；不晋升代码；不改旧判定/门槛；不恢复停止实验；M3 Stage1 执行须另立执行预注册+独立挑战+Lead 批准；功能头校准不得称细胞规律改变。
