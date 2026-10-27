# R198-A3v2 动态路线：L1 开发协议（protocol_draft_v2，DRAFT）

2026-10-27 ｜ 执行：cellstate-lit（task-47） ｜ 状态：**DRAFT（预注册设计；本轮不运行）**。
上位文件：**`spec.md`（FROZEN-DRAFT，判定门与定义以它为准）**、`qualification.md`（v1 资格）、`cadence_evidence.md`（可识别性）、`challenge_A3.md`（revise 判决与 5 必改）。
本文件取代 v1 `protocol_draft.md` §4–§7 的 L1 部分（v1 文件保留、不改；v1 的 L2 内容在此重述为"升级路径"，不因 v2 而解冻）。
**定位**：A3 仍是"另问" L1 开发资产；**不进入候选、不进入 L2**。禁止：训练、跑时间预测、读表达/响应、声称新颖性/世界模型/决策收益。

---

## 0. 与 v1 的差异（先看这里）

| 项 | v1 | v2 |
|---|---|---|
| 交付 | 声称 `spec.md` 但不存在 | **`spec.md` 已补交**（本目录） |
| L1 判定 | 只有 ΔSpearman/ΔR²，无判定门 | **冻结 δ_min/MDE80/room/split-half 可靠性/资格门；不过即 `evaluation_cannot_distinguish`** |
| C3 两快照拼接 | 与 V1 并列，存在把 24h 目标当输入的风险 | **C3 仅 V2（输入严格早于目标时间）定义；V1 禁止目标时间入输入（模型集不含 C3/C4）** |
| V2 地位 | 未明确 | **exploratory only（严格合格线 15<20）**；不作跨药推断、不出判定 |
| Q 表 | Q2 responder / Q5 措辞错 / Q7 标 M | Q2 改 state-associated proxy；Q5 更正；Q7 改 M*；补"静态/两快照已足够"清单 |
| 先例/边界 | 未落地 | 有界先例（2604.27646/CellFlow/State/XPert/BATCHIE/CADENCE）+ C174/C176/C177 边界 |
| 缓存读取 | qualification 与 record 不一致 | **统一为"只读 keys/shapes/dtypes、未读值、provenance 未审计"**（spec §2） |

---

## 1. 数据变体与资格（metadata-only 预检）

| 变体 | 数据 | 合格单元（≥20 QC-normal cells，含时间匹配 control） | 判定地位 |
|---|---|---|---|
| **V1** | 精确 6h/24h；4 药 + control；115 系；285 键 | 每药合格线：**BRD3379 95、Bortezomib 22、Idasanutlin 24、Trametinib 24**（均 ≥20） | **confirmatory-development** |
| **V2** | hashed Trametinib 24 系 × {3,6,12,24,48}h × {Tram, DMSO}（17,553 single-tag；13,713 normal） | 严格条件（Tram+DMSO 在所有输入/目标时间点均 ≥20 normal）下：**目标 12h = 15 系；目标 48h = 15 系**（<20） | **exploratory only** |
| 24h-only 9 药 | 单快照 94–98 系/臂 | — | 静态外部层（可选，不进入 L1 判定） |
| CRISPR 72/96h | 遗传扰动 | — | 不进入 |

来源：`tmp/a3v2_eligibility.py` → `tmp/a3v2_eligibility.json`（metadata-only；未读表达/响应）。
**独立单位 = 细胞系**；不是 key、不是细胞、不是时间点。V1 每药有效 n = 95/22/24/24；V2 n=15。

---

## 2. 端点、模型与比较器（冻结）

### 2.1 目标量

对 (drug `d`, cell line `c`, target time `t`)：
- pseudobulk effect `y_{d,c,t}`：QC-normal 单细胞表达按 (d,c,t) 聚合 → 对时间匹配 control 的 log2 ratio（log2((pseudo+1)/(ctrl+1))），再投影到 **train-only 冻结基因集**：按训练线平均 |logFC| 取 top-**K=200**（K 冻结；选择只用训练折），最终标量 = 该 200 基因的 logFC 均值。向量版副端点 = 同 200 基因的 logFC 向量。
- 对照：V1 用 6h/24h 的 `perturbation=control`（时间匹配）；V2 用同时间点 DMSO（`hash_assignment=DMSO_*`）。
- 目标外的时间/细胞系信息一律不进入特征（见 §5 泄漏审计）。

