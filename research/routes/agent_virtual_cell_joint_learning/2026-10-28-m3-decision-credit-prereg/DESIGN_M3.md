# DESIGN_M3.md —— R204-M3-P1 决策反馈信用分数支撑研究执行设计（预注册；不运行）

2026-10-28。依据：`PROBLEM_M3.md`、`formalism_M3.py/json`、`schema_M3.json`、R204 BRIEF/report、ERRATA C197/C199/C201/C207、R203 decision/power、M2 v0.2、M1 v0.2、N1 report（`no_increment` only its own primary）。
**状态：预注册设计草案；不运行效果、不拟合真实/响应数据；机制账 only；compute-only 0 wells；不称药理/真实决策/迁移/机制/新颖性；不晋升代码；不改旧判定/门槛。Stage1/2/3 执行须另立预注册+独立挑战+Lead 批准。**

## 0. 批准范围/前置

- 本文件只定义 M3 支撑研究的形式化、Stage1–3 设计、诊断/失败类别、分析规划与预算；**不批准执行**。
- 冻结：一步 DR/重要性校正、score-tilt 更新、概率/权重截断、评价独立、Stage1 已知真值检查；标准基线（全历史重训/IW/DR/TMLE/value-aware/层级-GP/BATCHIE）；同信息/同反馈/同调参/caps；主端点/δ、headroom/MDE/cluster、6,282 仅 Fisher-z。
- 不改旧门槛/旧判定；不恢复停止实验；不晋升代码；真实数据当前 `data_unavailable`（C203/C205）。

## 1. 一步形式化（与 PROBLEM 一致；此处给执行公式）

### 1.1 已知量与估计

- `h`：记录背景/历史；`a`：合法动作；`Y∈[0,1]` 独立功能读数；`b(a|h)>0`：实际随机化概率（已知）；`π_k(a|h)`：冻结候选策略；`mθ(h,a)`：功能均值预测。
- `H_k(h,a)=π_k(a|h)/b(a|h)`；`δ_k=E_{h,a∼b}[H_k(Y−mθ)]`；`V_k=E_h[Σ_aπ_k(a|h)mθ(h,a)]+δ_k`。
- **独立评价**：用于计算 `δ_k` 的样本必须独立于 mθ 的拟合与 π_k 的选择；否则 `design_invalid: leakage`。mθ 可在独立训练样本上拟合；Stage 预注册必须写明拆分/交叉拟合。
- **双稳健性只作为待核事实**：b 已知且支持覆盖时，mθ 任意时 `E[δ_k+Σπ mθ]` 等于真实策略值（标准 DR；不是新意）。

### 1.2 更新/截断

- `logit m_{θ,ε}=logit mθ + Σ_k ε_k H_k`；在独立真实反馈上拟合 ε 使 `E[H_k(Y−m_{θ,ε})]` 近零。
- 预先冻结权重/概率截断 `H_k≤C_H` 与 `b≥b_min`（Stage1 的 C=20、b_min=1e-3 仅为诊断示例，须在 Stage1 执行预注册时确认/冻结；不得看结果再改）。
- **非唯一/不保证有限解**：H_k 共线、某些方向被分离、或 ε 边界解 → `nonidentifiable`/`inconclusive`；不得用任意大 ε 掩盖。
- 只更新功能均值头；**不等同于**细胞状态轨迹核/动力学兼容更新。

## 2. 共享分数/分配（预注册公式）

- 冻结 m 时，单个 k 的估计方差贡献（二阶项）：
  `Q_k(b)=Σ_h p(h) Σ_a π_k(a|h)^2 [Var(Y|h,a)+(E[Y|h,a]−mθ(h,a))^2] / b(a|h)`。
- **错设**：`(E−mθ)^2` 非零且未知；分配不得只用 `Var`；须用估计/保守上界（如 `|E−mθ|≤B(h,a)` 的冻结界）构造最坏情况目标。
- 约束：b 概率单纯形、b≥b_min、动作支持、随机化记录；极端 H/零支持→`support/positivity`；分配设计不得复用评价结果选择 b（`leakage`）。
- 分配比较的候选基线：random、GP/不确定性、决策 AL、DR+MLE 最优分配；同一更新器、同成本、同信息。

## 3. 标准基线边界（同信息/同预算）

| 基线 | 必须固定的同信息 | 备注 |
|---|---|---|
| 全历史重训 | 同特征/历史/初始数据/反馈/调参 | 一步线性可能复制 |
| 重要性加权 | 同 b/H/评价样本 | 偏差-方差对照 |
| DR/TMLE targeting | 同 m 初始化/ε 拟合/截断/评价独立 | 直接强基线 |
| value-aware model learning | 同功能目标/反馈 | loss 改写可能等价 |
| 层级 GP | 同先验信息/批量/反馈 | 不确定性分配对照 |
| BATCHIE 适配 | 同批量/模型后验/反馈 | 批量选择强基线 |
| 最优实验设计/决策 AL | 同 b 支持/成本/查询 | 分配强基线 |

**共同合同**：同特征/知识/反馈/调参≤20 configs/计算 caps **1800 s、2 h、8 GB**/初始数据/随机化记录；只比较预注册 DR/决策端点；不得只胜错误基准。
**一步线性退化**：若 π=b（H=1）或线性 m，score-tilt 退化为加权残差；保留等价结论，撤主创新。
**序贯**：无完整序贯历史/propensity/删失，不宣称序贯 DR/TMLE。

## 4. Stage 1：已知真值诊断（冻结；不运行）

