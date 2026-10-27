# P-A 报告：DrugComb 药物→粗注释映射与覆盖资格审计（R191 阶段 1）

**日期**：2026-10-27 · **角色**：注释映射与覆盖审计员（独立于提案者）· **任务**：task-7
**协议**：`PROTOCOL_PA.md` v2，**2026-10-27T14:07:51 冻结**（在 `pa.py` 存在之前），SHA256 `16c40f9f61765637185bd061b1aeb4e62886bdfa027b8baf509830775bae607d`
**脚本**：`pa.py`，SHA256 `25e64208a95b0c92b126823020e361ad208e517eef95c4f093f6be835ff470f3`
**本轮范围**：只做映射与覆盖统计。**未读任何 DrugComb 响应值、未训练模型、未评估效应、未做机制/临床主张**。

---

## 判定

# `mapping_qualified`

主策略 = **S1（KEGG，186 个基因集）+ 规则 A（原始 argmax）**。4 条硬门槛与 4 项审计检查全部通过：

| 门槛 | 阈值（预注册） | 实测（主策略） | 结果 |
|---|---|---|---|
| G1 药物覆盖 | ≥25%（≥1,022 / 4,088） | **1,418 / 4,088 = 34.69%**（/4,076 = 34.79%） | ✅ PASS |
| G2 可分析水平 | ≥12 | **62**（E1 切分口径 63；水平总数 123） | ✅ PASS |
| G3 both-unseen 有注释单元 | ≥800 | **2,682**（E1 切分口径 3,739） | ✅ PASS |
| G4 训练有注释单元 | ≥5,000 | **85,436**（严格"两药均不在留出集"口径 58,788） | ✅ PASS |
| A1–A4 审计 | 输入哈希 / 非响应派生 / E1 复现 / 确定性 | 全部通过 | ✅ PASS |

**主策略覆盖 34.69%（1,418/4,088），可分析水平 62，both-unseen 有注释单元 2,682，训练单元 85,436；冻结表 SHA256 `45ede63521dc44fefec52d717765b4d2ba7d08ec3fde4372811c4d516de038d4`。**
**无失败门槛；解冻条件为空。** 但判定附带 **6 条必须带入阶段 2 的条件**（§10），其中第 1 条最关键：**阶段 2 必须先冻结切分口径**（PA 切分 vs E1 切分给出不同的 both-unseen 单元数：2,682 vs 3,739，两者都 ≥800）。

---

## 1. 执行与冻结追溯

1. 收到 task-7（revision 1）→ claim（revision 2）。
2. 只读勘察：BRIEF、R190-E1 协议/报告/`e1.json`；下载 MSigDB GMT；核对 I1–I3 表头/行数；在 `tmp/` 用原型脚本复算口径（**已在协议 §2 如实披露**，未据此改动任何规则或门槛）。
3. `PROTOCOL_PA.md` v1 写于 14:06:31（`pa.py` 尚不存在）。
4. **14:07:24 收到 Lead 补充指令**（规则 A/B + 超几何 z + 确定性选择开关；token 切分细化）→ **14:07:51 写定协议 v2**（`pa.py` 仍不存在，故不存在"看结果改规则"）；门槛数值未变。
5. 写 `pa.py`（独立实现，不复用原型脚本）→ 首次运行在 `[4/9]` 因实现 bug（数组 `sd` 与标量比较）中止（**未产生任何产物**）；修复后成功运行。
6. 修 2 处实现 bug（数组 `sd` 比较；`zmax` 赋值缺失），**均不涉及规则/门槛**；随后为 `brief_pa_diagnostic` 增加"逐库"数字（判定无关的诊断）。
7. **确定性验证**：连续两次运行，`pa.json` 与 `mapping_table.csv` 的 SHA256 完全一致（§9）；最终 `pa.json` SHA256 `f5559d26…`（Lead 独立复跑核对，见 `../2026-10-27-innovation-round-r191/record.md` §4）。

运行环境：`D:\anaconda\envs\maestro\python.exe`（Python 3.11.16；pandas 2.3.3；numpy 2.4.6；scipy 1.17.1）。`pa.py` 墙钟 21–44 s（冷/热缓存），远低于 ≤30 min 预算；不联网。

---

