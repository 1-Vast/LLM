# PROTOCOL_PB — R191 阶段 1 · P-B：DrugComb v1.4 端点映射、聚合规则与饱和性/可靠性协议

**运行前冻结。** 本文件在任何 DrugComb 响应值统计之前写成并固定；`pb.py` 只按本文件执行，结果与判定不得因看到数据而调整（唯一例外见 §12.3 预注册升级路径）。

- 角色：端点与测量体制审计员（独立于提案者）。本协议**不评估任何效应**：不拟合 identity/annotation 模型，不做 `通路−identity` 增益估计，不做机制/靶点/临床推断。
- 工作目录：`D:\MAESTRO`；写入范围仅 `research/2026-10-27-drugcomb-endpoint/` 与 `tmp/`。`research/2026-10-27-drugcomb-qualification/` 等其它目录只读，不改 INDEX/SYNTHESIS/git。
- 上位文件：`research/2026-10-27-innovation-round-r191/BRIEF.md` §1 P-B；`research/2026-10-27-drugcomb-qualification/report.md`；`research/SYNTHESIS.md` §2d / C98 / C130 / C155 / C156 / C160 / C162。

---

## 0. 一句话目标

为"在 DrugComb v1.4 上复现冻结结论（两药都未见时粗注释替代身份、排序增益）"选定与项目端点 `SYNERGY_DELTA_EMAX`（下称 `ΔEMAX`）**构造上最可比**的**主端点**与**聚合规则**，用**预注册判据**判定其是否可用，并给出**MDE80** 与**预注册 δ_min**。判定只允许 `endpoint_usable` / `endpoint_not_usable`，**不得用换指标绕过**。

## 1. 响应值使用白名单（先于一切计算冻结）

DrugComb v1.4 summary 的 12 个响应/派生列（`css, synergy_zip, synergy_bliss, synergy_loewe, synergy_hsa, ic50_row, ic50_col, ri_row, ri_col, css_row, css_col, S`）的**数值**只允许用于下列统计；除此之外一律不读：

1. **端点分布与饱和性**（n/缺失、均值/sd/分位、边界质量、按细胞与按块稳定性）。
2. **端点语义/构造核对**（列间恒等式验证，如 `S` 与 `css, ri_row, ri_col` 的关系；`css` 与 `css_row, css_col` 的关系；构造上下界核查）。
3. **可靠性统计**（同 cell×pair 多块的分半相关 / 方差成分 ICC / 块内 sd）。
4. **测量体制描述**（study / 剂量矩阵设计异质性；study/design 来源由 block_id 代理与 v1.5 study 名核查）。
5. **MDE 的方差估计**（§11：在固定端点边际分布与聚类结构下，对检验统计量做零信息预测的聚类 bootstrap；不涉及任何臂/特征/模型拟合）。

禁止：用响应值筛选训练集/特征/切分；用响应值估计任何臂的效应（含 `通路−identity`）；用响应值改变主端点或判据。

## 2. 冻结输入（pb.py 逐一记录 bytes + SHA256）

