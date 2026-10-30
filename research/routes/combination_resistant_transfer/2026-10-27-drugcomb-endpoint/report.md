# DrugComb v1.4 端点映射、聚合规则与饱和性/可靠性审计报告（R191-PB）

2026-10-27。角色：**端点与测量体制审计员**（独立于提案者）。本报告只回答一件事：为复现冻结结论（两药都未见时粗注释替代身份、排序增益）而选定的 DrugComb 主端点是否**可用**，以及其**聚合规则、饱和性、冗余性、与项目 `ΔEMAX` 的构造可比性、MDE80/δ_min**。**本报告不评估任何效应**：未拟合 identity/annotation 模型，未做 `通路−identity` 增益估计，未做机制/靶点/临床推断。响应值的使用严格限于 [PROTOCOL_PB.md](PROTOCOL_PB.md) §1 的白名单。

- 冻结协议：[PROTOCOL_PB.md](PROTOCOL_PB.md)（运行前冻结；SHA256 `1667F89CEF91162D2A84D98690370CF90F739968545DA15F5C7A39F557882823`）
- 审计脚本：[pb.py](pb.py)（SHA256 `5170E16FD3054090E2B4DBB4A2C9441241476B882AE0D58E3548EF64D3E35276`），离线、确定性、键排序、无时间戳
- 结果：[pb.json](pb.json)（SHA256 `ED5D6C951A3477E2F9A2A2BF57C79374117559F7248E701DE4EAD33EC3AD104B`，**连续两次运行逐字节相同**）＋ 逐指标统计：[endpoint_audit.csv](endpoint_audit.csv)（SHA256 `7EAAFFCDBEBB73F7F1325E3EA3EAA6041C7C121730AC5E2EEB7504D624C8FE2E`）
- 过程/预算/[usage.json](usage.json)：[record.md](record.md)；一手文献与实现源码：[sources/](sources/)

---

## 0. 判定

**`endpoint_not_usable`**（失败类别：**`evaluation_cannot_distinguish`**）。**不是因为饱和，也不是因为构造不可比**——主端点在饱和性、聚合稳健性、与 `ΔEMAX` 的书面构造可比性三道上**全部通过**；失败在**预注册的 MDE 硬门槛**：r=0.20 both-unseen 设计（16,078 单元 / 2,671 药对）下 `MDE80(双向聚类)=0.1149 > δ_min=0.03`，且预注册升级路径 r=0.40 仍为 `0.0614 > 0.03`。按 PROTOCOL_PB §12 记录 `evaluation_cannot_distinguish`，**不换指标、不换切分救结论**。

| # | 预注册门槛（PROTOCOL_PB §12.1） | 实测 | 结果 |
|---|---|---|---|
| 1 | 主端点 `synergy_bliss` 在 block 级与 unit 级均**非饱和/无越界/无缺失** | block：无 flag；unit：无 flag；缺失 0/466,033 | **PASS** |
| 2 | 聚合稳健性 A1≥0.99、A2≥0.80 | A1（mean~median）**0.99902**；A2（mean~首块，≥2 块单元）**0.83862** | **PASS** |
| 3 | `ΔEMAX` 构造可比性书面论证完整、差异不隐藏（C1–C4 + 14 条一手引文逐字核验） | 14/14 引文 verified；C1–C5 全部成立；C5 尺度比 1.12（Original）/0.80（Validation），落在 [1/3,3] | **PASS** |
| 4 | `MDE80(双向聚类) ≤ δ_min = 0.03`（r=0.20） | **0.1149**；pair-cluster 0.1061；permutation 0.0780；pair-level 0.0759（iid 解析 0.0221 仅为参考、忽略聚类） | **FAIL** |
| 4′ | 升级路径：r=0.40 的 `MDE80 ≤ 0.03` | **0.0614** | **FAIL** |

**主端点（冻结）**：`synergy_bliss`。
**聚合规则（冻结）**：分析单元 =（`cell_line_name` 归一名，无序归一药对）；端点值 = 该单元内**全部非缺失 block 的 `synergy_bliss` 算术平均**（block≥1）。理由见 §3。

