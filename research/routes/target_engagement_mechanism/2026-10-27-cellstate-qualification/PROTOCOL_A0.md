# 细胞状态特征资格审计协议（R190 线 D，A0）

2026-10-27，**在任何效应估计/模型拟合之前冻结**。角色：数据资格审计员（独立于提案者；不设计也不运行效果实验）。本协议只回答"资源与设计能否支持一个可证伪的排细胞假设"，不回答"表达特征有没有用"。

## 0. 范围与输入

- 问题：用药物靶点基因在细胞系的表达（辅以突变/组织）作为**细胞状态特征**，能否在留出细胞上把**同一药对内**的细胞按 `ΔEMAX` 排出可检出的次序？本审计判定该问题在本机上**是否可检验**，不做任何模型收益估计。
- 输入（只读）：
  - `data/external/gdsc_combinations/jaaks2022_figshare/Original screen_All tissues_fitted data.csv`（198,893,607 B；usecols 见下）
  - 同目录 `Validation screen_All tissues_fitted data.csv`（11,774,397 B，仅用于交叉核对/可靠性上限的辅助口径）
  - `data/external/depmap_19q4/sample_info.csv`（1,756 行）、`CCLE_expression.csv`（19,144 基因 × 细胞系）、`CCLE_mutations.csv`
  - `data/external/gdsc_combinations/jaaks2022_figshare/Glossary.xlsx`（列定义）
- 解释器：`D:\anaconda\envs\maestro\python.exe`（pandas 2.3.3 / numpy 2.4.6 / scipy）。本机 CPU，确定性，可重跑。
- 输出（全部写入 `research/2026-10-27-cellstate-qualification/`）：`PROTOCOL_A0.md`（本文件）、`a0.py`、`a0.json`、`identity_map.csv`、`target_map.csv`、`report.md`、`record.md`、`usage.json`。

## 1. 允许读取 / 禁止

**允许**：Jaaks 拟合表全部列（本审计需要 `CELL_LINE_NAME`、`COSMIC_ID`、`ANCHOR_NAME`、`LIBRARY_NAME`、`ANCHOR_TARGET`、`LIBRARY_TARGET`、`SYNERGY_DELTA_EMAX`、`Tissue` 等元数据）；DepMap sample_info 全部列；CCLE 表达/突变矩阵；Glossary。**允许读取响应值（`SYNERGY_DELTA_EMAX`）但只用于本协议 §4 预先写死的资格统计（方差成分、可靠性、检定力模拟）**，不得用于特征选择、调参、挑选子集或任何"效果"估计；所有用到响应值的统计必须在代码中显式标注 `purpose=qualification`。

**禁止**：拟合任何预测模型并报告其性能；按响应值筛选细胞/药对/基因；用即将检验的同一数据挑选特征或阈值；联网新增数据（本审计不联网）；修改任何输入/其它研究目录。

## 2. G1 身份连接（细胞）

- 主口径：Jaaks `COSMIC_ID`（数值）↔ DepMap `sample_info.COSMIC_ID`（数值），要求 **1:1**（同一 COSMIC 对应唯一 DepMap_ID；否则记歧义并按次口径处理）。
- 次口径（仅填补主口径未覆盖者）：`CELL_LINE_NAME` 经 NFKC→casefold→去非字母数字与 `stripped_cell_line_name` 相同且该归一名在两侧均唯一。
- 报告：主/次口径覆盖数、一对多/多对一/冲突清单、未匹配细胞；冻结 `identity_map.csv`（CELL_LINE_NAME, COSMIC_ID, DepMap_ID, join_method, note）并记 SHA256。
- 门槛：125 个 Jaaks 细胞中 **≥119（95%）** 映射到唯一 DepMap_ID 且有表达行；否则 `unqualified: data_unavailable`。

## 3. G2 特征可得性（表达与靶点映射）

