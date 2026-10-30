# R198-A3v2 修订回复：逐条落实挑战 A3 的 5 必改

2026-10-27 ｜ 执行：cellstate-lit（task-47） ｜ 上游：`challenge_A3.md`（drugcomb-auditor，判决 **`revise`**，≤5 必改，不 stop）。
本文件是**修订回复**：逐条列出挑战要求 → v2 落实 → 验收证据/位置 → 剩余缺口。**不改 v1 文件**（SHA 见 §4；v2 只新增文件）。
**总处置**：A3v2 仍是**"另问" L1 群体时间预测开发资产**；**不进入候选冻结、不进入 L2 决策层**；本轮**不训练/不跑时间预测/不读表达或响应/不声称新颖性**。

---

## 0. 状态与交付

- 挑战判决：`revise`（5 必改）；本修订**未 stop，也未运行**。
- 新增交付（均在 `dynamic_route/`）：
  - `spec.md`（补交；R198 record 第 82 行链接的路径）
  - `protocol_draft_v2.md`（DRAFT；取代 v1 protocol 的 L1 部分）
  - `REVISION_A3.md`（本文件）
  - `record_v2.md`、`usage_v2.json`
- v1 文件保持冻结、不改；v1 的两处措辞不一致在本文件 §2 与 `spec.md` §2 给权威统一描述（v1 不再作为运行依据）。
- 本轮新增 metadata-only 辅助：`tmp/a3v2_eligibility.py` → `tmp/a3v2_eligibility.json`（L1 合格单元数与 v1 SHA 复核；**不读表达/响应**）。

---

## 1. 五必改逐条落实

### 必改-1 交付完整性（补 spec / 统一 kinetic_horizon 描述 / v1 SHA）

**要求**：补 `spec.md` 或正式声明并入并同步；统一 `kinetic_horizon` 读取描述；A3 v1 五文件 SHA 登记。

**落实**：
- ✅ **补交 `spec.md`**：独立可审计（目的/范围、输入与 v1 SHA、资格摘要、定义、L1 判定门、C3 防泄漏、Q 表修正摘要、先例/边界、失败类别/停止、数据规格、不得声称清单、变更记录）。R198 record 的 `dynamic_route/spec.md` 链接现在可解析；**未修改 R198 record**（本轮写入范围仅 `dynamic_route/`，如需登记 spec.md 由 Lead 决定）。
- ✅ **统一 kinetic_horizon 描述**：权威表述 = **"仅识别文件名/字节数，并仅为判断是否为响应缓存而观察了 npz 的 keys/shapes/dtypes（元数据）；未读取任何数组值；provenance/split/用途未审计，不能作为认证终点或 SPEC 输入"**（`spec.md` §2；`record_v2.md` §2；`usage_v2.json`）。v1 的 `qualification.md` §0.4（"只列目录、不读内容"）与 `record.md` §1.2/§2.7（"观察 keys/shapes/dtypes"）不一致，**以 v2 权威描述为准**；v1 文件不改，避免伪造历史。
- ✅ **A3 v1 SHA 登记**：见 §4（7 个文件；其中 5 个与 v1 record 表一致，本轮 `tmp/a3v2_eligibility.json` 复核 `v1_hashes_match_record=true`；`record.md`/`usage.json` 由本轮补齐）。

**验收**：`spec.md` 存在；`REVISION_A3.md` §4 列出 v1 7 文件 SHA；`tmp/a3v2_eligibility.json` 记录 hash match=true。

---

### 必改-2 L1 判定门 / C3 防泄漏

**要求**：冻结 L1 的 δ_min/MDE80/room/split-half 可靠性门（不过即 `evaluation_cannot_distinguish`）；C3 仅 V2 第三时间点、V1 禁止目标时间入输入；比较器/切分/按细胞系分组写死；独立单位=细胞系；V2 标开发/探索、不作跨药推断。