| key | 路径 | 说明 |
|---|---|---|
| `v14_summary` | `research/2026-10-27-drugcomb-qualification/downloads/summary_table_v1.4.csv` | 193,184,734 B；SHA256 `E08E3D35BFA4BEA011AFE1B05B7025ACDE5C669C5E8D265866B5E12B08037A2F`（结构预跑已核） |
| `v15_chunks` | `…/downloads/v15_chunks/chunk_00..59_*.bin` | 60×1,000,000 B 均匀字节样本（全文件 4.22%）；逐块 SHA256 记录 |
| `v15_drug_id` / `v15_cell_id` | `…/downloads/DrugComb_drug_identifiers.xlsx` / `…_cell_line_identifiers.xlsx` | 仅作身份表交叉核对，本审计不以其为判定输入 |
| `nar2021` | `…/downloads/drugcomb_2021_supplementary_PMC8218202.zip` + 本目录 `sources/drugcomb2021_fullTextXML.xml` | Europe PMC `PMC8218202` = NAR 2021 `gkab438`（DrugComb update）；XML 100,166 B，SHA256 `7E67887349A04996C6E641ABB9F3D4162767E07740340F91BC1D9A7E43BF7BB7` |
| `nar2019` | `sources/drugcomb2019_fullTextXML.xml` | Europe PMC `PMC6602441` = NAR 2019 `gkz337`；107,898 B，SHA256 `F113A891CDA81855924481B0EEC3B4FE9FD0DB8669568F4AD3F35A69CB0BF781` |
| `malyutina2019` | `sources/malyutina2019_fullTextXML.xml` | PLoS Comput Biol 2019（CSS / S score 一手定义）；154,518 B，SHA256 `92F5F044A7CDA0A62379A78FDF98B607BD66DDC5B6600C39A46931C636288A76` |
| `synergyfinder_src` | `sources/R__*.R` | SynergyFinder 实现（Google 派生仓库 `google/synergyfinderengineered`，commit `64876b193d5cba140a1fee57bccf242d29d51f74`，2018-02-05）用于**聚合口径**核对；逐文件 SHA256 记录 |
| `e1_json` | `research/2026-10-27-drugcomb-qualification/e1.json` | 只读引用：v1.5 S1 study 表（37 study 的矩阵尺寸/块数）与 both-unseen 交叉核对值 |
| `jaaks_orig` / `jaaks_val` | `data/external/gdsc_combinations/jaaks2022_figshare/Original screen_All tissues_fitted data.csv`（198,893,607 B）/ `Validation screen_…`（11,774,397 B） | **仅作尺度参照**：读 `SYNERGY_DELTA_EMAX/EXP_EMAX/OBS_EMAX` 的边际分布，用于 §8.3 单位换算核对；**不进入任何 DrugComb 判定** |
| `protocol` / `script` | 本文件 / `pb.py` | SHA256 写入 `pb.json` |

版本归属（记录，不改判定）：NAR 2021 论文正文的 "As of March 2021, 751 498 drug combinations, 717 684 single drug screenings from 37 studies" 与 v1.5 相符；v1.4 summary 是其前代版本（Zenodo 记录 11102665，MD5 `c11efbd…66599b`）。响应列（`css`、四个 synergy、`S`）的**列语义**按 NAR 2021/2019 + Malyutina 2019 定义核对（§8）。

## 3. 结构事实（协议前置；只读身份/设计列，未读任何响应值）

来源：`tmp/pb_structure_prepass.py` → `tmp/pb_structure_prepass.json`（6.3 s）。

| 项 | 值 |
|---|---|
| 数据行 / 单药式 / **组合块** | 1,175,220 / 709,187 / **466,033** |
| `block_id` | 1…1,176,501 全表；**组合块 1…466,259**；无重复 block_id |
| 药物（组合行） | 原始名 4,150 / 归一名 **4,088**（归一 = NFKC→casefold→仅字母数字；碰撞键 12 个，与 R190-E1 一致） |
| 细胞 | **112**（无碰撞） |
| 无序药对 / **cell×pair 单元** | 62,826 / **380,418** |
| 每 cell×pair 块数分布 | 1:343,781；2:12,803；3:838；4:21,932；5:667；6:37；7:38；8:319；9:1；10:2 → 均值 **1.225055**；**≥2 块单元 36,637（9.63%）**，≥3 块 23,834 |
| 剂量设计信息 | **无浓度数值列**，只有 `conc_r_unit`/`conc_c_unit`（组合块 466,033/466,033 全为 `uM`）→ v1.4 的"剂量矩阵"只能经 **study 代理**间接推断 |
| study 列 | v1.4 **不存在** `study_name`（结构缺口，R190-E1 已记） |
| both-unseen r=0.20 复算 | 4,088 药 → k=818（`sorted` 归一名字典序 `[0::step][:k]`，step=4）→ **16,078 单元 / 2,671 药对**，与 R190-E1 精确一致 |

**study/design 代理（预注册）**：block_id 是单调分配的块标识，v1.5 分块样本的 `study_name` 显示 study 占据连续 block_id 段（如 ONEIL 689–91284、CLOUD 100338–132368、ALMANAC 132375–443923、PHELAN 445791–445852、MATHEWS 451709–465929、NCATS_MDR_CS 466192–466259，均在 v1.4 组合块范围内）。据此用 **`[min,max]` 窗口**把 v1.4 组合块指派到 v1.5 样本中出现的 study；未落入任何窗口的块记 `unassigned`。**这是代理，不是真 study 标签**；报告指派覆盖率，并另用"block_id 20 等分位"做无假设的 design-段异质性分析作交叉核对。

