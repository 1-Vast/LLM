# PROTOCOL_A0 — R193 条件偏移匹配资格审计（冻结于运行前）

2026-10-27，**在任何匹配计数运行前冻结**。角色：A0 匹配资格审计员（独立；不做效果分析、不估 Q）。本协议冻结后不再修改；实际结构与先验不符时按本协议如实记录，不回头改口径、不做事后门槛调整。

## 0. 范围与输入（只读）

- 任务：R193 A0 —— Jaaks GDSC 组合筛 Original/Validation **拟合表**的元数据匹配/四元组资格审计，回答"匹配四元组是否足够（≥预注册门槛）+ 是否有 ≥2 组独立测量 + 细胞/药对覆盖如何"，从而决定 Q 条件偏移复验（H193a）能否进入 A1 分析协议。**本任务不读响应数值、不估 Q、不做效应/相关/预测计算。**
- 输入（全部只读；SHA256 在运行时记录进 a0.json）：
  - `data/external/gdsc_combinations/jaaks2022_figshare/Original screen_All tissues_fitted data.csv`（198,893,607 B）
  - `data/external/gdsc_combinations/jaaks2022_figshare/Validation screen_All tissues_fitted data.csv`（11,774,397 B）
  - `data/external/gdsc_combinations/jaaks2022_figshare/Glossary.xlsx`（12,193 B）
- 解释器：`D:\anaconda\envs\maestro\python.exe`（Python 3.11.16 / pandas 2.3.3 / numpy 2.4.6 / openpyxl 3.1.5）。
- 只写 `research/2026-10-27-conditional-shift/` 与 `tmp/`；不联网、不改其它目录/源数据。

## 1. 允许读取 / 禁止读取的字段

**允许读取（元数据）**：`BARCODE`（板）、`COMBI_ID`、`Tissue`、`CELL_LINE_NAME`、`SIDM`、`COSMIC_ID`、`ANCHOR_ID`、`ANCHOR_NAME`、`ANCHOR_TARGET`、`ANCHOR_PATHWAY`、`ANCHOR_DRUG_TYPE`、`ANCHOR_Clin_Rel`、`ANCHOR_CONC`（anchor 浓度，uM）、`LIBRARY_ID`、`LIBRARY_NAME`、`LIBRARY_TARGET`、`LIBRARY_PATHWAY`、`LIBRARY_DRUG_TYPE`、`LIBRARY_Clin_Rel`、`LIBRARY_CONC`（library 最高浓度，uM）。

**禁止读取数值（DENY）**：`ANCHOR_VIABILITY`、`LIBRARY_RMSE`、`LIBRARY_EMAX`、`LIBRARY_XMID`、`LIBRARY_XMID_uM`、`LIBRARY_AUC`、`LIBRARY_fAUC`、`SYNERGY_RMSE`、`SYNERGY_EXP_EMAX`、`SYNERGY_OBS_EMAX`、`SYNERGY_DELTA_EMAX`、`SYNERGY_XMID`、`SYNERGY_XMID_uM`、`SYNERGY_DELTA_XMID`、`SYNERGY_DELTA_XMID_uM`、`SYNERGY_EXP_AUC`、`SYNERGY_OBS_AUC`、`SYNERGY_EXP_fAUC`、`SYNERGY_OBS_fAUC`、`SYNERGY_DELTA_AUC`、`SYNERGY_DELTA_fAUC`、`Synergy`、`DAY1_NORM_MEAN`、`DAY1_NORM_SD`、`GROWTH_RATE`、`DOUBLING_TIME`。

**唯一允许的存在性访问**：对端点列允许 `isna()` 二元存在性计数（仅行数/比例），用于确认端点结构可用性与匹配后单元是否缺端点；**不转换、不比较大小、不聚合、不写出任何响应数值**。匹配/筛选/分层绝不使用响应值（响应盲匹配）。

## 2. 身份归一与碰撞

- 细胞与药物（名称）归一：NFKC → casefold → 只保留 Unicode 字母数字（沿用 prior 口径）。药物身份主键优先用整数 `ANCHOR_ID`/`LIBRARY_ID` 字符串，名称仅作标签。
- 多对一碰撞：同一归一名对应 ≥2 个 casefold 后不同的原始名 → 逐条列出；**主计数保守剔除**该键（不参与严格匹配），宽松候选（不剔碰撞 + 别名合并）只作为敏感性计数，不证明同一实体。
- 复合值行：`ANCHOR_ID`/`LIBRARY_ID`/`ANCHOR_CONC` 含 `|` 的行是畸形合并值（多个值拼接），**剔除**并在报告中计数；不猜测其含义。
- 缺失：身份/剂量元数据任一缺失的行剔除并计数。

