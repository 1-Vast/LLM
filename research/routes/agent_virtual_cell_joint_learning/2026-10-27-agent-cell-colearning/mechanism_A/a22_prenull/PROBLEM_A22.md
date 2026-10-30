# PROBLEM_A22 —— R201-A.2.2 异方差稳健 σ/零模型/诊断预注册（C194 后；不运行 P1）

2026-10-28。依据：C194（A.2-EXEC 执行期发现；`a2_exec/` 产物）、`report_a2_exec.md`、`a2_exec.json`、`a2_exec_diagnostics.json`、DECISION_R201_A2_EXEC、A.2 v0.2 链、challenge_A2。
**本轮只做设计/算术/合成校准（不运行 P1、不读 O'Neil 响应做效应、不拟合预测）；A.2.2 预注册草案。**

## 0. C194 复述与问题界定

A.2-EXEC（Lead 批准、data-only）在预注册 D2 门失败：**verdict=`design_invalid: scale_mismatch`，P1 未执行（P1=None）**，无 positive/negative 结论；A.1 `p0p1_negative` 仍不可解释（仅"冻结 null 下未检出"）。

| C194 事实 | 数字 |
|---|---|
| D2 失败 | F_self_check **mean 0.9700 ✅ / median 0.4153 ❌**（目标 [0.5,2]）；分位 p5 .04 / p25 .17 / p50 .42 / p75 1.00 / p95 3.61 / max 67.18 |
| σ（A.2） | σ_w_hat=0.092919；S1=0.00107924；**σ_pair²_A2=0.00110139**（=0.5×S2_raw；/S1=1.0205） |
| legal | 阈值 0.09106062；n_legal_A2=176,934 |
| 机制 | `d_avg=(d_A+d_B)/2` 代数上 = **(r1−r4)/2**；同 wells 半拆差在 context 间**强异方差**（p25 .17 vs p95 3.61）；**单一全局 σ_pair² 只能校准均值、无法校准中位/各 context** |
| 其它门 | D1/D3/D6/D7 PASS；P1 未执行 |

**A.2.2 目标**：只修 **σ 估计 / F_pair 归一化 / 零模型 / D2–D3 诊断**，使 F 尺度可校准；**不改** P1 统计量结构/族/数据/|U|=340,088/N_perm=500/BH q=0.05/阳性三条件。**不得用 A.2 observed 结果后验选择**；A.2.2 须作为新预注册整体重跑 P1。

## 1. 候选稳健 σ（预注册比较；合成校准，不读 O'Neil 响应、不看 A.2 observed）

| id | σ 方案 | H0 | 可交换性/假设 | 实现 | 合成诊断（coverage / FPR / worst-context FPR / power） |
|---|---|---|---|---|---|
| **R0** 全局均值（A.2 基线） | 0.5×mean 全 plan/context `||P⊥d_A||²/(K−1)` | shared f + iid 噪声 | 同方差（异方差下失效） | 全局单一尺度 | coverage **0.500** / FPR 0.0723 / worst **0.682** / power 0.129 |
| **R1** per-context | `σ²(c)=0.5×mean_plans ||P⊥d_A||²/(K−1)`；F_pair 用共享 context 的 σ²(c) | shared f；context 内 iid；异方差允许 | 逐 context 标准化；context 内 plan 可交换 | 半拆 A 估计逐 context 尺度 | coverage **0.917** / FPR 0.0739 / worst **0.424** / power 0.171 |
| **R2** 稳健全局（中位/截尾） | median 或 20% trimmed mean over contexts of σ²(c) | shared f；稳健位置 | 稳健位置；非 per-context 校准 | 全局稳健尺度 | coverage 0.604 / FPR 0.121–0.122 / worst 0.803 / power 0.129 |
| **R4** fuller-profile resampling（**primary**） | per-context `σ²(c)` 由同 context **full-profile plan-pair 差**估计（`mean_pairs ||P⊥(f_a−f_b)||²/(K−1)`）；F_pair 用共享 context σ²(c) | shared f；plan-pair 可交换（H0 下 pair 差=纯噪声） | 同 context plan 对；H0 下 full-profile 差无偏 | 用全部 plan 对估尺度（比 half-split 用更多信息） | **coverage 0.875 / FPR 0.0439 / worst 0.121 / power 0.183**（唯一 eligible） |
| R5/R3 变体 | 分层零/加权聚合（R4 尺度 + 分层 χ² null） | 同上 | 分层零 | 与 R4 共用尺度，null 分层 | 记为 R4 的推断实现（不另立 eligibility） |

