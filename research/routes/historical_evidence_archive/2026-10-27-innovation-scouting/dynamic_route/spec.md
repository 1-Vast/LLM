# R198-A3v2 动态路线 L1 开发资产：SPEC（可审计版）

2026-10-27 ｜ 执行：cellstate-lit（task-47，A3v2 修订） ｜ 状态：**SPEC = FROZEN-DRAFT（只冻结"开发层 L1"的设计与判定门，不运行）**。
上游：A3 v1（`qualification.md` / `protocol_draft.md` / `cadence_evidence.md` / `record.md` / `usage.json`）与独立挑战 `challenge_A3.md`（判决 `revise`，≤5 必改，不 stop）。
定位（Lead 处置）：**"另问" L1 群体时间预测开发资产；不进入候选冻结、不进入 L2 决策层。** 本文件就是挑战要求补交的 `spec.md`（R198 record 第 82 行链接的路径）。
禁止：训练、跑时间预测、读表达矩阵或响应数值、声称新颖性、声称动态世界模型/真实轨迹/决策收益。

---

## 1. 目的与范围

- **唯一问题（L1）**：在本地 Mix-seq 的**表达层**，一个较早时间点的细胞状态（或时间点组合）能否在**留出细胞系**上，比**静态（无时间）基线**更好地预测较晚时间点的**处理效应**。
- **不是**：功能决策（L2）、真实个体轨迹（L3）、机制/靶点因果、动态世界模型、药物排序收益。
- **当前可执行性**：本 SPEC 只冻结设计；**本轮不运行**。L2 仍被"无独立功能结局 + 批次/剂量未认证"阻塞（见 `qualification.md` §5/§6）。
- **成功上限**：即使 L1 全过，也只允许说"开发层表达预测有可检出增量（在该小数据、单协议内）"，不得升级为决策层/世界模型。

---

## 2. 输入、证据与 v1 冻结登记

| 项 | 内容 | 状态 |
|---|---|---|
| 数据 | `data/external/mixseq_scperturb/mcfarland_2020.h5ad`（1,459,410,830 B；SHA256 `94a72400…`），**本 SPEC 只使用 obs/var 元数据与合格的计数**；表达 `X` 在 v2 修订轮**未读** | 元数据已复核（v1 + 挑战） |
| 旧 census | `research/eight_directions_20261026/evidence_audit/mixseq_design_census.csv`（SHA `0ef7b1c7…`，1,952 行，cells 合计 182,875） | 双源一致 |
| 资格报告 | `qualification.md`（`design_data_partial`；285 键；字段冲突/channel/剂量/功能结局缺口） | v1 冻结 |
| 可识别性 | `cadence_evidence.md`（DFA/COA/MRA/PR/FOA 逐字条件 + 行锚） | v1 冻结 |
| 独立挑战 | `challenge_A3.md`（`revise`；5 必改） | 已读 |
| 元数据辅助 | `tmp/a3v2_eligibility.py` → `tmp/a3v2_eligibility.json`（本轮新算：L1 合格单元数、v1 SHA 复核） | 本轮新增 |

**A3 v1 文件 SHA256（冻结；v2 不改它们）**：

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `a3_inspect.py` | 29,844 | `09e334417fecd389842000ffd6a48a0b105de441680ec9e4789d469854c7faa0` |
| `a3_meta.json` | 52,766 | `fcf56d459b3e78433b7efdb49ee29e0f9a65107b41b435e87664c4354c254000` |
| `qualification.md` | 20,666 | `13272b01000102b1c3cd8612cdee8eb6f9eca50b2b3d862c1d3c7c364d0c65d5` |
| `protocol_draft.md`（v1） | 21,521 | `9d7ae195224259a93defb57a7358752dbc7018b0562fb6dcdc2fb7cf09d4eedc` |
| `cadence_evidence.md` | 6,388 | `0b6bdcc3cddadba68b4b2e51f2782fe046562c39c3d3f759739fc1128e169fd6` |
| `record.md`（v1） | 9,283 | `873c0cb1dd0e791f7a2ac0b142e6c4f83d2cd22c51b3f4e58531928071941b76` |
| `usage.json`（v1） | 7,170 | `31d56cdaa4b8f32f6601ddc532c097826f3d4fa6765b5cef54a0aa69855dfee8` |

（v1 的 `record.md`/`usage.json` 不在 v1 record 的 5 行哈希表内，本表补齐。）

