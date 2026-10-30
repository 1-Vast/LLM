# PROBLEM_A2 —— R201-A.2 零模型/σ 尺度修正预注册（C192 后；本轮不运行 P1）

2026-10-28。依据：C192（R201-A P0/P1 执行期发现；`p0p1/` 产物）、`report_a_p0p1.md`、`a_p0p1.json`、`DECISION_R201_A_P0P1.md`、`DESIGN_A_v0_2.md`、`PROBLEM_A_v0_2.md`。
**本轮只做设计/算术/合成校准（不读 O'Neil 响应做效应、不运行 P1、不拟合预测）。A.2 预注册草案；执行须另立批准 + 独立挑战。**

## 0. 问题界定（C192）

R201-A P0/P1（Lead 批准、data-only）已执行，冻结规则下 verdict = `p0p1_negative`（BH 拒绝 0/30；pooled observed 0.1537 < null Q95 0.7491；G1–G5 PASS）。但执行期发现两类**校准问题**，使该 negative **不可解释为机制 A 的阴性证据**：

| # | 发现 | 数字（C192） |
|---|---|---|
| ① | 冻结行置换零分布**严重偏高**，不对应 shared-f H0 | null pooled 中位 **0.7457** ≫ observed **0.1537**；null median T **146.31** ≫ observed median **73.4**；per-cell null Q95 97.5–264.7 |
| ② | σ 尺度不一致 | 冻结 `σ_obs=sqrt(mean((h1−h2)²)/2)=0.065704`；`σ_obs_alt=sqrt(mean((h1−h2)²))=0.092919`；冻结 `σ_pair²=0.0021585`；半拆自检 `F_self` 中位 **0.4579**（H0 期望≈1） |

**结论**：A.1 的 negative 只能写"本资源/本族/本设计（冻结零模型）下未检出"；**不能写"矛盾不存在"**；不构成机制 A 阴性证据。**A.2 只修 null 与 σ 归一化，不改 P1 统计量/阈值/族/数据**；改后须整体重跑 P1（新预注册），**不得**在 A.1 结果上事后换零模型/阈值。

## 1. 不变对象（A.1 → A.2 完全保持）

- 数据：O'Neil batch1 complete-case、target30、完整 4×4 网格；plan-pair 宇宙 **|U|=340,088**；合法 pair 规则（两计划均单独合法：加性残差 RMS ≤ 1.96·σ_obs/2）。
- 统计量：`F_pair = [||P⊥(f_p−f_q)||²/(K−1)] / σ_pair²`（K=4）；per-cell `T_c=max F_pair`；pooled `#{legal pairs: F_pair≥F_crit}/n_legal`。
- 族：S-add（role-stratified）；`F_crit=2.60`（F_{0.95,3,∞}；仅在 F 归一化到 E[F]=1 时保留）；N_perm=**500**（主 null）；BH q=0.05（30 细胞）；P1 阳性三条件不变（BH 拒绝≥5 ∧ pooled ≥ null Q95 ∧ G1–G5）。
- **变化仅限**：(a) σ_pair 估计方案（§3）；(b) 零模型（§2）；(c) 新增校准诊断门（§4）。

## 2. 候选零模型（预注册比较；**不得看 A.1 结果选**）

每个候选给出 H0 定义、可交换性/假设、实现要点、校准诊断。**选择规则在合成校准之后、看 A.1/A.2 observed 之前按预注册优先级确定**（见 §2.6）。

| id | 零模型 | H0 定义 | 可交换性/假设 | 实现要点 | 预期（合成 H0） |
|---|---|---|---|---|---|
| **N0** | **参数化 χ² 零** | 在 shared f（S-add）与已知 σ_pair 下，`F_pair ~ χ²_{K−1}/(K−1)`；`T_c` 为 legal pairs 的最大值，用 F 分布/蒙特卡洛生成 | iid 噪声；σ_pair 正确；F 归一化 E=1 | 解析/蒙特卡洛（无需重拟合 observed）；用设计参数 U/legal-pair 数生成 T_c null | null 中位 T ≈ χ² 分布 max 的期望；pooled ≈ 0.05（FPR 名义） |
| **N1** | **参数化生成零（shared-f 拟合 + 噪声模拟）** | 从观测数据拟合 S-add（共享 f、每计划 g），在 σ_pair 下生成 y，重算 F_pair/T_c | 噪声 iid；f,g 可识别；**不用标签置换** | A.2 执行期实现；每次模拟重算 profile/F | null 应与 observed 可比（同数量级），pooled≈0.05 |
| **N2** | **残差置换零** | 拟合 shared-f 后，残差在 plan-cell 内可交换；置换残差得 null F | 残差可交换（iid）；保持孔位结构 | 残差置换后重算 profile/F | pooled≈0.05；对异方差敏感→诊断 |
| **N3** | **leave-dose-out / 交叉拟合残差零** | 用 4 个成员剂量中留出/交叉的剂量估计噪声尺度与 profile 差异；null 来自交叉拟合的差异 | 剂量可交换仅用于噪声估计；profile 组合不变 | 2+2 剂量交叉拟合；两半 profile 差做 null | pooled≈0.05；方差估计略保守 |
| **N4** | **dose-label 置换（保持剂量对齐）** | 在每计划内置换 4 个成员剂量标签（profile 值集合不变，跨计划对齐破坏） | **在 shared-f H0 下不成立**（A.1 行置换即此类的极端版） | 置换 4 个 profile 位置后重算 | **null 偏高（已由 A.1 证明）→ 列为"无效对照"，不作 primary** |
| **N5** | **技术半拆分层的零** | 每计划用 {1,2}/{3,4} 两独立半估计 profile；H0 下两半差为纯噪声；F_self 分布作 null 尺度校准 | 半拆分独立；技术重复相关会破坏（需诊断） | F_self 分布/尺度估计；用于 σ 校准与 null 诊断 | F_self 中位≈1（若相关/尺度问题则 ≠1 → scale_mismatch） |

