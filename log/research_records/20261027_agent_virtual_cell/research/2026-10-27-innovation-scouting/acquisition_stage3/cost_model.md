# R198-A5 成本模型：取证菜单的物理量 + 规划成本单位（planning only）

2026-10-27。配套 [spec.md](spec.md)。**本文件不含任何 acquisition 运行或效果数字**；所有数字来自：(a) 已发表设计的**物理锚点**（wells/plates/浓度设计，逐条给源）；(b) 本目录 `tmp/a5_cost_arithmetic.py` 的**确定性算术**（输入=锚点+规划系数，输出=wells/plates/batches/cost units）。**成本系数不是货币实测**：必须先由真实报价/LOI 替换后才能作为预算冻结（见 §7 冻结清单）。

## 0. 三个原则（写死）

1. **先物理量，后成本单位**：先按设计算 wells（combo/单药参照/对照/失败/重复），再把 wells 映射到 "cost units (CU = 1 informative well-equivalent)"；CU 只是比较尺度，**不是货币**。
2. **成本 ≠ 检定力**：成本回答"买多少物理测量"；检定力回答"这些测量在什么聚类结构下能分辨多大决策效应"（C136/C144/C154/C171 的教训）。两者分开报告，见 §6。
3. **等成本不是等行数**：比较必须在 **total CU** 上等（§5 的核查算法），同时报告 wells/plates/keys/cells/batches 与有效独立单元；**禁止**用"同行数/同 wells/同 keys"冒充等成本。

## 1. 物理锚点（全部有出处；不含推断的成本）

| 锚点 | 值 | 出处（一手/实测） |
|---|---|---|
| GDSC/Jaaks 组合板格式 | **1,536-well** | Jaaks 2022 Methods：`Screening Cells were transferred into 1,536-well plates in 7.5 μl ...`（R191-PB 已核对的 `jaaks_primary_lineage.body`） |
| 每个 (cell, anchor-library) 组合块 | **2 anchor 浓度 × 7 library 剂量 = 14 combo wells** | Jaaks Methods："2 × 7 concentration matrix, or 'anchored' approach" |
| anchor-alone / library-alone | 每板 **5 份 anchor-alone（两浓度）** + **4 份 library-alone（全 dose response）** | Jaaks Methods："Each screening plate contained five replicates of the anchor alone (high and low concentrations) and four replicates of the library alone (full dose response). A single replicate of the combination dose response was performed in the primary screen." |
| 对照/QC | 每板含阴性 DMSO、阳性（MG-132/staurosporine）、blank；QC 阈值 DMSO CV<0.18、Z-factor>0.3、RMSE<0.2（排除 ~1.5% 测量） | Jaaks Methods / 图 2；R191-PB 来源 |
| 播种密度优化（每新细胞） | 6 个密度 × 224 wells = **1,344 wells**（1 张 1,536 板） | Jaaks Methods |
| day=1 无药对照板 | **1,536 wells**（每次 cell-line screen 重复） | Jaaks Methods："a parallel undrugged control plate ... referred to as a 'day = 1' plate ... repeated each time that a cell line was screened" |
| 生物重复 | n=2–18（中位 4，仅部分 tuple） | Jaaks 图 2 / Methods |
| BATCHIE PAIR 屏格式 | **384-well**；206 药（210 库槽）；14 row plates × 10 column plates | R2 数据映射（`data_mapping.md`）+ BATCHIE 论文设计段 |
| R2 合法动作实测 | **2 张物理板 / 766 条原始 well 记录**（含控制与失败） | R2 report §2；`baseline_action_metrics.csv`（每 cell 12/3/3/6/6 个候选动作） |
| DrugComb 块设计 | 2×2, 3×3, 4×4, 4×6, 5×5, 6×6, 10×10（不同 study） | R191-PB：S1 study 表 + v1.4 summary（466,033 组合块）；v1.5 751,498 块 |
| BeatAML 单药设计 | 7×1（每 cell×drug 7 个单药 well）；528 细胞 | R191-PB/NAR2021 S1 表 |
| C136 前瞻验证规模 | **约 1,600 个 cell×pair 测量 = 80% 检定力**（200 个时 power≈0.46）；1,600 ≈ 13 药对 × 125 细胞 | SYNTHESIS C136（R169 report/record） |
| C144 预算分配 | 固定 ~1,000 keys；28×36 / 50×20 / 68×15 的 power 0.67/0.74/0.70（非单调，总量驱动） | SYNTHESIS C144 |
| C154/R187 饱和 | 补 50 对（≈1,835 行）只让增益动 ±0.003；pair-level uncertainty vs random −0.0040 [−0.0127,+0.0054]，MDE 0.0142 | SYNTHESIS C154；R187 report |
| R2 菜单头空间 | static −0.005547 / oracle −0.001205 → **residual regret 0.004343**；KG−random +0.0019 [−0.0811,+0.0636] | R2 report §3 |

