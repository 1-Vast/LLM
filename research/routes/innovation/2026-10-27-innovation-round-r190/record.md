# R190 轮次记录：细胞状态特征线（D）资格审计 → 停；DrugComb 第二资源（E1）→ `eligible_with_conditions`

2026-10-27。角色：Lead（冻结/核验/综合）＋ 3 名独立代理：细胞状态资格审计员（cellstate-auditor，task-4）、先例核验员（cellstate-lit，task-5）、DrugComb 资源审计员（drugcomb-auditor，task-6）。提案者（Lead）不自评。

本轮范围由 [BRIEF.md](BRIEF.md) 冻结：线 D＝用药物靶点基因的细胞表达作细胞状态特征，检验能否在留出细胞上把同一药对内细胞按 `ΔEMAX` 排出次序（先 A0 资格审计，通过后才冻结效果协议）；线 E1＝为冻结结论寻找/资格化第二资源（DrugComb）。**本轮未运行任何效果实验，无代码晋升，总体目标未达成。**

## 0. 一句话结果

- **线 D：`unqualified` → 停。** A0 按冻结协议字面判：G2 药对级靶点映射仅 **57.3%**（<90%）、G3(e) 双向聚类 **MDE80=0.240**（>0.05）——111 个有表达细胞、1,294 个药对嵌套在细胞上，排细胞实验在设计上检不出 δ=0.05。信号本身**存在**（interaction 份额 0.630、可加上限 0.256、room sd 0.052、可靠性上限 0.788、跨筛 within-pair ρ 0.59 辅助），但**本资源/本设计下不可检验**。
- **线 D 先例核验：部分覆盖 → 新颖性不得主张。** 细胞状态特征×协同、留出细胞评估、处理内细胞排序三项均已发表（SynVerse 2025、One-Hot News 2026、arXiv 2605.20885、Tahoe-100M LOCO 2026 等）；只有"`ΔEMAX` within-pair 排序 × 两药未见 × 细胞留出"这一拼装未发现（检索结果，非空白证明）。
- **线 E1：`eligible_with_conditions`（重大进展）。** DrugComb v1.4 summary（193 MB 全量核验）提供 **466,033 组合块、4,088 药、112 细胞、62,826 无序药对、380,418 cell×pair 单元**；C156 规格要求的 both-unseen 单元在 r=0.2/0.3/0.4 下为 **16,078 / 33,148 / 52,368**（≥800 门槛的 20–65 倍）。**这是 190 轮来第一个在结构上满足"第二资源"规格的候选**；但资格≠复现：注释映射协议、端点（ΔEMAX 等价性/饱和性）与 unseen-entity 切分都必须在下一轮先冻结。

## 1. 线 D1：最近先例核验（[prior_art.md](../2026-10-27-cellstate-qualification/prior_art.md)，F01–F35，56 条引文逐字审计 0 fails）

**判定：部分覆盖（partial coverage）。** 三项构成要素都已有发表先例：

| 要素 | 最近先例 | 关键事实 |
|---|---|---|
| 细胞状态特征×协同预测 | DeepSynergy 2018（novel-cell-lines CV，MSE/RMSE/PCC）、SynVerse 2025（16 模型×8 特征，含 CCLE 表达；**无一超过 one-hot 基线**）、DIPx 2025、SynProtX 2025 | 特征类已覆盖 |
| 留出细胞评估 | One-Hot News 2026（LCO/LDO 表：LCO 下特征≈OHE，LDO 两药全新均差）、PDTSyn 2026、BMC cold-start 2026（unseen cell lines 掉到 0.482） | 切分已覆盖 |
| 处理内细胞排序作为评价对象 | arXiv 2605.20885（原文 "isolates within-drug cell ranking"；cell-blind per-drug r=0.438；**明确排除 drug combinations**）、iScience 2025（cell-blind 下 per-combination PCC；per-drug PCC 仅 0.1）、Nair 2023 跨筛一致性 | 评价原则已覆盖（单药） |

**唯一未发现的拼装**：`ΔEMAX` 的 within-pair 细胞排序 × 两药未见 × 细胞留出（零命中只作检索结果）。**处置：不得声称新颖性；若继续只能作为复现+评估修正。** 先验定量且不乐观：Tahoe-100M LOCO 的 context 残差最好模型 R² +0.004、可靠性中位 0.067；DIPx 两药全新子组中位相关 −0.03；Baptista 2023 表达特征≈细胞标识符。检索缺口：仅 2 pass/EPMC+OpenAlex+arXiv；Regulon/Separating 全文、One-Hot 补充表 S7–S12 未读。