### 4.1 系统

| 项 | 冻结值 |
|---|---|
| 上下文 | H=3；p(h)=[.3,.4,.3] |
| 动作 | A=3 |
| 结果 | Y∈{0,1}，`P(Y=1|h,a)=μ(h,a)`（已知真值） |
| μ 表 | `[[.20,.50,.80],[.40,.60,.30],[.10,.70,.50]]` |
| b 表 | `[[.20,.30,.50],[.40,.40,.20],[.25,.35,.40]]` |
| π_1 / π_2 | 确定性置换策略 / 混合策略（见 `formalism_M3.py`；冻结） |
| 错误模型 m_wrong | 全 `.5`（仅诊断错设） |
| 截断示例 | C_H=20；b[0,2]=1e-3（仅演示截断偏差） |
| 诊断 seed | 20261200（固定；仅算术/检查，无随机效果） |

### 4.2 Stage1 检查与容差

| id | 检查 | 容差/判定 | 失败类别 |
|---|---|---|---|
| M3-S1-a | DR 期望恒等（m_true 与 m_wrong；两策略） | max abs gap ≤ **1e-12** | `design_invalid: calibration` |
| M3-S1-b | 零支持反例：H 未定义、policy value 未识别 | 检出 `identified=false` | `design_invalid: positivity/support` |
| M3-S1-c | 截断偏差：有界估计≠精确 policy value | 报告 bias；不得称精确 | `design_invalid: calibration`（若隐瞒） |
| M3-S1-d | score-tilt：简单例 ε root；score≤1e-10 | root 存在且 score 近零 | `nonidentifiable`（若无解/非唯一） |
| M3-S1-e | 共线 H：rank<2→ε 非唯一 | 检出 rank 1 | `nonidentifiable` |
| M3-S1-f | 分配二阶项：full≥noise；错设 bias 项>0 | 数值/单调检查 | `design_invalid: calibration` |
| M3-S1-g | 评价独立/无泄漏（结构） | 独立评价集声明 true | `design_invalid: leakage` |

**Stage1 不比较方法效果/不报告增益**；只输出上述检查/诊断；任何检查失败只写类别。形式化算术结果见 `formalism_M3.json`（当前 `all_checks_pass=true`，仅说明算术自洽，不证明效果）。

## 5. Stage 2：固定更新器比较分配（预注册；不运行）

- 固定：同一功能更新器、同反馈预算、同特征/调参/计算；比较 shared-score allocation vs random vs GP/uncertainty vs decision AL vs DR+MLE optimal。
- 设计：合成已知 truth（可先沿用 Stage1 系统扩展）或获批真实记录；每个 arm 同查询数/成本；分配仅影响下一批 b。
- 端点：分配后 DR 分数/策略值误差、后续决策效用（若进入 Stage3）；次端点不作主结论。
- 分析：按独立单位/cluster 配对；同预算；强基线复制→`no_increment`；预算超→`compute_budget_exceeded`；无支持→`support/positivity`；当前 **不运行**。

## 6. Stage 3：固定反馈比较学习 + 闭环（预注册；不运行）

- 固定同一批反馈（同信息/同预训练）；比较 candidate score-tilt vs full-history retrain、IW、DR targeting、TMLE targeting；同特征/调参/预算。
- 主端点：独立功能下的实际决策效用/后悔值（per endpoint 分别规划）；**δ=0.05 normalized**；先 `headroom=U_max−U0`（<δ→`unreachable_gate`；近满分→另立 budget-to-target，不换端点）；配对 `MDE80=2.801585·SD(D)/√n_eff`；cluster=独立培养/背景/任务；**6,282 仅 Fisher-z 相关比较规划，非通用决策门/非 paired DR 样本量**。
- 次端点：预测校准、DR 分数误差、RNA 误差；RNA/内部一致性不能替代独立功能决策。
- 最后闭环计培养/板/对照/失败/重复/校准/计算/调参成本；不得把规划推演当免费。
- 真实数据当前 **data_unavailable（C203/C205）**；本预注册不运行。
- 停止：标准 DR/TMLE + 最优分配等预算复制/超过→`no_increment`/撤主算法；CI 不能排除无实用收益→`inconclusive`；功能头校准→不得升级为细胞规律。

## 7. Schema/失败/预算

- **Schema**：`schema_M3.json` 定义 Stage1/2/3 产物 top keys、每方法/每 replicate 字段、summary、失败模板；结果 JSON 无 telemetry；wall/CPU/内存仅进 timing。
- **失败类别全集**：`design_invalid: support|positivity|propensity|leakage|calibration|compute_budget_exceeded`、`unreachable_gate`、`precision_insufficient`、`no_increment`、`inconclusive`。
- **预算**：合成 Stage1/2 compute-only、**0 wells**、caps **wall≤1800 s/CPU≤2 h/内存≤8 GB**；真实 Stage3 须另立预算/资源批准；本预注册不运行效果/湿实验。
- **数据需求**：独立功能读数（apoptosis/caspase/viability/regrowth 等）、随机分配/倾向记录、独立培养/板/背景/任务、剂量/时间/readout、评价与策略选择分离、计数保留；当前 AZ 数据字典/功能 numeric 缺失（C203/C205）→ `data_unavailable`，不得合成/RNA 替代。

## 8. 边界

机制账/支撑研究 only；不称药理/真实决策/迁移/机制/新颖性；一步公式非新意；不晋升代码；不改旧判定/门槛；不恢复停止实验；M3 执行须另立预注册+独立挑战+Lead 批准。