## 2. 输入与外部资源（全部只读；SHA256 逐条复核，7/7 ok）

| # | 输入 | 字节 | 本地 SHA256（前 16 位） | 用途 |
|---|---|---|---|---|
| I1 | DrugComb v1.4 summary（**仅身份列**） | 193,184,734 | `e08e3d35bfa4bea0` | 组合块身份、宇宙、单元 |
| I2 | DrugComb v1.5 drug identifiers | 5,856,350 | `02b1655ad15a81e0` | `dname` / `target_name` |
| I3 | Drug Repurposing Hub（skiprows=9） | 530,302 | `9c3a08b9d4369fe4` | `pert_iname` / `target` |
| I4 | MSigDB **S1 KEGG** 2023.1.Hs symbols GMT | 100,047 | `48de51190366ee38` | 186 基因集 |
| I5 | MSigDB **S2 Hallmark** 2023.1.Hs symbols GMT | 48,649 | `27e48f776cda235a` | 50 基因集 |
| I6 | Jaaks GDSC Original fitted（仅 4 列） | 198,893,607 | `1188968ce7fdcfb6` | 通路模板对照 |
| I7 | Jaaks GDSC Validation fitted（仅 4 列） | 11,774,397 | `dcbd4c3108d212fa` | 通路模板对照 |

**外部资源来源/版本**（下载 ≤ 50 MB 预算，实际 148,696 B）：
- S1：`https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2023.1.Hs/c2.cp.kegg.v2023.1.Hs.symbols.gmt`（MSigDB release **2023.1.Hs**，KEGG legacy gene sets，186 集）
- S2：`https://data.broadinstitute.org/gsea-msigdb/msigdb/release/2023.1.Hs/h.all.v2023.1.Hs.symbols.gmt`（MSigDB release **2023.1.Hs**，Hallmark，50 集）

**v1.4 身份审计（与 R190/E1 逐项一致）**：1,175,220 行；单药-like 709,187；**组合块 466,033**；归一药 **U = 4,088**；C155 碰撞键 12（D1 = 4,076）；细胞 112；无序药对 62,826；**cell×pair 单元 380,418**；E1 切分（k=818, step=4）的全体 both-unseen 单元 **16,078**（= R190 精确值）。12 个碰撞键全部逐条列在 `pa.json`（多为连字符/空格写法差异，如 `bibr1532` ← `BIBR 1532`/`BIBR-1532`；也有对映体前缀差异，如 `blebbistatin` ← `(+)-Blebbistatin`/`(-)-BLEBBISTATIN`）。

**靶点注释来源规模**：I2 `target_name` 非空 4,442/8,396（52.91%）；I3 `target` 非空 4,382/6,798。**合并后有 token 的 D1 药 2,367 个；token 总数 2,802；其中精确等于基因符号的 token 1,012（36.1%）；D1 中拥有 ≥1 个精确基因符号的药 = 1,572。** 来源归属（D1，有 token 的 2,367 药）：两者都有 1,168 / 仅 I2 801 / 仅 I3 398。
> **来源归属（映射层面，S1-A）**：1,418 个映射药中，**1,175 个（82.9%）的命中基因只来自 DRH `target`**、148 个（10.4%）两来源都有、**95 个（6.7%）只来自 I2 `target_name`**（T1 切分把蛋白名内嵌的符号词抽出来，如 `Tyrosine-protein kinase SRC` → `SRC`；I2 在 D1 中贡献 100 个精确符号 token，DRH 贡献 974 个）。**覆盖率主体由 DRH 驱动，但 I2 的贡献在 T1 规则下不可忽略（不是"可忽略"），且可能混有词内伪符号**（已见例：Taselisib 的 `C2` 来自 `...C2 domain-containing...`）。规则未因此改动（协议 §5 已预先声明蛋白名事实）。

---

## 3. 映射规则（协议 §5–§7 摘要）