**必须随结论传递的条件**（不是否决项，但不许隐藏）：
1. **study/剂量矩阵混杂**：v1.4 **无** study/design 列；用 block_id 窗＋身份签名代理显示端点存在强异质——`η²(study proxy, 含未指派)=0.1165`、`η²(block_id 20 等分位)=0.2948`、`η²(细胞)=0.1891`；单细胞系 2×2 设计（CLOUD/KBM-7）块均值 −8.08（sd 18.42）vs 5×5（ONEIL）+1.35（8.15）vs 4×4/4×6（ALMANAC）+0.05（6.10）。阶段 2 必须披露并以分层敏感性处理。
2. **MDE 失败是设计检定力问题，不是端点质量问题**：该设计对**冻结头条量级**（+0.1183）的检定力约 **0.78**，但对预注册 δ_min=0.03 只有 **0.024**——即"能看见大效应、看不见小效应"。是否改写 δ_min 是 Lead 的协议修订决定（§9.3 列出预注册重开条件），本审计不替 Lead 决定。
3. v1.4 无 QC flag 列、无 raw 剂量层（2,008,117,325 B 未下载）→ 剂量矩阵尺寸/口径只能经 study 代理间接推断；summary 的"矩阵平均"口径由 SynergyFinder 实现核对（§7.2），**未能**由 DrugComb 门户代码核实（门户本机不可达，见 R190-E1 §10）。
4. `css` 列在被测数据里有 **9.58%** 落在其已发表构造界 [0,100] 之外（min −107.57、max 103.76）→ `css` 不算可用端点（其构造在 summary 版中与 Malyutina 2019 不一致），但这不影响主端点判定。

**边界**：本判定 ≠ 冻结结论已解冻，≠ DrugComb 不能复现，≠ 有/无效应。本报告未读任何响应值做效应估计。

---

## 1. 方法与边界

- 输入：R190-E1 冻结下载（v1.4 summary 全量 193,184,734 B；v1.5 summary 固定 60×1 MB 字节样本；v1.5 标识表）、Europe PMC 一手全文（NAR 2021 `PMC8218202`=gkab438、NAR 2019 `PMC6602441`=gkz337、Malyutina 2019 `PMC6544320`）、SynergyFinder 实现源码（`google/synergyfinderengineered` @ `64876b193d5cba140a1fee57bccf242d29d51f74`），Jaaks 2022 拟合表（**仅尺度参照**）与 Jaaks 2022 全文（方法逐字核对）。全部 bytes/SHA256 见 `pb.json → inputs`。
- 结构预跑（`tmp/pb_structure_prepass.json`，只读身份/设计列，**未读响应值**）：1,175,220 行 / 组合块 **466,033** / cell×pair 单元 **380,418** / 药对 62,826 / 药 4,088 / 细胞 112 / 块/单元均值 1.225055；≥2 块单元 36,637（9.63%）；block_id 1…466,259（组合块）无重复；浓度单位 466,033/466,033 = `uM`；**无 study 列、无浓度数值列**。both-unseen r=0.20 复算 = k=818 / **16,078 单元 / 2,671 药对**，与 R190-E1 精确一致。
- 响应值白名单复核：`pb.py` 只把 12 个响应/派生列转 float 后用于（i）分布/饱和、（ii）列语义恒等式、（iii）可靠性、（iv）测量体制描述、（v）MDE 方差估计；**没有**任何模型拟合/训练/特征选择/效应估计代码路径（`pb.json → response_value_use_attestation`；grep 复核见 record §7）。

## 2. 结构与聚合规则候选

- DrugComb 的 **block = 一次实验/一张剂量矩阵**（NAR 2019：block id 用于区分"同一组合-细胞对在多次实验中的重复"；已逐字核验）。v1.4 每个组合块一行，故 cell×pair 单元 = 一个或多个 block。
- 块数分布：1 块 343,781（90.37%）；2 块 12,803；3 块 838；**4 块 21,932**；5 块 667；6–10 块 397。→ 多块单元足够做分半可靠性（36,637 个）。
- 聚合候选（预注册考察）：**块均值（主）** / 中位数 / 最大值 / 仅单块子集 / 首块。选择依据不看响应分布：Jaaks 对重复测量做平均（§7.1 引文）；block 是"一次实验"；均值对不等块数单元给出最小方差无偏组合。
- 完全重复块（同单元且 6 指标向量全同）：**48 个多余块 / 28 个单元**（0.01%）→ 保留（它们是不同 block/实验），影响可忽略。

## 3. 主端点选择与聚合稳健性

