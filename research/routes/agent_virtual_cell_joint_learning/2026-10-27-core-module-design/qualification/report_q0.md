# R199-Q0 报告：组合功能替换关系 Δ(c;a,a';b) 的数据资格审计（metadata-only）

2026-10-27 ｜ 执行：drugcomb-auditor（task-53）｜ 工作目录 `D:\MAESTRO`
**协议**：[PROTOCOL_Q0.md](PROTOCOL_Q0.md)（v1 **FROZEN**，SHA256 `D87C004E3FDBCC7093C76B913D6D79C98C0DA02C9A3C9B4B6108A03381A26877`；在任何 Q0 门槛计数前冻结）
**脚本/结果**：[q0.py](q0.py)（`01FDDDE5…7C54D`）、[q0.json](q0.json)（`F952CCF3…786B`，连续两跑逐字节相同）；输入/脚本 SHA 见 q0.json。
**边界**：metadata-only；**未读响应数值做效应、未训练/未拟合/未估 Q**；不改其它目录/INDEX/git；不写机制/迁移/决策收益/新颖性。

## 0. 判定（先行）

# 总体：`not_qualified`

| 候选 | 判定 | 一句话 |
|---|---|---|
| **Jaaks Original** | `not_qualified`（**可作 source**） | 三向交叉规模足够、Δ 可估；但合法暴露/独立功能终点/独立培养均只能 conditional，且它是 reference 本身、与 Validation 共享 96 细胞 → 不能当独立 target |
| **Jaaks Validation** | `not_qualified`（同一资源） | 与 Original 共享 **96 细胞**、4,760 个 pair 键；换聚合不是新数据 |
| **O'Neil** | `qualified_with_conditions`（**唯一非 not_qualified 候选**） | G1 过、G2–G5 全 conditional：39 细胞、4×4 数字剂量、4 个技术重复、3 个 BatchID 同 lab；仅 viability 端点；9/39 细胞与 Jaaks 重叠；无独立功能读数、无独立培养认证 |
| **DrugComb v1.5** | `not_qualified` | 交叉规模大但**无数字剂量/暴露**（G2 fail）；跨 study/剂量混杂；组合端点 viability 派生；与 Jaaks 49/288 细胞重叠 |
| **DrugComb v1.4** | `not_qualified` | 同上，且无 study 列、与 v1.5 同 lineage（block_id 100% 可映射） |
| **BeatAML** | `not_qualified` | 单药/患者，无同细胞 (a,b) 组合 |
| **Mix-seq** | `not_qualified` | 单药（4 处理+对照）转录组，无组合功能端点 |

**总体 `not_qualified` 的原因不是交叉规模**：本地可构造的 Δ 三向交叉很大（Jaaks **2,014,581** 单元；O'Neil **699,746**；DrugComb v1.5 理论 **76,415,680** 单元），Δ 的 MDE 先验在 24–48 个细胞簇下也 ≤0.10（σ_e 0.041–0.109）。**真正的阻塞是：没有任何 source→target 对同时满足**
1. **同族功能端点**（Jaaks 的 `SYNERGY_DELTA_EMAX` 是 viability 派生协同分数；O'Neil 是原始 viability；本地 O'Neil 无单药参照 → 不能换算成 ΔEMAX；两族不可直接比较）；
2. **可验证的合法暴露**（Jaaks 拟合表只有 2 anchor 浓度 + 1 个 library 浓度标记，无 7 剂量原始网格/暴露时间；DrugComb summary 只有单位字符串，无数字剂量；O'Neil 有 4×4 数字剂量但无暴露时间/assay 方法记录）；
3. **独立培养/批次**（全部只有技术/barcode 重复；O'Neil 的 3 个 BatchID 同 lab，未认证独立培养；Jaaks barcode 不相交 ≠ 独立培养）；
4. **独立 lineage**（Jaaks 是 reference 本身；Original/Validation 96 共享细胞；O'Neil 9/39 细胞与 Jaaks 重叠；DrugComb 与 Jaaks 49/288 重叠且 v1.4/v1.5 同 lineage）；
5. **独立功能读数**（本机只有 viability 派生端点，无 apoptosis/caspase/靶点参与等正交功能读数）。