### 2.2 V1 模型集（固定；**无 C3/C4**）

| 代号 | 模型 | 输入（仅训练折拟合） |
|---|---|---|
| C0 | mean | 训练线 y 均值（常数；组内排序 ρ=0 by construction） |
| C1 | static | 细胞系未处理特征：DepMap/CCLE basal expression 与 h5ad 基因 symbol 交集；训练折内标准化 + PCA(k 内层 CV) + ridge |
| C2 | early-state | 该细胞系 **6h** 处理 vs 6h control 的 pseudobulk logFC（同一冻结基因面板）→ ridge → 预测 24h y |
| C5 | oracle | 真实 24h y（上限；不是候选） |
| C6 | negative | C2 特征按细胞系标签置换（≥200 次），用于零分布 |

**V1 禁止任何 24h 派生物作输入**（含其标签均值、PCA、基因选择、标准化统计）。C3/C4 在 V1 的实现中不得出现（代码级断言 + 独立复审）。

### 2.3 V2 模型集（exploratory；C3 仅此）

| 代号 | 模型 | 输入 |
|---|---|---|
| C1 | static | 同 V1 的未处理特征 |
| C3 | two-snapshot | **严格更早时间点**的 pseudobulk 状态拼接（目标 12h：3h+6h；目标 48h：3/6/12/24h）→ ridge |
| C4 | simple linear-time | 对每个基因，用该细胞系**更早时间点**的 effect 拟合线性时间趋势，外推到目标 t（只用更早时间点） |
| C5/C6 | oracle / negative | 同上（C6 打乱细胞系标签） |

- **C3/C4 只允许出现在 V2**；OT/flow 只可作附加估计器对照（exploratory，不进入判定）。
- **V2 无判定权**：即使指标看起来好，也只报描述，不升级、不作跨药推断。

---

## 3. 动态量 → 决策映射（v2 修正表）

支持等级：`M`=元数据可支撑群体表达分析；`M*`=需清洗/新增注释；`F`=需功能终点；`X`=本资产不支持。

| # | 动态量 | 定义/计算（表达层） | 会改变什么决策 | 可证伪对比（H0 / 统计量） | 支持 |
|---|---|---|---|---|---|
| Q1 | 早期→晚期持续性 | 24h effect 对 6h effect 的预测关系 | D-C"6h 早读能否替代 24h"；D-D 选测量时间 | H0：24h effect = drug 均值；统计量 Δρ(C2−C1)（留出细胞系） | M |
| Q2 | **早期 vs 晚期 state-associated proxy 排序** | 固定药物下，细胞系按表达 effect 的 6h vs 24h 排序/翻转 | D-D、D-B 的**表达层候选 proxy**；**不称 responder**；功能 responder 需 L2 | H0：6h 与 24h 排序一致（ρ=1 或 ≥预注册阈值）；每药跨系 Spearman + top-k Jaccard | M |
| Q3 | 药物排序的时间依赖 | 固定细胞系下 4 药 effect 排序在 6h vs 24h 是否变化 | D-D（仅 4 药，功效低）；不作 D-A 推断 | H0：6h vs 24h 药排序一致（Kendall τ） | M（4 药，弱） |
| Q4 | 处理×时间交互 | 不同药物是否有不同时间形状 | D-D：动态特征能否跨药迁移（仅描述） | H0：时间×药物交互=0；留药 Δ 描述 | M（4 药，弱） |
| Q5 | **时间匹配对照的可用性** | control 在 **6h 与 24h 均有测量（115 键/时点）**；但 **channel/批次不可匹配**；hashed 臂另有 DMSO 5 时间点 | D-C/D-D：是否必须逐时间归一化；6h/24h 差异能否当时间效应 | H0：对照 6h vs 24h 差=0（在测量误差内）；对照差 vs 处理差的比值与 CI | **M***（对照存在但 batch/channel 不可匹配） |
| Q6 | 细胞系×时间交互 | 不同细胞系时间形状是否不同 | D-B/D-D：个性化选时间点/单点误排 | H0：cell×time 交互=0；方差分量 + 留细胞系预测 Δ | M（V1 只有 2 点，仅描述；V2 探索） |
| Q7 | 状态组成/细胞周期转移 | 24h 相对 6h 的**细胞状态组成**变化（cycle/stromal 程序） | D-C/D-B：晚期效应是否由组成漂移伪装；是否应状态分层 | H0：控制组成分数后处理效应消失；组成调整前后效应差 | **M***（**需新增细胞状态注释/打分**；h5ad 无状态注释） |
| Q8 | 可逆性/洗脱后恢复 | 洗脱/再挑战轨迹 | D-E | 无数据 | X |
| Q9 | 剂量×时间 | 不同剂量的时间过程 | D-E/D-D | 无剂量序列（单剂量） | X |
| Q10 | 真实路径/个体轨迹 | 同细胞连续状态 | 轨迹/机制主张 | 见 `cadence_evidence.md`；需 linkage | X |

