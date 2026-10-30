# PROBLEM_N1 —— R203-N1：非静态 S-add + plan-pair conflict 的合成机制预注册（设计，不运行效果）

2026-10-28。对象：R203-N1（机制账）。依据：`2026-10-28-decision-power-scope/`（R203-P1：PROBLEM_DECISION/DESIGN_SCOPE/power_scope）、`DECISION_R203_P1_SCOPE.md`（Lead 批准仅范围/规划）、A 线 C192–C195 停止记录。
**状态：设计/预注册草案，未执行任何效果或预测；不运行 N1/N2 效果；不改旧判定/门槛；不晋升代码；不恢复已停止实验；机制账 only（不称药理/真实决策/迁移/机制/新颖性）。**
**与 A 线的关系**：A 线（静态 S-add 联合矛盾检验）已停止归档；N1 **不是**其改名重做：N1 的生成过程含隐藏状态转移/历史依赖/计划对共享动态核，且终点是 held-out decision regret（非"矛盾存在性"检测）。

## 0. 一句话问题

在**已知 ground-truth 的合成非静态 S-add + plan-pair conflict** 环境中，**一次反馈的统一修订**（联合更新隐藏状态后验与状态依赖算子）能否在 held-out **决策后悔**上优于**等计算/等信息预算**的基线（full retrain、static S-add、hierarchical/EB、GP、random plan-pair、decision AL）？

## 1. 与已停止静态 S-add 的实质区别（形式化）

### 1.1 静态 S-add（已停止 A 线的对象；作为 N1 的**退化特例**）

对 plan p=(a,b)（A 药 a、B 药 b），剂量 (d_a,d_b)：

```
y_p(d_a,d_b) = f_a(d_a) + g_b(d_b) + ε,   ε ~ N(0, σ²)
```

- 算子 `(f_a,g_b)` **不随轮次/状态/历史变化**；计划对之间无共享动态核；无 plan-pair conflict；反馈不改变状态。
- 对应 A 线的静态 4×4 网格联合矛盾检验。

### 1.2 N1 非静态生成过程（本质不同）

对合成单位 i（独立 replicate）的决策序列 t=1..T：

1. **隐藏状态** `s_t ∈ {1..S}`（**S=3**，冻结）；初始 `s_1 ~ π0`（Dirichlet 先验）。
2. **状态转移（含历史/动作依赖）**：
   ```
   P(s_t = s' | s_{t-1}=s, a_{t-1}, r_{t-1}) = softmax_s'(α_s' + β·1[r_{t-1}≥τ] + γ·1[a_{t-1} ∈ conflict-set])
   ```
   `a_{t-1}` 为上一轮选择、`r_{t-1}` 为上一轮观测响应；`β,γ ≠ 0` ⇒ **历史/动作依赖**（静态特例：P=I 且 β=γ=0）。
3. **计划对共享动态核**：同一轮的两个计划 p=(a,b)、q=(c,d) 的观测共享**同一隐藏状态** s_t；每轮至少一个 plan-pair 被联合观测（pair window）。
4. **状态依赖算子**：
   ```
   y_p(d_a,d_b | s_t) = f_{a,s_t}(d_a) + g_{b,s_t}(d_b) + h_{a,b,s_t}(d_a,d_b) + ε
   ```
   `f,g` 随状态变化（非静态）；`h` 为 **plan-pair conflict/interaction**（`h=0` 时退回非静态加性；`S=1` 且 `h=0` 时**完全退化为静态 S-add**）。
5. **一次反馈统一修订**：每轮结束只观测**一个**反馈（所选计划在下一轮的验证观测或 pair window 的联合响应）；策略用这一个反馈**联合更新** `(state posterior, f_{·,s}, g_{·,s}, h)`；无额外 oracle/无重复测量。
6. **决策/菜单**：每轮给出**菜单** `M_t`（m=5 个候选 plan，从 12-plan universe 无放回抽取）；决策者选 `â_t ∈ M_t`；**held-out** 轮次（T_hold=2）不参与任何更新，只用于评价 regret。

**静态 S-add = 上述过程的退化点**：`S=1`、`P=[1]`、`β=γ=0`、`h≡0`、`f,g` 不随轮次变化。

### 1.3 "若 generator 退化为静态"的可检验判据（先于效果；失败类别 `design_invalid: rename_static_Sadd`）

在 N1 执行前/校准阶段，对生成器本身（已知 ground-truth）做以下四项检验；**任一项不满足即 `design_invalid: rename_static_Sadd`，停止且不运行效果**：