**`kinetic_horizon` 缓存读取的权威描述（v2 统一，取代 v1 两处不一致措辞）**：
> 仅识别 `data/external/kinetic_horizon_20261010/` 下的文件名/字节数，并仅为判断是否为响应缓存而观察了 npz 的 keys/shapes/dtypes（元数据）；**未读取任何数组值**；provenance、split 与用途**未审计**，不能作为认证终点或本 SPEC 的输入。

---

## 3. 资格结论摘要（不改写）

- `design_data_partial`：285 个 `(drug, cell_line)` 键在精确 6h/24h 两侧均存在（BRD3379 98 / Bortezomib 24 / Idasanutlin 24 / Trametinib 24 / control 115；115 细胞系）；双源逐元素一致。
- 每键 QC-normal 细胞数：6h 4/108/398、24h 7/104/378；≥20 normal 的键 279/285；每药满足"药物键 + 时间匹配 control 键均 ≥20"的细胞系数为 **BRD3379 95、Bortezomib 22、Idasanutlin 24、Trametinib 24**（本轮 `tmp/a3v2_eligibility.json`）。
- hashed 臂：20,028 细胞 → 17,553 single-tag（Tram 3/6/12/24/48h + DMSO 5 点 + Untreated_48hr），24 系；严格 ≥20 normal 且输入/目标条件齐全时，**目标 12h 与 48h 各只剩 15 系** → V2 只能作 exploratory（见 §5）。
- 缺口：无独立功能结局；无 batch/plate/run；6h/24h channel 不匹配；dose 单值且 BRD3379=0.0 矛盾；hash 赋值未重建（2,475 细胞 tag≠assignment）。这些是 v1 已定结论，本 SPEC 不重复展开。

---

## 4. 定义：资产、单元、端点

### 4.1 数据变体

| 变体 | 数据 | 用途 | 判定地位 |
|---|---|---|---|
| **V1** | 精确 6h/24h：4 药 + control × 115 系（285 键）；每药合格线 95/22/24/24 | 主开发资产（4 药可做跨药描述；**不作跨药推断单位**） | **confirmatory-development**（可出 L1 判定） |
| **V2** | hashed Trametinib：24 系 × {3,6,12,24,48}h × {Tram, DMSO} | 单药时间过程/方法开发 | **exploratory only**（严格合格线 15<20 → 不出判定、不升级） |
| V2-other | 24h-only 9 药 × 94–98 系 | 静态外部层（可选，不在本 SPEC 判定范围） | 不进入 L1 |
| CRISPR 72/96h | 遗传扰动 | 与药物决策不直接相关 | 不进入 |

### 4.2 端点

- **单元**：细胞系（不是 key、不是细胞、不是时间点）。V1 每药有效 n = 合格线数（95/22/24/24）；V2 有效 n = 15。
- **目标**：对每个 (drug `d`, 细胞系 `c`, 目标时间 `t`)：
  - `y_{d,c,t}` = 该细胞系在 t 的处理效应标量：**train-only 冻结的基因集**（按训练线平均 |logFC| 取 top-K=200，K/选择规则在冻结时写死、只看训练折）上的 pseudobulk logFC 均值；pseudobulk = 该 (d,c,t) 的 QC-normal 单细胞表达均值（对照为同时间匹配 control），logFC = log2((pseudo+1)/(ctrl+1))。
  - 向量版（副）：同基因集上的完整 logFC 向量，用于描述性相关。
- **基线模型（V1）**：
  - `C0` mean：训练线均值（常数）→ 组内排序 ρ=0 by construction。
  - `C1` static：细胞系**未处理**特征 → y。特征冻结为：DepMap/CCLE basal expression（本地 `depmap_19q4/CCLE_expression.csv`）与 h5ad 基因 symbol 的交集，训练折内标准化 + PCA（k 内层 CV 选）+ ridge。**C1 是"无时间"基线；它的存在保证 L1 比较不是"模型 vs 常数"。**
  - `C2` early-state：6h 处理 vs 6h 时间匹配 control 的 pseudobulk logFC（同一基因面板）→ ridge → 预测 24h y。
  - `C5` oracle：目标 24h 的 `y` 本身（仅用于 room/上限，不是候选模型）。
  - `C6` negative：把 C2 的 6h 特征按细胞系标签打乱（置换零分布，≥200 次）。
  - **V1 禁止出现 C3/C4**（见 §5.3）。
- **V2（exploratory）**：目标 12h（输入 3h、6h）与 48h（输入 3/6/12/24h）；比较 `C1 static`、`C3 two-snapshot（仅严格更早时间点拼接）`、`C4 simple linear-time model`（按基因对"更早时间点 → 目标时间"做线性外推/拟合，只用更早时间点；OT/flow 只可作附加估计器对照，不进判定）。**V2 无判定权。**

