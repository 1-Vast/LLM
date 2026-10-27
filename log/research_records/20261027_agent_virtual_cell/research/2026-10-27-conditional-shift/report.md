# R193-A0 条件偏移匹配资格审计报告（Jaaks Original / Validation）

2026-10-27。角色：A0 匹配资格审计员（独立；不做效果分析、不估 Q）。本报告只回答**匹配资格**：现有 Jaaks 组合筛测量中是否存在足够、可复验的**匹配四元组**（c,c' × p,q），使 `Q=(y[c,p]−y[c,q])−(y[c',p]−y[c',q])` 的条件偏移复验（H193a）可进入 A1 分析协议。**本轮不读响应数值、不估 Q、不做任何效应/相关/预测计算。**

- 冻结协议：[PROTOCOL_A0.md](PROTOCOL_A0.md)（SHA256 `D77316ED9983D803D0671EF0C7D51F58BCDD439CFCCF253110BEA9B19539AA93`）
- 代码：[a0.py](a0.py)（SHA256 `444E939CDDD2F2DBDAD805C298F73B89A538320CE1A4A6C2E7037C8CB66C3525`）
- 结果：[a0.json](a0.json)（SHA256 `72BBAF6DF9BF80BBD19BF946A8D7A369003861FF21BD95561BC6DA48021ECA22`）
- 匹配表：[matched_conditions.csv](matched_conditions.csv)（9,154 行；SHA256 `73FD5085A7586BB1F33768E34A587668953DA4C13735693DCF2FCCCBC51353FF`）、[matched_quadruples.csv](matched_quadruples.csv)（200,000 行审计子集，见 §3；SHA256 `881A0DFC62A7D70DE158F5795AE1F2766E8EA1091BF6ED4F7280BA4A8211CCF9`）
- 过程记录：[record.md](record.md)；运行时账：[usage.json](usage.json)
- 输入（只读）：Original fitted `1188968CE7FDCFB66D03791CF266515B7C7A2794E1FC73C966DBA40266FFA278`（198,893,607 B）、Validation fitted `DCBD4C3108D212FA771C52AE977C8E1C01A421162A2232CDC4273FAF257B2775`（11,774,397 B）、Glossary `E29D8D2DCCF230CE5E17B530C1A012389659142FDF78AE20C55B20A4C34619CE`（12,193 B）。

## 0. 判定

**`matching_qualified`** —— 冻结门槛（PROTOCOL_A0 §6）全部通过：

| 门槛 | 要求 | 实测 | 判定 |
|---|---|---|---|
| 主门槛：两独立组共同匹配四元组 R4 | ≥500 | **6,223,367** | 通过 |
| 独立测量组 ≥2 | 两组互不重叠板、各自可独立构成 ≥500 四元组 | Original vs Validation：**barcode 交集 0**；G1-only 4,415,971,041；G2-only 7,301,337 | 通过 |
| 覆盖下限 | ≥10 细胞、≥10 有向药对 | **96 细胞 / 98 有向药对**（291 条件、31 anchor、38 library） | 通过 |
| 端点可用 | 四键 `SYNERGY_DELTA_EMAX` 均存在 | 两文件四个 Δ 端点列 **0 空值 / 全部行**（仅存在性计数） | 通过 |

**边界声明（必须随判定一起引用）**：**匹配合格 ≠ Q 稳定或可迁移**。本判定只说明 H193a 所需的匹配结构在现有测量中"存在且非退化"；Q 是否可复验、是否超出平均效应、是否被单药/批次解释，全部属于 A0 之后冻结的 A1 协议，本轮不做任何此类主张。

## 1. 方法与纪律

- 只读 Original/Validation 的**元数据列**（身份、药对、方向、`ANCHOR_CONC`/`LIBRARY_CONC` 剂量设计、screen/板 barcode）与 Glossary（数据字典）文本。
- **响应盲**：`SYNERGY_*`、`LIBRARY_*`、`ANCHOR_VIABILITY`、`Synergy`、`DAY1_NORM_*`、`GROWTH_RATE`、`DOUBLING_TIME` 等 26 个响应/派生列**从未被读取为数值**；端点可用性用流式 csv 的**空串存在性检查**得到（不解析、不转换、不聚合），输出仅"空值行数=0"这类结构信息。
- 匹配/筛选/分层只使用身份、方向、剂量设计列、screen/板标识与端点存在性；未用任何响应值挑单位。
- 归一：NFKC → casefold → 仅保留字母数字；药物身份用整数 `ANCHOR_ID`/`LIBRARY_ID`，名称仅作标签。碰撞：细胞名在并集上**无碰撞**；药名有 1 个归一碰撞（`Afatinib | Trametinib` vs `Afatinib|Trametinib`，均为元数据标签，不影响以 ID 为准的匹配）。
- 排除：`ANCHOR_ID`/`LIBRARY_ID`/`ANCHOR_CONC` 含 `|` 的畸形合并行（Original 5,527 / Validation 158 行，如 `1032|1372`、`0.125|0.003`）剔除并计数，不猜测其含义；无身份/设计缺失行；两文件端点无缺失。
- 确定性：JSON 键排序、无时间戳、无随机抽样；连续两跑 a0.json 与两份 CSV 的 SHA256 逐字节相同。

## 2. 实测结构（原始/去重分层）

| 指标 | Original screen | Validation screen |
|---|---|---|
| 总行数 | 296,707 | 23,505 |
| 剔除畸形合并行 | 5,527 | 158 |
| 有效行 | **291,180** | **23,347** |
| 细胞 | 125（Breast/Colon/Pancreas） | 97（同三组织） |
| 有向药对（anchor→library） | 1,975 | 130 |
| 无序药对 | 1,269 | 98 |
| 组合条件（有向药对+`ANCHOR_CONC`+`LIBRARY_CONC`） | 4,528 | 295 |
| 板 barcode | 3,106 | 454 |
| 每细胞条件数（min/median/max） | 576 / 1,299 / 2,550 | 76 / 102 / 118 |
| cell×condition 唯一键 | 211,504 | 9,649 |
| 单板键 / ≥2 板键 | 180,485 / **31,019** | 211 / **9,438** |
| 端点空值（4 个 Δ 端点，存在性） | 0 | 0 |

- **组合条件定义（冻结）**：有向药对 `ANCHOR_ID → LIBRARY_ID`（方向固定，不做 anchor/library 互换）+ `ANCHOR_CONC`（uM）+ `LIBRARY_CONC`（library 最高浓度，uM）；四元组要求每条键使用同一条件元组，从而方向与已发布剂量设计列匹配。
- **原始 vs 去重**：原始行含同一 cell×condition 键在多个 barcode（重复板）上的多次测量；去重口径以唯一 cell×condition 键构造四元组，每个 (c,c',p,q) 只计一次（主计数）。Original 重复板结构：键的 barcode 数 1→180,485、2→10,940、3→8,053、4→8,501、…、10→1,357。

## 3. 匹配四元组计数（冻结定义）

定义（PROTOCOL_A0 §5）：四元组 = 两细胞 c≠c'、两条件 p≠q，四键 (c,p),(c,q),(c',p),(c',q) 在指定测量组均可用；对每个条件，其在四键中的方向与剂量设计元组相同；p、q **无序药对**不同；端点为同一 `SYNERGY_DELTA_EMAX` 且存在。

| 计数 | 数值 | 说明 |
|---|---|---|
| **R4（主，Original∩Validation 共同）** | **6,223,367** | 四键在两主组均可用；H193a 的 Q 复验单元 |
| R3（半匹配：恰 3 键双组可用，第 4 键单组可用） | **802,445** | 备选设计，主张强度降低 |
| 复制水平分布（四键在不同组数，level=双组可用键数） | R0 4,034,637,772；R1 177,515,510；R2 214,664,684；R3 802,445；**R4 6,223,367** | 四键至少单组可用的全部单元 |
| G1-only 四元组（Original 内可算） | 4,415,971,041 | 单组可算；受全部 125 细胞覆盖 |
| G2-only 四元组（Validation 内可算） | 7,301,337 | 单组可算；97 细胞 |
| barcode 分半次级 R4（Original 内，键需 ≥2 barcode） | **43,208,857** | 31,019 个键参与；A/B 按排序后 barcode 前 ⌈n/2⌉/其余确定分半 |

- R4 分层（6,223,367 内，按条件关系）：`controlled_anchor`（同 anchor+同 anchor 浓度+同 library 最高浓度、仅 library 不同）**92,039**；`same_anchor_any_conc` 568,029；`same_library` 309,351；`disjoint_pairs`（不共享任何药物）5,345,987；`same_tissue` 6,217,553 / `cross_tissue` **5,814**。
- R4 覆盖：**96 细胞**（Breast 33 / Colon 35 / Pancreas 28）、**291 条件**、**98 有向药对**、31 anchor、38 library；参与细胞对 3,418（共 4,560 对）。
- 参与度：细胞 degree min 33,814 / median 128,333 / max 165,672；有向药对 degree min 39,733 / median 90,997 / max 353,268；参与度最高的药对 `1022:1073`（353,268）、`1053:1564`（339,018）、`1011:1372`（334,197）；最高 anchor `1011`（2,020,200）、最高 library `1053`（1,241,403）。
- **CSV 说明（冻结规则）**：R4 = 6.22M > 上限 200,000，`matched_quadruples.csv` 为按 (cell_a,cell_b,条件元组) 字典序的**前 200,000 行确定性审计子集**（a0.json 记录完整计数；A1 可用同一代码重生成全表）。`matched_conditions.csv` 是全部 9,154 个双组可用的 (cell, condition) 键表（含每文件行数/barcode 数），可直接用于 A1 重建四元组。

> 重要解释：6.22M 是从 9,154 个 cell×condition 键组合出的**高度嵌套/冗余**计数（同一键出现在许多四元组中）；有效独立单位远小于 6.22M（96 细胞 × 98 药对 × 291 条件）。A1 必须按细胞/药对聚类，并按聚类报告 MDE，不能把 6.22M 当独立样本量。

## 4. 两组独立测量与覆盖

- **主独立组**：G1 = Original screen 文件（3,106 板，barcode 14,482–39,392）；G2 = Validation screen 文件（454 板，barcode 33,044–63,257）。**barcode 集合交集 = 0**（不同板），是两次独立筛；G2 是对 98 个无序药对、96 个细胞的独立复测。
- **共同测量结构**：细胞 96/97（原 125）；有向药对 130/130（Validation 的 130 个全部出现在 Original）；cell×condition 键 Original 211,504 / Validation 9,649 / **共同 9,154（=Validation 键的 94.87%）**。即 Validation 的绝大多数测量都能在 Original 中找到方向+剂量设计列一致的对应测量。
- **次级独立组**（敏感性/备选）：Original 内按板 barcode 分半（每键 ≥2 板才可分），31,019 键满足；barcode-split R4 = 43,208,857。该分半在拟合表中**没有板日期/批次信息**，独立性弱于跨 screen（见 §5 局限）。
- **剂量可比性（只到已发布设计列）**：Anchor 浓度水平 Original 26 个 / Validation 20 个，**共同 20 个**；`LIBRARY_CONC` 水平 12 / 11，**共同 10 个**；共同键中 127 个有向药对存在多个共同设计元组（多 anchor 浓度/多最高浓度布局）。**拟合表不发布完整 library 浓度点集，且本机没有 Validation raw 板布局文件** → "同一 library 剂量集"只能在已发布设计列层面验证，不能验证孔级完整剂量点等价。

## 5. 可估性 / 混杂清单

- **树/回路**：匹配四元组正是 cell×condition 二分图中的 4-回路（2×2 最小闭环）。Q 非可加性只有在回路存在时可识别；树状子图（单细胞内跨多对）只能估加性项，不能检验条件偏移。匹配复制子图：**节点 387（96 细胞 + 291 条件）、边 9,154 cell×condition 键、4-回路 6,223,367**。若只允许单细胞内跨对设计（BRIEF 的备用形态），则只能称"条件稳定性"，不能称"可迁移"——本审计主计数不采用该退路。
- **单药参照与 A1**：拟合表存在单药拟合列（`ANCHOR_VIABILITY`、`LIBRARY_EMAX/XMID/AUC/fAUC`），但按 A0 协议其**数值 DENY、本轮未读**。H193b 的 adjusted Q（扣细胞×单药效应）需要这些单药读数 → **A1 协议必须显式允许读取并冻结其使用规则**，否则 H193b 不可执行。
- **批次与 screen 混淆**：Original 与 Validation 是不同 screen/不同板/不同时间，**"独立测量组"身份与实验批次完全混淆**，无法把"跨 screen 不一致"分解为批次效应或真实条件不稳定。因此 A1 只能主张"跨 screen 条件稳定性"，不能主张纯 test–retest 可迁移性。
- **剂量布局**：见 §4 —— 拟合表只给 `ANCHOR_CONC` 与 `LIBRARY_CONC`（最高浓度），完整 library 浓度点数集不可得；Original 重复板无日期/批次元数据。
- **同组织/跨组织**：匹配四元组几乎全部是**同 Tissue 细胞对**（6,217,553 vs 跨组织 5,814）——各组织项目的 anchor 浓度/library 布局不同，跨组织匹配条件稀少。A1 的细胞条件结论实际上主要在**同组织内**可检验；跨组织迁移是另一个（数据不足的）问题。
- **归一/身份**：文本/ID 匹配不证明生物学同一实体；`Afatinib | Trametinib` 药名碰撞仅标签层，不影响 ID 匹配。

## 6. MDE 说明（门槛为下限，不是功效保证）

冻结门槛 500 来自 BRIEF 默认值并在 PROTOCOL_A0 §6 预先写死（未按实测调整）。说明：iid 情形下 n=500 对 Spearman ρ≈0.125 约 80% 功效（双尾 α=.05）；但匹配四元组按细胞/药对高度聚类，**有效 n 远低于名义计数**，故 500 只是**下限**。A1 必须在冻结协议中按细胞/药对（及可能的 screen）聚类 bootstrap，报告 **MDE80 与 CI 下界**，并以"最小有用条件偏移 δ_min"而不是本门槛反推结论。本审计不验证端点噪声/效应量。

## 7. 判定与后续所需

- **判定：`matching_qualified`**（失败项：无）。主门槛实测超门槛 4 个数量级，且两组独立、覆盖充分。
- **A1 必须继承的边界**：(a) 只主张跨 screen 条件稳定性（批次混淆）；(b) 剂量匹配只到已发布设计列；(c) 单药参照需 A1 显式解禁；(d) 按细胞/药对聚类、报 MDE；(e) 不得用本审计的匹配资格推断 Q 的存在、方向或大小。
- 若未来要升级为主张更强（纯 test–retest、孔级剂量等价、跨组织迁移），需要的测量规格是：Validation 的 raw 板布局文件（孔级浓度）、板日期/批次元数据、或专门设计的同条件重复筛（同批次内）、以及跨组织共享的剂量布局。

## 8. 复现与产物

```powershell
cd D:\MAESTRO
& D:\anaconda\envs\maestro\python.exe research\2026-10-27-conditional-shift\a0.py
```

- 只读、确定性：连续两跑 `a0.json` / `matched_conditions.csv` / `matched_quadruples.csv` SHA256 逐字节相同；JSON 键排序、无时间戳；输入与脚本/协议 SHA256 均记录于 a0.json。
- 实测耗时：约 26–35 s（pandas 元数据读入 + 端点存在性流式扫描 + 组合计数 + CSV 写出）；单命令远低于 15 分钟上限。
- 响应保护：响应列从未被读取为数值；输出仅含计数/标识/设计列/派生比率，无任何响应数值（`a0.json` 仅记录端点"空值行数=0"这类存在性信息）。

## 9. 局限

- 元数据匹配审计，不读响应值、不估 Q；"匹配合格"不等于 Q 稳定/可迁移/非混杂。
- 拟合表只发布 `ANCHOR_CONC` 与 `LIBRARY_CONC`（最高浓度），完整 library 浓度点集不可得；本机无 Validation raw 布局，无法验证孔级剂量一致。
- Original 重复板缺日期/批次 → barcode 分半独立性弱于跨 screen；本文以跨 screen 为主独立组。
- 匹配四元组计数高度冗余（嵌套），不是独立样本量；A1 必须聚类。
- 文本/ID 归一匹配不证明生物学同一实体；未联网、未引入外部 ID 库。
- 匹配四元组全部来自 Validation 所覆盖的 98 个无序药对（130 有向）与 96 个细胞——结论的**可迁移范围**受该子集限制，不等于整个 1,975 对有向药对/125 细胞宇宙。