**落实**（冻结值见 `spec.md` §5 / `protocol_draft_v2.md` §5）：
- ✅ **δ_min = 0.10**（Δ Spearman 绝对差；运营定义：22–95 系规模下约对应前 5 候选名单 1–2 个位置的稳定改变；**不依赖未读表达值；不得事后改**）。
- ✅ **G1 split-half 可靠性门**：每 (drug, target t) 内按细胞 hash 分半 → 两套 pseudobulk effect → 跨线相关 → Spearman–Brown `rho_sb`；门 **`rho_sb ≥ δ_min + MDE80`**。
- ✅ **G2 room 门**：`room = rho_oracle − rho_C1`；门 **`room ≥ max(δ_min, MDE80)`**。
- ✅ **G3 MDE80 门**：配对 Δ（C2−C1）按细胞系 cluster bootstrap（1,000 次，种子 20261027）估 SE；`MDE80=(1.959964+0.841621)·SE(Δ)`；门 **`MDE80 ≤ δ_min`**。预运行解析上界（冻结）：`MDE80_upper=2.802·sqrt(2/(n−1))` → V1 n=95/22/24/24 = **0.41/0.86/0.83/0.83**；V2 n=15 = **1.06**；要求的跨模型误差相关 `r_err ≥ 1−0.01(n−1)/15.70` → n=95 **0.940**、n=22 **0.987**、n=24 **0.985**、n=15 **0.991**。**实际>0.10 → 不跑 G4，直接 `evaluation_cannot_distinguish`。**
- ✅ **G0 资格门**：V1 每药合格线 ≥20（实测 95/22/24/24 全过）；V2 严格合格线 **15<20** → **exploratory only**、无判定权、不作跨药推断。
- ✅ **G4 主效应门**：V1 `Δ = mean_d(ρ(C2_d)−ρ(C1_d))`；要求点 ≥0.10 且 95% CI 下界 >0；4 药只作等权平均 + 描述，**不对药物总体推断**。
- ✅ **G5 泄漏审计**（一票否决）：见 `protocol_draft_v2.md` §6（代码级断言 V1 模型集、目标时间不可用、折按细胞系、特征只用训练折等）。
- ✅ **C3 仅 V2**：`C3_t = concat(严格早于 t 的时间点)`（12h 用 3h+6h；48h 用 3/6/12/24h）；**V1 模型集固定为 {C0,C1,C2,C5,C6}，C3/C4 不得出现，任何 24h 派生物不得入输入**（`spec.md` §5.3；`protocol_draft_v2.md` §2.2/§6）。
- ✅ **切分/调参写死**：V1 外层按细胞系 5 折 leave-cell-line-out（排序后 `i%5`），内层分组 5 折；V2 leave-one-time-out + 内层 leave-cell-line-out；种子 20261027；标准化/PCA/基因集/λ 只在训练折。
- ✅ **独立单位=细胞系**（非 key/细胞）；V1 每药 n=95/22/24/24；V2 n=15；V2 结果标 `exploratory_only`、不升级。

**验收**：`spec.md` §5（G0–G5 + 判定语义 + 预运行上界）；`protocol_draft_v2.md` §5/§6；L1 无判定门/C3 泄漏两项均不可再被读作"可运行但无门"。

---

### 必改-3 动态量→决策映射修正

**要求**：Q2 改"表达层效应/排查 proxy"（不称 responder）；Q5 更正 control 时间匹配但 channel/批次不匹配；Q7 改 `M*`/需新增注释；补"静态/两快照已足够"清单；Q8–Q10 保持不支持。

**落实**（`protocol_draft_v2.md` §3）：
- ✅ **Q2**：改为 **"早期 vs 晚期 state-associated proxy 排序"**；明确**不称 responder**；表达层排序不能外推功能 responder（D-B 需 L2）。统计对比改为"6h vs 24h **表达 effect 排序**一致性（每药跨系 Spearman + top-k Jaccard）"。
- ✅ **Q5**：改为 **"control 在 6h 与 24h 均有测量（115 键/时点），提供时间匹配对照；但 channel/批次不可匹配，6h/24h 差异不能直接当时间效应；hashed 臂另有 DMSO 5 时间点"**；支持等级 **M***。
- ✅ **Q7**：改为 **M***：需**新增细胞状态注释/打分**（h5ad 只有设计+QC 元数据，无状态注释）。
- ✅ **"静态/两快照已足够"清单**（`protocol_draft_v2.md` §3.2）：D-A 静态即可；24h-only 9 臂只做静态外部层；D-D 在 2 时间点退化为"仅 24h vs 6h+24h"二选一；Q3 若 6h/24h 药排序一致→单时点足够；Q5 对照漂移可忽略→两快照足够；C2≈C4→时间模型不必要；功能终点不可得→停在 L1。
- ✅ **Q8/Q9/Q10 保持不支持**（无洗脱、无剂量序列、无个体轨迹）。