### 4.3 切分与调参（写死）

- 随机种子 `20261027`；所有折、置换、bootstrap 用该种子派生。
- **V1**：外层 = 按细胞系分组的 5 折 leave-cell-line-out（合格细胞系按名称排序，`fold = i % 5`；同一细胞系所有键在同一折）。内层 = 训练折内按细胞系分组的 5 折用于 λ/PCA-k/基因集选择；标准化、PCA、基因选择只在训练折拟合。测试细胞系的任何信息（含其 6h/24h 标签）不得进入特征选择/标准化/调参。
- **V2**：外层 = leave-one-time-out（目标 12h 与 48h 各一折；6h/24h 可作探索，3h 无更早输入故不做目标）；内层 = leave-cell-line-out（训练时间与训练细胞系内 5 折）。任何模型不得使用目标时间点或更晚时间点。
- **聚合**：不做"键级合并"；V1 主统计量 = 4 个药的 Δ 的等权平均（先算每个药的组内排序相关，再平均；不把 95 系的药加权压过 22 系的药）。
- **CI**：两层 cluster bootstrap（细胞系内嵌套于药物；V1 主平均另对 4 个药做 drug-level 描述性重抽样并报告范围；4 个药不足以做药物总体推断，明确写"不对药物总体推断"）。

---

## 5. L1 预注册判定门（冻结；不通过 = `evaluation_cannot_distinguish`）

> δ_min = **0.10**（Δ Spearman，绝对差）。运营定义：在 22–95 系的规模下，Δρ=0.10 约对应"前 5 候选名单中 1–2 个位置的稳定改变"；小于 0.10 的增量不改变开发层动作（继续/停止动态取证），因此不设更小门。该定义不依赖本资产未读的表达值，**不得在看过测试集后改**。

### 5.1 顺序（先测后比）

1. **G0 资格门槛（metadata 已可预检）**：V1 每药合格线 ≥20（实际 95/22/24/24，全部过）；V2 严格合格线 15<20 → V2 只作 exploratory、无判定权。
2. **G1 split-half 可靠性上限**：对每个 (drug, 目标时间 t) 把每个合格 (c) 的 QC-normal 细胞按 `hash(cell_index, 20261027) % 2` 分两半；分别算 pseudobulk effect；跨线相关 `r_half`（half-A vs half-B）；Spearman–Brown `rho_sb = 2r_half/(1+r_half)`。门：**`rho_sb ≥ δ_min + MDE80`**。若 <20 系可算或任一半细胞 <10 → 门失败。
3. **G2 room（静态到 oracle 的差距）**：在留出细胞系上计算 `rho_oracle`（用 G1 的可靠性上限对目标排序的上界估计，或直接用 half-A 作为 oracle 预测、half-B 作观测）与 `rho_C1`；`room = rho_oracle − rho_C1`。门：**`room ≥ max(δ_min, MDE80)`**。
4. **G3 MDE80**：对主对比 Δ（C2−C1，配对）用 cluster bootstrap（按细胞系重抽，1,000 次，固定种子）估计 SE(Δ)，`MDE80 = (z_{0.975}+z_{0.80})·SE(Δ)`。门：**`MDE80 ≤ δ_min`**。
   - **预运行解析上界（本 SPEC 冻结；来自 n 与独立误差保守假设）**：`MDE80_upper = 2.802·sqrt(2/(n−1))`；V1 n=95/22/24/24 → **0.41 / 0.86 / 0.83 / 0.83**；V2 n=15 → **1.06**。因此除非两模型误差高度相关，否则门很可能失败；要求的跨模型误差相关（使 MDE80=0.10）为 `r_err ≥ 1 − 0.01(n−1)/15.70`：n=95 → **0.940**；n=22 → **0.987**；n=24 → **0.985**；n=15 → **0.991**。**若实际 bootstrap MDE80 > 0.10，直接判 G3 失败，不跑效应比较。**
5. **G4 主效应**：V1 主对比 `Δ = mean_{d}(ρ(C2_d) − ρ(C1_d))`（留出细胞系，按药先算后等权平均）。门：**点估计 ≥ δ_min 且 95% CI 下界 > 0**。
6. **G5 泄漏审计（一票否决）**：检查每个模型/特征/调参：无目标时间点或其函数进入任何输入；无未来时间点；无测试细胞系标签/统计；基因集/PCA/标准化/λ 只在训练折拟合；折按细胞系分组；V1 不含 C3/C4。失败 → `design_invalid`。

### 5.2 判定语义