| # | 判据 | 操作化 | 阈值（预注册） |
|---|---|---|---|
| V1 | **状态可检测** | GT-nonstatic 下，状态条件均值分离度 `Δ_f = min_{s≠s'} ||f_{a,s}−f_{a,s'}||₂ / σ`；LRT（静态 vs 状态模型）非中心参数 λ_state | Δ_f ≥ **2.0** 且 λ_state 使 power≥.80（见生成器校准） |
| V2 | **历史/动作依赖** | transition 参数 `β,γ` 的 KL 贡献 `KL(P(·|r=1)‖P(·|r=0))` | ≥ **0.10** nat；且估计的 `β,γ` 在参数恢复中 95% CI 不含 0 |
| V3 | **plan-pair conflict 真实存在** | interaction 能量 `E_h = mean_{a,b,s} ||h_{a,b,s}||² / σ²` | ≥ **0.20**；且无 `h` 模型在 GT-nonstatic 下校准失败 |
| V4 | **静态模型不可吞并** | 在 GT-nonstatic 数据上，静态 S-add 的 held-out 预测 ELPD 显著低于非静态模型（预注册 n_rep、α=.05） | ΔELPD ≥ **2×SE**（否则 generator 实际可被静态解释→rename_static_Sadd） |

**若 V1–V4 任一失败：`design_invalid: rename_static_Sadd`；不得用改名/换终点/换生成器救活。**

## 2. 生成器冻结（预注册参数；详见 `generator_n1.json`）

| 组件 | 冻结值/形式 |
|---|---|
| 状态数 | S=3；π0=Dirichlet(1,1,1)（每次 replicate 固定抽样，记录 seed） |
| 序列长度 | T=6（其中 T_fit=4 用于在线更新，T_hold=2 held-out） |
| 单位/菜单 | 每 replicate：n_units=300 独立单位；每轮菜单 m=5；plan universe=12 plan（A 药 3×B 药 4 的组合子集） |
| 剂量 | 每药 4 级（4×4 网格，归一化剂量 ∈{0,1/3,2/3,1}） |
| 算子 | `f_{a,s}(d)=Σ_{k=1..3} φ_k(d)·θ^{f}_{a,s,k}`（3 基函数：常数/线性/quadratic；θ 先验 N(0,1)）；`g` 同构；`h_{a,b,s}(d_a,d_b)=Σ_{k,l} ψ_{kl}(d_a,d_b)·η_{a,b,s,kl}`，η 稀疏（预注册 2 个活跃基） |
| 状态转移 | softmax 参数：α_s（N(0,.5)），β=−1.2（响应≥τ 时更持久），γ=+0.8（上轮选 conflict-set 时更易切换）；τ=中位数响应 |
| 噪声 | σ=0.15（训练）、σ=0.15（held-out）；另设 σ 敏感性 .10/.20（仅校准诊断） |
| 违例 | GT-static：S=1、β=γ=0、η=0；GT-nonstatic：S=3、β/γ≠0、η≠0、状态核分离 Δ_f≥2σ |
| 反馈 | 每轮 1 次观测（选中 plan 的下一轮验证观测或已选 pair 的联合响应） |
| 初始数据 | 每单位首轮前无数据；策略共享同一初始数据（round 1 的 pair window） |
| 随机性 | 每 replicate 独立 seed；生成器 seed 集合预注册（如 20261030 + r） |

## 3. 可辨识性/gauge（预注册）

- **状态标签置换**：S 个状态的任意置换不可辨识 → 报告时按 `Var(f_{·,s})` 降序固定状态序（gauge fixing）。
- **加性常数 gauge**：`f_{a,s} → f_{a,s}+c_s`、`g_{b,s} → g_{b,s}−c_s` 不改变观测（非静态 S-add 的 gauge）→ 固定 `mean_d f_{a,s}(d)=0`。
- **interaction gauge**：`h_{a,b,s} → h_{a,b,s}+φ_s(d_a)+ψ_s(d_b)` 可被 f,g 吸收 → 固定 `h` 在剂量网格上双中心化（行/列均值为 0）。
- **可辨识参数**：状态间算子差 `f_{a,s}−f_{a,s'}`、`g_{b,s}−g_{b,s'}`、transition 的 β/γ（相对 α）、interaction 能量与形状（双中心化后）。
- **不可辨识**：绝对状态标签、绝对加性常数、可能的状态特定尺度与噪声比（在固定 σ 下报告敏感性）。
- **参数恢复门**（校准阶段）：状态核相关 ≥.90、transition TV ≤.10、β/γ 95% CI 不含 0、interaction 能量相关 ≥.90、Jacobian 在 gauge-fixed 子空间满秩；失败→`design_invalid: nonidentifiable`。

## 4. 主终点：held-out decision regret（δ=.05 normalized）