- **T_j**：I2 `target_name` ∪ I3 `target`；先删括号说明，再按 `| ; , /` 与空白切分、剥首尾标点；**精确大小写敏感**匹配 GMT 基因符号，**不做别名/蛋白名→符号推断**。
- **规则 A**：`score(j,P)=|T_j∩P|`，`argmax`（并列按通路名升序），`max≥1` 登记。
- **规则 B**（Lead 补充）：超几何富集 `z=(x−n_jK_P/N_L)/sqrt(...)`，`n_j` = 命中背景基因数，`argmax z`，**z≥1.64** 才登记。
- **库**：S1=KEGG（186 集，背景基因 5,244）、S2=Hallmark（50，4,384）、S3=并集（236，7,335）。
- **主策略预注册层级**：`(S1,chosen)` → `(S2,chosen)` → `(S3,chosen)`；`chosen` 由 §6.3 开关决定（规则 A 若出现"单水平 >40% 映射药"或"可分析水平 <12"则改用 B）。
- **切分**：**PA 切分**（主口径，task-7 §3）= 在**已映射药**上 `k=max(1,round(0.2·N))`、`step=max(1,N//k)`、`H=names[0::step][:k]`；**E1 切分**（敏感性/阶段 2 兼容）= 同一规则作用在 U=4,088 上（k=818，step=4）。
- **单元** = `(cell_norm, unordered pair)`（380,418 个，与 E1 完全同口径）。

---

## 4. 主策略结果（S1 KEGG + 规则 A）

### 4.1 覆盖

| 指标 | 值 |
|---|---|
| 映射药数（D1，碰撞键剔除后） | **1,418** |
| 覆盖率（分母 4,088，G1 口径） | **34.69%**（门槛 25% → 余量 9.69 pp） |
| 覆盖率（分母 4,076） | 34.79% |
| 水平数 | 123（其中 ≥2 药的 91） |
| 最大水平占比 | 13.12%（`KEGG_NEUROACTIVE_LIGAND_RECEPTOR_INTERACTION`，186 药） |
| 单基因命中（score=1）占比 | 52.33%（742/1,418） |
| argmax 并列率 | **60.93%**（864/1,418） |
| 所选基因集大小中位数 | 90（11–325） |

### 4.2 可分析水平（PA 切分，G2）

- PA 切分：`n=1,418`，`k=284`，`step=4` → 训练药 1,134 / 留出药 284。
- **可分析水平 = 62**（同时满足：≥2 药；训练集 ≥1；留出集 ≥1）。E1 切分口径 = 63。
- 水平总数 123 → 32 个水平只有 1 个药；**51 个水平在 PA 留出集内无药**；10 个水平在训练集内无药。
- 前 15 大水平（n_all / train / holdout / E1-train / E1-holdout）：

| 水平 | all | train | hold | E1 train | E1 hold |
|---|---|---|---|---|---|
| KEGG_NEUROACTIVE_LIGAND_RECEPTOR_INTERACTION | 186 | 157 | 29 | 139 | 47 |
| KEGG_ACUTE_MYELOID_LEUKEMIA | 117 | 90 | 27 | 99 | 18 |
| KEGG_CALCIUM_SIGNALING_PATHWAY | 102 | 78 | 24 | 88 | 14 |
| KEGG_ADHERENS_JUNCTION | 71 | 61 | 10 | 61 | 10 |
| KEGG_CELL_CYCLE | 52 | 42 | 10 | 36 | 16 |
| KEGG_ARACHIDONIC_ACID_METABOLISM | 51 | 40 | 11 | 46 | 5 |
| KEGG_PATHWAYS_IN_CANCER | 43 | 37 | 6 | 39 | 4 |
| KEGG_ALZHEIMERS_DISEASE | 39 | 31 | 8 | 35 | 4 |
| KEGG_CHEMOKINE_SIGNALING_PATHWAY | 38 | 28 | 10 | 31 | 7 |
| KEGG_JAK_STAT_SIGNALING_PATHWAY | 28 | 23 | 5 | 23 | 5 |
| KEGG_PURINE_METABOLISM | 28 | 23 | 5 | 20 | 8 |
| KEGG_CYTOKINE_CYTOKINE_RECEPTOR_INTERACTION | 26 | 19 | 7 | 15 | 11 |
| KEGG_GAP_JUNCTION | 26 | 22 | 4 | 21 | 5 |
| KEGG_OOCYTE_MEIOSIS | 26 | 23 | 3 | 18 | 8 |
| KEGG_DRUG_METABOLISM_CYTOCHROME_P450 | 25 | 19 | 6 | 16 | 9 |

