# R198-A3 独立挑战（dynamic_route）：proceed / revise / stop

2026-10-27 ｜ 挑战者：drugcomb-auditor（未参与 A3 执行）｜ 范围：**只读 A3 产物与本地元数据复核；不训练、不跑时间预测、不读表达/响应数值、不改 A3 产物/其它目录/INDEX/git**。本文件是唯一写入（`dynamic_route/challenge_A3.md`）；复核脚本在 `tmp/`。
证据状态：`已复核（本挑战实测）` / `A3 报告事实` / `P（一手片段）` / `检索结果`；数字均为 metadata-only 计数，未读 h5ad `X` 值、未读任何响应矩阵。

## 0. 总判决（先行）

# **`revise`（≤5 必改；不 stop）**

- **A3 的核心资格结论与关键数字经独立复核全部成立**：285 键、per-drug 98/24/24/24/115、115 细胞系、双源逐元素一致、每键细胞数/QC、channel 缺失结构、hashed 臂 17,553/2,339/136、24 line × 11 标签 = 264 条件（中位 55/42）、字段冲突 2,475/9,945、PRISM 207/209 与 BRD3379 97/98、文件 SHA 全部匹配（§1）。
- **CADENCE 可识别性引用正确且未被当成已解决**：逐字锚点（:122/:123/:134/:138/:575/:581/:588/:396）经本地文本复核命中；A3 明确"两快照/5 固定点不能恢复真实路径、流匹配仅估计器"，并给出"群体边缘预测（L1）vs 功能决策（L2）vs 真实轨迹（L3）"分层——这一项是本轮 A3 最扎实的部分（§2 ①）。
- **但作为可冻结候选/下一轮模块仍不够**：① 声明的 `spec.md` **不存在**（R198 record 链接与任务清单均列它），交付清单不一致；② L1 开发设计**没有可判定的预注册门**（无 δ_min/MDE/room/可靠性阈值），且 C3"两快照拼接"在 V1 有**把目标时间点当输入**的泄漏风险；③ 动态量→决策映射中有 3 处**表述/支持等级过宽**（Q2 responder、Q5 对照可用性、Q7 注释需求），先例覆盖缺"群体时间预测/虚拟细胞基准"的有界说明，且缺 C174/C176/C177 边界引用；④ qualification 与 record 对 `kinetic_horizon` 缓存的读取描述不一致（"只列目录"vs"读 keys/shapes/dtypes"）。
- **处置建议**：**保留为"另问"的 L1 开发资产（群体时间预测），不进入候选冻结、不进入决策层（L2）**；按 §4 五条修完并由未参与复审后，才允许冻结一个"开发层"协议（仍不运行效果）。**本轮不运行时间预测/效果。**

## 1. 独立复核（本挑战实测，metadata-only）

复核对象：`dynamic_route/{qualification.md,protocol_draft.md,cadence_evidence.md,record.md,a3_meta.json,a3_inspect.py,usage.json}`；输入：本地 h5ad **obs/var 元数据**、`mixseq_design_census.csv`、DepMap `sample_info.csv`、PRISM treatment/cell-line **元数据列**、CADENCE 本地文本。脚本：`tmp/verify_a3_claims.py`、`tmp/verify_a3_claims2.py`；结果：`tmp/a3_verify.json`、`tmp/a3_verify2.json`。

