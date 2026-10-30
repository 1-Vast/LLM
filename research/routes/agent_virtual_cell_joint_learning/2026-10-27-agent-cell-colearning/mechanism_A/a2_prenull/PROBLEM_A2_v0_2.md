# PROBLEM_A2_v0_2 —— R201-A.2.1：S2 因子 2 / F_self 重写 / legal 规则 / 校准重算（修正预注册）

2026-10-28。本文件修正 v0.1 A.2 预注册（[PROBLEM_A2.md](PROBLEM_A2.md) `93C7613B…`，保留不改）。依据：challenge_A2（revise，5 必改）、C192、`null_design_A2.json`、DESIGN_A_v0_2、p0p1 产物。
**只做修正预注册（不运行 P1、不读 O'Neil 响应做效应、不拟合预测）；A.2 通过前不进入 P2/S2/H_A2；A.1 negative 不重判。**

## 0. 修正摘要（对应挑战 5 必改）

| # | 挑战 | 修正 |
|---|---|---|
| 1 | **S2 因子 2**：半拆差方差=2σ_pair²，v0.1 S2 估计的是 2σ_pair² | **σ_pair²_A2 = 0.5 × mean_{plan,context} ||P⊥(f_h1−f_h2)||²/(K−1)**；与 S1/A.1 倍数写死（见 §2） |
| 2 | **F_self 恒等**：同一半拆差/S2 恒≈1，掩盖 F_pair 半尺度 | 旧 F_self **作废**；新 **F_self_check** 用与 F_pair 分子**同方差**（`d_avg=(d_A+d_B)/2`，两套协方差为零的半拆）；D2/D3 重写（§3） |
| 3 | **legal 规则与 σ 矛盾**：PROBLEM 说规则不变、DESIGN 说按新 σ 重算 | **A.2 明确重算 legal 集**：A.2 σ_obs_A2=σ_w_hat/2、阈值=1.96·σ_obs_A2；**不冻结 A.1 n_legal=110,523**；pooled/BH 用 A.2 n_legal；三处一致（§4） |
| 4 | 按修正尺度重算合成校准 | 用**校正后 σ_pair²** 重算 N0/N1/N3/N5 FPR/power；若 N0 不再 eligible 按规则重选；无合格→`design_invalid: null_calibration`（§5） |
| 5 | 预算/失败类别统一 | N1 per-cell 500 fits + N0 pooled 500 + 诊断 2,000 的预算模型；统一四个失败类别（§6） |

## 1. 不变对象（A.1 → A.2 完全保持）

- 数据：O'Neil batch1 complete-case、target30、完整 4×4 网格；**|U|=340,088** 固定。
- 统计量：`F_pair=[||P⊥(f_p−f_q)||²/(K−1)]/σ_pair²`（K=4）；per-cell `T_c=max F_pair`；pooled `#{legal pairs: F≥F_crit}/n_legal`。
- 族：S-add（role-stratified）；N_perm=500（primary）；BH q=0.05（30 细胞）；P1 阳性三条件（BH 拒绝≥5 ∧ pooled ≥ null Q95 ∧ G1–G5 + 诊断门）。
- F_crit=**2.60**（仅在 §3 自检通过时保留；不得事后改阈值/缩放 observed F）。

## 2. σ 尺度修正（唯一 S2 定义）

记单孔方差 σ_w²，R=4 技术重复，M=4 伙伴剂量列：
- full profile `f=mean(4)·mean(M)`：`Var(f)=σ_w²/16`；配对差 `d=f_p−f_q`：`Var=σ_w²/8=σ_pair²`。
- 半拆 profile `h`（2 wells×M）：`Var(h)=σ_w²/8`；`f_h1−f_h2`：`Var=σ_w²/4=2σ_pair²`。
- **S2_raw** = `mean_{plan,context}||P⊥(f_h1−f_h2)||²/(K−1)` ⇒ `E[S2_raw]=2σ_pair²`。
- **A.2 primary**：`σ_pair²_A2 = 0.5 × S2_raw`（等价：F_pair 分母用 S2_raw/2）。
- **S1（敏感性）**：`σ_w_hat=sqrt(mean((h1−h2)²))`；`σ_pair²_S1=σ_w_hat²/8`；独立性下 `E[σ_pair²_A2]=σ_pair²_S1`（预期数值 ≈**0.00107924**）。
- **A.1 frozen** `σ_pair²=0.00215849` = **2.000×** 校正后值 → A.1 的 F 尺度为一半；A.2 不缩放 A.1、不改 F_crit，必须整体重跑。
- **不得复制 A.1 的因子 2 错误**；本公式与 S1/ frozen 的倍数写入 A.2 预注册（三处一致）。

## 3. F_self 重写与 D2/D3（旧自检作废）

- **旧 F_self（作废）**：`S2_raw/S2_raw ≡ 1`（恒等式，sd≈0），无法检出 F_pair 半尺度；D2/D3 不得再用。
- **新自检 `F_self_check`（与 F_pair 分子同方差）**：用两套半拆
  `A={1,2}/{3,4}`、`B={1,3}/{2,4}`；`d_A`、`d_B` 各 `Var=2σ_pair²`，且（iid 下）`Cov(d_A,d_B)=0`；`d_avg=(d_A+d_B)/2` ⇒ `Var(d_avg)=σ_pair²`（与 `f_p−f_q` 同方差）。
  `F_self_check = [||P⊥(d_avg)||²/(K−1)] / σ_pair²_A2`。
