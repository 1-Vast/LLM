# R196 v2 报告：C130 冻结结论的审计级可靠性重估（AMENDMENT-001 + 002；**待 task-32 挑战**）

**日期**：2026-10-27 · **角色**：独立 runner（未参与 C130/R163 开发）· **任务**：task-20 → v2 重跑
**协议**：`AMENDMENT_R196.md`（PREGISTERED AMENDMENT-001，SHA256 `6986b008ca799c3456076a630e92a04912bd3ea389ede3f83734a5607e855289`）+ `AMENDMENT_R196_002.md`（PREGISTERED AMENDMENT-002，verdict 规则补充）
**脚本**：`r196_v2.py`（SHA256 `3e4bae43cec54cb06da95774c4c78a762885f757b415c734078c2ac9743c4e17`）；**运行产物**：`r196_v2.json`（SHA256 `bd0ada7be102df430209422995609c1411cbcb6a231f763e6f96121cb4b952a4`）、`r196_v2_rows.csv`（SHA256 `576fb1550862b0dc862bd6fc94ce55353ab23189aab84e0fb29f69e9275aea84`）
**状态**：🟡 **结果解释状态 = 待 task-32（i003-challenger）独立挑战；本报告只按预注册规则给出机械 verdict 与数字，不做结论性解释、不写入 SYNTHESIS。**

---

## 0. 机械 verdict（按 AMENDMENT-002 §D）

> **`inconclusive`**
> 子类型：`design_check_failed`（E7：MDE80_design=0.0823 > δ_min=0.05）、`primary_mde80_gt_delta_min`（主 MDE80_drug=0.0857 > 0.05）、**`e9_wall_gt_900s`（AMENDMENT-002 §B：wall=1119.7 s > 900 s）**。
>
> 点估计 **+0.1415**；**主 CI（held-out 药物，drug-cluster bootstrap 95%）= [0.0625, 0.1826]**；主 MDE80（drug）= **0.0857**；partition 级 95% t-CI = [0.1238, 0.1591]（下界>0）；fold 级 t-CI（formal sensitivity）= [0.1177, 0.1652]。

**含义（仅机械）**：方向为正且四个聚类口径的 CI 下界均 >0，但**在主推断单位（held-out 药物）上 MDE80=0.0857 超过预注册最小可分辨效应 0.05** → 按预注册规则不可判 replicated；且 E7 设计门与 E9 预算门均不通过 → `inconclusive`。**不是阴性结论，也不是"C130 被推翻"**（见 §7 措辞限制）。

---

## 1. 本次重跑相对 v1 的修正（对应挑战 5 条必改）

| # | 挑战必改 | v2 落地 |
|---|---|---|
| ① | 主推断单位 = held-out 药物 | 10 个独立药物划分 × 5 折 = 50 折级增益；主 CI=**drug-cluster bootstrap**（双侧药物重抽）；主 MDE80 = 2.802×SD(drug bootstrap)；`replicated` 要求主 MDE80≤δ_min。细胞/药对/双向/partition 全部只作敏感性（AMENDMENT-001 §4） |
| ② | ≥10 个独立药物划分；fold dispersion 升为正式 sensitivity | 10 划分（种子 `20261027+100·p`，p=0..9）× 5 折；partition 级 CI 与 leave-one-partition-out 全报；50 折 t-CI 作 formal sensitivity（AMENDMENT-002 §A 另把 partition CI 下界>0 加入 replicated 合取） |
| ③ | 统一内层 λ 指标；row-level C130 网格桥接 | grouped 与 row-level 均用**折均 Spearman**（3 内层折）；row-level 变体：扩展网格 + **C130 原网格 ≤1000** 桥接；grouped 也加 C130 网格对称桥接；H196b 同网格比较（AMENDMENT-001 §3） |
| ④ | δ_min/稳定带 operational 化并与 drug 单位 MDE 联动 | δ_min=0.05 operational 定义（ρ=0.05 ⇔ Kendall τ≈0.0318 ⇔ ~1.59 pp 排序概率提升，近似）；`replicated` 要求主 MDE80≤δ_min；**取消稳定带上界**，>0.20 只记 `large_gain_flag`（AMENDMENT-001 §5） |
| ⑤ | 措辞模板 + 披露 + 可比性 | 本报告 §7 固定句式；peek 更正见 §6；C130 CI 明确声明**不是参照区间**；数据/端点/特征同构但切分/λ/内层口径不同 |

## 2. 执行与设计