## 2. 动作的物理换算（wells；per 1 action）

| 动作 | combo wells | 单药参照 wells | 对照 wells | 合计 wells（低–高） |
|---|---|---|---|---|
| A2 anchored key（2×7） | 14 | 12–38 | 8–16 | **34–68** |
| A3 dose grid 6×6 | 36 | 12–24 | 8–16 | **56–76** |
| A3 dose grid 10×10 | 100 | 20–40 | 8–16 | **128–156** |
| A4 single-dose key（复用历史单药） | 1 | 0（复用） | 0–2 | **1–3** |
| A4 single-dose key（买新单药参照） | 1 | 14 | 2–4 | **17–19** |
| A1 BATCHIE 整板动作（R2 实测） | ~700 | 40–60 | 6–10 | **746–770**（实测 766） |
| A5 BeatAML mono key（7×1） | 0 | 7 | 2–4 | **9–11** |
| A7 新细胞 setup（固定） | — | — | — | **2,880**（1,344 播种 + 1,536 day1），另加 1,344/1,536 的两次 QC 读出 |

## 3. 规划成本场景（CU；系数不是货币）

`CU = c_well × [paid_informative_wells + paid_setup_wells] + plate_equiv × c_well × plates + batch_equiv × c_well × batches`

- `paid_informative_wells = informative_wells × replicates / (1 − fail_frac)`（重复与失败孔都付费，不增加信息）
- `paid_setup_wells = 125 cells × 2,880 / (1 − fail_frac)`（新细胞 setup；可声明为 sunk，见 §4）
- 打包规则（冻结）：动作按 cell→pair→dose 顺序装入其格式的板（利用率 `eta`）；每批 ≤ **10 板**；批固定成本按批计。

| 系数 | optimistic | central | conservative | 依据/说明 |
|---|---|---|---|---|
| c_well（CU/well） | 0.5 | 1.0 | 2.0 | 试剂/耗材/化合物/细胞/读出的规划区间；**非实测** |
| plate_equiv（well-equivalents/plate） | 20 | 60 | 200 | 板/上机/耗材的固定折价；**非实测** |
| batch_equiv（well-equivalents/batch） | 50 | 200 | 500 | 培养/仪器/QC/人工的批次固定成本；**非实测** |
| eta（板利用率） | 1.00 | 0.60 | 0.25 | 小动作打不满板；未知设计真实利用率 → 区间 |
| fail_frac（失败/排除比例） | 0.00 | 0.015 | 0.05 | GDSC QC 排除 ~1.5%；BATCHIE QC 失败门 |
| replicates（技术/生效重复倍数） | 1 | 2 | 3 | primary 单份；确认重复 2 份；上界 3 份 |

**每动作 CU（cells=0，不含新细胞 setup）**：

| 动作 | optimistic | **central** | conservative |
|---|---|---|---|
| anchored key（2×7） | 60.5 | **363.6** | 1,722.1 |
| dose grid 6×6 | 68.0 | **394.0** | 1,816.8 |
| dose grid 10×10 | 106.0 | **548.3** | 2,296.8 |
| single-dose key（复用单药） | 36.0 | **264.1** | 1,412.6 |
| single-dose key（新单药参照） | 44.0 | **296.5** | 1,513.7 |
| BATCHIE 整板动作（R2 式） | 424.0 | **1,979.1** | 8,987.4 |
| BeatAML mono key（7×1） | 40.0 | **280.3** | 1,463.2 |

## 4. C136 规模（1,600 cell×pair keys ≈ 13 对 × 125 细胞）的规划成本

| 采集路径 | 1,600 keys 的 wells | central CU（cell setup 计入） | central CU（setup 视为 sunk） | optimistic / conservative（setup 计入） |
|---|---|---|---|---|
| anchored 2×7（每 key 一块） | 81,600 | **569,568** | **172,825** | 224,415 / 1,849,663 |
| dose grid 6×6（每 key 一块） | 105,600 | **620,458** | **223,716** | 236,615 / 2,032,042 |
| single-dose key（复用单药参照） | 3,200 | **404,480** | **7,737** | 184,665 / 1,264,905 |
| single-dose key（新单药参照） | 28,800 | **465,379** | **68,637** | 198,275 / 1,558,989 |
| BeatAML mono key（7×1，**非组合 key**，仅端点对照） | 16,000 | 435,030 | 38,087 | 191,470 / 1,411,947 |