| 复核项 | A3 声明 | 本挑战实测 | 结论 |
|---|---|---|---|
| h5ad 结构 | 182,875 × 32,738；obsm/layers/uns 空；raw 无；X 未读 | 完全一致；`a3_inspect.py` 仅取 X shape/type、未读值 | ✅ |
| 285 键（h5ad） | 285；per-drug 98/24/24/24/115；115 系 | 完全一致 | ✅ |
| 285 键（census 双源） | 逐元素相同 | `common_key_sets_identical=true`；census 1,952 行、cells 合 182,875 | ✅ |
| 每键细胞数/QC | 6h 4/108/398；24h 7/104/378；normal ≥10 = 282/285（per-drug 97/23/24/24/114） | 全部一致 | ✅ |
| channel | 6h 全缺失；24h 63,754/101,610 缺失；common keys 222 两侧缺失、63 仅 24h（Tram 24 + control 39） | 完全一致 | ✅ |
| dose | 每药单值；common keys 无剂量冲突；BRD3379=0.0 | 一致（BRD3379 0.0、Bortezomib/Idasanutlin 2.5、Tram 0.1、control 0.0） | ✅ |
| hashed 臂 | 20,028 cells；17,553 single + 2,339 combo + 136 unresolved；Tram/DMSO 各 5 时间点 + Untreated_48；9,945 DMSO/Untreated；2,475 hash_tag≠assignment；dose 全 0.1 | 全部一致（tag 逐项计数也一致） | ✅ |
| 264 条件 / 中位 55 / 42 | 24 行 × 11 标签 = 264；min/median/max 11/55/250；normal 8/42/212；normal 单标签细胞 13,713 | 全部一致 | ✅ |
| clean lines = focal24 | 24 行恰等于非 hashed focal24 | 集合相等（clean=focal24，24） | ✅ |
| 24h-only 9 臂 | 94–98 系/臂；单快照 | 一致（如 AZD5591 94 系、Dabrafenib/Navitoclax 98 系） | ✅ |
| PRISM 元数据 | 207/209 覆盖；focal24 全在；BRD3379 无；BRD3379 98 行中 97 在二级；一级三药各 1 行 2.5 µM；二级 16 剂量点 | 207/209；focal24 全在；BRD3379=0；**BRD3379 97/98（一级与二级均 97）**；一级 2.5 µM、二级 16 点 | ✅ |
| 文件 SHA | record 所列 5 个产物哈希 | 5/5 完全匹配（a3_inspect.py/a3_meta.json/qualification/protocol/cadence） | ✅ |
| `spec.md` | R198 record 与 task-41 列为交付 | **不存在**；A3 自身 record §4/usage outputs 也未列 spec.md | ❌ 交付不一致 |
| CADENCE 锚点 | :122/:123/:134/:138/:575/:581/:588/:396 | 本地文本行锚逐条命中（命题头/正文、COA、FOA、Temporal richness、单点塌缩、COA violation） | ✅ |

**限制**：本挑战未重跑 A3 的 `a3_inspect.py`（避免写 A3 产物）；用独立脚本从同一 h5ad obs 元数据复算，未读 X/响应；CADENCE 仅核 A3 所引片段，不是全文复核；`kinetic_horizon` 派生缓存未打开（A3 自身也未审计 provenance）。

## 2. 六项逐条判定

### ① Mix-seq 资格：**PASS（数字与分档诚实；两处措辞需修）**

- **285 键复核成立**：h5ad 与旧 census 双源逐元素一致（§1）。6h/24h 两快照、4 处理+对照（BRD3379/Bortezomib/Idasanutlin/Trametinib/control）、单药端点（单细胞转录组，无 viability/apoptosis/IC50）、剂量（每药单值，BRD3379=0.0 与处理矛盾）、批次（无 batch/plate/run/donor；channel 6h 全缺失、24h 部分缺失）、独立功能结局（缺失）——**A3 均正确标注**，没有把"可算"写成"已认证"。
- **分档诚实**：`可支撑`（文件/结构/285 键/身份连接/每键细胞数/pseudobulk 开发）vs `需清洗`（混合时间标签、hashed 臂 hash 赋值、BRD3379 剂量、combo/multiplet）vs `未认证`（剂量/批次/独立培养/时间匹配）vs `缺失`（功能结局、轨迹链接）——逐项有依据，`design_data_partial` 判定与证据一致。
- **新发现（hashed 5 时间点）**：不是把旧结论换个说法，而是从 `hash_assignment` 恢复的**单药 Trametinib 5 时间点 + 时间匹配 DMSO（24 系）**；A3 同时标注字段冲突与未认证，属**新增且诚实**的元数据发现；本挑战复算一致。
- **CADENCE 可识别性**：**正确引用而非当成已解决**——逐字条件（DFA/COA/MRA/PR/FOA）与"FOA 需入组时间跨区间、单点塌缩失败"被用于说明本资产**不满足**；且明确指出流匹配 `t` 非物理时间、两快照不能恢复路径。这是本文件应当被保留的核心价值。
- **需修（措辞一致性）**：
  - qualification §0.4 说 `kinetic_horizon_20261010/` **"只列目录、不读内容"**；record §1.2/§2.7 却写"仅观察了 npz 的 keys/shapes/dtypes，未读取数组值"。**两处不一致**；应统一为"仅读 npz keys/shapes/dtypes（元数据），未读数组值，provenance 未审计"。
  - `spec.md` 缺失使 ① 的"spec 部分"无法核；见 ③/⑤。