**选择（先于数据、构造性）**：六个候选中只有 `synergy_bliss` 用**与 `ΔEMAX` 相同的期望模型**（Bliss 独立）。`synergy_zip` 是"Bliss+Loewe"的 interaction-potency 模型；`hsa`/`loewe` 是不同零模型；`S`/`css` 是**敏感性**分数而非 observed−expected 残差（§5 给出 `S` 的精确恒等式证据）。同零模型是可比性的**必要条件**，故主端点唯一确定为 `synergy_bliss`。

**聚合稳健性**（预注册 A1–A4）：

| 指标 | A1 mean~median | A2 mean~首块（≥2 块） | A3 ρ(块数, 均值) | A4 mean~max |
|---|---|---|---|---|
| `synergy_bliss`（主） | **0.99902** ✓ | **0.83862** ✓ | 0.0906（未触发 >0.10 flag） | 0.98264 |
| `synergy_zip` | 0.99922 | 0.86783 | 0.13111 ⚠ | 0.98684 |
| `synergy_hsa` | 0.99907 | 0.85774 | 0.18026 ⚠ | 0.98499 |
| `synergy_loewe` | 0.99940 | 0.89139 | 0.07652 | 0.98597 |
| `S` | 0.99935 | 0.91143 | 0.01532 | 0.98734 |
| `css` | 0.99985 | 0.95647 | 0.21408 ⚠ | 0.99570 |

A1/A2 全过（主端点 0.999/0.839 ≥ 门限）。A3 显示 `zip`/`hsa`/`css` 的单元均值随块数上升（被研究越多的药对越"阳性"），主端点 `bliss` 接近但未过 flag 线；这是**块数/研究强度混杂**的信号，阶段 2 应把"块数"作为敏感性变量。

## 4. 端点分布与饱和性（逐指标）

判据在协议 §5 冻结：S1 贴边>0.90、S2 贴边>0.20、S3 圆整边界原子>0.05、S4 sd<2.0、S5 极值原子>0.001、S6 文档域越界>0.01、S7 缺失>0.20；`saturated=∨(S1..S5)`，`metric_usable = ¬saturated ∧ ¬range_violation ∧ ¬incomplete`，block 与 unit 两级都要过。

**block 级（n=466,033，缺失 0）**

| 指标 | mean | sd | p1 | p25 | p50 | p75 | p99 | min | max | atom=0 | \|v\|≥95 | 越 ±200 | n_distinct |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| `synergy_bliss` | −0.4477 | 9.6665 | −31.07 | −3.43 | 0.10 | 3.63 | 23.25 | −90.13 | 237.22 | 0 | 0.015% | 0.0006% | 464,444 |
| `synergy_zip` | −0.9984 | 9.0793 | −28.65 | −4.20 | −0.62 | 2.63 | 22.83 | −90.13 | 237.25 | 0 | 0.014% | 0.0006% | 465,392 |
| `synergy_hsa` | 0.4432 | 8.5896 | −23.91 | −3.08 | 0.15 | 3.90 | 23.99 | −93.76 | 84.31 | 0 | 0 | 0 | 437,641 |
| `synergy_loewe` | −7.7632 | 15.4499 | −63.68 | −12.55 | −4.13 | 0.57 | 22.16 | −121.73 | 86.69 | 7.1e-5 | 0.036% | 0 | 465,576 |
| `S` | 1.0032 | 18.0803 | −52.26 | −6.58 | 1.87 | 10.33 | 44.72 | −178.81 | 224.82 | 1.5e-5 | 0.106% | 0.0006% | 166,138 |
| `css` | 31.0037 | 25.8085 | −8.49 | 9.15 | 27.48 | 49.25 | 98.74 | −107.57 | 103.76 | 2e-6 | **19.45%** | **9.58% 出界** | 174,711 |

**unit 级（cell×pair 均值，n=380,418）**：主端点 mean −0.8751 / sd 9.8398 / p1 −31.99 / p99 23.42；`S` 1.0566/17.2279；`css` 27.3717/24.7117，贴边质量 **22.11%**、越 [0,100] **10.90%**。

**判定（逐指标）**