因此：**"固定反馈比较更新器"的公平 source→target 执行在本地数据上不可行**；进入第 2 步前需要新测量（§7）。若 Lead 接受"O'Neil 内部细胞留出的开发性比较"这一窄任务，可作 `qualified_with_conditions`，但那**不是** BRIEF 所要求的独立公平更新比较（不得据此宣称迁移/机制/决策收益）。

## 1. 对象与冻结定义

- `y(c,a,b)`：细胞 `c` 中成员药 `a` 与伙伴药 `b` 在合法暴露 `E` 下的功能响应均值。
- **替换关系**：`Δ(c;a,a';b) = E[y(c,a,b)] − E[y(c,a',b)]`，固定 `c`、`b`；`a,a'` 同角色可替换成员。Jaaks 主方向：`b`=anchor、`a,a'`=library；次方向 `b`=library、`a,a'`=anchor。
- **合法暴露**：同细胞、同伙伴身份、伙伴浓度档匹配、成员剂量曲线按预注册规则平均、暴露时间/端点/批次可核对；不得看结果挑剂量档。
- **三向交叉单元**：`(c, b, {a,a'})`，两侧均有合法测量。**可替换成员对**：同 `(c,b)` 下 `{a,a'}`。**跨细胞覆盖**：固定 `(b,{a,a'})` 在 ≥3 个细胞可算。
- **五门槛与判定**见协议 §3（冻结）：G1 交叉规模（≥5,000 单元/≥30 细胞/≥200 上下文/≥10 个跨 ≥3 细胞上下文）；G2 合法暴露（数字剂量+匹配≥95%+暴露记录）；G3 独立功能终点（非 viability 重编码；正交功能读数存在性）；G4 重复/批次（≥2 重复且独立培养/批次记录）；G5 Jaaks 重叠/非重聚合 lineage（≤10% 重叠为 pass，部分重叠 conditional，同资源/全重叠 fail）。`δ_min_provisional=0.10`（敏感性 0.05/0.10/0.15；第 2 步前须由 A5 决策成本替换）。

## 2. 五门槛数字（全部由 `q0.py` 从原始文件重算；metadata-only）

### G1 三向交叉（primary orientation；Jaaks `b`=anchor；其他候选以“固定伙伴+成员对”计）

| 候选 | 行数/输入 | 细胞 | 上下文 `(c,b)` | 三向单元 | 跨 ≥3 细胞成员对 | G1 |
|---|---:|---:|---:|---:|---:|---|
| Jaaks Original | 296,707 行；108,259 pair 键；46 anchors/65 libraries | 125 | 3,199（中位 25 成员/上下文） | **2,014,581** | **42,959** | **PASS** |
| Jaaks Validation | 23,505 行；4,933 pair 键 | 97 | 991（中位 4） | **12,622** | **388** | **PASS** |
| O'Neil（batch-aware） | 368,832 行；22,737 cell×pair 单元 | 39 | 1,792（中位 22） | **699,746** | **27,391** | **PASS** |
| DrugComb v1.5 | 1,432,351 行；739,964 combo blocks；26 个有组合的 study；288 combo 细胞；4,263 药 | 288 | 20,226（中位 83） | **76,415,680** | 未认证：pair×cell 枚举在 5,000,000 键上限停止（已见 508,385 个 ≥3 细胞键后停止） | **FAIL（未认证）** |
| DrugComb v1.4 | 1,175,220 行；466,033 combo blocks；112 细胞；4,088 药 | 112 | 11,148（中位 96） | **52,873,936** | 未认证（键数超 5,000,000 上限） | **FAIL（未认证）** |
| BeatAML | 单药 probit（942 临床行/63,395 药敏行；无组合） | — | 0 | 0 | — | **FAIL** |
| Mix-seq | 182,875 细胞；单药 4 处理+对照（含 CRISPR 臂） | — | 0 | 0 | — | **FAIL** |