## 2. 线 D：A0 资格审计（[report.md](../2026-10-27-cellstate-qualification/report.md)、[a0.json](../2026-10-27-cellstate-qualification/a0.json)）

协议 [PROTOCOL_A0.md](../2026-10-27-cellstate-qualification/PROTOCOL_A0.md) 运行前冻结（含 AMENDMENT-A0-001：CCLE 表达仅 111/125 细胞有行，来自 Lead 结构探针、先于任何资格统计）。**判定：`unqualified`**（门槛未改）。

| 门槛 | 实测 | 门槛 | 判定 |
|---|---|---|---|
| G1 身份 | COSMIC 主口径 122/125 + 归一次口径补 3 → **125/125** 唯一 DepMap_ID；其中 **111/125（88.8%）有表达行**（缺 14：Breast 5/Colon 6/Pancreas 3） | ≥119 且 ≥105 有表达 | **PASS**（修订后） |
| G2 靶点→基因 | 86 靶点映射 **72**（50 精确+22 冻结别名；14 机制类未映射）；**两侧各 ≥1 映射基因的药对仅 1161/2025=57.3%**（并集读法 95.0%） | 靶点 ≥60/86 且药对 ≥90% | **FAIL**（`data_unavailable`） |
| G3(a) 方差分解 | cell 0.050 / pair 0.326 / **interaction 0.630** | ≥0.10 | PASS |
| G3(b) 可加细胞效应上限 | 1,294 药对 `Spearman(y, â_cell)` 均值 **0.2555** | ≥0.05 | PASS |
| G3(c) room | 药对级 `sd(y_int)` 中位 **0.0522** | ≥0.02 | PASS |
| G3(d) 可靠性上限 | σ_e=0.0408（借用 R4；raw 无组合端点不可得）；**ρ_ceiling=0.788**；跨筛 within-pair ρ 中位 **0.593**（98 对，辅助） | ≥0.10 | PASS |
| G3(e) 检定力 | 111 细胞 5 折（23/22/22/22/22）；**MDE80=0.240**（双向聚类；per-fold 0.140–0.347；固定细胞置换 0.174；iid 解析 0.0295 仅该口径过） | ≤0.05 | **FAIL**（`evaluation_cannot_distinguish`） |
| G4 泄漏/切分 | 无 design_invalid；分折按细胞；特征为细胞注释、无响应派生；5 折哈希 `c312ccfe…` | — | PASS |
| G5 端点 | 主端点=留出细胞 within-pair Spearman；outcome 为 viability 派生 `ΔEMAX` | — | 记录完成 |

**Lead 裁定（两处字面歧义，均按字面判、不做事后调整）**：
1. G2 文字为"两侧靶点均 ≥1 个映射基因"→按每侧各 ≥1 = **57.3% FAIL**；并集读法 95.0% 只作披露，本轮不改口径。
2. G3(e) 协议写明"双向聚类 bootstrap"→ **0.240 FAIL**；iid 0.0295 只在"逐药对独立预测"下成立，而细胞状态型预测天然跨药对共享（这正是假设的形式），不能拿它当门槛。
3. **两项失败独立**：即使 G2 宽读通过，G3(e) 仍 fail；反之亦然——只有两处都宽读才全过，故判 `unqualified` 是稳健的。

**解冻条件（写入 report §8）**：① 为 12 个只有机制类靶点的药提供基因级注释，或显式限定到两侧均覆盖的药对子集（需新协议）；② 增加有表达细胞（或换 ≥数倍细胞数的组合数据）使聚类 MDE80 ≤ 预注册 δ，或改用有独立抽样单位的端点并预注册论证。

**决定：线 D 停止**——不冻结效果协议、不运行效果实验、不换指标/换聚合复活。保留物：A0 的测量级事实（interaction 份额、可加上限、room、可靠性、跨筛 within-pair ρ、MDE 的细胞嵌套效应）与"信号存在但本资源不可检验"的边界。

## 3. 线 E1：DrugComb 第二资源资格审计（[report.md](../2026-10-27-drugcomb-qualification/report.md)、[e1.json](../2026-10-27-drugcomb-qualification/e1.json)）

