# DESIGN_A2 —— R201-A.2 执行设计（零模型/σ 尺度修正；新预注册；本轮不执行）

2026-10-28。依据：`PROBLEM_A2.md`（C192 后问题界定）、`null_design_A2.json`（候选 null 合成校准、σ 算术、选择规则）、C192（A-P0P1 执行期发现）、`DESIGN_A_v0_2.md`、`DECISION_R201_A_P0P1.md`。
**状态：预注册草案（未执行）。A.2 须先经独立挑战 + Lead 批准后才可运行；不得用 A.1 结果事后换 null/σ。**

## 0. 范围与原则

- **只修 null 与 σ 归一化**；数据、P1 统计量、族、目标宇宙、N_perm、BH q、阳性三条件全部保持 A.1 冻结定义。
- **A.2 是新的整体预注册**（新 SHA），不是对 A.1 的补丁：A.1 的 `p0p1_negative` 保持原样、不重判；A.2 重跑 P1 并独立判定。
- data-only、0 新 wells；non-blind/peeked 继承 ON3；不称生物学/机制/迁移/决策收益/新颖性。
- A.2 通过前不得进入 P2/S2/H_A2。

## 1. 不变对象（与 A.1 完全一致）

| 项 | 冻结值 |
|---|---|
| 数据/人群 | O'Neil batch1 complete-case、target30、完整 4×4 网格；702/315 pair-cell 排除 |
| 计划对宇宙 | **|U|=340,088**（同 A.1） |
| 单独合法规则 | 加性残差 RMS ≤ 1.96·σ_obs/2（σ_obs 定义见 §2；改用 A.2 σ 方案后按新 σ 重算阈值属 A.2 的一部分，不沿用 A.1 数值） |
| 统计量 | `F_pair=[||P⊥(f_p−f_q)||²/(K−1)]/σ_pair²`（K=4）；per-cell `T_c=max F_pair`；pooled `#{legal pairs: F≥F_crit}/n_legal` |
| 族 | S-add（role-stratified） |
| F_crit | **2.60**（F_{0.95,3,∞}；仅在 §2 归一化门通过时保留） |
| N_perm | **500**（primary null；另 2–4 个候选 null 各 500 作校准比较，计入预算） |
| 多重性 | BH q=0.05（30 细胞） |
| P1 阳性 | BH 拒绝≥5 ∧ pooled ≥ null Q95 ∧ G1–G5（诊断门也须 PASS） |

## 2. σ 尺度修正（A.2 唯一改变之一）

### 2.1 公式
- 记单孔方差 σ_w²；每行 4 技术重复、plan-cell 有 M=4 个伙伴剂量列。
- `y_row=mean(4)`：Var=σ_w²/4；profile `f=row mean over M`：Var=σ_w²/(4M)=σ_w²/16；配对差 `d=f_p−f_q`：Var=σ_w²/8。
- **归一化 σ_pair² = σ_w²/8**（R=M=4）。
- **S1（独立性派生，敏感性）**：`σ_w_hat = sqrt(mean((h1−h2)²))`（技术半拆 {1,2}/{3,4}，h1,h2 各 2 孔均值；`Var(h1−h2)=σ_w²`）；`σ_pair²_S1 = σ_w_hat²/8`。
- **S2（primary；半拆层直接校准）**：对每 (plan-cell, context) 由两半矩阵得 profile `f_h1`,`f_h2`；`σ_pair²_A2 = mean_{plan,context} [ ||P⊥(f_h1−f_h2)||²/(K−1) ]`。H0 下 `E[F_self]=1`（半拆分独立时；对技术重复相关稳健），是 F_pair 分子在 H0 下的直接噪声尺度。

### 2.2 A.1 诊断（预注册说明，不改 A.1）
- `σ_w_hat=0.092919` → `σ_pair²_S1=0.00107924`；A.1 冻结 `σ_pair²=0.00215849` = **2.000×S1** → A.1 的 F 尺度为归一化尺度的一半。
- A.1 `F_self` 中位 **0.4579** ≠1 → A.1 的 σ/F 归一化不一致；**必须 A.2 整体重跑**，不得事后缩放 A.1 的 F 或改 F_crit。