（完整 123 行表、62 个可分析水平清单在 `pa.json` → `strategies.S1.A.levels.table`。）

### 4.3 单元（G3/G4）

| 单元统计 | 值 |
|---|---|
| 两药均映射的 cell×pair 单元 | 88,118（占 380,418 的 23.16%） |
| **both-unseen 有注释单元（PA 切分，G3 主口径）** | **2,682** |
| 同上，字面 `names[0::5][:k]` 变体（step=5 而非 4） | 4,203 |
| both-unseen 有注释单元（E1 切分，两药均映射且均留出） | **3,739**（= R190 的 16,078 单元中的 23.26%） |
| **训练有注释单元（PA 切分，G4 主口径）** | **85,436** |
| 其中"一药在留出集、一药不在"（派生：85,436−58,788） | 26,648 |
| 严格训练单元（两药都不在留出集） | 58,788 |
| 训练有注释单元（E1 切分） | 84,379 |

---

## 5. S1–S3 × 规则 A/B 全对比（协议 §6.4 要求）

覆盖（分母 4,088）与水平：

| 策略 | 映射药 | 覆盖 | 水平数 | ≥2 药 | **可分析 PA** | 可分析 E1 | 留出缺失水平 |
|---|---|---|---|---|---|---|---|
| **S1-A（主）** | **1,418** | **34.69%** | 123 | 91 | **62** | 63 | 51 |
| S1-B | 1,418 | 34.69% | 143 | 122 | **87** | 83 | 50 |
| S2-A | 1,289 | 31.53% | 49 | 48 | 42 | 41 | 7 |
| S2-B | 1,289 | 31.53% | 50 | 50 | 46 | 45 | 4 |
| S3-A | 1,572 | 38.45% | 147 | 107 | 74 | 77 | 64 |
| S3-B | 1,572 | 38.45% | 184 | 154 | 103 | 103 | 71 |

单元与诊断：

| 策略 | both-unseen PA | 字面 step5 | both-unseen E1 | 训练单元 | 严格训练 | 并列率 | score=1 | 最大水平占比 |
|---|---|---|---|---|---|---|---|---|
| **S1-A（主）** | **2,682** | 4,203 | 3,739 | **85,436** | 58,788 | 60.93% | 52.33% | 13.12% |
| S1-B | 2,682 | 4,203 | 3,739 | 85,436 | 58,788 | **2.26%** | — | 10.37% |
| S2-A | 2,061 | 5,567 | 3,143 | 90,950 | 66,938 | 58.88% | 75.64% | 9.39% |
| S2-B | 2,061 | 5,567 | 3,143 | 90,950 | 66,938 | 12.65% | — | 7.14% |
| S3-A | 3,306 | 3,306 | 3,955 | 110,621 | 77,154 | 67.56% | 54.77% | 9.73% |
| S3-B | 3,306 | 3,306 | 3,955 | 110,621 | 77,154 | 3.63% | — | 7.51% |

**注**：规则 A 与 B 的"映射药数相同"（S1 1,418 / S2 1,289 / S3 1,572）——单基因命中在超几何 z 下通常也 ≥1.64（S1 的最小 z = 4.24），故 B 的 z 门槛在本数据上不筛掉药，只改变**标签选择**（集合大小归一）。**三个库 × 两种规则共 6 个组合全部通过 G1–G4**；主策略仅按预注册开关定为 **S1-A**（其余为报告数字，不参与改选）。

---

## 6. 规则 A/B 与确定性选择开关（Lead 补充要求）

| 库 | 规则 A 最大水平占比 | 规则 A 可分析水平 | 触发条件 | **chosen** |
|---|---|---|---|---|
| S1 | 13.12%（186 药） | 62 | 无（<40%，≥12） | **A** |
| S2 | 9.39%（121 药） | 42 | 无 | A |
| S3 | 9.73%（153 药） | 74 | 无 | A |

**开关结论：三个库都保留规则 A（未出现"单水平 >40%"或"可分析水平 <12"的退化）。** 主策略 = `(S1, A)`。规则 B 的全部数字见 §5，供阶段 2 选择时参考。