**合成设置（预注册，不读 O'Neil 响应）**：6 cells × 8 contexts × **12 plans**、K=M=4；true σ²(c) ~ lognormal(sd=0.7) 截断 [0.02,50]（p25 .781 / p50 1.079 / p95 3.898）；H0 = shared f + context 异方差噪声；违例 = 一条 plan profile 形状偏移 2σ(c)。**选择规则（合成校准，不依赖 A.2 observed）**：eligible ⇔ per-context F_self 中位 coverage∈[0.5,2] ≥**0.85**（48 contexts 二项容差）∧ overall FPR@2.60∈[0.02,0.10] ∧ worst-context FPR≤0.25 ∧ context-FPR p95≤0.20；eligible 中取 power 最高；并列优先级 R1>R2med>R2trim>R4>R0；无 eligible → `design_invalid: null_calibration`。
**选择结果：primary = R4_full_profile**（唯一 eligible；coverage .875、FPR .0439、worst .121、p95 .076、power .183）；R1 虽 coverage .917，但 worst-context FPR .424 超门；R0（A.2 基线）coverage .500 复现异方差失效；R2 稳健全局仍 coverage .604（稳健位置不能替代逐 context 校准）。

## 2. D2/D3 重设计（替代 A.2 全局中位门；不用 observed 后验选择）

- **D2（scale/heteroscedasticity 门）**：① **per-context F_self_check 中位 coverage∈[0.5,2] ≥0.85**；② **全局 F_self_check 中位∈[0.5,1.5]**；③ **overall F_self_check FPR@F_crit≤0.10**；④ ratio 门：`σ²_R4(c)/median_c σ²_R4(c)` 的 p95/p05 有限且覆盖合理（仅诊断报告，不做硬闸）。失败 → `design_invalid: scale_mismatch`。
- **D3（noise_calibration 门）**：① overall FPR@F_crit≤0.10；② **worst-context FPR≤0.25**；③ **context-FPR p95≤0.20**。失败 → `design_invalid: noise_calibration`。
- **F_crit 保留条件**：D2+D3 全 PASS 才保留 **F_crit=2.60**（R4 标准化后 F~χ²₃/3）；否则 `design_invalid: scale_mismatch`；**不缩放 observed F、不改阈值**。
- **F_pair 归一化**：`F_pair = [||P⊥(f_p−f_q)||²/(K−1)] / σ²_R4(shared context)`（同一共享 context 用同一 σ）；pooled 与 per-cell 同用该归一化；**不再用全局单一 σ**。
- **零模型**：pooled = 分层/标准化 χ²₃/3（按 legal pair 的 context 尺度）；per-cell `T_c` = 参数化 bootstrap（拟合 shared f + 每 plan g，按 **context-specific σ²_R4(c)** 生成噪声，重算 F/T_c）；N_perm=500（seed=20261029）。

## 3. A.2.2 执行设计要点（完整见 DESIGN_A22.md）

- **不变**：数据/O'Neil batch1 complete-case/target30/完整 4×4、**|U|=340,088**、A.2 legal 规则（全局 σ_obs_A2、阈值 0.0910607；**本轮不改 legal 规则**，仅重算 n_legal_A2 并保持 ≥17,004.4 门）、S-add 族、F_pair/T_c/pooled 结构、**N_perm=500**、BH q=0.05、P1 阳性三条件（BH 拒绝≥5 ∧ pooled ≥ null Q95 ∧ D1–D7 PASS）。
- **仅改**：σ_pair² 用 **R4 per-context 尺度**；F_pair 归一化用共享 context σ²_R4(c)；null 分层/参数化 bootstrap（context 异方差）；**D2/D3 重设计**（per-context coverage + context-FPR 门）。
- **诊断门顺序**：D1 σ 非退化（所有 context σ² 有限/正）→ D2 → D3 → D4 null pooled 中位∈[0.02,0.15] → D5 median(T_null)/median(T_obs)∈[0.2,3] → D6 预算 → D7 G1–G5；任一失败 → 对应 `design_invalid`，不进入 P1 判定。
- **预算**：data-only、**0 新 wells**；wall≤900 s、CPU≤2 h、内存≤8 GB；N1 per-cell 500 fits + N0 pooled 500 + 候选诊断 1,500（总计≈2,500）；超限→`design_invalid: compute_budget_exceeded`（不减 N_perm）。
- **两跑逐字节一致**；结果 JSON 无 telemetry；失败类别统一：`scale_mismatch`（D1/D2/F_crit）、`noise_calibration`（D3）、`null_calibration`（D4/D5）、`compute_budget_exceeded`（D6）、A.1/A.2 既有类别（coverage/identifiability/leakage/family）。
- **解释边界**：阳性仅"本资源/本族/本设计下存在联合矛盾（开发性）"；阴性仅 `no_joint_contradiction`；pair 级仅描述性；不称生物学/机制/迁移/决策收益/新颖性；non-blind/peeked；**A.2.2 通过前不进入 P2/S2/H_A2；A.1 negative 不重判**。

## 4. 边界（写死）

- A.2.2 是**新预注册**；A.2 的 `design_invalid: scale_mismatch` 与 A.1 `p0p1_negative` 均保持原样、不重判。
- 未运行 P1、未读 O'Neil 响应做效应；合成校准只用于选 scheme/校准 D2/D3（机制已知、无 O'Neil 响应）。
- 未执行 P2/S1/S2/H_A2；无新测量/新 wells；不称新颖性/生物学/机制/迁移/决策收益；技术重复≠独立培养；不拼 ΔEMAX；non-blind/peeked。
