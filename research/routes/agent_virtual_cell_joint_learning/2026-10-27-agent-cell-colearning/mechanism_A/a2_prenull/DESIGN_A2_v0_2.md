# DESIGN_A2_v0_2 —— R201-A.2.1 执行设计（S2 修正/F_self 重写/legal 规则/校准重算；不执行 P1）

2026-10-28。本文件修正 v0.1 A.2 执行设计（[DESIGN_A2.md](DESIGN_A2.md) `6BB3460E…`，保留不改）。依据：challenge_A2（revise，5 必改）、[PROBLEM_A2_v0_2.md](PROBLEM_A2_v0_2.md)、`null_design_A2_v0_2.json`、C192、A.1 产物。
**状态：修正预注册草案（未执行）。A.2 须经独立挑战 + Lead 批准后才可运行；只批准 data-only P1 重跑（0 新 wells；不进 P2/S2/H_A2）。**

## 0. 范围与原则

- **A.2 = 新整体预注册**，只修 null 与 σ 归一化；数据/|U|=340,088/统计量/族/N_perm/BH/阳性规则全部保持 A.1 定义（除 §2/§3/§4 明确修正）。
- 不缩放 A.1、不改 A.1 判定；A.1 `p0p1_negative` 原样保留、不重判。
- 不运行 P1 本任务；data-only；non-blind/peeked；不称生物学/机制/迁移/决策收益/新颖性。

## 1. 不变对象

| 项 | 冻结值 |
|---|---|
| 数据/人群 | O'Neil batch1 complete-case、target30、完整 4×4 网格；702/315 pair-cell 排除 |
| |U| | **340,088** |
| 统计量 | `F_pair=[||P⊥(f_p−f_q)||²/(K−1)]/σ_pair²`（K=4）；per-cell `T_c=max`；pooled `#(F≥F_crit)/n_legal` |
| 族 | S-add（role-stratified） |
| N_perm / BH / 阳性 | 500（primary）/ BH q=0.05（30 细胞）/ 三条件不变 |
| F_crit | **2.60**（仅在 §2 D2/D3 通过时保留） |

## 2. σ 与 F_self（修正后冻结）

- **σ_pair²_A2 = 0.5 × mean_{plan,context} ||P⊥(f_h1−f_h2)||²/(K−1)**（S2_raw 的一半；S2_raw 期望=2σ_pair²）。
- **S1（敏感性）**：`σ_w_hat=sqrt(mean((h1−h2)²))`；`σ_pair²_S1=σ_w_hat²/8`；校正后预期 ≈**0.00107924**；A.1 frozen 0.00215849 = 2×。
- **F_self_check（新；替代旧恒等式自检）**：两套半拆 `A={1,2}/{3,4}`、`B={1,3}/{2,4}`；`d_avg=(d_A+d_B)/2`（Var=σ_pair²，Cov=0 under iid）；`F_self_check=[||P⊥d_avg||²/(K−1)]/σ_pair²_A2`。
- **D1 σ 非退化**：σ_w_hat、σ_pair²_A2 有限、>0、非退化；失败 `design_invalid: scale_mismatch`。
- **D2 F_self_check**：均值/中位 ∈[0.5,2.0]；**ratio 门** `σ_pair²_A2/σ_pair²_S1∈[0.5,2]`；失败 `design_invalid: scale_mismatch`。
- **D3 半拆 FPR**：`F_self_check` 在 F_crit=2.60 下 FPR≤0.10；失败 `design_invalid: noise_calibration`。
- **F_crit 条件**：D2+D3 通过 → 保留 2.60（E[F]=1 归一化）；否则 `design_invalid: scale_mismatch`；**不缩放 observed F、不改阈值**。

## 3. 零模型（修正尺度后冻结）

- 候选：N0 χ² 校准（pooled pair 级 χ²₃/3）；N1 参数化 bootstrap（per-cell T_c，相关保留）；N3 dose-split 交叉拟合；N5 技术半拆层（敏感性）；N2 残差置换（FPR .165 不 eligible）；N4 dose-label 置换（invalid 对照）。
- **合成校准按校正尺度重算**（见 `null_design_A2_v0_2.json → candidate_calibration_corrected`）：预期 N0 0.048/0.296、N1 0.054/0.289、N3 0.042/0.296、N5 0.049/0.296；N2 .165 不 eligible；N4 .947 invalid。
- **primary null = N0**（若合成重算后 N0 不再 eligible，按预注册规则重选 N0>N3>N2>N1>N5 中合格且 power 最高者；无合格 → `design_invalid: null_calibration`）。
- **wrong-scale 诊断**：若用 S2_raw（2σ_pair²）作 σ_pair²，observed F 减半 → FPR/power 崩塌（JSON 记录）；该诊断不参与选 null，只证明修正必要。