**关键读法（规划，不是效果）**：
1. **cell-line 广度是 125 细胞设计的支配性固定成本**：新细胞 setup（2,880 wells/cell）在 C136 规模下值 **~3.6×10^5 wells**，超过 combo+ref+control wells 本身；setup 计入 vs sunk 使同一设计的 central CU 相差 **2.5–5.2 倍**。→ 冻结时必须**写死 cell setup 的会计规则**，否则不同策略（不同 cell 广度）不可比。
2. **Key 的"类型"不同，成本不可比**：single-dose key（复用单药）central 仅 ~264 CU/次动作，但**不是** C136 意义上的 ΔEMAX cell×pair key（无剂量-反应）；把它当"便宜 key"会系统性低估端点噪声与统计成本。**成本模型必须与端点类型绑定**（§6）。
3. **整板动作昂贵但信息密集**：R2 式动作 central 1,979 CU/动作（766 wells/2 板，含控制与失败），单个动作就接近 5–20 个 anchored key 的成本；等成本比较必须按动作类型分开定价。
4. 以上未包含：化合物采购/建库（菜单只使用已有库）、独立培养认证、靶点读数（不可购买）、LLM/算力（另计入）。

## 5. 等成本设计：预算拟合与核查（冻结算法）

**输入**：预算 `B_CU`；动作类型与格式；打包规则（§3）；cell setup 会计规则（charged 或 sunk，全局一致）；成本场景（optimistic/central/conservative）。

**算法（每策略独立执行，结果哈希）**：
1. 策略产生动作序列；按打包规则装入板与批（新细胞按规则计 setup）。
2. 累计 `CU(plan)`；若不足 `B_CU`，用**预注册的补充规则**补足（例如各策略都补"固定配对 filler"直到无法再买一个最小动作），使每策略 `CU ∈ [B_CU − c_min, B_CU]`（`c_min` = 最小合法动作成本；**残余预算差 ≤ 一个最小动作**）。
3. **核查（写死）**：对每个策略输出：`{total_CU, wells, combo/ref/ctrl wells, plates, batches, new_cells, keys, cells, pairs, actions}`；要求 (a) 所有策略 total_CU 差 ≤ 一个最小动作；(b) 同一策略在三个成本场景下都可复现（plan 与 CU 计算入库）；(c) **策略排序结论在 optimistic/central/conservative 三套价格下一致**，否则判 `cost_sensitive`（不报赢家）。
4. **禁止**：等 rows/keys/wells；把"板数相同"当等成本；把 batch 固定成本摊到策略之外；只在 central 价格下选结论。

**预算拟合示例（B_CU = 100,000；central 价格；cell setup 按 charged / sunk 两种规则）**：

| 动作形状 | charged：动作数 / 细胞数 / 板数 / 批数 | sunk：动作数 / 板数 / 批数 |
|---|---|---|
| R2 式 BATCHIE 整板动作（≤5 细胞） | **46** / 5 / 168 / 17 | 55 / 181 / 19 |
| anchored key（≤125 细胞） | **277** / 22 / 85 / 9 | 923 / 52 / 6 |
| dose grid 6×6（≤125 细胞） | **256** / 20 / 82 / 9 | 713 / 52 / 6 |
| single-dose key（复用单药） | **384** / 30 / 98 / 10 | 20,985 / 183 / 19 |
| single-dose key（新单药参照） | **332** / 26 / 108 / 11 | 2,331 / 183 / 19 |

读法：**同一 100,000 CU 可以买 46 个整板动作，也可以买 20,985 个单剂量 key——形状相差 450 倍**；所以"等成本"比较必须先固定动作类型/端点类型，再比较策略；跨类型比较只能以"同一决策任务 + 同一端点"为前提（否则成本差异掩盖统计差异）。

## 6. 成本 ↔ 检定力：必须分开报告的量

| 量 | 定义 | 数据来源 | 是否成本模型决定 |
|---|---|---|---|
| `B_CU` | 预算（planning cost units） | 报价/LOI 替换系数后冻结 | 是 |
| `wells / plates / batches / cells` | 物理采购量 | 成本算术（§2–§5） | 是 |
| `keys`（cell×pair 测量数） | 端点相关测量数 | 动作类型×数量 | 是（但 key 类型必须与端点匹配） |
| `n_eff`（有效独立单元） | 细胞/药对/批次聚类后的有效样本 | 设计 + 聚类结构（C171 教训：96 细胞→n_eff≈189） | **否**（统计） |
| `MDE_decision` | 决策指标最小可检效应（80% power） | 预注册效应量 + 聚类结构 + 预算（C136 式：1,600 keys→80%；200→0.46） | **否**（统计） |
| `headroom` | 菜单 oracle − static 效用 | 离线菜单评分（R2：0.004343） | **否**（菜单属性） |
| `δ_min` | 最小有用决策差异 | 任务业务定义（预注册） | **否** |