### 3.2 "静态/两快照已足够"的决策清单（避免误读）

- **D-A 选药**：本资产**静态基线即可**（无预处理探针时，动态信息在决策前不可得；6h/24h 是处理后的快照，不能用于 D-A）。
- **24h-only 9 药臂**：只有单快照 → **只能做静态外部层**，不能做动态比较。
- **D-D 选测量时间**：在只有 2 个时间点时退化为**二选一**（"仅 24h" vs "6h+24h"）；它由 Q1 的同一 L1 比较直接回答，**不需要时间模型**。
- **若 Q3 的 6h/24h 药排序一致（ρ ≥ 预注册阈值）** → **单时点足够**，动态无增量。
- **若 Q5 对照漂移可忽略（区间内）** → 不需要逐时间对照模型；两快照足够。
- **若 C2 ≈ C4（V2 中）** → 时间模型不必要，两快照足够。
- **若功能终点不可得/决策对时间不敏感** → 停在 L1（表达层），静态/两快照足够，不进入 L2。

---

## 4. 切分、调参与推断（写死）

- 种子 `20261027`；所有随机过程由它派生。
- **V1 外层**：按细胞系分组的 5 折 leave-cell-line-out；合格细胞系按名称排序，`fold = i % 5`；同一细胞系所有键同折。
- **V1 内层**：训练折内按细胞系分组的 5 折（λ/PCA-k/基因集选择）；标准化/PCA/基因选择只在训练折拟合。
- **V2 外层**：leave-one-time-out（目标 12h、48h 各一折；6h/24h 探索；3h 不作目标）；**内层**：训练时间 × 训练细胞系的 5 折；任何输入只用严格更早时间点。
- **单位与聚合**：独立单位=细胞系；V1 主统计量 = 4 个药 Δ 的等权平均（先按药算 ρ(C2)−ρ(C1)，再平均；不按 95 系加权）；**不对药物总体做推断**（4 药仅作描述）。
- **CI**：按细胞系 cluster bootstrap（1,000 次，种子 20261027）；V1 主平均另做 drug-level 描述性重抽样并报告范围；V2 只给 15 系的描述区间。
- **禁止**：把 key/细胞当独立 n；用测试折做特征选择/调参；用随机行切分替代分组切分。

---

## 5. L1 判定门（与 `spec.md` §5 一致；本文件给实现细节）

**δ_min = 0.10**（Δ Spearman 绝对差；运营定义见 spec §5，冻结）。

**门顺序（先测后比）**：
1. **G0 资格**：V1 每药合格线 ≥20（95/22/24/24 全过）；V2 仅 15 系 → exploratory。
2. **G1 split-half 可靠性**：每个 (drug,t) 内，按 `hash(cell_index, 20261027) % 2` 把每个 (c) 的 QC-normal 细胞分两半 → 两套 pseudobulk effect → 跨线相关 `r_half` → Spearman–Brown `rho_sb=2r_half/(1+r_half)`；门 **`rho_sb ≥ δ_min + MDE80`**（<20 系或半折 <10 细胞 → 失败）。
3. **G2 room**：`room = rho_oracle − rho_C1`（用 half-A/half-B 构造 oracle 上界与 C1 实测）；门 **`room ≥ max(δ_min, MDE80)`**。
4. **G3 MDE80**：主对比 Δ（C2−C1，配对）按细胞系 cluster bootstrap（1,000 次）估 SE(Δ)；`MDE80=(1.959964+0.841621)·SE(Δ)`；门 **`MDE80 ≤ 0.10`**。
   - **预运行解析上界（冻结）**：`MDE80_upper=2.802·sqrt(2/(n−1))` → V1 n=95/22/24/24：**0.41/0.86/0.83/0.83**；V2 n=15：**1.06**。要求的跨模型误差相关：`r_err ≥ 1−0.01(n−1)/15.70` → n=95: **0.940**；n=22: **0.987**；n=24: **0.985**；n=15: **0.991**。实际 bootstrap 若 MDE80>0.10 → G3 失败，**不跑 G4**。