| 指标 | block 级 | unit 级 | 结论 |
|---|---|---|---|
| `synergy_bliss` | 无 flag | 无 flag | **未饱和、可用**（主端点） |
| `synergy_zip` | 无 flag | 无 flag | 未饱和、可用 |
| `synergy_hsa` | 无 flag | 无 flag | 未饱和、可用 |
| `synergy_loewe` | 无 flag | 无 flag | 未饱和、可用 |
| `S` | 无 flag | 无 flag | 未饱和、可用（但构造不可比，见 §5/§7） |
| `css` | 无 flag（贴边 19.45% 恰低于 0.20） | **S2：贴边 22.11% > 0.20**；**S6：10.90% 越 [0,100]** | **`metric_usable=false`** |

**读法**：四个 synergy 分数与 `S` 都**没有**"90% 贴边/方差塌缩/硬钳位"的饱和问题——这是本轮最干净的结论之一（与 Lead 预探完全一致）。唯一不合格的是 `css`：它的**贴边质量**与**文档域越界**同时触发。注意：`css` 出界不是"饱和"，而是**列语义与已发表构造不一致**（Malyutina 2019 说 CSS∈[0,100]，本表 9.58% 在界外，min −107.57）——即便不作主端点，这也是测量体制的实质发现。

## 5. 语义/构造核对（列恒等式）

在 466,033 个组合块上逐行验证（全部非缺失）：

| 恒等式 | 最大绝对差 | 完全相等比例 | 结论 |
|---|---|---|---|
| `css = (css_row + css_col)/2` | **0.0** | **100%** | 精确成立 |
| `S = css − (ri_row + ri_col)` | **0.0** | **100%** | **精确成立** |
| `S = css − max(ri_row,ri_col)` | 160.15 | 0.01% | 不成立 |
| `S = css − (ri_row+ri_col)/2` | 111.86 | 0.001% | 不成立 |

**这是可比性论证的关键证据**：DrugComb summary 的 `S` 就是 Malyutina 2019 的 **`S_sum = CSS − sum(AUC₁, AUC₂)`** 变体——一个"相对单药敏感性的增益"复合分，**不是** observed−expected（Bliss/Loewe/HSA/ZIP）残差，因此与 `ΔEMAX` **不同量**，不能当主端点。`synergy_zip` 虽含 Bliss 假设，但其分数是 interaction-potency 模型参数的平均，也不是同一统计量。

**Lead 预探的逐项复核**（协议 §15）：六个块级 mean/sd 与预探**完全一致**（−0.45/9.67、−1.00/9.08、0.44/8.59、−7.76/15.45、1.00/18.08、31.0/25.8）；预探的 `bliss–zip 0.920`、`bliss–hsa 0.801` 精确复现为 **Pearson**（block 级），而预注册的**秩**冗余（Spearman）为 0.805 / 0.734（§6）——两者不矛盾，是"线性相关（受尾部/尺度驱动）vs 秩相关"之别，本报告两者都给出。

## 6. 指标冗余（C98 教训的对照）

**unit 级 Spearman /（block 级 Pearson）**：

| pair | ρ (unit, Spearman) | Pearson (unit) | Pearson (block) | 分类（相对主端点，R1） |
|---|---|---|---|---|
| bliss ~ zip | **0.785** | 0.925 | **0.920** | `partially_redundant` |
| bliss ~ hsa | **0.727** | 0.794 | **0.801** | `partially_redundant` |
| bliss ~ loewe | 0.355 | 0.342 | 0.354 | `distinct` |
| bliss ~ S | 0.607 | 0.695 | 0.669 | `distinct` |
| bliss ~ css | 0.147 | 0.195 | 0.218 | `distinct` |

- **PCA（block 级秩，6 指标）**：PC1 解释 **52.6%**、PC2 18.1% → **不构成单一主因子**（<0.80），与 C98 的"四个连续 Δ 指标 ρ=0.806–0.967 = 一个读数"不同。
- **结论**：`bliss`/`zip`/`hsa` 是同一"observed−expected 残差"家族的三种零模型，秩相关 0.73–0.79（线性 0.80–0.93）→ **部分冗余**，不可当作三个独立终点/三条独立证据；`loewe`、`S`、`css` 与主端点秩相关低（0.15–0.61），但它们**构造上更不可比**（§7），所以"低相关"不构成改选理由。
- 复现阶段只允许**一个**主端点（`synergy_bliss`）；其余 5 个只能作**预先声明的次端点**，不得在主端点失败时替换（PROTOCOL_PB §12.2；本轮已遵守）。

## 7. 与 `ΔEMAX` 的构造可比性（一手引文，全部逐字核验）

### 7.1 一手定义（引文见 `pb.json → comparability.quotes`，14/14 verified=True）

