# DESIGN_A22 —— R201-A.2.2 执行设计（异方差稳健 σ/零模型/诊断；新预注册；不执行 P1）

2026-10-28。依据：[PROBLEM_A22.md](PROBLEM_A22.md)、`sigma_robust_A22.json`（合成校准/选择）、C194、A.2 v0.2 链、DECISION_R201_A2_EXEC、challenge_A2。
**状态：预注册草案（未执行）。A.2.2 须先经独立挑战 + Lead 批准后才可运行；不得用 A.2/A.1 observed 结果后验选规则。**

## 0. 范围与原则

- A.2.2 = **新整体预注册**：只修 **σ/F_pair 归一化/null/D2–D3 诊断**；P1 统计量结构/族/数据/|U|/N_perm/BH/阳性三条件保持 A.2 定义。
- A.2 `design_invalid: scale_mismatch` 与 A.1 `p0p1_negative` 均保持原样、不重判；A.2.2 通过前不进入 P2/S2/H_A2。
- data-only、0 新 wells；non-blind/peeked；不做生物学/机制/迁移/决策收益/新颖性主张。

## 1. 不变对象

| 项 | 冻结值 |
|---|---|
| 数据/人群 | O'Neil batch1 complete-case、target30、完整 4×4 网格；702/315 pair-cell 排除 |
| |U| | **340,088** |
| legal 规则 | **A.2 原规则不变**：`RMS ≤ 1.96·σ_obs_A2`，σ_obs_A2=σ_w_hat/2（阈值≈0.0910607）；n_legal_A2≥17,004.4 否则 coverage |
| 族 | S-add（role-stratified） |
| 统计量结构 | `F_pair=[||P⊥(f_p−f_q)||²/(K−1)]/σ²(shared context)`；per-cell `T_c=max`；pooled `#(F≥F_crit)/n_legal_A2` |
| F_crit | 2.60（仅 D2+D3 通过时保留） |
| N_perm / BH / 阳性 | 500（seed=20261029）/ q=0.05（30 细胞）/ 三条件不变 |

## 2. σ 与 F_pair 归一化（A.2.2 唯一改变的尺度部分）

- **R4 per-context 尺度（primary；合成校准选定，见 PROBLEM_A22 §1）**：
  对每个 context c=(cell, drug, role)（共享上下文），由该 context 下所有 **full-profile plan 对** (a,b)：
  `σ²_R4(c) = mean_{a<b} [ ||P⊥(f_a−f_b)||²/(K−1) ]`（f 为 full 4-rep profile；H0 下 pair 差为纯噪声）。
- **前置检查**：每 context 需 ≥2 plans 且 σ²_R4(c) 有限、>1e-12；不满足的 context 的 plan/pair **不进入 F 推断**并计数；要求被排除 pair 比例 ≤5%（否则 `design_invalid: coverage`）。
- **F_pair 归一化**：pair 共享 context c ⇒ 用同一 σ²_R4(c) 归一化：
  `F_pair = [||P⊥(f_p−f_q)||²/(K−1)] / σ²_R4(c)`。
- **不做**：全局单一 σ、med/trim 全局尺度、half-split 逐 context 尺度（R1）均不采用（合成校准中 R1 worst-context FPR .424 超门、R0/R2 coverage .50–.60）；保留为诊断敏感性（不参与判定）。

## 3. D1–D7 诊断门（先于 P1；按序）

| 门 | 内容 | 失败类别 |
|---|---|---|
| D1 | 全部纳入 context 的 σ²_R4(c) 有限、>1e-12、非退化；σ_w_hat 有限 | `design_invalid: scale_mismatch` |
| D2 | ① per-context F_self_check 中位 coverage∈[0.5,2] **≥0.85**；② 全局 F_self_check 中位∈[0.5,1.5]；③ overall F_self_check FPR@F_crit≤0.10；④ ratio 诊断（p95/p05）报告 | `design_invalid: scale_mismatch` |
| D3 | ① overall FPR@F_crit≤0.10；② **worst-context FPR≤0.25**；③ **context-FPR p95≤0.20**（F_self_check 在 context 层的 FPR） | `design_invalid: noise_calibration` |
| D4 | primary null（pooled）中位∈[0.02,0.15]（null 计算后） | `design_invalid: null_calibration` |
| D5 | `median(T_null)/median(T_obs)∈[0.2,3]`（null 计算后） | `design_invalid: null_calibration` |
| D6 | pilot 预算投影 ≤ caps（执行前） | `design_invalid: compute_budget_exceeded` |
| D7 | G1–G5（覆盖/可识别/泄漏/边界断言，A.1 定义）+ peek 披露 | A.1/A.2 既有类别 |