- 任一 G1–G3 失败 → **`evaluation_cannot_distinguish`**（不是"动态信息不存在"；不写阴性结论）。
- G0 失败 → `data_unavailable`。
- G5 失败 → `design_invalid`。
- G1–G5 全过且 G4 过 → **`development_increment_present`**（仅表达层开发结论；不得升级 L2/候选/世界模型）。
- G1–G3 过、G4 不过 → `no_increment`（停动态取证，但仍不得写"不存在"）。
- **V2**：因 n=15<20，仅报 exploratory 描述（含同样指标与门的结果），**不产生 pass/fail 判定、不升级**。

### 5.3 C3 防泄漏（挑战必改-B）

- **C3 只在 V2 定义**：`C3_t = concat(该细胞系在 t 之前的时间点的 pseudobulk 状态)`；对目标 12h 只用 3h/6h；对目标 48h 只用 3/6/12/24h。
- **V1 严禁任何"目标时间（24h）作输入"**：V1 模型集 = {C0, C1, C2, C5, C6}；C3/C4 不在 V1 出现；任何 24h 派生物（含其标签均值、PCA、基因选择）不得进入输入/调参/标准化。
- G5 自动检查：模型输入列不含目标时间；特征管道无未来时间；代码冻结后由独立复审重放检查。

---

## 6. 动态量→决策映射（v2 修正摘要）

完整表见 `protocol_draft_v2.md` §3。v2 修正：
- **Q2**：改称"早期 vs 晚期**表达层 state-associated proxy 排序**"；**不称 responder**；表达效应不能外推功能 responder（D-B 需 L2）。
- **Q5**：更正为"**control 在 6h 与 24h 均有测量（115 键/时点）**，提供时间匹配对照；但 **channel/批次不可匹配**，所以 6h/24h 差异不能直接当时间效应；hashed 臂另有 DMSO 5 时间点"。
- **Q7**：支持等级改 **M***（需新增细胞状态注释/打分；h5ad 只有设计+QC 元数据，无状态注释）。
- **静态/两快照已足够的决策清单**：见 `protocol_draft_v2.md` §3.2（D-A 基线即可；24h-only 9 臂只做静态外部层；D-D 在只有 2 点时退化为"仅 24h vs 6h+24h"二选一；若 Q3 的 6h/24h 药排序一致 → 单时点足够；若 Q5 对照漂移可忽略 → 无需时间匹配模型；若 C2≈C4 → 两快照足够）。
- **Q8/Q9/Q10 保持不支持**（无洗脱、无剂量序列、无个体轨迹）。

---

## 7. 先例与边界（bounded；不声称新颖性）

- **检索范围/状态**：本轮不做系统检索；仅沿用项目既有 registry 与用户报告的**有界阅读**（窗口 2025-01-01—2026-10-27；非穷尽；`未发现 ≠ 不存在`）。所有条目均标注证据级，**本 SPEC 不主张任何新颖性**。
- **近期有界先例**：
  1. **虚拟细胞 in-the-wild 基准**（arXiv:2604.27646，2026-04-30；本地 `reference/papers/arxiv-2604.27646/paper.html`，P 级；`reference/papers.tsv` reading_scope="Results on context transfer, unseen perturbations, cross-dataset integration; evaluation limits"）：在 unseen cell / unseen perturbation / cross-dataset 三场景统一基准 11 模型；**其数据清单明确包含 McFarland2020（本资产的来源研究）**，并强调"简单线性基线常常优于复杂模型"（`tmp/arxiv_2604.27646.txt:186,269`）→ 本 SPEC 的 L1 必须把线性/静态基线作为主对照，且**不是新基准**。
  2. **CellFlow（形态）**：未配对终点流匹配，插值 `t` 非物理时间（用户报告 P 级；`evidence_notes.md:19`）。
  3. **State**（Cell 2026，DOI 10.1016/j.cell.2026.07.052；项目 registry **A 级**，全文受限）：跨 context 扰动响应预测；不能当本资产的轨迹证据。
  4. **XPert**（Nat Mach Intell 2026，DOI 10.1038/s42256-025-01165-w；`handoff-method-audit/report.md:25` P 级）：KG+扰动表达+剂量/时间，已有未见细胞/药物任务；主要输出转录变化，不能当独立决策收益。
  5. **BATCHIE**（Nat Commun 2025）：条件组合模型+后验更新+整板设计（用户报告 P 级）；"主动选测量"已有先例，L2 若做决策设计需与之对拍。
  6. **CADENCE**（arXiv:2605.23470v1）：见 `cadence_evidence.md`（可识别性条件；本 SPEC 的 L1 不做轨迹主张）。
  7. **target-identifiability**（SSRN 7368638；A 级，403 未读）：破坏性快照/路径目标/sharp bounds，仅登记为压力。