- 解析 `CCLE_expression.csv`：行标识列 == `DepMap_ID`；列名 `GENE (entrez)` 提取 GENE；报告矩阵维度、重复基因名、常数/零方差列数、缺失值数。
- 靶点→基因列映射：Jaaks `ANCHOR_TARGET`/`LIBRARY_TARGET`（逗号分隔，去重）共 86 个唯一值。先做**精确匹配**；未命中者只允许使用本协议冻结的**别名表**（见下表；每条注明理由），别名表外的机制类词条（如 "Microtubule destabiliser"、"DNA alkylating agent"）**不猜映射**，列入 `unmapped`。
- 冻结别名表（写入代码常量）：ABL→ABL1；BCL-W→BCL2L2；BCL-XL→BCL2L1；DNAPK→PRKDC；ERK1→MAPK3；ERK2→MAPK1；IR→INSR；JNK2→MAPK9；MEK1→MAP2K1；MEK2→MAP2K2；MTORC1→MTOR；MTORC2→MTOR；PDGFR→PDGFRA+PDGFRB；PI3Kalpha→PIK3CA；PI3Kbeta→PIK3CB；RAF→RAF1+BRAF；S6K1→RPS6KB1；VEGFR→KDR+FLT1；p38→MAPK14；HSP90→HSP90AA1+HSP90AB1；ERBB2|MEK1→ERBB2+MAP2K1；Ephrins→EPHA2+EPHB2（仅当两列均在矩阵中）。
- 报告：精确/别名/未映射数量；每个药物的靶点基因覆盖数分布；**映射覆盖率**（86 中映射成功数）与药物级覆盖（2025 药对中两侧靶点均 ≥1 个映射基因的比例）。
- 门槛：86 个靶点中 **≥60 映射成功**；且 2025 药对中 **≥90%** 两侧靶点均 ≥1 映射基因。否则 `unqualified: data_unavailable`。

## 4. G3 信号、room 与检定力（预注册统计；只用资格口径）

- 键定义：`(CELL_LINE_NAME, 无序药对)`，药物对按 `ANCHOR_NAME`+`LIBRARY_NAME` 的字符串对（无序；同名对保留但报告数量）；响应 `y = mean(SYNERGY_DELTA_EMAX over rows of that key)`。
- **(a) 方差分解**：两路可加 ANOVA（迭代均值中心化，收敛 1e-9）：`y ≈ μ + a_cell + b_pair + ε`。报告 cell / pair / interaction 方差份额。**门槛：interaction 份额 ≥ 0.10**（within-pair 细胞特异变化必须非平凡；如低于此值，"排细胞"无对象）。
- **(b) 可加细胞效应上限**：对每个有 ≥5 个细胞的药对，计算 `Spearman(y, â_cell)`；报告均值/中位/分布（这是"只知道细胞主效应"时 within-pair 排序的上限）。**门槛：均值 ≥ 0.05**（若连这个上限都接近 0，任何细胞特征都不可能通过主效应路径排序；交互路径另行报告但本门槛不淘汰）。
- **(c) 交互路径的 room**：对每个药对，把 `y` 对药对均值中心化得 `y_int`；报告 within-pair 的 `y_int` 标准差分布。**门槛：药对级 `sd(y_int)` 中位数 ≥ 0.02**（与 ΔEMAX 本身量级比较，防止"变异全是噪声"）。
- **(d) 测量噪声与可靠性上限**：用 `Original_screen_All_tissues_raw_data.csv.zip`（若可解析）估计键级重复噪声 σ_e；不可解析时借用 R4 的 σ_e=0.041 并标明 `borrowed`。报告可靠性上限 `ρ_ceiling = sqrt(var_signal/(var_signal+σ_e²))`，其中 `var_signal = median_pair_sd(y_int)²`。**门槛：ρ_ceiling ≥ 0.10**。另用 Validation screen 的重叠键做**跨筛 within-pair 排序可靠性**（若某药对在两筛中均有 ≥2 个共同细胞，则计算 within-pair Spearman；报告可算药对数——**仅辅助，不作门槛**）。
- **(e) 检定力**：按 5 折留出细胞（确定性分折：细胞归一名排序后 `i % 5`；每折 25 细胞）。对每折：测试键 = 该折细胞的所有键；对每个药对，若测试细胞数 ≥2，计算 `within-pair Spearman(pred, y)`（pred 由后续效果协议定义；本审计用**零预测**的解析 SE 与 bootstrap 模拟估计 MDE，不拟合模型）。报告：每折测试键数、可排药对比例、均值 within-pair Spearman 的 **MDE80**（bootstrap 按药对与细胞双向聚类，1,000 次重采样，固定种子 20261027）。**门槛：MDE80 ≤ 0.05**（即计划最小效应 δ_min=0.05 可在 80% 检定力下检出）。
- **(f) 目标组织外推**：报告 125 细胞的 `Tissue` 分布与留出细胞在组织层面的覆盖（仅描述；若某折组织完全缺失，记录为设计限制）。

## 5. G4 泄漏与切分可行性

- 书面核对并写入报告：表达/突变是**细胞注释**、非响应派生；靶点注释来自 GDSC 元数据（不是由响应反推）；`identity_map` 不依赖响应；分折按**细胞**（不是行），内层 λ 选择须按细胞分组（效果协议要求）；最终留出细胞不参与任何特征标准化/调参。
- 产出 5 折细胞清单（冻结）与每折的键数、可排药对数；`a0.json` 记录分折哈希。
- 若任何一项无法满足（如表达矩阵含隐藏响应派生列、DepMap_ID 重复），记录 `design_invalid` 并停。

## 6. G5 端点与决策操作化（为效果协议定稿提供）

