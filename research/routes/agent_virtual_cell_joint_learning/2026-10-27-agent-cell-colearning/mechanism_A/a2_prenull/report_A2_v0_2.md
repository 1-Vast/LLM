# R201-A.2.1 报告：S2 因子 2 修正 / F_self 重写 / legal 规则 / 校准重算（修正预注册）

2026-10-28。角色：独立审计/设计修订员（未参与 R197/R200 模型开发）。任务 task-120（A.2.1）。
**只做修正预注册：未运行 P1、未读 O'Neil 响应做效应、未拟合预测；A.1 negative 不重判；A.2 通过前不进 P2/S2/H_A2；non-blind/peeked；0 新 wells。**
- 修正问题定义：[PROBLEM_A2_v0_2.md](PROBLEM_A2_v0_2.md)（`3B49A8AB…F1F16104`）
- 修正执行设计：[DESIGN_A2_v0_2.md](DESIGN_A2_v0_2.md)（`3AB5A663…2CF3142E`）
- 算术/合成校准：[null_design_A2_v0_2.py](null_design_A2_v0_2.py)（`AC4DE4C7…8BD721`）→ [null_design_A2_v0_2.json](null_design_A2_v0_2.json)（`96AE014D…76A24E5`）
- 记录/用量：[record_A2_v0_2.md](record_A2_v0_2.md)、[usage_A2_v0_2.json](usage_A2_v0_2.json)
- 依据：challenge_A2（revise，5 必改）、C192、A.1 P0/P1 产物、v0.1 A.2 预注册（未改：PROBLEM_A2/DESIGN_A2/null_design_A2 及其 SHA 保持不变）。

## 0. 5 必改落实（判定：可提交 Lead 批准 A.2 data-only P1 重跑）

| # | 挑战 | v0.2 落实 |
|---|---|---|
| 1 | **S2 因子 2** | **σ_pair²_A2 = 0.5 × mean||P⊥(f_h1−f_h2)||²/(K−1)**；推导：Var(full)=0.00053962、σ_pair²=0.00107924、Var(half diff)=0.00215849=**2×**；正后值=**0.00107924=S1**；A.1 frozen 0.00215849=2.000×；v0.1 A.2 的 S2 确实是 A.1 错误换名，已修 |
| 2 | **F_self 恒等** | 旧 F_self（同一半拆差/S2）**作废**（实测 mean=1.0、sd=0，恒等）；新 **F_self_check** 用两套协方差为零的半拆 `A={1,2}/{3,4}`、`B={1,3}/{2,4}`，`d_avg=(d_A+d_B)/2`（Var=σ_pair²，与 F_pair 分子同方差）；实测 **mean 1.0053、median 0.8001、FPR@2.60=0.0490**（≤0.10）；D2/D3 重写，另加 ratio 门 `σ_pair²_A2/σ_pair²_S1∈[0.5,2]` |
| 3 | **legal 规则与 σ 矛盾** | **A.2 冻结**：`RMS ≤ 1.96·σ_obs_A2`，`σ_obs_A2=σ_w_hat/2`（行均值噪声 SD）=**0.0464595**，阈值 **0.0910607**（A.1 为 0.06438958）；**A.2 重算 legal 集，不冻结 A.1 n_legal=110,523**；门 `n_legal_A2 ≥ 5%·|U|=17,004.4` 否则 `design_invalid: coverage`；pooled 分母=n_legal_A2、BH q=0.05 不变；PROBLEM/DESIGN/JSON 三处一致 |
| 4 | **按修正尺度重算合成校准** | 校正尺度后：**N0 0.0483/0.2956**、**N1 0.0578/0.2889**、**N3 0.0420/0.2956**、**N5 0.0475/0.2956**（均 eligible）；N2 0.1652/0.1933（不 eligible）；N4 0.9474/0（invalid 对照）；**primary null 仍=N0**（规则未变：FPR∈[0.02,0.10]、非 N4、power 最高、并列 N0>N3>N2>N1>N5）；无合格→`design_invalid: null_calibration`；**wrong-scale 诊断**：若用 S2_raw 作 σ_pair²，observed F 减半 → FPR/power 崩塌（证明因子 2 修正必要） |
| 5 | **预算/失败类别统一** | 预算：N1 per-cell **500 fits**（≤50 s）+ N0 pooled **500**（≤1 s）+ 诊断 **2,000 模拟**（N2/N3/N5 各 500 + pooled 500；≤75 s）+ observed（≤60 s）≈**186 s**；caps wall≤900 s/CPU≤2 h/内存≤8 GB；两跑逐字节；统一失败类别：`scale_mismatch`（D1/D2/ratio/F_crit）、`noise_calibration`（D3）、`null_calibration`（D4/D5）、`compute_budget_exceeded`（D6）——PROBLEM/DESIGN/JSON 一致 |