5. **G4 主效应**：`Δ = mean_d(ρ(C2_d)−ρ(C1_d))`；门 **点 ≥0.10 且 95% CI 下界 >0**。
6. **G5 泄漏审计**（一票否决）：见 §6。

**判定语义**：G1–G3 任一失败 → `evaluation_cannot_distinguish`；G0 → `data_unavailable`；G5 → `design_invalid`；全过且 G4 过 → `development_increment_present`（仅表达层开发）；G1–G3 过、G4 不过 → `no_increment`。**一律不得写成"动态信息不存在"**。
**V2**：即使 G1–G5 全过也只写 `exploratory_only`，不出 pass/fail、不升级。

---

## 6. 泄漏审计清单（G5；代码级检查项）

1. 输入特征列不含目标时间 `t` 或更晚时间；V1 输入不含任何 24h 派生量。
2. 基因集/PCA/标准化/λ 只由训练折细胞系估计；测试细胞系标签不参与。
3. 外层折按细胞系分组，同一细胞系不跨折；内层同样按细胞系分组。
4. V1 模型集 = {C0,C1,C2,C5,C6}，实现中断言 C3/C4 不存在；V2 的 C3/C4 输入的 max(time) < 目标 t（代码断言）。
5. 置换零分布/负对照与主模型同管道、同预算。
6. 报告"目标时间不可用"的显式断言（运行前/运行中）。
7. 冻结后再跑：任何阈值/端点/切分改动需新协议，不得事后改。

---

## 7. 先例与边界（bounded；不声称新颖性）

**范围声明**：本轮不做系统检索；沿用项目 registry 与用户报告的有界阅读（窗口 2025-01-01—2026-10-27；非穷尽；**未发现 ≠ 不存在**；本路线**不主张新颖性**）。

| 先例 | 与本路线关系 | 证据状态 |
|---|---|---|
| arXiv:2604.27646 虚拟细胞 in-the-wild 基准（2026-04-30） | unseen cell / unseen perturbation / cross-dataset 三场景统一基准 11 模型；**数据包含 McFarland2020（本资产来源）**；"简单线性基线常优于复杂模型" → L1 必须以线性/静态为主对照；**不是新基准** | P（本地 `reference/papers/arxiv-2604.27646/paper.html`；`tmp/arxiv_2604.27646.txt:186,269`；`reference/papers.tsv` reading_scope） |
| CellFlow 形态（arXiv:2502.09775v1） | 未配对终点流匹配；插值 t 不是物理时间 → 不能当轨迹证据 | P（用户报告 `evidence_notes.md:19`；本轮未重读） |
| State（Cell 2026, DOI 10.1016/j.cell.2026.07.052） | 跨 context 扰动响应预测；不能当本资产路径证据 | A（registry；全文受限） |
| XPert（Nat Mach Intell 2026, DOI 10.1038/s42256-025-01165-w） | KG+扰动表达+剂量/时间；已有未见细胞/药物任务；输出转录变化≠决策收益 | P（`handoff-method-audit/report.md:25`） |
| BATCHIE（Nat Commun 2025） | 条件组合模型+后验更新+整板设计；主动设计已有先例 | P（用户报告） |
| CADENCE（arXiv:2605.23470v1） | DFA/COA/MRA/PR/FOA；本资产不满足 FOA → 不做轨迹主张 | P + 本轮 HTML 复核（`cadence_evidence.md`） |
| target-identifiability（SSRN 7368638） | 破坏性快照/路径目标/sharp bounds 的先例压力 | A（403 未读） |