协议 [PROTOCOL_E1.md](../2026-10-27-drugcomb-qualification/PROTOCOL_E1.md) 运行前冻结；全部数据来自 Zenodo 官方记录 + Europe PMC 补充材料（门户 drugcomb.org/fimm.fi 本机 SSL 不可达，记缺口）。**判定：`eligible_with_conditions`（5 道硬门槛全过）**。

| 门槛 | 实测 | 判定 |
|---|---|---|
| ① 文件可获取/解析 | v1.4 summary 全量 193,184,734 B（SHA256 `e08e3d35…`，MD5 与官方一致）；v1.5 标识表 2 个 + v1.5 summary 60×1MB 分块（4.22%，全文件 1,421,694,989 B）；NAR2021 S1 复算 751,498/717,684 与论文一致 | 通过 |
| ② 药/细胞名可检索 | v1.5 标识表 **8,396 药 / 2,320 细胞**，归一名非空率 100%；样本内匹配 100% | 通过 |
| ③ 排除 Jaaks/GDSC 后单元 ≥2,000 | **v1.4 全量：466,033 组合块 / 4,088 药 / 112 细胞 / 62,826 无序药对 / 380,418 cell×pair**；both-unseen（确定性留药）r=0.2/0.3/0.4 = **16,078 / 33,148 / 52,368** 单元；v1.5 样本剔除 GDSC 后下界 29,028；GDSC1 为单药 study（组合行 0），无 Jaaks | 通过（14.5–190×） |
| ④ 粗注释覆盖 ≥50% | 本地 7 来源并集对 D1（v1.4 组合药 4,076）= **51.28%**（边际 +1.28pp）；对 D2=49.12%；**项目 38 通路模板仅 0.98%** | 通过（条件） |
| ⑤ 非饱和可后验 | v1.4 12 / v1.5 14 个响应/派生列存在（只读表头）；无显式 QC flag | 通过（待测） |

**与 Jaaks 重合**：细胞 18/112、药物 40/65（61.5% 的 Jaaks 药在 DrugComb 出现）、cell×pair 键 241 —— 非零，须 unseen-entity 切分。
**条件（必须随结论传递）**：① v1.5 全表未全量核验（仅 4.22% 分块，全文件 SHA=null；端到端全量核验的是 v1.4）；② 注释覆盖边际且过线依赖小表；③ **无本地 "MoA/靶点→项目 38 通路水平" 可审计映射**（下一轮必须先冻结映射协议并验证 ≥12 个可分析水平）；④ 端点饱和性未测、summary 不直接含 `ΔEMAX`（可能需 2 GB raw dose-level 重拟合）；⑤ unseen-entity 切分待冻结；⑥ v1.4 无 study 列；⑦ 标识表碰撞（药 128 / 细胞 5）已保守剔除。

**Lead 裁定**：④ 按任务文本读法（"存在可覆盖 ≥50% 药物的粗注释来源"）通过；但**这不等于"通路语义复现可行"**——若下一轮映射协议不能给出 ≥12 个可分析水平（覆盖 ≥阈值、可审计、非响应派生），则升级为 `not_eligible`。**"eligible_with_conditions" 不等于解冻/复现成立。**

## 4. Lead 独立核验

- **A0 确定性**：Lead 独立重跑 `a0.py`（约 82 s）→ a0.json/identity_map.csv/target_map.csv 三份 SHA256 与审计员产物**逐字节一致**；verdict/关键数字一致。
- **E1 确定性**：Lead 独立重跑 `e1.py`（约 25 s）→ **e1.json SHA256 与审计员一致**（`2FD636D8…19DDB`）；Lead 另用独立 pandas 直接重算 v1.4：行 1,175,220 / 组合 466,033 / 药物 4,150 原始、4,088 归一 / 细胞 112 / 无序药对 62,826 / cell×pair 380,418 —— **与审计完全一致**。
- **先例**：Lead 抽查 prior_art.md 中 2605.20885（F28/F30 行锚）、iScience 2025（F31/F32）与 One-Hot 相关引文，均逐字存在；引用审计脚本自报 56 条 0 fails。
- **纪律**：A0 只做资格统计（响应值仅用于协议 §4 预注册量，`purpose=qualification`）；E1 响应列只读表头（grep 复核无响应数值）；两审计均未联网改数据、未改协议门槛、未改其它目录。

## 5. 本轮新增可引用事实（登记于 EVIDENCE_REGISTER / CLAIM_STATUS_AUDIT）