- 说明：Jaaks 次方向（`b`=library、`a,a'`=anchor）同样大：**1,283,472** 单元、4,383 上下文、**27,052** 个 ≥3 细胞成员对；不改变判定。
- DrugComb 的 "pair 单元" 与 A3 的口径不同：A3 报的是**全局 distinct 无序药对**（v1.5 73,167；v1.4 62,826）；本表报的是 **(study, cell, 无序药对)** 与替换单元；A3 的跨 study 匹配为 41 共享细胞/4,179 单元（仅背景引用，**不作 Q0 证据**，见 C175/ERRATA_A3）。

### G2–G5 状态

| 候选 | G2 合法暴露 | G3 独立功能终点 | G4 重复/批次 | G5 Jaaks 重叠/lineage |
|---|---|---|---|---|
| Jaaks Original | **conditional**：可解析的 2 anchor 浓度×1 library 浓度标记；anchor 至少 1 个共同浓度 99.34%，至少 2 个共同浓度 85.46%；library 7 剂量网格/暴露时间不在拟合表 | **conditional**：`SYNERGY_DELTA_EMAX` = viability 派生协同分数；无正交功能读数 | **conditional**：pair 行重复 99.5% ≥2（含 2 anchor 浓度），但**同一 anchor 浓度**的 barcode 重复只有 **14.58%** 单元 ≥2 行；无独立培养 | **fail**：same reference；与 Validation **96 共享细胞**、4,760 共享 pair 键 |
| Jaaks Validation | conditional：anchor 共同 ≥1 浓度 100% | conditional（同上） | conditional：anchor 级重复 97.8% | **fail**（同资源；96 共享细胞） |
| O'Neil | **conditional**：数字剂量存在；同 batch×cell×partner 的伙伴剂量集 **100%** 唯一匹配；无暴露时间/assay 方法 | **conditional**：viability1–4 raw；无正交功能读数（`mu/muMax`、`X/X0` 是 viability 派生） | **conditional**：每 dose-cell 4 个技术重复；3 BatchID（1: 358,560 行；2: 5,232；3: 5,040）同 lab；无独立培养认证 | **conditional**：39 细胞中 **9** 与 Jaaks 重叠（23.1%）；非 Jaaks 细胞存在；独立 publication，但非独立 lineage |
| DrugComb v1.5 | **fail**：summary 只有 `conc_row_unit/conc_col_unit` 字符串，无数字剂量/暴露 | conditional：14 个 synergy/viability 派生列；无正交功能读数 | conditional：6.33% pair 单元 ≥2 blocks；A3 跨 study 仅 41 细胞/4,179 单元 | conditional：49/288 细胞与 Jaaks 重叠（17.0%） |
| DrugComb v1.4 | **fail**（同上；仅 `conc_r_unit/conc_c_unit`） | conditional：synergy 列存在 | conditional：9.63% pair 单元 ≥2 blocks；无 study 列 | conditional：18/112 细胞与 Jaaks 重叠（16.1%）；与 v1.5 同 lineage（block_id 100% 可映射） |
| BeatAML | fail（无组合） | fail（单药曲线） | fail | conditional（患者来源，非细胞系；不适用组合） |
| Mix-seq | fail（无组合） | fail（转录组，不是功能读数） | fail | conditional（单细胞转录；不适用组合） |

## 3. Δ 可估性与 MDE 先验（冻结公式；metadata-only）

- **每单元重复**：Jaaks 每个 `(cell,anchor,library,anchor 浓度)` 的 barcode 行数 min/median/max = **1/1/10**；**14.58%** 的 anchor 级单元有 ≥2 行（技术/barcode，同 screen，不跨批）。O'Neil 每个 `(cell,pair)` 有 16 行（4×4 dose grid，少数 32），每行 4 个 viability 技术重复 → 技术重复充足；无独立培养。DrugComb v1.5/v1.4 的 pair 单元 ≥2 blocks 分别 6.33%/9.63%（同 study/同批为主，非独立培养）。
- **Δ 的 MDE 先验**（`MDE80 = 2.801585 × σ_e/√n_eff`；σ_e 取既有轮次估计，非本轮读数）：
  σ_e = 0.041（A0 borrowed R4）/0.058（A2 single-key σ）/0.109（A2 noise variance 的方根）；
  n_eff = 24/48/96/192 → MDE80 表：