**规则 B 的额外诊断**（报告用，不改判定）：
- S1-B：143 水平、122 个 ≥2 药、87 可分析（PA）/83（E1）；并列率 **2.26%**（vs A 的 60.93%）；`max_z` 中位数 10.30、最小 4.24；所选通路大小的集合大小归一使水平数增加。
- **z 与精确超几何 p 的判定不一致**：S1-B 55/1,418、S2-B 139/1,289、S3-B 9/1,572 个药出现 `z≥1.64` 但 `p≥0.05`（常态近似 vs 精确上尾的差异）。**B 的价值在集合大小归一的"排序"，不在 p 值显著性**——其超几何零假设对"靶点基因并非随机抽样（聚集在可成药家族）"未校准，z 阈值实际上不筛任何药（最小 z=1.94–4.24 ≫1.64）。这一点必须在阶段 2 解释 B 标签时写明。

---

## 7. 敏感性（只报告，未改变主策略）

### 7.1 留药比例 r

| r | both-unseen 有注释单元（PA 切分） | K（留出药） | both-unseen（E1 切分） |
|---|---|---|---|
| **0.20（主）** | **2,682** | 284 | 3,739 |
| 0.30 | 6,411 | 425 | 7,334 |
| 0.40 | 13,795 | 567 | 11,912 |

（另见 §5：S2/S3 的 r=0.30/0.40 数字在 `pa.json` → `strategies.*.units.both_unseen_units_pa_r`；S1-A 的 E1 切分 r=0.30/0.40 = 7,334 / 11,912。）

### 7.2 字面 `names[0::5][:k]` 变体

task-7 文本写的是 `names[0::5][:k]`，而 E1 规则的 step 是 `N//k`；对主策略 N=1,418 → `k=284`、`step=4`（非 5），两者给出不同留出集：主口径 **2,682**，字面 step=5 口径 **4,203**（都 ≥800；协议 §7 已冻结以 E1 规则为主口径）。S2（N=1,289，step=4）主口径 2,061 / 字面 5,567；S3（N=1,572，step=5）两者相同 3,306。

### 7.3 token 切分与大小写

| 库 | 规则 A 映射药：T0（不切空白/斜杠） | **T1（冻结，Lead 要求）** | 大小写不敏感匹配 |
|---|---|---|---|
| S1 | 1,325 | **1,418** | 1,443 |
| S2 | 1,204 | **1,289** | 1,315 |
| S3 | 1,472 | **1,572** | 1,594 |

- T1 相对 T0 新增 **93** 个映射药（S1），全部由"从复合/连写靶点名中抽出内嵌基因符号"驱动；新增命中 token 的高频项为 `FLT3(20) JAK3(19) RET(17) BTK(17) JAK2(15) SRC(13) LCK(13) ITK(13) TYK2(13) FYN(11) SYK(11) PIM1(11) PLK4(10)` 等激酶符号，与这些药（激酶抑制剂、代号化合物如 `a770041`/`ast487`/`afuresertib`）的靶点注释一致；**三库 × 两规则的 T0→T1 丢失数均为 0**（`pa.json` → `token_sensitivity.*.drugs_mapped_T0_not_T1_*`；T1 相对 T0 新增 1,459 个基因符号 token）。
- **与 Lead 预探的对账**：Lead 预探 KEGG **1,341（32.8%）** / Hallmark **1,224（29.9%）**；本次冻结规则 T0 口径 = 1,325（32.41% / 4,088）/ 1,204（29.45%），T1 口径 = **1,418（34.69%）** / **1,289（31.53%）**。预探值落在 T0 与 T1 之间，**可由 token 切分严格度差异解释**（预探脚本未留存，无法逐条对账；差异 ±0.4–2.1 pp，不影响任何门槛）。
- 大小写不敏感匹配（敏感性）额外 +25 药（S1）；主规则保持大小写敏感。

### 7.4 v1.4 解析与碰撞（口径复核，与 E1 完全一致）

组合块 466,033 / U 4,088 / D1 4,076 / 细胞 112 / 药对 62,826 / cell×pair 380,418 / E1 切分 both-unseen 16,078 —— **7/7 与 R190 精确值相等**（审计 A3）。碰撞键 12 个，保守剔除；主策略的 1,418 个映射药本来就不含这些碰撞键（故 U 与 D1 口径覆盖率相同）。

---

## 8. 12 个机制类药的处理（BRIEF §P-A 要求）