- **数据**：Jaaks Original fitted（SHA256 `1188968c…`，与 C130 一致）；`SYNERGY_DELTA_EMAX` 按 `(cell, anchor + " + " + library)` 均值聚合 → **108,259 单元 / 125 细胞 / 65 药 / 2,025 有向药对**。
- **特征**：身份 130 维两侧 one-hot；注释 38 维双侧通路 one-hot（17 anchor + 21 library 水平）。
- **外层**：10 个独立药物划分（65 药均分 5 折，13 药/折）；测试=两药均在 held；训练=两药均不在 held；one-seen 排除。每 (划分,折) 测试行见 `r196_v2.json→partitions`（**每折 1,791–7,476 行，全部 ≥ 预注册的 300**；每折覆盖 122–125 细胞）；**50 折合计测试行 201,576**；pooled 覆盖 125 细胞；每折训练药 52。
- **内层 λ**：3 个药物分组内层折（both-unseen 内层验证，scaler 折内拟合）；指标=折均 Spearman；网格 `L_EXT`(11) 与 `L_C130`(9)。
- **运行**：单命令 **wall = 1,119.7 s（18.66 min）**（脚本 stdout `DONE wall=1119.7s`），CPU：run-1 进程在 18:29:07 最后一次读到 **CPU 累计 4,184.94 s**（当时 wall 仅约 660 s——BLAS 多线程使 CPU 时间远高于 wall），进程退出后未能再读最终 CPU，故最终 CPU 记 `null`；E9 按冻结规则以 wall 为准。。**超过 E9 冻结预算 900 s → E9 不通过 → verdict 必须 `inconclusive`（AMENDMENT-002 §B）**。
- **确定性**：运行 1 产物保留 `tmp/r196_v2_run1.json`（SHA256 `bd0ada7be102df430209422995609c1411cbcb6a231f763e6f96121cb4b952a4`）；同脚本二次完整运行用于确定性校验（见 §5）。

## 3. 结果（数字；机械登记，待挑战后再解释）

### 3.1 主臂与主推断

| 指标 | 值 |
|---|---|
| annotation 臂 per-fold mean ρ（50 折） | **0.141464** |
| identity 臂 | **0.0（显式约定；50/50 折常数）** |
| **主增益点估计 Δ = mean(50 折 gain)** | **+0.141464** |
| **主 CI（drug-cluster bootstrap，B=2,000）** | **[0.062468, 0.182579]**（boot mean 0.140743，SD 0.030592） |
| **主 MDE80（drug）= 2.802×SD** | **0.085720** |
| cell-cluster CI / MDE80 | [0.128835, 0.153969] / 0.018345 |
| pair-cluster CI / MDE80 | [0.116415, 0.163036] / 0.033827 |
| two-way cluster CI / MDE80 | [0.111766, 0.168516] / 0.040218 |
| `large_gain_flag`（>0.20，仅描述） | false |

### 3.2 partition 级（AMENDMENT-002 §A 合取条件）

per-partition 增益 = [0.145022, 0.115611, 0.174600, 0.138670, 0.125094, 0.158891, 0.154888, 0.129675, 0.099101, 0.173085]；mean **0.141464**，SD **0.024658**，**95% t-CI（df=9）[0.123826, 0.159102]（下界>0）**，min 0.099101，max 0.174600；leave-one-partition-out 均值范围见 `r196_v2.json`。→ **partition 合取条件（CI 下界>0、无符号不一致）满足**。

### 3.3 fold 级（formal sensitivity，非独立样本）

50 折：mean 0.141464，SD **0.083518**，se 0.011810，95% t-CI（df=49）**[0.117723, 0.165204]**，min **−0.032480**，max **0.301134**。按 AMENDMENT-002 §A：50 折来自 10 个共享 65 药的划分、**不能当独立样本 CI**，只作 sensitivity。

### 3.4 零模型（calibration）

| 臂 | 10 seeds 折均 ρ：mean（sd）[min,max] | 判据 |
|---|---|---|
| shuffle（药物层标签置换，完整设计） | **−0.006231**（0.046087）[−0.103960, +0.049324]；q025 −0.089544、q975 0.048069 | E6 通过（\|mean\|≤0.02 且区间含 0） |
| capacity（同维随机连续特征；partition 0） | +0.000874（0.006740）[−0.013071, +0.009211] | 校准通过 |