## 4. 主端点与聚合规则（冻结）

**主端点 = `synergy_bliss`（block 级数值 = 该 block 的剂量矩阵 Bliss 协同均值）。**
**分析单元 = (cell_line_name 归一名, 无序归一药对)。**
**聚合规则 = 该单元内全部 block 的 `synergy_bliss` 算术平均（missing 不参与；≥1 个非缺失 block 即纳入）。**

理由（先于数据，构造性）：
1. `ΔEMAX` 的一手定义（Jaaks 2022 Methods，§8.1 逐字）是 `ΔEmax = Bliss Emax − combination Emax`，即**以 Bliss 独立为期望模型**的 observed−expected 效应差。DrugComb 六个候选里只有 `synergy_bliss` 使用**同一期望模型**（Bliss independence）；`synergy_zip` 为"Bliss+Loewe"的 interaction-potency 模型，`synergy_hsa`/`synergy_loewe` 为不同零模型，`S`/`css` 属敏感性（sensitivity）而非 observed−expected 残差。→ **同零模型是可比性的必要条件**。
2. Jaaks 对重复测量做平均后进入分析（"Drug responses were averaged across technical and biological replicates"）→ 单元级用**块均值**与项目端点的测量体制对齐；`block` 是 DrugComb 的"一次实验/一张剂量矩阵"单位（NAR 2019：block id 用于区分"同一组合-细胞对在多次实验中被重复"）。
3. 不按响应值做任何筛选（不看 mean/sd/缺失挑子集）：全部分析宇宙块保留；聚合规则不看响应分布。

敏感性聚合（描述性，不替代主规则）：median、max、仅单块子集、按 block_id 取首块。稳健性判据见 §6。

**缺失与重复**：主端点缺失的 block 不参与均值；若一个单元全部 block 缺失 → 该单元在主端点下无定义（报告数量）。完全相同的 block 行（同单元且 6 个响应列全同）作为"精确重复"计数并**保留**（它们是不同实验/不同 block），另报"去精确重复"敏感性。

## 5. 饱和性判据（冻结；逐指标、block 级主判、unit 级复判）

判据只用端点自身的分布形状与**构造边界**，不用任何外部模型。记指标值 `v`，分析宇宙 = 466,033 组合块（缺失去除后）。

构造边界（一手）：`css`∈[0,100]（Malyutina 2019 Eq.5 "varies between 0 and 100"）；四个 synergy 与 `S` 以 **% inhibition 点数**为尺度（Malyutina：S 与 CSS "utilize the same unit as the percentage of inhibition"；NAR 2021 QC 口径把 % inhibition < −200% 或 > 200% 的剂量点标为 poor-quality → ±200 为文档化数据边界，±100 为 % 抑制名义尺度）。因此对 `synergy_*`/`S` 定义 **edge band = |v| ≥ 95**、**nominal half-range = 100**、**documented range = ±200**；对 `css` 定义 **edge band = (v ≤ 5) ∪ (v ≥ 95)**、**documented range = [0,100]**。

| id | 判据（冻结阈值） | 命中即记 |
|---|---|---|
| **S1** | 贴边质量：edge-band 内比例 **> 0.90** | `saturated`（BRIEF 字面"90% 值贴边"） |
| **S2** | 压缩：edge-band 内比例 **> 0.20** | `saturated`（天花板/地板压缩） |
| **S3** | 边界原子：任一"圆整构造边界" `B ∈ {−200,−100,−50,0,50,100,200}`（`css` 用 `{0,50,100}`）上精确取值的比例 **> 0.05** | `saturated`（钳位/填充/舍入原子） |
| **S4** | 方差塌缩：block 级 sd **< 2.0** 点（名义尺度 100 的 2%） | `saturated`（无可排序方差） |
| **S5** | 截断原子：等于观测最小值的比例 **> 0.001** 或等于观测最大值的比例 **> 0.001** | `saturated`（硬钳位痕迹） |
| **S6** | 文档域越界：`|v| > 200` 的比例 **> 0.01**（`css`：`v<0 或 v>100` 的比例 > 0.01） | `range_violation`（不是"饱和"，但同一硬门槛内判不可用） |
| **S7** | 完整性：主端点缺失比例 **> 0.20** | `incomplete`（不可用） |