### 2.3 归一化门（A.2 执行期，先于 P1）
1. `σ_w_hat`、`σ_pair²_A2` 有限、>0、非退化（否则 `design_invalid: scale_mismatch`）。
2. `F_self`（用 σ_pair²_A2）均值与中位 ∈ **[0.5, 2.0]**，且 `FPR@F_crit ≤0.10`；失败 → `design_invalid: scale_mismatch`。
3. 全部门通过后，`F_crit=2.60` 按归一化 F 使用；**不重算阈值、不缩放 observed F**。
4. 主要判据用 S2；S1 仅敏感性报告。

## 3. 零模型（A.2 唯一改变之二）

### 3.1 候选（全部预注册、合成校准；选择不依赖 A.1/A.2 observed 结果）

| id | H0 | 可交换性/假设 | 实现 | 合成校准（FPR@2.60 / power） |
|---|---|---|---|---|
| **N0** χ² 校准 | shared f + iid 噪声；F 归一化 E=1 | iid；σ 正确 | 解析/模拟 χ²₃/3；pooled 用其尾概率 | **0.048 / 0.296**（eligible） |
| **N1** 参数化 bootstrap | S-add shared f + 每计划 g；iid 噪声 | 参数化；f,g 可识别 | 拟合 shared f（组内均值 profile）+ 每计划 g（列均值），重模拟 y 后重算 F | **0.054 / 0.289**（eligible） |
| **N2** 残差置换 | 每计划加性拟合后残差可交换 | 残差 iid；保持孔位 | 每 plan-cell 加性拟合，置残差后重算 F | 0.165 / 0.193（**不 eligible**：FPR>0.10） |
| **N3** dose-split 交叉拟合 | 剂量可交换仅用于噪声估计；shared f | 交叉拟合；2+2 剂量 | 半剂量 profile 差估计尺度，χ² null 按尺度缩放 | **0.042 / 0.296**（eligible） |
| **N4** dose-label 置换 | **不成立**（A.1 行置换即此类极端） | 剂量标签；**与 shared-f H0 相悖** | 置换每计划 4 个剂量位置 | 0.947 / 0.000（**invalid，仅诊断对照**） |
| **N5** 技术半拆层 | 半拆分独立；shared f | 独立半拆分 | 由 F_self 校准尺度，归一化 χ² null | **0.049 / 0.296**（eligible） |

**合成校准设置（预注册）**：5 cells × 6 groups × 6 plans、K=M=4、σ_w=0.10；违例 = 一条计划 profile 形状偏移 `2·σ_pair`（P⊥ 方向）；FPR = null F>2.60 比例；power = observed 违例 F > null Q95 比例；seed 20261030；不读 O'Neil 响应。

### 3.2 选择规则（预注册；只看合成校准，不看 A.1/A.2 结果）
1. 候选须 `FPR∈[0.02,0.10]` 且非 N4；按 power 最高；并列按优先级 **N0 > N3 > N2 > N1 > N5**。
2. **结果：primary = N0（χ² 校准）**；eligible = N0/N1/N3/N5；N2 不 eligible（FPR 0.165）；N4 无效对照。
3. **实现细化（预注册）**：per-cell `T_c` 的最大值需要计划间相关性（同 profile 被多对共享）；**N0 用于 pooled 的 pair 级 χ² 尾概率；per-cell T_c 的 null 用 N1 参数化 bootstrap**（相关结构由数据级重模拟保留）。二者均通过合成校准（N0 FPR .048/power .296；N1 .054/.289）；此细化在 A.2 预注册中写死，不属结果驱动选择。
4. 若无候选满足（合成校准下）→ `design_invalid: null_calibration`。