| 药 | 在 U | 在 D1 | token 数 | 命中基因数 | **S1(KEGG)-A 水平** | score/并列 | Jaaks 标签 | 说明 |
|---|---|---|---|---|---|---|---|---|
| 5-FU | ✅ | ✅ | 0 | 0 | `unmapped` | — | — | **同义词失配**：I2/I3 用 `5-Fluorouracil`/`5-fluorouracil`，v1.4 用 `5-FU`；按"不做别名推断"规则无法联结 |
| Bortezomib | ✅ | ✅ | 39 | 23 | `KEGG_PROTEASOME` | 21 / 1 | Protein stability and degradation | 语义正确 |
| Cisplatin | ✅ | ✅ | 1 | 1 | `KEGG_APOPTOSIS` | 1 / **6** | DNA replication | 弱证据（单基因 + 6 并列） |
| Docetaxel | ✅ | ✅ | 21 | 19 | `KEGG_GAP_JUNCTION` | 16 / 2 | Mitosis | tubulin 家族主导 |
| Gemcitabine | ✅ | ✅ | 4 | 4 | `KEGG_PYRIMIDINE_METABOLISM` | 4 / 1 | DNA replication | 语义合理 |
| Oxaliplatin | ✅ | ✅ | 0 | 0 | `unmapped` | — | DNA replication | I3 `target` 为空 |
| Paclitaxel | ✅ | ✅ | 55 | 20 | `KEGG_PATHOGENIC_ESCHERICHIA_COLI_INFECTION` | 17 / 1 | Mitosis | **家族偏置的教科书例**：DRH 列出 18 个 tubulin 基因，argmax 选中"恰好含 17 个 tubulin"的 KEGG 集 |
| Pictilisib | ❌ | ❌ | 0 | 0 | `unmapped`（不在宇宙） | — | PI3K/MTOR signaling | v1.4 组合块中无此药（I2 亦无该拼写） |
| Taselisib | ✅ | ✅ | 19 | 2 | `KEGG_ACUTE_MYELOID_LEUKEMIA` | 1 / **36** | PI3K/MTOR signaling | 极弱证据（2 基因、36 并列，按名序仲裁） |
| Temozolomide | ✅ | ✅ | 2 | 0 | `unmapped`（KEGG） | — | DNA replication | `DNA`/`MGMT` 非 KEGG 符号；S2 映射到 `HALLMARK_APOPTOSIS`（1/2） |
| Vinorelbine | ✅ | ✅ | 27 | 16 | `KEGG_GAP_JUNCTION` | 16 / 2 | Mitosis | tubulin 家族主导 |
| Vorinostat | ❌ | ❌ | 0 | 0 | `unmapped`（不在宇宙） | — | Chromatin histone acetylation | 不在 v1.4 组合块（I2 有该药）；另有拼写变体 `vorinostat…` 组合名 |

12 药中 **6 个有 S1 标签**（Bortezomib/Gemcitabine 语义正确；Docetaxel/Vinorelbine 为 tubulin 共属；Cisplatin/Taselisib 为弱/并列仲裁），**4 个 unmapped**（5-FU 同义词、Oxaliplatin 无靶点、Temozolomide 靶点不在 KEGG），**2 个不在分析宇宙**（Pictilisib/Vorinostat）。这张表是 §10 条件 3/4 的直接证据：**粗注释 = 靶点基因集共属，不是机制通路**。

---

## 9. Jaaks 通路模板对照与 BRIEF 旧门槛冲突

- **Jaaks 模板**：读入 320,212 行（I6+I7 四列）；65 个药有通路标签、**21 个水平**；与 D1 药交集 **40 个（0.98%）**、与 U 交集 40。⇒ **单独用 Jaaks 模板不可能满足 ≥12 水平 × 每水平 ≥2 药 × 覆盖 ≥25%**（覆盖比门槛低 24 pp）。这是"必须引入外部基因集库"的**先验**依据，也是协议 §6 选择 MSigDB 而非 Jaaks 的理由（不是对 Jaaks 的否定）。
- **BRIEF §P-A 旧门槛冲突（需 Lead 裁决）**：BRIEF 曾建议"两药均被映射的药对 ≥50%"。实测（诊断，不参与本任务判定）：
  - S1-A：18,258 / 62,826 = **29.06%**（cell×pair 单元口径 23.16%）
  - S2-A：17,108 / 62,826 = **27.23%**（单元 24.45%）
  - S3-A：23,206 / 62,826 = **36.94%**（单元 29.95%）
  ⇒ **任何策略都不满足"药对 ≥50%"**。task-7 已用 G1–G4 取代该门槛，本报告以 task-7 为准并明确披露该冲突：若 Lead 仍要求药对 ≥50%，本资源在任何候选策略下都不达标，应改判 `mapping_not_qualified`（这不是本任务预注册的门槛，故本报告不做该判定）。