**验收**：`protocol_draft_v2.md` §3 表与 §3.2 清单；`spec.md` §6 摘要。

---

### 必改-4 先例/边界/去重

**要求**：补有界先例（2604.27646 virtual-cell benchmark、CellFlow、State 等；`未发现≠不存在`、不声称新颖性）；补 C174/C176/C177 边界；明确不重开 R196v2/R197v2；与 A1/A2/A4/A5 解耦。

**落实**（`spec.md` §7；`protocol_draft_v2.md` §7）：
- ✅ **有界先例**（不新增系统检索；沿用项目 registry 与用户报告阅读，窗口 2025-01-01—2026-10-27，非穷尽）：
  - **arXiv:2604.27646 虚拟细胞 in-the-wild 基准**（P；本地 `reference/papers/arxiv-2604.27646/paper.html`，`tmp/arxiv_2604.27646.txt` 行锚 :186/:269）：unseen cell / unseen perturbation / cross-dataset 三场景；**数据包含 McFarland2020（本资产来源）**；"简单线性基线常优于复杂模型" → L1 必须以线性/静态为主对照，**不是新基准**。
  - **CellFlow**（P；`evidence_notes.md:19`）：插值 t ≠ 物理时间。
  - **State**（A；registry；全文受限）：跨 context 扰动响应预测，不能当路径证据。
  - **XPert**（P；`handoff-method-audit/report.md:25`）：已有未见细胞/药物任务；输出转录变化≠决策收益。
  - **BATCHIE**（P）：条件组合模型+整板设计；主动设计已有先例。
  - **CADENCE**（P + 本轮 HTML 复核）：DFA/COA/MRA/PR/FOA；本资产不满足 FOA → 不做轨迹主张。
  - **target-identifiability**（A，403 未读）：破坏性快照/路径目标/sharp bounds 的先例压力。
- ✅ **C174/C176/C177 边界**（引用 EVIDENCE_REGISTER 已核实条目）：
  - **C174**：1.43% 仅为加性条件主效应份额；加权矩/依赖/可靠性需重核 → 动态路线**不以 C172/C174 旧解释为前提**。
  - **C176**：R196 `replicated_under_audit` 作废、`inconclusive`（原数字保留）；**C177**：R197 v1 协议作废、v1 结果不得解释（低秩问题仍未被检验）。
  - 明确：**C176/C177 的撤回不影响本路线，但禁止引用旧判定；R196v2/R197v2 未完成前不重开其问题**。
- ✅ **与 A1/A2/A4/A5 解耦**：本 SPEC 只作"另问" L1 开发资产，不改变、不依赖其它 A 线结论。
- ✅ **不声称新颖性**；`未发现≠不存在` 写死在 §7 范围声明。

**验收**：`spec.md` §7、`protocol_draft_v2.md` §7 完整表与谱系段落。

---

### 必改-5 记录/措辞一致性

**要求**：统一缓存读取描述（见必改-1）；record/usage 记录 spec 决定；复查全文 `动态世界模型/机制/决策收益/证明/已支持` 均为否定或条件句；不删 §7"不得声称"清单；阴性不写不存在；失败类别/停止条件与挑战一致。