## 3. "组合条件"定义（metadata-only）

一个**组合条件** C =（有向药对 `ANCHOR_ID → LIBRARY_ID`，`ANCHOR_CONC`，`LIBRARY_CONC`）：
- 方向：表结构固定 anchor（主药）→ library（库药）；同一条记录内方向唯一，**不把 anchor/library 互换视为同一条件**；
- 剂量布局标识：`ANCHOR_CONC`（anchor 浓度，uM）+ `LIBRARY_CONC`（library 最高使用浓度，uM）。二者相同才视为"同一剂量布局"（可验证等价；完整 library 浓度点数集在拟合表中不可得，见 §8 局限）；
- 端点：`SYNERGY_DELTA_EMAX`（与 C130 ΔEMAX 一致优先）；匹配条件要求四键端点同一列且存在（isna 检查）；
- cell×condition 键 =（归一细胞名，条件 C）。同一键在一个 measurement group 内可有多行（不同 `BARCODE` = 不同板/重复测量）；A0 只按存在性与重复板数计数，不读取任何响应。

## 4. 独立测量组（pre-registered）

- **主组**：G1 = Original screen 文件；G2 = Validation screen 文件（两次独立筛，板 barcode 互不重叠；本审计验证 barcode 交集与文件身份）。
- 一个条件 C 在组内"可用"当且仅当该 cell×condition 键在组内 ≥1 行且端点列存在。
- **复验单元（匹配四元组）**：Q 需要的四个 cell×condition 键在**两个组都可用**。
- **次级（敏感性）独立组**：Original 内部按板 barcode 拆分：对每个 cell×condition 键，按其不同 barcode 升序排序，A 组 = 前 ⌈n/2⌉ 个，B 组 = 其余；键需 ≥2 个不同 barcode 才能同时存在于两组。注意：拟合表不含板日期/批次，板级重复的独立性弱于跨 screen（A1 报告中须写明）。
- 不假设 Validation 的完整 library 浓度点集与 Original 相同；只按 §3 的设计列匹配，残留不一致计入 §8 局限。

## 5. 匹配四元组（冻结定义）