### ② 动态信息 ↔ 决策映射：**WEAK（映射表有价值，但有 3 处支持等级/措辞过宽）**

- **优点**：Q1–Q10 每项给了"可计算动态量 → 会改变的具体决策（D-A…D-E）→ H0/统计量 → 支持等级（M/M*/F/X）"，并且明确 D-A 需要预处理探针、D-E/路径/剂量×时间**本资产不支持**；没有把"动态量可算"直接当"决策改善"。
- **没有把群体时间预测写成动态世界模型**：grep 全部 A3 文件，`动态世界模型`只出现在**否定句**（"不得声称…"）；`决策收益`只出现在 D-D 指标定义与"报告预测改善但决策不改善"的停止条件中。**这一点 PASS**。
- **WEAK-1（Q2 responder）**：Q2 写"早期 triage 会把哪些细胞系判为 **responder**"，但 L1 只有**表达效应**、没有功能 responder；应改为"表达层效应排序/候选 proxy"，并注明不能外推功能 responder（D-B 需要 L2）。
- **WEAK-2（Q5 对照可用性）**：Q5 支持等级写 `M*`，括注"hashed 臂有 DMSO 时间匹配；6/24 臂只有 24h channel 信息"——易读成 6/24 臂**没有**时间匹配对照。实际 `control` 在 6h 与 24h **都有测量**（115 键/时点，本挑战复核），只是 channel/批次未匹配；应改为"6/24 臂有时间匹配 control 测量，但 channel/批次不可匹配；hashed 臂另有 DMSO 5 时间点"。
- **WEAK-3（Q7 状态组成/细胞周期）**：Q7 支持等级标 `M`（需表达），但"状态组成/细胞周期"需要**细胞状态注释/打分**；h5ad 只有设计+QC 元数据，无状态注释。应改 `M*` 或"需新增注释"，不能与 Q1–Q4 同档。
- **应补**：明确"哪些决策**静态/两快照就够**"（例如 D-A 仅基线；24h-only 9 臂只能做静态外部层；D-D 的"测量时间点"在只有 2 点时可退化为"6h+24h vs 仅 24h"的二选一比较），避免让读者以为所有 D-* 都需要动态模型。

### ③ 设计草案：**WEAK → 需修（比较器/停止框架可执行；缺 L1 判定门 + C3 泄漏风险）**

- **可执行部分（PASS）**：V1/V2 数据变体、C0–C6 比较器、按细胞系/留药/留时间切分、负对照/容量对照、失败类别（7 类）与总停止规则、数据规格（§6）都写得具体，且明确"本轮不训练/不跑/不读数值"；不越界为效果设计。
- **必改-A（L1 无判定门）**：§4 的 L1 只定义 ΔSpearman/ΔR² 相对基线，但**没有预注册 δ_min、MDE、room、可靠性上限门**（这些只出现在 §5.4，且是 L2 决策层）。按现文，L1 跑出"比均值高一点"也可以被叙述为增量，无法判定"是否值得继续"；至少应二选一：**(a)** 给 L1 冻结数值门（例如 ΔSpearman ≥ 预注册 δ_min、split-half 可靠性上限 > δ_min、room≥MDE、按细胞系 cluster bootstrap 的 MDE80 ≤ δ_min；否则 `evaluation_cannot_distinguish`）或 **(b)** 明确把 L1 标为 **exploratory（不产出判定、不得据此升级 L2）**。
- **必改-B（C3 泄漏风险）**：§4.3 C3 写"6h+24h 拼接 → 目标（若目标是留出的 third time，则用 6h/24h 两输入）"。若 V1 的目标是 24h，则把 24h 当输入=**目标泄漏**；当前文字虽用括注限定 V2 third-time，但 V1/C3 行并列呈现，协议冻结时容易被误实现。应明确写死：**C3 仅在 V2（留出 12h/48h 等第三时间点）定义；V1 不得把目标时间点输入任何臂**（或在 V1 中删除 C3）。
- **C3（小）**：V2 leave-one-time-out 只有 1 个药物（Trametinib），5 个时间点，功效仅够开发；应像 Q3 一样显式标注"不能作跨药推断"，避免 24 lines 的 264 条件被当独立样本。A3 已说"独立单位=细胞系/不是键/细胞"（§5.4），建议在 L1 也重复这一句。