## 4. 合法 pair 规则（A.2 冻结；三处一致）

- **公式**：`RMS ≤ 1.96·σ_obs_A2`，`σ_obs_A2 = σ_w_hat/2`（行均值噪声 SD）。数值（C192 σ_w_hat=0.092919）：σ_obs_A2=0.0464595，阈值 **0.0910607**（A.1 阈值 0.06438958）。
- **A.2 重算 legal 集**：不沿用/不冻结 A.1 n_legal=110,523；报告 n_legal_A2；门 `n_legal_A2 ≥ 5%·|U| = 17,004.4` 否则 `design_invalid: coverage`。
- **pooled/BH**：pooled 分母 = n_legal_A2；逐细胞 legal 数按 A.2 规则；BH q=0.05（30 细胞）不变；A.1 legal 集仅描述性对照。
- 不得执行时按 observed 选择；PROBLEM_A2_v0_2/DESIGN_A2_v0_2/JSON 三处必须一致。

## 5. A.2 执行流程（冻结顺序）

1. 读数据 → 建 target30 完整 4×4 plan-cells（同 A.1）→ 计算 σ_w_hat（半拆）、σ_pair²_A2、σ_pair²_S1。
2. 按 §4 规则重算 legal 集与 n_legal_A2；≥5%U 否则 coverage fail。
3. **D1–D3**：σ 非退化、F_self_check 均值/中位/ratio、F_self_check FPR@2.60；失败→scale_mismatch/noise_calibration（不进入 P1）。
4. 计算 observed F_pair/T_c/pooled（A.2 σ，legal 集 A.2）。
5. **null**：per-cell T_c 用 N1 bootstrap（500 次拟合/模拟）；pooled 用 N0 pair 级 χ²（500 模拟）；得 p_c、BH、Q95_pooled。
6. **D4/D5**：null pooled 中位∈[0.02,0.15]；median(T_null)/median(T_obs)∈[0.2,3]；失败→null_calibration。
7. **D6**：预算实测（wall/CPU/mem）与 caps 比较；失败→compute_budget_exceeded。
8. **D7**：G1–G5（A.1 定义）+ 解释边界检查。
9. P1 判定（阳性三条件，同 A.1）；阳性仅开发性存在性；阴性仅 `no_joint_contradiction`。
10. 两跑逐字节一致；JSON 无 telemetry；usage 记录实测 wall/CPU/内存。

## 6. 预算与失败类别（统一）

- **模拟/拟合数**：N1 per-cell bootstrap **500 次拟合**（30 细胞）；N0 pooled **500**；候选诊断 **2,000 模拟**（N2/N3/N5 各 500 + pooled 500）；observed 统计 1 次。总估计 ≤200 s；caps：wall≤900 s、CPU≤2 h、内存≤8 GB；超限→`design_invalid: compute_budget_exceeded`（不得减 N_perm/换便宜分析）。
- **失败类别映射（统一，三处一致）**：
  - D1/D2/ratio/F_crit 条件 → `design_invalid: scale_mismatch`
  - D3 半拆 FPR>0.10 → `design_invalid: noise_calibration`
  - D4/D5 → `design_invalid: null_calibration`
  - D6 → `design_invalid: compute_budget_exceeded`
  - D7 G1–G5 → A.1 既有类别（coverage/identifiability/noise/leakage/family）
- 两跑逐字节一致；schema 沿用 A.1 + A.2 诊断字段。

## 7. 解释边界与批准清单

- 阳性仅"本资源/本族/本设计下存在联合矛盾（开发性）"；阴性仅 `no_joint_contradiction`（不写"矛盾不存在"）；pair 级仅描述性；不称生物学/机制/迁移/决策收益/新颖性；non-blind/peeked。
- **Lead 批准清单**：① S2=0.5×，预期 σ_pair²≈0.00107924，与 S1/A.1 倍数写死；② F_self_check 新定义+D2/D3+ratio 门，旧恒等自检作废；③ legal 规则 A.2 公式/σ 来源/重算 n_legal/≥5%U 门/pooled-BH 口径写死；④ 合成校准按校正尺度重算的选择规则；⑤ 预算/失败类别统一、两跑/schema；⑥ 仅 data-only P1 重跑、0 新 wells、不进 P2/S2/H_A2。