- **`ΔEMAX`（Jaaks 2022, Nature 603:594，Methods）**：*"Shifts in potency (ΔIC50) and in efficacy (ΔEmax) were calculated as the difference between the observed combination response and expected Bliss (ΔIC50 = Bliss IC50 − combination IC50, and ΔEmax = Bliss Emax − combination Emax)."*；*"Emax is reported at the highest tested concentration for the drug."*；Bliss 期望：*"every point on the Bliss dose response curve is defined as the product between the anchor viability and the corresponding point on the library dose response curve."*；重复处理：*"Drug responses were averaged across technical and biological replicates"*。
- **DrugComb 四个模型（NAR 2021 gkab438）**：*"For evaluating the drug synergy, we implement four major mathematical models including Bliss, Loewe, HSA and ZIP"*；*"the Bliss model assumes probabilistic independence when drugs are non-interactive while the Loewe model assumes that the efficacy of non-synergistic drug combinations is identical to that of a drug combined with itself"*；*"The ZIP model … can be considered as an Ensembl model as it combines the assumptions of Bliss and Loewe"*；符号：*"Drug combinations with synergy scores of zero are considered additive, while a positive synergy score suggests synergy, and a negative score suggests antagonism"*。
- **块/矩阵语义（NAR 2019 gkz337）**：*"a unique identifier, termed block id, is needed to differentiate the same drug combination—cell line pair that has been repeated in multiple experiments"*；QC 边界：*"abnormal response values, for example percentage inhibition of cell growth less than −200% or larger than 200%, were marked as poor-quality data points"*。
- **尺度（Malyutina 2019）**：CSS *"varies between 0 and 100"*；S/CSS *"utilize the same unit as the percentage of inhibition of cell viability. Therefore, the synergy score can be interpreted as the extra percentage inhibition effect beyond the expectation."*
- **实现口径（SynergyFinder @ 64876b1）**：`Bliss()` 参考矩阵 `ref.mat[i,j] = drug1.response[i] + drug2.response[j] − drug1.response[i]*drug2.response[j]/100`、`syn.mat = response.mat − ref.mat`（% 抑制尺度，正=协同）；`Plot_synergy.R` 的标题分数 = 所选矩阵区域 `mean()`，并注释 *"When dose=0 for either drug, the synergy score is also 0."*

### 7.2 可比性结论

| 条件 | 结论 | 依据 |
|---|---|---|
| **C1 同零模型** | **成立**（唯一） | `ΔEMAX` 用 Bliss 独立；六候选中只有 `synergy_bliss` 由 Bliss 独立残差构造 |
| **C2 同方向** | **成立** | 两者都是"正 = 组合优于期望" |
| **C3 可换算尺度** | **成立** | `ΔEMAX` 在 viability 分数（阈值 0.2=20%），DrugComb 协同分在 % 抑制点；×100 可换 |
| **C5 尺度一致性（描述）** | 通过 | Jaaks `ΔEMAX` sd 0.0866（Original，n=296,707）/0.1205（Validation，n=23,505）→ ×100 = 8.66/12.05；DrugComb `synergy_bliss` block sd 9.67 → 比值 **1.12 / 0.80**，落 [1/3,3] |
| **C4 差异（不隐藏）** | 已记录 | ① `ΔEMAX` 是**拟合 Emax 的效能对比（最高测试浓度）**，`synergy_bliss` 是**整张剂量矩阵逐点 Bliss 残差的平均**（混入 potency 与低剂量近零残差）→ **不是同一统计量**；② Jaaks 为 anchored 2×7 设计，DrugComb block 混 2×2…10×10 多种设计（v1.4 无设计列）；③ Jaaks 用拟合曲线参数与嵌套重复，DrugComb 用 SynergyFinder 矩阵分且 93.2% 数据点无重复（NAR 2021）；④ summary block = 一次实验/一张矩阵 |

**结论**：`synergy_bliss` 是 DrugComb summary 中**唯一**在零模型/方向/尺度上与 `ΔEMAX` 可对照的端点——但它是**部分可比（proxy）**，不是等价物。跨资源**没有**可用的实体级响应配对（细胞交集 18、药 40、单元键 241，且设计不同），因此**不作数值等价性主张**；复现若失败，`construct_mismatch` 必须作为一个候选失败类别（已写入 PROTOCOL_PB §12 / BRIEF 阶段 2）。