### ④ 先例/新颖性：**WEAK（CADENCE 覆盖正确；群体时间预测/虚拟细胞基准覆盖不足）**

- **PASS**：CADENCE 的条件与其局限被逐字引用并落在"不可识别"一侧；CellFlow（插值 t≠物理时间）与 target-identifiability（A 级、403 未读）均按证据状态登记；没有声称"未发现=空白"或"首次"。
- **WEAK**：任务要求的"**群体时间预测/虚拟细胞基准**覆盖判定"没有落地：A3 未讨论 2026 的 virtual-cell in-the-wild 基准（arXiv 2604.27646，背景/扰动/跨数据集迁移与强基线）、State（Cell 2026，跨 context 扰动预测；本项目 registry 为 A 级）、以及群体时间预测/流匹配类先例的边界。资格文件 §8.5 已自认"未做文献综述"——诚实，但作为候选冻结前应补一段**有界先例说明**（检索式、日期、命中项、`未发现≠不存在`），否则"另问"的价值边界不清。
- **建议**：不要求本轮做系统综述；只需在 `spec`/`protocol` 加一段"最近先例与剩余差异（bounded search）"，并保留"不声称新颖性"。

### ⑤ 谱系/纪律/措辞：**WEAK → 需修（缺 C174/C176/C177 边界；交付清单不一致；缓存读取描述不一致）**

- **PASS**：未训练/未跑时间预测/未读表达或响应（`a3_inspect.py` 只读元数据；usage 明示 `expression_matrix_read=false`/`response_values_read=false`/`model_training_runs=0`）；只在 dynamic_route + tmp 写入；不重开 R197（BRIEF:40 只读引用）；不换名重启；措辞模板总体合规（"不得声称动态世界模型/真实轨迹/决策收益"）。
- **必改-C（边界引用不全）**：A3 引了 C160/C167/C172，但 R198 record/任务要求同时说明 **C174（Q2 解释更正：1.43% 只是加性主效应份额）**、**C176（R196 判定撤回）**、**C177（R197 v1 协议作废）** 的边界；否则读者可能把旧"条件规律小/可迁移性已证伪"再带进动态路线。应补一句"动态路线不以 C172/C174 的旧解释为前提；C176/C177 的撤回不影响本路线，但禁止引用旧判定；R196v2/R197v2 未完成前不重开其问题"。
- **必改-D（交付清单）**：R198 record 第 82 行链接 `spec.md`、task-41 也把 spec.md 列为必读，但文件不存在；A3 自身 record §4/usage outputs 也不含 spec.md。**必须二选一**：补写 `spec.md`（把 §0–§7 的问题陈述/资格结论/设计约束/不做清单独立成文）**或**明确"spec 已并入 qualification/protocol"，并同步修改 R198 record 的链接与产物清单、在 A3 record/usage 记录该决定。未解决前 A3 不能进入候选冻结（冻结需要可审的 spec）。
- **必改-E（缓存读取描述）**：见 ①（qualification §0.4 vs record §1.2/§2.7）。
- **必须保留的措辞模板**：`不得声称动态世界模型成立/真实轨迹恢复/多快照即可恢复路径/决策收益`；`表达层 L1 ≠ 功能决策 L2 ≠ 个体轨迹 L3`；`6h/24h 差异不能直接当时间效应`（无 batch/run、channel 不同）。这些是 A3 最有价值的纪律，v2 不得删弱。

### ⑥ 总判决：**`revise`（≤5 必改）；A3 作为"另问"L1 开发资产保留，不进入候选冻结、不进入 L2**

见 §0/§3/§4。明确：**本轮不运行时间预测/效果**；即使修完，也只允许在冻结 L1 协议后运行"群体表达层开发"，仍不得声称决策层/世界模型/真实路径。

## 3. 最致命的 3 条