**F_crit 条件**：D2+D3 全 PASS 才保留 F_crit=2.60（R4 标准化后 F~χ²₃/3）；否则 `design_invalid: scale_mismatch`；不缩放 observed F、不改阈值。

## 4. 零模型（A.2.2 冻结）

- **pooled null（N0-strat）**：legal pair 按 context 分层；每次 replicate 对每 pair 抽取 `F* ~ χ²₃/3`（标准化后），pooled* = mean(F*≥F_crit)；N=500，seed=20261029；得 Q95 与中位。
- **per-cell null（N1-R4）**：seed=20261029；每次 replicate：对每共享 context c 拟合 `f_hat(c)=mean full profile`；每 plan 生成 `f*_p = f_hat(c) + ε_p`，`ε_p ~ N(0, σ²_R4(c)/2)`（per dose）；重算各 pair 的 `F*`（用 σ²_R4(c)）与 per-cell `T_c*`（legal pair 集固定为 A.2 observed legal 集）；N=500。
- **p 值/BH**：`p_c=(1+#{T_c*≥T_c})/(1+500)`；BH q=0.05（30 细胞）；无 legal pair 的细胞 p=1。
- **阳性三条件（同 A.1）**：① BH 拒绝≥5；② pooled_obs ≥ Q95_N0；③ D1–D7 全 PASS。阳性→`p1_positive`（仅"本资源/本族/本设计下存在联合矛盾（开发性）"）；否则→`p1_negative`（仅 `no_joint_contradiction`）。

## 5. 执行流程与预算

1. 读数据 → 建 plan-cell 与 context → 估 σ_w_hat、σ_obs_A2（A.2 同定义）→ A.2 legal 集。
2. 估 R4 per-context σ²；前置检查/排除计数；D1。
3. F_self_check（R4 归一化）→ D2/D3；F_crit 保留判定。
4. D7 G1–G5；D6 pilot 预算测试（测 N1/N0 单次耗时投影；caps：wall≤900 s、CPU≤2 h、内存≤8 GB；≈2,500 模拟：N1 500 + N0 500 + 诊断 1,500）。
5. 观测 F_pair/T_c/pooled（R4 归一化）→ N0-strat → N1-R4 → D4/D5 → 阳性三条件。
6. 两跑逐字节一致；结果 JSON 无 telemetry（wall/CPU/内存写 usage/diagnostics）；行级 CSV 逐细胞。
- 失败类别统一：`design_invalid: scale_mismatch` / `noise_calibration` / `null_calibration` / `compute_budget_exceeded` / A.1–A.2 既有类别（coverage/identifiability/leakage/family）。
- 超预算→`design_invalid: compute_budget_exceeded`（不减 N_perm/不换便宜分析）。

## 6. 解释边界与批准清单

- 阳性仅开发性存在性；阴性仅 `no_joint_contradiction`（**不写"矛盾不存在"**）；pair 级仅描述性；不称生物学/机制/迁移/决策收益/新颖性；non-blind/peeked；A.2.2 通过前不进 P2/S2/H_A2。
- **Lead 批准清单**：① 候选 R0–R4 的 H0/实现/合成校准与选择规则（primary=R4；不依赖 observed）；② R4 σ 公式、前置检查/排除比例门、F_pair 归一化；③ D2/D3 新门（coverage≥0.85、global median∈[0.5,1.5]、overall FPR≤0.10、worst-context FPR≤0.25、context-FPR p95≤0.20）与 F_crit 条件；④ null 分层/参数化 bootstrap 实现与 seed/N_perm；⑤ 预算/失败类别/两跑/schema；⑥ 仅 data-only P1 重跑、0 新 wells、不进 P2/S2/H_A2、A.1/A.2 不重判。