**落实**：
- ✅ `record_v2.md` 记录：spec.md 决定（补交，不并入）、统一措辞、五必改落实、v1 不改及 SHA 复核、读取边界。
- ✅ `usage_v2.json` 记录：`expression_matrix_read=false`、`response_values_read=false`、`model_training_runs=0`、`time_prediction_runs=0`、`network_fetches=0`、v2 输出 SHA、v1 SHA 复核。
- ✅ 保留措辞模板（`spec.md` §10；`protocol_draft_v2.md` §10）：**不得声称动态世界模型成立/真实轨迹恢复/多快照即可恢复路径/动态信息改变决策/L1 支持 L2**。
- ✅ 失败类别/停止条件对齐挑战（`spec.md` §8；`protocol_draft_v2.md` §8）：`data_unavailable` / `design_invalid` / `evaluation_cannot_distinguish` / `no_increment` / `exploratory_only` / `decision_layer_blocked` / `identifiability_unsupported`；阴性不写"不存在"。
- ✅ 全文禁用措辞复查：v2 四文件中 `动态世界模型/决策收益/已支持/证明` 仅出现在否定句或条件句（`REVISION_A3.md` 本句、spec/protocol 的"不得声称"清单）。

**验收**：`record_v2.md`/`usage_v2.json` 存在且字段一致；`spec.md` §10、`protocol_draft_v2.md` §10 保留模板。

---

## 2. Q 表修正 before/after（挑战必改-3 的精确 diff）

| # | v1（过宽/错误） | v2（修正） |
|---|---|---|
| Q2 | "早期 triage 会把哪些细胞系判为 **responder**" | **"早期 vs 晚期 state-associated proxy 排序"**；不称 responder；表达层不能外推功能 responder（D-B 需 L2） |
| Q5 | 支持 `M*`，括注"hashed 臂有 DMSO 时间匹配；6/24 臂只有 24h channel 信息"（易读成 6/24 无时间匹配对照） | **"control 6h/24h 均有测量（115 键/时点），时间匹配对照存在；但 channel/批次不可匹配；hashed 臂另有 DMSO 5 时间点"**；支持 `M*` |
| Q7 | 支持 `M`（需表达） | **`M*`：需新增细胞状态注释/打分；h5ad 无状态注释** |
| 新增 | — | **"静态/两快照已足够"清单**（D-A、24h-only、D-D 二选一、Q3 一致即单时点、Q5 漂移可忽略、C2≈C4、功能终点不可得 → 停在 L1） |

---

## 3. 关键数字与 v2 新增 metadata-only 结果

- **v1 数字不变**（挑战独立复核一致）：285 键；per-drug 98/24/24/24/115；115 系；双源逐元素一致；hashed 20,028=17,553+2,339+136；264 条件；字段冲突 2,475 / DMSO/Untreated 9,945；PRISM 207/209、BRD3379 97/98；v1 5 文件 SHA 5/5 匹配。
- **v2 新算（metadata-only，来自 `tmp/a3v2_eligibility.json`）**：
  - V1 每药合格线（≥20 normal cells，药物键+时间匹配 control 键均满足）：**BRD3379 95 / Bortezomib 22 / Idasanutlin 24 / Trametinib 24**（均 ≥20 → V1 可作 confirmatory-development）。
  - V2 严格合格线（Tram+DMSO 在输入/目标全部时间点 ≥20 normal）：目标 12h = **15 系**、目标 48h = **15 系**（<20 → exploratory only）。
  - V2 条件级：231/264 条件 ≥20 normal；总 264 条件（24×11 标签）。
  - `v1_hashes_match_record=true`。
- **L1 门数字**：δ_min=0.10；MDE80 预运行上界 0.41/0.86/0.83/0.83（n=95/22/24/24）、1.06（n=15）；所需跨模型误差相关 0.940/0.987/0.985/0.991。**明确写出：除非误差高度相关，L1 很可能 `evaluation_cannot_distinguish`；这正是预注册门的意义（不把"比均值好一点"当增量）。**

---

## 4. A3 v1 文件 SHA256 冻结登记（本轮复核 5/5 与 v1 record 表一致）