**单指标判定（冻结）**：`metric_usable(m) = NOT saturated(m) AND NOT range_violation(m) AND NOT incomplete(m)`；
`saturated(m) = S1 ∨ S2 ∨ S3 ∨ S4 ∨ S5`。

**一致性要求**：主端点必须在 **block 级**与 **单元级（cell×pair 均值）** 两级都通过（两级判据相同，阈值相同）；若两级结论矛盾，以较严者为准并记录。

报告项（每指标、block 级与 unit 级各一套）：n、缺失数/率、mean、sd、min、p1/p25/p50/p75/p99、max、`atom0`（=0 比例）、`atom_min`/`atom_max`（=观测极值比例）、`atom_bound_max`（圆整边界原子最大比例）、`frac_abs_ge_95`（含 css 版）、`frac_abs_ge_99`、`frac_beyond_documented`、`sd_over_scale`、偏度/峰度、过零比例 `frac_gt0`/`frac_lt0`、`n_distinct`。

## 6. 聚合规则稳健性判据（冻结）

- **A1**：`Spearman(单元均值, 单元中位数) ≥ 0.99`（全部单元）。
- **A2**：`Spearman(单元均值, 单元内 block_id 最小的单块值) ≥ 0.80`（仅 ≥2 块单元，可靠性型检查）。
- **A3**（诊断，不设门槛）：`Spearman(块数, 单元均值)`，`|ρ| > 0.10` 记 `block_count_bias_flag`（重度研究过的组合可能更协同）。
- **A4**（描述）：`Spearman(均值, 最大值)` 报告。
- **判定**：A1、A2 任一不满足 → 记 `aggregation_unstable` → 主端点不可用（聚合不稳定≡端点噪声过大，按 §12 处理，不改聚合规则以救结论）。

## 7. 冗余判据（冻结）

在 6 个候选上计算 **block 级**与**单元级** Spearman 相关矩阵（pairwise complete）。
- **R1**：`ρ ≥ 0.90` → `redundant`（同一读数的不同口径）；`0.70 ≤ ρ < 0.90` → `partially_redundant`；`< 0.70` → `distinct`。
- **R2**：对 5 个 synergy 指标 + `S` 的 block 级相关矩阵做主成分：第一主成分解释方差 **≥ 0.80** → `single_dominant_factor`，并记录"候选不是互相独立的终点"。
- **R3**：预留规则——复现阶段只允许 1 个主端点进入主对比；其它指标只能作**预先声明的次端点**，不得用于"主端点不显著时换一个"。参照 C98 教训（四个连续 Δ 指标 ρ=0.806–0.967 不能当独立终点）。
- 另报 `ρ(ΔEMAX-like 排序, 各指标)` 不可得时的替代：不做任何 DrugComb–Jaaks 行级连接（无实体级交集键的响应配对），只在**分布/尺度**层面对照（§8.3）。

## 8. 与 `ΔEMAX` 的构造可比性（冻结的论证要求）

### 8.1 一手定义逐字引文（必须原样出现在报告里）
- **ΔEMAX（Jaaks 2022, Nature 603:594, Methods "Classifying synergy"）**：*"Shifts in potency (ΔIC50) and in efficacy (ΔEmax) were calculated as the difference between the observed combination response and expected Bliss (ΔIC50 = Bliss IC50 − combination IC50, and ΔEmax = Bliss Emax − combination Emax). … or the ΔEmax ≥ 0.2 (20% shift in viability)."*；*"The Emax and the IC50 are based on the fitted curves. Emax is reported at the highest tested concentration for the drug."*；Bliss 期望：*"every point on the Bliss dose response curve is defined as the product between the anchor viability and the corresponding point on the library dose response curve."*
- **DrugComb Bliss（NAR 2021, gkab438）**：*"For evaluating the drug synergy, we implement four major mathematical models including Bliss, Loewe, HSA and ZIP (36) … The Bliss model assumes probabilistic independence when drugs are non-interactive while the Loewe model assumes that the efficacy of non-synergistic drug combinations is identical to that of a drug combined with itself."*；符号：*"Drug combinations with synergy scores of zero are considered additive, while a positive synergy score suggests synergy, and a negative score suggests antagonism."*；尺度（Malyutina 2019）：CSS/S *"utilize the same unit as the percentage of inhibition of cell viability. Therefore, the synergy score can be interpreted as the extra percentage inhibition effect beyond the expectation."*
- **块级聚合口径（SynergyFinder 实现，commit 64876b1）**：`Bliss()` 的参考矩阵 `ref.mat[i,j] = drug1.response[i] + drug2.response[j] − drug1.response[i]*drug2.response[j]/100`，`syn.mat = response.mat − ref.mat`（% 抑制尺度；正值=协同）；`Plot_synergy.R` 的标题分数 = 所选矩阵区域的 `mean()`（"Average synergy"），且注释说明"first row and column are removed … When dose=0 for either drug, the synergy score is also 0."。