- **D2（scale_mismatch 门）**：`F_self_check` 均值/中位 ∈ **[0.5, 2.0]**；另加 **ratio 门**：`σ_pair²_A2 / σ_pair²_S1 ∈ [0.5,2]`；任一失败 → `design_invalid: scale_mismatch`。
- **D3（noise_calibration 门）**：`F_self_check` 在 `F_crit=2.60` 下的 FPR **≤0.10**；失败 → `design_invalid: noise_calibration`。
- **F_crit 保留条件**：D2+D3 均 PASS 才保留 `F_crit=2.60`（归一化 F 下 χ²₃/3 的 95% 分位）；否则 `design_invalid: scale_mismatch`；**不缩放 observed F、不改阈值**。
- 合成校准（已执行）：新 F_self_check 的期望≈1、FPR@2.60≈名义 5%（见 `null_design_A2_v0_2.json → F_self_rewrite`）；旧 F_self sd≈0 证明恒等。

## 4. 合法 pair 规则（A.2 冻结；与 A.1 不同，写死三处一致）

- **A.2 规则**：`RMS ≤ 1.96·σ_obs_A2`，其中 `σ_obs_A2 = σ_w_hat/2`（= 行均值噪声 SD；σ_w_hat 为孔级 SD 估计）。
  数值（用 C192 的 σ_w_hat=0.092919）：`σ_obs_A2=0.0464595`，阈值 **0.0910607**（A.1 阈值为 0.06438958；A.2 因修正 σ 定义而更宽）。
- **legal 集与 n_legal 重算**：A.2 用上述阈值在 |U| 内**重新计算** legal pair 集；**不冻结/不沿用 A.1 的 n_legal=110,523**；n_legal_A2 报告；门：`n_legal_A2 ≥ 5%·|U| = 17,004.4`，否则 `design_invalid: coverage`。
- **pooled/BH 口径**：pooled 分母 = n_legal_A2（逐细胞 legal 数按 A.2 规则）；BH q=0.05（30 细胞）不变；A.1 legal 集仅作描述性对照。
- **不得执行时按 observed 选择**：σ 来源/阈值公式/是否保持 A.1 legal 集均在此写死；PROBLEM/DESIGN/JSON 三处一致。

## 5. 候选 null 合成校准重算（修正尺度；不依赖 observed）

- 用**校正后 σ_pair²**（E=1 归一化）重算：N0/N1/N3/N5 的 FPR@2.60 / power；N2/N4 排除规则不变。
- 预期（与 v0.1 一致，因为 v0.1 合成 F 已用真实 σ 归一化）：N0 0.048/0.296、N1 0.054/0.289、N3 0.042/0.296、N5 0.049/0.296（N2 0.165 不 eligible；N4 0.947 invalid）。
- **若 N0 不再 eligible** → 按预注册选择规则重选（FPR∈[0.02,0.10]、非 N4、power 最高、并列 N0>N3>N2>N1>N5）；**无合格候选 → `design_invalid: null_calibration`**。
- **wrong-scale 诊断**：若错误地用 S2_raw=2σ_pair² 作 σ_pair²，observed F 减半、null（E=1 类）不变 → FPR/power 崩塌（合成诊断表见 JSON）；该诊断证明因子 2 修正必要。

## 6. 预算与失败类别（统一）

- **预算模型**（data-only、0 新 wells）：N1 per-cell bootstrap **500 次拟合**（30 细胞；估计 ≤50 s）；N0 pooled **500**（≤1 s）；候选诊断 **2,000 模拟**（N2/N3/N5 各 500 + pooled 500；≤75 s）；observed 统计 ≤60 s；总估计 **≤200 s**；caps：wall≤900 s、CPU≤2 h、内存≤8 GB；超限 → `design_invalid: compute_budget_exceeded`（不得减 N_perm/换便宜分析）。
- **失败类别统一映射**（PROBLEM/DESIGN/JSON 三处一致）：
  | 门 | 失败类别 |
  |---|---|
  | D1 σ 非退化 / D2 F_self_check / ratio / F_crit 条件 | `design_invalid: scale_mismatch` |
  | D3 半拆 FPR>0.10 | `design_invalid: noise_calibration` |
  | D4 null pooled 中位∉[0.02,0.15] / D5 null/observed T 比∉[0.2,3] | `design_invalid: null_calibration` |
  | D6 预算超限 | `design_invalid: compute_budget_exceeded` |
  | D7 G1–G5 | A.1 既有类别（coverage/identifiability/noise/leakage/family） |
- 两跑逐字节一致；结果 JSON 不含 telemetry（wall/CPU/内存写 usage）。

## 7. 边界（不变）

A.2 通过前不进入 P2/S2/H_A2；A.1 negative 不重判；阳性仅"本资源/本族/本设计下存在联合矛盾（开发性）"；阴性仅 `no_joint_contradiction`（不写"矛盾不存在"）；pair 级仅描述性；non-blind/peeked；不称生物学/机制/迁移/决策收益/新颖性；技术重复≠独立培养；不拼 ΔEMAX；0 新 wells。