- **谱系/边界引用**：
  - **C160**（R190-D 停：检定力/设计失败，非"细胞状态无信息"）；**C167**（R192 `not_replicated`，不证明"不能复现"）；**C172**（Q 条件主效应 1.43% 仅为加性份额）。
  - **C174**（R194 解释更正：1.43% 只是加性条件主效应份额；加权矩/依赖/可靠性需重核）——动态路线**不以 C172/C174 的旧解释为前提**。
  - **C176**（R196 判定撤回 `replicated_under_audit` 作废，`inconclusive`；原数字保留）；**C177**（R197 v1 协议作废、v1 结果不得解释；低秩问题仍未检验）——**C176/C177 的撤回不影响本路线，但禁止引用旧判定；R196v2/R197v2 未完成前不重开其问题**。
  - 与 **A1/A2/A4/A5 解耦**：本 SPEC 只作"另问" L1 开发资产，不改变、不依赖其它 A 线结论。
- **不得声称新颖性**：本 SPEC 的 L1 是**小规模、单资产、预注册开发比较**，不是新方法/新基准/新机制。

---

## 8. 失败类别与停止条件（与挑战一致）

| 类别 | 触发 | 动作 |
|---|---|---|
| `data_unavailable` | G0 不合格（<20 系/药；条件不足） | 停；不写阴性 |
| `design_invalid` | G5 泄漏审计失败；折/种子/管道偏离 | 停并修协议；不得解释旧输出 |
| `evaluation_cannot_distinguish` | G1/G2/G3 任一不过 | 判 inconclusive；**不写"动态信息不存在"**；停 L1，不升级 |
| `no_increment` | G1–G3 过、G4 不过 | 停动态取证；保留描述性结果；不升级 |
| `identifiability_unsupported` | 任何轨迹/个体路径主张（L3） | 禁止；本 SPEC 不产出 |
| `exploratory_only` | V2（n=15<20） | 只报描述，无判定 |
| `decision_layer_blocked` | L2 所需功能结局/批次/剂量缺失 | 停在 L1；L2 等新测量，不换名重启 |

**总停止规则**：任何门失败 → 不运行后续；不换端点/阈值；不得事后挑指标；L1 不过不得进入 L2/候选。

---

## 9. L2 升级所需数据（不在本轮）

见 `protocol_draft_v2.md` §7（功能终点、时间匹配、批次、重复、决策效用/δ_min、MDE、预注册）。**L1 通过也不自动进入 L2**；L2 必须另立协议 + 独立挑战。

---

## 10. 不做 / 不得声称（保留模板）

1. 本轮**不训练、不跑时间预测、不读表达/响应**；SPEC 只是设计。
2. **不得声称**：动态世界模型成立、真实轨迹恢复、多快照即可恢复路径、动态信息带来决策收益、L1 增量已支持 L2。
3. **不得**把 6h/24h 差异直接当时间效应（无 batch/run、channel 不同）；**不得**把表达 proxy 当功能 responder；**不得**把流匹配插值当物理时间。
4. **不得**把"未发现"写成"不存在"；**不得**声称新颖性。
5. **不得**改 v1 文件；v1 的两处措辞不一致以本 SPEC §2 的权威描述为准（v2 记录 `REVISION_A3.md`/`record_v2.md` 登记）。

---

## 11. 变更记录（v1 → v2）

| # | 挑战必改 | v2 落实 |
|---|---|---|
| 1 | `spec.md` 缺失；kinetic_horizon 描述不一致 | 本文件即补交的 SPEC；§2 给权威统一描述；`REVISION_A3.md` 逐条映射 |
| 2 | L1 无判定门；C3 泄漏风险 | §5 冻结 δ_min/MDE80/room/split-half/eligibility 门与语义；§5.3 C3 仅 V2、V1 禁目标时间 |
| 3 | Q2/Q5/Q7 过宽；缺"静态即可"清单 | §6 修正 + `protocol_draft_v2.md` §3 完整表与清单 |
| 4 | 先例/边界不全 | §7 有界先例 + C174/C176/C177 + 不重开 R196v2/R197v2 |
| 5 | 记录/措辞一致性 | §10 模板保留；`record_v2.md`/`usage_v2.json` 记录 spec 决定、SHA 与读取边界 |

**v2 新文件 SHA256**：见 `REVISION_A3.md` §4 与 `usage_v2.json`（以其冻结值为准；本文件自身哈希不内嵌）。