### 8.2 可比性硬条件（全部必须成立才可写"论证成立"）
- **C1 同零模型**：主端点必须由 **Bliss 独立**期望构造（`synergy_bliss` 满足；其它不满足）。
- **C2 同方向**：正值 = 组合优于期望（`synergy_bliss` 满足）。
- **C3 可换算尺度**：主端点以 % 抑制点为单位，`ΔEMAX` 以 viability 分数为单位（阈值 0.2 = 20 点）→ 乘 100 可直接换到同一 %-point 尺度。
- **C4 书面差异（必须明写，不得隐藏）**：① `ΔEMAX` 是**拟合 Emax 的效能对比（最高测试浓度处的 observed−expected）**，而 summary 的 synergy 是**整张剂量矩阵逐点残差的平均**（混入 potency 与低剂量近零残差）→ 不是同一统计量；② Jaaks 为 **anchored 2×7** 设计，DrugComb block 的矩阵尺寸/设计混杂（2×2 … 10×10，v1.4 无设计列）；③ Jaaks 用**拟合曲线参数**，DrugComb 用 SynergyFinder 矩阵均值；④ DrugComb 93.2% 数据点无重复（NAR 2021），重复/批次结构不同。
- **C5 尺度一致性核对（描述性，不作独立门槛）**：`sd(synergy_bliss)` 与 `100 × sd(ΔEMAX)` 的比值必须报告；比值落在 `[1/3, 3]` 记 `scale_consistent`，否则记 `scale_divergence_flag`（阈值预注册，不用于单独否决，但须在报告里解释）。

### 8.3 明确不可得
DrugComb 与 Jaaks 之间**没有可用的实体级响应配对**用于直接比较端点数值等价性（细胞交集 18、药 40，单元键 241；且两资源设计不同）。因此可比性只能在**构造/零模型/符号/尺度**层论证，**不作"等价性"主张**。

## 9. 可靠性/测量体制（冻结算法）

- **ICC(1)**：对 ≥2 块单元（36,637 个）做一元随机效应方差分解，`σ²_within = Σ_i Σ_j (y_ij − ȳ_i)² / Σ_i (m_i − 1)`；`m0 = (Σm_i − Σm_i²/Σm_i)/(k−1)`；`σ²_between = max(0, (MSB − σ²_within)/m0)`；`ICC = σ²_between/(σ²_between+σ²_within)`。
- **分半相关**：单元内 block 按 block_id 排序，偶/奇交替分半；两半均非空的单元上算 Pearson 与 Spearman，再做 **Spearman–Brown** 校正 `r2 = 2r/(1+r)`。
- **块内 sd**：≥2 块单元的块内 sd 中位数；按块是否落在**同一 study 代理窗口**分"同 study/跨 study"两组报告（与 NAR 2019 报告的 CSS 复现性基准对照：*within-study average sd 4.25（ONEIL）/12.02（ALMANAC），between-study 15.44，负对照 17.5*）。
- **可靠性上限**：`ρ_ceiling = sqrt(ICC·m̄/(1+(m̄−1)ICC))`（报告，不作门槛）。
- **按细胞稳定性**：每细胞（112 个）块级均值/sd 的跨细胞分布（mean of means、sd of means、IQR）；报告细胞间方差份额。
- **按块稳定性**：block_id 20 等分位段内的均值/sd；`η²(block_id bin)`（组间方差/总方差）作为 design/时间异质性指标。
- **study 代理异质性**：§3 的窗口指派 → 每 study 的块数、主端点均值/sd/p50；`η²(study_proxy)`；**剂量矩阵混染检验**（预注册两个竞争预测，均用 v1.5 S1 的矩阵尺寸）：
  - 若 summary 值 = **不含零剂量的实剂点平均**：`sd_study ∝ 1/sqrt(k)`，`k = (nr−1)(nc−1)`；
  - 若 summary 值 = **含零剂量边界（结构性 0）的整矩阵平均**：`sd_study ∝ f = k/(nr·nc)`（幅度衰减）。
  报告 `corr(sd_study, 1/sqrt(k))`、`corr(sd_study, f)` 与各自解释；并报告 v1.5 分块样本的 study 级 `synergy_bliss` 分布作独立复核（同一 S1 矩阵尺寸）。**只描述、不据此选主端点**。