### 2.6 预注册选择规则（不依赖 A.1/A.2 结果）
1. **N4 不入 primary**（其 H0 与 shared-f 相悖，A.1 已证 null 偏高；仅作"为什么 A.1 失败"的对照）。
2. 候选 N0–N3、N5 中，用**合成数据校准模拟**（机制已知、σ 已知、不含 O'Neil 响应）评估：H0 下 FPR@F_crit=2.60、以及预注册违例下的 power（效应量固定：一条计划 profile 平移 Δ=2σ_pair，K=4）。
3. **primary null = 满足 `FPR∈[0.02,0.10]` 的候选中 power 最高者**；并列时按预注册优先级 **N0 > N3 > N2 > N1 > N5**。
4. 所有候选在 A.2 中均报告（primary 决定判定；其余为校准敏感性/诊断）；**不得**在 A.2 执行后按 observed 结果改选。
5. 若**没有**候选满足 FPR∈[0.02,0.10]（在合成校准下）→ A.2 `design_invalid: null_calibration`（不得强行选一个）。

## 3. σ 尺度修正（预注册公式；数值在 A.2 执行期计算）

- 记单孔方差 σ_w²（well-level），每行 4 技术重复，每 plan-cell M=4 个伙伴剂量列。
- `y_row=mean(4 reps)`：`Var=σ_w²/4`；profile `f=row mean over M`：`Var=σ_w²/(4·4)=σ_w²/16`；跨计划差 `d=f_p−f_q`：`Var=σ_w²/8` ⇒ **归一化 σ_pair² = σ_w²/8**（R=M=4）。
- σ_w 估计：技术半拆 `{1,2}/{3,4}`：`h1,h2` 各为 2 孔均值，`Var(h1−h2)=σ_w²` ⇒ `σ_w_hat=sqrt(mean_over_rows((h1−h2)²))`（=A.1 的 σ_obs_alt **0.092919**；A.1 冻结公式 `/2` 使其 =0.065704，对应 σ_pair²=σ_w²/4，为正确尺度的 **2 倍**）。
- **S1（独立性派生，敏感性）**：`σ_pair² = σ_w_hat²/8`。
- **S2（primary；半拆层直接校准）**：对每 (plan-cell, context) 计算两半 profile 差 `d_h=f_h1−f_h2`；`σ_pair²_A2 = mean_{ (plan,context) } [ ||P⊥d_h||²/(K−1) ]`。H0 下 `E[F_self]=E[||P⊥(d_h)||²/(K−1)]/σ_pair² = 1`（半拆分独立时；对技术重复相关稳健），这正是 F_pair 分子在 H0 下的尺度。
- **F 归一化与 F_crit**：仅当 S2 校准后 `mean/median F_self∈[0.5,2]` 且 `FPR@F_crit≤0.10` 时保留 **F_crit=2.60**；否则 `design_invalid: scale_mismatch`（**不**改阈值、不缩放 observed F）。
- **A.1 诊断算术（预注册说明，不改变 A.1）**：σ_w_hat²/8 = 0.0010793；A.1 冻结 σ_pair²=0.0021585 = 2×S1 → A.1 的 F 尺度为正确尺度的一半；F_self 中位 0.4579 与 1 不符 → A.1 必须整体重跑，不得事后改阈值。

## 4. A.2 执行设计要点（完整见 `DESIGN_A2.md`）

- **只修 null/σ**：数据、P1 统计量、族、`F_crit=2.60`（条件性）、per-cell T_c、N_perm=500、BH q=0.05、阳性三条件**不变**。
- **诊断门（A.2 执行期，先于 P1 判定）**：① `F_self` 均值/中位 ∈[0.5,2] 且 FPR@F_crit≤0.10；② 主 null 的 pooled 中位 ∈[0.02,0.15]（有效 null 下应≈FPR 名义 0.05）；③ null 中位 T / observed 中位 T ∈[0.2,3]（可比性，防 null 过度膨胀/塌缩）；④ `σ_w_hat`、`σ_pair²_A2` 有限且非退化；⑤ 技术半拆 FPR≤0.10。任一失败 → `design_invalid: null_calibration|scale_mismatch`，**不进入 P1 判定**。
- **预算**：data-only、0 新 wells；wall≤900 s、CPU≤2 h、内存≤8 GB；N_perm=500（primary）+ 候选 null 各 500（校准比较，计入总预算）；两跑逐字节一致。
- **失败类别**：`design_invalid: null_calibration`、`design_invalid: scale_mismatch`、`design_invalid: compute_budget_exceeded`（另保留 A.1 既有的 coverage/identifiability/noise/leakage/family/compute 类别）。
- **解释边界**：A.2 阳性/阴性措辞同 A.1（阳性仅"本资源/本族/本设计下存在联合矛盾（开发性）"；阴性仅 `no_joint_contradiction`，不写"矛盾不存在"）；A.2 通过前不进入 P2/S2/H_A2；不称生物学/机制/迁移/决策收益/新颖性；non-blind/peeked。