- **C159**（线 D 先例定位，部分覆盖）：细胞状态特征×协同、留出细胞评估、处理内细胞排序三项均已发表；唯一未发现拼装是 `ΔEMAX` within-pair×两药未见×细胞留出（检索结果）；**新颖性不得主张**；先验定量多为负/极小（SynVerse 无一超 one-hot、DIPx 两药全新中位 −0.03、Tahoe LOCO residual R²≈0、per-drug PCC 0.1）。
- **C160**（线 D A0 `unqualified`）：111 表达细胞、1,294 药对嵌套 → 双向聚类 MDE80=0.240 远大于 δ_min=0.05；G2 两侧覆盖 57.3%（并集 95.0%）；但 interaction 份额 0.630、可加上限 0.256、room 0.052、ρ_ceiling 0.788、跨筛 within-pair ρ 0.59 → **信号存在但本资源不可检验**；线停。
- **C161**（线 E1 DrugComb `eligible_with_conditions`）：v1.4 全量 466,033 组合块/4,088 药/112 细胞/62,826 药对/**380,418 cell×pair**；both-unseen 16,078/33,148/52,368（≫800）；注释并集覆盖 51.28%（项目通路模板 0.98%）；与 Jaaks 重合 18 细胞/40 药/241 键；**结构性满足 C155/C156 的第二资源规格，但复现仍需映射/端点/unseen-entity 三份协议**。
- **C162**（资格≠复现）：`eligible_with_conditions` 不改变冻结结论的状态；下一轮必须先冻结（i）可审计 MoA/靶点→≥12 粗水平映射、（ii）端点映射与饱和性、（iii）unseen-entity 切分，然后才谈复现；任何"第二资源已找到"的写法不得越过这三道门。

## 6. 决定与下一步（R191）

1. **线 D 停止**：不运行效果实验；保留 A0 测量级事实与解冻条件（gene-level 注释补全 / 更多细胞或独立抽样单位设计）。
2. **R191 立项：DrugComb 外部复现前置协议（两阶段）**——见 [../2026-10-27-innovation-round-r191/BRIEF.md](../2026-10-27-innovation-round-r191/BRIEF.md)：
   - **阶段 1（不读响应值）**：P-A 注释映射协议（MoA/靶点/家族 → ≥12 个可审计粗略水平；覆盖、碰撞、非响应派生检查；冻结映射表+SHA）；P-B 端点映射与饱和性协议（summary 的 `synergy_bliss`/`S_mean`/`css` 选主端点或 raw dose-level 重拟合 ΔEMAX；饱和/天花板检验；指标冗余）。
   - **阶段 2（前置通过后）**：冻结复现协议——20% 留药（k=818）、both-unseen 16,078 单元、identity/注释/尺寸匹配随机/打乱映射对照、内层按药物分组 λ、Spearman/ top-quartile 指标、MDE、停止条件；独立代理挑战后才运行。
3. 不因 E1 通过而解冻冻结结论；**R191 复现结果出来前，SYNTHESIS 的"唯一解冻条件"仍标未满足**。

## 7. 产物、预算与边界

- 新目录：[../2026-10-27-cellstate-qualification/](../2026-10-27-cellstate-qualification/)（PROTOCOL_A0、a0.py/json、identity_map、target_map、report、record、usage、prior_art、sources_lit）、[../2026-10-27-drugcomb-qualification/](../2026-10-27-drugcomb-qualification/)（PROTOCOL_E1、fetch_data.py、e1.py/json、report、record、usage、download_receipt、downloads/ 260 MB）、本目录 BRIEF/PROTOCOL_D_DRAFT/record/usage。
- 代理：3 名（资格审计×2、先例核验×1）＋Lead；检索预算：prior art 2 pass（EPMC/OpenAlex/arXiv）；下载 260.0 MB（≤300 MB）。
- 计算：a0.py 3+1 次全跑（各 ~73–82 s）、e1.py 3 次全跑（各 ~25 s）；CPU-only；无 GPU、无湿实验、无效果估计。
- 边界：D 线"unqualified"是设计/资源结论，不是"细胞状态没有信息"（A0 显示信号与 room 存在，是**检定力**问题）；E1"eligible_with_conditions"是资源结构结论，不是复现成立；无机制/靶点/临床主张；**未晋升任何代码**；总体目标未达成。