**旁证（不参与判定）**：Jaaks 拟合表中 `ΔEMAX = SYNERGY_EXP_EMAX − SYNERGY_OBS_EMAX` 在 296,707 行上最大残差 **0.0**（恒等式成立）；`ΔEMAX ≥ 0.2` 比例 2.32%（Original）/12.28%（Validation），即 Jaaks 所述的"少数协同"。

## 8. 可靠性/测量体制

### 8.1 块间可靠性（≥2 块单元，n=36,637）

| 指标 | ICC(1) | 平均块数 | 均值端点可靠性 | 分半 Spearman–Brown | 块内 sd 中位 |
|---|---|---|---|---|---|
| `synergy_bliss` | 0.674 | 3.34 | 0.873 | 0.784 | 2.65（p25 1.51 / p75 4.41） |
| `synergy_zip` | 0.645 | 3.34 | 0.858 | 0.765 | 2.13 |
| `synergy_hsa` | 0.711 | 3.34 | 0.891 | 0.826 | 2.55 |
| `synergy_loewe` | 0.857 | 3.34 | 0.952 | 0.887 | 2.86 |
| `S` | 0.838 | 3.34 | 0.945 | 0.895 | 4.14 |
| `css` | 0.860 | 3.34 | 0.953 | 0.914 | 4.44 |

**对照已发表复现性**（NAR 2019，逐字）：CSS 的 within-study 平均 sd **4.25（ONEIL）/12.02（ALMANAC）**，between-study **15.44**，负对照 17.5。本轮 `synergy_bliss` 的块内 sd 中位 2.65（同 study 代理 2.61 / 跨 study 代理 3.49）→ **不差于已发表 within-study 复现性**，且"cross > same"方向与文献一致（跨 study 单元仅 620 个，估计不稳，仅描述）。可靠性上限 `ρ_ceiling = sqrt(0.873) = 0.934`。

### 8.2 study / 剂量矩阵混杂（这是需要写进条件的东西）

- **v1.4 无 study 列**（R190-E1 结构缺口），本审计用两条代理：
  1. **block_id 窗**：v1.5 分块样本里每个 study 占据连续 block_id 段；用其 `[min,max]` 指派 v1.4 块（指派率 **96.20%**，窗口零重叠）。
  2. **身份签名验证**：对每个窗口数 v1.4 的 distinct 细胞数，与论文 S1 的 cell line 数比对——**5 个窗口通过**（ALMANAC 60/60、ONEIL 39/39、CLOUD 1/1、NCATS_MDR_CS 2/2、PHELAN 1/1），MATHEWS 窗（19 vs S1 的 1）判为**混合窗、排除出 design 检验**。
- **验证过的 study 端点水平差异巨大**（全部为 v1.4 实测）：

| study（代理） | 块数 | 矩阵 | mean | sd | 覆盖 vs S1 |
|---|---|---|---|---|---|
| ALMANAC | 311,549 | 4×4, 4×6 | **+0.05** | 6.10 | 1.00 |
| ONEIL | 90,596 | 5×5 | **+1.35** | 8.15 | 0.98 |
| CLOUD | 32,031 | 2×2 | **−8.08** | 18.42 | 0.80（KBM-7 单细胞系；另有 8,129 个 KBM-7 块落在未指派段） |
| NCATS_MDR_CS | 68 | 10×10 | **+21.36** | 15.04 | 1.00 |
| PHELAN | 62 | 10×10 | **+1.10** | 6.68 | 1.00 |
| 未指派段 | 17,732 | — | **−10.90** | 18.89 | block_id 91,285–100,337 段（身份签名：KBM-7 8,129 块＝CLOUD 类）＋ T98G 1,818 块（FORCINA 类）等 |

  `η²(study 代理)=0.0869`（仅指派）/ **0.1165（含未指派）**；`η²(block_id 20 等分位)=0.2948`；`η²(细胞)=0.1891`（112 个细胞块均值的 sd = 5.15 点，范围 −12.14…+33.57）。