## 1. S2 因子 2 的推导与数值（可复核）

记单孔方差 σ_w²，R=4 技术重复，M=4 伙伴剂量列：
- `Var(full profile f)=σ_w²/(4·4)=0.00053962`；配对差 `f_p−f_q`：`Var=σ_w²/8=0.00107924=σ_pair²`。
- 半拆 profile（2 wells×M）：`Var(h)=σ_w²/8=0.00107924`；`f_h1−f_h2`：`Var=σ_w²/4=0.00215849=**2σ_pair²**`。
- **S2_raw=mean||P⊥(f_h1−f_h2)||²/(K−1)** → E=2σ_pair²；**正确 σ_pair²_A2=0.5·S2_raw**=0.00107924（=S1）。
- **A.1 frozen σ_pair²=0.00215849=2.000×** 校正值；A.1 的 F 尺度为一半。v0.1 A.2 的 S2 公式正是 A.1 错误换名 → 若不修，A.2 的 observed F_pair 期望=0.5、F_crit/FPR/功效全偏。

## 2. F_self 重写（旧恒等自检作废）

- **旧 F_self**（分子=同一半拆差，分母=S2）按定义恒等于 1（实测 mean=1.000000、sd=0），**无法检出 F_pair 半尺度**；A.1 的 F_self 中位 0.4579 也是被该恒等式掩盖的产物；已从 D2/D3 移除。
- **新 F_self_check**：两套半拆 A={1,2}/{3,4}、B={1,3}/{2,4}；iid 下 `Cov(d_A,d_B)=0`（代数：共享孔系数乘积和为 0），`d_avg=(d_A+d_B)/2` 的 `Var=σ_pair²`（与 F_pair 分子 `f_p−f_q` 同方差）；`F_self_check=[||P⊥d_avg||²/(K−1)]/σ_pair²_A2`。
- 合成实测（seed 20261030，4000 plans，**独立半拆理想化**）：**mean 1.0053、median 0.8001、FPR@2.60=0.0490** → 通过 D2（[0.5,2]）/D3（≤0.10）。
- **D2/D3 门（A.2 执行期）**：D2 = F_self_check 均值/中位∈[0.5,2] 且 ratio `σ_pair²_A2/σ_pair²_S1∈[0.5,2]`，失败 `design_invalid: scale_mismatch`；D3 = F_self_check FPR@2.60≤0.10，失败 `design_invalid: noise_calibration`；两者通过后才保留 **F_crit=2.60**，否则 `design_invalid: scale_mismatch`（不缩放 observed F、不改阈值）。

## 3. legal pair 规则（A.2 冻结）

- **A.2 规则**：`RMS ≤ 1.96·σ_obs_A2`，`σ_obs_A2=σ_w_hat/2`（行均值噪声 SD；σ_w_hat=0.092919）→ σ_obs_A2=0.0464595、阈值 **0.0910607**（A.1 为 1.96·0.065704/2=0.06438958）。
- **legal 集重算**：A.2 用该阈值在 |U|=340,088 内重新计算；**不冻结/不沿用 A.1 n_legal=110,523**；报告 n_legal_A2；门 **n_legal_A2≥5%·|U|=17,004.4**，否则 `design_invalid: coverage`。
- **pooled/BH 口径**：pooled 分母=n_legal_A2（逐细胞 legal 数按 A.2 规则）；BH q=0.05（30 细胞）不变；A.1 legal 集仅描述性对照；不得执行时按 observed 选择。

## 4. 修正尺度后的合成校准（不依赖 observed）

| 候选 | H0 简要 | FPR@2.60 | power | eligible |
|---|---|---|---|---|
| **N0 χ² 校准** | shared f + iid 噪声；χ²₃/3 | **0.0483** | **0.2956** | ✅ |
| **N1 参数化 bootstrap** | 拟合 shared f+每计划 g，重模拟 | 0.0578 | 0.2889 | ✅ |
| N2 残差置换 | 加性拟合后残差可交换 | 0.1652 | 0.1933 | ❌ |
| **N3 dose-split 交叉拟合** | 半剂量 profile 差估尺度 | 0.0420 | 0.2956 | ✅ |
| N4 dose-label 置换 | 与 shared-f H0 相悖（invalid 对照） | 0.9474 | 0.0000 | ❌ |
| **N5 技术半拆层** | 半拆独立；F_self 校准 | 0.0475 | 0.2956 | ✅ |