**冻结门槛**（与 spec §7 一致）：`MDE_decision(B_CU) ≤ δ_min ≤ headroom`。写死：**不得**用 wells/keys 代替 n_eff，**不得**用全局相关系数的 MDE 代替决策指标的 MDE（R187/C154 教训），**不得**用旧 CI 下界反推 δ_min（R193 教训）。

**规划锚（不是效果）**：C136 的 1,600 keys 若用 anchored 2×7 在 125 细胞上购买，central（setup 计入）约 **5.70×10^5 CU**、sunk 约 **1.73×10^5 CU**；若预算只有 1.0×10^5 CU（central、setup 计入），可买约 **277 个 anchored keys（22 细胞）或 256 个 6×6 grids（20 细胞）**——**距离 1,600 keys 的 C136 门槛差 5.8–6.3 倍**，即"按 C136 的检定力目标，现有单轮 acquisition 预算买不起一次验证战役；这本身就是资源/设计事实，不是 acquisition 策略优劣"。

## 7. 敏感性（±50% 系数，anchored 2×7、125 细胞、1,600 keys、central 基准 569,568 CU）

| 系数（±50%） | CU 变化 | 弹性解读 |
|---|---|---|
| `c_well` | **−50.0% / +50.0%** | 主导项：wells 单价（试剂/化合物/细胞）是最大不确定性；必须优先报价校准 |
| `replicates`（1→2→3 中从 2 变 1/3） | −14.5% / +14.5% | 第二主导：重复倍数（技术 vs 生物重复须分开定价） |
| `eta`（0.6→0.3/0.9） | +6.7% / −2.2% | 板利用率：小动作打不满板时显著变贵 |
| `plate_equiv` | −2.5% / +2.5% | 板固定成本在 1,536-well 高密度路径下次要 |
| `batch_equiv` | −0.8% / +0.8% | 批次固定成本在"1,600 keys 跨很多板"时被摊薄 |
| `fail_frac`（1.5%→0.75%/2.25%） | −0.7% / +0.7% | 失败孔影响小但**必须入账**（R2 冻结"失败仍收费"） |

**single-dose（复用单药）路径的敏感性不同**：`eta` +8.0%/−2.6%、`plate_equiv` ±3.0%、`batch_equiv` ±1.0%、`replicates` ±0.8%（因为 setup 与 plate/batch 占比更高）——**不同动作形状的成本敏感性不同，不能一律用同一套 sensitivity 结论**。

## 8. 冻结前必须补齐的数（成本模型不假装已有）

1. **货币/报价**：`c_well`、`plate_equiv`、`batch_equiv` 必须由实际报价/LOI 替换（当前为 planning 区间；本文件**不提供美元数字**，因为项目没有认证的采购成本记录——R2 已明确"货币成本未认证"）。
2. **真实设计利用率 `eta`**：需从具体 study 的板布局文件核出（GDSC 每板只放 14 combo wells 的假设可能过低；DrugComb 的 2×2…10×10 布局另算）。
3. **单药参照覆盖**：复用历史 fitted 数据的匹配限制（细胞/药/剂量/端点必须匹配；R191-PB 已示 Jaaks 与 DrugComb 端点/设计不可直接混）→ 决定"复用 0 wells"是否合法。
4. **独立培养**：现有 barcode 不相交不等于独立培养（R2 数据映射）；若要求独立生物重复，`replicates` 与批次数上升，成本按 §3 重算。
5. **失败/QC 率**：GDSC ~1.5% 排除、BATCHIE "viability 差 >0.5 的孔 QC 标记"；实际菜单的失败率须由 pilot 估计。
6. **LLM/算力成本**：按预注册单位（token/CPU-hour 折算 CU）入账，不隐藏在"策略实现"里。

## 9. 限制（本成本模型不自称完整）

- 系数是**规划参数**，不是实测货币；所有 CU 数字只在相同系数下可比较。
- 动作成本随**打包/批次共享**变化，策略间比较必须用同一打包规则；板内空孔（利用率）是不可忽略的浪费项。
- 125 细胞的 C136 规模下 cell setup 支配成本；若实际细胞已可得（sunk），成本骤降——这不是"省钱技巧"，是必须冻结的会计规则。
- 成本算术不涉及端点质量；**便宜的 key 可能更差**（无剂量-反应的单剂量 key 不能替代 ΔEMAX key），故 key 类型必须与端点绑定。
- 本模型不证明任何 acquisition 策略有收益；只提供等合法预算比较的**可审计定价与核查**。

*算术脚本与输出：[tmp/a5_cost_arithmetic.py](../../../tmp/a5_cost_arithmetic.py) / [tmp/a5_cost_arithmetic.json](../../../tmp/a5_cost_arithmetic.json)（确定性、无时间戳、固定算法）。*