- 若 study/design 代理显示主端点存在强异质（`η²(study_proxy) ≥ 0.10` 或矩阵尺寸解释 sd 的方向性一致），必须作为**条件**写入判定（不是否决项，但不得隐藏）。

## 10. 确定性、可复现与响应保护

- `pb.py`：纯离线、单进程、固定种子（`SEED = 20261027`；bootstrap 每个 `np.random.default_rng(seed + k)` 独立流）、**JSON 键排序**、**无时间戳**、浮点统一 `round(x, 6)`；输入/脚本/协议 SHA256 全部写入 `pb.json`。
- 重跑两次 `pb.json` 必须逐字节相同（写进 report）。
- 产物中不得出现任何训练/效应估计痕迹：grep 复核输出无 `ridge`/`fit(`/`predict`/`coef`/`annotation arm` 一类内容（`grep` 审计写进 record）。

## 11. MDE80（冻结定义与算法）

**目标量**：在 r=0.20 留药、both-unseen 设计（16,078 单元 / 2,671 药对）下，排序主指标（**Spearman ρ**，全评估单元上预测 vs 端点）的 80% 检定力最小可检效应 **MDE80**。

**统计量**：`ρ̂ = Spearman(ẑ, y)`，`y` = 主端点单元均值（§4），`ẑ` = 臂预测。both-unseen 下 **identity 臂预测恒为常数**（两药 one-hot 全 0 → ridge 预测 = 截距）⇒ `ρ(identity)` 约定为 0（与 C130 的 ρ=+0.0001≈0 一致）；故主对比 `Δρ = ρ_annotation − ρ_identity` 的 MDE = 单臂 ρ 对 0 的 MDE。此约定写死。

**MDE80 定义（与项目 A0/C160 同口径）**：`MDE80 = (z_{1−α/2} + z_{power}) × SE = 2.801585218112968 × SE`，α=0.05 双侧、power=0.80；`SE` = 统计量在**零信息预测**下的聚类 bootstrap 标准差。

**零信息预测**：每个药对 p 抽 `z_p ~ N(0,1)`，广播到该对全部单元（因为注释/身份臂的预测在固定药对下不随细胞变化；C141："只排组合、不排细胞"）。

**bootstrap 设计（B = 2,000）**：
- **Regime A（药对聚类）**：以药对为单位有放回重采样 2,671 个药对（带入其全部单元；单元重复计数），每 replicate 重抽 `z_p`，算 `ρ̂`；`SE_A = sd(ρ̂)`，`MDE80_A = 2.801585 × SE_A`。
- **Regime B（药/细胞双向聚类）**：每 replicate 独立地 (i) 有放回重采样药对；(ii) 有放回重采样 112 个细胞系；每个观测单元权重 `w = mult_pair × mult_cell`（展开为重复单元后算 `ρ̂`，并列用 midrank）；`SE_B`、`MDE80_B`。
- **iid 解析参照**：`SE_iid = 1/sqrt(n−1)`，`MDE80_iid = 2.801585 × SE_iid`（报告，不作门槛）。
- **检定力校验**：在 `δ ∈ {0.03, MDE80_B, 0.05, 0.10, 0.1183}` 上模拟（`z* = δ·(y 标准化) + sqrt(1−δ²)·noise`，重抽 1,000 次），报告 `P(ρ̂ > 1.96·SE_B)`；在 `δ = MDE80_B` 处应 ≈0.80（正态近似校验，允许 ±0.05）。
- **设计尺寸敏感性（预注册的规划用，不是结果驱动）**：同一算法在 r=0.30（33,148 单元）/ r=0.40（52,368 单元）上重算 MDE80_A/B（`B=1,000`，同种子规则），仅用于**阶段 2 设计尺寸规划**。