---

## 10. 审计

### 10.1 非响应派生（协议 §3 / 审计 A2）

- **结构性保证**：v1.4 以 `csv.reader` 解析，**只按列位置取** `drug_row`/`drug_col`/`cell_line_name`（以及 `block_id` 仅用于表头核对）；12 个 DENY 列只做**表头存在性**记录，其值不进入任何 Python 对象、不写入任何产物。I2/I3 只读 `dname`/`target_name` 与 `pert_iname`/`target`（`moa`/`target_type` 只统计非空行数）。
- **grep 复核**（产物）：`mapping_table.csv` 与 `mapping_table_rules_AB.csv` 对 `synergy|bliss|loewe|ic50|css|ri_row|ri_col|S_mean|S_sum|S_max` 的匹配数 = **0**。
`pa.json` 中响应列名只出现在 3 处**文档性位置**（`deny_columns_present`、`header_columns`、`non_response_derivation.response_columns_present_but_never_read`），**全部是字符串列名，从不作为 JSON 键、不携带任何数值**（程序化检查：`dict_key_hits = 0`，`response_values_stored = false`）。
- 映射输入仅：I1 身份双列 + I2/I3 公开注释 + I4/I5 公开基因集。**未用任何响应值筛药/筛水平/选库。**

### 10.2 确定性与可复现（A4）

- `pa.py` 无随机、无时间戳；JSON `sort_keys=True`；所有集合遍历前 `sorted()`。
- **连续两次运行产物 SHA256 完全一致**：`mapping_table.csv` = `45ede635…`（连续 7 次运行同一值）；`mapping_table_rules_AB.csv` = `96f1f51b…`；最终 `pa.json` = `f5559d26…`（同一脚本版本连续 2 次运行同一值）。

### 10.3 E1 交叉校验（A3）

`combos=466,033 / U=4,088 / D1=4,076 / cells=112 / pairs=62,826 / cell×pair=380,418 / E1-split both-unseen=16,078` — **expected 与 actual 全部相等**（`pa.json` → `judgment.audit_checks[2]`）。

---

## 11. 局限与必须随判定带走的条件

1. **切分口径必须先冻结（最重要）**：PA 切分（留出集建在已映射药上，N=1,418）→ both-unseen 有注释单元 2,682；E1 切分（留出集建在 4,088 全体，k=818）→ 3,739（R190 的 16,078 both-unseen 单元中仅 23.3% 两药均有注释）。两者都过 G3，但**含义不同**：PA 切分让注释臂在测试集恒有注释（便于识别"注释 vs identity"），E1 切分与 R190 的 16,078 单元可比但 76.7% 单元至少一药无注释。**阶段 2 协议必须二选一并写死，不能事后换。**
2. **规则 A 的标签语义是"基因集共属"而非"机制通路"**：`score=|T∩P|` 未做集合大小归一 → 靶点家族大小主导（taxane→tubulin→"E. coli infection"、"gap junction" 是典型例）；52.33% 单基因命中、60.93% 并列（按名序仲裁）。**阶段 2 的解释必须限制在"粗粒度基因集共属"层面，不得写成机制/靶点/临床主张。** 规则 B（集合大小归一，并列率 2.26%，可分析水平 87）已在 §5–§6 给出全部数字，如阶段 2 想改用 B，必须作为**新的冻结选择**并重跑本审计。
3. **覆盖是保守下界**：不做同义词/别名合并（5-FU、Vorinostat 等拼写变体失配）、12 个碰撞键剔除；I2 蛋白名在 T1 规则下贡献 95 个独有映射药（其中可能混有词内伪符号，如 `C2`），DRH 主导 1,175 个；真实可注释药数应高于 1,418。阶段 2 若只关心机制语义，可用"仅 DRH 驱动"的 1,175 药子集做敏感性。
4. **规则 B 的 z 未校准**：靶点基因非随机抽样，z 阈值实际不筛药（最小 z=4.24；`z≥1.64` 与 `p<0.05` 在 55/1,418 个药上不一致）；B 只应作水平多样性敏感性，不应报告为"显著富集"。
5. **BRIEF 旧门槛 ≥50% 药对未满足**（29.06%）；本判定依据 task-7 预注册的 G1–G4，该冲突已在 §9 显式披露，需 Lead 裁决。
6. **只映射了 4 类粗注释来源**：MSigDB 2023.1.Hs（KEGG legacy + Hallmark）。未测试 Reactome/GO/Enrichr 等替代库（不在 task-7 要求内）。若阶段 2 需要"更接近项目 GDSC 21 通路模板"的语义，需另立协议。