- **矩阵尺寸检验**（5 个验证 study，描述性 n=5）：块 sd 与"实剂点数平均"预测 `1/sqrt(k)` 正相关（Pearson **+0.664**），与"零剂量边界衰减"预测 `f=k/(nr·nc)` **负**相关（Pearson **−0.538**）→ **不支持**"summary 值被结构性 0 剂量按矩阵尺寸稀释"；方向更支持"对更多真实剂量点取平均 → 方差更小"。n=5 且与生物学混杂 → **仅作描述**，不作口径断言。
- **v1.5 分块样本（4.22% 字节样本）复核**：61,872 行 / 组合 32,721 / 出现 12 个组合 study；study 级 `synergy_bliss`：FRIEDMAN sd **39.51**（3×3）、CLOUD mean **−25.25**、MATHEWS +10.66、ALMANAC +0.19 —— study 间差异同样巨大。该样本是**字节均匀而非行随机**（块按 block_id 排序），study 均值不能外推为全量；只作描述。对照：v1.5 样本 `synergy_bliss` 总 mean 0.55 / sd 24.51（与 v1.4 的 −0.45/9.67 不可直接比，study 组成不同）。

## 9. MDE80 与 δ_min

### 9.1 定义（预注册，A0/C160 同口径）

`MDE80 = (z_{0.975}+z_{0.80}) × SE = 2.801585 × SE`；统计量 = 全评估单元上 `Spearman(臂预测, 主端点)`；both-unseen 下 identity 臂预测恒为常数（两药 one-hot 全 0）⇒ ρ(identity)=0 约定，`Δρ` 的 MDE = 单臂 ρ 的 MDE。零信息预测 = 每药对 `z_p~N(0,1)` 广播到该对全部单元（预测只随药对变，C141）。bootstrap B=2,000，主设计 r=0.20（16,078 单元 / 2,671 药对 / 101 细胞）。

### 9.2 结果

| MDE80（r=0.20） | SE | MDE80 | 说明 |
|---|---|---|---|
| **双方聚类 bootstrap（预注册门槛）** | 0.0410 | **0.1149** | 药对×细胞双向重采样 |
| 药对聚类 bootstrap | 0.0379 | 0.1061 | 仅药对聚类 |
| permutation（固定 y，重抽 z） | 0.0278 | 0.0780 | 仅预测向量随机性（诊断分解） |
| 药对级 bootstrap（pair 均值） | 0.0271 | 0.0759 | 诊断分解 |
| iid 解析（参考，忽略聚类） | 0.0079 | 0.0221 | 不可用于判定 |

**各 r 的预注册 MDE80（双向聚类）**：r=0.20 → **0.1149**；r=0.30（33,148 单元/5,853 对）→ **0.0811**；r=0.40（52,368 单元/8,535 对）→ **0.0614**。全部 **> δ_min=0.03**。

**检定力校验**（固定评估单元，one-sided ρ>1.96·SE 检验）：δ=0.03 → 0.024；δ=0.05 → 0.078；δ=0.10 → 0.591；δ=MDE80(0.1149) → 0.708；**δ=0.1183（冻结头条量级）→ 0.783**。

**为什么 MDE 这么大**：both-unseen 的 2,671 个药对里 **2,397 个只有 1 个细胞**（均 6.02、最大 61），药对水平 ICC=0.765（σ²_between 95.0 / σ²_within 29.2）→ 有效独立单元远小于 16,078。这是**资源结构**的结果，不是端点噪声：iid 解析 MDE 只有 0.022，聚类后大 3.5–5 倍。

### 9.3 δ_min 与判定

预注册 **δ_min = 0.03**（= 冻结头条增益 +0.1183 的 1/4 ≈ 0.0296，向上取 0.03；与 BRIEF "0.02–0.05 量级"一致；项目先例：线 D δ_min=0.05）。**r=0.20 不满足，预注册升级路径 r=0.40 也不满足 → `endpoint_not_usable`（`evaluation_cannot_distinguish`）。**

**这是检定力/设计结论，不是端点坏**：该端点自身干净（§4）、聚合稳（§3）、构造可比（§7）、可靠（§8），并且对**冻结头条量级**仍有约 **0.78** 的检定力；它只是**看不见 0.03 量级的小效应**。是否把 δ_min 改写为头条量级（或 1/2 头条 = 0.059）是 Lead 的**协议修订**决定；本审计按预注册执行并**不做**该修订。

**预注册重开条件（PROTOCOL_PB §12.3 / `pb.json → judgment.reopen_conditions_for_stage_2`）**：
1. Lead 显式修订 δ_min（例如 δ_min = 0.1183 或 0.059）并说明理由——本设计 MDE80=0.115，只有 δ_min ≥ 0.115 才能过；
2. 增加独立药对/细胞（r=0.40 仍 0.061）；
3. 走 raw dose-level（2,008,117,325 B）重拟合 `ΔEMAX` 类端点的新冻结协议——需下载预算批准，且它改变的是端点、不改变评估单元数，检定力增益未知。