**谱系边界**：
- C160（R190-D 停：检定力/设计失败，非"细胞状态无信息"）；C167（`not_replicated`≠"不能复现"）；C172（1.43% 仅加性份额）。
- **C174**：1.43% 只是加性条件主效应份额；加权矩/依赖/可靠性需重核 → 动态路线**不以 C172/C174 旧解释为前提**。
- **C176**（R196 `replicated_under_audit` 作废、`inconclusive`，原数字保留）；**C177**（R197 v1 协议作废、v1 结果不得解释）→ **撤回不影响本路线，但禁止引用旧判定；R196v2/R197v2 未完成前不重开其问题**。
- 与 A1/A2/A4/A5 **解耦**：本 SPEC 只是"另问" L1 开发资产。

---

## 8. 失败类别与停止条件

| 类别 | 触发 | 动作 |
|---|---|---|
| `data_unavailable` | G0 不过 | 停；不写阴性 |
| `design_invalid` | G5 失败；折/种子/管道偏离 | 停并修协议 |
| `evaluation_cannot_distinguish` | G1/G2/G3 任一不过 | 判 inconclusive；不写"不存在"；停 L1 |
| `no_increment` | G1–G3 过、G4 不过 | 停动态取证；保留描述；不升级 |
| `exploratory_only` | V2（n=15<20） | 只报描述，无判定 |
| `decision_layer_blocked` | L2 功能结局/批次/剂量缺失 | 停在 L1；L2 等新测量；不换名重启 |
| `identifiability_unsupported` | 轨迹/个体路径主张 | 禁止；本 SPEC 不产出 |

**总停止规则**：任一判定门失败即停；不换端点/阈值；不把 L1 结果升级为 L2/候选；阴性不写不存在。

---

## 9. L2 升级所需数据（不在本轮；L1 通过也不自动进入 L2）

同 `spec.md` §9 / v1 protocol §6：与 Mix-seq **同细胞系 × 同药物 × 同剂量 × 同时间点（6/24/48h）** 的独立功能读数（viability + 凋亡/死亡；时间匹配 vehicle；≥3 复孔 × ≥2 独立培养/批次）；明确暴露/洗脱方案；批次/run/plate/passage 元数据；决策、效用/成本、δ_min、MDE 预注册；≥2 独立队列。**PRISM 只能作非时间匹配的外部二级验证**（3/4 药有、BRD3379 无、assay/剂量/时间不匹配）。

---

## 10. 不做 / 不得声称（保留模板）

1. 本轮**不训练、不跑时间预测、不读表达/响应**。
2. **不得声称**动态世界模型成立 / 真实轨迹恢复 / 多快照即可恢复路径 / 动态信息改变具体药物决策 / L1 增量支持 L2。
3. **不得**把 6h/24h 差异直接当时间效应；**不得**把表达 proxy 当功能 responder；**不得**把流匹配插值当物理时间。
4. **不得**把"未发现"写成"不存在"；**不得**声称新颖性。
5. **不得**改 v1 文件；v1 措辞不一致以 `spec.md` §2 权威描述为准。

---

## 11. 变更记录与实现清单

| # | 变更 | 位置 |
|---|---|---|
| 1 | 补交 spec；统一 kinetic_horizon 读取描述；v1 SHA 登记 | `spec.md` §2 |
| 2 | L1 判定门冻结（δ_min=0.10；MDE80/room/split-half/资格；不过即 `evaluation_cannot_distinguish`） | `spec.md` §5；本文件 §5 |
| 3 | C3 仅 V2、V1 禁目标时间入输入；泄漏审计 G5 | `spec.md` §5.3；本文件 §2.2/§6 |
| 4 | Q2/Q5/Q7 修正 + "静态/两快照已足够"清单 | 本文件 §3 |
| 5 | 有界先例 + C174/C176/C177 + 不重开 R196v2/R197v2 | `spec.md` §7；本文件 §7 |
| 6 | 记录/措辞一致性、失败类别/停止条件 | 本文件 §8/§10；`record_v2.md` |

**实现清单（冻结后、运行前）**：① 代码级断言 V1 模型集；② 折/种子/管道写死并记 SHA；③ G5 泄漏审计脚本；④ 运行顺序 G0→G1→G2→G3→G4；⑤ 所有结果带 `evaluation_cannot_distinguish`/`no_increment`/`development_increment_present` 判定字段；⑥ 输出不得含决策/世界模型措辞。