**E7 设计门（仅 shuffle_seed0 的 drug-cluster SD）**：boot mean 0.028179、sd 0.029360、CI [−0.027922, 0.086636]、**MDE80_design = 0.082267 > δ_min=0.05 → E7 不通过**（E7 是打分前功效门，不是对处理臂的检验；与 §3.1 主 MDE80=0.085720 是不同统计量，二者均 >δ_min）。
补充（描述性）：**annotation − capacity_seed0（partition 0）差值 = +0.139692**（0.145022 vs 0.005330）。

### 3.5 其它臂与 H196b

| 臂/对比 | 值 |
|---|---|
| annotation_only（[ANN]） | 0.139796；drug-cluster CI [0.068056, 0.186094] |
| grouped_c130_grid（grouped，λ≤1000） | 0.141261 |
| rowlevel_ext（行级内层，λ 扩展网格） | 0.141264 |
| rowlevel_c130_grid（行级内层，λ≤1000 桥接） | 0.141323 |
| **H196b（同内层指标 + 同网格）**：rowlevel_ext − grouped_ext | **−0.000199**，配对 drug-cluster CI [−0.001013, 0.000340] |
| H196b（C130 网格桥接）：rowlevel_c130 − grouped_c130 | **+0.000061**，CI [−0.000113, 0.000330] |
| material_optimism_flag（差值>0.05） | **false** |
| λ 触上限次数（50 折中） | annotation 26；grouped_c130 29；rowlevel_ext 31；rowlevel_c130 43 |

**注**：`rowlevel_c130_grid` 用折内 scaler（v2 统一口径），与 v1/C130 的**折前 scaler** 不同 → 仅为"同一 R196 外层设计 + C130 网格"的**桥接诊断**，不是 C130 复现（AMENDMENT-002 §C.4）。

## 4. 设计体检

| # | 检查 | 通过 | 证据 |
|---|---|---|---|
| E1 | 折结构/覆盖 | ✅ | 10×5；每折测试 1,791–7,476（均 ≥300）；每折细胞 122–125；50 折合计 201,576；pooled 125 细胞；训练药 52 |
| E2 | 内层药物重叠=0 / 内层验证 both-unseen | ✅ | 50 个外层折全部断言通过 |
| E3 | 内层指标统一（折均） | ✅ | grouped 与 row-level 同函数同口径 |
| E4 | λ 网格固定 | ✅ | `L_EXT`(11)/`L_C130`(9) |
| E5 | 测试标签仅打分 | ✅ | 计数 **800/800**（5 臂×50 + capacity 10×5 + shuffle 10×50）；λ 选择/拟合只看训练掩码视图 |
| E6 | 零分布校准 | ✅ | shuffle mean −0.0062 ∈ [−0.02,0.02]，区间含 0 |
| E7 | MDE 设计门（drug） | ❌ | MDE80_design=0.082267 > 0.05 |
| E8 | 引擎等价性 | ✅ | 计数式块 Gram vs 稠密实现 max abs diff **7.02e-13**（主）/ **1.97e-13**（path） |
| E9 | 单命令 ≤15 min + 确定性 | ❌ | **wall 1,119.7 s > 900 s → E9 失败**；确定性见 §5 |
| — | identity 常数性 | ✅ | partition 0 的 5/5 折实拟合验证常数；构造对全部 50 折相同（AMENDMENT-002 §C.3） |

## 5. 确定性 / 可复现

- run-1 产物：`tmp/r196_v2_run1.json`（SHA256 `bd0ada7be102df430209422995609c1411cbcb6a231f763e6f96121cb4b952a4`）、`tmp/r196_v2_rows_run1.csv`（SHA256 `576fb1550862b0dc862bd6fc94ce55353ab23189aab84e0fb29f69e9275aea84`）。
- 同脚本、同输入、同冻结协议的第二次完整运行已执行用于确定性校验；结果：同脚本、同输入、同冻结协议的第二次完整运行完成：wall = 1,078.6 s（run-1 = 1,119.7 s；两次均 > 900 s，E9 均不通过）。`r196_v2.json`（SHA256 `bd0ada7be102df430209422995609c1411cbcb6a231f763e6f96121cb4b952a4`）与 `r196_v2_rows.csv`（SHA256 `576fb1550862b0dc862bd6fc94ce55353ab23189aab84e0fb29f69e9275aea84`）在两次运行中**逐字节一致** → 确定性通过（固定种子、无时间戳、JSON 键排序）。
- 分步缓存（Lead 要求；**post-hoc 从 run-1 产物切分**，因为进程内状态无法热落盘——已在 `record_r196_v2.md` 记为运行时偏离，不改任何规则）：`tmp/r196_v2_stage_1_design_and_data.json`、`stage_2_null_models.json`、`stage_3_treatment_arms.json`、`stage_4_bootstrap_and_judgment.json`、`stage_5_runtime_and_E9.json`，SHA256 见 `tmp/r196_v2_stage_manifest.json`（`53c2f2b9c0456c3a12c010a4242f14270c44021e96db2883665d9ad171646f16`）。