## 10. 判定与失败类别

- **判定：`endpoint_not_usable`**；失败类别：**`evaluation_cannot_distinguish`**。
- **主端点**：`synergy_bliss`（block 级，Bliss 独立残差矩阵均值）；**聚合**：cell×pair 单元内 block 均值（≥1 块）。
- **不得换指标绕过**（PROTOCOL_PB §12.2）：不允许因 MDE/饱和/冗余改选 `synergy_zip/hsa/loewe/S/css`（构造更不可比）；本轮**未**发生任何改选。
- 条件（随结论传递）：§0 条件 1–4。
- 本判定**不**等于冻结结论已解冻，也不等于"DrugComb 不能复现"——它只说明**当前预注册设计+δ_min 下 P-B 不通过**，阶段 2 不应按 r=0.20/δ_min=0.03 启动。

## 11. 局限与缺口

1. **v1.4 无 study/design 列**：study 归属只能经 block_id 窗 + 身份签名代理；窗口来自 v1.5 的 4.22% 字节样本（是真实 study 范围的**下界**），3.8% 块无法指派；MATHEWS 窗被证明是混合窗。→ 端点受 study/design 混杂的结论**方向可信、幅度有不确定性**。
2. **无 per-block 剂量矩阵尺寸/浓度列**（仅单位字符串 `uM`）：矩阵尺寸只能按 study 的论文 S1 记录近似；"summary 值 = 矩阵平均"来自 SynergyFinder 实现与 NAR 文本，**未能**由 DrugComb 门户/管线代码核实（门户在本机不可达，见 R190-E1 §10）；"是否把零剂量边界计入平均"无法从 summary 直接判定（§8.2 的检验只给出方向性证据）。
3. **v1.5 样本非行随机**（按 block_id 排序后的字节均匀抽样）：study 级均值/窗口只作描述，不能外推全量。
4. **无 QC flag 列**：只能用构造边界做间接 QC；`css` 的 9.58% 出界即是间接 QC 的收获，但无逐块可信度权重。
5. **MDE 是保守口径**：双向聚类 bootstrap 同时包含预测向量随机性与 y 重采样；4 种聚类口径下 MDE80 都在 0.076–0.115（iid 0.022 不可用）——判定对该口径选择稳健。
6. **可靠性 ≠ 技术重复**：同 cell×pair 的多个 block 多数来自不同实验/设计，ICC 混合了技术噪声、设计差异与真实 study 效应；v1.4 无法分离。
7. **无实体级响应配对**：不与项目 Jaaks 表做行级端点等价性比较；只有构造/尺度层面论证。
8. **重复块**：48 个精确重复块保留（未做去重敏感性，因其占比 0.01% 且不影响任何统计量到报告精度）。

## 12. 复现

```powershell
cd D:\MAESTRO
$env:PYTHONHASHSEED="0"
& D:\anaconda\envs\maestro\python.exe research\2026-10-27-drugcomb-endpoint\pb.py
```

- 实测耗时：**77.5–106 s**（两次正式运行 + 早期版本）；两次正式运行 `pb.json` 逐字节相同 `ED5D6C95…AD104B`、`endpoint_audit.csv` 亦相同。
- 输入/脚本/协议 SHA256 全在 `pb.json → inputs / script / protocol`；无时间戳、JSON 键排序、固定种子（master 20261027）。
- 结构预跑（只读身份列）：`tmp/pb_structure_prepass.py`；身份签名分段诊断：`tmp/pb_identity_segments.py`（输出 `tmp/pb_identity_segments.json`）；MDE 分解诊断：`tmp/pb_mde_diag.py`。这些是辅助诊断，**判定数字以 `pb.py` 产物为准**。

## 13. 边界声明

- 未拟合任何 identity/annotation 模型；未做任何效应估计（含 `通路−identity` 增益）；未用响应值选训练集/特征/切分；未改其它目录、INDEX、SYNTHESIS、git、R190-E1 下载目录（只读）。
- 本报告不构成机制/靶点/临床主张；不把"端点可用性审计"写成"第二资源复现成立"；冻结结论（C130/C155–C156）状态**未变**。