**本轮不回答**：DrugComb 端点可用性/饱和性；注释特征是否真的带来排序增益（这是阶段 2 的效应问题）；两个资源是否等价。**"映射资格通过" ≠ "冻结结论已复现"**。

---

## 12. 解冻条件

无（`mapping_not_qualified` 未触发）。若未来要改判/改主策略，必须按协议 §9 以**新协议**重新冻结，不得在本轮产物上事后修改。

---

## 13. 产物与 SHA256

| 产物 | 字节 | SHA256 |
|---|---|---|
| `PROTOCOL_PA.md`（v2，先冻结） | 18,851 | `16c40f9f61765637185bd061b1aeb4e62886bdfa027b8baf509830775bae607d` |
| `pa.py` | 51,047 | `25e64208a95b0c92b126823020e361ad208e517eef95c4f093f6be835ff470f3` |
| `pa.json` | 216,184 | `f5559d26a86679bd7be77ffd00fc5c4195be50eb611e8677a87434fb842c9fa3` |
| **`mapping_table.csv`（冻结表）** | 1,486,713 | **`45ede63521dc44fefec52d717765b4d2ba7d08ec3fde4372811c4d516de038d4`** |
| `mapping_table_rules_AB.csv`（辅助审计表） | 1,215,381 | `96f1f51be78f970c28bb6409d240db99e4a568dea7a9b1a2144414c5329db87c` |
| `resources/c2.cp.kegg.v2023.1.Hs.symbols.gmt` | 100,047 | `48de51190366ee388dffe34fa2931e590de43ee5e2a4c27c50c0fc33b9d194fc` |
| `resources/h.all.v2023.1.Hs.symbols.gmt` | 48,649 | `27e48f776cda235ad5b63acaecc3136853ee79c6447d883ce2b070a4d2d47b75` |

**冻结表格式**：`mapping_table.csv` = 4,088 药 × 3 库 = 12,264 行，列 `drug_normalized_name, source_library, pathway, n_target_genes, n_genes_in_pathway, drug_drop, notes`；每行按 §6.3 为该库选定的规则（本次三库均为 `rule=A`）产生；**主策略行 = `source_library == "S1"`**；`pathway=unmapped` 表示未映射；`drug_drop ∈ {none, collision_key_conservatively_dropped, no_target_annotation, no_exact_gene_symbol_overlap}`；`notes` 含 `rule/max_score/n_matched_genes/tie_pathways/jaaks_pathway`（键=值;分号串）。排序固定（药名升序 → S1<S2<S3），`\n` 行尾，纯 ASCII 安全内容。辅助表 `mapping_table_rules_AB.csv` = 4,088×3×2 = 24,528 行，含 A/B 两规则逐药标签与统计量。

---

## 14. 复现

```powershell
cd D:\MAESTRO\research\2026-10-27-drugcomb-annotation
& 'D:\anaconda\envs\maestro\python.exe' pa.py
# 期望（确定性）：verdict mapping_qualified | primary S1 A
# mapping_table.csv SHA256 = 45ede63521dc44fefec52d717765b4d2ba7d08ec3fde4372811c4d516de038d4
```

`pa.py` 内写死 7 个输入的字节数与 SHA256（任一不符即 `SystemExit` 中止），并写死 E1 交叉校验的 7 个期望值（不符即中止）。