| n_eff | σ=0.041 | σ=0.058 | σ=0.109 |
|---:|---:|---:|---:|
| 24 | 0.02345 | 0.03317 | 0.06233 |
| 48 | 0.01658 | 0.02345 | 0.04408 |
| 96 | 0.01172 | 0.01658 | 0.03117 |
| 192 | 0.00829 | 0.01173 | 0.02204 |

- 达到 `MDE80 ≤ 0.10` 所需 n_eff：σ=0.041→**1.32**；0.058→**2.64**；0.109→**9.33**；达到 ≤0.15：0.59/1.17/4.15。**因此在 39（O'Neil）/125（Jaaks）个细胞簇下，MDE 先验均 ≤0.049（最保守 σ=0.109）——精度不是阻塞项**；阻塞项是 G2/G3/G4/G5。

## 4. 候选逐项结论（含"可支撑/需清洗/未认证/缺失"）

### 4.1 Jaaks Original / Validation——source 可用、target 不可用
- **可支撑**：三向交叉（Original 2,014,581 单元/3,199 上下文/125 细胞；Validation 12,622/991/97）；Δ 可估（pair 级重复行）；真实测量剂量设计（2 anchor 浓度，library 为全 dose-response 拟合）。
- **需清洗/未认证**：拟合表只有 1 个 library 浓度标记（7 剂量原始网格不在表中）；暴露时间/assay 未在表内；barcode 重复是同 screen 技术重复（每 anchor 级仅 14.6% ≥2 行）。
- **缺失**：独立功能读数（只有 viability 派生 ΔEMAX）；独立培养/批次记录。
- **lineage**：Original 与 Validation **共享 96 细胞/4,760 pair 键** → **不能把两者当独立数据**（BRIEF 明令）；Jaaks 自身不能当 target。
- **判定**：`not_qualified`（作为独立/target）；**可作 source**（G1 pass、G2/G3/G4 conditional、MDE ok）。

### 4.2 O'Neil——唯一 `qualified_with_conditions`，但只能当"受限 target/开发"
- **可支撑**：G1 **PASS**（699,746 单元；39 细胞；1,792 个 batch-aware 上下文；27,391 个 ≥3 细胞成员对）；数字剂量（4×4 网格，少数 5/7 水平；22,422 个 cell×pair 为 16 行，315 个 32 行）；同 batch×cell×partner 伙伴剂量 100% 唯一匹配；4 个 viability 技术重复。
- **需清洗/未认证**：无暴露时间/assay 方法列；BatchID 3 个同 lab、非独立培养；`mu/muMax`、`X/X0` 是 viability 派生，不作为独立功能读数。
- **缺失**：正交功能读数；单药参照（本地 workbook 只有 combination response，无 single-agent 表 → 无法自算 ΔEMAX）。
- **lineage**：39 细胞中 9 与 Jaaks 重叠（23.1%），30 个非 Jaaks 细胞；独立 publication 但非独立 lineage。
- **判定**：`qualified_with_conditions`。**条件**（写死）：① 只能作**开发性/内部细胞留出**比较（39 细胞；source/target 细胞不相交的留出），不得称独立/跨资源确认；② 端点仅 viability（不得写药效/临床/机制；不得把 I 类/II 类错误当条件规律）；③ 技术重复≠独立培养（BatchID 同 lab，未认证）；④ 与 Jaaks 9 个重叠细胞必须从 target 排除或单独报告；⑤ 无单药参照 → 不能与 Jaaks ΔEMAX source 拼成同端点 pair。