对细胞 c≠c'、组合条件 p≠q，四元组 = { (c,p),(c,q),(c',p),(c',q) }。**主定义（Q 单元）**：

- M1 **四键齐全**：四个 cell×condition 键在每个被使用的独立测量组都必须可用（对照复验要求两主组均可；单组报告要求该组可用）；
- M2 **同条件匹配**：对 p（及 q）而言，它在四个键中的条件元组相同——同一有向药对、同一 `ANCHOR_CONC`、同一 `LIBRARY_CONC`（即方向/剂量布局匹配）；c 与 c' 的测量条件因此可比；
- M3 **药对不同**：p 与 q 的**无序药对**（drug id 集合）不同（同一无序药对的两个方向/两个剂量布局不算不同药对，不计入）；
- M4 **端点同一且可用**：四键端点均为 `SYNERGY_DELTA_EMAX` 且存在（isna 检查）；
- M5 **细胞不同**：c≠c'（归一细胞名不同）；细胞可来自同一或不同 Tissue。
- p 与 q 之间**不要求**共享 anchor/library（主定义是宽定义：任何两个不同药对）；报告分层：
  - `controlled_anchor`：p、q 同 `ANCHOR_ID`、同 `ANCHOR_CONC`、同 `LIBRARY_CONC`、不同 `LIBRARY_ID`（仅 library 不同的受控对比）；
  - `same_anchor_any_conc`：同 `ANCHOR_ID`（浓度可不同）；
  - `same_library`：同 `LIBRARY_ID`（不同 anchor）；
  - `disjoint_pairs`：p、q 不共享任何 drug id；
  - `same_tissue` / `cross_tissue`。

**计数口径**：
- "原始"= 行数（含重复板）与去重后 cell×condition 键数分层报告；
- "去重后四元组"= 以唯一 (cell,condition) 键构造、每个 (c,c',p,q) 只计一次（默认去重口径，主计数）；
- "重复板加权"仅作描述（同一键多板不重复计入四元组）；
- 单组四元组（G1-only、G2-only）与两主组共同四元组分别报告；
- **半匹配（3/4）**：四键中恰有 3 个键在两主组均可用、第 4 键仅单组可用的 (c,c',p,q) 数量；同时报告 2/4、1/4 数量。
- 去重/分层计数全部为组合计数（cell-pair × condition-pair 的类别对），不依赖响应值。

## 6. 资格门槛（先验冻结；不做事后调整）

`matching_qualified` 需要**同时**满足：

1. **主门槛**：两主组共同匹配四元组数 **R4 ≥ 500**（BRIEF 建议 500；本协议冻结采用 500。MDE 备注：500 单元在 iid、双尾 α=.05 下对 Spearman ρ≈0.125 有约 80% 功效；聚类/重复会降低有效 n，故 500 为下限而非充分功效保证——A1 必须按聚类报 MDE）；
2. **独立测量组 ≥2**：G1 与 G2 为互不重叠板的两次独立筛（barcode 交集为空且文件独立），且**各自**可独立构成 ≥500 个单组匹配四元组（同一宽定义）；
3. **覆盖下限**：R4 四元组涉及 ≥10 个不同细胞、≥10 个不同有向药对（低于此视为结构退化；BRIEF 只要求"可报告"，此处额外写死为资格下限，理由：Q 是异质细胞×药对交互量，单细胞/单药对无法区分细胞条件结构与个体噪声）；
4. **端点可用**：四键的 `SYNERGY_DELTA_EMAX` 均存在（isna=0；只做存在性计数）。

另报告（不单独否决）：各组单组四元组数、R3/R2 半匹配、分层计数、每细胞/每药对参与度、Tissue 覆盖、重复板结构、barcode/板独立性。若 §1 门槛不满足 → `matching_not_qualified`，列失败项与所需测量规格并停（不做可迁移条件结构主张）。

## 7. 可估性/混杂清单（报告项，不构成额外门槛）

- 2×2 最小闭环：一个匹配四元组恰是 cell×condition 二分图中的 4-回路；**树状子图不能识别非可加性**（任意边值可被加性项吸收），回路数=四元组数；报告每细胞/每药对的回路参与度。
- 单药参照：拟合表有单药拟合列（`ANCHOR_VIABILITY`、`LIBRARY_EMAX` 等）但数值属 DENY，本任务不读；只报告其列存在性（H193b 的 adjusted Q 需这些列，但属 A1）。
- 批次/板：Original 同键多板（barcode）结构、Original/Validation 板 barcode 范围与交集、每组内板数；批次与"独立测量组"身份在跨 screen 设计下不可完全分离（报告）。
- 剂量：`ANCHOR_CONC` 水平数、`LIBRARY_CONC` 每 library 值数、Original vs Validation 剂量水平集合差异；full library 浓度点集在拟合表中不可得（报告为不可验证）。
- 细胞/组织：Tissue 分布；同组织 vs 跨组织四元组数。
- 端点：多个 Δ 端点列的列存在性与 isna 计数（只存在性，不读值）；主端点选择冻结为 `SYNERGY_DELTA_EMAX`。

## 8. 产物、确定性、局限

- 产物（写入 `research/2026-10-27-conditional-shift/`）：`PROTOCOL_A0.md`、`a0.py`、`a0.json`、`matched_conditions.csv`、`matched_quadruples.csv`（若 R4 > 200,000 行，按冻结规则写**按字典序前 200,000 行**的确定性审计子集，完整计数在 a0.json；A1 可用同一代码重生成全表）、`Glossary` 引用、`report.md`、`record.md`、`usage.json`。
- 确定性：输入/脚本/协议 SHA256 记录；JSON 键排序、无时间戳、无随机数；CSV 行序确定（cell 对、条件对字典序）。
- 局限（预先声明）：(a) 拟合表只提供 `LIBRARY_CONC` 最高浓度，不提供完整 library 浓度点集，剂量布局等价只在设计列层面验证；(b) Validation 无对应 raw 板布局文件，跨 screen 的孔级布局一致性不可验证；(c) Original 重复板缺少日期/批次元数据，板级重复独立性弱；(d) 归一/ID 匹配是文本/ID 匹配，不证明生物学同一实体；(e) Q 的可估性不等于 Q 的稳定性/可迁移性——后者是 A1 的问题；(f) 本审计不读响应值，故不能报告响应缺失以外的端点质量。

## 9. 明确不做

不读响应数值、不估计 Q/效应/相关/预测性能、不做 A1 分析、不按响应挑单位/挑切分、不做机制或临床推断、不联网、不改源数据或其它研究目录。