**预注册 δ_min = 0.03**：理由——冻结结论头条增益 +0.1183 的 1/4 ≈ 0.0296 → 取 **0.03**；复现必须在 ≥1/4 头条效应的量级上可检。门槛：**MDE80_B（conservative） ≤ δ_min**（若 r=0.20 不满足则触发 §12.3 预注册升级路径检查）。

## 12. 判定规则（冻结）

### 12.1 `endpoint_usable` 当且仅当全部成立
1. 主端点 `synergy_bliss` 在 §5 下 **两级（block / unit）均 `metric_usable`**；
2. §6 聚合稳健性 A1、A2 均满足；
3. §8 C1–C4 成立（书面论证完整、差异不隐藏），且 C5 已报告（若 `scale_divergence_flag` 须给出解释）；
4. `MDE80_B ≤ δ_min = 0.03`（r=0.20 主设计；§12.3 允许的升级路径见下）。
否则 **`endpoint_not_usable`**，失败类别取下列之一并逐条记录证据：
`endpoint_saturated` / `range_violation` / `endpoint_incomplete` / `aggregation_unstable` / `construct_mismatch` / `evaluation_cannot_distinguish`。

### 12.2 禁止事项（写死）
- **禁止**因饱和/分布/冗余/效应不显著而改选 `synergy_zip`/`synergy_hsa`/`synergy_loewe`/`S`/`css` 作主端点——它们在契约上是**更不可比**的构造（不同零模型或不同量）；任何此类改选一律记 `endpoint_not_usable` + `metric_switch_prohibited`。
- 副指标（其它 5 个）的分布/冗余结论**只作描述与风险披露**，不参与主判定，也不得用于"换一个指标让 P-B 过关"。

### 12.3 唯一预注册升级路径
若 §12.1 的第 1–3 条成立、但 r=0.20 的 `MDE80_B > 0.03`：
- 依 §11 的设计尺寸敏感性检查 r=0.40：若 `MDE80_B(r=0.40) ≤ 0.03` → 判 **`endpoint_usable`（条件：阶段 2 主设计必须使用预注册的 r=0.40 切分；r=0.20 仅作敏感性）**，理由写成"设计检定力不足，扩大预注册设计尺寸"，并明确这不是换切分重试（效应尚未运行）。
- 若 r=0.40 仍 `> 0.03` → **`endpoint_not_usable`**（`evaluation_cannot_distinguish`），并记录升级方向：冻结新的 **raw dose-level（2,008,117,325 B）重拟合 ΔEMAX 协议**（需 Lead 单独批准下载预算；且须声明 DrugComb 多数 study 非 anchored 设计，重拟合只能逼近 Jaaks 的 Emax 对比，不能完全等同）。

## 13. 交付物（本目录）
`PROTOCOL_PB.md`（本文件，运行前冻结）→ `pb.py` → `pb.json`（键排序、无时间戳、含全部输入/脚本 SHA256）→ `endpoint_audit.csv`（逐指标一行）→ `report.md` → `record.md` → `usage.json`；`sources/` 存一手文献与实现源码（SHA256 已记）；`tmp/` 存结构预跑与运行日志。

## 14. 明确不做
不拟合 identity/annotation 模型；不做任何效应估计（含 `通路−identity` 增益）；不选训练集/特征；不重开线 D；不重开 I003/可检出性；不做机制/靶点/临床主张；不把"端点可用"写成"冻结结论已解冻"；不改其它目录/INDEX/SYNTHESIS/git。

## 15. 与 Lead 预探的关系
Lead 的预探（块级 `synergy_bliss` 均值 −0.45/sd 9.67、`synergy_loewe` −7.76/15.45、`synergy_hsa` 0.44/8.59、`synergy_zip` −1.00/9.08、`S` 1.00/18.08、`css` 31.0/25.8；bliss–zip 0.920、bliss–hsa 0.801、loewe 与其余 0.07–0.55、css 低相关）**只作参考**：本审计独立重算并逐项复核；任何与预探不一致之处如实报告（不调和、不隐藏）。预探数值不进入任何判据阈值。

---
*冻结时间：2026-10-27（协议 SHA256 见 `pb.json → protocol.sha256`；本文件在 `pb.py` 首次运行前完成）。*