### 4.3 DrugComb v1.5 / v1.4——规模大但资格不成立
- **v1.5**：combo 739,964 blocks；288 combo 细胞；26 个有组合的 study（A3 总 34 study 含单药）；4,263 药；替换单元理论 76,415,680（20,226 个 study×cell×partner 上下文）；**但 summary 无数字剂量/暴露**（只有单位字符串）→ G2 fail；跨 study 只有 41 共享细胞/4,179 匹配单元（A3，仅背景）；6.33% pair 单元 ≥2 blocks；49/288 细胞与 Jaaks 重叠。
- **v1.4**：466,033 combo blocks；112 细胞；4,088 药；380,418 cell×pair 单元；替换单元 52,873,936；**无 study 列、无数字剂量** → G2 fail/G1 未认证；9.63% pair 单元 ≥2 blocks；18/112 细胞与 Jaaks 重叠；block_id 100% 映射 v1.5 → 同 lineage。
- **判定**：两者 `not_qualified`；v1.5 即使下载 raw dose-level 数据（2.0 GB，未下载）也只是"可能"解决 G2，G3/G4/G5 仍需处理；不得把大单元数当资格。

### 4.4 BeatAML / Mix-seq——结构上不适用
- BeatAML：单药 probit（942 临床行/63,395 药敏行）、患者样本、无同细胞两药组合 → G1 fail；单药曲线非组合功能端点 → G3 fail。
- Mix-seq：单细胞转录组、单药（4 处理+对照）、无组合功能终点 → G1/G3 fail（转录组不能代替功能读数，BRIEF 明确）。
- 判定：`not_qualified`（`no_combination_data`/`endpoint_not_independent`）。

## 5. 总体 source→target 判定（协议 §5）

- **source**：Jaaks Original（G1 pass；G2/G3/G4 conditional；MDE80 0.010–0.027）→ **source 可估**；Validation 是同一资源，不能当 source/target 独立。
- **target**：O'Neil 的 G1–G5 全过/conditional（target gates ok），但 **端点族与 Jaaks 不同**（Jaaks ΔEMAX vs O'Neil raw viability；本地无 O'Neil 单药参照，无法换算 ΔEMAX）→ **不可作 Jaaks 的 endpoint-compatible target**；DrugComb v1.4/v1.5 的 G2 fail；BeatAML/Mix-seq 无组合。
- **结论**：**没有 source→target 对同时满足"target gates + 同族端点 + 合法暴露 + 独立培养 + 非重聚合 lineage"** → 总体 **`not_qualified`**；公平更新比较不可执行。`fair_source_target_pair_found=false`。

## 6. 失败类别

`cross_scale_insufficient`（DrugComb v1.4 未认证；BeatAML/Mix-seq 无组合）、`exposure_unverifiable`（DrugComb v1.4/v1.5；Jaaks/O'Neil 为 conditional 未 fail）、`endpoint_not_independent`（全部候选的端点只有 viability 派生；无正交功能读数）、`replicates_missing`（BeatAML/Mix-seq）、`lineage_reaggregation`（Jaaks 自身/96 共享细胞）、`precision_insufficient`（BeatAML/Mix-seq；非其他候选的阻塞）。
- **注意**：`not_qualified` 是"本资源/本设计不能公平执行"，不是"条件替换规律不存在"；不是对 R196/R197 的复活或否定（C176/C177 均为 `inconclusive`/作废状态）。

## 7. 所需测量规格（最小新增；写死）

1. **target 资源**：≥30 个与 Jaaks 不重叠的细胞系（最好 ≥60，3 个以上组织）；**与 source 同族功能端点**（ΔEMAX 类协同或能由单药参照换算；不得 raw viability 直接拼 ΔEMAX）；**数字剂量设计 + 暴露时间 + assay 方法**；同 (cell,partner) 的伙伴剂量匹配；**≥2 个独立培养/批次**（不同日/passage/培养瓶；barcode/技术重复不算）；**≥1 个正交功能读数**（apoptosis/caspase/靶点参与/live imaging 任一）；端点与 source 的校准/桥接先于冻结。
2. **source–target 不相交**：细胞/条件/筛选批次预注册留出；不得用 Jaaks Original/Validation 换聚合；不得用重叠 9 细胞当 target。
3. **Δ 可估**：每单元 ≥2 次独立测量（或独立培养）；MDE80 ≤ δ_min（δ_min 须由 A5 决策成本冻结，不得沿用 0.10 临时值）；按细胞/伙伴聚类；MDE 模拟先于冻结。
4. **替代（若只做本地窄任务）**：O'Neil 内部细胞留出的开发性比较（`qualified_with_conditions`，条件见 §4.2），只能报告"该资源/该端点内的更新比较"，**不得**称独立确认/迁移/决策收益；要升级须补 §7.1–7.3。
5. **不达标不进入第 2 步**；不得换指标/切分/端点/剂量档凑资格。