## 6. 披露（必须与数字一起读）

1. **peek 更正**：v2 **不是盲验、不是独立复现**。AMENDMENT-001 冻结前，v1 已产出并已撤回的结果（annotation 0.1447、rowlevel_c130 0.1441、cell CI、**drug CI [0.0139,0.2233]、MDE80_drug=0.1527**、fold dispersion）是已知的；v2 是在已知 v1 全部结果基础上的**审计重分析**。v2 的规则/阈值/网格/划分种子来自挑战与撤回文本，但"任何响应读取前冻结"对 v2 不成立。
2. **运行预算**：wall 1,119.7 s（18.66 min）> E9 的 900 s；CPU：run-1 进程在 18:29:07 最后一次读到 **CPU 累计 4,184.94 s**（当时 wall 仅约 660 s——BLAS 多线程使 CPU 时间远高于 wall），进程退出后未能再读最终 CPU，故最终 CPU 记 `null`；E9 按冻结规则以 wall 为准。分步缓存为**post-hoc 切分**，非运行中热缓存（运行时偏离，记录在 `record_r196_v2.md`）。
3. **C130 的 CI [0.0947,0.1409] 不是本审计的参照区间**：切分（40 重叠随机 vs 10 独立划分）、λ 网格（≤1000 vs ≤10000）、内层口径（行级 vs 药物分组）均不同。row-level 变体只是同一外层设计下的桥接诊断。
4. **E7 与 §5 主 MDE80 的关系**：E7 用 shuffle_seed0（B=1,000）的 drug-cluster SD；主 MDE80 用处理臂（B=2,000）的 drug-cluster SD；两者均 >δ_min，故 `inconclusive` 有两重依据；子类型区分 `design_check_failed` 与 `primary_mde80_gt_delta_min`。
5. **近似说明**：δ_min 的 Kendall 换算 τ≈(2/π)arcsin ρ 是 bivariate-normal 近似；1.59 pp 为近似值。
6. **不改动**：v1 的 `PROTOCOL_R196.md`/`r196.py`/`r196.json`/`r196_rows.csv` 与 AMENDMENT-001 均未修改；本次只新增 v2 产物与 AMENDMENT-002。

## 7. 措辞限制（AMENDMENT-001 §7 + 002 §D）

- 本报告**不得**写：C130 被复现/独立确认/量级恢复/决策有用/机制；也不得写 C130 被推翻/注释无用；不写外部复现。
- `inconclusive` 只能写"**审计目标单位功效不足 / 设计体检未过 → 未决**"。
- 机械登记影响：R196 v2 **不进入 SYNTHESIS"成立"类**；C130 状态保持"冻结但未被外部/审计级确认"。
- **结果解释前须先通过 task-32（i003-challenger）独立挑战**。

## 8. 产物与哈希

| 文件 | SHA256 |
|---|---|
| `AMENDMENT_R196.md` | `6986b008ca799c3456076a630e92a04912bd3ea389ede3f83734a5607e855289` |
| `AMENDMENT_R196_002.md` | `fe1836bd8aa02e5399e03eb022df3e89b18d2edf2ce7d7d019650693b0c68432` |
| `r196_v2.py` | `3e4bae43cec54cb06da95774c4c78a762885f757b415c734078c2ac9743c4e17` |
| `r196_v2.json` | `bd0ada7be102df430209422995609c1411cbcb6a231f763e6f96121cb4b952a4` |
| `r196_v2_rows.csv` | `576fb1550862b0dc862bd6fc94ce55353ab23189aab84e0fb29f69e9275aea84` |
| `report_r196_v2.md` / `record_r196_v2.md` | 见 `usage_r196_v2.json` |
| run-1 保留副本 | `tmp/r196_v2_run1.json` / `tmp/r196_v2_rows_run1.csv`（`bd0ada7be102df430209422995609c1411cbcb6a231f763e6f96121cb4b952a4` / `576fb1550862b0dc862bd6fc94ce55353ab23189aab84e0fb29f69e9275aea84`） |
| 分步缓存 manifest | `tmp/r196_v2_stage_manifest.json`（`53c2f2b9c0456c3a12c010a4242f14270c44021e96db2883665d9ad171646f16`） |