### 3.3 A.2 主推断程序（冻结）
1. 用 S2 估 `σ_pair²_A2`；执行 §2.3 归一化门。
2. 计算 observed `F_pair`/`T_c`/pooled（与 A.1 同公式，仅 σ_pair 换 A.2）。
3. **per-cell null**：N1 参数化 bootstrap（500 次模拟；每次拟合 shared f + 每计划 g，重模拟噪声，重算 T_c）；`p_c=(1+#{T^{(b)}≥T_c})/(1+500)`；BH q=0.05（30 细胞）。
4. **pooled null**：N0 χ²₃/3 的 pair 级 null（按 n_legal 生成 500 个 pooled 比例）；`Q95_pooled`。
5. 阳性三条件同 A.1；另需 §4 全部门 PASS。
6. 阴性 → `no_joint_contradiction`（不写"矛盾不存在"）。

## 4. 诊断门（A.2 执行期；任一失败 → 不进入 P1 判定）

| 门 | 指标 | 目标 | 失败类别 |
|---|---|---|---|
| D1 σ 非退化 | `σ_w_hat`, `σ_pair²_A2` | 有限、>0、>1e-12 | `design_invalid: scale_mismatch` |
| D2 F_self | 均值/中位（A.2 σ） | ∈[0.5,2.0] | `design_invalid: scale_mismatch` |
| D3 F_self FPR | `FPR@F_crit`（半拆自检） | ≤0.10 | `design_invalid: noise_calibration` |
| D4 null pooled | primary(null) pooled 比例中位 | ∈[0.02,0.15] | `design_invalid: null_calibration` |
| D5 null vs observed T | `median(T_null)/median(T_obs)` | ∈[0.2,3.0] | `design_invalid: null_calibration` |
| D6 预算 | wall/CPU/memory | ≤900 s/≤2 h/≤8 GB | `design_invalid: compute_budget_exceeded` |
| D7 G1–G5（A.1 定义） | 覆盖/可识别/泄漏/边界 | 全部 PASS | 既有类别 |

## 5. 预算与运行

- data-only、**0 新 wells**；N_perm：primary 500（N1 bootstrap）+ pooled N0 500 + 候选诊断 N2/N3/N5 各 500（≤2,000 置换等价）；总 ≈2,500 模拟。
- 估计：A.1 一次全量置换 ≈0.05 s（向量化）；A.2 的 N1 bootstrap 需拟合（每次 ~秒级），预估 wall 3–10 min；**cap: wall≤900 s、CPU≤2 h、内存≤8 GB**；超限 → `design_invalid: compute_budget_exceeded`（不得减 N_perm/换便宜分析）。
- **两跑逐字节一致**；结果 JSON 不含 telemetry（wall/CPU/内存写 usage）；schema 沿用 A.1 + A.2 诊断门字段。
- 失败类别：`design_invalid: null_calibration` / `scale_mismatch` / `compute_budget_exceeded`（+ A.1 既有类别）。
- A.2 结果解释边界：阳性仅"本资源/本族/本设计下存在联合矛盾（开发性）"；阴性仅 `no_joint_contradiction`；pair 级仅描述性；non-blind/peeked；不称生物学/机制/迁移/决策收益/新颖性。

## 6. 批准清单（建议 Lead/挑战者核对）

1. A.2 只改 null/σ，不改数据/U/统计量/族/F_crit（条件性）/N_perm/BH/阳性规则 —— 核对 §1 vs A.1 设计。
2. σ S2 公式与归一化门（§2）可执行、可复算；A.1 诊断数字（ratio 2.000、F_self 0.4579）一致。
3. 候选 null 的合成校准与选择规则（§3）不依赖 A.1/A.2 observed 结果；primary=N0 + per-cell N1 的实现细化已写死。
4. 诊断门 D1–D7 与失败类别可判定；预算 data-only 0 新 wells、caps 明确。
5. A.2 通过前不进入 P2/S2/H_A2；解释边界与 A.1 一致。