## 8. 纪律与边界

- metadata-only：只读列名/ID/剂量设计/重复结构/行数；**响应列只做存在性检查，未读数值**；未训练/未拟合/未估 Q。
- **同一 96 细胞换聚合不是新数据**：Jaaks Original/Validation 共享 96 细胞/4,760 pair 键，已明确不当作独立证据。
- **C176/C177**：R196v2 `inconclusive`、R197v1 作废（低秩结构仍未检验）——既不支持机制成立，也不证明条件规律不存在；Q0 不引用其效果数字。
- **C174/C175**：1.43% 仅加性条件主效应份额；A3 `not_qualified` 只对冻结大规模门槛，41/4,179 仅作背景，不当 Q0 证据。
- 不写机制/迁移/决策收益/新颖性；阴性完整记录；本审计不声称"条件替换规律不存在"。
- 确定性：JSON 键排序、无时间戳；`q0.json` 两跑逐字节相同（`F952CCF3…786B`）；单命令 ≤15 min（实测首跑 ~177 s、修复后 ~80 s；见 record）。

## 9. 复现与文件

```powershell
cd D:\MAESTRO\research\2026-10-27-core-module-design\qualification
& D:\anaconda\envs\maestro\python.exe q0.py    # 写 q0.json；metadata-only，不读响应值
```

- 输入：Jaaks Original/Validation fitted、DrugComb v1.4 summary、DrugComb v1.5 full（`tmp/a3_v15_summary.csv`，SHA 见 q0.json；本审计只读身份/study 列）、O'Neil workbook（只读 BatchID/cell/drug/dose 列）、BeatAML 列名、Mix-seq obs 元数据；SHA 全部写入 q0.json。
- 产物：`PROTOCOL_Q0.md`、`q0.py`、`q0.json`、本报告、`record_q0.md`、`usage_q0.json`。
- 关键 SHA：PROTOCOL `D87C004E…A26877`；q0.py `01FDDDE5…27C54D`；q0.json `F952CCF3…1DA786B`。

## 10. 限制（必须随判定一起读）

1. **metadata-only**：所有"可支撑/conditional"都是元数据级判断；没有读响应值，因此不能给 Δ 的实测效应/噪声；MDE 是先验公式（σ_e 用 A0/A2 既有估计）。
2. **阈值是冻结的 provisional**：δ_min=0.10 为临时值，须由 A5 决策成本替换；G1 规模阈值（5,000 单元/30 细胞/200 上下文/10 个 ≥3 细胞上下文）是设计下限，不是统计功效反推。
3. **端点判断**：把"ΔEMAX 是由 viability 派生"判为 G3 conditional 而非 pass；若 Lead 认为 viability 本身就是合格功能端点，需在冻结前改口径——本审计不改已冻结规则。
4. **跨覆盖枚举上限**：DrugComb v1.4/v1.5 的 pair×cell 表在 5,000,000 键上限停止（G1 未认证）；这是内存保护，不是"交叉不存在"。
5. **O'Neil 的 batch-aware 解释**：把 BatchID 当 exposure 单元；若 BatchID 实际只是同 lab 技术批，O'Neil 的 G4 仍是 conditional（已如实标）。
6. **本审计不做系统资源综述**：未下载 DrugComb raw（2.0 GB）、未评其它未列候选；"未列"≠"不存在"。