**选择规则（同 v0.1，预注册）**：FPR∈[0.02,0.10]、非 N4、power 最高、并列 N0>N3>N2>N1>N5 → **primary null=N0**（若重算后 N0 不再 eligible 按规则重选；无合格→`design_invalid: null_calibration`）。per-cell T_c 用 **N1 bootstrap**（保留共享 profile 相关性）。**wrong-scale 诊断**：若 σ_pair² 误用 S2_raw（2×），observed F 减半 → FPR/power 向 0 崩塌（JSON `wrong_scale_diagnostic`）。

## 5. 预算与失败类别（统一）

- **预算模型**（data-only、0 新 wells）：N1 per-cell 500 fits（≤50 s）；N0 pooled 500（≤1 s）；诊断 2,000 模拟（N2/N3/N5 各 500 + pooled 500；≤75 s）；observed 统计（≤60 s）；总估计 **186 s**；caps **wall≤900 s、CPU≤2 h、内存≤8 GB**；超限→`design_invalid: compute_budget_exceeded`（不得减 N_perm/换便宜分析）；两跑逐字节一致；结果 JSON 无 telemetry。
- **失败类别映射（PROBLEM/DESIGN/JSON 三处一致）**：
  - D1（σ 非退化）/ D2（F_self_check + ratio）/ F_crit 条件 → `design_invalid: scale_mismatch`
  - D3（半拆 FPR>0.10）→ `design_invalid: noise_calibration`
  - D4（null pooled 中位∉[0.02,0.15]）/ D5（null/observed T 比∉[0.2,3]）→ `design_invalid: null_calibration`
  - D6（wall/CPU/内存超限）→ `design_invalid: compute_budget_exceeded`
  - D7（G1–G5）→ A.1 既有类别

## 6. 边界与解释

- A.2 是**新预注册**；A.1 `p0p1_negative` 原样保留、不重判；不得用 A.1 结果改 null/σ/阈值；不得用 A.2 observed 选 null/legal 规则。
- 阳性仅"本资源/本族/本设计下存在联合矛盾（开发性）"；阴性仅 `no_joint_contradiction`（不写"矛盾不存在"）；pair 级仅描述性；不称生物学/机制/迁移/决策收益/新颖性；non-blind/peeked；技术重复≠独立培养；不拼 ΔEMAX。
- A.2 通过前不进入 P2/S2/H_A2；仅 data-only P1 重跑、0 新 wells。

## 7. 产物与确定性

| 文件 | SHA256 |
|---|---|
| `PROBLEM_A2_v0_2.md` | `3B49A8ABA7FBA903C1C88CBE75318E55F5C3045512A058E4FF54AA5EF1F16104` |
| `DESIGN_A2_v0_2.md` | `3AB5A663AD485579A42B0C3BB09096D756CBD6F123A93815A7FC91EA2CF3142E` |
| `null_design_A2_v0_2.py` | `AC4DE4C7F1859E35E4BDFA49B428F1C2319390E611D822DF622FEF4AA58BD721` |
| `null_design_A2_v0_2.json` | `96AE014DA6B8E9E5CA7AF359CC3DAA0D683FE8F865655A468167AC16176A24E5` |
| report/record/usage | 见 `usage_A2_v0_2.json` |
| v0.1 A.2（未改） | PROBLEM_A2 `93C7613B…`、DESIGN_A2 `6BB3460E…`、null_design_A2.py `BD281F12…`、null_design_A2.json `7BCBA58D…` |

**确定性**：同脚本两跑 `null_design_A2_v0_2.json` 逐字节一致（SHA `96AE014D…76A24E5`；wall 各 0.2 s）；JSON 键排序/无时间戳/allow_nan=False；输入 SHA 写入 JSON。

## 8. 建议

1. **提交 A.2.1 修正预注册（PROBLEM/DESIGN/null_design v0.2）做轻量复核/再挑战**；通过后请 Lead **批准 A.2 data-only P1 重跑**（0 新 wells；不进 P2/S2/H_A2）。
2. 复核重点：S2=0.5× 与预期 0.00107924；F_self_check 与 D2/D3/ratio 门；legal 规则（σ_obs_A2/阈值/重算 n_legal/≥5%U/pooled-BH口径）；修正尺度后的 N0/N1/N3/N5 校准与 primary=N0；预算 186 s 与失败类别统一；两跑/schema。
3. A.2 执行前不解释 A.1 negative；**不写"矛盾不存在/机制/迁移/决策收益"**。