1. **声明交付物 `spec.md` 缺失，交付/记录不一致**：R198 record 与 task-41 都把 spec.md 当必读，磁盘不存在；A3 自身 record/usage 也未列它。结果是"资格结论"可审、但"设计 spec"不可审，**不能作为冻结候选**（不是数据错误，是交付完整性/可审计性缺口）。
2. **L1 设计无判定门，且 C3 有目标泄漏风险**：无 L1 δ_min/MDE/room/可靠性门 → 任何"比均值好一点"都可能被写成增量；C3"两快照拼接"若在 V1 把 24h 目标当输入即为泄漏。两者都会让"是否继续动态取证"的决策不可复现。
3. **动态量→决策映射 3 处过宽 + 先例/边界不完整**：Q2 responder（表达 proxy vs 功能）、Q5 对照可用性（control 6/24 均在，但通道/批次不匹配）、Q7 需注释；先例缺群体时间预测/虚拟细胞基准的有界说明；缺 C174/C176/C177 边界。这些是"措辞/谱系"问题，不是数字造假，但足以让 A3 被误读为已支持决策层或已排除先例。

## 4. 必改清单（≤5，逐条可验收）

1. **交付完整性**：补 `spec.md`（问题陈述/资格结论/设计约束/不做清单/失败类别/停止条件；与 qualification/protocol 不重复堆叠）**或**正式声明"spec 并入 qualification/protocol"，并同步修改 R198 record 产物清单与链接、A3 record/usage；同时统一 `kinetic_horizon` 读取描述（只读 keys/shapes/dtypes、未读值、provenance 未审计）。
2. **L1 判定门 / C3 防泄漏**：写入 L1 的 `δ_min`（数值或由成本定义的 operational 规则）、`MDE80`/`room`/`split-half 可靠性上限`门，以及不过即 `evaluation_cannot_distinguish`；**明确 C3 只在 V2（留出第三时间点）定义，V1 禁止目标时间点入输入**；V2 结果标"开发/探索，不作跨药推断"。
3. **动态量→决策映射修正**：Q2 改"表达层效应/排查 proxy"（不称 responder）；Q5 改为"control 6h/24h 均有时间匹配测量，但 channel/批次不可匹配"；Q7 改 `M*`/需新增注释；补"静态/两快照已足够的决策"清单（D-A、24h-only 静态层、D-D 的二选一）。
4. **先例/边界/去重**：补一段有界先例（群体时间预测/virtual-cell in-the-wild 基准 2604.27646、CellFlow、State 等；检索日期/式/命中；`未发现≠不存在`、不声称新颖性）；补引 C174/C176/C177 边界并明确动态路线不重开 R196v2/R197v2；保持与 A1/A2/A4/A5 解耦（只作"另问"）。
5. **记录/措辞一致性**：把 qualification §0.4 与 record §1.2/§2.7 的缓存读取描述统一；在 record/usage 记录 spec.md 决定；复查全文 `动态世界模型/机制/决策收益/证明/已支持` 均为否定或条件句；不删 §7"不得声称"清单。

## 5. 是否值得作为"另问"模块保留

**值得保留（L1 开发资产）**，理由：本地确实有 285 键的 4 药+对照 × 115 系 6h/24h 表达层数据与 hashed Trametinib 5 时间点+时间匹配 DMSO（24 系），足以做"静态 vs 两快照 vs 时间模型"的**预注册开发比较**；A3 的资格判定诚实、数字可复核、CADENCE 边界正确。但它**现在不能升级为"动态世界模型/决策层"候选**；在 §4 修完并由未参与挑战者复审前，不冻结、不运行。**若 Lead 只允许保留一个方向，A3 应作为"另问"模块而非主线候选**（与 R197 BRIEF:40、R198 record 一致）。

## 6. 本轮复核的边界

- 只写 `challenge_A3.md`；复核脚本在 `tmp/`；未改 A3 产物（a3_meta.json、qualification.md 等 5/5 SHA 与 A3 record 一致）。
- 未读 h5ad `X` 值/obsm/layers/未读任何 PRISM logfold-change/响应矩阵；未训练/未跑时间预测；未联网（CADENCE 用本地 tmp 文本）。
- 不声称"未发现=不存在"；本挑战不评估 A3 之外的动态文献；`spec.md` 缺失使对本轮 spec 的审查受限（按现有 4 份文档审）。
- 本挑战的复核数字见 `tmp/a3_verify.json`、`tmp/a3_verify2.json`，可由 `tmp/verify_a3_claims.py`/`tmp/verify_a3_claims2.py` 重放（只读元数据）。