- **决策集/菜单**：每轮菜单 `M_t ⊂ P`（|M_t|=5，无放回）；held-out 轮 t∈{5,6} 的菜单只用 held-out 决策。
- **效用**：对单位 i、轮 t、菜单 M_t：`U_t(p) = (ȳ_control − ȳ_p(d_{a},d_{b}))/(ȳ_control − ȳ_floor)`，其中 `ȳ_p` 为 plan p 的 4×4 网格在剂量组合（最优组合由 ground-truth 已知）的响应，`ȳ_control` 为对照（单药最大剂量），`ȳ_floor` 为预注册下限；**U∈[0,1]**，越大越好。
- **regret**：`r_t = max_{p∈M_t} U_t(p) − U_t(â_t)`（normalized，∈[0,1]）；单位 i 的 held-out regret `R_i = mean_{t∈held-out} r_t`。
- **主终点（paired）**：`D_i = R_i(method) − R_i(baseline)`（lower-better；负值=方法更好）；primary test = paired mean ΔR 的 95% CI，δ=.05 normalized，paired across n_units，按 replicate/cluster 计。
- **headroom 预检**（执行前，用 GT + 校准 pilot）：
  - `U0` = 基线策略的 held-out utility（≈1−R0）；`U_max`=1（或 ground-truth 上限）；`headroom = U_max − U0`；要求 `δ ≤ headroom`，否则 `unreachable_gate`（不降 δ；若基线近满分，另立 **budget-to-target**（E5）问题，不静默换终点）。
  - `MDE80 = 2.801585 × SD(D) / sqrt(n_units)`；`n_req = ceil((2.801585×SD(D)/δ)²)`；cluster：`n_req,cluster = ceil(n_req × [1+(m−1)ICC])`；要求 `MDE80 ≤ δ` 且 `n_units ≥ n_req`，否则 `precision_insufficient`。
- **不静默换终点**：headroom/MDE 不通过时停止；不得改 δ/换 baseline/换端点（须新预注册）。

## 5. 等 compute/query 基线（预注册清单）

统一规则：同一 prior、同一初始数据（round-1 pair window）、同一次反馈预算（每轮 1 次）、同一 query 数（每单位 T=6 轮）、同一调参预算（每方法 ≤20 个超参配置，嵌套 CV 在同一数据）、同一 wall/CPU cap、同一特征信息（全部单位 histories 相同；no leakage）。

| id | 基线 | 信息/更新 | 说明 |
|---|---|---|---|
| B1 | **full retrain** | 每轮用全历史重拟合静态 S-add（无状态） | 同数据/同预算，非状态依赖 |
| B2 | **static S-add（同信息同预算）** | 只有静态 `f_a+g_b`；无状态/历史 | **关键强基线**；若等效→撤算法主张 |
| B3 | **hierarchical/EB** | 随机效应（按 unit/state 部分池化） | 同更新次数 |
| B4 | **GP** | 输入 (a,b,d_a,d_b) 的 GP 回归 | 同 query 数/调参预算 |
| B5 | **random plan-pair** | 随机选 plan-pair 观测（无冲突定向） | 同预算 |
| B6 | **decision AL** | 基于不确定性的主动学习选 plan | 同预算 |
| **M** | **N1 method** | 状态后验 + 一次反馈联合修订（f,g,h） | 主方法 |

## 6. 校准/资格门（先于效果；失败只写 `design_invalid`，不报效果）

| 门 | 内容 | 阈值 | 失败类别 |
|---|---|---|---|
| G1 generator 校准（FPR） | GT-static 下，状态/历史/interaction 检测器的 FPR（"误报非静态"） | ≤ α=.05 | `calibration_failed` / `rename_static_Sadd` |
| G2 generator 校准（power） | GT-nonstatic 下检测 power（检测非静态） | ≥ .80（n_rep=200） | `calibration_failed` |
| G3 可辨识/参数恢复 | §3 指标 | 见 §3 | `nonidentifiable` |
| G4 无泄漏 | held-out 轮不参与更新；特征不含 hidden state；菜单抽样与状态独立（除通过观测） | 审计检查 | `leakage` |
| G5 两跑 | 同 seed 两跑，结果 JSON 逐字节一致 | 是 | `design_invalid` |
| G6 schema | 预注册输出字段/失败模板 | 是 | `design_invalid` |
| G7 预算 | pilot 计时投影 ≤ caps | wall≤**1800 s**、CPU≤**2 h**、内存≤**8 GB** | `compute_budget_exceeded` |

## 7. 失败类别/停止（统一）

`design_invalid: rename_static_Sadd`（V1–V4 任一失败）、`generator_misspecified`、`calibration_failed`、`nonidentifiable`、`leakage`、`compute_budget_exceeded`、`no_increment`（门通过但效应<δ且 CI 排除 0）、`inconclusive`（CI 不能分辨）、`unreachable_gate`/`precision_insufficient`。**任何强基线（尤其 B2 static S-add）等预算等效 → 撤回算法增量主张（`no_increment`），不称新颖性/决策收益。**

## 8. 预算与边界

- **合成 pilot**：10 replicate 计时（生成器+特征+baseline stub，不比较方法）→ `timing_n1_pilot.json`；主预算：n_units=300、R=50 replicate、7 方法、T=6 轮、每轮 1 反馈；wall≤**1800 s**、CPU≤**2 h**、内存≤**8 GB**；**不得使用 A/B 线资源**（纯 compute，0 wells）。
- **边界**：机制账 only；不称药理/真实决策/迁移/机制/新颖性；合成≠药理；不晋升代码；不恢复已停止实验；不改旧门槛/判定；不运行效果结论。
- **注意**：本文件与 `generator_n1.py` 仅为设计/算术/合成 pilot 计时；**任何 N1 效果执行须另立预注册 + 独立挑战 + Lead 批准**。