| 文件 | 字节 | SHA256 | v1 record 表 |
|---|---:|---|---|
| `a3_inspect.py` | 29,844 | `09e334417fecd389842000ffd6a48a0b105de441680ec9e4789d469854c7faa0` | ✓ |
| `a3_meta.json` | 52,766 | `fcf56d459b3e78433b7efdb49ee29e0f9a65107b41b435e87664c4354c254000` | ✓ |
| `qualification.md` | 20,666 | `13272b01000102b1c3cd8612cdee8eb6f9eca50b2b3d862c1d3c7c364d0c65d5` | ✓ |
| `protocol_draft.md`（v1） | 21,521 | `9d7ae195224259a93defb57a7358752dbc7018b0562fb6dcdc2fb7cf09d4eedc` | ✓ |
| `cadence_evidence.md` | 6,388 | `0b6bdcc3cddadba68b4b2e51f2782fe046562c39c3d3f759739fc1128e169fd6` | ✓ |
| `record.md`（v1） | 9,283 | `873c0cb1dd0e791f7a2ac0b142e6c4f83d2cd22c51b3f4e58531928071941b76` | 补齐 |
| `usage.json`（v1） | 7,170 | `31d56cdaa4b8f32f6601ddc532c097826f3d4fa6765b5cef54a0aa69855dfee8` | 补齐 |

**挑战文件**：`challenge_A3.md`（18,890 B；SHA256 `04ff07f91af558564f7d6839cbbaca2fe03a8c10b375b6983e022f0c0fa8b87f`）只读引用。

---

## 5. v2 新文件 SHA256（冻结值）

| 文件 | 字节 | SHA256 |
|---|---:|---|
| `spec.md` | 19,330 | `1fc255b4485d369da3ca0dbe57e907c9890fb741883987d0d667c3d50a805121` |
| `protocol_draft_v2.md` | 17,875 | `c58e522b6b450f0f9286053c9a131ccf2c2d2168c00cfda7cbcf6f344daeb89b` |
| `REVISION_A3.md` | 本文件 | 不内嵌自身哈希（以 `usage_v2.json` 冻结为准） |
| `record_v2.md` | 见 `usage_v2.json` | 见 `usage_v2.json` |
| `usage_v2.json` | 见文件 | 见文件 |
| `tmp/a3v2_eligibility.py` | 7,748 | `f9e09b196de678a987f03c0cd9577e4d665d248f5ea52748f5edc340d21de7be` |
| `tmp/a3v2_eligibility.json` | 6,082 | `0e9178338fdadb8934555e3079e46e39d297c48f5c045294572b853ed23a172c` |
| `tmp/arxiv_2604.27646.txt` | 85,942 | `1c4a0fff5dd88a4eb25163e8d88773c6c02599dc65fbc0478bc9988297d34840` |

---

## 6. 剩余缺口（不回避）

1. **L1 很可能不可分辨**：预运行上界显示 V1 的 Δ 需跨模型误差相关 0.94–0.99 才可能达到 δ_min=0.10；V2 n=15 → 上界 1.06。若运行，预期首先在 G3 失败并判 `evaluation_cannot_distinguish`——这是预注册门的预期用途，不是阴性结论。
2. **V2 只能 exploratory**：严格合格线 15<20；即使指标好也不能出判定/跨药推断。
3. **表达值未读**：本修订轮不验证任何实际预测/可靠性；所有门是"冻结后运行的规则"。
4. **L2 仍被阻塞**：无功能结局、批次/剂量未认证、无独立培养；需要 §9 数据规格的新测量，且不因 L1 通过而自动解锁。
5. **先例为有界阅读**：非系统检索；2604.27646 的本地 P 级、State 为 registry A（全文受限）、XPert 为 P；`未发现≠不存在`。
6. **R198 record 未改**：本轮写入范围仅 `dynamic_route/`；`spec.md` 已存在使链接可解析，但若 Lead 要在 R198 record 的产物清单中登记，需 Lead 侧操作。

---

## 7. 结论

- 挑战 5 必改**全部落实**（本文件 §1 逐条、§2 Q diff、§3 数字、§4/§5 SHA）。
- A3v2 保持为 **"另问" L1 开发资产：不进入候选冻结、不进入 L2**；本轮**不训练/不跑时间预测/不读表达或响应/不声称新颖性**。
- 建议 Lead：把 `spec.md` 作为 L1 冻结文本；在独立复审（未参与挑战者）确认本文件 §1 的落实与 §5 SHA 后，**才允许**按 `spec.md` §5 冻结 L1 协议并（另立任务）运行开发层比较；**L2 继续等新测量**。