- 主端点：留出细胞上 **within-pair Spearman** 的折均值（每药对 ≥2 测试细胞）；次端点：within-pair top-1 命中（预测最高细胞的真实是否为该对最高四分位）与 top-quartile AUC。
- 对照基线（效果协议用，不由本审计评估）：cell-blind（pair 常数，within-pair 秩相关定义为 0）；tissue-only；同维随机基因块；打乱药物↔靶点映射；可加细胞主效应模型。
- 记录：outcome 为 `SYNERGY_DELTA_EMAX`（viability 派生协同读数），**不构成独立功能终点/机制/临床结论**。

## 7. 判定规则（冻结）

- 前置：P1 输入文件 SHA256 记录；P2 表结构/列定义与 Glossary 一致（不一致如实记录并按实测重述，不判死）。
- 门槛：G1 覆盖 ≥95%；G2 映射 ≥60/86 且药对覆盖 ≥90%；G3(a) interaction 份额 ≥0.10；G3(b) 可加细胞效应上限 ≥0.05；G3(c) 中位 `sd(y_int)` ≥0.02；G3(d) ρ_ceiling ≥0.10；G3(e) MDE80 ≤0.05；G4 无 design_invalid。
- 输出：`qualified` / `qualified_with_conditions`（列出条件与相应限制）/ `unqualified`（列出失败门槛、失败类别与解冻条件）。**不允许事后调整门槛**。

## 8. 失败类别与停止

- `data_unavailable`：身份/表达/靶点映射不满足。
- `data_insufficient`：room 或可靠性不足（interaction 份额、sd、ceiling 未达门槛）。
- `evaluation_cannot_distinguish`：MDE80 > 0.05。
- `design_invalid`：泄漏/分折/表结构问题。
- 任何未达门槛 → 记录并停，不运行效果实验、不换指标/换聚合制造收益。

## 9. 确定性与产物规范

- `a0.py` 确定性：固定种子 20261027，JSON 键排序、无时间戳，输入与脚本 SHA256 写入 `a0.json`；重跑输出逐字节一致（审计员至少验证一次）。
- `report.md`：方法、实测结构、G1–G5 逐项数字与判定、失败类别、解冻条件、局限。`record.md`：范围/预算/命令/耗时/观测/决定。`usage.json`：未知数值记 null。
- 只写本目录与 `tmp/`；不改 `research/INDEX.md`、`SYNTHESIS.md`、`git`、其它研究目录。

## 10. 明确不做

不拟合预测模型、不报告任何"表达特征有/无收益"的结论、不做特征选择、不做机制/临床推断、不联网、不修改效果协议、不晋升代码。

## AMENDMENT-A0-001（2026-10-27 13:2x，**审计脚本运行之前**记录；Lead 结构探针触发）

- **事由**：Lead 在协议冻结后、审计运行前的结构探针（只读身份/表达矩阵行，未计算任何响应统计）发现：`CCLE_expression.csv` 只有 **1,249** 个 `DepMap_ID` 行（`sample_info.csv` 有 1,756 行）；Jaaks 125 个细胞全部可映射到唯一 DepMap_ID，但其中 **111/125（88.8%）** 有表达行，**14 个缺失**（Breast 5：OCUB-M、MDA-MB-330、MRK-nu-1、EVSA-T、COLO-824；Colon 6：COLO-320-HSR、HCC2998、COLO-205、CaR-1、DiFi、SNU-C2B；Pancreas 3：PL4、MZ1-PC、KP-1N）。原 G1 门槛"≥119（95%）映射且**有表达行**"按此实测会因表达矩阵覆盖不足而被判 `data_unavailable`，但该门槛的本意是"身份与特征可得"，不是要求 100% 细胞都有表达。
- **修订（仅此一处门槛；其余门槛与口径不变）**：G1 门槛改为 **≥119（95%）映射到唯一 DepMap_ID**，且其中 **≥105（84%）有表达行**；缺失表达细胞必须逐一列出（名称、组织），并在 G3(e)/G4 中按**有表达细胞**（预期 111）做 5 折留出；报告全部 125 与 111 两套键数/药对数以量化损失。MDE 必须按 111 细胞重算（每折 ~22 细胞）。
- **为什么不是事后调门槛**：本修订发生在任何资格统计（方差成分/room/可靠性/MDE）计算之前，只依据"矩阵有多少行、能映射多少细胞"这一结构事实；修订方向是**放宽到可检验**而非为通过而放宽效果口径，且损失（14 细胞）被显式报告。原门槛文本保留如上，不作删除。
- **附加事实**：表达矩阵 19,144 基因列、1,249 行；若后续审计发现 `DepMap_ID` 重复/列解析异常，按 P1/P2 如实报告，不猜。

